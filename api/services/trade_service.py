import logging
from datetime import datetime

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from config import MT5_DEV, MT5_MAGIC, MT5_TIMEOUT, MAX_LOT_SIZE
from repositories.connection_repo import get_connection
from repositories.trade_repo import save_trade, get_trade_history, get_open_trades, get_trade_count
from repositories.settings_repo import get_settings
from repositories.activity_repo import log_activity
from services.mt5_service import _init_mt5, _shutdown

logger = logging.getLogger("trade_service")


def execute_trade(user_id: int, symbol: str, action: str, lot: float,
                  sl: float = 0, tp: float = 0, source: str = "webhook") -> dict | None:
    stored = get_connection(user_id)
    if not stored:
        raise RuntimeError("No MT5 connection found. Please connect first.")

    if not HAS_MT5:
        raise RuntimeError("MetaTrader 5 terminal is not installed. Please install MT5 from your broker.")

    settings = get_settings(user_id)

    if not settings.get("auto_trading_enabled", 0):
        raise RuntimeError("Auto trading is disabled. Enable it in settings.")

    max_open = settings.get("max_open_trades", 5)
    current_open = len(get_open_trades(user_id))
    if current_open >= max_open:
        raise RuntimeError(f"Max open trades limit reached ({max_open}). Close existing trades first.")

    max_lot = settings.get("max_lot_size", MAX_LOT_SIZE)
    if lot > max_lot:
        raise RuntimeError(f"Lot size {lot} exceeds max allowed ({max_lot}).")

    if not _init_mt5():
        error = mt5.last_error()
        raise RuntimeError(f"Failed to initialize MT5: {error}")

    try:
        authorized = mt5.login(login=stored["login_id"], password=stored["password"],
                               server=stored["server_name"])
        if not authorized:
            error = mt5.last_error()
            raise RuntimeError(f"MT5 login failed: {error}")

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
            "comment": f"ForexTrade {source}",
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
