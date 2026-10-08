import yfinance as yf
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
import structlog
import time
from .base import (
    MarketDataProvider, ProviderQuote, ProviderCandle, ProviderFinancialStatement, 
    StockInfo, DataQuality
)

logger = structlog.get_logger(__name__)

class YahooFinanceProvider(MarketDataProvider):
    
    @property
    def name(self) -> str:
        return "Yahoo Finance"
    
    @property
    def data_quality(self) -> DataQuality:
        return DataQuality.DELAYED
        
    def _format_symbol(self, symbol: str, exchange: str) -> str:
        if exchange == 'NSE':
            return f"{symbol}.NS"
        elif exchange == 'BSE':
            return f"{symbol}.BO"
        return symbol

    def get_stock_info(self, symbol: str, exchange: str = 'NSE') -> Optional[StockInfo]:
        yf_symbol = self._format_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            if not info or 'shortName' not in info:
                return None
            return StockInfo(
                symbol=symbol,
                name=info.get('longName', info.get('shortName', symbol)),
                isin=None,
                exchange=exchange,
                sector=info.get('sector'),
                industry=info.get('industry')
            )
        except Exception as e:
            logger.error("yahoo_get_stock_info_error", symbol=symbol, error=str(e))
            return None

    def search_stocks(self, query: str) -> List[StockInfo]:
        return []

    def get_quote(self, symbol: str, exchange: str = 'NSE') -> Optional[ProviderQuote]:
        yf_symbol = self._format_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            if not info:
                return None
            
            price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', price)
            change = price - prev_close if price and prev_close else 0
            change_percent = (change / prev_close * 100) if prev_close else 0
            
            return ProviderQuote(
                symbol=symbol,
                price=price,
                change=change,
                change_percent=change_percent,
                open=info.get('open'),
                high=info.get('dayHigh'),
                low=info.get('dayLow'),
                prev_close=prev_close,
                volume=info.get('volume'),
                market_cap=info.get('marketCap'),
                data_quality=self.data_quality,
                provider_name=self.name,
                source_timestamp=datetime.now(timezone.utc),
                fetch_timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error("yahoo_get_quote_error", symbol=symbol, error=str(e))
            return None

    def get_daily_candles(
        self, symbol: str, exchange: str = 'NSE',
        start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[ProviderCandle]:
        yf_symbol = self._format_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(yf_symbol)
            
            kwargs = {}
            if start_date:
                kwargs['start'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                kwargs['end'] = (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
            if not kwargs:
                kwargs['period'] = '1y'
                
            df = ticker.history(**kwargs)
            if df.empty:
                return []
                
            candles = []
            for d, row in df.iterrows():
                candles.append(ProviderCandle(
                    date=d.date(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    adjusted_close=None
                ))
            return candles
        except Exception as e:
            logger.error("yahoo_get_daily_candles_error", symbol=symbol, error=str(e))
            return []

    def get_intraday_candles(
        self, symbol: str, exchange: str = 'NSE',
        interval: str = '15m', days_back: int = 5
    ) -> List[dict]:
        return []

    def get_financial_statements(
        self, symbol: str, exchange: str = 'NSE'
    ) -> List[ProviderFinancialStatement]:
        yf_symbol = self._format_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(yf_symbol)
            statements = []
            
            # Annual Income Statement
            inc = ticker.income_stmt
            if not inc.empty:
                for col in inc.columns:
                    stmt = ProviderFinancialStatement(
                        statement_type='income',
                        period_type='annual',
                        reporting_type='consolidated',
                        period_end_date=col.date(),
                        currency='INR',
                        unit='absolute',
                        data=inc[col].dropna().to_dict(),
                        source_url=None
                    )
                    statements.append(stmt)
                    
            bs = ticker.balance_sheet
            if not bs.empty:
                for col in bs.columns:
                    stmt = ProviderFinancialStatement(
                        statement_type='balance_sheet',
                        period_type='annual',
                        reporting_type='consolidated',
                        period_end_date=col.date(),
                        currency='INR',
                        unit='absolute',
                        data=bs[col].dropna().to_dict(),
                        source_url=None
                    )
                    statements.append(stmt)
                    
            cf = ticker.cashflow
            if not cf.empty:
                for col in cf.columns:
                    stmt = ProviderFinancialStatement(
                        statement_type='cash_flow',
                        period_type='annual',
                        reporting_type='consolidated',
                        period_end_date=col.date(),
                        currency='INR',
                        unit='absolute',
                        data=cf[col].dropna().to_dict(),
                        source_url=None
                    )
                    statements.append(stmt)
                    
            return statements
        except Exception as e:
            logger.error("yahoo_get_financials_error", symbol=symbol, error=str(e))
            return []

    def get_corporate_actions(
        self, symbol: str, exchange: str = 'NSE'
    ) -> List[dict]:
        yf_symbol = self._format_symbol(symbol, exchange)
        try:
            ticker = yf.Ticker(yf_symbol)
            actions = ticker.actions
            if actions.empty:
                return []
                
            results = []
            for d, row in actions.iterrows():
                if 'Dividends' in row and row['Dividends'] > 0:
                    results.append({
                        'action_type': 'dividend',
                        'ex_date': d.date(),
                        'dividend_amount': float(row['Dividends']),
                        'details_json': {'type': 'dividend', 'amount': float(row['Dividends'])}
                    })
                if 'Stock Splits' in row and row['Stock Splits'] > 0:
                    results.append({
                        'action_type': 'split',
                        'ex_date': d.date(),
                        'details_json': {'type': 'split', 'ratio': float(row['Stock Splits'])}
                    })
            return results
        except Exception as e:
            logger.error("yahoo_get_corporate_actions_error", symbol=symbol, error=str(e))
            return []
