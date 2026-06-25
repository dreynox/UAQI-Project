# Backend

FastAPI service for Urban Air Quality Intelligence.

## Run locally

```bash
# Windows
run_dev.bat
# macOS/Linux
./run_dev.sh
```

The backend will:
1. Create the SQLite DB (`uaqi.db`) and tables on first run.
2. Seed demo data (3 cities × 30 days hourly AQI, weather, traffic, etc.).
3. Start on `http://localhost:8000`. Docs at `/docs`.

## Manual reseed

```bash
python scripts/init_db.py
```

## Environment

See `.env.example`. Override `DATABASE_URL` to point at Postgres.

## Endpoints

See `../docs/api-contract.md`. Health check at `GET /api/health`.