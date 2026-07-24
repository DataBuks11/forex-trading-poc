"""
MT5 Bridge Service - Windows Local Bridge
=========================================
This service runs on your Windows PC alongside MetaTrader 5.
It provides a REST API that the Vercel backend proxies to.

Run: python bridge.py
Default port: 8765
"""

import logging
import os
import sys
import json
import traceback
import platform as _platform
from datetime import datetime
from pathlib import Path
from typing import Optional

import MetaTrader5 as mt5
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | MT5-Bridge | %(levelname)s | %(message)s",
)
logger = logging.getLogger("mt5-bridge")

BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", "8765"))
BRIDGE_TOKEN = os.environ.get("BRIDGE_TOKEN", "mt5-bridge-default-token-change-me")

app = FastAPI(title="MT5 Bridge Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_active_connection: Optional[dict] = None


# ── Models ──────────────────────────────────────────────────────────────

class ConnectRequest(BaseModel):
    broker_name: str
    login_id: int
    password: str
    server_name: str

class TradeRequest(BaseModel):
    symbol: str
    action: str
    lot: float = 0.01
    sl: float = 0
    tp: float = 0

class ModifySLTPRequest(BaseModel):
    ticket: int
    sl: float = 0
    tp: float = 0


# ── Security check ──────────────────────────────────────────────────────

def _check_token(token: str | None = None):
    if token != BRIDGE_TOKEN and BRIDGE_TOKEN != "mt5-bridge-default-token-change-me":
        raise HTTPException(status_code=401, detail="Invalid bridge token")


# ── MT5 Discovery / Diagnostics ─────────────────────────────────────────

COMMON_MT5_PATHS = [
    r"C:\Program Files\MetaTrader 5\terminal64.exe",
    r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    r"C:\Program Files\MetaTrader 5\terminal.exe",
    r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
    os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal"),
    os.path.expandvars(r"%LOCALAPPDATA%\MetaQuotes\Terminal"),
    os.path.expandvars(r"%PROGRAMDATA%\MetaQuotes\Terminal"),
]


def _find_mt5_terminals() -> list[dict]:
    """Scan common paths and find installed MT5 terminals."""
    found = []
    for path in COMMON_MT5_PATHS:
        p = Path(path)
        if p.exists():
            if p.is_file():
                found.append({"path": str(p), "type": "terminal", "exists": True})
            else:
                found.append({"path": str(p), "type": "folder", "exists": True})
    # Also check subfolders for terminal64.exe
    for base in [Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")]:
        try:
            for d in base.glob("MetaTrader*"):
                for exe in d.glob("terminal*.exe"):
                    found.append({"path": str(exe), "type": "terminal", "exists": True})
        except Exception:
            pass
    return found


@app.get("/diagnostics")
def diagnostics():
    """Full system and MT5 diagnostics."""
    result = {
        "system": {
            "os": _platform.system(),
            "os_version": _platform.version(),
            "architecture": _platform.architecture(),
            "python_version": sys.version,
            "python_arch": _platform.machine(),
            "python_executable": sys.executable,
            "cwd": os.getcwd(),
            "bridge_port": BRIDGE_PORT,
        },
        "mt5_import": {
            "available": True,
            "library_version": mt5.__version__,
        },
        "mt5_terminals_found": _find_mt5_terminals(),
        "mt5_initialize": {},
        "mt5_terminal_info": {},
        "mt5_account_info": {},
        "mt5_connection": {},
    }

    # Try to initialize and gather MT5 info
    if mt5.initialize():
        result["mt5_initialize"]["status"] = True
        result["mt5_initialize"]["message"] = "MT5 initialized successfully"

        ti = mt5.terminal_info()
        if ti:
            result["mt5_terminal_info"] = {
                "community_account": ti.community_account,
                "community_connection": ti.community_connection,
                "connected": ti.connected,
                "dlls_allowed": ti.dlls_allowed,
                "trade_allowed": ti.trade_allowed,
                "tradeapi_disabled": ti.tradeapi_disabled,
                "email_enabled": ti.email_enabled,
                "ftp_enabled": ti.ftp_enabled,
                "notifications_enabled": ti.notifications_enabled,
                "mqid": ti.mqid,
                "build": ti.build,
                "maxbars": ti.maxbars,
                "codepage": ti.codepage,
                "ping_last": ti.ping_last,
                "community_balance": ti.community_balance,
                "retransmission": ti.retransmission,
                "path": ti.path,
                "data_path": ti.data_path,
                "commondata_path": ti.commondata_path,
            }

        ai = mt5.account_info()
        if ai:
            result["mt5_account_info"] = {
                "login": ai.login,
                "trade_mode": "demo" if ai.trade_mode == 0 else "live",
                "leverage": ai.leverage,
                "limit_orders": ai.limit_orders,
                "margin_so_mode": ai.margin_so_mode,
                "trade_allowed": ai.trade_allowed,
                "trade_expert": ai.trade_expert,
                "margin_mode": ai.margin_mode,
                "currency_digits": ai.currency_digits,
                "fifo_close": ai.fifo_close,
                "balance": ai.balance,
                "credit": ai.credit,
                "profit": ai.profit,
                "equity": ai.equity,
                "margin": ai.margin,
                "margin_free": ai.margin_free,
                "margin_level": ai.margin_level,
                "margin_so_call": ai.margin_so_call,
                "margin_so_so": ai.margin_so_so,
                "margin_initial": ai.margin_initial,
                "margin_maintenance": ai.margin_maintenance,
                "assets": ai.assets,
                "liabilities": ai.liabilities,
                "commission_blocked": ai.commission_blocked,
                "name": ai.name,
                "server": ai.server,
                "currency": ai.currency,
                "company": ai.company,
            }
        else:
            result["mt5_account_info"]["error"] = str(mt5.last_error())

        # If connected, get connection info
        if result["mt5_terminal_info"].get("connected", False):
            result["mt5_connection"]["status"] = "Terminal is connected to broker"
        else:
            result["mt5_connection"]["status"] = "Terminal is NOT connected to broker"
            result["mt5_connection"]["message"] = "Open MT5, log in to your broker account, then try again."

        mt5.shutdown()
    else:
        result["mt5_initialize"]["status"] = False
        result["mt5_initialize"]["error_code"] = mt5.last_error()
        result["mt5_initialize"]["message"] = str(mt5.last_error())

    return result


# ── MT5 Connection ──────────────────────────────────────────────────────

@app.post("/connect")
def connect(req: ConnectRequest, token: str | None = None):
    """Connect to an MT5 account."""
    _check_token(token)
    global _active_connection

    if not mt5.initialize():
        err = mt5.last_error()
        raise HTTPException(
            status_code=500,
            detail=f"MT5 initialization failed: {err}. Is MT5 terminal running?",
        )

    authorized = mt5.login(
        login=req.login_id,
        password=req.password,
        server=req.server_name,
    )

    if not authorized:
        err = mt5.last_error()
        mt5.shutdown()
        raise HTTPException(
            status_code=400,
            detail=f"MT5 login failed: {err}. Check your credentials and server name.",
        )

    account_info = mt5.account_info()
    terminal_info = mt5.terminal_info()

    if not account_info:
        mt5.shutdown()
        raise HTTPException(status_code=500, detail="Failed to retrieve account information from MT5.")

    _active_connection = {
        "broker_name": req.broker_name,
        "login_id": req.login_id,
        "server_name": req.server_name,
        "account_number": account_info.login,
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin": account_info.margin,
        "free_margin": account_info.margin_free,
        "leverage": account_info.leverage,
        "currency": account_info.currency,
        "company": account_info.company or req.broker_name,
        "account_type": "live" if account_info.trade_mode != 0 else "demo",
        "terminal_build": terminal_info.build if terminal_info else 0,
        "terminal_path": terminal_info.path if terminal_info else "",
        "connected_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Connected: {account_info.login} on {req.server_name}")

    return {
        "status": "connected",
        "account": _active_connection,
    }


@app.post("/disconnect")
def disconnect(token: str | None = None):
    """Disconnect from MT5."""
    _check_token(token)
    global _active_connection
    mt5.shutdown()
    _active_connection = None
    return {"status": "disconnected"}


@app.get("/account")
def account(token: str | None = None):
    """Get current account information."""
    _check_token(token)
    if not _active_connection:
        raise HTTPException(status_code=400, detail="Not connected. Call /connect first.")

    if not mt5.initialize():
        raise HTTPException(status_code=500, detail=f"MT5 init failed: {mt5.last_error()}")

    try:
        ai = mt5.account_info()
        if not ai:
            raise HTTPException(status_code=500, detail="Could not fetch account info")
        return {
            "account_number": ai.login,
            "balance": ai.balance,
            "equity": ai.equity,
            "margin": ai.margin,
            "free_margin": ai.margin_free,
            "leverage": ai.leverage,
            "currency": ai.currency,
            "company": ai.company or _active_connection["broker_name"],
            "account_type": "live" if ai.trade_mode != 0 else "demo",
            "server": ai.server,
        }
    finally:
        mt5.shutdown()


@app.get("/positions")
def positions(token: str | None = None):
    """Get all open positions."""
    _check_token(token)
    if not mt5.initialize():
        raise HTTPException(status_code=500, detail=f"MT5 init failed: {mt5.last_error()}")
    try:
        positions = mt5.positions_get()
        if not positions:
            return []
        result = []
        for pos in positions:
            result.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == 0 else "SELL",
                "volume": pos.volume,
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "swap": pos.swap,
                "commission": pos.commission,
                "open_time": str(pos.time) if pos.time else "",
                "comment": pos.comment or "",
            })
        return result
    finally:
        mt5.shutdown()


