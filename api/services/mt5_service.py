import logging
import httpx
from datetime import datetime

from repositories.connection_repo import save_connection, get_connection, disconnect, update_account_info
from repositories.settings_repo import get_settings
from repositories.activity_repo import log_activity

logger = logging.getLogger("mt5_service")

TIMEOUT = 30


def _get_bridge_url(user_id: int) -> str:
    settings = get_settings(user_id)
    url = settings.get("bridge_url", "").rstrip("/")
    if not url:
        raise RuntimeError(
            "MT5 Bridge not configured. Install and run the MT5 Bridge on your Windows PC, "
            "then enter the bridge URL in Settings. See documentation for setup instructions."
        )
    return url


def _check_response(resp: httpx.Response):
    if resp.status_code >= 400:
        detail = "Unknown error"
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)


def connect_account(user_id: int, broker_name: str, login_id: int, password: str,
                    server_name: str) -> dict:
    bridge_url = _get_bridge_url(user_id)

    try:
        resp = httpx.post(
            f"{bridge_url}/connect",
            json={
                "broker_name": broker_name,
                "login_id": login_id,
                "password": password,
                "server_name": server_name,
            },
            timeout=TIMEOUT,
        )
    except httpx.ConnectError:
        raise RuntimeError(
            f"Could not reach MT5 Bridge at {bridge_url}. "
            "Ensure the bridge is running on your Windows PC and the URL is accessible."
        )
    except httpx.TimeoutException:
        raise RuntimeError(f"MT5 Bridge at {bridge_url} timed out. Check your network connection.")

    _check_response(resp)
    data = resp.json()
    account = data.get("account", data)

    account_data = {
        "account_number": account.get("account_number", 0),
        "balance": account.get("balance", 0),
        "equity": account.get("equity", 0),
        "margin": account.get("margin", 0),
        "free_margin": account.get("free_margin", 0),
        "leverage": account.get("leverage", 0),
        "currency": account.get("currency", "USD"),
        "terminal_version": f"Build {account.get('terminal_build', '')}",
        "connection_time": account.get("connected_at", datetime.utcnow().isoformat()),
    }

    account_type = account.get("account_type", "live")
    save_connection(user_id, broker_name, login_id, password, server_name, account_data, account_type)
    log_activity(user_id, "broker_connected", f"Connected to {broker_name} ({server_name}) via Bridge")

    result = {
        "broker": broker_name,
        "account_number": account_data["account_number"],
        "balance": account_data["balance"],
        "equity": account_data["equity"],
        "margin": account_data["margin"],
        "free_margin": account_data["free_margin"],
        "leverage": account_data["leverage"],
        "currency": account_data["currency"],
        "terminal_version": account_data["terminal_version"],
        "connection_time": account_data["connection_time"],
        "is_connected": True,
        "account_type": account_type,
        "company": account.get("company", broker_name),
    }
    return result


def get_account_status(user_id: int) -> dict | None:
    stored = get_connection(user_id)
    if not stored:
        return None

    bridge_url = _get_bridge_url(user_id)

    try:
        resp = httpx.get(f"{bridge_url}/account", timeout=TIMEOUT)
        _check_response(resp)
        data = resp.json()

        result = {
            "account_number": data.get("account_number", stored["account_number"]),
            "broker": stored["broker_name"],
            "balance": data.get("balance", stored["balance"]),
            "equity": data.get("equity", stored["equity"]),
            "margin": data.get("margin", stored["margin"]),
            "free_margin": data.get("free_margin", stored.get("free_margin", 0)),
            "leverage": data.get("leverage", stored["leverage"]),
            "currency": data.get("currency", stored["currency"]),
            "terminal_version": stored.get("terminal_version", ""),
            "connection_time": stored.get("connection_time", ""),
            "is_connected": True,
            "account_type": data.get("account_type", stored.get("account_type", "")),
            "company": data.get("company", stored["broker_name"]),
        }
        update_account_info(user_id, result)
        return result
    except (httpx.ConnectError, httpx.TimeoutException):
        return {
            "account_number": stored["account_number"],
            "broker": stored["broker_name"],
            "balance": stored["balance"],
            "equity": stored["equity"],
            "margin": stored["margin"],
            "free_margin": stored.get("free_margin", 0),
            "leverage": stored["leverage"],
            "currency": stored["currency"],
            "terminal_version": stored.get("terminal_version", ""),
            "connection_time": stored.get("connection_time", ""),
            "is_connected": True,
            "account_type": stored.get("account_type", ""),
            "company": stored["broker_name"],
        }


def get_open_positions(user_id: int) -> list:
    bridge_url = _get_bridge_url(user_id)
    try:
        resp = httpx.get(f"{bridge_url}/positions", timeout=TIMEOUT)
        _check_response(resp)
        return resp.json()
    except Exception:
        return []


def disconnect_account(user_id: int):
    bridge_url = _get_bridge_url(user_id)
    try:
        httpx.post(f"{bridge_url}/disconnect", timeout=10)
    except Exception:
        pass
    disconnect(user_id)
    log_activity(user_id, "broker_disconnected", "MT5 disconnected")
