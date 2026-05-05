"""
靜態頁面資料產生器。
由 GitHub Actions 每日收盤後執行，輸出 JSON 到 docs/stocks/。

用法：
    python scripts/generate_static.py
    python scripts/generate_static.py 2330 3661 2454  # 指定股票
"""
import sys
import json
import math
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from data.fetcher import daily_ohlcv, institutional_investors, margin_purchase, stock_info
from indicators.technical import compute_indicators, technical_summary, key_levels, detect_patterns
from indicators.chip import aggregate_chip, main_force_signal
from model.predict import predict as ml_predict

DOCS = ROOT / "docs" / "stocks"
DOCS.mkdir(parents=True, exist_ok=True)

DEFAULT_WATCHLIST = [
    "2330", "2317", "2454", "2382", "3711",
    "3661", "2308", "2303", "6505", "2412",
    "0050", "2603", "2609", "2615", "2迷",
]
# 剔除非法代碼
DEFAULT_WATCHLIST = [s for s in DEFAULT_WATCHLIST if s.isdigit() or s.isalnum()]


def _safe(v):
    """把 NaN / Inf 轉成 None，讓 JSON 可以序列化。"""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if (math.isnan(float(v)) or math.isinf(float(v))) else float(v)
    return v


def _series(s: pd.Series) -> list:
    return [_safe(v) for v in s.tolist()]


def generate_stock(stock_id: str) -> bool:
    print(f"[{stock_id}] 開始...")
    try:
        df_day   = daily_ohlcv(stock_id, days=120)
        chip_raw = institutional_investors(stock_id, days=30)
        margin_raw = margin_purchase(stock_id, days=30)
        info     = stock_info(stock_id)

        if df_day.empty:
            print(f"[{stock_id}] 無資料，跳過")
            return False

        df      = compute_indicators(df_day).dropna().reset_index(drop=True)
        chip_df = aggregate_chip(chip_raw)
        summary = technical_summary(df)
        levels  = key_levels(df)
        patterns = detect_patterns(df)
        signal  = main_force_signal(chip_df, df)
        pred    = ml_predict(df_day, chip_raw, margin_raw)

        # ── OHLCV ──────────────────────────────────────────────────────
        dates  = df["date"].astype(str).tolist()
        ohlcv  = {
            "date":   dates,
            "open":   _series(df["open"]),
            "high":   _series(df["high"]),
            "low":    _series(df["low"]),
            "close":  _series(df["close"]),
            "volume": _series(df["volume"]),
        }

        # ── Indicators ────────────────────────────────────────────────
        indicators = {
            "ma5":         _series(df["ma5"]),
            "ma20":        _series(df["ma20"]),
            "ma60":        _series(df["ma60"]),
            "bb_upper":    _series(df["bb_upper"]),
            "bb_lower":    _series(df["bb_lower"]),
            "bb_mid":      _series(df["bb_mid"]),
            "kd_k":        _series(df["kd_k"]),
            "kd_d":        _series(df["kd_d"]),
            "macd":        _series(df["macd_dif"]),    # DIF 線
            "macd_signal": _series(df["macd_signal"]), # DEA 線
            "macd_hist":   _series(df["macd_osc"]),    # 柱狀
            "rsi14":       _series(df["rsi14"]),
        }

        # ── Chip ──────────────────────────────────────────────────────
        chip = {}
        if not chip_df.empty:
            chip = {
                "dates":   chip_df["日期"].astype(str).tolist(),
                "foreign": _series(chip_df["外資"]),
                "trust":   _series(chip_df["投信"]),
                "dealer":  _series(chip_df["自營"]),
                "total":   _series(chip_df["合計"]),
            }

        # ── Patterns ─────────────────────────────────────────────────
        # detect_patterns 回傳 dict，例如 {"w_bottom": {"formed": True, ...}, ...}
        PATTERN_NAMES = {"w_bottom": "W底", "m_top": "M頭"}
        pattern_list = []
        for key, info in (patterns or {}).items():
            if isinstance(info, dict) and info.get("formed"):
                pattern_list.append({
                    "label":  PATTERN_NAMES.get(key, key),
                    "desc":   info.get("reason", ""),
                    "date":   "",
                })
            elif isinstance(info, dict) and not info.get("formed"):
                pattern_list.append({
                    "label":  PATTERN_NAMES.get(key, key) + "（未完成）",
                    "desc":   info.get("reason", ""),
                    "date":   "",
                })

        # ── Levels ───────────────────────────────────────────────────
        # key_levels 回傳混合型：有些值是字串範圍，有些是數值
        levels_out = {}
        for k, v in (levels or {}).items():
            if isinstance(v, str):
                levels_out[k] = v          # 直接保留字串（如 "4660 ～ 4710"）
            else:
                levels_out[k] = _safe(v)   # 數值走 safe 轉換

        # ── Prediction ───────────────────────────────────────────────
        pred_out = {
            "up":       _safe(pred.get("up", 0.33)),
            "sideways": _safe(pred.get("sideways", 0.34)),
            "down":     _safe(pred.get("down", 0.33)),
            "accuracy": _safe(pred.get("accuracy", 0)),
            "error":    pred.get("error"),
        }

        close_last = float(df["close"].iloc[-1]) if not df.empty else None
        close_prev = float(df["close"].iloc[-2]) if len(df) >= 2 else None
        change     = round(close_last - close_prev, 2) if (close_last and close_prev) else None
        change_pct = round(change / close_prev * 100, 2) if (change is not None and close_prev) else None

        payload = {
            "stock_id":     stock_id,
            "name":         info.get("name", stock_id),
            "industry":     info.get("industry", "—"),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "quote": {
                "close":      close_last,
                "prev":       close_prev,
                "change":     change,
                "change_pct": change_pct,
                "volume":     _safe(df["volume"].iloc[-1]) if not df.empty else None,
            },
            "ohlcv":      ohlcv,
            "indicators": indicators,
            "chip":       chip,
            "signal":     signal,
            "summary":    summary,
            "levels":     levels_out,
            "patterns":   pattern_list,
            "prediction": pred_out,
        }

        out = DOCS / f"{stock_id}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{stock_id}] ✓ 已寫入 {out}")
        return True

    except Exception as e:
        print(f"[{stock_id}] 錯誤：{e}")
        import traceback; traceback.print_exc()
        return False


def update_manifest(success_ids: list[str]):
    manifest = []
    for sid in success_ids:
        f = DOCS / f"{sid}.json"
        if not f.exists():
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            manifest.append({
                "stock_id":     d["stock_id"],
                "name":         d["name"],
                "industry":     d["industry"],
                "generated_at": d["generated_at"],
                "close":        d["quote"]["close"],
                "change_pct":   d["quote"]["change_pct"],
                "signal_label": d["signal"]["label"],
                "signal_color": d["signal"]["color"],
            })
        except Exception:
            pass

    manifest.sort(key=lambda x: x["stock_id"])
    (DOCS / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"manifest.json 更新完成，共 {len(manifest)} 檔")


if __name__ == "__main__":
    watchlist = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_WATCHLIST
    watchlist = [s.strip() for s in watchlist if s.strip()]

    print(f"=== 開始產生靜態資料 ({len(watchlist)} 檔) ===")
    ok = []
    for sid in watchlist:
        if generate_stock(sid):
            ok.append(sid)

    update_manifest(ok)
    print(f"=== 完成：{len(ok)}/{len(watchlist)} ===")
