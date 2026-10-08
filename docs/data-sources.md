# NSE Stock Analysis Platform — Data Source Comparison

> **Last verified:** 2026-10-08
> **Purpose:** Document all evaluated data sources for the NSE analysis platform, with honest assessments of availability, legality, and limitations.

---

## Executive Summary

| Aspect | Decision |
|--------|----------|
| **Default source** | Yahoo Finance via `yfinance` (EOD/delayed, no account needed) |
| **Fallback source** | CSV import with manual Bhavcopy download |
| **Future live data** | Fyers API v3 (free with brokerage account) or Zerodha Kite Connect |
| **Fundamentals** | Yahoo Finance (limited) + CSV import workflow |
| **Data quality label** | All Yahoo Finance data labeled as **"delayed"** or **"EOD"** |

> [!IMPORTANT]
> Free, real-time NSE data is **not legally available** without a brokerage account and exchange data entitlements. This platform defaults to delayed/EOD mode and provides a pluggable adapter for broker APIs.

---

## 1. Broker APIs (Require Brokerage Account)

### 1.1 Zerodha Kite Connect

| Field | Details |
|-------|---------|
| **URL** | https://kite.trade/docs/connect/v3/ |
| **Data coverage** | Real-time quotes, historical OHLCV (daily + intraday), instruments list, corporate actions |
| **Timeliness** | Real-time streaming + EOD |
| **Auth required** | Zerodha brokerage account + API subscription |
| **Cost** | ₹500/month (waived if ₹2,000+ monthly brokerage generated) |
| **Rate limits** | 10 requests/second |
| **Historical limits** | Minute data: 60 days; Day data: since 2000 |
| **Storage** | Personal use allowed |
| **Redistribution** | Prohibited without exchange approval |
| **Status** | ✅ Active, industry standard |

### 1.2 Upstox API v2/v3

| Field | Details |
|-------|---------|
| **URL** | https://upstox.com/developer/api-documentation/ |
| **Data coverage** | Quotes, OHLCV, order execution |
| **Timeliness** | Real-time + EOD |
| **Auth required** | Upstox brokerage account |
| **Cost** | Free (no monthly API charges) |
| **Rate limits** | Documented per endpoint |
| **Storage** | Personal use allowed |
| **Redistribution** | Prohibited |
| **Status** | ✅ Active, well-maintained |

### 1.3 Angel One SmartAPI

| Field | Details |
|-------|---------|
| **URL** | https://smartapi.angelone.in/docs |
| **Data coverage** | Real-time streaming, historical data, order execution |
| **Timeliness** | Real-time + EOD |
| **Auth required** | Angel One brokerage account |
| **Cost** | Free |
| **Rate limits** | Aggressive rate limits (can trigger `DataException`) |
| **Storage** | Personal use allowed |
| **Redistribution** | Prohibited |
| **Status** | ✅ Active, rate limits can be challenging |

### 1.4 Fyers API v3

| Field | Details |
|-------|---------|
| **URL** | https://myapi.fyers.in/docsv3 |
| **Data coverage** | Real-time WebSocket, historical OHLCV, order execution |
| **Timeliness** | Real-time + EOD |
| **Auth required** | Fyers brokerage account |
| **Cost** | **Free** (no monthly charges for Trading + Data API) |
| **Rate limits** | 10,000 requests/day; 5,000 concurrent WebSocket symbols |
| **Historical limits** | Generous historical data access |
| **Storage** | Personal use allowed |
| **Redistribution** | Prohibited |
| **Status** | ✅ Active, excellent free option |
| **Recommendation** | **Best free broker API for future live data integration** |

### 1.5 DhanHQ API

| Field | Details |
|-------|---------|
| **URL** | https://dhanhq.co/docs/v2/ |
| **Data coverage** | Real-time quotes, historical OHLCV, option chain |
| **Timeliness** | Real-time + EOD |
| **Auth required** | Dhan brokerage account |
| **Cost** | Trading API free; Data API ₹499+taxes/month |
| **Rate limits** | 10 OPS for orders; 100,000 requests/day for historical |
| **Status** | ✅ Active, fast and reliable |

