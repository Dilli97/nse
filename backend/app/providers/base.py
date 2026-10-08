from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

class DataQuality(str, Enum):
    LIVE = 'live'
    DELAYED = 'delayed'
    EOD = 'eod'
    STALE = 'stale'
    DEMO = 'demo'

@dataclass
class ProviderQuote:
    symbol: str
    price: float
    change: float
    change_percent: float
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    prev_close: Optional[float]
    volume: Optional[int]
    market_cap: Optional[float]
    data_quality: DataQuality
    provider_name: str
    source_timestamp: Optional[datetime]
    fetch_timestamp: datetime

@dataclass 
class ProviderCandle:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None

@dataclass
class ProviderFinancialStatement:
    statement_type: str
    period_type: str
    reporting_type: str
    period_end_date: date
    currency: str
    unit: str
    data: dict
    source_url: Optional[str] = None

@dataclass
class StockInfo:
    symbol: str
    name: str
    isin: Optional[str]
    exchange: str
    sector: Optional[str]
    industry: Optional[str]

class MarketDataProvider(ABC):
    """Abstract interface for market data providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for display and logging."""
        pass
    
    @property
    @abstractmethod
    def data_quality(self) -> DataQuality:
        """Default data quality level for this provider."""
        pass
    
    @abstractmethod
    def get_stock_info(self, symbol: str, exchange: str = 'NSE') -> Optional[StockInfo]:
        """Fetch stock metadata."""
        pass
    
    @abstractmethod
    def search_stocks(self, query: str) -> List[StockInfo]:
        """Search for stocks by name or symbol."""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str, exchange: str = 'NSE') -> Optional[ProviderQuote]:
        """Fetch latest quote."""
        pass
    
    @abstractmethod
    def get_daily_candles(
        self, symbol: str, exchange: str = 'NSE',
        start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[ProviderCandle]:
        """Fetch daily OHLCV candles."""
        pass
    
    @abstractmethod
    def get_intraday_candles(
        self, symbol: str, exchange: str = 'NSE',
        interval: str = '15m', days_back: int = 5
    ) -> List[dict]:
        """Fetch intraday candles. Returns empty if not supported."""
        pass
    
    @abstractmethod
    def get_financial_statements(
        self, symbol: str, exchange: str = 'NSE'
    ) -> List[ProviderFinancialStatement]:
        """Fetch financial statements. Returns empty if not supported."""
        pass
    
    @abstractmethod
    def get_corporate_actions(
        self, symbol: str, exchange: str = 'NSE'
    ) -> List[dict]:
        """Fetch corporate actions. Returns empty if not supported."""
        pass
