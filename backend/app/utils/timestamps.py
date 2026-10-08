"""Timezone and timestamp utilities.

All database timestamps are stored in UTC.
Market display uses Asia/Kolkata (IST, UTC+5:30).
Data freshness is calculated relative to the current UTC time.
"""
from datetime import datetime, timezone, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.UTC


def now_utc() -> datetime:
    """Current time in UTC with timezone info."""
    return datetime.now(timezone.utc)


def now_ist() -> datetime:
    """Current time in IST."""
    return datetime.now(IST)


def utc_to_ist(dt: datetime) -> datetime:
    """Convert UTC datetime to IST."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def ist_to_utc(dt: datetime) -> datetime:
    """Convert IST datetime to UTC."""
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    return dt.astimezone(UTC)


def data_age_seconds(fetch_timestamp: datetime) -> float:
    """Calculate age of data in seconds from fetch_timestamp to now."""
    if fetch_timestamp is None:
        return float('inf')
    now = now_utc()
    if fetch_timestamp.tzinfo is None:
        fetch_timestamp = fetch_timestamp.replace(tzinfo=timezone.utc)
    return (now - fetch_timestamp).total_seconds()


def classify_freshness(fetch_timestamp: datetime, is_market_hours: bool = False) -> str:
    """Classify data freshness.
    
    Returns: 'live', 'delayed', 'eod', 'stale'
    - live: < 5 seconds old (only during market hours with live provider)
    - delayed: < 20 minutes old  
    - eod: < 24 hours old
    - stale: > 24 hours old
    """
    age = data_age_seconds(fetch_timestamp)
    if age < 5 and is_market_hours:
        return 'live'
    elif age < 1200:  # 20 minutes
        return 'delayed'
    elif age < 86400:  # 24 hours
        return 'eod'
    else:
        return 'stale'
