import pickle
import numpy as np
import pytest
from pathlib import Path


def _make_mock_model(tmp_path):
    from sklearn.ensemble import RandomForestClassifier
    X = np.random.rand(100, 18)
    y = np.random.choice([-1, 0, 1], 100)
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X, y)
    path = tmp_path / "rf_model.pkl"
    with open(path, "wb") as f:
        pickle.dump({"model": clf, "accuracy": 0.55, "features": [f"f{i}" for i in range(18)]}, f)
    return path


def test_predict_returns_required_keys(tmp_path, monkeypatch):
    import model.predict as mp
    model_path = _make_mock_model(tmp_path)
    monkeypatch.setattr(mp, "_MODEL_PATH", model_path)
    mp._cache.clear()

    import pandas as pd
    row = {f"f{i}": [np.random.rand()] for i in range(18)}
    built_df = pd.DataFrame(row)

    result = mp._predict_from_row(built_df)
    assert set(["up", "down", "sideways", "accuracy"]).issubset(result.keys())
    assert abs(result["up"] + result["down"] + result["sideways"] - 1.0) < 0.01


def test_predict_row_df_uses_18_features(tmp_path, monkeypatch):
    import model.predict as mp
    model_path = _make_mock_model(tmp_path)
    monkeypatch.setattr(mp, "_MODEL_PATH", model_path)
    mp._cache.clear()

    import pandas as pd
    row = {f"f{i}": [0.5] for i in range(18)}
    result = mp._predict_from_row(pd.DataFrame(row))
    assert result["up"] + result["down"] + result["sideways"] > 0
