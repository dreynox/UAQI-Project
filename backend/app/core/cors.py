"""CORS configuration."""

from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

# When DEBUG and origins is "*" we still allow credentials=False (browser rule).
# For production, set explicit origins in CORS_ORIGINS.
_origins = settings.cors_origin_list or ["*"]

cors_middleware_kwargs = dict(
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def install_cors(app) -> None:
    """Install CORS middleware on the FastAPI app."""
    app.add_middleware(CORSMiddleware, **cors_middleware_kwargs)
