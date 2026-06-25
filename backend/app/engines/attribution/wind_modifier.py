"""Wind-direction modifier used by the attribution agents.

Pollution from upwind sources contributes more to a ward's concentration
than downwind sources. This module provides the Gaussian-plume-inspired
wind-weighting function used by all four agents.

Convention:
- wind_from_deg: direction the wind is COMING FROM (meteorological),
  0=N, 90=E, 180=S, 270=W.
- source_to_ward_bearing: bearing from source TO ward (0=N).
- We want: how much does the source contaminate the ward given the wind?
  If the wind blows FROM source TO ward, the source is upwind and the
  contribution is high. If wind blows FROM ward TO source, contribution
  is low.
"""

from __future__ import annotations

import math


def normalize_angle(deg: float) -> float:
    """Normalize angle to [0, 360)."""
    return deg % 360.0


def angular_diff(a: float, b: float) -> float:
    """Smallest absolute angular difference between two bearings in degrees."""
    d = (a - b + 180.0) % 360.0 - 180.0
    return abs(d)


def bearing_to(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> float:
    """Initial bearing FROM (from_lat, from_lon) TO (to_lat, to_lon) in degrees [0, 360)."""
    lat1 = math.radians(from_lat)
    lat2 = math.radians(to_lat)
    dlon = math.radians(to_lon - from_lon)
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return normalize_angle(bearing)


def downwind_factor(
    source_lat: float,
    source_lon: float,
    ward_lat: float,
    ward_lon: float,
    wind_from_deg: float,
) -> float:
    """Return a multiplier in [0, 1] for how downwind the source is from the ward.

    Logic:
    - Compute the bearing from the source TO the ward (where the plume travels).
    - The plume travels in the direction the wind BLOWS TOWARDS, which is
      wind_from_deg + 180.
    - If the bearing from source→ward matches wind_towards, the source is
      upwind of the ward and contributes strongly.
    - The factor decays with angular mismatch using a half-Gaussian.

    Returns:
        1.0 when perfectly upwind (plume aimed directly at ward),
        ~0.5 when 90° off-axis,
        ~0.0 when 180° off (downwind of the ward — the ward's own pollution
            travels away from the source).
    """
    wind_to_deg = normalize_angle(wind_from_deg + 180.0)
    b_src_to_ward = bearing_to(source_lat, source_lon, ward_lat, ward_lon)
    diff = angular_diff(wind_to_deg, b_src_to_ward)  # 0..180
    # half-Gaussian falloff: cos^2 of half the angle scaled.
    # diff=0 -> 1.0, diff=90 -> 0.5, diff=180 -> 0.0
    factor = 0.5 * (1.0 + math.cos(math.radians(diff)))
    return max(0.0, min(1.0, factor))
