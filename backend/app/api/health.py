"""Health check and system status endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from app.database import get_db
from app.config import settings
from app.utils.calendar import market_status

router = APIRouter()


@router.get("/")
def health_check(db: Session = Depends(get_db)):
    """Health check with database connectivity and provider status."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    mkt = market_status()

    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "provider": settings.default_provider,
        "provider_status": "configured",
        "market": mkt,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
