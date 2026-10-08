"""NSE Trading Calendar utilities.

Uses exchange-calendars library for accurate holiday detection.
Falls back to basic weekday check if calendar data is unavailable.
"""
from datetime import date, time, datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

# NSE trading hours
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
PRE_OPEN_START = time(9, 0)
PRE_OPEN_END = time(9, 15)


def _get_calendar():
    """Get NSE trading calendar. Returns None if unavailable."""
    try:
        import exchange_calendars as xcals
        return xcals.get_calendar("XBOM")  # BSE calendar covers NSE holidays too
    except Exception:
        return None


def is_trading_day(check_date: date | None = None) -> bool:
    """Check if a given date is a trading day on NSE.
    
    Falls back to weekday check if exchange-calendars is unavailable.
    """
    if check_date is None:
        check_date = datetime.now(IST).date()
    
    cal = _get_calendar()
    if cal:
        try:
            return cal.is_session(check_date.isoformat())
        except Exception:
            pass
    
    # Fallback: weekdays only (no holiday awareness)
    return check_date.weekday() < 5


def is_market_open() -> bool:
    """Check if NSE market is currently open."""
    now = datetime.now(IST)
    if not is_trading_day(now.date()):
        return False
    current_time = now.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def get_last_trading_day(from_date: date | None = None) -> date:
    """Get the most recent trading day on or before from_date."""
    if from_date is None:
        from_date = datetime.now(IST).date()
    
    check = from_date
    for _ in range(10):  # Max 10 days back (long weekends + holidays)
        if is_trading_day(check):
            return check
        check = date.fromordinal(check.toordinal() - 1)
    
    return from_date  # Fallback


def market_status() -> dict:
    """Get current market status information."""
    now = datetime.now(IST)
    is_open = is_market_open()
    is_trading = is_trading_day(now.date())
    
    return {
        "is_open": is_open,
        "is_trading_day": is_trading,
        "current_time_ist": now.strftime("%H:%M:%S"),
        "current_date": now.date().isoformat(),
        "market_open_time": MARKET_OPEN.strftime("%H:%M"),
        "market_close_time": MARKET_CLOSE.strftime("%H:%M"),
        "status": "Open" if is_open else ("Closed (Holiday/Weekend)" if not is_trading else "Closed"),
    }
