from pydantic import BaseModel
from typing import Optional


class DashboardData(BaseModel):
    account: Optional[dict] = None
    open_positions: list = []
    trade_history: list = []
    recent_activity: list = []
    stats: dict = {}


class AutoTradingSettings(BaseModel):
    auto_trading_enabled: bool = False
    default_lot_size: float = 0.01
    risk_percent: float = 1.0
    default_sl: float = 0
    default_tp: float = 0
    max_open_trades: int = 5
    trading_pairs: str = "EURUSD,GBPUSD,USDJPY"
    trading_session: str = "ALL"
    bot_status: str = "stopped"


class WebhookSettings(BaseModel):
    webhook_enabled: bool = True
    webhook_secret: str = ""
    webhook_url: str = ""


class ActivityLogEntry(BaseModel):
    id: int
    event_type: str
    description: str
    metadata: str = "{}"
    created_at: str = ""


class WebhookLogEntry(BaseModel):
    id: int
    symbol: str
    action: str
    lot: float
    status: str
    message: str = ""
    ticket: Optional[int] = None
    received_at: str = ""
    executed_at: Optional[str] = None
