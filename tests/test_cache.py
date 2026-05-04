import time
from pathlib import Path
import pandas as pd
import pytest

@pytest.fixture(autouse=True)
def clean_cache(tmp_path, monkeypatch):
    import data.cache as c
    monkeypatch.setattr(c, "CACHE_DIR", tmp_path)

def test_get_returns_none_when_missing():
    from data.cache import get
    assert get("missing_key") is None

def test_set_then_get_returns_dataframe():
    from data.cache import get, set as cache_set
    df = pd.DataFrame({"a": [1, 2, 3]})
    cache_set("test_key", df)
    result = get("test_key")
    assert result is not None
    assert list(result["a"]) == [1, 2, 3]

def test_get_returns_none_when_expired(monkeypatch):
    from data.cache import get, set as cache_set
    df = pd.DataFrame({"a": [1]})
    cache_set("expired_key", df)
    import data.cache as c
    _orig = time.time
    monkeypatch.setattr(c.time, "time", lambda: _orig() + 400)
    assert get("expired_key", ttl=300) is None

def test_is_after_hours_weekday_morning(monkeypatch):
    from datetime import datetime
    import data.cache as c
    monkeypatch.setattr(c, "datetime", type("dt", (), {"now": staticmethod(lambda: datetime(2026, 5, 4, 10, 0))})())
    assert c.is_after_hours() is False

def test_is_after_hours_evening(monkeypatch):
    from datetime import datetime
    import data.cache as c
    monkeypatch.setattr(c, "datetime", type("dt", (), {"now": staticmethod(lambda: datetime(2026, 5, 4, 19, 0))})())
    assert c.is_after_hours() is True
