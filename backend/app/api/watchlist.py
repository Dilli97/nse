"""Watchlist API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock import Stock, Watchlist, WatchlistItem
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


@router.get("", response_model=List[WatchlistItemOut])
@router.get("/", response_model=List[WatchlistItemOut])
@router.get("/items", response_model=List[WatchlistItemOut])
def get_watchlist(db: Session = Depends(get_db)):
    """Get watchlist items with latest quotes."""
    wl = db.query(Watchlist).filter(Watchlist.name == "Default").first()
    if not wl:
        return []

    items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == wl.id)
        .order_by(WatchlistItem.sort_order)
        .all()
    )

    result = []
    for item in items:
        stock = db.query(Stock).filter(Stock.id == item.stock_id).first()
        if not stock:
            continue

        quote = db.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
        quote_out = _build_quote_out(stock, quote) if quote else None

        result.append(
            WatchlistItemOut(
                id=item.id,
                stock=StockOut(
                    id=stock.id,
                    symbol=stock.symbol,
                    name=stock.name,
                    isin=stock.isin,
                    exchange="NSE",
                    sector=stock.sector,
                    industry=stock.industry,
                    is_active=stock.is_active,
                ),
                quote=quote_out,
            )
        )
    return result


@router.post("/items")
def add_to_watchlist(req: AddWatchlistRequest, db: Session = Depends(get_db)):
    """Add a stock to watchlist."""
    stock = db.query(Stock).filter(Stock.id == req.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    wl = db.query(Watchlist).filter(Watchlist.name == "Default").first()
    if not wl:
        wl = Watchlist(name="Default")
        db.add(wl)
        db.flush()

    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == wl.id, WatchlistItem.stock_id == stock.id)
        .first()
    )
    if existing:
        return {"message": "Stock already in watchlist", "id": existing.id}

    max_order = db.query(WatchlistItem).filter(WatchlistItem.watchlist_id == wl.id).count()
    item = WatchlistItem(watchlist_id=wl.id, stock_id=stock.id, sort_order=max_order)
    db.add(item)
    db.commit()
    return {"message": "Added to watchlist", "id": item.id}


@router.delete("/items/{item_id}")
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db)):
    """Remove a stock from watchlist."""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}
