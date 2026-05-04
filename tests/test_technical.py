import pandas as pd
import numpy as np
import pytest

def _make_df(n=80):
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    open_ = close * (1 + np.random.randn(n) * 0.003)
    high = np.maximum(close, open_) * (1 + abs(np.random.randn(n) * 0.003))
    low = np.minimum(close, open_) * (1 - abs(np.random.randn(n) * 0.003))
    volume = np.random.randint(1000, 5000, n).astype(float)
    return pd.DataFrame({
        "date": dates.astype(str),
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })

def test_compute_indicators_adds_columns():
    from indicators.technical import compute_indicators
    df = _make_df()
    result = compute_indicators(df)
    for col in ["bb_upper", "bb_mid", "bb_lower", "bb_width",
                "kd_k", "kd_d", "macd_dif", "macd_signal", "macd_osc",
                "ma5", "ma20", "ma60", "rsi14", "vol_ma20"]:
        assert col in result.columns, f"Missing column: {col}"

def test_bb_upper_always_gt_lower():
    from indicators.technical import compute_indicators
    df = _make_df()
    result = compute_indicators(df).dropna()
    assert (result["bb_upper"] > result["bb_lower"]).all()

def test_kd_range_0_to_100():
    from indicators.technical import compute_indicators
    df = _make_df()
    result = compute_indicators(df).dropna()
    assert result["kd_k"].between(0, 100).all()
    assert result["kd_d"].between(0, 100).all()

def test_technical_summary_returns_8_items():
    from indicators.technical import compute_indicators, technical_summary
    df = compute_indicators(_make_df()).dropna().reset_index(drop=True)
    summary = technical_summary(df)
    assert len(summary) == 8
    for item in summary:
        assert "label" in item and "value" in item and "direction" in item
        assert item["direction"] in ("up", "down", "neutral")

def test_key_levels_has_required_keys():
    from indicators.technical import compute_indicators, key_levels
    df = compute_indicators(_make_df()).dropna().reset_index(drop=True)
    levels = key_levels(df)
    for k in ["resistance", "pullback", "support", "breakdown", "breakout"]:
        assert k in levels

def test_detect_patterns_returns_w_and_m():
    from indicators.technical import compute_indicators, detect_patterns
    df = compute_indicators(_make_df()).dropna().reset_index(drop=True)
    patterns = detect_patterns(df)
    assert "w_bottom" in patterns and "m_top" in patterns
    assert "formed" in patterns["w_bottom"] and "reason" in patterns["w_bottom"]
