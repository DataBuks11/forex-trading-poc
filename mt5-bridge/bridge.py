"""
MT5 Bridge Service - Multi-Strategy Connection
==============================================
Strategies (tried in order):
  1. Direct login via mt5.initialize(login=..., password=..., server=..., path=...)
  2. Launch MT5 with /login /password /server CLI flags, then mt5.initialize()
  3. Standard IPC reconnect to already-running/logged-in terminal
  4. File-based MQL5 bridge (commands via C:\\mt5_bridge\\command.txt)

Run: python bridge.py
"""

import logging
import os
import sys
import json
import time
import subprocess
import platform as _platform
import ctypes as _ctypes
import glob as _glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from enum import Enum

import MetaTrader5 as mt5
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", "8765"))
BRIDGE_TOKEN = os.environ.get("BRIDGE_TOKEN", "mt5-bridge-default-token-change-me")
MT5_EXE_PATH = os.environ.get("MT5_EXECUTABLE_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")
MT5_LOGIN = os.environ.get("MT5_LOGIN")
MT5_PASSWORD = os.environ.get("MT5_PASSWORD")
MT5_SERVER = os.environ.get("MT5_SERVER")
FILE_BRIDGE_DIR = os.environ.get(
    "MT5_FILE_BRIDGE_DIR",
    os.path.join(os.environ.get("APPDATA", ""), "MetaQuotes", "Terminal", "Common", "Files")
)
COMMAND_FILE = os.path.join(FILE_BRIDGE_DIR, "command.txt")
RESPONSE_FILE = os.path.join(FILE_BRIDGE_DIR, "response.txt")

BROKER_SPECIFIC_DIRS = [
    "CXM Trader", "CXM", "FXTM", "ICMarkets", "Pepperstone",
    "IC Markets", "Vantage", "FP Markets", "Eightcap", "Blueberry",
    "Go Markets", "Axi", "AxiTrader", "ThinkMarkets", "Tickmill",
    "Admiral Markets", "Fusion Markets", "BlackBull", "TMGM",
    "Coinexx", "Hankotrade", "OANDA", "Forex.com",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | MT5-Bridge | %(levelname)s | %(message)s",
)
logger = logging.getLogger("mt5-bridge")


class BridgeMode(Enum):
    IPC = "ipc"
    FILE = "file"
    NONE = "none"


bridge_mode: BridgeMode = BridgeMode.NONE
_active_connection: Optional[dict] = None

app = FastAPI(title="MT5 Bridge Service", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# ── Auth ────────────────────────────────────────────────────────────────

def _check_token(token: Optional[str] = None):
    if token != BRIDGE_TOKEN and BRIDGE_TOKEN != "mt5-bridge-default-token-change-me":
        raise HTTPException(status_code=401, detail="Invalid bridge token")


# ── Python version check ────────────────────────────────────────────────

def _check_python_version():
    vi = sys.version_info[:3]
    if vi >= (3, 12):
        return (
            f"[WARN] Python {vi[0]}.{vi[1]}.{vi[2]} detected. "
            "The MetaTrader5 package may have issues with Python >= 3.12. "
            "For best results, use Python 3.10 or 3.11 (64-bit). "
            "We pinned MetaTrader5==5.0.45 which is the most compatible build."
        )
    return None


# ── MT5 Discovery Helpers ───────────────────────────────────────────────

def _find_terminal64_recursive() -> list[str]:
    found = []
    for root in [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    ]:
        if not os.path.isdir(root):
            continue
        try:
            import subprocess as _sp
            r = _sp.run(
                ["cmd", "/c", f'dir /s /b "{root}\\terminal64.exe" 2>nul'],
                capture_output=True, text=True, timeout=30, shell=True,
            )
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line and os.path.isfile(line):
                    found.append(line)
        except Exception:
            pass
    return list(dict.fromkeys(found))


def _get_mt5_terminal_path() -> Optional[str]:
    candidates = [
        os.environ.get("MT5_EXECUTABLE_PATH", ""),
        os.environ.get("MT5_PATH", ""),
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
    ]
    for bp in BROKER_SPECIFIC_DIRS:
        for root in [r"C:\Program Files", r"C:\Program Files (x86)"]:
            candidates.append(os.path.join(root, bp, "terminal64.exe"))
            candidates.append(os.path.join(root, bp, "terminal.exe"))
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    deeper = _find_terminal64_recursive()
    return deeper[0] if deeper else None


def _find_mt5_data_dirs() -> list[str]:
    dirs = []
    base = os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal")
    if os.path.isdir(base):
        for entry in os.scandir(base):
            if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "origin.txt")):
                dirs.append(entry.path)
    return dirs


