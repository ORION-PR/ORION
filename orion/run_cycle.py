"""Ciclo integrado de investigación y evaluación de ORION."""
import subprocess
import sys
steps = [[sys.executable, "-m", "orion.multisector_research"], [sys.executable, "-m", "orion.opportunity_evaluator"]]
for step in steps:
    print("\n>>>", " ".join(step), flush=True)
    result = subprocess.run(step, check=False)
    if result.returncode != 0:
        print("Ciclo detenido: una etapa terminó con error.")
        raise SystemExit(result.returncode)
print("\nCICLO ORION COMPLETADO")
print("Revisar: data/multisector_runs.json")
print("Revisar: data/opportunity_evaluations.json")
