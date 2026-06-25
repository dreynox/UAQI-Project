"""Per-city GradientBoosting forecast model.

For each city we train one GradientBoostingRegressor on its 30-day
historical AQI series, with dispersion-inspired features.

The model is loaded lazily on first use. If a model file doesn't exist,
`forecast_ward` falls back to the persistence baseline.
"""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.engines.forecast.features import (
    FeatureContext,
    build_feature_row,
    _load_aqi_history,
)
from app.models.city import City
from app.models.forecast import Forecast
from app.models.ward import Ward

log = logging.getLogger("uaqi.forecast")

# Per-city model version label.
MODEL_VERSION = "gbr-v1"

# Train set: use historical rows from each city's AQITimeSeries.
# Predict horizon: 1, 3, 6, 12, 24, 48, 72 hours ahead.

PREDICTION_HORIZONS = (24, 48, 72)


@dataclass
class ForecastRow:
    """One forecast point at a horizon."""

    ward_id: int
    horizon_hours: int
    generated_at: datetime
    target_time: datetime
    predicted_aqi: float
    baseline_aqi: float
    confidence_low: float
    confidence_high: float
    model_version: str


# In-memory cache of loaded models: city_id -> dict[horizon -> model]
_MODEL_CACHE: Dict[int, Dict[int, GradientBoostingRegressor]] = {}
# Train metadata cache.
_TRAIN_META: Dict[int, dict] = {}


