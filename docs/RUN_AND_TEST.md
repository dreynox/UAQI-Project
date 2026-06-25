# How to Run & Test UAQI — Complete Guide

> Step-by-step instructions to get the Urban Air Quality Intelligence
> platform running locally and verify every module end-to-end.
>
> Tested on: **Windows 11 + Python 3.11.9 + Node 24.11.1**.
> macOS and Linux work identically — only the activation command differs.

---

## 0. Prerequisites

You need **both** of these installed on your machine:

| Tool | Minimum version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ (LTS recommended) | `node --version` |
| npm | comes with Node | `npm --version` |
| pip | comes with Python | `pip --version` |

If you don't have them:
- Python → https://www.python.org/downloads/ (tick "Add to PATH" on Windows)
- Node.js → https://nodejs.org/ (download the LTS build)

That's it. No database server, no API keys, no Docker required for local dev.

---

## 1. Project layout (what lives where)

```
ET-AI-2026/
├── backend/         FastAPI service (Python)
├── frontend/        React app (Node + Vite)
├── docs/            Architecture, API contract, demo script, etc.
└── README.md        Top-level overview
```

Two processes run side-by-side: **backend on port 8000** and **frontend on port 5173**.
The frontend's Vite dev server is configured to proxy `/api/*` requests straight to
the backend, so the browser only ever talks to `:5173`.

---

## 2. First-time setup (5 min)

### 2.1 Backend

```bash
cd backend

# (Recommended) create a virtual environment — keeps deps isolated
python -m venv .venv

# Activate it
#   Windows (PowerShell):
.venv\Scripts\Activate.ps1
#   Windows (cmd):
.venv\Scripts\activate.bat
#   macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the env template (only once)
copy .env.example .env          # Windows cmd
# cp .env.example .env          # macOS / Linux bash
```

You should see a fresh `.venv/` folder and a `.env` file in `backend/`.

> **Note for Windows PowerShell users:** if `Activate.ps1` is blocked by
> execution policy, run this once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
> Then retry the activation.

### 2.2 Frontend

```bash
cd frontend

npm install
```

This downloads React, Vite, Leaflet, Recharts, Zustand, TanStack Query, axios, etc.
Takes 1-2 minutes the first time; subsequent installs are near-instant.

---

## 3. Running the app (the actual demo)

You need **two terminals** open — one for backend, one for frontend.

### Terminal 1 — Backend (FastAPI :8000)

```bash
cd backend
# (activate venv first if you created one — see 2.1)

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see logs that look like:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
2026-06-25 [INFO] uaqi.main: Starting Urban Air Quality Intelligence (env=development, data_mode=mock)
2026-06-25 [INFO] uaqi.main: Seeding demo data...
2026-06-25 [INFO] uaqi.seed: Wiping existing demo data...
2026-06-25 [INFO] uaqi.seed: Seeding city: build_delhi
2026-06-25 [INFO] uaqi.seed:   wards=50 stations=15 ...
...
2026-06-25 [INFO] uaqi.main: Seed complete.
2026-06-25 [INFO] uaqi.main: Computing attribution for 3 cities...
2026-06-25 [INFO] uaqi.main: Attribution rows: 125
2026-06-25 [INFO] uaqi.main: Computing forecasts for all wards...
2026-06-25 [INFO] uaqi.forecast: Loaded forecast model for city_id=1 from ...
...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**First boot takes ~30 seconds** (DB creation + seeding + training forecast models).
Subsequent boots are ~5 seconds.

### Terminal 2 — Frontend (Vite :5173)

```bash
cd frontend
npm run dev
```

You should see:

```
  VITE v5.4.21  ready in 369 ms

  ➜  Local:   http://127.0.0.1:5173/
```

### Open the app

Point your browser at:

> **http://localhost:5173/story/DEL** ← start here, this is the demo

Or just `http://localhost:5173/` for the multi-city overview.

---

## 4. The "is it working?" smoke test

