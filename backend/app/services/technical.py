"""Technical analysis calculations.

All indicators are calculated from actual stored market data.
Only completed candles are used (current day excluded if market is open).
Each indicator specifies required periods and reports insufficient data clearly.

Implementation notes:
- SMA: Simple arithmetic mean over the period
- EMA: Exponential moving average using the standard multiplier 2/(period+1)
- RSI: Uses Wilder's smoothing method (exponential moving average of gains/losses)
- MACD: Difference between fast and slow EMA, with signal line as EMA of MACD
- Bollinger Bands: SMA ± (standard deviation × multiplier)
- ATR: Wilder's Average True Range using true range calculation
- Support/Resistance: Pivot point method using recent high/low extrema
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class IndicatorResult:
    """Result of a technical indicator calculation."""
    name: str
    value: Optional[float]
    signal: str  # 'bullish', 'bearish', 'neutral'
    description: str  # Plain language explanation
    timeframe: str  # e.g., 'daily'
    latest_candle_date: str
    sufficient_data: bool
    periods_available: int
    periods_required: int


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average.
    
    Formula: SMA = sum(close[i] for i in range(period)) / period
    Requires at least `period` data points.
    """
    if len(prices) < period:
        return pd.Series([np.nan] * len(prices), index=prices.index)
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average.
    
    Formula: EMA = close × k + EMA_prev × (1 - k), where k = 2 / (period + 1)
    Uses pandas ewm with span parameter.
    Requires at least `period` data points.
    """
    if len(prices) < period:
        return pd.Series([np.nan] * len(prices), index=prices.index)
    return prices.ewm(span=period, adjust=False).mean()


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing.
    
    Formula:
    1. Calculate price changes: delta = close - close_prev
    2. Separate gains (positive deltas) and losses (negative deltas)
    3. First average: simple mean of first `period` gains/losses
    4. Subsequent: avg = (prev_avg × (period-1) + current) / period
    5. RS = average_gain / average_loss
    6. RSI = 100 - (100 / (1 + RS))
    
    Requires at least period + 1 data points.
    """
    if len(prices) < period + 1:
        return pd.Series([np.nan] * len(prices), index=prices.index)
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    # Wilder's smoothing (same as EMA with alpha=1/period)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def calculate_macd(
    prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence).
    
    Formula:
    - MACD line = EMA(fast) - EMA(slow)
    - Signal line = EMA(MACD line, signal period)
    - Histogram = MACD line - Signal line
    
    Requires at least slow + signal - 1 data points.
    """
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: pd.Series, period: int = 20, std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands.
    
    Formula:
    - Middle Band = SMA(period)
    - Upper Band = Middle Band + (std_dev × standard_deviation(period))
    - Lower Band = Middle Band - (std_dev × standard_deviation(period))
    
    Requires at least `period` data points.
    """
    sma = calculate_sma(prices, period)
    std = prices.rolling(window=period).std(ddof=0)
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


def calculate_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """Average True Range.
    
    Formula:
    True Range = max(high - low, |high - prev_close|, |low - prev_close|)
    ATR = Wilder's smoothing of True Range over `period`
    
    Requires at least `period + 1` data points.
    """
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's smoothing
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr


def calculate_volume_analysis(volume: pd.Series, period: int = 20) -> dict:
    """Volume analysis comparing current volume to moving average.
    
    Returns current volume, average volume, and ratio.
    Ratio > 1.5 suggests high activity, < 0.5 suggests low activity.
    """
    if len(volume) < period:
        return {
            "current_volume": int(volume.iloc[-1]) if len(volume) > 0 else None,
            "avg_volume": None,
            "volume_ratio": None,
            "assessment": "insufficient_data",
        }
    
    current_vol = int(volume.iloc[-1])
    avg_vol = float(volume.rolling(window=period).mean().iloc[-1])
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 0
    
    if vol_ratio >= 2.0:
        assessment = "Very high volume - significant activity"
    elif vol_ratio >= 1.5:
        assessment = "Above average volume - increased interest"
    elif vol_ratio >= 0.8:
        assessment = "Normal volume"
    elif vol_ratio >= 0.5:
        assessment = "Below average volume - reduced interest"
    else:
        assessment = "Very low volume - limited activity"
    
    return {
        "current_volume": current_vol,
        "avg_volume": round(avg_vol),
        "volume_ratio": round(vol_ratio, 2),
        "assessment": assessment,
    }