def _model_dir() -> Path:
    settings = get_settings()
    p = Path(settings.forecast_model_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _model_path(city_id: int) -> Path:
    return _model_dir() / f"city_{city_id}_{MODEL_VERSION}.joblib"


def _load_model_from_disk(city_id: int) -> Optional[Dict[int, GradientBoostingRegressor]]:
    path = _model_path(city_id)
    if not path.exists():
        return None
    try:
        bundle = joblib.load(path)
        _MODEL_CACHE[city_id] = bundle["models"]
        _TRAIN_META[city_id] = bundle.get("meta", {})
        log.info("Loaded forecast model for city_id=%s from %s", city_id, path)
        return bundle["models"]
    except Exception as e:
        log.warning("Failed to load model for city_id=%s: %s", city_id, e)
        return None


def _ensure_model_for_city(session: Session, city_id: int) -> Dict[int, GradientBoostingRegressor]:
    """Return cached per-city models, training if missing."""
    if city_id in _MODEL_CACHE:
        return _MODEL_CACHE[city_id]
    loaded = _load_model_from_disk(city_id)
    if loaded:
        return loaded
    log.info("No model for city_id=%s on disk; training now...", city_id)
    train_city_model(session, city_id)
    return _MODEL_CACHE.get(city_id, {})


def ensure_model_for_city(session: Session, city_id: int) -> Dict[int, GradientBoostingRegressor]:
    """Public alias for model loading/training."""
    return _ensure_model_for_city(session, city_id)


# --- Training ----------------------------------------------------------

def _build_training_set(
    session: Session, city_id: int, horizon: int
) -> Tuple[np.ndarray, np.ndarray, List[datetime], List[int]]:
    """For each (ward, training_timestamp), build features at target_time and label = actual_aqi.

    Target_time = training_timestamp + horizon hours.
    """
    wards = session.query(Ward).filter(Ward.city_id == city_id).all()
    if not wards:
        return np.empty((0, 0)), np.empty((0,)), [], []

    # Pick a sampling stride: every 6 hours across history.
    from app.engines.forecast.features import FEATURE_NAMES

    X_rows: List[np.ndarray] = []
    y: List[float] = []
    sample_times: List[datetime] = []
    sample_wards: List[int] = []

    for ward in wards:
        # Pre-load AQI history for this ward.
        history_rows = (
            session.query(Forecast)
            .filter(Forecast.ward_id == ward.id)
            .all()
        )
        # We'll fill history per timestamp as we go.
        for h in (24, 48):  # we use 24h history; predictions land on future hours
            pass  # placeholder

        # For each historical hour we have, try to predict the value at +horizon.
        from app.models.aqi import AQITimeSeries
        all_readings = (
            session.query(AQITimeSeries)
            .filter(
                AQITimeSeries.ward_id == ward.id,
                AQITimeSeries.timestamp <= datetime(2026, 6, 25, 23, 0, 0),
            )
            .order_by(AQITimeSeries.timestamp)
            .all()
        )
        if len(all_readings) < 50:
            continue

        readings_by_ts = {r.timestamp: r for r in all_readings}

        # Sample every 6 hours (skip first 48h to give us lag features).
        for i in range(48, len(all_readings) - horizon, 6):
            train_ts = all_readings[i].timestamp
            target_ts = train_ts + timedelta(hours=horizon)
            # Skip if no future reading to label against.
            if target_ts not in readings_by_ts:
                continue

            ctx = FeatureContext(
                ward=ward,
                city_id=city_id,
                target_time=train_ts,  # features built "as of" train_ts
            )
            row = build_feature_row(session, ctx)
            if row is None:
                continue

            X_rows.append(row)
            y.append(float(readings_by_ts[target_ts].aqi))
            sample_times.append(train_ts)
            sample_wards.append(ward.id)

    if not X_rows:
        return np.empty((0, len(FEATURE_NAMES))), np.empty((0,)), [], []
    return np.vstack(X_rows), np.array(y), sample_times, sample_wards


def train_city_model(session: Session, city_id: int) -> Dict[str, dict]:
    """Train GradientBoosting per horizon for a city. Save to disk."""
    from app.engines.forecast.features import FEATURE_NAMES

    log.info("Training forecast model for city_id=%s ...", city_id)
    models: Dict[int, GradientBoostingRegressor] = {}
    meta: Dict[str, dict] = {
        "city_id": city_id,
        "feature_names": FEATURE_NAMES,
        "horizons": {},
    }

    for horizon in PREDICTION_HORIZONS:
        X, y, sample_times, sample_wards = _build_training_set(session, city_id, horizon)
        if len(X) == 0:
            log.warning("No training samples for city_id=%s horizon=%sh", city_id, horizon)
            continue

        # Train/test split: last 20% as test.
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        model = GradientBoostingRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            random_state=42,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        rmse = float(math.sqrt(mean_squared_error(y_test, y_pred))) if len(y_test) > 0 else None

        # Compare against persistence baseline.
        if len(y_test) > 0:
            # Persistence baseline = current AQI at train_ts (the first feature).
            # X_test[:, FEATURE_NAMES.index('current_aqi')] holds current_aqi.
            current_aqi_idx = FEATURE_NAMES.index("current_aqi")
            baseline_pred = X_test[:, current_aqi_idx]
            baseline_rmse = float(math.sqrt(mean_squared_error(y_test, baseline_pred)))
        else:
            baseline_rmse = None

        models[horizon] = model
        meta["horizons"][str(horizon)] = {
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "rmse_model": round(rmse, 2) if rmse is not None else None,
            "rmse_persistence": round(baseline_rmse, 2) if baseline_rmse is not None else None,
            "model_advantage": (
                round(baseline_rmse - rmse, 2)
                if (rmse is not None and baseline_rmse is not None)
                else None
            ),
        }
        log.info(
            "  city=%s horizon=%sh model_rmse=%.2f baseline_rmse=%.2f advantage=%.2f",
            city_id, horizon,
            rmse if rmse else 0,
            baseline_rmse if baseline_rmse else 0,
            (baseline_rmse - rmse) if (rmse and baseline_rmse) else 0,
        )

    _MODEL_CACHE[city_id] = models
    _TRAIN_META[city_id] = meta

    # Persist to disk.
    path = _model_path(city_id)
    joblib.dump({"models": models, "meta": meta}, path)
    log.info("Saved model to %s", path)
    return {"models": models, "meta": meta}


def train_all_city_models(session: Session) -> Dict[int, dict]:
    """Train all cities in the DB."""
    cities = session.query(City).all()
    out = {}
    for c in cities:
        out[c.id] = train_city_model(session, c.id)
    return out


# --- Inference ---------------------------------------------------------

def _persistence_baseline(ward: Ward, horizon_hours: int) -> float:
    """Tomorrow = today's AQI."""
    return ward.current_aqi


def _confidence_band(
    predicted: float, horizon_hours: int, n_train: int
) -> Tuple[float, float]:
    """Heuristic confidence band: wider for longer horizons."""
    base_sigma = 8.0 + (horizon_hours / 24.0) * 6.0
    # If we have less training data, widen the band.
    widen = max(0.0, (200.0 - n_train) / 200.0) * 6.0
    sigma = base_sigma + widen
    return (predicted - 1.96 * sigma, predicted + 1.96 * sigma)


def forecast_ward(
    session: Session,
    ward: Ward,
    horizons: Optional[List[int]] = None,
    as_of: Optional[datetime] = None,
) -> List[ForecastRow]:
    """Generate forecast rows for one ward at the requested horizons."""
    horizons = horizons or list(PREDICTION_HORIZONS)
    as_of = as_of or datetime(2026, 6, 25, 23, 0, 0)

    models = _ensure_model_for_city(session, ward.city_id)
    out: List[ForecastRow] = []

    for horizon in horizons:
        target_time = as_of + timedelta(hours=horizon)
        baseline = _persistence_baseline(ward, horizon)

        ctx = FeatureContext(
            ward=ward,
            city_id=ward.city_id,
            target_time=as_of,  # features built "as of" current time
        )
        # Inject history directly so we don't re-query.
        ctx.aqi_history = _load_aqi_history(session, ward, as_of)
        # The build_feature_row function looks up weather at target_time;
        # but our training used "as_of" train_ts for the wind/stability.
        # For inference, we approximate by using as_of as the feature time.
        # (Predictions degrade gracefully — wind will be the same throughout.)

        row = build_feature_row(session, ctx)
        if row is None or horizon not in models:
            # Fallback: persistence baseline only.
            predicted = baseline
        else:
            X = row.reshape(1, -1)
            try:
                predicted = float(models[horizon].predict(X)[0])
                predicted = max(0.0, predicted)
            except Exception as e:
                log.warning("Predict failed for ward=%s horizon=%s: %s", ward.id, horizon, e)
                predicted = baseline

        meta = _TRAIN_META.get(ward.city_id, {})
        n_train = sum(
            h.get("n_train", 0) for h in meta.get("horizons", {}).values()
        )
        low, high = _confidence_band(predicted, horizon, n_train)

        out.append(ForecastRow(
            ward_id=ward.id,
            horizon_hours=horizon,
            generated_at=datetime.utcnow(),
            target_time=target_time,
            predicted_aqi=round(predicted, 1),
            baseline_aqi=round(baseline, 1),
            confidence_low=round(max(0.0, low), 1),
            confidence_high=round(high, 1),
            model_version=MODEL_VERSION,
        ))

    return out


def persist_forecast_rows(session: Session, rows: List[ForecastRow]) -> int:
    """Write Forecast rows to DB."""
    for r in rows:
        session.add(Forecast(
            ward_id=r.ward_id,
            horizon_hours=r.horizon_hours,
            generated_at=r.generated_at,
            target_time=r.target_time,
            predicted_aqi=r.predicted_aqi,
            baseline_aqi=r.baseline_aqi,
            confidence_low=r.confidence_low,
            confidence_high=r.confidence_high,
            model_version=r.model_version,
        ))
    session.flush()
    return len(rows)


def get_train_meta() -> Dict[int, dict]:
    return dict(_TRAIN_META)
