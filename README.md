# NSE Stock Analysis Platform

A self-hosted, evidence-based Indian equity research and technical/fundamental stock analysis platform built with Next.js, FastAPI, PostgreSQL, and APScheduler.

---

## Highlights

- **Legally Sound Market Data Architecture:** Default delayed/EOD mode using free, open endpoints (Yahoo Finance) and documented CSV import workflows (e.g. NSE Bhavcopies, Screener export). Zero paid subscriptions required.
- **Pluggable Broker Interface:** Abstract provider architecture ready for real-time WebSocket broker data (e.g., Fyers API v3, Zerodha Kite Connect).
- **Rule-Based Technical Analysis:**
  - Moving Averages: SMA 20, 50, 200; EMA 12, 26
  - Momentum: RSI 14 (Wilder's smoothing), MACD (12, 26, 9)
  - Volatility & Volume: Bollinger Bands (20, 2), ATR 14, Volume vs 20-period average
  - Support & Resistance: Rule-based pivot points and local extrema on completed daily candles.
- **Comprehensive Fundamental Analysis:**
  - Multi-year financial statements: Income Statement, Balance Sheet, Cash Flow
  - Margins: Operating margin, Net profit margin
  - Returns: ROE, ROCE (with specialized financial institution / banking exceptions)
  - Solvency: Debt-to-Equity, Interest coverage
  - Valuation: P/E, P/B, EV/EBITDA, Dividend yield
  - Cash Flow: Free Cash Flow ($FCF = OCF - Capex$) and multi-year consistency
  - Growth: YoY and 3-Year / 5-Year compound annual growth rates (CAGR)
  - Transparent Fundamental Score (0-100) with weights, parameter coverage, and limitations.
- **Evidence-Based Research Reports:**
  - Deterministic template generation (works offline without any LLM)
  - Optional local LLM summarization via Ollama (`llama3`, `mistral`)
  - Strict anti-hallucination prompts citing only stored factual points.
  - Scenario analysis (Bull / Base / Bear) with explicit computational assumptions.
- **In-App Alerts:** Price and RSI threshold alert monitoring.
- **Security-First MVP:** Default localhost binding, environment variable secret management, parameterized queries, and optional token authentication.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, lightweight-charts (TradingView OSS), SWR, Lucide Icons |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Structlog |
| **Database** | PostgreSQL 16 Alpine |
| **Worker / Jobs** | APScheduler (separate container process) |
| **Reverse Proxy** | NGINX Alpine |
| **Containerization** | Docker Compose |

---

## Quick Start (Local Docker Deployment)

### 1. Prerequisites
- Docker Engine & Docker Compose (v2.20+)
- Git

### 2. Configuration
Clone the repository and prepare your environment file:
```bash
cp .env.example .env
```

Review `.env` settings. The default configuration connects to the local PostgreSQL container and defaults to `DEFAULT_PROVIDER=yahoo`.

### 3. Launch Services
Run the full stack with Docker Compose:
```bash
docker-compose up --build -d
```

This launches 5 coordinated services:
- `db`: PostgreSQL 16 listening on `127.0.0.1:5432`
- `backend`: FastAPI API server listening on `127.0.0.1:8000`
- `worker`: Background scheduler syncing quotes and daily candles
- `frontend`: Next.js frontend listening on `127.0.0.1:3000`
- `nginx`: Reverse proxy routing requests on `http://127.0.0.1:80`

### 4. Access the Application
Open your browser at:
- **Web UI:** [http://localhost](http://localhost) (or `http://localhost:3000`)
- **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## Market Data Legality & Entitlements

> [!IMPORTANT]
> **Free, authorized real-time NSE tick data does not exist legally without exchange entitlements.**
>
> 1. **Default Mode (Delayed / EOD):** We use Yahoo Finance for historical daily OHLCV and 15-minute delayed quotes. Every quote and chart displays a visible **Data Quality Label** (`delayed`, `eod`, `stale`).
> 2. **CSV Import Fallback:** You can import official daily Bhavcopies or export files directly via the UI settings or API.
> 3. **Future Broker API Integration:** If you hold a trading account with brokers like **Fyers** (free API) or **Zerodha** (Kite Connect), you can configure your API credentials in `.env` to enable live streaming feeds.

See [docs/data-sources.md](docs/data-sources.md) for the complete legal and architectural comparison of Indian market data providers.

---

## Project Structure

```
nse-analysis/
├── docker-compose.yml          # Container composition (binds 127.0.0.1)
├── .env.example                # Documented configuration variables
├── nginx/
│   └── nginx.conf              # Reverse proxy configuration
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt        # Pinned dependencies
│   ├── alembic.ini             # Database migration configuration
│   ├── alembic/                # Schema migration scripts
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint & seed logic
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # SQLAlchemy engine & session factory
│   │   ├── auth.py             # Token & API key verification
│   │   ├── models/             # Database ORM models
│   │   ├── api/                # REST API routers
│   │   ├── providers/          # Market data providers (Yahoo, CSV, Base)
│   │   ├── services/           # Technical, Fundamental, Ingestion, Reports
│   │   ├── worker/             # APScheduler background tasks
│   │   └── utils/              # Trading calendar & timezone helpers
│   └── tests/                  # Pytest test suite with fixtures
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # Stock charts, tables, panels
│   │   ├── lib/                # API client & TypeScript interfaces
│   │   └── hooks/              # SWR data fetching hooks
├── data/
│   └── csv_imports/            # Sample CSV import files
└── docs/
    ├── data-sources.md         # Data source research & legality
    ├── setup.md                # Development & operational setup
    └── deployment.md           # Production server deployment guide
```

---

## Running Tests

To run the backend test suite inside Docker:
```bash
docker-compose run --rm backend pytest -v
```
Or locally if Python 3.12 is installed:
```bash
cd backend
pip install -r requirements.txt
pytest -v
```

---

## License

Free and Open-Source Software under the MIT License.