def find_support_resistance(
    high: pd.Series, low: pd.Series, close: pd.Series, lookback: int = 60
) -> dict:
    """Rule-based support and resistance using pivot points and local extrema.
    
    Method:
    1. Classic pivot: P = (H + L + C) / 3, R1 = 2P - L, S1 = 2P - H
    2. Local extrema: significant highs/lows in the lookback period
    
    Transparent rules: support/resistance levels are derived purely from
    price action without any predictive claims.
    """
    if len(close) < max(lookback, 5):
        return {"support": [], "resistance": [], "pivot": None, "method": "insufficient_data"}
    
    recent_high = high.tail(lookback)
    recent_low = low.tail(lookback)
    recent_close = close.tail(lookback)
    
    # Classic pivot point
    h = float(recent_high.iloc[-1])
    l = float(recent_low.iloc[-1])
    c = float(recent_close.iloc[-1])
    pivot = round((h + l + c) / 3, 2)
    r1 = round(2 * pivot - l, 2)
    s1 = round(2 * pivot - h, 2)
    r2 = round(pivot + (h - l), 2)
    s2 = round(pivot - (h - l), 2)
    
    # Local extrema (peaks and troughs)
    window = min(10, lookback // 3)
    local_highs = []
    local_lows = []
    
    for i in range(window, len(recent_high) - window):
        if recent_high.iloc[i] == recent_high.iloc[i - window:i + window + 1].max():
            local_highs.append(float(recent_high.iloc[i]))
        if recent_low.iloc[i] == recent_low.iloc[i - window:i + window + 1].min():
            local_lows.append(float(recent_low.iloc[i]))
    
    # Combine pivot and local extrema, deduplicate nearby levels
    resistance_levels = sorted(set([r1, r2] + local_highs), reverse=True)[:3]
    support_levels = sorted(set([s1, s2] + local_lows))[:3]
    
    return {
        "support": [round(s, 2) for s in support_levels],
        "resistance": [round(r, 2) for r in resistance_levels],
        "pivot": pivot,
        "method": "pivot_points_and_local_extrema",
    }


def generate_technical_summary(df: pd.DataFrame) -> List[IndicatorResult]:
    """Generate all technical indicators from a DataFrame with OHLCV columns.
    
    DataFrame must have columns: date, open, high, low, close, volume.
    Uses only completed candles.
    
    Returns a list of IndicatorResult objects, each with:
    - A rule-based signal (bullish, bearish, neutral)
    - A plain language description of what the signal means
    - Clear identification of insufficient data
    
    DISCLAIMER: These are rule-based observations, not trading recommendations.
    No guaranteed returns or probability estimates are provided.
    """
    if df.empty or "close" not in df.columns:
        return []
    
    df = df.copy().sort_values("date").reset_index(drop=True)
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    latest_date = str(df["date"].iloc[-1])[:10]
    n = len(df)
    current_price = float(close.iloc[-1])
    
    results: List[IndicatorResult] = []
    
    # --- SMA: 20, 50, 200 ---
    for period in [20, 50, 200]:
        sma = calculate_sma(close, period)
        sufficient = n >= period
        sma_val = round(float(sma.iloc[-1]), 2) if sufficient and not pd.isna(sma.iloc[-1]) else None
        
        if sma_val is not None:
            if current_price > sma_val * 1.02:
                signal, desc = "bullish", f"Price (₹{current_price:.2f}) is above {period}-day SMA (₹{sma_val:.2f}), indicating upward momentum"
            elif current_price < sma_val * 0.98:
                signal, desc = "bearish", f"Price (₹{current_price:.2f}) is below {period}-day SMA (₹{sma_val:.2f}), indicating downward pressure"
            else:
                signal, desc = "neutral", f"Price (₹{current_price:.2f}) is near {period}-day SMA (₹{sma_val:.2f})"
        else:
            signal, desc = "neutral", f"Insufficient data for {period}-day SMA (need {period} periods, have {n})"
        
        results.append(IndicatorResult(
            name=f"SMA ({period})",
            value=sma_val,
            signal=signal,
            description=desc,
            timeframe="daily",
            latest_candle_date=latest_date,
            sufficient_data=sufficient,
            periods_available=n,
            periods_required=period,
        ))
    
    # --- EMA: 12, 26 ---
    for period in [12, 26]:
        ema = calculate_ema(close, period)
        sufficient = n >= period
        ema_val = round(float(ema.iloc[-1]), 2) if sufficient and not pd.isna(ema.iloc[-1]) else None
        
        if ema_val is not None:
            if current_price > ema_val * 1.01:
                signal, desc = "bullish", f"Price is above {period}-day EMA (₹{ema_val:.2f})"
            elif current_price < ema_val * 0.99:
                signal, desc = "bearish", f"Price is below {period}-day EMA (₹{ema_val:.2f})"
            else:
                signal, desc = "neutral", f"Price is near {period}-day EMA (₹{ema_val:.2f})"
        else:
            signal, desc = "neutral", f"Insufficient data for {period}-day EMA"
        
        results.append(IndicatorResult(
            name=f"EMA ({period})",
            value=ema_val,
            signal=signal,
            description=desc,
            timeframe="daily",
            latest_candle_date=latest_date,
            sufficient_data=sufficient,
            periods_available=n,
            periods_required=period,
        ))
    
    # --- RSI (14) ---
    rsi = calculate_rsi(close, 14)
    sufficient_rsi = n > 14
    rsi_val = round(float(rsi.iloc[-1]), 2) if sufficient_rsi and not pd.isna(rsi.iloc[-1]) else None
    
    if rsi_val is not None:
        if rsi_val > 70:
            signal, desc = "bearish", f"RSI at {rsi_val:.1f} indicates overbought conditions (above 70). This may suggest the stock is overextended."
        elif rsi_val > 60:
            signal, desc = "bullish", f"RSI at {rsi_val:.1f} shows bullish momentum (60-70 range)"
        elif rsi_val < 30:
            signal, desc = "bullish", f"RSI at {rsi_val:.1f} indicates oversold conditions (below 30). This may suggest a potential reversal."
        elif rsi_val < 40:
            signal, desc = "bearish", f"RSI at {rsi_val:.1f} shows bearish momentum (30-40 range)"
        else:
            signal, desc = "neutral", f"RSI at {rsi_val:.1f} is in neutral territory (40-60 range)"
    else:
        signal, desc = "neutral", "Insufficient data for RSI calculation"
    
    results.append(IndicatorResult(
        name="RSI (14)",
        value=rsi_val,
        signal=signal,
        description=desc,
        timeframe="daily",
        latest_candle_date=latest_date,
        sufficient_data=sufficient_rsi,
        periods_available=n,
        periods_required=15,
    ))
    
    # --- MACD (12, 26, 9) ---
    macd_line, signal_line, histogram = calculate_macd(close, 12, 26, 9)
    sufficient_macd = n >= 35  # 26 + 9
    macd_val = round(float(macd_line.iloc[-1]), 2) if sufficient_macd and not pd.isna(macd_line.iloc[-1]) else None
    hist_val = round(float(histogram.iloc[-1]), 2) if sufficient_macd and not pd.isna(histogram.iloc[-1]) else None
    sig_val = round(float(signal_line.iloc[-1]), 2) if sufficient_macd and not pd.isna(signal_line.iloc[-1]) else None
    
    if hist_val is not None:
        if hist_val > 0 and (len(histogram) > 1 and histogram.iloc[-2] <= 0):
            signal, desc = "bullish", f"MACD histogram just turned positive (bullish crossover). MACD: {macd_val}, Signal: {sig_val}"
        elif hist_val < 0 and (len(histogram) > 1 and histogram.iloc[-2] >= 0):
            signal, desc = "bearish", f"MACD histogram just turned negative (bearish crossover). MACD: {macd_val}, Signal: {sig_val}"
        elif hist_val > 0:
            signal, desc = "bullish", f"MACD line ({macd_val}) is above signal line ({sig_val}), indicating bullish momentum"
        elif hist_val < 0:
            signal, desc = "bearish", f"MACD line ({macd_val}) is below signal line ({sig_val}), indicating bearish momentum"
        else:
            signal, desc = "neutral", "MACD and signal lines are converging"
    else:
        signal, desc = "neutral", "Insufficient data for MACD calculation"
    
    results.append(IndicatorResult(
        name="MACD (12,26,9)",
        value=macd_val,
        signal=signal,
        description=desc,
        timeframe="daily",
        latest_candle_date=latest_date,
        sufficient_data=sufficient_macd,
        periods_available=n,
        periods_required=35,
    ))
    
    # --- Bollinger Bands (20, 2) ---
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close, 20, 2.0)
    sufficient_bb = n >= 20
    bb_upper_val = round(float(bb_upper.iloc[-1]), 2) if sufficient_bb and not pd.isna(bb_upper.iloc[-1]) else None
    bb_lower_val = round(float(bb_lower.iloc[-1]), 2) if sufficient_bb and not pd.isna(bb_lower.iloc[-1]) else None
    bb_mid_val = round(float(bb_middle.iloc[-1]), 2) if sufficient_bb and not pd.isna(bb_middle.iloc[-1]) else None
    
    if bb_upper_val is not None and bb_lower_val is not None:
        bb_width = bb_upper_val - bb_lower_val
        if current_price >= bb_upper_val:
            signal, desc = "bearish", f"Price at upper Bollinger Band (₹{bb_upper_val:.2f}). Band width: ₹{bb_width:.2f}. May indicate overextension."
        elif current_price <= bb_lower_val:
            signal, desc = "bullish", f"Price at lower Bollinger Band (₹{bb_lower_val:.2f}). Band width: ₹{bb_width:.2f}. May indicate oversold."
        else:
            pct_b = (current_price - bb_lower_val) / bb_width if bb_width > 0 else 0.5
            signal = "neutral"
            desc = f"Price within Bollinger Bands. Upper: ₹{bb_upper_val:.2f}, Lower: ₹{bb_lower_val:.2f}. %B: {pct_b:.2f}"
    else:
        signal, desc = "neutral", "Insufficient data for Bollinger Bands"
    
    results.append(IndicatorResult(
        name="Bollinger Bands (20,2)",
        value=bb_mid_val,
        signal=signal,
        description=desc,
        timeframe="daily",
        latest_candle_date=latest_date,
        sufficient_data=sufficient_bb,
        periods_available=n,
        periods_required=20,
    ))
    
    # --- ATR (14) ---
    atr = calculate_atr(high, low, close, 14)
    sufficient_atr = n >= 15
    atr_val = round(float(atr.iloc[-1]), 2) if sufficient_atr and not pd.isna(atr.iloc[-1]) else None
    
    if atr_val is not None:
        atr_pct = (atr_val / current_price) * 100
        if atr_pct > 3:
            signal, desc = "neutral", f"ATR: ₹{atr_val:.2f} ({atr_pct:.1f}% of price). High volatility."
        elif atr_pct > 1.5:
            signal, desc = "neutral", f"ATR: ₹{atr_val:.2f} ({atr_pct:.1f}% of price). Moderate volatility."
        else:
            signal, desc = "neutral", f"ATR: ₹{atr_val:.2f} ({atr_pct:.1f}% of price). Low volatility."
    else:
        signal, desc = "neutral", "Insufficient data for ATR calculation"
    
    results.append(IndicatorResult(
        name="ATR (14)",
        value=atr_val,
        signal=signal,
        description=desc,
        timeframe="daily",
        latest_candle_date=latest_date,
        sufficient_data=sufficient_atr,
        periods_available=n,
        periods_required=15,
    ))
    
    # --- Volume Analysis ---
    vol_analysis = calculate_volume_analysis(volume, 20)
    vol_ratio = vol_analysis.get("volume_ratio")
    sufficient_vol = vol_ratio is not None
    
    if vol_ratio is not None:
        if vol_ratio >= 1.5:
            signal = "bullish" if current_price > float(close.iloc[-2]) else "bearish"
            desc = f"Volume {vol_ratio:.1f}x average. {vol_analysis['assessment']}."
        elif vol_ratio <= 0.5:
            signal, desc = "neutral", f"Volume {vol_ratio:.1f}x average. {vol_analysis['assessment']}."
        else:
            signal, desc = "neutral", f"Volume {vol_ratio:.1f}x average. {vol_analysis['assessment']}."
    else:
        signal, desc = "neutral", "Insufficient data for volume analysis"
    
    results.append(IndicatorResult(
        name="Volume vs 20-day Avg",
        value=vol_ratio,
        signal=signal,
        description=desc,
        timeframe="daily",
        latest_candle_date=latest_date,
        sufficient_data=sufficient_vol,
        periods_available=n,
        periods_required=20,
    ))
    
    return results
