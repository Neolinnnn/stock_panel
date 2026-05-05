import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from data.cache import get as _cget, set as _cset, is_after_hours

_loader = None
_loader_token: str = ""


def _dl():
    """回傳已登入的 DataLoader。若 .env token 有變化則重新建立 loader。"""
    global _loader, _loader_token
    load_dotenv(override=True)  # 每次重新讀取 .env，允許不重啟 app 更新 token
    token = os.environ.get("FINMIND_TOKEN", "")
    if _loader is None or token != _loader_token:
        from FinMind.data import DataLoader
        _loader = DataLoader()
        if token:
            _loader.login_by_token(api_token=token)
        _loader_token = token
    return _loader


def _ttl() -> int:
    return 60 * 60 if is_after_hours() else 5 * 60


def daily_ohlcv(stock_id: str, days: int = 120) -> pd.DataFrame:
    """回傳日線 OHLCV。若股票不存在回傳空 DataFrame；API 失敗則拋例外。"""
    key = f"daily_{stock_id}_{days}"
    cached = _cget(key, _ttl())
    if cached is not None:
        return cached

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
    # 讓 KeyError / 網路錯誤直接往上拋，由 app.py 顯示有意義的訊息
    df = _dl().taiwan_stock_daily(stock_id=stock_id, start_date=start, end_date=end)
    if df.empty:
        return df  # 股票代碼不存在，真正空資料

    df = df.sort_values("date").rename(columns={"max": "high", "min": "low", "Trading_Volume": "volume"})
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.tail(days).reset_index(drop=True)
    _cset(key, df)
    return df


def minute_ohlcv(stock_id: str) -> pd.DataFrame:
    key = f"minute_{stock_id}"
    cached = _cget(key, _ttl())
    if cached is not None:
        return cached

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        df = _dl().taiwan_stock_minute_data(stock_id=stock_id, start_date=start, end_date=end)
        if not df.empty:
            df = df.sort_values("date")
            _cset(key, df)
        return df
    except Exception:
        return pd.DataFrame()


def institutional_investors(stock_id: str, days: int = 30) -> pd.DataFrame:
    key = f"chip_{stock_id}_{days}"
    cached = _cget(key, _ttl())
    if cached is not None:
        return cached

    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
        df = _dl().taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start, end_date=end)
        if not df.empty:
            df = df.tail(days).reset_index(drop=True)
            _cset(key, df)
        return df
    except Exception:
        return pd.DataFrame()


def margin_purchase(stock_id: str, days: int = 30) -> pd.DataFrame:
    key = f"margin_{stock_id}_{days}"
    cached = _cget(key, _ttl())
    if cached is not None:
        return cached

    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
        df = _dl().taiwan_stock_margin_purchase_short_sale(stock_id=stock_id, start_date=start, end_date=end)
        if not df.empty:
            df = df.tail(days).reset_index(drop=True)
            _cset(key, df)
        return df
    except Exception:
        return pd.DataFrame()


def realtime_quote(stock_id: str) -> dict:
    try:
        import twstock
        data = twstock.realtime.get(stock_id)
        if data and data.get("success"):
            rt = data["realtime"]
            return {
                "bid":    rt.get("best_bid_price",  [None])[0],
                "ask":    rt.get("best_ask_price",  [None])[0],
                "price":  rt.get("latest_trade_price"),
                "volume": rt.get("accumulated_trade_volume"),
            }
    except Exception:
        pass
    return {"bid": None, "ask": None, "price": None, "volume": None}


def stock_info(stock_id: str) -> dict:
    key = f"info_{stock_id}"
    cached = _cget(key, ttl=24 * 3600)
    if cached is not None and not cached.empty:
        row = cached.iloc[0]
        return {
            "name":     str(row.get("stock_name",       stock_id)),
            "industry": str(row.get("industry_category", "—")),
        }

    try:
        info = _dl().taiwan_stock_info()
        row  = info[info["stock_id"] == stock_id]
        if not row.empty:
            df = row[["stock_name", "industry_category"]].head(1)
            _cset(key, df)
            return {
                "name":     df["stock_name"].values[0],
                "industry": df["industry_category"].values[0],
            }
    except Exception:
        pass
    return {"name": stock_id, "industry": "—"}
