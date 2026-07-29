import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Forex Trading Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VERSION = "2.0.0"


@app.get("/")
def root():
    return {
        "service": "ForexTrade API",
        "status": "online",
        "version": VERSION,
        "documentation": "/docs",
        "health": "/api/health",
    }


@app.get("/api/version")
def api_version():
    return {"version": VERSION}


@app.get("/api/status")
def api_status():
    return {"status": "online", "version": VERSION, "uptime": "operational"}


@app.get("/api/info")
def api_info():
    return {
        "service": "ForexTrade API",
        "version": VERSION,
        "description": "Automated Forex Trading Platform with MT5 integration and TradingView webhook support.",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "endpoints": {
            "auth": "/api/auth",
            "mt5": "/api/mt5",
            "dashboard": "/api/dashboard",
            "webhook": "/api/webhook/tradingview",
            "trades": "/api/trades",
            "activity": "/api/activity",
            "settings": "/api/settings",
        },
    }


@app.get("/api/test-bridge")
def test_bridge(bridge_url: str = ""):
    """Test if the MT5 Bridge is reachable."""
    if not bridge_url:
        from repositories.settings_repo import get_settings
        settings = get_settings(1)  # first user
        bridge_url = settings.get("bridge_url", "")
    if not bridge_url:
        return {"error": "No bridge_url configured"}
    try:
        import httpx
        resp = httpx.get(f"{bridge_url}/health", timeout=10)
        return {"status": resp.status_code, "body": resp.text, "bridge_url": bridge_url}
    except httpx.ConnectError as e:
        return {"error": f"Connection refused: {bridge_url}. Is the bridge running?", "detail": str(e)}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/api/test-connect-error")
def test_connect_error():
    """Test that RuntimeError properly converts to HTTPException."""
    from services.mt5_service import _get_bridge_url, _check_response
    import httpx
    try:
        url = _get_bridge_url(1)
        return {"bridge_url": url}
    except RuntimeError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Bridge not configured: {e}")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e) or type(e).__name__)

@app.get("/api/test-import")
def test_import():
    try:
        from services.mt5_service import _get_bridge_url, _check_response
        return {"mt5_service_import": "ok", "has_get_bridge": True}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@app.get("/api/test-connect-error")
def test_connect_error():
    from services.mt5_service import _get_bridge_url
    from fastapi import HTTPException
    try:
        url = _get_bridge_url(1)
        return {"bridge_url": url}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")

@app.post("/api/debug-connect")
async def debug_connect(req: Request):
    """Debug the connect flow step by step."""
    from fastapi import HTTPException
    data = await req.json()
    try:
        import httpx
        bridge_url = data.get("bridge_url", "")
        resp = httpx.post(f"{bridge_url}/connect", json={
            "broker_name": data.get("broker_name", ""),
            "login_id": data.get("login_id", 0),
            "password": data.get("password", ""),
            "server_name": data.get("server_name", ""),
        }, timeout=30)
        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
        }
    except httpx.ConnectError as e:
        raise HTTPException(status_code=400, detail=f"Connection error: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")

@app.get("/api/health")
def health():
    try:
        import httpx
        httpx_ver = httpx.__version__
    except ImportError:
        httpx_ver = "not-installed"
    return {"status": "ok", "version": VERSION, "httpx": httpx_ver}


from database import init_db
init_db()

from routers.auth import router as auth_router
app.include_router(auth_router)

from routers.mt5 import router as mt5_router
app.include_router(mt5_router)

from routers.dashboard import router as dashboard_router
app.include_router(dashboard_router)

from routers.webhook import router as webhook_router
app.include_router(webhook_router)

from routers.trades import router as trades_router
app.include_router(trades_router)

from routers.activity import router as activity_router
app.include_router(activity_router)

from routers.settings import router as settings_router
app.include_router(settings_router)

from routers.scripts import router as scripts_router
app.include_router(scripts_router)
