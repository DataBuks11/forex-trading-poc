import logging
from datetime import datetime
from typing import Optional

import MetaTrader5 as mt5

from config import MT5_DEV, MT5_MAGIC, MT5_TIMEOUT
from repositories.connection_repo import save_connection, get_connection, disconnect, update_account_info
from repositories.activity_repo import log_activity

logger = logging.getLogger("mt5_service")

_demo_cache: dict = {}


def _init_mt5() -> bool:
    if not mt5.initialize():
        logger.error(f"MT5 init failed: {mt5.last_error()}")
        return False
    return True


def _shutdown():
    mt5.shutdown()


def connect_account(user_id: int, broker_name: str, login_id: int, password: str,
                    server_name: str) -> dict:
    is_demo = "demo" in broker_name.lower() or "demo" in server_name.lower()

    if is_demo:
        return _connect_demo(user_id, broker_name, login_id, server_name)

    if not _init_mt5():
        raise RuntimeError("Failed to initialize MT5. Is MetaTrader 5 installed?")

    try:
        authorized = mt5.login(login=login_id, password=password, server=server_name)
        if not authorized:
            error = mt5.last_error()
            raise ValueError(f"Login failed: {error}")

        info = mt5.account_info()
        if not info:
            raise ValueError("Could not fetch account info")

        terminal = mt5.terminal_info()
        tv = f"Build {terminal.build}" if terminal else ""

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

        save_connection(user_id, broker_name, login_id, password, server_name, account_data)
        log_activity(user_id, "broker_connected", f"Connected to {broker_name} ({server_name})")
    finally:
        _shutdown()

    account_data["broker"] = broker_name
    account_data["is_connected"] = True
    account_data["is_demo"] = is_demo
    return account_data


def _connect_demo(user_id: int, broker_name: str, login_id: int, server_name: str) -> dict:
    import random
    balance = round(random.uniform(5000, 50000), 2)
    equity = round(balance * random.uniform(0.98, 1.02), 2)
    margin = round(balance * random.uniform(0.05, 0.15), 2)

    account_data = {
        "account_number": login_id,
        "balance": balance,
        "equity": equity,
        "margin": margin,
        "free_margin": round(equity - margin, 2),
        "leverage": random.choice([100, 200, 500]),
        "currency": "USD",
        "terminal_version": "Build 4380 (Demo Mode)",
        "connection_time": datetime.utcnow().isoformat(),
        "broker": broker_name,
        "is_connected": True,
        "is_demo": True,
    }

    save_connection(user_id, broker_name, login_id, "demo_pwd", server_name, account_data)
    _demo_cache[user_id] = account_data
    log_activity(user_id, "broker_connected", f"[DEMO] Connected to {broker_name} ({server_name})")
    return account_data


def get_account_status(user_id: int) -> dict | None:
    stored = get_connection(user_id)
    if not stored:
        return None

    is_demo = stored.get("is_demo", 0)

    if is_demo:
        if user_id in _demo_cache:
            cached = _demo_cache[user_id]
            import random
            cached["equity"] = round(cached["balance"] * random.uniform(0.97, 1.03), 2)
            cached["free_margin"] = round(cached["equity"] - cached["margin"], 2)
            return {
                "account_number": cached["account_number"],
                "broker": cached["broker"],
                "balance": cached["balance"],
                "equity": cached["equity"],
                "margin": cached["margin"],
                "free_margin": cached["free_margin"],
                "leverage": cached["leverage"],
                "currency": cached["currency"],
                "terminal_version": cached["terminal_version"],
                "connection_time": cached["connection_time"],
                "is_connected": True,
                "is_demo": True,
            }
        return None

    if not _init_mt5():
        return None

    try:
        authorized = mt5.login(login=stored["login_id"], password=stored["password"], server=stored["server_name"])
        if not authorized:
            disconnect(user_id)
            return None
        info = mt5.account_info()
        if not info:
            return None

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
            "is_demo": False,
        }
        update_account_info(user_id, result)
        return result
    finally:
        _shutdown()


def get_open_positions(user_id: int) -> list:
    stored = get_connection(user_id)
    if not stored:
        return []

    is_demo = stored.get("is_demo", 0)
    if is_demo:
        import random
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        positions = []
        for i in range(random.randint(0, 3)):
            symbol = random.choice(symbols)
            action = random.choice(["BUY", "SELL"])
            open_p = round(random.uniform(1.05, 1.35), 5)
            positions.append({
                "ticket": random.randint(1000000, 9999999),
                "symbol": symbol,
                "type": action,
                "volume": round(random.uniform(0.01, 0.5), 2),
                "open_price": open_p,
                "current_price": round(open_p * random.uniform(0.995, 1.005), 5),
                "sl": round(open_p * 0.99, 5) if action == "BUY" else round(open_p * 1.01, 5),
                "tp": round(open_p * 1.02, 5) if action == "BUY" else round(open_p * 0.98, 5),
                "profit": round(random.uniform(-50, 100), 2),
                "swap": round(random.uniform(-2, 0), 2),
                "commission": round(random.uniform(-1, 0), 2),
                "open_time": datetime.utcnow().isoformat(),
                "comment": "Demo Trade",
            })
        return positions

    if not _init_mt5():
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
    _demo_cache.pop(user_id, None)
    log_activity(user_id, "broker_disconnected", "MT5 disconnected")
    _shutdown()
