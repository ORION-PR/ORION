"""Ejecutor multisectorial de ORION. Usa el buscador existente."""
import json
from datetime import datetime, timezone
from pathlib import Path
from orion.opportunity_sectors import list_sectors
from orion.research import search_web
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "multisector_runs.json"
def main():
    run = {"started_at": datetime.now(timezone.utc).isoformat(), "mode": "research_only_no_trading", "sectors": []}
    print("ORION | INVESTIGACION MULTISECTORIAL\nModo: investigación web; sin operaciones ni señales de compra")
    for sector in list_sectors():
        query = sector["queries"][0]
        print(f"\n[{sector['name']}] {query}")
        try:
            result = search_web(query, max_results=5)
            items = result.get("results", []) or []
            entry = {"sector_id": sector["id"], "sector": sector["name"], "query": query, "sources_found": len(items), "error": result.get("error"), "sources": [{"title": x.get("title"), "url": x.get("url")} for x in items if isinstance(x, dict)]}
            print(f"Fuentes encontradas: {len(items)}")
            if entry["error"]: print("Aviso del buscador:", entry["error"])
            for src in entry["sources"][:3]: print(" -", src.get("title") or "Sin título", src.get("url") or "")
        except Exception as exc:
            entry = {"sector_id": sector["id"], "sector": sector["name"], "query": query, "sources_found": 0, "error": type(exc).__name__, "sources": []}
            print("Error en este sector:", type(exc).__name__)
        run["sectors"].append(entry)
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    history = []
    if OUT.exists():
        try:
            history = json.loads(OUT.read_text(encoding="utf-8"))
            if not isinstance(history, list): history = []
        except (ValueError, OSError):
            print("ERROR: no se pudo leer el informe anterior; no se sobrescribe."); return 2
    history.append(run)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUT)
    print(f"\nSectores procesados: {len(run['sectors'])}")
    print(f"Fuentes encontradas en total: {sum(s['sources_found'] for s in run['sectors'])}")
    print(f"Informe guardado: {OUT.relative_to(ROOT)}")
    print("Nota: hallar fuentes no valida por sí solo una oportunidad comercial.")
    return 0
if __name__ == "__main__": raise SystemExit(main())
