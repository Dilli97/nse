# Development & Setup Guide

This guide walks through configuring, setting up, and running the NSE Stock Analysis platform locally and in development environments.

---

## 1. Environment Requirements

- **Operating System:** Linux, macOS, or Windows (WSL2 recommended for Windows)
- **Containerization:** Docker Engine 24+ and Docker Compose v2+
- **Languages (if running outside containers):**
  - Python 3.11 or 3.12
  - Node.js 18 or 20 (LTS) & npm 9+
  - PostgreSQL 15+

---

## 2. Docker Compose Setup (Recommended)

1. **Clone & Configure:**
   ```bash
   cd nse-analysis
   cp .env.example .env
   ```

2. **Generate Secret Keys:**
   ```bash
   # On Linux/macOS
   openssl rand -hex 32
   ```
   Paste the generated token into `.env` under `SECRET_KEY`.

3. **Start the Stack:**
   ```bash
   docker-compose up --build -d
   ```

4. **Verify Container Health:**
   ```bash
   docker-compose ps
   ```
   All 5 containers (`db`, `backend`, `worker`, `frontend`, `nginx`) should be in an `Up` / `healthy` state.

5. **Tail Logs:**
   ```bash
   docker-compose logs -f backend worker
   ```

---

## 3. Running Without Docker (Bare Metal Development)

### Database Setup
1. Ensure PostgreSQL is running locally:
   ```sql
   CREATE USER nseapp WITH PASSWORD 'changeme_use_strong_password';
   CREATE DATABASE nse_analysis OWNER nseapp;
   ```

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```

3. Start the API Server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. Run the Background Worker (in a separate terminal):
   ```bash
   python -m app.worker.scheduler
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. The UI is accessible at `http://localhost:3000`.

---

## 4. Watchlist Configuration

The platform automatically initializes with a default seeded watchlist of 10 highly liquid NSE stocks:
- `RELIANCE` (Reliance Industries)
- `TCS` (Tata Consultancy Services)
- `INFY` (Infosys)
- `HDFCBANK` (HDFC Bank)
- `ICICIBANK` (ICICI Bank)
- `ITC` (ITC Limited)
- `HINDUNILVR` (Hindustan Unilever)
- `BHARTIARTL` (Bharti Airtel)
- `SBIN` (State Bank of India)
- `LT` (Larsen & Toubro)

### Adding Custom Stocks
You can add any NSE stock via the UI Search Bar or via the API:
```bash
curl -X POST http://localhost:8000/api/watchlist/items \
  -H "Content-Type: application/json" \
  -d '{"stock_id": 1}'
```

---

## 5. CSV Import Specification

For data provenance or offline usage, you can upload CSV files for historical candles or financial statements.

### A. Daily Candles CSV
**Columns required:**
`date,open,high,low,close,volume`

**Sample format (`data/csv_imports/sample_reliance_candles.csv`):**
```csv
date,open,high,low,close,volume
2024-01-01,2500.00,2520.00,2490.00,2510.00,1000000
2024-01-02,2515.00,2540.00,2505.00,2530.00,1200000
```

**Upload via curl:**
```bash
curl -X POST http://localhost:8000/api/settings/import/csv \
  -F "symbol=RELIANCE" \
  -F "data_type=candles" \
  -F "file=@data/csv_imports/sample_reliance_candles.csv"
```

### B. Financial Statements CSV
**Columns required:**
`period_end_date,period_type,statement_type,reporting_type,currency,unit,line_item,value`

**Sample format (`data/csv_imports/sample_tcs_financials.csv`):**
```csv
period_end_date,period_type,statement_type,reporting_type,currency,unit,line_item,value
2024-03-31,annual,income,consolidated,INR,crores,Total Revenue,240893.0
2024-03-31,annual,income,consolidated,INR,crores,Operating Income,59346.0
2024-03-31,annual,income,consolidated,INR,crores,Net Income,46099.0
2024-03-31,annual,balance_sheet,consolidated,INR,crores,Stockholders Equity,90498.0
2024-03-31,annual,balance_sheet,consolidated,INR,crores,Total Debt,0.0
2024-03-31,annual,cash_flow,consolidated,INR,crores,Operating Cash Flow,44300.0
2024-03-31,annual,cash_flow,consolidated,INR,crores,Capital Expenditure,3100.0
```

---

## 6. Running Unit & Integration Tests

Run the full pytest suite:
```bash
docker-compose run --rm backend pytest -v
```

Expected test coverage:
- Technical indicators against mathematical definitions
- Fundamental ratios, growth rates, and CAGRs
- Bank/NBFC distinct handling (skipping industrial leverage formulas)
- Negative equity and missing data handling
- Split, bonus, and dividend corporate action adjustments
- Duplicate-safe ingestion and timestamp conversions
- Deterministic research report synthesis
