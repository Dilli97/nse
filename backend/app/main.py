"""NSE Stock Analysis Platform - FastAPI Application."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db, SessionLocal
from app.models.stock import Exchange, Stock, Watchlist, WatchlistItem
from app.models.market_data import DailyCandle, IntradayCandle, LatestQuote, CorporateAction
from app.models.fundamental import FinancialStatement, CalculatedRatio, ShareholdingPattern
from app.models.report import ResearchReport
from app.api.router import api_router

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger(__name__)

SEED_STOCKS = [
    ("RELIANCE", "Reliance Industries Limited", "INE002A01018", "Oil & Gas", "Refineries"),
    ("TCS", "Tata Consultancy Services Limited", "INE467B01029", "IT", "IT Services"),
    ("INFY", "Infosys Limited", "INE009A01021", "IT", "IT Services"),
    ("HDFCBANK", "HDFC Bank Limited", "INE040A01034", "Financial Services", "Banks"),
    ("ICICIBANK", "ICICI Bank Limited", "INE090A01021", "Financial Services", "Banks"),
    ("ITC", "ITC Limited", "INE154A01025", "FMCG", "Tobacco & Cigarettes"),
    ("HINDUNILVR", "Hindustan Unilever Limited", "INE030A01027", "FMCG", "Personal Care"),
    ("BHARTIARTL", "Bharti Airtel Limited", "INE397D01024", "Telecom", "Telecom Services"),
    ("SBIN", "State Bank of India", "INE062A01020", "Financial Services", "Banks"),
    ("LT", "Larsen & Toubro Limited", "INE018A01030", "Construction", "Infrastructure"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("starting_application")
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Seed data
    db = SessionLocal()
    try:
        nse = db.query(Exchange).filter(Exchange.code == "NSE").first()
        if not nse:
            logger.info("seeding_database")
            nse = Exchange(
                code="NSE",
                name="National Stock Exchange of India",
                timezone="Asia/Kolkata",
                mic_code="XNSE",
            )
            db.add(nse)
            db.flush()

            wl = Watchlist(name="Default")
            db.add(wl)
            db.flush()

            for i, (sym, name, isin, sector, industry) in enumerate(SEED_STOCKS):
                stock = Stock(
                    symbol=sym,
                    name=name,
                    isin=isin,
                    exchange_id=nse.id,
                    sector=sector,
                    industry=industry,
                    is_active=True,
                )
                db.add(stock)
                db.flush()
                db.add(
                    WatchlistItem(
                        watchlist_id=wl.id, stock_id=stock.id, sort_order=i
                    )
                )

            db.commit()
            logger.info("database_seeded", stocks=len(SEED_STOCKS))
        else:
            logger.info("database_already_seeded")
    except Exception as e:
        logger.error("seed_error", error=str(e))
        db.rollback()
    finally:
        db.close()

    yield
    logger.info("shutting_down")


app = FastAPI(
    title="NSE Stock Analysis Platform",
    description="Self-hosted NSE stock analysis with technical and fundamental analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(",") if hasattr(settings, 'allowed_origins') else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router, prefix="/api")
