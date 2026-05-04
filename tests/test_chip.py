import pandas as pd
import pytest


def _make_chip_raw(dates, values):
    """模擬 FinMind 三大法人原始格式。"""
    rows = []
    for date, (foreign, trust, dealer) in zip(dates, values):
        rows += [
            {"date": date, "name": "Foreign_Investor", "buy": max(foreign, 0) * 1000, "sell": max(-foreign, 0) * 1000},
            {"date": date, "name": "Investment_Trust",  "buy": max(trust, 0)   * 1000, "sell": max(-trust, 0)   * 1000},
            {"date": date, "name": "Dealer_self",       "buy": max(dealer, 0)  * 1000, "sell": max(-dealer, 0)  * 1000},
        ]
    return pd.DataFrame(rows)


def _make_price_df(close=4000, high60=4500, vol=2000, vol_ma20=3000):
    closes = [close] * 60
    closes[0] = high60
    vols = [vol] * 60
    vol_ma20_vals = [vol_ma20] * 60
    return pd.DataFrame({
        "close": closes, "volume": vols, "vol_ma20": vol_ma20_vals
    })


def test_aggregate_chip_returns_correct_columns():
    from indicators.chip import aggregate_chip
    dates = ["2026-04-28", "2026-04-29", "2026-04-30"]
    raw = _make_chip_raw(dates, [(100, 20, -10), (-50, 5, 30), (200, -10, 15)])
    result = aggregate_chip(raw)
    assert set(["日期", "外資", "投信", "自營", "合計", "10日累計"]).issubset(result.columns)
    assert len(result) == 3


def test_aggregate_chip_sums_correctly():
    from indicators.chip import aggregate_chip
    dates = ["2026-04-30"]
    raw = _make_chip_raw(dates, [(100, 20, -10)])
    result = aggregate_chip(raw)
    assert result.iloc[0]["外資"] == 100
    assert result.iloc[0]["投信"] == 20
    assert result.iloc[0]["自營"] == -10
    assert result.iloc[0]["合計"] == 110


def test_signal_buying():
    from indicators.chip import aggregate_chip, main_force_signal
    dates = [f"2026-04-{20+i:02d}" for i in range(7)]
    raw = _make_chip_raw(dates, [(200, 50, 30)] * 7)
    chip = aggregate_chip(raw)
    price = _make_price_df(close=4000, high60=4500)
    sig = main_force_signal(chip, price)
    assert sig["label"] == "吸籌期"


def test_signal_distribution():
    from indicators.chip import aggregate_chip, main_force_signal
    dates = [f"2026-04-{20+i:02d}" for i in range(7)]
    raw = _make_chip_raw(dates, [(-200, -50, -30)] * 7)
    chip = aggregate_chip(raw)
    price = _make_price_df(close=4400, high60=4500)
    sig = main_force_signal(chip, price)
    assert sig["label"] == "出貨初期"


def test_aggregate_chip_maps_all_aliases():
    from indicators.chip import aggregate_chip
    dates = ["2026-04-30"]
    rows = [
        {"date": "2026-04-30", "name": "Foreign_Dealer_Self", "buy": 50000, "sell": 0},
        {"date": "2026-04-30", "name": "Dealer_Hedging",      "buy": 0,     "sell": 30000},
    ]
    raw = pd.DataFrame(rows)
    result = aggregate_chip(raw)
    assert result.iloc[0]["外資"] == 50   # 50000 / 1000
    assert result.iloc[0]["自營"] == -30  # -30000 / 1000


def test_signal_consolidation():
    from indicators.chip import aggregate_chip, main_force_signal
    # recent5 < 500, vol_ratio < 0.8
    dates = [f"2026-04-{20+i:02d}" for i in range(7)]
    raw = _make_chip_raw(dates, [(30, 10, -5)] * 7)  # recent5 = 5*35 = 175 < 500
    chip = aggregate_chip(raw)
    # Create df where last-day volume is lower than 20-day average
    closes = [4000] * 60
    closes[0] = 4500
    # First 59 days: volume=3000, last day: volume=2000
    vols = [3000] * 59 + [2000]
    vol_ma20_vals = [3000] * 60
    price = pd.DataFrame({"close": closes, "volume": vols, "vol_ma20": vol_ma20_vals})
    sig = main_force_signal(chip, price)
    assert sig["label"] == "整理期"


def test_signal_neutral():
    from indicators.chip import aggregate_chip, main_force_signal
    # recent5 ~ 350 (below 500), vol_ratio > 0.8 → should be 觀望
    dates = [f"2026-04-{20+i:02d}" for i in range(7)]
    raw = _make_chip_raw(dates, [(50, 10, 10)] * 7)  # recent5 = 5*70 = 350 < 500
    chip = aggregate_chip(raw)
    # vol=3000 for all days → vol_ratio = 1.0 > 0.8 (not consolidation)
    price = _make_price_df(close=4000, high60=4500, vol=3000, vol_ma20=3000)
    sig = main_force_signal(chip, price)
    assert sig["label"] == "觀望"
