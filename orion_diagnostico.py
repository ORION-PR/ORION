#!/usr/bin/env python3
# ORION — Diagnóstico integral, de solo lectura
# Uso desde la raíz del repositorio:
#   python3 orion_diagnostico.py
# No modifica archivos ni realiza operaciones financieras.

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FILES = {
    "investigaciones": DATA / "multisector_runs.json",
    "evaluaciones": DATA / "opportunity_evaluations.json",
    "investigacion_detallada": DATA / "orion_research.json",
    "resumen": DATA / "ORION_RESUMEN_DIARIO.md",
}
SECTORES_ESPERADOS = {
    "inteligencia artificial", "tecnologia", "negocios digitales",
    "videojuegos", "criptoactivos",
}

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

def parse_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def age_hours(value):
    dt = parse_date(value)
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600, 1)

def latest_list_record(value):
    if isinstance(value, list) and value:
        return value[-1]
    return None

def domain_of(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def report(status, title, detail=""):
    print(f"[{status}] {title}" + (f" — {detail}" if detail else ""))

def main():
    print("=" * 64)
    print("ORION — DIAGNÓSTICO INTEGRAL (solo lectura)")
    print("Fecha UTC:", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    print("=" * 64)
    problems = 0
    warnings = 0

    loaded = {}
    for key, path in FILES.items():
        if not path.exists():
            report("ERROR", f"Falta {path.relative_to(ROOT)}")
            problems += 1
            loaded[key] = None
            continue
        if path.stat().st_size == 0:
            report("ERROR", f"Archivo vacío: {path.relative_to(ROOT)}")
            problems += 1
            loaded[key] = None
            continue
        if key == "resumen":
            loaded[key] = path.read_text(encoding="utf-8", errors="replace")
            report("OK", f"{path.relative_to(ROOT)}", f"{path.stat().st_size} bytes")
        else:
            result = read_json(path)
            if isinstance(result, tuple) and len(result) == 2 and result[0] is None:
                report("ERROR", f"JSON inválido: {path.relative_to(ROOT)}", result[1])
                problems += 1
                loaded[key] = None
            else:
                loaded[key] = result
                report("OK", f"JSON válido: {path.relative_to(ROOT)}", f"{path.stat().st_size} bytes")

    runs = loaded.get("investigaciones")
    latest_run = latest_list_record(runs)
    if latest_run:
        started = latest_run.get("started_at")
        sectors = latest_run.get("sectors", [])
        sector_names = {
            str(s.get("sector", "")).strip().lower()
            for s in sectors if isinstance(s, dict)
        }
        total_sources = sum(
            int(s.get("sources_found", 0) or 0)
            for s in sectors if isinstance(s, dict)
        )
        run_age = age_hours(started)
        report("INFO", "Última investigación", f"fecha={started}; edad_h={run_age}; sectores={len(sectors)}; fuentes={total_sources}")
        if run_age is None:
            report("AVISO", "No se pudo interpretar started_at de la última investigación")
            warnings += 1
        elif run_age > 30:
            report("AVISO", "Investigación posiblemente desactualizada", f"{run_age} horas")
            warnings += 1
        missing = sorted(SECTORES_ESPERADOS - sector_names)
        if missing:
            report("AVISO", "Sectores esperados ausentes", ", ".join(missing))
            warnings += 1
        else:
            report("OK", "Están presentes los cinco sectores esperados")
        for sector in sectors:
            if not isinstance(sector, dict):
                continue
            name = sector.get("sector", sector.get("sector_id", "sector sin nombre"))
            n = sector.get("sources_found", 0)
            err = sector.get("error")
            if err:
                report("ERROR", f"Sector {name}", f"error={err}")
                problems += 1
            elif not n:
                report("AVISO", f"Sector {name}", "cero fuentes encontradas")
                warnings += 1
    elif runs is not None:
        report("ERROR", "El historial multisector está vacío o no es una lista")
        problems += 1

    evaluations = loaded.get("evaluaciones")
    latest_eval = latest_list_record(evaluations)
    if latest_eval:
        evaluated = latest_eval.get("evaluated_at")
        items = latest_eval.get("evaluations", [])
        eval_age = age_hours(evaluated)
        report("INFO", "Última evaluación", f"fecha={evaluated}; edad_h={eval_age}; sectores_evaluados={len(items)}")
        if eval_age is None:
            report("AVISO", "No se pudo interpretar evaluated_at")
            warnings += 1
        elif eval_age > 30:
            report("AVISO", "Evaluaciones posiblemente desactualizadas", f"{eval_age} horas")
            warnings += 1
        for item in items:
            if not isinstance(item, dict):
                continue
            sector = item.get("sector", item.get("sector_id", "sin nombre"))
            score = item.get("evidence_score_out_of_100")
            domains = item.get("distinct_domains")
            demand = item.get("commercial_demand_validated")
            profit = item.get("profitability_validated")
            report("INFO", f"Evaluación: {sector}", f"puntaje_documental={score}; dominios={domains}; demanda_validada={demand}; rentabilidad_validada={profit}")
            if demand is not True or profit is not True:
                warnings += 1
        if not items:
            report("ERROR", "La última evaluación no contiene evaluaciones")
            problems += 1
    elif evaluations is not None:
        report("ERROR", "El historial de evaluaciones está vacío o no es una lista")
        problems += 1

    research = loaded.get("investigacion_detallada")
    if isinstance(research, dict):
        investigations = research.get("investigations", [])
        last = latest_list_record(investigations)
        if last:
            saved = last.get("saved_at")
            results = last.get("results", [])
            domains = {domain_of(r.get("url", "")) for r in results if isinstance(r, dict)}
            domains.discard("")
            report("INFO", "Investigación detallada más reciente", f"fecha={saved}; edad_h={age_hours(saved)}; resultados={len(results)}; dominios_unicos={len(domains)}")
            if age_hours(saved) is not None and age_hours(saved) > 30:
                report("AVISO", "La investigación detallada podría estar desactualizada")
                warnings += 1
        else:
            report("AVISO", "orion_research.json no contiene investigaciones")
            warnings += 1

    summary = loaded.get("resumen")
    if isinstance(summary, str):
        summary_lower = summary.lower()
        if not summary.strip():
            report("ERROR", "El resumen diario está vacío")
            problems += 1
        else:
            for sector in sorted(SECTORES_ESPERADOS):
                if sector not in summary_lower:
                    report("AVISO", "El resumen no menciona un sector", sector)
                    warnings += 1
            if "puntaje documental" in summary_lower and "rentabilidad comprobada" in summary_lower:
                report("OK", "El resumen distingue evaluación documental de rentabilidad comprobada")
            if latest_eval and latest_eval.get("evaluated_at"):
                eval_date = parse_date(latest_eval.get("evaluated_at"))
                if eval_date:
                    date_text = eval_date.strftime("%d/%m/%Y")
                    if date_text not in summary:
                        report("AVISO", "La fecha de evaluación no aparece claramente en el resumen", date_text)
                        warnings += 1

    print("-" * 64)
    if problems:
        print(f"RESULTADO: {problems} error(es), {warnings} aviso(s). Revisar primero los errores.")
        return 1
    if warnings:
        print(f"RESULTADO: sin errores estructurales detectados; {warnings} aviso(s) requieren atención.")
        return 0
    print("RESULTADO: no se detectaron errores en las comprobaciones incluidas.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
