"""Stock and watchlist API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.stock import Stock, Watchlist, WatchlistItem, Exchange
from app.models.market_data import LatestQuote

router = APIRouter()


class StockOut(BaseModel):
    id: int
    symbol: str
    name: str
    isin: Optional[str] = None
    exchange: str = "NSE"
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class QuoteOut(BaseModel):
    stock_id: int
    symbol: str
    price: float
    change: float
    change_percent: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    data_quality: str
    provider: str
    source_timestamp: Optional[str] = None
    fetch_timestamp: str


class WatchlistItemOut(BaseModel):
    id: int
    stock: StockOut
    quote: Optional[QuoteOut] = None


class AddWatchlistRequest(BaseModel):
    stock_id: int


@router.get("/", response_model=List[StockOut])
def list_stocks(search: Optional[str] = None, db: Session = Depends(get_db)):
    """List stocks, optionally filtered by search query."""
    query = db.query(Stock).filter(Stock.is_active == True)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Stock.symbol.ilike(search_pattern)) | (Stock.name.ilike(search_pattern))
        )
    stocks = query.order_by(Stock.symbol).limit(50).all()
    result = []
    for s in stocks:
        result.append(StockOut(
            id=s.id,
            symbol=s.symbol,
            name=s.name,
            isin=s.isin,
            exchange="NSE",
            sector=s.sector,
            industry=s.industry,
            is_active=s.is_active,
        ))
    return result


@router.get("/{symbol}", response_model=StockOut)
def get_stock(symbol: str, db: Session = Depends(get_db)):
    """Get stock details by symbol."""
    stock = db.query(Stock).filter(
        Stock.symbol == symbol.upper(), Stock.is_active == True
    ).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return StockOut(
        id=stock.id,
        symbol=stock.symbol,
        name=stock.name,
        isin=stock.isin,
        exchange="NSE",
        sector=stock.sector,
        industry=stock.industry,
        is_active=stock.is_active,
    )


def _build_quote_out(stock: Stock, quote: LatestQuote) -> QuoteOut:
    return QuoteOut(
        stock_id=stock.id,
        symbol=stock.symbol,
        price=float(quote.price),
        change=float(quote.change),
        change_percent=float(quote.change_percent),
        open=float(quote.open) if quote.open else None,
        high=float(quote.high) if quote.high else None,
        low=float(quote.low) if quote.low else None,
        prev_close=float(quote.prev_close) if quote.prev_close else None,
        volume=int(quote.volume) if quote.volume else None,
        market_cap=float(quote.market_cap) if quote.market_cap else None,
        data_quality=quote.data_quality,
        provider=quote.provider,
        source_timestamp=quote.source_timestamp.isoformat() if quote.source_timestamp else None,
        fetch_timestamp=quote.fetch_timestamp.isoformat(),
    )



