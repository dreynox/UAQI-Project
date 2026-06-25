"""Geospatial helpers (haversine, simple polygon ops)."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

# Earth radius in km.
EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def point_in_bbox(lat: float, lon: float, bbox: Sequence[float]) -> bool:
    """True if point lies within bbox = [min_lat, min_lon, max_lat, max_lon]."""
    return bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]


def centroid(coords: Iterable[Tuple[float, float]]) -> Tuple[float, float]:
    """Average lat/lon of a coordinate list."""
    pts = list(coords)
    if not pts:
        return (0.0, 0.0)
    lat = sum(p[0] for p in pts) / len(pts)
    lon = sum(p[1] for p in pts) / len(pts)
    return (lat, lon)


def bbox_of(coords: Iterable[Tuple[float, float]]) -> List[float]:
    """Bounding box [min_lat, min_lon, max_lat, max_lon] for coordinate list."""
    pts = list(coords)
    if not pts:
        return [0.0, 0.0, 0.0, 0.0]
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    return [min(lats), min(lons), max(lats), max(lons)]
