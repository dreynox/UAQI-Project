"""SQLAlchemy engine, session, and Base declarative class.

All model modules are eagerly imported so SQLAlchemy's metadata registry
sees every table class on first use.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# `check_same_thread` is required for SQLite + FastAPI's threadpool.
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Imports model modules so they register with Base."""
    # Import all model modules so SQLAlchemy sees them before create_all.
    from app.models import (  # noqa: F401
        advisory,
        aqi,
        attribution,
        city,
        construction_site,
        forecast,
        industrial_site,
        institutions,
        intervention,
        thermal_anomaly,
        traffic,
        vulnerable,
        ward,
        weather,
    )

    Base.metadata.create_all(bind=engine)