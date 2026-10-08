from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Date, BigInteger, JSON, UniqueConstraint
from app.database import Base
from datetime import datetime, timezone

class DailyCandle(Base):
    __tablename__ = 'daily_candles'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    open = Column(Numeric(14,4), nullable=False)
    high = Column(Numeric(14,4), nullable=False)
    low = Column(Numeric(14,4), nullable=False)
    close = Column(Numeric(14,4), nullable=False)
    volume = Column(BigInteger, nullable=False)
    adjusted_close = Column(Numeric(14,4), nullable=True)
    is_adjusted = Column(Boolean, default=False)
    provider = Column(String, nullable=False)
    source_timestamp = Column(DateTime(timezone=True), nullable=True)
    fetch_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('stock_id', 'date', 'is_adjusted', name='_stock_date_adj_uc'),)

class IntradayCandle(Base):
    __tablename__ = 'intraday_candles'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    interval = Column(String, nullable=False)
    open = Column(Numeric(14,4), nullable=False)
    high = Column(Numeric(14,4), nullable=False)
    low = Column(Numeric(14,4), nullable=False)
    close = Column(Numeric(14,4), nullable=False)
    volume = Column(BigInteger, nullable=False)
    provider = Column(String, nullable=False)
    fetch_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('stock_id', 'timestamp', 'interval', name='_stock_ts_int_uc'),)

class LatestQuote(Base):
    __tablename__ = 'latest_quotes'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), unique=True, nullable=False)
    price = Column(Numeric(14,4), nullable=False)
    change = Column(Numeric(14,4), nullable=False)
    change_percent = Column(Numeric(8,4), nullable=False)
    open = Column(Numeric(14,4), nullable=True)
    high = Column(Numeric(14,4), nullable=True)
    low = Column(Numeric(14,4), nullable=True)
    prev_close = Column(Numeric(14,4), nullable=True)
    volume = Column(BigInteger, nullable=True)
    market_cap = Column(Numeric(20,4), nullable=True)
    data_quality = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    source_timestamp = Column(DateTime(timezone=True), nullable=True)
    fetch_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

class CorporateAction(Base):
    __tablename__ = 'corporate_actions'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    action_type = Column(String, nullable=False)
    ex_date = Column(Date, nullable=False)
    record_date = Column(Date, nullable=True)
    details_json = Column(JSON, nullable=False)
    ratio_from = Column(Numeric, nullable=True)
    ratio_to = Column(Numeric, nullable=True)
    dividend_amount = Column(Numeric, nullable=True)
    provider = Column(String, nullable=False)
    fetch_timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

class PriceAlert(Base):
    __tablename__ = 'price_alerts'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    alert_type = Column(String, nullable=False)  # 'price_above', 'price_below', 'rsi_above', 'rsi_below'
    threshold = Column(Numeric(14,4), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
