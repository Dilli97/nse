"""Tests for technical indicator calculations."""
import pandas as pd
import numpy as np
from app.services.technical import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_volume_analysis,
    find_support_resistance,
    generate_technical_summary,
)


def test_sma_calculation(sample_candles_data):
    """Test SMA calculations and verify insufficient history behavior."""
    df = pd.DataFrame(sample_candles_data)
    close = df["close"]

    # SMA 20 on 25 candles should have values for index 19 onwards
    sma_20 = calculate_sma(close, 20)
    assert len(sma_20) == len(close)
    assert pd.isna(sma_20.iloc[0])
    assert pd.isna(sma_20.iloc[18])
    assert not pd.isna(sma_20.iloc[19])

    # Expected SMA 20 at index 19 is mean of first 20 closes
    expected_sma_20_first = close.iloc[:20].mean()
    assert round(sma_20.iloc[19], 2) == round(expected_sma_20_first, 2)

    # Insufficient history for SMA 50 on 25 candles
    sma_50 = calculate_sma(close, 50)
    assert sma_50.isna().all()


def test_ema_calculation(sample_candles_data):
    """Test EMA calculations."""
    df = pd.DataFrame(sample_candles_data)
    close = df["close"]

    ema_12 = calculate_ema(close, 12)
    assert len(ema_12) == len(close)
    # EMA starts computing immediately and reflects exponential smoothing
    assert not pd.isna(ema_12.iloc[-1])


def test_rsi_bounds_and_values(sample_candles_data):
    """Test RSI calculation and guarantee bounds between 0 and 100."""
    df = pd.DataFrame(sample_candles_data)
    close = df["close"]

    rsi_14 = calculate_rsi(close, 14)
    assert len(rsi_14) == len(close)

    valid_rsi = rsi_14.dropna()
    assert len(valid_rsi) > 0
    # RSI must be strictly bounded between 0 and 100
    assert (valid_rsi >= 0.0).all()
    assert (valid_rsi <= 100.0).all()


def test_macd_calculation(sample_candles_data):
    """Test MACD line, signal line, and histogram arithmetic."""
    df = pd.DataFrame(sample_candles_data)
    close = df["close"]

    macd_line, signal_line, hist = calculate_macd(close, fast=12, slow=26, signal=9)
    # Histogram must equal macd_line - signal_line
    diff = (macd_line - signal_line).dropna()
    hist_valid = hist.dropna()
    np.testing.assert_allclose(diff.values, hist_valid.values, rtol=1e-5)


def test_bollinger_bands(sample_candles_data):
    """Test Bollinger Bands relationships: Lower <= Middle <= Upper."""
    df = pd.DataFrame(sample_candles_data)
    close = df["close"]

    upper, mid, lower = calculate_bollinger_bands(close, period=20, std_dev=2.0)
    valid_idx = ~(upper.isna() | mid.isna() | lower.isna())

    assert (upper[valid_idx] >= mid[valid_idx]).all()
    assert (mid[valid_idx] >= lower[valid_idx]).all()


def test_atr_volatility(sample_candles_data):
    """Test Average True Range calculation is positive."""
    df = pd.DataFrame(sample_candles_data)
    atr = calculate_atr(df["high"], df["low"], df["close"], period=14)
    valid_atr = atr.dropna()

    assert len(valid_atr) > 0
    assert (valid_atr > 0).all()


def test_volume_analysis(sample_candles_data):
    """Test volume vs 20-period average."""
    df = pd.DataFrame(sample_candles_data)
    vol_res = calculate_volume_analysis(df["volume"], period=20)

    assert vol_res["current_volume"] is not None
    assert vol_res["avg_volume"] is not None
    assert vol_res["volume_ratio"] is not None
    assert vol_res["volume_ratio"] > 0


def test_support_resistance_rule_based(sample_candles_data):
    """Test support and resistance levels are valid numbers without predictive claims."""
    df = pd.DataFrame(sample_candles_data)
    sr = find_support_resistance(df["high"], df["low"], df["close"], lookback=20)

    assert "support" in sr
    assert "resistance" in sr
    assert "pivot" in sr
    assert sr["pivot"] is not None
    # Pivot should be between lowest low and highest high
    assert df["low"].min() <= sr["pivot"] <= df["high"].max()


def test_generate_technical_summary(sample_candles_data):
    """Test complete summary generation on completed candles."""
    df = pd.DataFrame(sample_candles_data)
    df["date"] = pd.to_datetime(df["date"])

    indicators = generate_technical_summary(df)
    assert len(indicators) > 0

    ind_names = [ind.name for ind in indicators]
    assert "SMA (20)" in ind_names
    assert "SMA (50)" in ind_names
    assert "RSI (14)" in ind_names
    assert "MACD (12,26,9)" in ind_names
    assert "Bollinger Bands (20,2)" in ind_names

    # Check that SMA (50) correctly reports insufficient data on 25 candles
    sma_50 = next(ind for ind in indicators if ind.name == "SMA (50)")
    assert sma_50.sufficient_data is False
    assert sma_50.value is None
    assert "Insufficient data" in sma_50.description
