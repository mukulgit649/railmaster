"""XGBoost-based maintenance priority scoring (DCI).

A regressor is trained once, at process start, on a synthetic dataset built
from a weighted formula + noise. Real job feature vectors are then scored by
calling model.predict() -- the DCI numbers are never hardcoded.
"""

from typing import Dict, List

import numpy as np
import xgboost as xgb

FEATURE_ORDER = [
    "severity",
    "days_overdue",
    "asset_health",
    "asset_age",
    "traffic_density",
    "historical_failures",
    "failure_consequence",
    "operational_criticality",
]

_WEIGHTS = {
    "severity": 20.0,           # 0-5 scale
    "days_overdue": 15.0,       # 0-10 scale
    "asset_health_inv": 15.0,   # (100 - health)/100
    "asset_age": 10.0,          # 0-30 scale
    "traffic_density": 15.0,    # 0-1 scale
    "historical_failures": 10.0,  # 0-10 scale
    "failure_consequence": 10.0,  # 0-1 scale
    "operational_criticality": 5.0,  # 0-1 scale
}

_model: xgb.XGBRegressor | None = None


def _synthetic_target(row: np.ndarray) -> float:
    severity, days_overdue, asset_health, asset_age, traffic_density, hist_failures, failure_consequence, op_crit = row
    score = (
        _WEIGHTS["severity"] * (severity / 5.0)
        + _WEIGHTS["days_overdue"] * min(days_overdue / 10.0, 1.0)
        + _WEIGHTS["asset_health_inv"] * (1.0 - asset_health / 100.0)
        + _WEIGHTS["asset_age"] * min(asset_age / 30.0, 1.0)
        + _WEIGHTS["traffic_density"] * traffic_density
        + _WEIGHTS["historical_failures"] * min(hist_failures / 10.0, 1.0)
        + _WEIGHTS["failure_consequence"] * failure_consequence
        + _WEIGHTS["operational_criticality"] * op_crit
    )
    return score


def _generate_training_set(n: int = 500, seed: int = 42):
    rng = np.random.default_rng(seed)
    severity = rng.integers(1, 6, n).astype(float)
    days_overdue = rng.integers(0, 11, n).astype(float)
    asset_health = rng.uniform(20, 100, n)
    asset_age = rng.uniform(0, 30, n)
    traffic_density = rng.uniform(0, 1, n)
    historical_failures = rng.integers(0, 11, n).astype(float)
    failure_consequence = rng.uniform(0, 1, n)
    operational_criticality = rng.uniform(0, 1, n)

    X = np.column_stack(
        [
            severity,
            days_overdue,
            asset_health,
            asset_age,
            traffic_density,
            historical_failures,
            failure_consequence,
            operational_criticality,
        ]
    )
    y = np.array([_synthetic_target(row) for row in X])
    noise = rng.normal(0, 4, n)
    y = np.clip(y + noise, 0, 100)
    return X, y


def _get_model() -> xgb.XGBRegressor:
    global _model
    if _model is None:
        X, y = _generate_training_set()
        model = xgb.XGBRegressor(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.15,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
        )
        model.fit(X, y)
        _model = model
    return _model


def predict_dci(jobs: List[dict]) -> Dict[str, int]:
    """Run the trained XGBoost model on each job's feature vector."""
    model = _get_model()
    X = np.array([[job["features"][f] for f in FEATURE_ORDER] for job in jobs])
    preds = model.predict(X)
    preds = np.clip(preds, 0, 100)
    return {job["id"]: int(round(float(p))) for job, p in zip(jobs, preds)}
