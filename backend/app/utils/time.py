"""Time helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def hour_floor(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def hour_range(start: datetime, hours: int) -> List[datetime]:
    """Inclusive list of hour-aligned datetimes starting from `start`."""
    start = hour_floor(start)
    return [start + timedelta(hours=i) for i in range(hours)]