def _read_mt5_logs(data_dir: str, max_lines: int = 100) -> list[str]:
    log_dir = os.path.join(data_dir, "logs")
    if not os.path.isdir(log_dir):
        return []
    log_files = sorted(
        _glob.glob(os.path.join(log_dir, "*.log")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not log_files:
        return []
    try:
        with open(log_files[0], "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-max_lines:]]
    except Exception:
        return []


def _check_logs_for_connection(data_dir: str) -> dict:
    lines = _read_mt5_logs(data_dir, max_lines=200)
    connected = False
    relevant = []
    keywords = ["authorized", "connected", "connect", "login", "logged", "trade server"]
    for line in lines:
        low = line.lower()
        if any(kw in low for kw in keywords):
            relevant.append(line)
            if "authorized" in low or "connected" in low:
                connected_path = True
                if "success" not in low and "fail" in low:
                    connected_path = False
    last_relevant = relevant[-5:] if relevant else []
    return {
        "connected": connected if 'connected' in dir() else False,
        "last_relevant": last_relevant,
    }


def _is_mt5_running() -> Optional[int]:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5,
        )
        if r.stdout.strip() and "terminal64" in r.stdout.lower():
            for line in r.stdout.splitlines():
                parts = line.replace('"', '').split(",")
                if len(parts) >= 2 and "terminal64" in parts[0].lower():
                    try:
                        return int(parts[1])
                    except ValueError:
                        return -1
    except Exception:
        pass
    return None


def _get_installed_package_version() -> Optional[str]:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "show", "MetaTrader5"],
            capture_output=True, text=True, timeout=10,
        )
        for line in r.stdout.splitlines():
            if line.lower().startswith("version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


# ── File-based MQL5 Bridge ──────────────────────────────────────────────

def _file_bridge_init():
    os.makedirs(FILE_BRIDGE_DIR, exist_ok=True)
    Path(COMMAND_FILE).write_text("")
    Path(RESPONSE_FILE).write_text("")


def _file_bridge_send_command(cmd: str, timeout_sec: float = 30.0) -> dict:
    for _ in range(2):
        try:
            Path(RESPONSE_FILE).write_text("")
            break
        except Exception:
            time.sleep(0.2)
    for _ in range(2):
        try:
            Path(COMMAND_FILE).write_text(cmd)
            break
        except Exception:
            time.sleep(0.2)
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        time.sleep(0.3)
        try:
            raw = Path(RESPONSE_FILE).read_text().strip()
        except Exception:
            continue
        if raw:
            Path(COMMAND_FILE).write_text("")
            parts = raw.split("|")
            status = parts[0].upper() if parts else "ERROR"
            if status == "OK":
                return {"success": True, "data": parts[1:]}
            else:
                return {"success": False, "error": raw, "data": []}
    return {"success": False, "error": "TIMEOUT: no response from MQL5 EA", "data": []}


def _file_bridge_read_account() -> dict:
    res = _file_bridge_send_command("ACCOUNT")
    if not res["success"]:
        raise HTTPException(status_code=500, detail=f"File bridge error: {res['error']}")
    data = res["data"]
    if len(data) >= 13:
        return {
            "account_number": int(data[0].split("=",1)[1]) if "=" in data[0] else data[0],
            "balance": float(data[1].split("=",1)[1]) if "=" in data[1] else float(data[1]),
            "equity": float(data[2].split("=",1)[1]) if "=" in data[2] else float(data[2]),
            "margin": float(data[3].split("=",1)[1]) if "=" in data[3] else float(data[3]),
            "free_margin": float(data[4].split("=",1)[1]) if "=" in data[4] else float(data[4]),
            "leverage": int(data[5].split("=",1)[1]) if "=" in data[5] else int(data[5]),
            "currency": data[6].split("=",1)[1] if "=" in data[6] else data[6],
            "company": data[7].split("=",1)[1] if "=" in data[7] else data[7],
            "account_type": data[8].split("=",1)[1] if "=" in data[8] else data[8],
            "server": data[9].split("=",1)[1] if "=" in data[9] else data[9],
            "name": data[10].split("=",1)[1] if "=" in data[10] and len(data) > 10 else "",
            "profit": float(data[11].split("=",1)[1]) if len(data) > 11 and "=" in data[11] else 0,
            "margin_free": float(data[12].split("=",1)[1]) if len(data) > 12 and "=" in data[12] else 0,
            "margin_level": float(data[13].split("=",1)[1]) if len(data) > 13 and "=" in data[13] else 0,
        }
    raise HTTPException(status_code=500, detail=f"Invalid account data from EA: {res}")


def _file_bridge_read_positions() -> list[dict]:
    res = _file_bridge_send_command("POSITIONS")
    if not res["success"]:
        raise HTTPException(status_code=500, detail=f"File bridge error: {res['error']}")
    if not res["data"] or (len(res["data"]) == 1 and not res["data"][0].strip()):
        return []
    raw_data = "|".join(res["data"])
    positions = []
    for entry in raw_data.split("|||"):
        entry = entry.strip()
        if not entry:
            continue
        fields = entry.split("|")
        if len(fields) >= 10:
            positions.append({
                "ticket": int(fields[0]),
                "symbol": fields[1],
                "type": fields[2],
                "volume": float(fields[3]),
                "open_price": float(fields[4]),
                "current_price": float(fields[5]),
                "sl": float(fields[6]),
                "tp": float(fields[7]),
                "profit": float(fields[8]),
                "swap": float(fields[9]),
                "commission": float(fields[10]) if len(fields) > 10 else 0,
                "open_time": fields[11] if len(fields) > 11 else "",
                "comment": fields[12] if len(fields) > 12 else "",
            })
    return positions


def _file_bridge_send_trade(symbol: str, action: str, lot: float, sl: float, tp: float) -> dict:
    cmd = f"TRADE|{symbol.upper()}|{action.upper()}|{lot}|{sl}|{tp}"
    res = _file_bridge_send_command(cmd)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=f"Trade failed: {res['error']}")
    result = {}
    for part in res["data"]:
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                result[k] = float(v) if "." in v else int(v)
            except ValueError:
                result[k] = v
    return result


