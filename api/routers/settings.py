from fastapi import APIRouter, Depends
from schemas.dashboard import AutoTradingSettings
from repositories.settings_repo import get_settings, update_settings
from repositories.activity_repo import log_activity
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/settings", tags=["Settings & Auto Trading"])


@router.get("")
def user_settings(user: TokenData = Depends(get_current_user)):
    """Get all user settings including auto-trading configuration."""
    return get_settings(user.user_id)


@router.put("/auto-trading")
def update_auto_trading(data: AutoTradingSettings, user: TokenData = Depends(get_current_user)):
    """Update auto-trading settings and bot status."""
    update_settings(user.user_id, data.model_dump())
    if data.bot_status == "running":
        log_activity(user.user_id, "bot_started", "Auto trading bot started")
    elif data.bot_status == "stopped":
        log_activity(user.user_id, "bot_stopped", "Auto trading bot stopped")
    return {"message": "Settings updated", "status": data.bot_status}


@router.put("")
def update_user_settings(data: dict, user: TokenData = Depends(get_current_user)):
    """Update any user settings."""
    update_settings(user.user_id, data)
    return {"message": "Settings updated"}