@app.post("/trade")
def trade(req: TradeRequest, token: str | None = None):
    """Execute a trade on MT5."""
    _check_token(token)
    if not _active_connection:
        raise HTTPException(status_code=400, detail="Not connected. Call /connect first.")

    if not mt5.initialize():
        raise HTTPException(status_code=500, detail=f"MT5 init failed: {mt5.last_error()}")

    try:
        symbol = req.symbol.upper()
        action = req.action.upper()

        if not mt5.symbol_select(symbol, True):
            raise HTTPException(status_code=400, detail=f"Symbol {symbol} not found")

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            raise HTTPException(status_code=400, detail=f"No price data for {symbol}")

        if action == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif action == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}. Must be BUY or SELL.")

        request_params = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(req.lot),
            "type": order_type,
            "price": price,
            "sl": float(req.sl) if req.sl else 0,
            "tp": float(req.tp) if req.tp else 0,
            "deviation": 20,
            "magic": 123456,
            "comment": "ForexTrade Bridge",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request_params)

        if result is None:
            raise HTTPException(status_code=500, detail="Order send returned None")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise HTTPException(
                status_code=500,
                detail=f"Order rejected: retcode={result.retcode}, comment={result.comment}",
            )

        return {
            "status": "executed",
            "ticket": result.order,
            "symbol": symbol,
            "action": action,
            "volume": req.lot,
            "price": result.price,
            "sl": req.sl,
            "tp": req.tp,
            "comment": result.comment,
        }
    finally:
        mt5.shutdown()


