# Forex Trading POC - SaaS Automated Trading Platform

Proof of Concept demonstrating MT5 connection, dashboard, and TradingView webhook-based automated trading.

## Architecture

```
forex-trading-poc/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # FastAPI app with all routes
│   ├── database.py             # SQLite database setup
│   ├── auth.py                 # JWT authentication
│   ├── mt5_service.py          # MetaTrader 5 integration
│   ├── trade_service.py        # Trade execution engine
│   ├── schemas.py              # Pydantic models
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Next.js TypeScript frontend
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Entry redirect
│   │   ├── globals.css         # Global styles (dark theme)
│   │   ├── login/page.tsx      # Login / Register page
│   │   └── dashboard/
│   │       ├── layout.tsx      # Dashboard layout + sidebar
│   │       └── page.tsx        # Main dashboard
│   ├── components/
│   │   ├── sidebar.tsx         # Navigation sidebar
│   │   ├── mt5-connection-card.tsx
│   │   ├── account-summary.tsx
│   │   ├── trade-history-table.tsx
│   │   ├── open-positions-table.tsx
│   │   └── connection-status.tsx
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   ├── auth.ts             # Auth helpers
│   │   └── utils.ts            # Utility functions
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── postcss.config.mjs
└── README.md
```

## Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **MetaTrader 5** terminal installed (required for MT5 Python package)

> The MetaTrader5 Python package requires an MT5 terminal to be installed on the same machine. Download from [metatrader5.com](https://www.metatrader5.com/en/download).

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API runs at **http://localhost:8000**

API docs at **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI runs at **http://localhost:3000**

### 3. Open the App

Navigate to http://localhost:3000. Enter any username and password -- an account will be created automatically on first login.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login |
| POST | `/api/mt5/connect` | Connect MT5 account |
| GET | `/api/mt5/status` | Get connection status + account info |
| POST | `/api/mt5/disconnect` | Disconnect MT5 |
| GET | `/api/dashboard` | Dashboard data (account, positions, history) |
| POST | `/api/webhook/tradingview` | TradingView webhook endpoint |
| GET | `/api/trades/history` | Trade history |
| GET | `/api/trades/open` | Open trades |
| GET | `/api/health` | Health check |

## TradingView Webhook Setup

In TradingView alert settings, set the webhook URL to:

```
http://127.0.0.1:8000/api/webhook/tradingview
```

Use this JSON payload format:

```json
{
  "symbol":"EURUSD",
  "action":"BUY",
  "lot":0.10,
  "sl":1.1200,
  "tp":1.1300
}
```

The webhook endpoint currently uses `user_id=1` (first user). For production, pass an API key or token.

## Notes

- This is a **Proof of Concept**. Not production-ready.
- MT5 credentials are stored in SQLite (plain text) - use a proper secret manager in production.
- The webhook endpoint uses a hardcoded `user_id=1`; implement proper API key routing for multi-user.
- JWT secret is hardcoded; use an environment variable in production.
- Only one MT5 connection is supported per user.
