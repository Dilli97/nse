from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone

class Exchange(Base):
    __tablename__ = 'exchanges'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    timezone = Column(String, default='Asia/Kolkata')
    mic_code = Column(String, nullable=True)

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    name = Column(String, nullable=False)
    isin = Column(String, nullable=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'), nullable=False)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class SymbolChange(Base):
    __tablename__ = 'symbol_changes'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    old_symbol = Column(String, nullable=False)
    new_symbol = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class Watchlist(Base):
    __tablename__ = 'watchlists'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default='Default', nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class WatchlistItem(Base):
    __tablename__ = 'watchlist_items'
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.now(timezone.utc))
    sort_order = Column(Integer, default=0)
