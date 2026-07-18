from fastapi import APIRouter, HTTPException, Depends, Query
from schemas.trade import TradeWebhookPayload
from services.webhook_service import process_webhook
from repositories.webhook_repo import get_webhook_logs, get_last_webhook
from repositories.settings_repo import get_settings, regenerate_secret, update_settings
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/webhook", tags=["TradingView Webhook"])


@router.post("/tradingview")
def tradingview_webhook(payload: TradeWebhookPayload):
    """Receive TradingView alerts. Executes trades on the connected MT5 account.
    
    Currently uses user_id=1 for webhook routing. Pass secret for security.
    """
    try:
        result = process_webhook(
            user_id=1,
            symbol=payload.symbol,
            action=payload.action,
            lot=payload.lot,
            sl=payload.sl or 0,
            tp=payload.tp or 0,
            secret=payload.secret or "",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def webhook_history(user: TokenData = Depends(get_current_user),
                    limit: int = Query(50, ge=1, le=200)):
    """Get webhook signal history."""
    return get_webhook_logs(user.user_id, limit)


@router.get("/last-signal")
def last_signal(user: TokenData = Depends(get_current_user)):
    """Get the most recent webhook signal."""
    return get_last_webhook(user.user_id)


@router.get("/settings")
def webhook_settings(user: TokenData = Depends(get_current_user)):
    """Get webhook configuration including URL and secret."""
    settings = get_settings(user.user_id)
    return {
        "webhook_enabled": settings.get("webhook_enabled", 1),
        "webhook_secret": settings.get("webhook_secret", ""),
        "webhook_url": "http://127.0.0.1:8000/api/webhook/tradingview",
    }


@router.post("/settings")
def update_webhook_settings(data: dict, user: TokenData = Depends(get_current_user)):
    """Update webhook settings."""
    update_settings(user.user_id, data)
    return {"message": "Settings updated"}


@router.post("/regenerate-secret")
def regen_secret(user: TokenData = Depends(get_current_user)):
    """Generate a new webhook secret key."""
    secret = regenerate_secret(user.user_id)
    return {"webhook_secret": secret}


@router.post("/test")
def test_webhook(user: TokenData = Depends(get_current_user)):
    """Simulate a TradingView webhook signal from the UI.
    
    Sends a test BUY order for EURUSD with 0.01 lot.
    """
    try:
        result = process_webhook(
            user_id=user.user_id,
            symbol="EURUSD",
            action="BUY",
            lot=0.01,
            sl=1.0800,
            tp=1.1200,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
