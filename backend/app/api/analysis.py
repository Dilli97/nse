"""Technical and fundamental analysis API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd

from app.database import get_db
from app.models.stock import Stock
from app.models.market_data import DailyCandle, LatestQuote
from app.models.fundamental import FinancialStatement, CalculatedRatio, ShareholdingPattern
from app.services.technical import generate_technical_summary
from app.services.fundamental import FundamentalService

router = APIRouter()


@router.get("/{symbol}/technical")
def get_technical_analysis(symbol: str, db: Session = Depends(get_db)):
    """Get technical indicators for a stock.
    
    Calculates indicators from stored daily candles using completed candles only.
    Each indicator includes a signal (bullish/bearish/neutral) and plain-language description.
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    candles = (
        db.query(DailyCandle)
        .filter(DailyCandle.stock_id == stock.id, DailyCandle.is_adjusted == False)
        .order_by(DailyCandle.date.asc())
        .all()
    )

    if not candles:
        return {
            "symbol": symbol.upper(),
            "indicators": [],
            "support_resistance": {"support": [], "resistance": []},
            "volume_analysis": {},
            "message": "No candle data available. Please refresh data first.",
        }

    data = [
        {
            "date": pd.to_datetime(c.date),
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": int(c.volume),
        }
        for c in candles
    ]
    df = pd.DataFrame(data)
    indicators = generate_technical_summary(df)

    return {
        "symbol": symbol.upper(),
        "indicators": [vars(ind) for ind in indicators],
        "candle_count": len(candles),
        "first_date": candles[0].date.isoformat(),
        "last_date": candles[-1].date.isoformat(),
    }


@router.get("/{symbol}/fundamentals")
def get_fundamentals(symbol: str, db: Session = Depends(get_db)):
    """Get fundamental analysis data for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    svc = FundamentalService(db)
    return svc.get_fundamental_summary(stock)


@router.get("/{symbol}/peers")
def get_peers(symbol: str, db: Session = Depends(get_db)):
    """Get peer comparison for a stock based on sector classification."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    if not stock.sector:
        return {
            "symbol": symbol.upper(),
            "sector": None,
            "peers": [],
            "message": "Sector not available for peer comparison.",
        }

    # Find stocks in the same sector
    peers = (
        db.query(Stock)
        .filter(Stock.sector == stock.sector, Stock.is_active == True)
        .limit(20)
        .all()
    )

    peer_data = []
    for peer in peers:
        quote = db.query(LatestQuote).filter(LatestQuote.stock_id == peer.id).first()
        
        # Get latest calculated ratios
        pe = db.query(CalculatedRatio).filter(
            CalculatedRatio.stock_id == peer.id,
            CalculatedRatio.ratio_name == "pe_ratio",
        ).order_by(CalculatedRatio.period_end_date.desc()).first()
        
        pb = db.query(CalculatedRatio).filter(
            CalculatedRatio.stock_id == peer.id,
            CalculatedRatio.ratio_name == "pb_ratio",
        ).order_by(CalculatedRatio.period_end_date.desc()).first()
        
        roe = db.query(CalculatedRatio).filter(
            CalculatedRatio.stock_id == peer.id,
            CalculatedRatio.ratio_name == "roe",
        ).order_by(CalculatedRatio.period_end_date.desc()).first()
        
        de = db.query(CalculatedRatio).filter(
            CalculatedRatio.stock_id == peer.id,
            CalculatedRatio.ratio_name == "debt_to_equity",
        ).order_by(CalculatedRatio.period_end_date.desc()).first()

        peer_data.append({
            "symbol": peer.symbol,
            "name": peer.name,
            "market_cap": float(quote.market_cap) if quote and quote.market_cap else None,
            "pe_ratio": float(pe.value) if pe and pe.value else None,
            "pb_ratio": float(pb.value) if pb and pb.value else None,
            "roe": float(roe.value) if roe and roe.value else None,
            "debt_to_equity": float(de.value) if de and de.value else None,
            "revenue_growth": None,  # Calculated when statement data is available
        })

    return {
        "symbol": symbol.upper(),
        "sector": stock.sector,
        "industry": stock.industry,
        "peers": peer_data,
    }
