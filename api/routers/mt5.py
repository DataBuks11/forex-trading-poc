from fastapi import APIRouter, HTTPException, Depends
from schemas.mt5 import MT5ConnectRequest, MT5AccountInfo
from services.mt5_service import connect_account, get_account_status, disconnect_account, get_open_positions
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/mt5", tags=["MT5 Connection"])


@router.post("/connect", response_model=MT5AccountInfo)
def mt5_connect(payload: MT5ConnectRequest, user: TokenData = Depends(get_current_user)):
    """Connect to MetaTrader 5 account with real broker credentials."""
    try:
        result = connect_account(user.user_id, payload.broker_name,
                                 payload.login_id, payload.password, payload.server_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=MT5AccountInfo)
def mt5_status(user: TokenData = Depends(get_current_user)):
    """Get current MT5 connection status and account information."""
    info = get_account_status(user.user_id)
    if not info:
        return MT5AccountInfo(is_connected=False)
    return info


@router.post("/disconnect")
def mt5_disconnect(user: TokenData = Depends(get_current_user)):
    """Disconnect from MT5 account."""
    disconnect_account(user.user_id)
    return {"message": "Disconnected successfully"}


@router.post("/test")
def mt5_test_connection(payload: MT5ConnectRequest, user: TokenData = Depends(get_current_user)):
    """Test MT5 connection without saving credentials."""
    try:
        result = connect_account(user.user_id, payload.broker_name,
                                 payload.login_id, payload.password, payload.server_name)
        return {"success": True, "account": result}
    except (ValueError, RuntimeError) as e:
        return {"success": False, "error": str(e)}


@router.get("/positions")
def mt5_positions(user: TokenData = Depends(get_current_user)):
    """Get current open positions from MT5."""
    return get_open_positions(user.user_id)
