"""Dispersion-inspired feature engineering for AQI forecasting.

We don't run real Gaussian plume / CFD models in real-time, but we
*engineer features that mimic the structure of dispersion physics*:

- Diurnal cycle (sin/cos of hour)
- Wind direction (sin/cos so 359° and 1° are adjacent)
- Stability class proxy (Pasquill-Gifford-inspired)
- Downwind source exposure (Gaussian plume-inspired): how many thermal
  anomalies / industries are upwind of the ward, weighted by distance
- Lag features (last 1h, 3h, 6h, 24h AQI) for temporal continuity
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.engines.attribution.wind_modifier import (
    angular_diff,
    bearing_to,
    normalize_angle,
)
from app.models.aqi import AQITimeSeries
from app.models.industrial_site import IndustrialSite
from app.models.thermal_anomaly import ThermalAnomaly
from app.models.ward import Ward
from app.models.weather import WeatherForecast
from app.utils.geo import haversine_km


# Feature columns (stable order; MUST match train + predict).
FEATURE_NAMES: List[str] = [
    # Diurnal cycle (sin/cos of hour)
    "hour_sin",
    "hour_cos",
    # Day of week (sin/cos)
    "dow_sin",
    "dow_cos",
    # Wind features
    "wind_speed_kmh",
    "wind_dir_sin",
    "wind_dir_cos",
    # Atmospheric stability
    "stability_A",
    "stability_B",
    "stability_C",
    "stability_D",
    "stability_E",
    "stability_F",
    # Other weather
    "temperature_c",
    "humidity_pct",
    "pressure_hpa",
    "cloud_cover_pct",
    "precip_mm",
    # Source exposure (dispersion-inspired)
    "downwind_biomass_intensity",
    "downwind_industrial_intensity",
    "nearby_construction_intensity",
    "nearby_industrial_intensity",
    # Lag features
    "aqi_lag_1h",
    "aqi_lag_3h",
    "aqi_lag_6h",
    "aqi_lag_24h",
    "aqi_lag_48h",
    # Baseline + delta
    "current_aqi",
    "current_aqi_delta_24h",
]


def _stability_onehot(stability_class: str) -> List[float]:
    """One-hot encode Pasquill-Gifford stability class."""
    classes = ["A", "B", "C", "D", "E", "F"]
    return [1.0 if stability_class == c else 0.0 for c in classes]


def _downwind_intensity(
    points: List[Tuple[float, float, float]],  # (lat, lon, intensity)
    ward_lat: float,
    ward_lon: float,
    wind_from_deg: float,
    sigma_km: float,
    max_dist_km: float = 100.0,
) -> float:
    """Gaussian plume-inspired: sum intensity * exp(-d^2/sigma^2) * cos²(angle/2).

    Higher when sources are upwind (plume travels toward ward).
    """
    if not points:
        return 0.0
    wind_to_deg = normalize_angle(wind_from_deg + 180.0)
    out = 0.0
    for (lat, lon, intensity) in points:
        d = haversine_km(ward_lat, ward_lon, lat, lon)
        if d > max_dist_km:
            continue
        decay = math.exp(-(d ** 2) / (2.0 * sigma_km ** 2))
        b_src_to_ward = bearing_to(lat, lon, ward_lat, ward_lon)
        diff = angular_diff(wind_to_deg, b_src_to_ward)
        wind = 0.5 * (1.0 + math.cos(math.radians(diff)))
        out += intensity * decay * wind
    return out


def _nearby_intensity(
    points: List[Tuple[float, float, float]],
    ward_lat: float,
    ward_lon: float,
    sigma_km: float,
    max_dist_km: float = 10.0,
) -> float:
    """Distance-only intensity sum (no wind modifier)."""
    if not points:
        return 0.0
    out = 0.0
    for (lat, lon, intensity) in points:
        d = haversine_km(ward_lat, ward_lon, lat, lon)
        if d > max_dist_km:
            continue
        decay = math.exp(-(d ** 2) / (2.0 * sigma_km ** 2))
        out += intensity * decay
    return out


@dataclass
class FeatureContext:
    """All the inputs needed to build a feature row for a (ward, target_time)."""

    ward: Ward
    city_id: int
    target_time: datetime
    # Latest weather snapshot (will be looked up if None).
    wind_speed: float = 10.0
    wind_dir: float = 270.0
    stability_class: str = "D"
    temperature_c: float = 28.0
    humidity_pct: float = 60.0
    pressure_hpa: float = 1005.0
    cloud_cover_pct: float = 50.0
    precip_mm: float = 0.0
    # Past AQI readings (timestamp -> aqi).
    aqi_history: Dict[datetime, float] = None  # type: ignore[assignment]


def build_feature_row(
    session: Session,
    ctx: FeatureContext,
) -> Optional[np.ndarray]:
    """Build the feature vector for one (ward, target_time).

    Returns None if the ward has no AQI history (cannot forecast).
    """
    if ctx.aqi_history is None:
        ctx.aqi_history = _load_aqi_history(session, ctx.ward, ctx.target_time)

    if not ctx.aqi_history:
        return None

    # If a forecast weather row exists at target_time, use it;
    # otherwise use the latest available snapshot.
    # Initialize from context defaults so we always have a value.
    wind_speed = ctx.wind_speed
    wind_dir = ctx.wind_dir
    stability = ctx.stability_class
    temp = ctx.temperature_c
    humid = ctx.humidity_pct
    pressure = ctx.pressure_hpa
    cloud = ctx.cloud_cover_pct
    precip = ctx.precip_mm

    wf = (
        session.query(WeatherForecast)
        .filter(
            WeatherForecast.city_id == ctx.city_id,
            WeatherForecast.timestamp == ctx.target_time,
        )
        .first()
    )
    if wf:
        wind_speed = wf.wind_speed_kmh
        wind_dir = wf.wind_dir_deg
        stability = wf.stability_class
        temp = wf.temperature_c
        humid = wf.humidity_pct
        pressure = wf.pressure_hpa
        cloud = wf.cloud_cover_pct
        precip = wf.precip_mm
    else:
        wf_latest = (
            session.query(WeatherForecast)
            .filter(
                WeatherForecast.city_id == ctx.city_id,
                WeatherForecast.timestamp <= ctx.target_time,
            )
            .order_by(WeatherForecast.timestamp.desc())
            .first()
        )
        if wf_latest:
            wind_speed = wf_latest.wind_speed_kmh
            wind_dir = wf_latest.wind_dir_deg
            stability = wf_latest.stability_class
            temp = wf_latest.temperature_c
            humid = wf_latest.humidity_pct
            pressure = wf_latest.pressure_hpa
            cloud = wf_latest.cloud_cover_pct
            precip = wf_latest.precip_mm

    # Hour + day-of-week cyclical encoding.
    hour = ctx.target_time.hour
    dow = ctx.target_time.weekday()
    hour_sin = math.sin(2 * math.pi * hour / 24.0)
    hour_cos = math.cos(2 * math.pi * hour / 24.0)
    dow_sin = math.sin(2 * math.pi * dow / 7.0)
    dow_cos = math.cos(2 * math.pi * dow / 7.0)

    # Wind direction cyclical.
    wind_dir_rad = math.radians(wind_dir)
    wind_sin = math.sin(wind_dir_rad)
    wind_cos = math.cos(wind_dir_rad)

    # Stability one-hot.
    stability_vec = _stability_onehot(stability)

    # Downwind source exposure.
    # Biomass thermals — look at last 24h up to target_time.
    as_of = ctx.target_time
    biomass_points = (
        session.query(ThermalAnomaly)
        .filter(
            and_(
                ThermalAnomaly.city_id == ctx.city_id,
                ThermalAnomaly.timestamp >= as_of - timedelta(hours=24),
                ThermalAnomaly.timestamp <= as_of,
                ThermalAnomaly.source_type.in_(["biomass", "wildfire"]),
            )
        )
        .all()
    )
    biomass_triples = [
        (t.lat, t.lon, (t.intensity_kelvin - 300.0) / 60.0 * t.confidence)
        for t in biomass_points
    ]
    downwind_biomass = _downwind_intensity(
        biomass_triples, ctx.ward.centroid_lat, ctx.ward.centroid_lon, wind_dir,
        sigma_km=50.0, max_dist_km=120.0,
    )

    # Industrial thermals — short window.
    industrial_ta_points = (
        session.query(ThermalAnomaly)
        .filter(
            and_(
                ThermalAnomaly.city_id == ctx.city_id,
                ThermalAnomaly.timestamp >= as_of - timedelta(hours=12),
                ThermalAnomaly.timestamp <= as_of,
                ThermalAnomaly.source_type == "industrial",
            )
        )
        .all()
    )
    industrial_ta_triples = [
        (t.lat, t.lon, (t.intensity_kelvin - 300.0) / 60.0 * t.confidence)
        for t in industrial_ta_points
    ]
    downwind_industrial = _downwind_intensity(
        industrial_ta_triples, ctx.ward.centroid_lat, ctx.ward.centroid_lon,
        wind_dir, sigma_km=20.0, max_dist_km=60.0,
    )

    # Nearby industries (no wind — just distance).
    industries = (
        session.query(IndustrialSite)
        .filter(IndustrialSite.city_id == ctx.city_id)
        .all()
    )
    nearby_industrial_intensity = _nearby_intensity(
        [(i.lat, i.lon, i.intensity / 100.0) for i in industries],
        ctx.ward.centroid_lat, ctx.ward.centroid_lon,
        sigma_km=8.0, max_dist_km=15.0,
    )

    # Construction intensity (no separate table query — use bbox for the demo).
    # Approximate via static count scaled.
    from app.models.construction_site import ConstructionSite
    constructions = (
        session.query(ConstructionSite)
        .filter(ConstructionSite.city_id == ctx.city_id)
        .all()
    )
    nearby_construction_intensity = _nearby_intensity(
        [(c.lat, c.lon, c.intensity / 100.0) for c in constructions],
        ctx.ward.centroid_lat, ctx.ward.centroid_lon,
        sigma_km=6.0, max_dist_km=12.0,
    )

    # Lag features.
    aqi_lag_1h = _lookup_lag(ctx.aqi_history, ctx.target_time - timedelta(hours=1))
    aqi_lag_3h = _lookup_lag(ctx.aqi_history, ctx.target_time - timedelta(hours=3))
    aqi_lag_6h = _lookup_lag(ctx.aqi_history, ctx.target_time - timedelta(hours=6))
    aqi_lag_24h = _lookup_lag(ctx.aqi_history, ctx.target_time - timedelta(hours=24))
    aqi_lag_48h = _lookup_lag(ctx.aqi_history, ctx.target_time - timedelta(hours=48))

    current_aqi = aqi_lag_1h if aqi_lag_1h is not None else ctx.ward.current_aqi
    current_aqi_delta_24h = (
        (current_aqi - aqi_lag_24h) if (aqi_lag_24h is not None and current_aqi is not None)
        else 0.0
    )

    row = np.array([
        hour_sin,
        hour_cos,
        dow_sin,
        dow_cos,
        wind_speed,
        wind_sin,
        wind_cos,
        *stability_vec,
        temp,
        humid,
        pressure,
        cloud,
        precip,
        downwind_biomass,
        downwind_industrial,
        nearby_construction_intensity,
        nearby_industrial_intensity,
        aqi_lag_1h if aqi_lag_1h is not None else current_aqi,
        aqi_lag_3h if aqi_lag_3h is not None else current_aqi,
        aqi_lag_6h if aqi_lag_6h is not None else current_aqi,
        aqi_lag_24h if aqi_lag_24h is not None else current_aqi,
        aqi_lag_48h if aqi_lag_48h is not None else current_aqi,
        current_aqi if current_aqi is not None else 0.0,
        current_aqi_delta_24h if current_aqi_delta_24h is not None else 0.0,
    ], dtype=float)

    return row


def _load_aqi_history(
    session: Session, ward: Ward, target_time: datetime
) -> Dict[datetime, float]:
    """Load all AQI history up to target_time for the ward (or its station)."""
    rows = (
        session.query(AQITimeSeries)
        .filter(
            AQITimeSeries.ward_id == ward.id,
            AQITimeSeries.timestamp <= target_time,
        )
        .order_by(AQITimeSeries.timestamp)
        .all()
    )
    return {r.timestamp: r.aqi for r in rows}


def _lookup_lag(history: Dict[datetime, float], target: datetime) -> Optional[float]:
    """Find AQI nearest to target within +/- 30 minutes."""
    if not history:
        return None
    # Search for nearest timestamp within 30 minutes.
    best = None
    best_diff = None
    for ts, aqi in history.items():
        diff = abs((ts - target).total_seconds())
        if best_diff is None or diff < best_diff:
            best = aqi
            best_diff = diff
    if best_diff is not None and best_diff <= 1800:  # 30 min tolerance
        return best
    return None
