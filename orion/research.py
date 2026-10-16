"""Motor inicial de investigación web de ORION."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import requests

TIMEOUT = 12
HEADERS = {"User-Agent": "ORION-Research/0.1"}


def inspect_url(url: str) -> dict[str, Any]:
    """Obtiene metadatos básicos de una página pública."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Solo se admiten URL HTTPS válidas.")

    try:
        response = requests.get(
            url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        return {
            "url": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "content_type": content_type,
            "title": _extract_title(response.text) if "html" in content_type else None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }


def _extract_title(html: str) -> str | None:
    """Extrae el título HTML sin depender de una biblioteca adicional."""
    import re
    match = re.search(r"<title[^>]*>(.*?)</title\s*>", html, re.I | re.S)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()[:300]


def compare_sources(urls: list[str]) -> dict[str, Any]:
    """Inspecciona varias fuentes y resume los resultados obtenidos."""
    results = [inspect_url(url) for url in urls]
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sources_checked": len(results),
        "sources_ok": sum(1 for item in results if not item.get("error")),
        "results": results,
        "limitation": (
            "Inspección técnica inicial: todavía no realiza búsquedas generales "
            "ni determina por sí sola si una oportunidad es rentable."
        ),
    }

def _search_web_tavily(query: str, max_results: int = 10) -> dict[str, Any]:
    """Busca en la web con Tavily y devuelve fuentes identificables."""
    import os
    import requests
    from datetime import datetime, timezone

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"query": query, "error": "Falta TAVILY_API_KEY", "results": []}

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max(1, min(int(max_results), 20)),
                "search_depth": "advanced",
                "include_answer": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        sources = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "score": item.get("score"),
            }
            for item in data.get("results", [])
        ]
        return {
            "query": query,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "sources_found": len(sources),
            "results": sources,
            "note": "Verificar las afirmaciones con las fuentes originales.",
        }
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "query": query,
            "error": f"Falló la búsqueda Tavily (HTTP {status})" if status else f"Falló la búsqueda Tavily: {type(exc).__name__}",
            "results": [],
        }


def search_web(query: str, max_results: int = 10) -> dict[str, Any]:
    """Busca con Tavily y guarda automáticamente el resultado."""
    from orion.research_history import save_investigation

    result = _search_web_tavily(query, max_results)
    try:
        record = save_investigation(result)
        result["history_saved"] = True
        result["history_id"] = record["id"]
    except Exception as exc:
        result["history_saved"] = False
        result["history_error"] = type(exc).__name__
    return result
