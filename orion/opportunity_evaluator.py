"""Evaluación preliminar y explicable de evidencias de ORION."""
import json
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "multisector_runs.json"
OUTPUT = ROOT / "data" / "opportunity_evaluations.json"
def evaluate_sector(sector):
    sources = sector.get("sources", []); domains = set(); valid = []
    for src in sources:
        url = src.get("url", ""); title = (src.get("title") or "").strip(); parsed = urlparse(url); host = parsed.hostname
        if title and host and parsed.scheme in ("http", "https"):
            valid.append(src); domains.add(host.lower().removeprefix("www."))
    count = len(valid); diversity = len(domains); score = min(60, count*8) + min(40, diversity*8)
    level = "SIN EVIDENCIA DOCUMENTAL" if count == 0 else ("BASE DOCUMENTAL INICIAL" if diversity >= 3 and count >= 3 else "EVIDENCIA INSUFICIENTE")
    return {"sector_id":sector.get("sector_id"),"sector":sector.get("sector"),"query":sector.get("query"),"sources_validated_format":count,"distinct_domains":diversity,"evidence_score_out_of_100":score,"evidence_level":level,"commercial_demand_validated":False,"profitability_validated":False,"next_checks":["Verificar contenido y fecha de cada fuente","Buscar evidencia directa de demanda de clientes","Estimar costos, competencia e inversión inicial","Validar modelo de ingresos y riesgos"],"sources":valid}
def main():
    if not INPUT.exists(): raise SystemExit("Falta data/multisector_runs.json; ejecutá primero la investigación.")
    runs=json.loads(INPUT.read_text(encoding="utf-8"))
    if not isinstance(runs,list) or not runs: raise SystemExit("El historial está vacío o tiene formato inesperado.")
    latest=runs[-1]; report={"research_started_at":latest.get("started_at"),"evaluated_at":datetime.now(timezone.utc).isoformat(),"method":"documental_transparente_no_rentabilidad","evaluations":sorted([evaluate_sector(s) for s in latest.get("sectors",[])],key=lambda x:x["evidence_score_out_of_100"],reverse=True)}
    previous=[]
    if OUTPUT.exists():
        try:
            previous=json.loads(OUTPUT.read_text(encoding="utf-8"))
            if not isinstance(previous,list): raise ValueError("El informe existente no es una lista")
        except (ValueError,OSError) as exc: raise SystemExit(f"No se sobrescribe el historial: {exc}")
    previous.append(report); tmp=OUTPUT.with_suffix(".json.tmp"); tmp.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); tmp.replace(OUTPUT)
    print("ORION | EVALUACION DOCUMENTAL")
    for e in report["evaluations"]: print(f"{e['sector']}: {e['evidence_score_out_of_100']}/100 | {e['evidence_level']} | {e['distinct_domains']} dominios")
    print("Demanda comercial y rentabilidad: aún no validadas"); print("Informe guardado: data/opportunity_evaluations.json")
if __name__ == "__main__": main()