---

## 2. Free Data Sources (No Brokerage Account Required)

### 2.1 Yahoo Finance (via `yfinance` library) — **DEFAULT**

| Field | Details |
|-------|---------|
| **URL** | https://pypi.org/project/yfinance/ |
| **Data coverage** | Daily OHLCV, basic fundamentals (P&L, balance sheet, cash flow), dividends, splits, info |
| **Timeliness** | 15-minute delayed quotes; EOD candles after market close |
| **Auth required** | None |
| **Cost** | Free |
| **Rate limits** | Undocumented; aggressive use may trigger IP blocks; add delays between requests |
| **Historical limits** | OHLCV: full history (decades); Fundamentals: ~4 years |
| **Storage** | Personal/educational use |
| **Redistribution** | Not permitted |
| **NSE symbol format** | Append `.NS` suffix (e.g., `RELIANCE.NS`) |
| **BSE symbol format** | Append `.BO` suffix |
| **Status** | ✅ Working reliably (2024-2025) |
| **Limitations** | Unofficial API wrapper; may break if Yahoo changes endpoints; fundamental data is shallow; no intraday below 1-minute |

> [!NOTE]
> `yfinance` is an unofficial library that wraps Yahoo Finance's web endpoints. It is not an officially supported API. Yahoo does not explicitly authorize or prohibit personal analytical use, but commercial redistribution is not permitted. We label all data from this source as **"delayed"** or **"EOD"**.

### 2.2 NSE Bhavcopy (Official EOD Files)

| Field | Details |
|-------|---------|
| **URL** | https://www.nseindia.com/all-reports-derivatives |
| **Data coverage** | Daily EOD snapshot of all traded securities (OHLCV, delivery %) |
| **Timeliness** | EOD (published after market close, typically by 6-7 PM IST) |
| **Auth required** | None (public download) |
| **Cost** | Free |
| **Rate limits** | NSE actively blocks automated downloads with anti-bot measures |
| **Storage** | Personal use |
| **Status** | ⚠️ Available but difficult to automate due to anti-bot measures |
| **Format** | CSV/ZIP files |

### 2.3 BSE Bhavcopy

| Field | Details |
|-------|---------|
| **URL** | https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx |
| **Data coverage** | Daily EOD data for BSE-listed securities |
| **Timeliness** | EOD |
| **Auth required** | None |
| **Cost** | Free |
| **Status** | ✅ More accessible than NSE for automated downloads |

### 2.4 `jugaad-data` Library

| Field | Details |
|-------|---------|
| **URL** | https://pypi.org/project/jugaad-data/ |
| **Data coverage** | NSE historical data, Bhavcopies, RBI data |
| **Timeliness** | EOD |
| **Auth required** | None |
| **Cost** | Free |
| **Status** | ✅ Active and maintained |
| **Notes** | Uses caching to avoid NSE blocks; good fallback for Bhavcopy data |

### 2.5 `nsepython` Library

| Field | Details |
|-------|---------|
| **URL** | https://pypi.org/project/nsepython/ |
| **Data coverage** | NSE website data wrapper (quotes, option chain, corporate actions) |
| **Timeliness** | Near real-time (wraps NSE website) |
| **Auth required** | None |
| **Cost** | Free |
| **Status** | ✅ Active, replaces deprecated nsepy/nsetools |
| **Risk** | Wraps NSE website; may break when NSE changes UI |

---

## 3. Deprecated / Non-Functional Sources

| Source | Status | Notes |
|--------|--------|-------|
| `nsepy` | ❌ Deprecated/broken | Do not use |
| `nsetools` | ❌ Deprecated/broken | Do not use |
| Screener.in API | ❌ No API; scraping violates ToS | Uses Cloudflare protection |
| Moneycontrol API | ❌ No official API; scraping violates ToS | Anti-bot protection |
| Trendlyne API | ❌ No public API | Paid institutional access only |

---

## 4. Fundamental Data Sources

