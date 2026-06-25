"""Stable, human-readable ID generation."""

from __future__ import annotations

import hashlib
import re
from typing import Optional


def slugify(value: str, fallback: str = "x") -> str:
    """Lowercase, dash-separated slug."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return s or fallback


def short_hash(*parts: Optional[str], length: int = 8) -> str:
    """Stable short hash of arbitrary parts."""
    joined = "|".join((p or "") for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:length]


def make_ward_id(city_code: str, ward_code: str) -> str:
    return f"{city_code.upper()}-{slugify(ward_code)}"