def _file_bridge_close_position(ticket: int) -> dict:
    res = _file_bridge_send_command(f"CLOSE|{ticket}")
    if not res["success"]:
        raise HTTPException(status_code=500, detail=f"Close failed: {res['error']}")
    result = {}
    for part in res["data"]:
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                result[k] = float(v) if "." in v else int(v)
            except ValueError:
                result[k] = v
    return result


def _file_bridge_modify_sltp(ticket: int, sl: float, tp: float) -> dict:
    res = _file_bridge_send_command(f"MODIFY|{ticket}|{sl}|{tp}")
    if not res["success"]:
        raise HTTPException(status_code=500, detail=f"Modify failed: {res['error']}")
    result = {}
    for part in res["data"]:
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                result[k] = float(v) if "." in v else int(v)
            except ValueError:
                result[k] = v
    return result


# ── IPC-based MT5 helpers ───────────────────────────────────────────────

def _ipc_ensure_init():
    if not mt5.initialize():
        err = mt5.last_error()
        raise HTTPException(status_code=500, detail=f"MT5 init failed: {err}")


def _ipc_ensure_connected():
    if not _active_connection:
        raise HTTPException(status_code=400, detail="Not connected. Call /connect first.")


# ── FastAPI Endpoints ───────────────────────────────────────────────────

