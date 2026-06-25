"""Health and metadata endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.database import engine

router = APIRouter()
settings = get_settings()


@router.get("/health")
def health():
    """Liveness + DB connectivity check."""
    db_ok = True
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        db_error = str(exc)

    return {
        "data": {
            "status": "ok" if db_ok else "degraded",
            "service": settings.app_name,
            "version": __version__,
            "env": settings.app_env,
            "data_mode": settings.data_mode,
            "database_ok": db_ok,
            "database_error": db_error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "meta": {"generated_at": datetime.now(timezone.utc).isoformat()},
        "warnings": [],
        "error": None,
    }


@router.get("/version")
def version():
    return {
        "data": {"version": __version__, "service": settings.app_name},
        "meta": {},
        "warnings": [],
        "error": None,
    }
