import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("forex-poc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized - Forex POC ready")
    yield


app = FastAPI(
    title="Forex Trading Platform API",
    description="""
## SaaS Automated Forex Trading Platform - Client Demo

### Features
- **Authentication**: JWT-based login/register
- **MT5 Connection**: Connect MetaTrader 5 accounts (real or demo)
- **Dashboard**: Real-time account summary, positions, trade history
- **TradingView Webhook**: Receive alerts and auto-execute trades
- **Auto Trading**: Configure and control automated trading bot
- **Activity Logs**: Track all platform events

### Demo Mode
Use "Demo" in broker name or server name to test without a real MT5 terminal.
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import auth, mt5, dashboard, webhook, trades, activity, settings

app.include_router(auth.router)
app.include_router(mt5.router)
app.include_router(dashboard.router)
app.include_router(webhook.router)
app.include_router(trades.router)
app.include_router(activity.router)
app.include_router(settings.router)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
