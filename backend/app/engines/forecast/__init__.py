"""Hyperlocal AQI forecast engine.

Per-city GradientBoostingRegressor trained on the seeded time-series,
fed dispersion-inspired features (diurnal cycle, wind direction relative
to thermal-anomaly sources, stability class, etc.).
"""

from app.engines.forecast.model import (
    ensure_model_for_city,
    forecast_ward,
    train_all_city_models,
)

__all__ = ["forecast_ward", "train_all_city_models", "ensure_model_for_city"]
