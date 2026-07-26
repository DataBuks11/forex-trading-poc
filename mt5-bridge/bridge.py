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

BROKER_SPECIFIC_DIRS = [
    "CXM Trader", "CXM", "FXTM", "ICMarkets", "Pepperstone",
    "IC Markets", "Vantage", "FP Markets", "Eightcap", "Blueberry",
    "Go Markets", "Axi", "AxiTrader", "ThinkMarkets", "Tickmill",
    "Admiral Markets", "Fusion Markets", "BlackBull", "TMGM",
    "Coinexx", "Hankotrade", "OANDA", "Forex.com",
]

MT5_INSTANCE_ID = "D0E8209F77C8CF37AD8BF550E51FF075"


def _find_mt5_terminals() -> list[dict]:
    """Scan common paths and find installed MT5 terminals."""
    found = []
    seen = set()
    for path in COMMON_MT5_PATHS:
        p = Path(path)
        if p.exists() and str(p) not in seen:
            seen.add(str(p))
            if p.is_file():
                found.append({"path": str(p), "type": "terminal", "exists": True})
            else:
                found.append({"path": str(p), "type": "folder", "exists": True})
    for base in [Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")]:
        try:
            for d in base.glob("MetaTrader*"):
                for exe in d.glob("terminal*.exe"):
                    if str(exe) not in seen:
                        seen.add(str(exe))
                        found.append({"path": str(exe), "type": "terminal", "exists": True})
        except Exception:
            pass
        try:
            for broker_dir in BROKER_SPECIFIC_DIRS:
                broker_path = base / broker_dir
                if broker_path.exists():
                    for exe in broker_path.glob("terminal*.exe"):
                        if str(exe) not in seen:
                            seen.add(str(exe))
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


# ── Robust Initialization Helpers ───────────────────────────────────────

def _kill_mt5_processes():
    """Kill all MT5 terminal processes to ensure a clean state."""
    killed = []
    for exe_name in ["terminal64.exe", "terminal.exe", "metaeditor64.exe", "metaeditor.exe"]:
        try:
            import subprocess
            r = subprocess.run(
                ["taskkill", "/F", "/IM", exe_name, "/T"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                killed.append(exe_name)
        except Exception:
            pass
    return killed


def _find_terminal64_recursive() -> list[str]:
    """Recursively scan for ALL terminal64.exe files on common drives."""
    found = []
    import subprocess
    search_roots = [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("APPDATA", ""),
    ]
    for root in search_roots:
        if not root or not os.path.isdir(root):
            continue
        try:
            r = subprocess.run(
                ["cmd", "/c", f'dir /s /b "{root}\\terminal64.exe" 2>nul'],
                capture_output=True, text=True, timeout=30, shell=True
            )
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line and os.path.isfile(line):
                    found.append(line)
        except Exception:
            pass
    return list(dict.fromkeys(found))


def _find_mt5_data_dirs() -> list[str]:
    """Find MT5 terminal data directories (containing origin.txt)."""
    dirs = []
    base = os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal")
    if os.path.isdir(base):
        for entry in os.scandir(base):
            if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "origin.txt")):
                dirs.append(entry.path)
    return dirs


def _read_mt5_logs(data_dir: str, max_lines: int = 50) -> list[str]:
    """Read the most recent lines from MT5 log file."""
    import glob as _glob
    log_dir = os.path.join(data_dir, "logs")
    if not os.path.isdir(log_dir):
        return []
    log_files = sorted(_glob.glob(os.path.join(log_dir, "*.log")), key=os.path.getmtime, reverse=True)
    if not log_files:
        return []
    try:
        with open(log_files[0], "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-max_lines:]]
    except Exception:
        return []


def _send_wm_copydata():
    """Send WM_COPYDATA to MT5 main window to wake up the IPC pipe."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    WM_COPYDATA = 0x004A
    hwnd = user32.FindWindowW(None, None)
    found_hwnd = None
    while hwnd:
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if "MetaTrader" in title and "terminal" not in title.lower():
                pass
            if "MetaTrader 5" in title or "MetaTrader" in title:
                found_hwnd = hwnd
                break
        hwnd = user32.GetWindow(hwnd, 2)  # GW_HWNDNEXT
    if found_hwnd:
        # Python 3.13 compatibility: ULONG_PTR and LPVOID may not exist
        try:
            ULONG_PTR = wintypes.ULONG_PTR
        except AttributeError:
            ULONG_PTR = ctypes.c_ulonglong
        try:
            LPVOID = wintypes.LPVOID
        except AttributeError:
            LPVOID = ctypes.c_void_p

        class COPYDATASTRUCT(ctypes.Structure):
            _fields_ = [("dwData", ULONG_PTR),
                        ("cbData", wintypes.DWORD),
                        ("lpData", LPVOID)]
        msg = b"MT5_BRIDGE_PING"
        cds = COPYDATASTRUCT()
        cds.dwData = 0
        cds.cbData = len(msg)
        cds.lpData = ctypes.cast(ctypes.create_string_buffer(msg), LPVOID)
        user32.SendMessageW(found_hwnd, WM_COPYDATA, 0, ctypes.byref(cds))
        return True
    return False


def _is_mt5_mcp_ready(data_dir: str) -> bool:
    """Check MT5 logs for 'MCP started' line to confirm terminal is ready for IPC."""
    lines = _read_mt5_logs(data_dir, max_lines=20)
    for line in lines:
        if "MCP" in line and "started" in line:
            return True
    return False


def _get_mt5_terminal_path() -> str | None:
    """Find the best MT5 terminal path, preferring broker-specific installs."""
    paths = [
        os.environ.get("MT5_EXECUTABLE_PATH", ""),
        os.environ.get("MT5_PATH", ""),
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
    ]
    for bp in BROKER_SPECIFIC_DIRS:
        for root in [r"C:\Program Files", r"C:\Program Files (x86)"]:
            paths.append(os.path.join(root, bp, "terminal64.exe"))
            paths.append(os.path.join(root, bp, "terminal.exe"))
    for p in paths:
        if p and os.path.isfile(p):
            return p
    deeper = _find_terminal64_recursive()
    if deeper:
        return deeper[0]
    return None


# ── Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import subprocess
    import time
    import sys as _sys
    import ctypes as _ctypes

    print("=" * 60)
    print("  MT5 Bridge Service v2.0")
    print(f"  Port: {BRIDGE_PORT}")
    print(f"  Token: {BRIDGE_TOKEN[:8]}...")
    print("=" * 60)
    print()

    # ── System Info ──────────────────────────────────────────────────
    is_admin = _ctypes.windll.shell32.IsUserAnAdmin() if hasattr(_ctypes, 'windll') else False
    print(f"[SYS] Administrator: {is_admin}")
    print(f"[SYS] Python arch:   {_platform.architecture()[0]}")
    print(f"[SYS] Python:        {_sys.executable}")
    print(f"[SYS] CWD:           {os.getcwd()}")

    # ── Windows Defender check ────────────────────────────────────────
    print()
    print("[DEFENDER] Checking Windows Defender status...")
    defender_on = False
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-MpComputerStatus).RealTimeProtectionEnabled"],
            capture_output=True, text=True, timeout=10
        )
        if r.stdout.strip() == "True":
            defender_on = True
            print("[DEFENDER] Real-time protection is ON - will add exclusions now")
            if is_admin:
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         f"Add-MpPreference -ExclusionProcess '{_sys.executable}' -Force"],
                        capture_output=True, timeout=10
                    )
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "Add-MpPreference -ExclusionProcess 'terminal64.exe' -Force"],
                        capture_output=True, timeout=10
                    )
                    print("[DEFENDER] Exclusions added for python.exe and terminal64.exe")
                except Exception:
                    print("[DEFENDER] Could not add exclusions automatically")
            else:
                print("[DEFENDER] Run as Admin to auto-add exclusions")
        else:
            print("[DEFENDER] Real-time protection is OFF")
    except Exception as e:
        print(f"[DEFENDER] Could not check: {e}")

    # ── Detect running MT5 (do not kill, do not launch) ───────────────
    print()
    print("[DETECT] Checking if MT5 terminal is running...")
    mt5_running = False
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        if r.stdout.strip() and "terminal64" in r.stdout.lower():
            mt5_running = True
            print(f"[DETECT] terminal64.exe IS running")
    except Exception:
        pass

    if not mt5_running:
        print("[DETECT] terminal64.exe is NOT running")
        print()
        print("  >>> ACTION REQUIRED <<<")
        print("  1. Open MetaTrader 5 manually from your desktop")
        print("  2. Log into your broker account (CXM, CXM-Primary)")
        print("  3. Wait for charts to load and connection status to show green")
        print("  4. Then re-run: python bridge.py")
        print()
        sys.exit(1)

    # ── Find MT5 data directory ───────────────────────────────────────
    data_dirs = _find_mt5_data_dirs()
    data_dir = data_dirs[0] if data_dirs else os.path.expandvars(
        rf"%APPDATA%\MetaQuotes\Terminal\{MT5_INSTANCE_ID}"
    )
    print(f"[INFO] Data directory: {data_dir}")

    # ── Force restart MT5 to clear IPC with new exclusions ───────────
    if defender_on and is_admin:
        print()
        print("[RESTART] Force-restarting MT5 to apply Defender exclusions...")
        subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"], capture_output=True)
        time.sleep(3)
        mt5_exe = _get_mt5_terminal_path()
        if mt5_exe:
            subprocess.Popen([mt5_exe], creationflags=0x00000008 if hasattr(subprocess, 'DETACHED_PROCESS') else 0)
            print("[RESTART] MT5 restarted, waiting 20s for full load...")
            time.sleep(20)
        else:
            print("[RESTART] Could not find terminal64.exe to restart")
    print()
    print("[INIT] Connecting to running MT5 terminal...")
    initialized = False
    last_error = None

    for attempt in range(5):
        try:
            result = mt5.initialize()
            if result:
                initialized = True
                print(f"[INIT] Connected! (attempt {attempt+1})")
                break
            err = mt5.last_error()
            last_error = err
            code = err[0] if err else -1
            print(f"[INIT] Attempt {attempt+1}: {err}")
            mt5.shutdown()
            time.sleep(3)
        except Exception as ex:
            print(f"[INIT] Attempt {attempt+1}: EXCEPTION {ex}")
            time.sleep(2)

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
        print("  BRIDGE READY - MT5 connected successfully")
    else:
        print()
        print(f"  MT5 initialization FAILED (last error: {last_error})")
        print()
        print("  TROUBLESHOOTING:")
        print("  1. Make sure MT5 is OPEN and you are LOGGED IN to your broker")
        print("  2. Go to Tools -> Options -> Expert Advisors -> enable 'Allow Automated Trading'")
        print("  3. Restart MT5 after enabling the setting above")
        print("  4. Check if Windows Defender is blocking the connection")
        print("  5. Try running this script BEFORE opening MT5 (reverse order)")
        print()
        sys.exit(1)

    print("=" * 60)
    print()
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)
