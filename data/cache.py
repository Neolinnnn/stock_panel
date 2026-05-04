import time
from datetime import datetime
from pathlib import Path
import pandas as pd

CACHE_DIR = Path(".cache")
DEFAULT_TTL = 5 * 60


def _path(key: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR / f"{key}.parquet"


def get(key: str, ttl: int = DEFAULT_TTL) -> pd.DataFrame | None:
    p = _path(key)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > ttl:
        return None
    return pd.read_parquet(p)


def set(key: str, df: pd.DataFrame) -> None:
    df.to_parquet(_path(key))


def is_after_hours() -> bool:
    now = datetime.now()
    return now.hour >= 18 or now.weekday() >= 5
