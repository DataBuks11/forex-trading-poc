import logging
import random
from datetime import datetime

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from config import MT5_DEV, MT5_MAGIC, MT5_TIMEOUT
from repositories.connection_repo import get_connection
from repositories.trade_repo import save_trade, get_trade_history, get_open_trades, get_trade_count
from repositories.activity_repo import log_activity
from services.mt5_service import _init_mt5, _shutdown

logger = logging.getLogger("trade_service")


def execute_trade(user_id: int, symbol: str, action: str, lot: float,
                  sl: float = 0, tp: float = 0, source: str = "webhook") -> dict | None:
    stored = get_connection(user_id)
    if not stored:
        raise RuntimeError("No MT5 connection found. Please connect first.")

    is_demo = stored.get("is_demo", 0)

    if is_demo:
        return _execute_demo(user_id, symbol, action, lot, sl, tp, source, stored)

    if not _init_mt5():
        raise RuntimeError("Failed to initialize MT5")

    try:
        authorized = mt5.login(login=stored["login_id"], password=stored["password"],
                               server=stored["server_name"])
        if not authorized:
            raise RuntimeError("MT5 login failed")

        sym = symbol.upper()
        if not mt5.symbol_select(sym, True):
            raise RuntimeError(f"Symbol {sym} not available")

        tick = mt5.symbol_info_tick(sym)
        if not tick:
            raise RuntimeError(f"No tick data for {sym}")

        if action.upper() == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym,
            "volume": float(lot),
            "type": order_type,
            "price": price,
            "sl": float(sl) if sl else 0,
            "tp": float(tp) if tp else 0,
            "deviation": MT5_DEV,
            "magic": MT5_MAGIC,
            "comment": f"ForexPOC {source}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Order failed: {result.comment}")

        trade_id = save_trade(user_id, sym, action.upper(), lot, sl, tp,
                              result.order, result.price, source,
                              stored.get("broker_name", ""))

        log_activity(user_id, "trade_executed",
                     f"{action} {lot} {sym} @ {result.price}",
                     {"ticket": result.order, "symbol": sym})

        return {
            "id": trade_id, "ticket": result.order, "symbol": sym,
            "action": action.upper(), "lot": lot, "sl": sl, "tp": tp,
            "open_price": result.price, "status": "OPEN",
        }
    finally:
        _shutdown()


def _execute_demo(user_id: int, symbol: str, action: str, lot: float,
                  sl: float, tp: float, source: str, stored: dict) -> dict:
    import random
    sym = symbol.upper()
    open_price = round(random.uniform(1.05, 1.35), 5)
    ticket = random.randint(1000000, 9999999)

    trade_id = save_trade(user_id, sym, action.upper(), lot, sl, tp,
                          ticket, open_price, source,
                          stored.get("broker_name", "Demo Broker"))

    log_activity(user_id, "trade_executed",
                 f"[DEMO] {action} {lot} {sym} @ {open_price}",
                 {"ticket": ticket, "symbol": sym, "demo": True})

    return {
        "id": trade_id, "ticket": ticket, "symbol": sym,
        "action": action.upper(), "lot": lot, "sl": sl, "tp": tp,
        "open_price": open_price, "status": "OPEN",
    }
