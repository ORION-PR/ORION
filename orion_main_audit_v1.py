"""
ORION — Observatorio Inteligente de Oportunidades
MVP educativo de investigación y simulación PAPER. No opera dinero real.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

APP_NAME = "ORION"
DATA_DIR = Path(os.getenv("ORION_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "orion_history.json"
HTTP_TIMEOUT = 12

DEFAULT_HISTORY = {
    "observations": [],
    "hypotheses": [],
    "paper_trades": [],
    "paper_account": {"initial_cash": 500.0, "cash": 500.0, "positions": {}},
    "research_runs": [],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_history() -> dict[str, Any]:
    if not DB_FILE.exists():
        return json.loads(json.dumps(DEFAULT_HISTORY))
    try:
        data = json.loads(DB_FILE.read_text(encoding="utf-8"))
        for key, default in DEFAULT_HISTORY.items():
            if key not in data:
                data[key] = json.loads(json.dumps(default))
        return data
    except (json.JSONDecodeError, OSError) as exc:
        # Do not silently overwrite a potentially recoverable history file.
        raise RuntimeError(
            f"No se pudo leer {DB_FILE}. Conservá el archivo para recuperarlo: {exc}"
        ) from exc


def save_history(history: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="orion_", suffix=".tmp", dir=str(DATA_DIR))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(history, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, DB_FILE)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def record_observation(source: str, topic: str, evidence: Any) -> dict[str, Any]:
    history = load_history()
    record = {
        "timestamp": utc_now(),
        "source": source,
        "topic": topic,
        "evidence": evidence,
    }
    history["observations"].append(record)
    save_history(history)
    return record


def record_hypothesis(topic: str, hypothesis: str, evidence: Any) -> dict[str, Any]:
    history = load_history()
    record = {
        "id": f"H{len(history['hypotheses']) + 1:05d}",
        "timestamp": utc_now(),
        "topic": topic,
        "hypothesis": hypothesis,
        "evidence": evidence,
        "status": "pending_validation",
        "validation": None,
    }
    history["hypotheses"].append(record)
    save_history(history)
    return record


def fetch_crypto_prices(coins: dict[str, str] | None = None) -> dict[str, Any]:
    """
    Consulta CoinGecko y Binance como dos referencias públicas.
    Los símbolos Binance pueden no existir para todos los activos.
    """
    coins = coins or {"bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT"}
    ids = ",".join(coins.keys())
    output: dict[str, Any] = {"timestamp": utc_now(), "assets": {}, "warnings": []}

    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=HTTP_TIMEOUT,
            headers={"accept": "application/json", "user-agent": "ORION-MVP/1.0"},
        )
        response.raise_for_status()
        cg = response.json()
    except (requests.RequestException, ValueError) as exc:
        cg = {}
        output["warnings"].append(f"CoinGecko no disponible: {exc}")

    for coin_id, symbol in coins.items():
        asset = symbol.replace("USDT", "")
        item: dict[str, Any] = {"coingecko_id": coin_id, "symbol": asset}
        if coin_id in cg:
            item["coingecko"] = {
                "price_usd": cg[coin_id].get("usd"),
                "change_24h_pct": cg[coin_id].get("usd_24h_change"),
            }
        else:
            item["coingecko"] = None

        try:
            r = requests.get(
                f"https://api.binance.com/api/v3/ticker/price",
                params={"symbol": symbol},
                timeout=HTTP_TIMEOUT,
                headers={"user-agent": "ORION-MVP/1.0"},
            )
            r.raise_for_status()
            item["binance"] = {"price_usdt": float(r.json()["price"])}
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            item["binance"] = None
            output["warnings"].append(f"Binance {symbol} no disponible: {exc}")

        prices = []
        cg_price = (item.get("coingecko") or {}).get("price_usd")
        bn_price = (item.get("binance") or {}).get("price_usdt")
        if isinstance(cg_price, (int, float)) and cg_price > 0:
            prices.append(float(cg_price))
        if isinstance(bn_price, (int, float)) and bn_price > 0:
            prices.append(float(bn_price))
        item["reference_price_usd"] = sum(prices) / len(prices) if prices else None
        if len(prices) == 2:
            item["price_difference_pct"] = abs(prices[0] - prices[1]) / min(prices) * 100
        else:
            item["price_difference_pct"] = None
        output["assets"][asset] = item

    record_observation("CoinGecko + Binance", "crypto_prices", output)
    history = load_history()
    history["research_runs"].append(output)
    save_history(history)
    return output


def record_paper_trade(
    asset: str,
    action: str,
    amount_usd: float,
    price: float,
    fee_rate: float = 0.006,
) -> dict[str, Any]:
    """
    Registra una compra/venta PAPER con comisión proporcional configurable.
    fee_rate=0.006 equivale a 0,6% por operación; verificar tarifas reales
    de la plataforma antes de usar cualquier comparación.
    """
    action = action.strip().upper()
    asset = asset.strip().upper()
    if action not in {"BUY", "SELL"}:
        raise ValueError("action debe ser BUY o SELL.")
    if not asset or amount_usd <= 0 or price <= 0 or fee_rate < 0 or fee_rate >= 1:
        raise ValueError("Activo, importe, precio o comisión inválidos.")

    history = load_history()
    account = history["paper_account"]
    positions = account.setdefault("positions", {})
    fee = round(amount_usd * fee_rate, 8)
    units = amount_usd / price
    realized_pnl = None

    if action == "BUY":
        total_cost = amount_usd + fee
        if account["cash"] < total_cost:
            raise ValueError(f"Saldo PAPER insuficiente. Disponible: ${account['cash']:.2f}")
        account["cash"] = round(account["cash"] - total_cost, 8)
        position = positions.setdefault(asset, {"units": 0.0, "cost_basis_usd": 0.0})
        position["units"] += units
        position["cost_basis_usd"] += total_cost
    else:
        position = positions.get(asset)
        if not position or position["units"] <= 0:
            raise ValueError(f"No hay posición PAPER disponible en {asset}.")
        units_to_sell = amount_usd / price
        if units_to_sell > position["units"] + 1e-10:
            raise ValueError("La venta supera la cantidad disponible en la posición PAPER.")
        cost_per_unit = position["cost_basis_usd"] / position["units"]
        allocated_cost = cost_per_unit * units_to_sell
        net_proceeds = amount_usd - fee
        realized_pnl = round(net_proceeds - allocated_cost, 8)
        account["cash"] = round(account["cash"] + net_proceeds, 8)
        position["units"] -= units_to_sell
        position["cost_basis_usd"] -= allocated_cost
        if position["units"] < 1e-10:
            positions.pop(asset, None)

    trade = {
        "timestamp": utc_now(),
        "asset": asset,
        "action": action,
        "amount_usd": round(amount_usd, 8),
        "price": price,
        "units": units if action == "BUY" else amount_usd / price,
        "fee_rate": fee_rate,
        "fee_usd": fee,
        "realized_pnl_usd": realized_pnl,
        "mode": "PAPER",
    }
    history["paper_trades"].append(trade)
    save_history(history)
    return trade


def paper_summary(mark_prices: dict[str, float] | None = None) -> dict[str, Any]:
    history = load_history()
    account = history["paper_account"]
    positions = account.get("positions", {})
    mark_prices = mark_prices or {}
    market_value = 0.0
    unpriced_assets = []
    for asset, position in positions.items():
        price = mark_prices.get(asset)
        if isinstance(price, (int, float)) and price > 0:
            market_value += position["units"] * price
        else:
            unpriced_assets.append(asset)

    valuation_complete = not unpriced_assets
    equity = account["cash"] + market_value if valuation_complete else None
    initial_cash = account["initial_cash"]
    return {
        "mode": "PAPER",
        "initial_cash": initial_cash,
        "cash": round(account["cash"], 8),
        "positions": positions,
        "market_value_of_priced_positions": round(market_value, 8),
        "valuation_complete": valuation_complete,
        "equity_usd": round(equity, 8) if equity is not None else None,
        "net_pnl_usd": round(equity - initial_cash, 8) if equity is not None else None,
        "net_pnl_pct": round((equity - initial_cash) / initial_cash * 100, 4) if equity is not None and initial_cash else None,
        "unpriced_assets": unpriced_assets,
        "fees_paid_total": round(sum(t["fee_usd"] for t in history["paper_trades"]), 8),
        "trades": len(history["paper_trades"]),
        "note": "La ganancia/pérdida total solo se informa cuando todas las posiciones tienen precio válido.",
    }


def validate_hypothesis(hypothesis_id: str, status: str, notes: str) -> dict[str, Any]:
    allowed = {"supported", "rejected", "inconclusive"}
    if status not in allowed:
        raise ValueError(f"status debe ser uno de: {', '.join(sorted(allowed))}")
    history = load_history()
    for item in history["hypotheses"]:
        if item["id"] == hypothesis_id:
            item["status"] = status
            item["validation"] = {"timestamp": utc_now(), "notes": notes}
            save_history(history)
            return item
    raise ValueError(f"No se encontró la hipótesis {hypothesis_id}")


def main() -> None:
    history = load_history()
    print(f"{APP_NAME} — Observatorio Inteligente de Oportunidades")
    print("Modo: investigación y simulación PAPER; no opera dinero real.")
    print(f"Archivo de historial: {DB_FILE.resolve()}")
    print(
        f"Observaciones: {len(history['observations'])} | "
        f"Hipótesis: {len(history['hypotheses'])} | "
        f"Operaciones PAPER: {len(history['paper_trades'])}"
    )
    print("Comandos disponibles: python main.py --research | --summary")
    import sys
    if "--research" in sys.argv:
        result = fetch_crypto_prices()
        for asset, info in result["assets"].items():
            print(f"{asset}: referencia USD={info['reference_price_usd']}")
        for warning in result["warnings"]:
            print(f"AVISO: {warning}")
    if "--summary" in sys.argv:
        summary = paper_summary()
        print("Resumen PAPER:")
        print(f"Efectivo: ${summary['cash']:.2f}")
        print(f"Operaciones: {summary['trades']}")
        print(f"Comisiones acumuladas: ${summary['fees_paid_total']:.2f}")
        if summary["valuation_complete"]:
            print(f"Valor total: ${summary['equity_usd']:.2f}")
            print(f"Resultado neto: ${summary['net_pnl_usd']:.2f} ({summary['net_pnl_pct']:.2f}%)")
        else:
            missing = ", ".join(summary["unpriced_assets"])
            print(f"Valor total y resultado neto: pendientes; faltan precios válidos para: {missing}")


if __name__ == "__main__":
    main()
