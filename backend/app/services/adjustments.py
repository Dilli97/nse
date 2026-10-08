"""Corporate action adjustment service.

Maintains strict separation between raw price series and adjusted price series.
Adjusts historical OHLCV data for:
1. Stock Splits (e.g., 10:1 split divides past prices by 10, multiplies volume by 10)
2. Bonus Issues (e.g., 1:1 bonus divides past prices by 2, multiplies volume by 2)
3. Cash Dividends (Total Return adjustment factor: 1 - Dividend / Prev_Close)

Rules:
- Raw candle records maintain is_adjusted=False.
- Adjusted candles maintain is_adjusted=True and adjusted_close populated.
- Technical analysis defaults to raw completed candles unless explicitly adjusted.
"""
from datetime import date
from typing import List, Dict, Any, Optional
from decimal import Decimal
import pandas as pd


def adjust_candles_for_split(
    candles: List[Dict[str, Any]], split_ex_date: date, ratio_from: float, ratio_to: float
) -> List[Dict[str, Any]]:
    """Adjust candle history for stock split.

    A ratio_from:ratio_to split (e.g. 1:2 split means 1 old share becomes 2 new shares):
    - Factor = ratio_from / ratio_to (0.5 for 1:2)
    - Candles before split_ex_date have prices multiplied by Factor.
    - Candles before split_ex_date have volumes divided by Factor (multiplied by ratio_to/ratio_from).
    """
    if ratio_to <= 0 or ratio_from <= 0:
        return candles

    factor = ratio_from / ratio_to
    adjusted = []
    for c in candles:
        c_copy = dict(c)
        c_date = c_copy["date"]
        if isinstance(c_date, str):
            c_date = date.fromisoformat(c_date.split("T")[0])

        if c_date < split_ex_date:
            c_copy["open"] = round(float(c_copy["open"]) * factor, 4)
            c_copy["high"] = round(float(c_copy["high"]) * factor, 4)
            c_copy["low"] = round(float(c_copy["low"]) * factor, 4)
            c_copy["close"] = round(float(c_copy["close"]) * factor, 4)
            c_copy["adjusted_close"] = c_copy["close"]
            c_copy["volume"] = int(round(float(c_copy["volume"]) / factor))
            c_copy["is_adjusted"] = True
        else:
            c_copy["adjusted_close"] = float(c_copy["close"])
        adjusted.append(c_copy)
    return adjusted


def adjust_candles_for_bonus(
    candles: List[Dict[str, Any]], bonus_ex_date: date, bonus_ratio: float
) -> List[Dict[str, Any]]:
    """Adjust candle history for bonus issue.

    bonus_ratio = bonus shares / existing shares (e.g., 1:1 bonus is 1.0, 1:2 is 0.5):
    - Factor = 1 / (1 + bonus_ratio) (e.g. 1/2 = 0.5 for 1:1 bonus)
    - Historical prices before ex-date multiplied by Factor.
    - Historical volumes divided by Factor.
    """
    if bonus_ratio <= 0:
        return candles

    factor = 1.0 / (1.0 + bonus_ratio)
    adjusted = []
    for c in candles:
        c_copy = dict(c)
        c_date = c_copy["date"]
        if isinstance(c_date, str):
            c_date = date.fromisoformat(c_date.split("T")[0])

        if c_date < bonus_ex_date:
            c_copy["open"] = round(float(c_copy["open"]) * factor, 4)
            c_copy["high"] = round(float(c_copy["high"]) * factor, 4)
            c_copy["low"] = round(float(c_copy["low"]) * factor, 4)
            c_copy["close"] = round(float(c_copy["close"]) * factor, 4)
            c_copy["adjusted_close"] = c_copy["close"]
            c_copy["volume"] = int(round(float(c_copy["volume"]) / factor))
            c_copy["is_adjusted"] = True
        else:
            c_copy["adjusted_close"] = float(c_copy["close"])
        adjusted.append(c_copy)
    return adjusted


def calculate_dividend_adjusted_series(
    candles: List[Dict[str, Any]], dividends: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Compute total return price series adjusted for cash dividends.

    Adjustment factor on ex-date:
        multiplier = 1.0 - (dividend_amount / prior_day_close)
    All days preceding ex-date are adjusted downward by multiplier.
    """
    if not dividends or not candles:
        return candles

    df = pd.DataFrame(candles)
    if df.empty or "close" not in df.columns:
        return candles

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values("date").reset_index(drop=True)
    df["adj_factor"] = 1.0

    for div in sorted(dividends, key=lambda x: x["ex_date"], reverse=True):
        ex_date = div["ex_date"]
        if isinstance(ex_date, str):
            ex_date = date.fromisoformat(ex_date)
        div_amt = float(div["amount"])

        # Find candle on or immediately preceding ex_date
        prior_candles = df[df["date"] < ex_date]
        if not prior_candles.empty and div_amt > 0:
            prior_close = float(prior_candles.iloc[-1]["close"])
            if prior_close > div_amt:
                factor = 1.0 - (div_amt / prior_close)
                df.loc[df["date"] < ex_date, "adj_factor"] *= factor

    df["adjusted_close"] = (df["close"] * df["adj_factor"]).round(4)
    df["is_adjusted"] = True
    return df.to_dict(orient="records")
