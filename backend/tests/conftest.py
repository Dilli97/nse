"""Pytest fixtures for NSE stock analysis backend."""
import json
from pathlib import Path
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.stock import Exchange, Stock, Watchlist, WatchlistItem
from app.models.market_data import DailyCandle, LatestQuote, PriceAlert, CorporateAction
from app.models.fundamental import FinancialStatement, ShareholdingPattern
from app.models.report import ResearchReport

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed basic NSE exchange
    nse = Exchange(code="NSE", name="National Stock Exchange of India", timezone="Asia/Kolkata")
    session.add(nse)
    session.flush()

    # Seed test stock
    stock = Stock(
        symbol="RELIANCE",
        name="Reliance Industries Limited",
        isin="INE002A01018",
        exchange_id=nse.id,
        sector="Oil & Gas",
        industry="Refineries",
        is_active=True,
    )
    session.add(stock)

    bank_stock = Stock(
        symbol="HDFCBANK",
        name="HDFC Bank Limited",
        isin="INE040A01034",
        exchange_id=nse.id,
        sector="Banks",
        industry="Private Sector Bank",
        is_active=True,
    )
    session.add(bank_stock)

    session.commit()
    yield session
    session.close()


@pytest.fixture
def sample_candles_data():
    """Load JSON sample candles fixture."""
    with open(FIXTURES_DIR / "sample_candles.json", "r") as f:
        return json.load(f)


@pytest.fixture
def sample_financials_data():
    """Load JSON sample financials fixture."""
    with open(FIXTURES_DIR / "sample_financials.json", "r") as f:
        return json.load(f)
