"""Research report generation and retrieval endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.stock import Stock
from app.models.report import ResearchReport
from app.services.reports import ReportService

router = APIRouter()


@router.post("/{symbol}/report")
def generate_report(symbol: str, db: Session = Depends(get_db)):
    """Generate a research report for a stock.
    
    Uses deterministic template-based generation by default.
    If Ollama is configured and available, can optionally use LLM enhancement.
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    svc = ReportService(db)
    report = svc.generate_report(stock)
    return report


@router.get("/{symbol}/report/latest")
def get_latest_report(symbol: str, db: Session = Depends(get_db)):
    """Get the most recent research report for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    report = (
        db.query(ResearchReport)
        .filter(ResearchReport.stock_id == stock.id)
        .order_by(ResearchReport.generated_at.desc())
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="No report found. Generate one first using POST.",
        )

    return {
        "id": report.id,
        "stock_id": report.stock_id,
        "symbol": stock.symbol,
        "report_type": report.report_type,
        "generated_at": report.generated_at.isoformat(),
        "generation_method": report.generation_method,
        "sections": report.report_json.get("sections", []) if report.report_json else [],
        "data_freshness": report.data_freshness_json or {},
        "llm_model": report.llm_model,
    }
