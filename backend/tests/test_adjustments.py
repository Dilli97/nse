"""Tests for corporate action price adjustments (splits, bonuses, dividends)."""
from datetime import date
from app.services.adjustments import (
    adjust_candles_for_split,
    adjust_candles_for_bonus,
    calculate_dividend_adjusted_series,
)


def test_split_adjustment():
    """Verify 1:2 stock split halves pre-split price and doubles pre-split volume."""
    raw_candles = [
        {"date": "2024-01-10", "open": 2000.0, "high": 2050.0, "low": 1980.0, "close": 2020.0, "volume": 100000},
        {"date": "2024-01-11", "open": 2020.0, "high": 2040.0, "low": 2000.0, "close": 2010.0, "volume": 120000},
        # Split ex-date is 2024-01-12 (1:2 split -> 1 old share becomes 2 new shares)
        {"date": "2024-01-12", "open": 1005.0, "high": 1020.0, "low": 995.0, "close": 1010.0, "volume": 250000},
    ]

    adjusted = adjust_candles_for_split(
        raw_candles, split_ex_date=date(2024, 1, 12), ratio_from=1.0, ratio_to=2.0
    )

    assert len(adjusted) == 3

    # Pre-split candle on Jan 10 must be halved in price and doubled in volume
    assert adjusted[0]["close"] == 1010.0
    assert adjusted[0]["volume"] == 200000
    assert adjusted[0]["is_adjusted"] is True

    # Pre-split candle on Jan 11 must be halved
    assert adjusted[1]["close"] == 1005.0
    assert adjusted[1]["volume"] == 240000

    # Post-split candle on Jan 12 remains unchanged in close
    assert adjusted[2]["close"] == 1010.0
    assert adjusted[2]["volume"] == 250000


def test_bonus_issue_adjustment():
    """Verify 1:1 bonus issue (bonus_ratio=1.0) halves pre-bonus price."""
    raw_candles = [
        {"date": "2024-02-01", "open": 3000.0, "high": 3100.0, "low": 2950.0, "close": 3000.0, "volume": 50000},
        # Ex-date 2024-02-02
        {"date": "2024-02-02", "open": 1500.0, "high": 1550.0, "low": 1490.0, "close": 1520.0, "volume": 110000},
    ]

    adjusted = adjust_candles_for_bonus(
        raw_candles, bonus_ex_date=date(2024, 2, 2), bonus_ratio=1.0
    )

    # 1:1 bonus factor is 1 / (1 + 1) = 0.5
    assert adjusted[0]["close"] == 1500.0
    assert adjusted[0]["volume"] == 100000
    assert adjusted[0]["is_adjusted"] is True

    # Post-bonus candle is untouched
    assert adjusted[1]["close"] == 1520.0


def test_cash_dividend_adjustment():
    """Verify dividend adjustment calculates total-return multiplier correctly."""
    raw_candles = [
        {"date": "2024-03-01", "open": 1000.0, "high": 1020.0, "low": 990.0, "close": 1000.0, "volume": 50000},
        {"date": "2024-03-04", "open": 980.0, "high": 995.0, "low": 970.0, "close": 985.0, "volume": 60000},
    ]
    # ₹20 dividend on 2024-03-04. Prior close = 1000. Factor = 1 - (20/1000) = 0.98
    dividends = [{"ex_date": "2024-03-04", "amount": 20.0}]

    adjusted = calculate_dividend_adjusted_series(raw_candles, dividends)

    assert len(adjusted) == 2
    assert adjusted[0]["adjusted_close"] == 980.0  # 1000 * 0.98 = 980
    assert adjusted[1]["adjusted_close"] == 985.0  # Unadjusted on/after ex-date
