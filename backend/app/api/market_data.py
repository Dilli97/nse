"""Market data API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime, timedelta, timezone

from app.database import get_db
from app.models.stock import Stock
from app.models.market_data import DailyCandle, LatestQuote
from app.services.ingestion import IngestionService
from app.utils.timestamps import data_age_seconds

router = APIRouter()


class CandleOut(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


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


class FreshnessOut(BaseModel):
    quote_age_seconds: Optional[float] = None
    candle_last_date: Optional[str] = None
    overall_quality: str


PERIOD_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "3y": 1095,
    "5y": 1825,
    "max": 36500,
}


@router.get("/{symbol}/candles", response_model=List[CandleOut])
def get_candles(
    symbol: str,
    period: str = Query("1y", description="Time period: 1mo, 3mo, 6mo, 1y, 3y, 5y, max"),
    db: Session = Depends(get_db),
):
    """Get daily OHLCV candles for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    days = PERIOD_DAYS.get(period, 365)
    start_date = date.today() - timedelta(days=days)

    candles = (
        db.query(DailyCandle)
        .filter(
            DailyCandle.stock_id == stock.id,
            DailyCandle.is_adjusted == False,
            DailyCandle.date >= start_date,
        )
        .order_by(DailyCandle.date.asc())
        .all()
    )

    return [
        CandleOut(
            date=c.date.isoformat(),
            open=float(c.open),
            high=float(c.high),
            low=float(c.low),
            close=float(c.close),
            volume=int(c.volume),
        )
        for c in candles
    ]


@router.get("/{symbol}/quote")
def get_quote(symbol: str, db: Session = Depends(get_db)):
    """Get the latest quote for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    quote = db.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
    if not quote:
        return {
            "stock_id": stock.id,
            "symbol": stock.symbol,
            "price": 0,
            "change": 0,
            "change_percent": 0,
            "data_quality": "stale",
            "provider": "none",
            "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "No quote data available. Trigger a refresh or wait for scheduled ingestion.",
        }

    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "price": float(quote.price),
        "change": float(quote.change),
        "change_percent": float(quote.change_percent),
        "open": float(quote.open) if quote.open else None,
        "high": float(quote.high) if quote.high else None,
        "low": float(quote.low) if quote.low else None,
        "prev_close": float(quote.prev_close) if quote.prev_close else None,
        "volume": int(quote.volume) if quote.volume else None,
        "market_cap": float(quote.market_cap) if quote.market_cap else None,
        "data_quality": quote.data_quality,
        "provider": quote.provider,
        "source_timestamp": quote.source_timestamp.isoformat() if quote.source_timestamp else None,
        "fetch_timestamp": quote.fetch_timestamp.isoformat(),
    }


@router.get("/{symbol}/freshness")
def get_freshness(symbol: str, db: Session = Depends(get_db)):
    """Get data freshness information for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    quote = db.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
    last_candle = (
        db.query(DailyCandle)
        .filter(DailyCandle.stock_id == stock.id)
        .order_by(DailyCandle.date.desc())
        .first()
    )

    quote_age = data_age_seconds(quote.fetch_timestamp) if quote else None
    candle_date = last_candle.date.isoformat() if last_candle else None
    
    if quote_age is None:
        quality = "stale"
    elif quote_age < 1200:
        quality = "delayed"
    elif quote_age < 86400:
        quality = "eod"
    else:
        quality = "stale"

    return FreshnessOut(
        quote_age_seconds=quote_age,
        candle_last_date=candle_date,
        overall_quality=quality,
    )


@router.post("/{symbol}/refresh")
def refresh_stock(symbol: str, db: Session = Depends(get_db)):
    """Manually trigger data refresh for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    svc = IngestionService(db)
    try:
        svc.refresh_single_stock(stock)
        return {"message": f"Refreshed data for {stock.symbol}", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")