Run this curl **in a third terminal** (or after the backend has fully started):

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "data": {
    "status": "ok",
    "service": "Urban Air Quality Intelligence",
    "version": "1.0.0",
    "env": "development",
    "data_mode": "mock",
    "database_ok": true,
    ...
  }
}
```

If you see `"status": "ok"` and `"database_ok": true` — you're good.

---

## 5. Testing every module (the fun part)

The frontend has 7 pages; each one corresponds to a backend module.
The fastest way to verify the whole stack is to walk these 7 pages in order
with the browser open at `http://localhost:5173/`.

### 5.1 The 7-page walkthrough

| # | Page | URL | What you should see |
|---|---|---|---|
| 1 | **Overview** | `/` or `/city/DEL` | 3 cities, mean AQI tiles (DEL=305.7, BOM=206.3, BLR=176.3), 5 hotspot cards |
| 2 | **Map** | `/map/DEL` | Leaflet map of all 50 Delhi wards colored by AQI, layer toggles |
| 3 | **Ward Detail** | click any ward, or `/ward/34` | Attribution + forecast chart + enforcement actions + multilingual advisory |
| 4 | **Enforcement** | `/enforcement/DEL` | Prioritized inspector queue (Narela 79.6, Tilak Nagar 79.1) with action cards |
| 5 | **Compare** | `/compare` | Cross-city table: DEL=stubble_burning, BLR=construction, BOM=traffic |
| 6 | **Health Overlay** | `/health/DEL` | Per-ward vulnerability map (schools, hospitals, elderly care) |
| 7 | **Story Mode** | `/story/DEL` | Guided 4-step demo: hotspot → source → forecast → intervention |

### 5.2 Testing each backend module with curl

If you want to verify the API directly (and not just trust the frontend), here
are the 20 endpoints the frontend calls. **All should return HTTP 200.**

#### System

```bash
# Health check
curl http://127.0.0.1:8000/api/health
```

#### Cities & Overview

```bash
# List 3 cities
curl http://127.0.0.1:8000/api/cities

# Full city dashboard
curl http://127.0.0.1:8000/api/cities/DEL/overview

# Wards sorted by AQI
curl "http://127.0.0.1:8000/api/cities/DEL/wards?limit=5"

# Top-N hotspots
curl "http://127.0.0.1:8000/api/cities/DEL/hotspots?limit=3"
```

#### Wards (the core intelligence layer)

```bash
# Single ward detail
curl http://127.0.0.1:8000/api/wards/34

# Multi-agent source attribution (Okhla, DEL)
curl http://127.0.0.1:8000/api/wards/34/attribution
# Expected: top_source="stubble_burning", confidence≈0.46

# Hyperlocal AQI forecast (24/48/72h)
curl "http://127.0.0.1:8000/api/wards/34/forecast?horizons=24,48,72"
# Expected: predicted ~325, baseline ~374, improvement ~49

# Forecast vs persistence baseline (compact view)
curl http://127.0.0.1:8000/api/wards/34/forecast/compare

# Multilingual advisory (try lang=hi|kn|ta|en)
curl "http://127.0.0.1:8000/api/wards/34/advisory?lang=hi"
curl "http://127.0.0.1:8000/api/wards/34/advisory?lang=kn"
curl "http://127.0.0.1:8000/api/wards/34/advisory?lang=ta"

# City-default-language advisory
curl http://127.0.0.1:8000/api/cities/DEL/advisory
```

#### Geo layers (for the Map page)

```bash
# Ward polygons (GeoJSON)
curl http://127.0.0.1:8000/api/cities/DEL/geo/wards > wards.geojson

# Point layers (institutions, industry, construction, thermal anomalies)
curl http://127.0.0.1:8000/api/cities/DEL/geo/layers/institutions
curl http://127.0.0.1:8000/api/cities/DEL/geo/layers/industry
curl http://127.0.0.1:8000/api/cities/DEL/geo/layers/construction
curl http://127.0.0.1:8000/api/cities/DEL/geo/layers/thermal
```