@app.post("/modify-position")
def modify_position(req: ModifySLTPRequest, token: str | None = None):
    """Modify SL/TP of an open position."""
    _check_token(token)
    if not mt5.initialize():
        raise HTTPException(status_code=500, detail=f"MT5 init failed: {mt5.last_error()}")
    try:
        pos = mt5.positions_get(ticket=req.ticket)
        if not pos:
            raise HTTPException(status_code=404, detail=f"Position {req.ticket} not found")
        pos = pos[0]
        request_params = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": req.ticket,
            "sl": float(req.sl),
            "tp": float(req.tp),
        }
        result = mt5.order_send(request_params)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return {"status": "modified", "ticket": req.ticket, "sl": req.sl, "tp": req.tp}
        raise HTTPException(status_code=500, detail=f"Modification failed: {result.comment if result else 'unknown'}")
    finally:
        mt5.shutdown()


@app.post("/close-position")
def close_position(ticket: int, token: str | None = None):
    """Close an open position."""
    _check_token(token)
    if not mt5.initialize():
        raise HTTPException(status_code=500, detail=f"MT5 init failed: {mt5.last_error()}")
    try:
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            raise HTTPException(status_code=404, detail=f"Position {ticket} not found")
        pos = pos[0]
        symbol = pos.symbol
        tick = mt5.symbol_info_tick(symbol)
        order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        price = tick.bid if pos.type == 0 else tick.ask

        request_params = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "ForexTrade Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request_params)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return {"status": "closed", "ticket": ticket, "close_price": price}
        raise HTTPException(status_code=500, detail=f"Close failed: {result.comment if result else 'unknown'}")
    finally:
        mt5.shutdown()


@app.get("/health")
def health():
    return {"status": "ok", "service": "MT5 Bridge", "port": BRIDGE_PORT}


# ── Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import subprocess
    print("=" * 60)
    print("  MT5 Bridge Service")
    print(f"  Port: {BRIDGE_PORT}")
    print(f"  Token: {BRIDGE_TOKEN[:8]}...")
    print("=" * 60)
    print()

    # Check if running as admin
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() if hasattr(ctypes, 'windll') else False
    print(f"  Running as Administrator: {is_admin}")
    print(f"  Python architecture: {_platform.architecture()[0]}")

    # Scan for running MT5 processes
    print()
    print("Detecting running MT5 terminals...")
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq terminal64.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            print(f"  terminal64.exe IS running")
            print(f"  {result.stdout.strip()}")
        else:
            print(f"  terminal64.exe NOT running - start MT5 first!")
            result2 = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq terminal.exe', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=5
            )
            if result2.stdout.strip():
                print(f"  terminal.exe IS running")
                print(f"  {result2.stdout.strip()}")
            else:
                print(f"  terminal.exe NOT running either")
    except Exception as e:
        print(f"  Process scan failed: {e}")

    # Find installed terminals
    print()
    print("Installed MT5 terminals found:")
    terminals = _find_mt5_terminals()
    for t in terminals:
        print(f"  {t['path']}")

    # Try initialization
    print()
    print("Attempting MT5 initialization...")
    initialized = False

    # Method 1: Default initialize
    if mt5.initialize():
        initialized = True
        print("  Method 1 (default): SUCCESS")
    else:
        err = mt5.last_error()
        print(f"  Method 1 (default): FAILED - {err}")

    # Method 2: Try with explicit paths from found terminals
    if not initialized:
        for t in terminals:
            if t.get("type") == "terminal":
                path = t["path"]
                print(f"  Method 2 (path={path}): Trying...")
                try:
                    if mt5.initialize(path=path):
                        initialized = True
                        print(f"  Method 2 (path={path}): SUCCESS")
                        break
                    else:
                        print(f"  Method 2 (path={path}): FAILED - {mt5.last_error()}")
                except Exception as ex:
                    print(f"  Method 2 (path={path}): EXCEPTION - {ex}")

    # Method 3: Try with folder path
    if not initialized:
        for t in terminals:
            if t.get("type") == "folder":
                p = t["path"]
                for exe in [r"terminal64.exe", r"terminal.exe"]:
                    fp = os.path.join(p, exe)
                    if Path(fp).exists():
                        print(f"  Method 3 (path={fp}): Trying...")
                        try:
                            if mt5.initialize(path=fp):
                                initialized = True
                                print(f"  Method 3 (path={fp}): SUCCESS")
                                break
                            else:
                                print(f"  Method 3 (path={fp}): FAILED - {mt5.last_error()}")
                        except Exception as ex:
                            print(f"  Method 3 (path={fp}): EXCEPTION - {ex}")
                if initialized:
                    break

    # Method 4: Try common install paths directly
    if not initialized:
        paths_to_try = [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\CXM Trader\terminal64.exe",
            r"C:\Program Files\MetaTrader 5 CXM\terminal64.exe",
        ]
        for p in paths_to_try:
            if Path(p).exists():
                print(f"  Method 4 (path={p}): Trying...")
                try:
                    if mt5.initialize(path=p):
                        initialized = True
                        print(f"  Method 4 (path={p}): SUCCESS")
                        break
                    else:
                        print(f"  Method 4 (path={p}): FAILED - {mt5.last_error()}")
                except Exception as ex:
                    print(f"  Method 4 (path={p}): EXCEPTION - {ex}")

    if initialized:
        ver = mt5.version()
        print(f"  MT5 Version: {ver[0]}.{ver[1]} build {ver[2]}")
        ti = mt5.terminal_info()
        if ti:
            print(f"  Terminal path: {ti.path}")
            print(f"  Connected to broker: {ti.connected}")
            if ti.connected:
                ai = mt5.account_info()
                if ai:
                    print(f"  Account: {ai.login} on {ai.server}")
                    print(f"  Balance: {ai.balance} {ai.currency}")
                    print(f"  Company: {ai.company}")
        mt5.shutdown()
        print()
        print("  ✓ BRIDGE READY - MT5 connected successfully")
    else:
        print()
        print("  ✗ MT5 initialization FAILED with all methods")
        print()
        print("  TROUBLESHOOTING:")
        print("  1. Open MetaTrader 5 and log into your broker account")
        print("  2. Go to Tools → Options → Expert Advisors → Enable 'Allow Automated Trading'")
        print("  3. Run this script as Administrator (right-click → Run as admin)")
        print("  4. If MT5 is installed in a custom location, set MT5_EXECUTABLE_PATH")
        print("     Example: set MT5_EXECUTABLE_PATH=C:\\YourPath\\terminal64.exe")
        print("  5. Ensure only ONE instance of MT5 is running")

    print()
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)
