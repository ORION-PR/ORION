
"""Ejecutor multisectorial de ORION. Investiga varias consultas por sector."""
import json
from datetime import datetime, timezone
from pathlib import Path

from orion.opportunity_sectors import list_sectors
from orion.research import search_web

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "multisector_runs.json"


def main():
    run = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": "research_only_no_trading",
        "sectors": [],
    }

    print(
        "ORION | INVESTIGACION MULTISECTORIAL\n"
        "Modo: investigación web; sin operaciones ni señales de compra"
    )

    for sector in list_sectors():
        queries = sector.get("queries", [])
        if isinstance(queries, str):
            queries = [queries]
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]

        sources = []
        seen_urls = set()
        errors = []

        print(f"\n[{sector['name']}] Consultas: {len(queries)}")

        for query in queries:
            print(f"  Buscando: {query}")

            try:
                result = search_web(query, max_results=5)
                if not isinstance(result, dict):
                    errors.append(f"{query}: respuesta inesperada")
                    continue

                if result.get("error"):
                    errors.append(f"{query}: {result['error']}")

                items = result.get("results", []) or []

                for item in items:
                    if not isinstance(item, dict):
                        continue

                    url = (item.get("url") or "").strip()
                    if not url or url in seen_urls:
                        continue

                    seen_urls.add(url)
                    sources.append({
                        "title": item.get("title") or "Sin título",
                        "url": url,
                        "query": query,"snippet": str(item.get("snippet") or item.get("content") or "")[:4000],
"search_score": item.get("score"),
                    })

                print(f"    Resultados recibidos: {len(items)}")

            except Exception as exc:
                errors.append(f"{query}: {type(exc).__name__}")
                print(f"    Error: {type(exc).__name__}")

        entry = {
            "sector_id": sector["id"],
            "sector": sector["name"],
            "queries": queries,
            "queries_count": len(queries),
            "sources_found": len(sources),
            "error": "; ".join(errors) if errors else None,
            "sources": sources,
        }

        print(f"  Fuentes únicas: {len(sources)}")
        for source in sources[:3]:
            print("   -", source["title"], source["url"])

        run["sectors"].append(entry)

    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if OUT.exists():
        try:
            history = json.loads(OUT.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                print("ERROR: el historial no es una lista; no se sobrescribe.")
                return 2
        except (ValueError, OSError):
            print("ERROR: no se pudo leer el informe anterior; no se sobrescribe.")
            return 2

    history.append(run)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(OUT)

    print(f"\nSectores procesados: {len(run['sectors'])}")
    print(f"Consultas ejecutadas: {sum(s['queries_count'] for s in run['sectors'])}")
    print(f"Fuentes únicas: {sum(s['sources_found'] for s in run['sectors'])}")
    print(f"Informe guardado: {OUT.relative_to(ROOT)}")
    print("Nota: encontrar fuentes no demuestra demanda ni rentabilidad.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

