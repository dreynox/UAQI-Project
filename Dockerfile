# Top-level Dockerfile for Railway.
# Railway looks for ./Dockerfile at the repo root. This file:
#  1. Copies the backend/ contents into /app
#  2. Installs deps and runs uvicorn from there
# This avoids needing the "Root Directory" dashboard setting.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (kept minimal; shapely needs GEOS).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend folder's contents (the build context becomes /app).
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/scripts ./scripts

ENV APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080

EXPOSE 8080

# Railway injects $PORT at runtime. We use an entrypoint shell script
# so $PORT is expanded by the shell (the JSON-array CMD form does NOT
# expand env vars — they're passed as literals, which is why $PORT was
# being treated as the string "$PORT" instead of the port number).
RUN printf '#!/bin/sh\nexec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"\n' \
    > /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