> ℹ Note: `/api/cities/{code}/geo/traffic` returns 404 — that route is not
> implemented (the Map page never calls it). All four layers above are 200.

#### Enforcement + Health

```bash
# Prioritized inspector queue for the city
curl "http://127.0.0.1:8000/api/cities/DEL/enforcement/queue?limit=5"
# Expected: Narela, Tilak Nagar, etc. with urgency scores

# Per-ward enforcement breakdown
curl http://127.0.0.1:8000/api/cities/DEL/enforcement/34
# Expected: priority_score≈69, actions: odd_even, public_advisory, waste_burning

# Per-ward vulnerability overlay
curl http://127.0.0.1:8000/api/cities/DEL/health/overlay
```

#### Cross-city comparison

```bash
# Per-city rollup (sort by AQI / vulnerability / interventions)
curl "http://127.0.0.1:8000/api/compare/cities?metric=aqi"
curl "http://127.0.0.1:8000/api/compare/cities?metric=interventions"

# Intervention effectiveness across all cities
curl http://127.0.0.1:8000/api/compare/interventions
# Expected: ~23 (city, action_type) buckets, sorted by mean_aqi_delta

# Per-city intervention effectiveness
curl http://127.0.0.1:8000/api/compare/interventions/DEL
# Expected: 8 action types, best is construction_shutdown
```

#### Demo / Story Mode (the killer endpoint)

```bash
# Pre-bundled "what's happening right now in {city}"
curl "http://127.0.0.1:8000/api/demo/scenario?city_code=DEL"
curl "http://127.0.0.1:8000/api/demo/scenario?city_code=BLR"
curl "http://127.0.0.1:8000/api/demo/scenario?city_code=BOM"

# Guided 4-step storyboard
curl "http://127.0.0.1:8000/api/demo/story?city_code=DEL"
# Expected: 4 steps, step 1 = Okhla (AQI 374), step 4 = enforcement actions
```

### 5.3 The "everything is wired" probe (one-liner)

```bash
# Probe every endpoint the frontend uses, all in one go.
# Exit code 0 = all green. (Bash only — for PowerShell, run the loop manually.)

for path in \
  /api/health \
  /api/cities \
  /api/cities/DEL/overview \
  /api/cities/DEL/wards \
  /api/cities/DEL/hotspots?limit=10 \
  /api/cities/DEL/geo/wards \
  /api/cities/DEL/geo/layers/institutions \
  /api/cities/DEL/geo/layers/industry \
  /api/cities/DEL/geo/layers/construction \
  /api/cities/DEL/geo/layers/thermal \
  /api/cities/DEL/enforcement/queue?limit=10 \
  /api/cities/DEL/enforcement/34 \
  /api/cities/DEL/health/overlay \
  /api/wards/34 \
  /api/wards/34/attribution \
  /api/wards/34/forecast?horizons=24,48,72 \
  /api/wards/34/advisory?lang=hi \
  /api/cities/DEL/advisory \
  /api/compare/cities?metric=aqi \
  /api/compare/interventions \
  /api/compare/interventions/DEL \
  /api/demo/scenario?city_code=DEL \
  /api/demo/story?city_code=DEL ; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000${path}")
  echo "${code}  ${path}"
done
```