| Source | Coverage | Depth | Cost | Automation |
|--------|----------|-------|------|------------|
| yfinance | P&L, BS, CF | ~4 years | Free | ✅ Automated |
| NSE XBRL filings | Full XBRL | Complete history | Free | ⚠️ Complex XML parsing |
| BSE XBRL filings | Full XBRL | Complete history | Free | ⚠️ Complex XML parsing |
| SEBI EDGAR | Corporate filings | Complete | Free | ⚠️ Manual download |
| CSV import | User-provided | User-defined | Free | ✅ Manual + validated |

> [!TIP]
> For the MVP, we use `yfinance` for basic fundamentals (~4 years) and provide a **CSV import workflow** for users who want deeper historical data from sources like Screener.in (manual export) or paid databases.

---

## 5. CSV Import Specification

For users who want to import data from external sources:

### Price Data CSV Format
```csv
date,open,high,low,close,volume
2024-01-02,2500.00,2525.50,2490.00,2510.75,1234567
```

### Financial Statement CSV Format
```csv
period_end_date,period_type,statement_type,reporting_type,currency,unit,line_item,value
2024-03-31,annual,income,consolidated,INR,crores,total_revenue,945320.00
2024-03-31,annual,income,consolidated,INR,crores,operating_profit,182340.00
```

### Required fields and validation rules are documented in the import endpoint.

---

## 6. Key Distinctions

### API Access vs. Market Data Entitlements

| Aspect | Free API (e.g., Fyers) | Market Data Entitlement |
|--------|------------------------|------------------------|
| What it means | API endpoints are accessible without monthly charge | Permission from NSE/BSE to receive and use live price feeds |
| Requirement | Brokerage account | Usually included with brokerage account |
| Real-time data | ✅ Included with brokerage | ✅ Provided by exchange via broker |
| Without account | ❌ Cannot access | ❌ Cannot access |

> A "free API" from a broker means no additional charge beyond the brokerage account. It does **not** mean data is available without any account.

### Data Quality Labels Used in This Platform

| Label | Meaning | Typical Source |
|-------|---------|---------------|
| `live` | Real-time, <1 second delay | Broker WebSocket |
| `delayed` | 15-minute delayed | Yahoo Finance during market hours |
| `eod` | End-of-day, updated after market close | Bhavcopy, Yahoo after-hours |
| `stale` | Data older than expected (>24h for EOD) | Any source after fetch failure |
| `demo` | Fixture/sample data for testing | Built-in test data |

---

## 7. Unresolved Questions

1. **Yahoo Finance long-term reliability:** As an unofficial wrapper, `yfinance` could break at any time if Yahoo changes their endpoints. Mitigation: CSV import fallback.
2. **NSE anti-bot measures:** Direct Bhavcopy download automation is unreliable. Mitigation: Use `jugaad-data` which handles this, or manual download + CSV import.
3. **XBRL parsing complexity:** Building a full XBRL parser for NSE/BSE filings is significant engineering work. Deferred to future phase.
4. **Exchange data redistribution:** Even for personal tools, if the platform is ever shared or made public, exchange data terms would apply.

---

## 8. Selected Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Data Sources                        │
├──────────────┬──────────────┬───────────────────────┤
│ Yahoo Finance│  CSV Import  │ Future: Broker API    │
│ (Default)    │  (Fallback)  │ (Fyers/Kite)          │
│ Delayed/EOD  │  EOD         │ Real-time             │
└──────┬───────┴──────┬───────┴───────────┬───────────┘
       │              │                   │
       ▼              ▼                   ▼
┌─────────────────────────────────────────────────────┐
│         Provider Interface (Abstract Base)           │
│  - get_quote()  - get_daily_candles()               │
│  - get_financial_statements()                        │
│  - get_corporate_actions()                           │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              Ingestion Service                       │
│  - Idempotent upsert  - Rate limit handling         │
│  - Retry logic         - Freshness tracking          │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL Database                     │
│  - Raw prices  - Adjusted prices  - Fundamentals    │
│  - Corporate actions  - Reports                      │
└─────────────────────────────────────────────────────┘
```
