from pydantic import BaseModel
from typing import Optional


class TradeWebhookPayload(BaseModel):
    symbol: str
    action: str
    lot: float = 0.01
    sl: Optional[float] = None
    tp: Optional[float] = None
    secret: Optional[str] = None


class TradeRecord(BaseModel):
    id: int
    symbol: str
    action: str
    lot: float
    sl: float = 0
    tp: float = 0
    ticket: Optional[int] = None
    open_price: float = 0
    close_price: float = 0
    profit: float = 0
    swap: float = 0
    commission: float = 0
    status: str = "OPEN"
    source: str = "webhook"
    broker: str = ""
    created_at: str = ""
    closed_at: Optional[str] = None
