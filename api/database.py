import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", os.path.join("/tmp", "forex_trading.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT DEFAULT '',
            hashed_password TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mt5_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            broker_name TEXT NOT NULL DEFAULT '',
            login_id INTEGER NOT NULL DEFAULT 0,
            password TEXT NOT NULL DEFAULT '',
            server_name TEXT NOT NULL DEFAULT '',
            is_connected BOOLEAN DEFAULT 0,
            account_number INTEGER DEFAULT 0,
            balance REAL DEFAULT 0,
            equity REAL DEFAULT 0,
            margin REAL DEFAULT 0,
            free_margin REAL DEFAULT 0,
            leverage INTEGER DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            terminal_version TEXT DEFAULT '',
            connection_time TIMESTAMP,
            account_type TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            lot REAL NOT NULL DEFAULT 0.01,
            sl REAL DEFAULT 0,
            tp REAL DEFAULT 0,
            ticket INTEGER,
            open_price REAL DEFAULT 0,
            close_price REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            swap REAL DEFAULT 0,
            commission REAL DEFAULT 0,
            status TEXT DEFAULT 'OPEN',
            source TEXT DEFAULT 'webhook',
            broker TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS webhook_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            lot REAL DEFAULT 0,
            sl REAL DEFAULT 0,
            tp REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            message TEXT DEFAULT '',
            ticket INTEGER,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            auto_trading_enabled BOOLEAN DEFAULT 0,
            default_lot_size REAL DEFAULT 0.01,
            risk_percent REAL DEFAULT 1.0,
            default_sl REAL DEFAULT 0,
            default_tp REAL DEFAULT 0,
            max_open_trades INTEGER DEFAULT 5,
            trading_pairs TEXT DEFAULT 'EURUSD,GBPUSD,USDJPY',
            trading_session TEXT DEFAULT 'ALL',
            bot_status TEXT DEFAULT 'stopped',
            webhook_secret TEXT DEFAULT '',
            webhook_enabled BOOLEAN DEFAULT 1,
            max_lot_size REAL DEFAULT 10.0,
            bridge_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS trading_scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            symbol TEXT NOT NULL DEFAULT 'EURUSD',
            timeframe TEXT DEFAULT 'M5',
            script_config TEXT NOT NULL DEFAULT '{}',
            created_by INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_admin_only BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS user_scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            script_id INTEGER NOT NULL,
            is_enabled BOOLEAN DEFAULT 1,
            custom_lot_size REAL DEFAULT 0.01,
            custom_risk REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, script_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (script_id) REFERENCES trading_scripts(id)
        );

        CREATE TABLE IF NOT EXISTS script_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            script_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            signal_type TEXT DEFAULT 'entry',
            price REAL DEFAULT 0,
            lot REAL DEFAULT 0.01,
            sl REAL DEFAULT 0,
            tp REAL DEFAULT 0,
            ticket INTEGER,
            status TEXT DEFAULT 'pending',
            message TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMP,
            FOREIGN KEY (script_id) REFERENCES trading_scripts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    # Migration: add columns that may be missing from older schema
    try:
        c.execute("ALTER TABLE settings ADD COLUMN bridge_url TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE settings ADD COLUMN max_daily_loss REAL DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE settings ADD COLUMN max_drawdown REAL DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()
