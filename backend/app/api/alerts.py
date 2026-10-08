"""Price and technical indicator alert endpoints."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app.models.stock import Stock
from app.models.market_data import PriceAlert, LatestQuote, DailyCandle
from app.services.technical import calculate_rsi

router = APIRouter()


class AlertCreate(BaseModel):
    stock_id: int
    alert_type: str  # 'price_above', 'price_below', 'rsi_above', 'rsi_below'
    threshold: float
    notes: Optional[str] = None


class AlertOut(BaseModel):
    id: int
    stock_id: int
    symbol: str
    stock_name: str
    alert_type: str
    threshold: float
    is_active: bool
    triggered_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: str


@router.get("/", response_model=List[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    """List all created price/indicator alerts."""
    alerts = db.query(PriceAlert).order_by(PriceAlert.created_at.desc()).all()
    results = []
    for a in alerts:
        stock = db.query(Stock).filter(Stock.id == a.stock_id).first()
        results.append(
            AlertOut(
                id=a.id,
                stock_id=a.stock_id,
                symbol=stock.symbol if stock else "UNKNOWN",
                stock_name=stock.name if stock else "Unknown Stock",
                alert_type=a.alert_type,
                threshold=float(a.threshold),
                is_active=a.is_active,
                triggered_at=a.triggered_at.isoformat() if a.triggered_at else None,
                notes=a.notes,
                created_at=a.created_at.isoformat(),
            )
        )
    return results


@router.post("/", response_model=AlertOut)
def create_alert(req: AlertCreate, db: Session = Depends(get_db)):
    """Create a new price or RSI alert for a stock."""
    stock = db.query(Stock).filter(Stock.id == req.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    valid_types = {"price_above", "price_below", "rsi_above", "rsi_below"}
    if req.alert_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"alert_type must be one of {valid_types}")

    alert = PriceAlert(
        stock_id=stock.id,
        alert_type=req.alert_type,
        threshold=req.threshold,
        is_active=True,
        notes=req.notes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return AlertOut(
        id=alert.id,
        stock_id=alert.stock_id,
        symbol=stock.symbol,
        stock_name=stock.name,
        alert_type=alert.alert_type,
        threshold=float(alert.threshold),
        is_active=alert.is_active,
        triggered_at=None,
        notes=alert.notes,
        created_at=alert.created_at.isoformat(),
    )


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert."""
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}


@router.post("/evaluate")
def evaluate_alerts(db: Session = Depends(get_db)):
    """Evaluate all active alerts against latest quotes and indicators.
    
    Triggers matching alerts and records triggered_at timestamp.
    """
    alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
    triggered_count = 0
    now = datetime.now(timezone.utc)

    for alert in alerts:
        stock = db.query(Stock).filter(Stock.id == alert.stock_id).first()
        if not stock:
            continue

        quote = db.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
        current_price = float(quote.price) if quote and quote.price else None
        thresh = float(alert.threshold)

        should_trigger = False

        if alert.alert_type == "price_above" and current_price and current_price >= thresh:
            should_trigger = True
        elif alert.alert_type == "price_below" and current_price and current_price <= thresh:
            should_trigger = True
        elif "rsi" in alert.alert_type:
            candles = (
                db.query(DailyCandle)
                .filter(DailyCandle.stock_id == stock.id, DailyCandle.is_adjusted == False)
                .order_by(DailyCandle.date.asc())
                .all()
            )
            if len(candles) > 15:
                series = pd.Series([float(c.close) for c in candles])
                rsi_val = calculate_rsi(series, 14).iloc[-1]
                if not pd.isna(rsi_val):
                    if alert.alert_type == "rsi_above" and float(rsi_val) >= thresh:
                        should_trigger = True
                    elif alert.alert_type == "rsi_below" and float(rsi_val) <= thresh:
                        should_trigger = True

        if should_trigger:
            alert.triggered_at = now
            alert.is_active = False  # Deactivate once triggered
            triggered_count += 1

    db.commit()
    return {"evaluated": len(alerts), "triggered": triggered_count}
