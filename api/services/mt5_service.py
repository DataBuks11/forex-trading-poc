import logging
from datetime import datetime

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from config import MT5_DEV, MT5_MAGIC, MT5_TIMEOUT
from repositories.connection_repo import save_connection, get_connection, disconnect, update_account_info
from repositories.activity_repo import log_activity

logger = logging.getLogger("mt5_service")


def _init_mt5() -> bool:
    if not HAS_MT5:
        return False
    if not mt5.initialize():
        logger.error(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True


def _shutdown():
    if HAS_MT5:
        mt5.shutdown()


def connect_account(user_id: int, broker_name: str, login_id: int, password: str,
                    server_name: str) -> dict:
    if not HAS_MT5 or not _init_mt5():
        error_msg = mt5.last_error() if HAS_MT5 else None
        detail = "MetaTrader 5 terminal is not installed. Please install MT5 from your broker."
        if error_msg:
            detail = f"MT5 initialization failed: {error_msg}"
        raise RuntimeError(detail)

    try:
        authorized = mt5.login(login=login_id, password=password, server=server_name)
        if not authorized:
            error = mt5.last_error()
            raise ValueError(f"Login failed: {error}")

        info = mt5.account_info()
        if not info:
            raise ValueError("Could not fetch account information")

        terminal = mt5.terminal_info()
        tv = f"Build {terminal.build}" if terminal else ""

        account_type = "demo" if info.trade_mode == 0 else "live"

        account_data = {
            "account_number": info.login,
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free if hasattr(info, 'margin_free') else info.balance - info.margin,
            "leverage": info.leverage,
            "currency": info.currency,
            "terminal_version": tv,
            "connection_time": datetime.utcnow().isoformat(),
        }

        save_connection(user_id, broker_name, login_id, password, server_name, account_data, account_type)
        log_activity(user_id, "broker_connected", f"Connected to {broker_name} ({server_name})")
    finally:
        _shutdown()

    account_data["broker"] = broker_name
    account_data["is_connected"] = True
    account_data["account_type"] = account_type
    return account_data


def get_account_status(user_id: int) -> dict | None:
    stored = get_connection(user_id)
    if not stored:
        return None

    if not HAS_MT5 or not _init_mt5():
        return {
            "account_number": stored["account_number"],
            "broker": stored["broker_name"],
            "balance": stored["balance"],
            "equity": stored["equity"],
            "margin": stored["margin"],
            "free_margin": stored["free_margin"],
            "leverage": stored["leverage"],
            "currency": stored["currency"],
            "terminal_version": stored.get("terminal_version", ""),
            "connection_time": stored.get("connection_time", ""),
            "is_connected": True,
            "account_type": stored.get("account_type", ""),
        }

    try:
        authorized = mt5.login(login=stored["login_id"], password=stored["password"], server=stored["server_name"])
        if not authorized:
            disconnect(user_id)
            return None
        info = mt5.account_info()
        if not info:
            return None

        account_type = "demo" if info.trade_mode == 0 else "live"

        result = {
            "account_number": info.login,
            "broker": stored["broker_name"],
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free if hasattr(info, 'margin_free') else info.balance - info.margin,
            "leverage": info.leverage,
            "currency": info.currency,
            "terminal_version": stored.get("terminal_version", ""),
            "connection_time": stored.get("connection_time", ""),
            "is_connected": True,
            "account_type": account_type,
        }
        update_account_info(user_id, result)
        return result
    finally:
        _shutdown()


def get_open_positions(user_id: int) -> list:
    stored = get_connection(user_id)
    if not stored:
        return []

    if not HAS_MT5 or not _init_mt5():
        return []

    try:
        authorized = mt5.login(login=stored["login_id"], password=stored["password"], server=stored["server_name"])
        if not authorized:
            return []
        positions = mt5.positions_get()
        if not positions:
            return []
        result = []
        for pos in positions:
            result.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == 0 else "SELL",
                "volume": pos.volume,
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "swap": pos.swap,
                "commission": pos.commission,
                "open_time": str(pos.time) if pos.time else "",
                "comment": pos.comment or "",
            })
        return result
    finally:
        _shutdown()


def disconnect_account(user_id: int):
    disconnect(user_id)
    log_activity(user_id, "broker_disconnected", "MT5 disconnected")
    _shutdown()
