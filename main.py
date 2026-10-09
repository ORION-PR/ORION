
import json
import os
from datetime import datetime, timezone
from pathlib import Path

APP_NAME = "ORION"
DATA_DIR = Path(os.getenv("ORION_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = DATA_DIR / "orion_history.json"


def load_history():
    if DB_FILE.exists():
        try:
            return json.loads(DB_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"observations": [], "hypotheses": [], "paper_trades": []}


def save_history(history):
    temporary = DB_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(DB_FILE)


def record_observation(source, topic, evidence, history=None):
    history = history if history is not None else load_history()
    history["observations"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "topic": topic,
        "evidence": evidence,
    })
    save_history(history)
    return history


def record_hypothesis(topic, hypothesis, evidence, history=None):
    history = history if history is not None else load_history()
    history["hypotheses"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "hypothesis": hypothesis,
        "evidence": evidence,
        "status": "pending_validation",
    })
    save_history(history)
    return history


def record_paper_trade(asset, action, amount, price, fee=0.0):
    if amount <= 0 or price <= 0 or fee < 0:
        raise ValueError("Importes, precio y comisión inválidos.")
    history = load_history()
    history["paper_trades"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": asset,
        "action": action,
        "amount": amount,
        "price": price,
        "fee": fee,
        "mode": "PAPER",
    })
    save_history(history)
    return history


def main():
    history = load_history()
    print(f"{APP_NAME} — Observatorio Inteligente de Oportunidades")
    print("Modo: PAPER / investigación sin órdenes reales")
    print(f"Observaciones: {len(history['observations'])}")
    print(f"Hipótesis: {len(history['hypotheses'])}")
    print(f"Registros PAPER: {len(history['paper_trades'])}")
    print("Sistema inicializado correctamente.")


if __name__ == "__main__":
    main()
