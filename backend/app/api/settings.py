"""Settings and CSV import endpoints."""
import csv
import io
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.stock import Stock
from app.models.market_data import DailyCandle
from app.models.fundamental import FinancialStatement

router = APIRouter()


@router.get("/providers")
def get_provider_status():
    """Get current provider configuration."""
    return {
        "default_provider": settings.default_provider,
        "broker_configured": bool(settings.broker_api_key),
        "ollama_configured": bool(settings.ollama_base_url),
        "market_timezone": settings.market_timezone,
    }


@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    symbol: str = Form(...),
    data_type: str = Form("candles"),  # 'candles' or 'financials'
    db: Session = Depends(get_db),
):
    """Import market data from a CSV file.

    Supported formats:
    - candles: date,open,high,low,close,volume
    - financials: period_end_date,period_type,statement_type,reporting_type,currency,unit,line_item,value

    Data quality is labeled as 'eod' for imported data.
    Import is idempotent - duplicate date+stock combinations are updated.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found. Add it first.")

    content = await file.read()
    text_content = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text_content))

    if data_type == "candles":
        return _import_candles(reader, stock, db, file.filename)
    elif data_type == "financials":
        return _import_financials(reader, stock, db, file.filename)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown data_type: {data_type}")


def _import_candles(reader: csv.DictReader, stock: Stock, db: Session, filename: str) -> dict:
    """Import daily candle data from CSV."""
    required_cols = {"date", "open", "high", "low", "close", "volume"}
    if not required_cols.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have columns: {', '.join(sorted(required_cols))}",
        )

    imported = 0
    updated = 0
    errors = []
    now = datetime.now(timezone.utc)

    for row_num, row in enumerate(reader, start=2):
        try:
            candle_date = date.fromisoformat(row["date"].strip())
            open_val = float(row["open"])
            high_val = float(row["high"])
            low_val = float(row["low"])
            close_val = float(row["close"])
            volume_val = int(float(row["volume"]))

            # Validation
            if high_val < low_val:
                errors.append(f"Row {row_num}: high ({high_val}) < low ({low_val})")
                continue
            if any(v < 0 for v in [open_val, high_val, low_val, close_val]):
                errors.append(f"Row {row_num}: negative price values")
                continue
            if volume_val < 0:
                errors.append(f"Row {row_num}: negative volume")
                continue

            existing = (
                db.query(DailyCandle)
                .filter(
                    DailyCandle.stock_id == stock.id,
                    DailyCandle.date == candle_date,
                    DailyCandle.is_adjusted == False,
                )
                .first()
            )

            if existing:
                existing.open = open_val
                existing.high = high_val
                existing.low = low_val
                existing.close = close_val
                existing.volume = volume_val
                existing.provider = f"csv:{filename}"
                existing.fetch_timestamp = now
                updated += 1
            else:
                dc = DailyCandle(
                    stock_id=stock.id,
                    date=candle_date,
                    open=open_val,
                    high=high_val,
                    low=low_val,
                    close=close_val,
                    volume=volume_val,
                    is_adjusted=False,
                    provider=f"csv:{filename}",
                    fetch_timestamp=now,
                )
                db.add(dc)
                imported += 1

        except (ValueError, KeyError) as e:
            errors.append(f"Row {row_num}: {str(e)}")
            continue

    db.commit()
    return {
        "status": "success",
        "symbol": stock.symbol,
        "imported": imported,
        "updated": updated,
        "errors": errors[:10],  # Limit error output
        "total_errors": len(errors),
    }


def _import_financials(
    reader: csv.DictReader, stock: Stock, db: Session, filename: str
) -> dict:
    """Import financial statement data from CSV."""
    required_cols = {
        "period_end_date", "period_type", "statement_type",
        "reporting_type", "currency", "unit", "line_item", "value",
    }
    if not required_cols.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have columns: {', '.join(sorted(required_cols))}",
        )

    # Group rows by statement period
    statements: dict = {}
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            key = (
                row["period_end_date"].strip(),
                row["period_type"].strip(),
                row["statement_type"].strip(),
                row["reporting_type"].strip(),
            )
            if key not in statements:
                statements[key] = {
                    "currency": row["currency"].strip(),
                    "unit": row["unit"].strip(),
                    "data": {},
                }
            statements[key]["data"][row["line_item"].strip()] = float(row["value"])
        except (ValueError, KeyError) as e:
            errors.append(f"Row {row_num}: {str(e)}")

    imported = 0
    now = datetime.now(timezone.utc)

    for (period_end, period_type, stmt_type, rpt_type), info in statements.items():
        try:
            period_date = date.fromisoformat(period_end)
            existing = (
                db.query(FinancialStatement)
                .filter(
                    FinancialStatement.stock_id == stock.id,
                    FinancialStatement.period_end_date == period_date,
                    FinancialStatement.period_type == period_type,
                    FinancialStatement.statement_type == stmt_type,
                    FinancialStatement.reporting_type == rpt_type,
                )
                .first()
            )

            if existing:
                existing.data_json = info["data"]
                existing.provider = f"csv:{filename}"
                existing.fetch_timestamp = now
            else:
                fs = FinancialStatement(
                    stock_id=stock.id,
                    statement_type=stmt_type,
                    period_type=period_type,
                    reporting_type=rpt_type,
                    period_end_date=period_date,
                    currency=info["currency"],
                    unit=info["unit"],
                    data_json=info["data"],
                    provider=f"csv:{filename}",
                    fetch_timestamp=now,
                )
                db.add(fs)
            imported += 1
        except Exception as e:
            errors.append(f"Statement {period_end}/{stmt_type}: {str(e)}")

    db.commit()
    return {
        "status": "success",
        "symbol": stock.symbol,
        "statements_imported": imported,
        "errors": errors[:10],
        "total_errors": len(errors),
    }
