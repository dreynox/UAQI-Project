"""Consistent API response envelope helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def envelope(
    data: Any,
    *,
    meta: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    error: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wrap a payload in the standard response envelope."""
    base_meta: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if meta:
        base_meta.update(meta)
    return {
        "data": data,
        "meta": base_meta,
        "warnings": warnings or [],
        "error": error,
    }


def ok(data: Any, **meta: Any) -> Dict[str, Any]:
    return envelope(data, meta=meta)


def warn(data: Any, warnings: List[str], **meta: Any) -> Dict[str, Any]:
    return envelope(data, meta=meta, warnings=warnings)


def err(code: str, message: str, *, status: int = 400) -> Dict[str, Any]:
    return envelope(None, error={"code": code, "message": message})
