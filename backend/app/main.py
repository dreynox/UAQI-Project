"""FastAPI application entry point.

Wires routers, CORS, logging, lifecycle hooks (DB init + seed + model train).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import __version__
from app.core.config import get_settings
from app.core.cors import install_cors
from app.core.database import init_db
from app.core.logging import configure_logging
from app.routers import (
    advisory,
    attribution,
    cities,
    compare,
    demo,
    enforcement,
    forecast,
    geo,
    health,
    health_risk,
    wards,
)

settings = get_settings()
configure_logging()
log = logging.getLogger("uaqi.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown hooks."""
    log.info("Starting %s (env=%s, data_mode=%s)", settings.app_name, settings.app_env, settings.data_mode)
    init_db()

    if settings.seed_on_startup and settings.data_mode == "mock":
        from app.core.database import SessionLocal
        from app.data.seed.seed_all import run_seed
        log.info("Seeding demo data...")
        run_seed()
        log.info("Seed complete.")

        # Always run attribution engine after seed so the API has data.
        # Forecast is trained lazily on first request (cheap), but we
        # pre-populate if the artifacts don't exist on disk.
        from app.engines.attribution import compute_attribution, persist_attribution
        from app.engines.forecast.model import (
            forecast_ward,
            persist_forecast_rows,
            train_all_city_models,
        )
        from app.models.city import City
        from app.models.ward import Ward

        session = SessionLocal()
        try:
            cities = session.query(City).all()
            log.info("Computing attribution for %d cities...", len(cities))
            attr_count = 0
            for c in cities:
                wards = session.query(Ward).filter(Ward.city_id == c.id).all()
                for w in wards:
                    r = compute_attribution(session, w, c)
                    persist_attribution(session, w, r)
                    attr_count += 1
            session.commit()
            log.info("Attribution rows: %d", attr_count)

            # Train forecast models if not cached on disk.
            import os
            from pathlib import Path
            model_dir = Path(settings.forecast_model_dir)
            have_models = model_dir.exists() and any(
                p.name.startswith("city_") and p.name.endswith(".joblib")
                for p in model_dir.iterdir()
            )
            if not have_models or settings.forecast_retrain_on_startup:
                log.info("Training forecast models...")
                train_all_city_models(session)

            log.info("Computing forecasts for all wards...")
            fc_count = 0
            for c in cities:
                wards = session.query(Ward).filter(Ward.city_id == c.id).all()
                for w in wards:
                    rows = forecast_ward(session, w)
                    persist_forecast_rows(session, rows)
                    fc_count += len(rows)
            session.commit()
            log.info("Forecast rows: %d", fc_count)
        except Exception as e:
            log.exception("Engine population failed: %s", e)
            session.rollback()
        finally:
            session.close()
    yield
    log.info("Shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "AI-powered Urban Air Quality Intelligence platform for Indian smart cities. "
        "Provides geospatial source attribution, hyperlocal AQI forecasting, "
        "enforcement prioritization, public-health risk overlay, and cross-city "
        "comparative analytics."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

install_cors(app)


# --- Mount routers under /api ---
app.include_router(health.router, prefix="/api", tags=["system"])
app.include_router(cities.router, prefix="/api", tags=["cities"])
app.include_router(wards.router, prefix="/api", tags=["wards"])
app.include_router(geo.router, prefix="/api", tags=["geo"])
app.include_router(attribution.router, prefix="/api", tags=["attribution"])
app.include_router(forecast.router, prefix="/api", tags=["forecast"])
app.include_router(enforcement.router, prefix="/api", tags=["enforcement"])
app.include_router(health_risk.router, prefix="/api", tags=["health"])
app.include_router(advisory.router, prefix="/api", tags=["advisory"])
app.include_router(compare.router, prefix="/api", tags=["compare"])
app.include_router(demo.router, prefix="/api", tags=["demo"])


@app.get("/", include_in_schema=False)
def root():
    """Root redirect target — useful for sanity checks."""
    return {
        "service": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """Return a clean JSON error envelope for unhandled exceptions."""
    log.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "meta": {},
            "error": {"code": "internal_error", "message": "An unexpected error occurred."},
        },
    )
