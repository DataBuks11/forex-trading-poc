import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
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


@app.get("/api/health")
def health():
    return {"status": "ok", "version": VERSION}


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