@app.post("/connect")
def connect(req: ConnectRequest, token: Optional[str] = None):
    _check_token(token)
    global _active_connection, bridge_mode

    if bridge_mode == BridgeMode.IPC:
        if not mt5.initialize():
            err = mt5.last_error()
            raise HTTPException(
                status_code=500,
                detail=f"MT5 initialization failed: {err}. Is MT5 terminal running?",
            )
        authorized = mt5.login(login=req.login_id, password=req.password, server=req.server_name)
        if not authorized:
            err = mt5.last_error()
            mt5.shutdown()
            raise HTTPException(status_code=400, detail=f"MT5 login failed: {err}")
        ai = mt5.account_info()
        ti = mt5.terminal_info()
        if not ai:
            mt5.shutdown()
            raise HTTPException(status_code=500, detail="Failed to get account info")
        _active_connection = {
            "broker_name": req.broker_name,
            "login_id": req.login_id,
            "server_name": req.server_name,
            "account_number": ai.login,
            "balance": ai.balance,
            "equity": ai.equity,
            "margin": ai.margin,
            "free_margin": ai.margin_free,
            "leverage": ai.leverage,
            "currency": ai.currency,
            "company": ai.company or req.broker_name,
            "account_type": "live" if ai.trade_mode != 0 else "demo",
            "terminal_build": ti.build if ti else 0,
            "terminal_path": ti.path if ti else "",
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
    elif bridge_mode == BridgeMode.FILE:
        _file_bridge_send_command(f"LOGIN|{req.login_id}|{req.password}|{req.server_name}")
        ai_data = _file_bridge_read_account()
        _active_connection = {
            "broker_name": req.broker_name,
            "login_id": req.login_id,
            "server_name": req.server_name,
            "account_number": ai_data.get("account_number", req.login_id),
            "balance": ai_data.get("balance", 0),
            "equity": ai_data.get("equity", 0),
            "margin": ai_data.get("margin", 0),
            "free_margin": ai_data.get("free_margin", 0),
            "leverage": ai_data.get("leverage", 0),
            "currency": ai_data.get("currency", "USD"),
            "company": ai_data.get("company", req.broker_name),
            "account_type": ai_data.get("account_type", "live"),
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        raise HTTPException(status_code=500, detail="No bridge mode active. Call /diagnostics for status.")

    logger.info(f"Connected: {_active_connection.get('account_number')} on {req.server_name}")
    return {"status": "connected", "account": _active_connection}


@app.post("/disconnect")
def disconnect(token: Optional[str] = None):
    _check_token(token)
    global _active_connection
    if bridge_mode == BridgeMode.IPC:
        mt5.shutdown()
    _active_connection = None
    return {"status": "disconnected"}


@app.get("/account")
def account(token: Optional[str] = None):
    _check_token(token)
    if bridge_mode == BridgeMode.FILE:
        return _file_bridge_read_account()
    _ipc_ensure_init()
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
            "company": ai.company or "",
            "account_type": "live" if ai.trade_mode != 0 else "demo",
            "server": ai.server,
            "name": ai.name or "",
            "profit": ai.profit or 0,
            "margin_free": ai.margin_free or 0,
            "margin_level": ai.margin_level if ai.margin_level else 0,
        }
    finally:
        mt5.shutdown()


@app.get("/positions")
def positions(token: Optional[str] = None):
    _check_token(token)
    if bridge_mode == BridgeMode.FILE:
        return _file_bridge_read_positions()
    _ipc_ensure_init()
    try:
        pos_list = mt5.positions_get()
        if not pos_list:
            return []
        result = []
        for pos in pos_list:
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
def trade(req: TradeRequest, token: Optional[str] = None):
    _check_token(token)
    _ipc_ensure_connected()
    if bridge_mode == BridgeMode.FILE:
        result = _file_bridge_send_trade(req.symbol, req.action, req.lot, req.sl, req.tp)
        return {
            "status": "executed",
            "ticket": result.get("ticket", 0),
            "symbol": req.symbol.upper(),
            "action": req.action.upper(),
            "volume": req.lot,
            "price": result.get("price", 0),
            "sl": req.sl,
            "tp": req.tp,
            "comment": str(result.get("comment", "")),
        }
    _ipc_ensure_init()
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
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
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
            raise HTTPException(status_code=500, detail=f"Order rejected: retcode={result.retcode}, comment={result.comment}")
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
def modify_position(req: ModifySLTPRequest, token: Optional[str] = None):
    _check_token(token)
    if bridge_mode == BridgeMode.FILE:
        result = _file_bridge_modify_sltp(req.ticket, req.sl, req.tp)
        return {"status": "modified", "ticket": req.ticket, "sl": req.sl, "tp": req.tp}
    _ipc_ensure_init()
    try:
        pos = mt5.positions_get(ticket=req.ticket)
        if not pos:
            raise HTTPException(status_code=404, detail=f"Position {req.ticket} not found")
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
def close_position(ticket: int, token: Optional[str] = None):
    _check_token(token)
    if bridge_mode == BridgeMode.FILE:
        result = _file_bridge_close_position(ticket)
        return {"status": "closed", "ticket": ticket, "close_price": result.get("close_price", 0)}
    _ipc_ensure_init()
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


@app.get("/diagnostics")
def diagnostics():
    result = {
        "system": {
            "os": _platform.system(),
            "os_version": _platform.version(),
            "python_version": sys.version,
            "python_arch": _platform.machine(),
            "python_executable": sys.executable,
            "bridge_port": BRIDGE_PORT,
            "bridge_mode": bridge_mode.value,
        },
        "mt5_installed_package": _get_installed_package_version(),
        "mt5_exe_path": _get_mt5_terminal_path(),
        "mt5_running_pid": _is_mt5_running(),
        "mt5_terminals_found": _find_terminal64_recursive(),
        "connection": {},
    }
    data_dirs = _find_mt5_data_dirs()
    result["data_dirs"] = data_dirs
    for dd in data_dirs:
        logs = _check_logs_for_connection(dd)
        result["connection"][dd] = logs
    if bridge_mode == BridgeMode.FILE:
        result["file_bridge"] = {
            "dir": FILE_BRIDGE_DIR,
            "command_exists": os.path.isfile(COMMAND_FILE),
            "response_exists": os.path.isfile(RESPONSE_FILE),
        }
    if bridge_mode == BridgeMode.IPC:
        try:
            if mt5.initialize():
                ti = mt5.terminal_info()
                if ti:
                    result["terminal_info"] = {
                        "connected": ti.connected,
                        "trade_allowed": ti.trade_allowed,
                        "path": ti.path,
                        "data_path": ti.data_path,
                        "build": ti.build,
                    }
                ai = mt5.account_info()
                if ai:
                    result["account_info"] = {
                        "login": ai.login,
                        "server": ai.server,
                        "balance": ai.balance,
                        "equity": ai.equity,
                    }
                mt5.shutdown()
        except Exception as e:
            result["mt5_error"] = str(e)
    return result


@app.get("/health")
def health():
    return {"status": "ok", "service": "MT5 Bridge v3", "port": BRIDGE_PORT, "mode": bridge_mode.value}


@app.get("/mode")
def get_mode(token: Optional[str] = None):
    _check_token(token)
    return {"bridge_mode": bridge_mode.value}


# ── MQL5 EA Generator ───────────────────────────────────────────────────

def _generate_mql5_ea():
    ea_code = r'''//+------------------------------------------------------------------+
//|                                         mt5_file_bridge.mq5         |
//|         File-based bridge for Python MT5 Bridge                    |
//|         Attach this EA to any chart in MT5                         |
//+------------------------------------------------------------------+
#property copyright "MT5 Bridge"
#property link      "https://github.com/example"
#property version   "1.00"
#property description "Reads commands from C:\\mt5_bridge\\command.txt"
#property description "Writes responses to C:\\mt5_bridge\\response.txt"

string   InpBridgeDir  = "C:\\mt5_bridge";   // Bridge files directory
int      InpPollMs     = 500;                // Poll interval (ms)

string   g_cmdFile;
string   g_respFile;
datetime g_lastCmdMod;

//+------------------------------------------------------------------+
int OnInit() {
   g_cmdFile  = InpBridgeDir + "\\command.txt";
   g_respFile = InpBridgeDir + "\\response.txt";

   if (!FolderCreate(InpBridgeDir)) {
      if (GetLastError() != 5019) { // already exists
         Print("Error creating bridge dir: ", InpBridgeDir, " error=", GetLastError());
      }
   }

   FileDelete(g_cmdFile);
   FileDelete(g_respFile);

   EventSetMillisecondTimer(InpPollMs);
   g_lastCmdMod = 0;
   Print("MT5 File Bridge EA started. Polling: ", InpBridgeDir);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
   EventKillTimer();
}

//+------------------------------------------------------------------+
void OnTimer() {
   if (!FileIsExist(g_cmdFile)) return;

   datetime modTime = (datetime)FileGetInteger(g_cmdFile, FILE_MODIFY_TIME, false);
   if (modTime == g_lastCmdMod) return;
   g_lastCmdMod = modTime;

   string cmd;
   int handle = FileOpen(g_cmdFile, FILE_TXT|FILE_READ|FILE_SHARE_READ|FILE_SHARE_WRITE);
   if (handle == INVALID_HANDLE) return;

   cmd = FileReadString(handle, 4096);
   FileClose(handle);

   if (StringLen(cmd) == 0) return;

   Print("Processing command: ", cmd);

   string resp = ProcessCommand(cmd);

   handle = FileOpen(g_respFile, FILE_TXT|FILE_WRITE|FILE_SHARE_READ|FILE_SHARE_WRITE);
   if (handle != INVALID_HANDLE) {
      FileWriteString(handle, resp);
      FileClose(handle);
   } else {
      Print("Cannot write response file: ", g_respFile, " error=", GetLastError());
   }

   FileDelete(g_cmdFile);
   g_lastCmdMod = 0;
}

//+------------------------------------------------------------------+
string ProcessCommand(string cmd) {
   string parts[];
   int n = StringSplit(cmd, '|', parts);

   if (n >= 1 && parts[0] == "ACCOUNT")  return HandleAccount();
   if (n >= 1 && parts[0] == "POSITIONS") return HandlePositions();
   if (n >= 1 && parts[0] == "TRADE")    return HandleTrade(parts, n);
   if (n >= 1 && parts[0] == "CLOSE")    return HandleClose(parts, n);
   if (n >= 1 && parts[0] == "MODIFY")   return HandleModify(parts, n);
   if (n >= 1 && parts[0] == "LOGIN")    return HandleLogin(parts, n);
   if (n >= 1 && parts[0] == "PING")     return "OK|time=" + TimeToString(TimeCurrent());

   return "ERROR|Unknown command: " + parts[0];
}

//+------------------------------------------------------------------+
string HandleAccount() {
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);
   double margin   = AccountInfoDouble(ACCOUNT_MARGIN);
   double freeMgn  = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   double profit   = AccountInfoDouble(ACCOUNT_PROFIT);
   long   leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);
   long   login    = AccountInfoInteger(ACCOUNT_LOGIN);
   string currency = AccountInfoString(ACCOUNT_CURRENCY);
   string company  = AccountInfoString(ACCOUNT_COMPANY);
   string server   = AccountInfoString(ACCOUNT_SERVER);
   string name     = AccountInfoString(ACCOUNT_NAME);
   long   tradeMode= AccountInfoInteger(ACCOUNT_TRADE_MODE);
   string accType  = (tradeMode == 0) ? "demo" : "live";
   double mgnLevel = (margin > 0) ? equity / margin * 100 : 0;

   return StringFormat("OK|login=%d|balance=%.2f|equity=%.2f|margin=%.2f|free_margin=%.2f|leverage=%d|currency=%s|company=%s|type=%s|server=%s|name=%s|profit=%.2f|margin_free=%.2f|margin_level=%.2f",
      login, balance, equity, margin, freeMgn, leverage, currency, company, accType, server, name, profit, freeMgn, mgnLevel);
}

//+------------------------------------------------------------------+
string HandlePositions() {
   string result = "OK|";
   bool first = true;

   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      if (!PositionSelectByTicket(PositionGetTicket(i))) continue;

      long   ticket     = PositionGetInteger(POSITION_TICKET);
      string symbol     = PositionGetString(POSITION_SYMBOL);
      long   posType    = PositionGetInteger(POSITION_TYPE);
      double volume     = PositionGetDouble(POSITION_VOLUME);
      double openPrice  = PositionGetDouble(POSITION_PRICE_OPEN);
      double curPrice   = PositionGetDouble(POSITION_PRICE_CURRENT);
      double sl         = PositionGetDouble(POSITION_SL);
      double tp         = PositionGetDouble(POSITION_TP);
      double profit     = PositionGetDouble(POSITION_PROFIT);
      double swap       = PositionGetDouble(POSITION_SWAP);
      double commission = PositionGetDouble(POSITION_COMMISSION);
      datetime openTime = (datetime)PositionGetInteger(POSITION_TIME);
      string comment    = PositionGetString(POSITION_COMMENT);
      string typeStr    = (posType == POSITION_TYPE_BUY) ? "BUY" : "SELL";

      if (!first) result += "|||";
      first = false;

      result += StringFormat("%d|%s|%s|%.2f|%.5f|%.5f|%.5f|%.5f|%.2f|%.2f|%.2f|%s|%s",
         ticket, symbol, typeStr, volume, openPrice, curPrice,
         sl, tp, profit, swap, commission,
         TimeToString(openTime), comment);
   }
   return result;
}

//+------------------------------------------------------------------+
string HandleTrade(string &parts[], int n) {
   if (n < 5) return "ERROR|Usage: TRADE|SYMBOL|BUY/SELL|LOT|SL|TP";

   string symbol = parts[1];
   string action = parts[2];
   double lot    = StringToDouble(parts[3]);
   double sl     = StringToDouble(parts[4]);
   double tp     = StringToDouble(parts[5]);

   MqlTick tick;
   if (!SymbolInfoTick(symbol, tick)) {
      return "ERROR|No tick for " + symbol;
   }

   double price;
   int orderType;
   if (action == "BUY") {
      price = tick.ask;
      orderType = ORDER_TYPE_BUY;
   } else if (action == "SELL") {
      price = tick.bid;
      orderType = ORDER_TYPE_SELL;
   } else {
      return "ERROR|Invalid action: " + action;
   }

   if (sl > 0 && orderType == ORDER_TYPE_BUY  && sl >= price) sl = price - (price * 0.001);
   if (sl > 0 && orderType == ORDER_TYPE_SELL && sl <= price) sl = price + (price * 0.001);
   if (tp > 0 && orderType == ORDER_TYPE_BUY  && tp <= price) tp = price + (price * 0.001);
   if (tp > 0 && orderType == ORDER_TYPE_SELL && tp >= price) tp = price - (price * 0.001);

   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = symbol;
   request.volume    = lot;
   request.type      = (ENUM_ORDER_TYPE)orderType;
   request.price     = price;
   request.sl        = sl;
   request.tp        = tp;
   request.deviation = 20;
   request.magic     = 123456;
   request.comment   = "MT5BridgeEA";
   request.type_filling = ORDER_FILLING_FOK;
   //// request.type_time    = ORDER_TIME_GTC;  -- remove this (only for pending orders)

   if (!OrderSend(request, result)) {
      return StringFormat("ERROR|OrderSend failed: retcode=%d comment=%s", result.retcode, result.comment);
   }

   if (result.retcode != TRADE_RETCODE_DONE) {
      return StringFormat("ERROR|retcode=%d comment=%s", result.retcode, result.comment);
   }

   return StringFormat("OK|ticket=%d|price=%.5f|volume=%.2f|comment=%s",
      result.order, result.price, result.volume, result.comment);
}

//+------------------------------------------------------------------+
string HandleClose(string &parts[], int n) {
   if (n < 2) return "ERROR|Usage: CLOSE|TICKET";

   long ticket = StringToInteger(parts[1]);

   if (!PositionSelectByTicket(ticket)) {
      return "ERROR|Position not found: " + IntegerToString(ticket);
   }

   string   symbol   = PositionGetString(POSITION_SYMBOL);
   double   volume   = PositionGetDouble(POSITION_VOLUME);
   long     posType  = PositionGetInteger(POSITION_TYPE);

   MqlTick tick;
   if (!SymbolInfoTick(symbol, tick)) {
      return "ERROR|No tick for " + symbol;
   }

   int    orderType;
   double price;
   if (posType == POSITION_TYPE_BUY) {
      orderType = ORDER_TYPE_SELL;
      price     = tick.bid;
   } else {
      orderType = ORDER_TYPE_BUY;
      price     = tick.ask;
   }

   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = symbol;
   request.volume    = volume;
   request.type      = (ENUM_ORDER_TYPE)orderType;
   request.position  = ticket;
   request.price     = price;
   request.deviation = 20;
   request.magic     = 123456;
   request.comment   = "MT5BridgeClose";
   request.type_filling = ORDER_FILLING_FOK;

   if (!OrderSend(request, result)) {
      return StringFormat("ERROR|Close failed: retcode=%d comment=%s", result.retcode, result.comment);
   }

   if (result.retcode != TRADE_RETCODE_DONE) {
      return StringFormat("ERROR|Close retcode=%d comment=%s", result.retcode, result.comment);
   }

   return StringFormat("OK|ticket=%d|close_price=%.5f", ticket, price);
}

//+------------------------------------------------------------------+
string HandleModify(string &parts[], int n) {
   if (n < 4) return "ERROR|Usage: MODIFY|TICKET|SL|TP";

   long   ticket = StringToInteger(parts[1]);
   double sl     = StringToDouble(parts[2]);
   double tp     = StringToDouble(parts[3]);

   if (!PositionSelectByTicket(ticket)) {
      return "ERROR|Position not found: " + IntegerToString(ticket);
   }

   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action   = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.sl       = sl;
   request.tp       = tp;

   if (!OrderSend(request, result)) {
      return StringFormat("ERROR|Modify failed: retcode=%d comment=%s", result.retcode, result.comment);
   }

   if (result.retcode != TRADE_RETCODE_DONE) {
      return StringFormat("ERROR|Modify retcode=%d comment=%s", result.retcode, result.comment);
   }

   return StringFormat("OK|ticket=%d|sl=%.5f|tp=%.5f", ticket, sl, tp);
}

//+------------------------------------------------------------------+
string HandleLogin(string &parts[], int n) {
   return "OK|login=" + parts[1] + "|server=" + parts[3];
}
//+------------------------------------------------------------------+
'''

    ea_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge.mq5")
    with open(ea_path, "w") as f:
        f.write(ea_code)
    return ea_path


# ── Connection Strategies ───────────────────────────────────────────────

def _prompt_credentials():
    """Try env vars first, then prompt."""
    login_str = MT5_LOGIN or input("Enter MT5 Login ID: ").strip()
    password = MT5_PASSWORD or input("Enter MT5 Password: ").strip()
    server = MT5_SERVER or input("Enter MT5 Server [CXMDirect-Live]: ").strip() or "CXMDirect-Live"
    login_str = login_str or "732959"
    return login_str, password, server


def _print_diagnostics():
    print()
    print("─" * 50)
    print("  DETAILED DIAGNOSTICS")
    print("─" * 50)
    pid = _is_mt5_running()
    print(f"  MT5 terminal process running: {'YES' if pid else 'NO'}")
    if pid:
        print(f"  MT5 terminal PID: {pid}")
    exe = _get_mt5_terminal_path()
    print(f"  MT5 exe path found: {exe or 'NOT FOUND'}")
    data_dirs = _find_mt5_data_dirs()
    if data_dirs:
        for dd in data_dirs:
            logs = _check_logs_for_connection(dd)
            print(f"  Data dir: {dd}")
            print(f"  Broker connected (from logs): {'YES' if logs.get('connected') else 'NOT DETECTED'}")
            if logs.get("last_relevant"):
                print("  Last relevant log lines:")
                for line in logs["last_relevant"]:
                    print(f"    {line[-120:]}")
    else:
        print("  No MT5 data directories found (no origin.txt)")
    pkg_ver = _get_installed_package_version()
    print(f"  MetaTrader5 package version: {pkg_ver or 'NOT INSTALLED'}")
    print(f"  Python: {sys.version}")


def _strategy_1_direct_login(login_str: str, password: str, server: str) -> bool:
    """Try mt5.initialize(login=..., password=..., server=..., path=...)."""
    global bridge_mode
    print()
    print("[STRATEGY 1] Direct login via mt5.initialize(login=..., password=..., server=..., path=...)")

    exe_path = _get_mt5_terminal_path()
    if not exe_path:
        print("[STRATEGY 1] Cannot find terminal64.exe. Skipping.")
        return False

    print(f"[STRATEGY 1] exe: {exe_path}")
    print(f"[STRATEGY 1] login: {login_str}, server: {server}")

    try:
        login_int = int(login_str)
    except ValueError:
        print(f"[STRATEGY 1] Invalid login ID: {login_str}")
        return False

    for attempt in range(3):
        print(f"[STRATEGY 1] Attempt {attempt+1}/3...")
        try:
            if mt5.initialize(path=exe_path, login=login_int, password=password, server=server):
                print("[STRATEGY 1] mt5.initialize() SUCCEEDED!")
                ver = mt5.version()
                print(f"  MT5 Version: {ver[0]}.{ver[1]} build {ver[2]}")
                ti = mt5.terminal_info()
                if ti:
                    print(f"  Terminal connected to broker: {ti.connected}")
                    print(f"  Terminal path: {ti.path}")
                    print(f"  Trade allowed: {ti.trade_allowed}")
                ai = mt5.account_info()
                if ai:
                    print(f"  Account: {ai.login} on {ai.server}")
                    print(f"  Balance: {ai.balance} {ai.currency}")
                    print(f"  Company: {ai.company}")
                mt5.shutdown()
                bridge_mode = BridgeMode.IPC
                return True
            else:
                err = mt5.last_error()
                print(f"[STRATEGY 1] Attempt {attempt+1}: FAILED - {err}")
                try:
                    mt5.shutdown()
                except Exception:
                    pass
        except Exception as ex:
            print(f"[STRATEGY 1] Attempt {attempt+1}: EXCEPTION - {ex}")
        time.sleep(3)

    print("[STRATEGY 1] All attempts failed.")
    return False


def _strategy_2_launch_with_cli_flags(login_str: str, password: str, server: str) -> bool:
    """Launch MT5 with /login /password /server flags, wait, then mt5.initialize()."""
    global bridge_mode
    print()
    print("[STRATEGY 2] Launch MT5 with CLI login flags")

    exe_path = _get_mt5_terminal_path()
    if not exe_path:
        print("[STRATEGY 2] Cannot find terminal64.exe. Skipping.")
        return False

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "terminal64.exe"],
            capture_output=True,
            timeout=10,
        )
        print("[STRATEGY 2] Killed existing terminal64.exe processes")
    except Exception:
        pass
    time.sleep(2)

    cmd = [exe_path, f"/login:{login_str}", f"/password:{password}", f"/server:{server}"]
    print(f"[STRATEGY 2] Launching: {cmd[0]} /login:*** /password:*** /server:{server}")

    try:
        subprocess.Popen(cmd, creationflags=0x00000008)
    except Exception as e:
        print(f"[STRATEGY 2] Failed to launch: {e}")
        return False

    print("[STRATEGY 2] Waiting 30s for MT5 to load and connect to broker...")
    time.sleep(30)

    pid = _is_mt5_running()
    if not pid:
        print("[STRATEGY 2] MT5 did not start. PID check returned None.")
    else:
        print(f"[STRATEGY 2] MT5 is running (PID: {pid})")

    print("[STRATEGY 2] Trying mt5.initialize()...")
    for attempt in range(5):
        try:
            if mt5.initialize():
                print(f"[STRATEGY 2] mt5.initialize() SUCCEEDED on attempt {attempt+1}!")
                ti = mt5.terminal_info()
                if ti:
                    print(f"  Terminal connected to broker: {ti.connected}")
                    print(f"  Trade allowed: {ti.trade_allowed}")
                ai = mt5.account_info()
                if ai:
                    print(f"  Account: {ai.login} on {ai.server}")
                    print(f"  Balance: {ai.balance} {ai.currency}")
                _active_conn = {
                    "login_id": ai.login if ai else 0,
                    "server_name": server,
                    "balance": ai.balance if ai else 0,
                }
                mt5.shutdown()
                bridge_mode = BridgeMode.IPC
                return True
            else:
                err = mt5.last_error()
                print(f"[STRATEGY 2] Attempt {attempt+1}/{5}: {err}")
                try:
                    mt5.shutdown()
                except Exception:
                    pass
        except Exception as ex:
            print(f"[STRATEGY 2] Attempt {attempt+1}/{5}: EXCEPTION - {ex}")
        time.sleep(5)

    print("[STRATEGY 2] All attempts failed.")
    return False


