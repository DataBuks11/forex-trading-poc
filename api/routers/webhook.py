import os
from fastapi import APIRouter, HTTPException, Depends, Query, Header, Request
from schemas.trade import TradeWebhookPayload
from services.webhook_service import process_webhook
from repositories.webhook_repo import get_webhook_logs, get_last_webhook
from repositories.settings_repo import get_settings, regenerate_secret, update_settings, get_webhook_secret
from repositories.user_repo import get_user_by_id
from middleware import get_current_user, TokenData
from config import API_DOMAIN

router = APIRouter(prefix="/api/webhook", tags=["TradingView Webhook"])


def _resolve_user_from_secret(secret: str) -> int | None:
    if not secret:
        return None
    from database import get_db
    db = get_db()
    try:
        row = db.execute("SELECT user_id FROM settings WHERE webhook_secret=? AND webhook_enabled=1",
                         (secret,)).fetchone()
        if row:
            return row["user_id"]
        return None
    finally:
        db.close()


@router.post("/tradingview")
def tradingview_webhook(payload: TradeWebhookPayload, request: Request):
    """Receive TradingView alerts. Requires a valid webhook secret via query param or header."""
    secret = payload.secret or request.query_params.get("secret") or request.headers.get("X-Webhook-Secret", "")

    if not secret:
        raise HTTPException(status_code=401, detail="Webhook secret is required. Provide via payload.secret, ?secret=, or X-Webhook-Secret header.")

    user_id = _resolve_user_from_secret(secret)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or disabled webhook secret.")


@router.get("/tradingview")
def tradingview_webhook_info():
    """Informational endpoint for the TradingView webhook."""
    return {
        "service": "TradingView Webhook",
        "status": "active",
        "method": "POST",
        "message": "This endpoint accepts TradingView webhook POST requests only.",
    }

    try:
        result = process_webhook(
            user_id=user_id,
            symbol=payload.symbol,
            action=payload.action,
            lot=payload.lot,
            sl=payload.sl or 0,
            tp=payload.tp or 0,
            secret=secret,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Trade execution failed. Check logs for details.")


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
        "webhook_url": f"https://{API_DOMAIN}/api/webhook/tradingview",
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
    """Send a test BUY order for EURUSD with 0.01 lot via authenticated user."""
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
        raise HTTPException(status_code=500, detail="Trade execution failed. Check logs for details.")
