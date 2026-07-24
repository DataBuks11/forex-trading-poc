import logging
import httpx
from datetime import datetime

from repositories.connection_repo import get_connection
from repositories.trade_repo import save_trade, get_trade_history, get_open_trades, get_trade_count
from repositories.settings_repo import get_settings
from repositories.activity_repo import log_activity

logger = logging.getLogger("trade_service")

TIMEOUT = 30


def _get_bridge_url(user_id: int) -> str:
    settings = get_settings(user_id)
    url = settings.get("bridge_url", "").rstrip("/")
    if not url:
        raise RuntimeError(
            "MT5 Bridge not configured. Install and run the MT5 Bridge on your Windows PC, "
            "then enter the bridge URL in Settings."
        )
    return url


def execute_trade(user_id: int, symbol: str, action: str, lot: float,
                  sl: float = 0, tp: float = 0, source: str = "webhook") -> dict | None:
    stored = get_connection(user_id)
    if not stored:
        raise RuntimeError("No MT5 connection found. Please connect first.")

    settings = get_settings(user_id)

    if not settings.get("auto_trading_enabled", 0):
        raise RuntimeError("Auto trading is disabled. Enable it in settings.")

    max_open = settings.get("max_open_trades", 5)
    current_open = len(get_open_trades(user_id))
    if current_open >= max_open:
        raise RuntimeError(f"Maximum open trades limit reached ({max_open}). Close existing trades first.")

    max_lot = settings.get("max_lot_size", 10.0)
    if lot > max_lot:
        raise RuntimeError(f"Lot size {lot} exceeds maximum allowed ({max_lot}).")

    bridge_url = _get_bridge_url(user_id)

    try:
        resp = httpx.post(
            f"{bridge_url}/trade",
            json={
                "symbol": symbol.upper(),
                "action": action.upper(),
                "lot": lot,
                "sl": sl,
                "tp": tp,
            },
            timeout=TIMEOUT,
        )
    except httpx.ConnectError:
        raise RuntimeError(f"Could not reach MT5 Bridge at {bridge_url}. Is the bridge running?")
    except httpx.TimeoutException:
        raise RuntimeError(f"MT5 Bridge at {bridge_url} timed out.")

    if resp.status_code >= 400:
        detail = "Trade execution failed"
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)

    data = resp.json()

    trade_id = save_trade(
        user_id, symbol.upper(), action.upper(), lot, sl, tp,
        data.get("ticket"), data.get("price", 0), source,
        stored.get("broker_name", ""),
    )

    log_activity(user_id, "trade_executed",
                 f"{action.upper()} {lot} {symbol.upper()} @ {data.get('price', 0)}",
                 {"ticket": data.get("ticket"), "symbol": symbol.upper()})

    return {
        "id": trade_id,
        "ticket": data.get("ticket"),
        "symbol": symbol.upper(),
        "action": action.upper(),
        "lot": lot,
        "sl": sl,
        "tp": tp,
        "open_price": data.get("price", 0),
        "status": "OPEN",
    }
