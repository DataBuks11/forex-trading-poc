import logging
from repositories.webhook_repo import log_webhook, update_webhook_status, get_webhook_logs, get_last_webhook
from repositories.settings_repo import get_webhook_secret
from repositories.activity_repo import log_activity
from services.trade_service import execute_trade

logger = logging.getLogger("webhook_service")


def process_webhook(user_id: int, symbol: str, action: str, lot: float,
                    sl: float = 0, tp: float = 0, secret: str = "") -> dict:
    action = action.upper()
    if action not in ("BUY", "SELL"):
        raise ValueError("Action must be BUY or SELL")
    if lot <= 0:
        raise ValueError("Lot size must be positive")
    if not symbol:
        raise ValueError("Symbol is required")

    stored_secret = get_webhook_secret(user_id)
    if stored_secret and secret and secret != stored_secret:
        raise ValueError("Invalid webhook secret")

    log_id = log_webhook(user_id, symbol.upper(), action, lot, sl, tp, "received",
                         f"Signal received: {action} {lot} {symbol}")

    log_activity(user_id, "webhook_received",
                 f"Webhook: {action} {lot} {symbol}",
                 {"symbol": symbol, "action": action, "lot": lot})

    update_webhook_status(log_id, "validating", "Validating payload...")

    try:
        trade_result = execute_trade(user_id, symbol, action, lot, sl, tp, source="webhook")
        if trade_result:
            update_webhook_status(log_id, "executed", "Trade opened successfully",
                                  trade_result.get("ticket"))
            return {
                "status": "success",
                "message": f"{action} {lot} {symbol} executed",
                "ticket": trade_result.get("ticket"),
                "log_id": log_id,
                "steps": ["received", "validating", "executing", "completed"],
            }
        else:
            update_webhook_status(log_id, "failed", "Trade execution returned no result")
            raise RuntimeError("Trade execution failed")
    except Exception as e:
        update_webhook_status(log_id, "failed", str(e))
        raise
