from pydantic import BaseModel
from typing import Optional


class MT5ConnectRequest(BaseModel):
    broker_name: str
    login_id: int
    password: str
    server_name: str
    remember: bool = True


class MT5AccountInfo(BaseModel):
    account_number: int = 0
    broker: str = ""
    balance: float = 0
    equity: float = 0
    margin: float = 0
    free_margin: float = 0
    leverage: int = 0
    currency: str = "USD"
    terminal_version: str = ""
    connection_time: Optional[str] = None
    is_connected: bool = False
    is_demo: bool = False
