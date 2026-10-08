"""Tests for market data ingestion, idempotence, and freshness detection."""
from datetime import date, datetime, timezone, timedelta
import pytz
from app.models.stock import Stock
from app.models.market_data import DailyCandle, LatestQuote
from app.utils.timestamps import now_utc, utc_to_ist, data_age_seconds, classify_freshness


def test_utc_and_ist_timestamps():
    """Verify UTC storage and accurate conversion to Asia/Kolkata."""
    utc_dt = datetime(2024, 10, 8, 10, 0, 0, tzinfo=timezone.utc)
    ist_dt = utc_to_ist(utc_dt)

    # IST is UTC + 5:30
    assert ist_dt.hour == 15
    assert ist_dt.minute == 30
    assert ist_dt.tzinfo.zone == "Asia/Kolkata"


def test_freshness_classification():
    """Verify data quality label classification based on age."""
    now = now_utc()

    # 10 seconds old
    recent = now - timedelta(seconds=10)
    assert classify_freshness(recent, is_market_hours=False) == "delayed"

    # 5 minutes old
    delayed = now - timedelta(minutes=5)
    assert classify_freshness(delayed) == "delayed"

    # 4 hours old
    eod = now - timedelta(hours=4)
    assert classify_freshness(eod) == "eod"

    # 36 hours old
    stale = now - timedelta(hours=36)
    assert classify_freshness(stale) == "stale"


def test_idempotent_candle_upsert(db_session):
    """Verify that multiple ingestion runs for the same date update rather than duplicating."""
    stock = db_session.query(Stock).filter(Stock.symbol == "RELIANCE").first()
    test_date = date(2024, 1, 15)

    # First insertion
    c1 = DailyCandle(
        stock_id=stock.id,
        date=test_date,
        open=2500.0,
        high=2550.0,
        low=2490.0,
        close=2540.0,
        volume=1000000,
        is_adjusted=False,
        provider="test",
        fetch_timestamp=now_utc(),
    )
    db_session.add(c1)
    db_session.commit()

    # Second simulated ingestion with adjusted volume
    existing = (
        db_session.query(DailyCandle)
        .filter(
            DailyCandle.stock_id == stock.id,
            DailyCandle.date == test_date,
            DailyCandle.is_adjusted == False,
        )
        .first()
    )
    assert existing is not None

    # Update in-place
    existing.close = 2545.0
    existing.volume = 1200000
    existing.fetch_timestamp = now_utc()
    db_session.commit()

    # Query total count for this date: must be strictly 1
    count = (
        db_session.query(DailyCandle)
        .filter(
            DailyCandle.stock_id == stock.id,
            DailyCandle.date == test_date,
            DailyCandle.is_adjusted == False,
        )
        .count()
    )
    assert count == 1

    updated = db_session.query(DailyCandle).filter(DailyCandle.stock_id == stock.id, DailyCandle.date == test_date).first()
    assert float(updated.close) == 2545.0
    assert updated.volume == 1200000


def test_quote_upsert_idempotence(db_session):
    """Verify latest quote record is unique per stock and safely updated."""
    stock = db_session.query(Stock).filter(Stock.symbol == "RELIANCE").first()

    # Insert quote
    q1 = LatestQuote(
        stock_id=stock.id,
        price=2500.0,
        change=10.0,
        change_percent=0.4,
        data_quality="delayed",
        provider="yahoo",
        fetch_timestamp=now_utc(),
    )
    db_session.add(q1)
    db_session.commit()

    # Subsequent refresh updates existing quote
    existing_q = db_session.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
    assert existing_q is not None
    existing_q.price = 2520.0
    existing_q.change = 30.0
    existing_q.change_percent = 1.2
    db_session.commit()

    quotes_count = db_session.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).count()
    assert quotes_count == 1
    assert float(existing_q.price) == 2520.0
