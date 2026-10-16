"""Historial independiente de investigaciones web de ORION."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_PATH = Path("data/orion_research.json")


def save_investigation(result: dict[str, Any]) -> dict[str, Any]:
    """Guarda una investigación y devuelve el registro almacenado."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if HISTORY_PATH.exists():
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError("No se pudo leer el historial; no se modificó.") from exc
    else:
        data = {"version": 1, "investigations": []}

    if not isinstance(data, dict) or not isinstance(data.get("investigations"), list):
        raise RuntimeError("Formato de historial inesperado; no se modificó.")

    record = {
        "id": len(data["investigations"]) + 1,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "query": result.get("query", ""),
        "sources_found": result.get("sources_found", 0),
        "results": result.get("results", []),
        "error": result.get("error"),
    }

    data["investigations"].append(record)
    HISTORY_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return record


def load_investigations() -> list[dict[str, Any]]:
    """Recupera las investigaciones guardadas."""
    if not HISTORY_PATH.exists():
        return []
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    return data.get("investigations", [])
