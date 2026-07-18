from fastapi import APIRouter, Depends, Query
from repositories.trade_repo import get_trade_history, get_open_trades, get_trade_count, close_trade
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/trades", tags=["Trades"])


@router.get("/history")
def trade_history(user: TokenData = Depends(get_current_user),
                  limit: int = Query(50, ge=1, le=200),
                  offset: int = Query(0, ge=0),
                  symbol: str = Query(""),
                  action: str = Query(""),
                  status: str = Query("")):
    """Get trade history with optional filters and pagination."""
    return get_trade_history(user.user_id, limit, offset, symbol, action, status)


@router.get("/open")
def open_trades(user: TokenData = Depends(get_current_user)):
    """Get currently open trades."""
    return get_open_trades(user.user_id)


@router.get("/count")
def trade_count(user: TokenData = Depends(get_current_user)):
    """Get total trade count."""
    return {"count": get_trade_count(user.user_id)}