def _strategy_3_standard_ipc() -> bool:
    """Standard IPC: connect to already-running terminal."""
    global bridge_mode
    print()
    print("[STRATEGY 3] Standard IPC to already-running terminal")

    pid = _is_mt5_running()
    print(f"[STRATEGY 3] MT5 running: {'YES (PID=' + str(pid) + ')' if pid else 'NO'}")

    if not pid:
        print("[STRATEGY 3] terminal64.exe is not running. Cannot use IPC without terminal.")
        print("[STRATEGY 3] Please start MT5 and log in, then re-run bridge.py.")
        return False

    for attempt in range(5):
        try:
            if mt5.initialize():
                print(f"[STRATEGY 3] mt5.initialize() SUCCEEDED on attempt {attempt+1}!")
                ti = mt5.terminal_info()
                if ti:
                    print(f"  Terminal connected to broker: {ti.connected}")
                    print(f"  Trade allowed: {ti.trade_allowed}")
                    print(f"  Build: {ti.build}")
                ai = mt5.account_info()
                if ai:
                    print(f"  Account: {ai.login} on {ai.server}")
                    print(f"  Balance: {ai.balance} {ai.currency}")
                mt5.shutdown()
                bridge_mode = BridgeMode.IPC
                return True
            else:
                err = mt5.last_error()
                print(f"[STRATEGY 3] Attempt {attempt+1}/5: {err}")
                try:
                    mt5.shutdown()
                except Exception:
                    pass
        except Exception as ex:
            print(f"[STRATEGY 3] Attempt {attempt+1}/5: EXCEPTION - {ex}")
        time.sleep(3)

    print("[STRATEGY 3] All attempts failed.")
    return False


