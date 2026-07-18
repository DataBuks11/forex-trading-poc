from fastapi import APIRouter, Depends, Query
from services.mt5_service import get_account_status, get_open_positions
from services.trade_service import get_trade_history, get_open_trades, get_trade_count
from repositories.activity_repo import get_activity_logs
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(user: TokenData = Depends(get_current_user)):
    """Get complete dashboard data: account info, positions, trade history, activity."""
    account = get_account_status(user.user_id)
    positions = get_open_positions(user.user_id)
    history = get_trade_history(user.user_id, limit=20)
    activity = get_activity_logs(user.user_id, limit=10)
    total_trades = get_trade_count(user.user_id)
    open_count = len(get_open_trades(user.user_id))

    profit_today = sum(t.get("profit", 0) for t in get_trade_history(user.user_id, limit=100)
                       if t.get("status") == "CLOSED")

    return {
        "account": account,
        "open_positions": positions,
        "trade_history": history,
        "recent_activity": activity,
        "stats": {
            "total_trades": total_trades,
            "open_positions": open_count,
            "win_rate": 0,
            "profit_today": round(profit_today, 2),
        },
    }