All 23 should print `200`. If anything prints `404` or `500`, the backend has
a problem — see [§ 7 Troubleshooting](#7-troubleshooting).

### 5.4 Same probe through the Vite proxy (validates the frontend wiring)

Same loop, but hit port 5173 instead of 8000. If all return 200, the frontend
can talk to the backend correctly:

```bash
# Same loop as 5.3, just change the base URL:
#   http://127.0.0.1:8000 → http://127.0.0.1:5173
```

---

## 6. Useful commands

### 6.1 Reseed the database

The backend seeds on every boot (intentional — keeps the demo reproducible).
If you want to manually reseed without restarting:

```bash
cd backend
python scripts/init_db.py
```

This wipes `uaqi.db` and re-creates + re-seeds everything.

### 6.2 Force-retrain forecast models

```bash
cd backend
python scripts/train_models.py --retrain
```

Useful if you want to demonstrate that the GBR actually trains from scratch.
The trained models are cached at `backend/app/data/models/city_{1,2,3}_gbr-v1.joblib`.

### 6.3 Backend sanity scripts

```bash
# Quick DB connectivity + row counts
python scripts/check_db.py

# Hit a single forecast endpoint
python scripts/test_forecast.py

# Re-run attribution + forecast for all wards (no seed wipe)
python scripts/populate_engines.py
```

### 6.4 Production build (frontend)

```bash
cd frontend
npm run build      # tsc + vite build → dist/
npm run preview    # serve dist/ locally to test the production build
```

### 6.5 Interactive API docs

While the backend is running, open:

> **http://localhost:8000/docs** ← FastAPI's auto-generated Swagger UI

You can click any endpoint, hit "Try it out", and see the full response.

---

## 7. Troubleshooting

### 7.1 "Address already in use" / port 8000 collision

Another process is on port 8000. Find and kill it:

```bash
# Windows PowerShell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PID> -Force

# macOS / Linux
lsof -i :8000
kill -9 <PID>
```

Or just run the backend on a different port:

```bash
uvicorn app.main:app --port 8001
# Then update frontend/vite.config.ts proxy target to 8001.
```

### 7.2 "Module not found" on `uvicorn` start

The virtualenv isn't activated, or `pip install` didn't complete. Retry:

```bash
cd backend
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

### 7.3 Backend boots but `/api/health` returns `database_ok: false`

The SQLite file got into a bad state. Wipe and reseed:

```bash
cd backend
rm uaqi.db
uvicorn app.main:app --reload --port 8000
# Lifespan will re-create the DB + re-seed.
```

### 7.4 Frontend shows a blank page or "Network Error"

- Open browser DevTools → Network tab. Is anything failing?
- Confirm backend is up: `curl http://127.0.0.1:8000/api/health`
- Confirm Vite proxy is configured: see `frontend/vite.config.ts`. It should
  have `proxy: { "/api": { target: "http://127.0.0.1:8000" } }`.
- Hard refresh the browser (Ctrl+Shift+R / Cmd+Shift+R) — Vite HMR can
  occasionally cache a stale module.

### 7.5 "Port 5173 is in use" (frontend)

Vite picks the next free port. Check the terminal output for the actual URL.
You can force a specific port:

```bash
npm run dev -- --port 5174
```

### 7.6 Forecast model fails to train

You'll see something like `ValueError: could not convert string to float` in
the backend log. Most common cause: stale `uaqi.db` from before a schema
change. Fix:

```bash
cd backend
rm uaqi.db
rm app/data/models/*.joblib
uvicorn app.main:app --reload --port 8000
```

### 7.7 Stuck on a `wandb` / MLflow / TensorFlow prompt

The project doesn't use any of these. If `pip install` triggers one, you
probably have a global `requirements.txt` shadow. Make sure you're running
from inside the venv:

```bash
which python     # macOS/Linux  →  should point to backend/.venv/bin/python
where python     # Windows cmd  →  should show backend\.venv\Scripts\python.exe first
```

### 7.8 Leaflet map shows grey squares / tiles don't load

You're offline. Leaflet tiles come from `tile.openstreetmap.org` — needs
internet on first load. After that, the map works offline (tiles are cached
by the browser).

### 7.9 I want a totally clean re-run

```bash
# Backend
cd backend
rm -rf .venv uaqi.db app/data/models/*.joblib
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
rm -rf node_modules dist
npm install
npm run dev
```

---

## 8. What "good" looks like

After step 3, you should be able to:

| Click | See |
|---|---|
| `http://localhost:5173/` | Dark "command center" overview with 3 city tiles (DEL mean AQI 305.7, BOM 206.3, BLR 176.3) |
| Click "Map" in the nav | Leaflet map of India zoomed into Delhi, wards colored by AQI |
| Click any ward | Ward detail page with attribution radar + forecast chart + enforcement actions + advisory |
| `http://localhost:5173/story/DEL` | 4-step storyboard resolving to Okhla → stubble_burning → forecast 326 vs 374 baseline → enforcement actions |
| `http://localhost:5173/compare` | 3-city table: Delhi=stubble_burning, BLR=construction, BOM=traffic |
| `http://localhost:5173/health/DEL` | Per-ward vulnerability overlay |
| `curl /api/wards/34/advisory?lang=hi` | Hindi advisory for Okhla |
| `curl /api/cities/DEL/enforcement/queue?limit=3` | Narela (priority 79.6, high), Tilak Nagar (79.1), all stubble_burning |

If all of the above work, the platform is fully functional and demo-ready.

---

## 9. Running the 3-minute judge demo

Once everything is up, follow `docs/demo-script.md` for the exact
judge-walking flow. The short version:

1. **Start at `/story/DEL`** (don't make judges navigate)
2. **Step 1** — *"Delhi NCR has 50 wards. The worst is Okhla at AQI 374."*
3. **Step 2** — *"Why? Stubble burning 46%. Four cooperating agents agree."*
4. **Step 3** — *"Tomorrow: AQI 326. Naive forecast: 374. We beat it by 49."*
5. **Step 4** — *"Inspector gets: odd-even, waste-burning crackdown, public advisory. Cost and lead time shown."*
6. **Pivot to `/compare`** — *"Mumbai's enforcement has the best measured impact. Cross-city learning."*
7. **Switch to Hindi advisory** — *"Outreach isn't just English."*
8. **Close** — *"This compresses signal-to-intervention time from days to minutes."*

---

## 10. Next steps after running locally

| Want to... | Do this |
|---|---|
| Deploy the backend | `backend/Dockerfile` + `backend/render.yaml` are ready. Connect repo to Render for one-click deploy. |
| Deploy the frontend | Set `VITE_API_BASE=https://<your-backend>.onrender.com/api`, then `npm run build`. Deploy `dist/` to Vercel/Netlify/Cloudflare Pages. |
| Wire real Sentinel/MODIS data | Populate the `thermal_anomalies` table (schema in `docs/data-dictionary.md`); no code change needed. |
| Wire real OpenAQ/CPCB feed | Populate `aqi_stations` + `aqi_time_series`; set `DATA_MODE=live` and `SEED_ON_STARTUP=false`. |
| Swap templated advisories for a real LLM | Replace `engines/advisory/generator.py:compose_text` with an LLM call. Interface is already LLM-ready. |
| Add a 4th city | Drop a new `build_{city}.py` into `backend/app/data/seed/`, add it to `seed_all.py`, add a row to the `cities` table. Done. |

---

## Appendix A — Environment variables

All optional, all have safe defaults. Edit `backend/.env` if you want to change anything.

| Variable | Default | What it does |
|---|---|---|
| `APP_ENV` | `development` | `development` or `production` |
| `APP_PORT` | `8000` | Port the backend listens on |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |
| `DATABASE_URL` | `sqlite:///./uaqi.db` | SQLAlchemy URL. Switch to `postgresql://...` for prod. |
| `DATA_MODE` | `mock` | `mock` = seeded demo data; `live` = skip seed (for future live integration) |
| `SEED_ON_STARTUP` | `true` | Wipe + reseed DB on every boot. Set `false` for production. |
| `SEED_RANDOM_SEED` | `42` | Deterministic seed for reproducible demo data |
| `DEMO_DAYS_HISTORY` | `30` | How many days of AQI history to seed |
| `DEMO_FORECAST_HOURS` | `72` | Forecast horizon (hours) |
| `FORECAST_RETRAIN_ON_STARTUP` | `false` | Force-retrain GBR models on every boot. Off by default (uses cached `.joblib`). |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

Frontend: only `VITE_API_BASE` (defaults to `/api`, which the Vite proxy handles automatically).