def _strategy_4_file_bridge() -> bool:
    """File-based MQL5 bridge."""
    global bridge_mode
    print()
    print("[STRATEGY 4] File-based MQL5 bridge")
    print(f"[STRATEGY 4] Bridge directory: {FILE_BRIDGE_DIR}")

    _file_bridge_init()

    ea_path = _generate_mql5_ea()
    print(f"[STRATEGY 4] MQL5 EA written to: {ea_path}")

    print()
    print("─" * 60)
    print("  FILE BRIDGE SETUP INSTRUCTIONS")
    print("─" * 60)
    print(f"  1. Open MetaTrader 5")
    print(f"  2. Open MetaEditor (F4) -> Open -> {ea_path}")
    print(f"  3. Press F7 / Compile to produce bridge.ex5")
    print(f"  4. Go back to MT5, open Navigator (Ctrl+N)")
    print(f"  5. Under Expert Advisors, find 'mt5_file_bridge'")
    print(f"  6. Drag it onto ANY chart (EURUSD, GBPUSD, etc.)")
    print(f"  7. In the Common tab: enable 'Allow Automated Trading'")
    print(f"  8. Click OK - you should see a smiley face on the chart")
    print("─" * 60)
    print()

    input("Press ENTER after you have attached the EA to a chart...")

    print("[STRATEGY 4] Testing bridge with PING command...")
    res = _file_bridge_send_command("PING", timeout_sec=5.0)
    if res["success"]:
        print(f"[STRATEGY 4] Bridge is working! Response: {res}")
        bridge_mode = BridgeMode.FILE
        return True
    else:
        print(f"[STRATEGY 4] Bridge test failed: {res}")
        return False


