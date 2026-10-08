"""Market data ingestion service.

Handles fetching and storing market data from providers.
All operations are idempotent - safe to retry after failures.
Timestamps: fetch_timestamp is always UTC, source_timestamp is provider-dependent.
"""
import structlog
import time
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.stock import Watchlist, WatchlistItem, Stock
from app.models.market_data import LatestQuote, DailyCandle, CorporateAction
from app.models.fundamental import FinancialStatement
from app.providers.base import MarketDataProvider, DataQuality
from app.providers.yahoo import YahooFinanceProvider
from app.config import settings

logger = structlog.get_logger(__name__)

# Rate limit: seconds between provider requests to avoid being blocked
REQUEST_DELAY = 1.0


class IngestionService:
    """Service for fetching and storing market data from providers."""

    def __init__(self, db: Session, provider: Optional[MarketDataProvider] = None):
        self.db = db
        self.provider = provider or YahooFinanceProvider()

    def get_watchlist_stocks(self, watchlist_name: str = "Default") -> list[Stock]:
        """Get all stocks in a watchlist."""
        wl = self.db.query(Watchlist).filter(Watchlist.name == watchlist_name).first()
        if not wl:
            return []
        items = (
            self.db.query(WatchlistItem)
            .filter(WatchlistItem.watchlist_id == wl.id)
            .order_by(WatchlistItem.sort_order)
            .all()
        )
        stock_ids = [item.stock_id for item in items]
        if not stock_ids:
            return []
        return self.db.query(Stock).filter(Stock.id.in_(stock_ids)).all()

    def refresh_single_stock(self, stock: Stock) -> None:
        """Refresh quote and recent candles for a single stock."""
        self._refresh_quote(stock)
        time.sleep(REQUEST_DELAY)
        self._refresh_candles(stock, period="3mo")

    def refresh_quotes(self) -> dict:
        """Refresh quotes for all watchlist stocks.
        
        Returns summary of results.
        """
        stocks = self.get_watchlist_stocks()
        results = {"success": 0, "failed": 0, "total": len(stocks)}

        for stock in stocks:
            try:
                self._refresh_quote(stock)
                results["success"] += 1
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logger.error("refresh_quote_failed", symbol=stock.symbol, error=str(e))
                results["failed"] += 1

        logger.info("quotes_refreshed", **results)
        return results

    def refresh_daily_candles(self) -> dict:
        """Refresh daily candles for all watchlist stocks.
        
        Fetches 1 year of history on first run, then only recent data.
        """
        stocks = self.get_watchlist_stocks()
        results = {"success": 0, "failed": 0, "total": len(stocks)}

        for stock in stocks:
            try:
                # Check if we have existing data
                last_candle = (
                    self.db.query(DailyCandle)
                    .filter(DailyCandle.stock_id == stock.id)
                    .order_by(DailyCandle.date.desc())
                    .first()
                )

                if last_candle:
                    # Fetch only recent data
                    start = last_candle.date - timedelta(days=5)  # Overlap for safety
                    self._refresh_candles(stock, start_date=start)
                else:
                    # First run: fetch 1 year
                    self._refresh_candles(stock, period="1y")

                results["success"] += 1
                time.sleep(REQUEST_DELAY * 2)  # Extra delay for larger requests
            except Exception as e:
                logger.error(
                    "refresh_candles_failed", symbol=stock.symbol, error=str(e)
                )
                results["failed"] += 1

        logger.info("candles_refreshed", **results)
        return results

    def refresh_financials(self) -> dict:
        """Refresh financial statements for all watchlist stocks."""
        stocks = self.get_watchlist_stocks()
        results = {"success": 0, "failed": 0, "total": len(stocks)}

        for stock in stocks:
            try:
                self._refresh_financial_statements(stock)
                results["success"] += 1
                time.sleep(REQUEST_DELAY * 3)
            except Exception as e:
                logger.error(
                    "refresh_financials_failed", symbol=stock.symbol, error=str(e)
                )
                results["failed"] += 1

        logger.info("financials_refreshed", **results)
        return results

    def _refresh_quote(self, stock: Stock) -> None:
        """Fetch and upsert latest quote for a stock."""
        quote = self.provider.get_quote(stock.symbol, "NSE")
        if not quote:
            logger.warning("no_quote_data", symbol=stock.symbol)
            return

        lq = self.db.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
        if not lq:
            lq = LatestQuote(stock_id=stock.id)
            self.db.add(lq)

        lq.price = quote.price
        lq.change = quote.change
        lq.change_percent = quote.change_percent
        lq.open = quote.open
        lq.high = quote.high
        lq.low = quote.low
        lq.prev_close = quote.prev_close
        lq.volume = quote.volume
        lq.market_cap = quote.market_cap
        lq.data_quality = quote.data_quality.value
        lq.provider = quote.provider_name
        lq.source_timestamp = quote.source_timestamp
        lq.fetch_timestamp = quote.fetch_timestamp

        self.db.commit()
        logger.info(
            "quote_updated",
            symbol=stock.symbol,
            price=quote.price,
            quality=quote.data_quality.value,
        )

    def _refresh_candles(
        self,
        stock: Stock,
        period: Optional[str] = None,
        start_date: Optional[date] = None,
    ) -> None:
        """Fetch and upsert daily candles for a stock."""
        if start_date:
            candles = self.provider.get_daily_candles(
                stock.symbol, "NSE", start_date=start_date
            )
        else:
            candles = self.provider.get_daily_candles(stock.symbol, "NSE")

        if not candles:
            logger.warning("no_candle_data", symbol=stock.symbol)
            return

        now = datetime.now(timezone.utc)
        new_count = 0
        update_count = 0

        for c in candles:
            existing = (
                self.db.query(DailyCandle)
                .filter(
                    DailyCandle.stock_id == stock.id,
                    DailyCandle.date == c.date,
                    DailyCandle.is_adjusted == False,
                )
                .first()
            )

            if existing:
                existing.open = c.open
                existing.high = c.high
                existing.low = c.low
                existing.close = c.close
                existing.volume = c.volume
                existing.adjusted_close = c.adjusted_close
                existing.provider = self.provider.name
                existing.fetch_timestamp = now
                update_count += 1
            else:
                dc = DailyCandle(
                    stock_id=stock.id,
                    date=c.date,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                    adjusted_close=c.adjusted_close,
                    is_adjusted=False,
                    provider=self.provider.name,
                    fetch_timestamp=now,
                )
                self.db.add(dc)
                new_count += 1

        self.db.commit()
        logger.info(
            "candles_updated",
            symbol=stock.symbol,
            new=new_count,
            updated=update_count,
        )

    def _refresh_financial_statements(self, stock: Stock) -> None:
        """Fetch and store financial statements for a stock."""
        statements = self.provider.get_financial_statements(stock.symbol, "NSE")
        if not statements:
            logger.warning("no_financial_data", symbol=stock.symbol)
            return

        now = datetime.now(timezone.utc)
        for stmt in statements:
            existing = (
                self.db.query(FinancialStatement)
                .filter(
                    FinancialStatement.stock_id == stock.id,
                    FinancialStatement.statement_type == stmt.statement_type,
                    FinancialStatement.period_type == stmt.period_type,
                    FinancialStatement.reporting_type == stmt.reporting_type,
                    FinancialStatement.period_end_date == stmt.period_end_date,
                )
                .first()
            )

            if existing:
                existing.data_json = stmt.data
                existing.provider = self.provider.name
                existing.fetch_timestamp = now
            else:
                fs = FinancialStatement(
                    stock_id=stock.id,
                    statement_type=stmt.statement_type,
                    period_type=stmt.period_type,
                    reporting_type=stmt.reporting_type,
                    period_end_date=stmt.period_end_date,
                    currency=stmt.currency,
                    unit=stmt.unit,
                    data_json=stmt.data,
                    source_url=stmt.source_url,
                    provider=self.provider.name,
                    fetch_timestamp=now,
                )
                self.db.add(fs)

        self.db.commit()
        logger.info(
            "financials_updated",
            symbol=stock.symbol,
            statements=len(statements),
        )