# ── Main ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  MT5 Bridge Service v3.0 - FILE MODE")
    print(f"  Port: {BRIDGE_PORT}")
    print("=" * 60)

    # Ensure bridge directory exists
    os.makedirs(FILE_BRIDGE_DIR, exist_ok=True)

    print()
    print("[FILE MODE] Using file-based MQL5 bridge (bypasses IPC)")
    print(f"[FILE MODE] Command file: {COMMAND_FILE}")
    print(f"[FILE MODE] Response file: {RESPONSE_FILE}")
    print()

    # Test the bridge
    response = _file_bridge_send_command("PING", timeout_sec=5)
    if response.get("success"):
        data = response.get("data", [])
        print(f"[FILE MODE] Bridge working! Response: {'|'.join(data)}")
        bridge_mode = BridgeMode.FILE
        print()
        print("  *** BRIDGE READY - File-based mode active ***")
    else:
        print(f"[FILE MODE] Bridge test: {response.get('error', 'No response')}")
        print("[FILE MODE] EA not attached yet. Bridge will start anyway.")
        print("[FILE MODE] Attach the EA to an MT5 chart and it will auto-connect.")
        bridge_mode = BridgeMode.FILE

    print(f"  Port: {BRIDGE_PORT}")
    print("=" * 60)
    print()
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)
