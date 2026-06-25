# Urban Air Quality Intelligence (UAQI)

> Multi-city decision-support platform for Indian smart cities (Delhi, Bengaluru,
> Mumbai) that turns raw AQI data into actionable intervention guidance. Built
> for the ET-AI-2026 hackathon.

The system answers the **4-question loop every city admin needs in 5 seconds**:

1. **Where** is pollution worst? → Interactive Map + Hotspots
2. **Why** is it bad here? → Multi-Agent Source Attribution
3. **What'll it be** tomorrow? → Hyperlocal Forecast (24/48/72h)
4. **What should I do**? → Prioritized Enforcement + Multilingual Advisory

Plus a 5th: **what worked elsewhere?** → Cross-City Comparative Learning.

## What's in the box

| Layer | Status |
|---|---|
| Backend (FastAPI + SQLAlchemy 2 + scikit-learn) | ✅ Built and verified end-to-end |
| Frontend (React 18 + TS + Vite + Leaflet + Recharts) | ✅ Built and verified end-to-end |
| Story Mode (`/api/demo/story`) | ✅ Live, 4 steps per city |
| Docs (`docs/architecture.md`, `api-contract.md`, `data-dictionary.md`, `demo-script.md`, `presentation-outline.md`) | ✅ Complete |
| Deployment (Dockerfile + render.yaml) | 🟡 Backend ready, frontend static build ready, deploy target TBD |

## Run it locally (3 commands)

Need Python 3.11+ and Node 18+. For the **complete step-by-step guide** (gotchas, troubleshooting, every curl command), see **[`docs/RUN_AND_TEST.md`](docs/RUN_AND_TEST.md)**. The short version:

```bash
# 1. Backend (FastAPI :8000)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000  ·  /docs for OpenAPI

# 2. Frontend (Vite :5173 — proxies /api to :8000)
cd frontend
npm install
npm run dev
# → http://localhost:5173

# 3. Open Story Mode
# → http://localhost:5173/story/DEL
```

On first boot, the backend will:
1. Create `backend/uaqi.db` (SQLite) and all tables.
2. Seed 3 cities × 30 days of hourly AQI + 7 days of weather + 178 interventions
   + 250 advisories.
3. Train per-city GradientBoostingRegressor forecast models (or load from
   `backend/app/data/models/*.joblib` if present).
4. Compute attribution for all 125 wards.
5. Serve on `:8000`.

Startup takes ~30s the first time (seed + train); subsequent boots are <5s.

## Project structure

```
ET-AI-2026/
├── backend/                  FastAPI service
│   ├── app/
│   │   ├── main.py           lifespan + router mount
│   │   ├── core/             config, database, cors, logging
│   │   ├── models/           15 SQLAlchemy ORM models
│   │   ├── schemas/          Pydantic response envelopes
│   │   ├── routers/          11 routers under /api
│   │   ├── engines/
│   │   │   ├── attribution/  spatial / satellite / traffic / land_use / wind / orchestrator / explainer
│   │   │   ├── forecast/     features / model (per-city GBR)
│   │   │   ├── enforcement/  priority / action_library / impact_estimator
│   │   │   └── advisory/     templates / languages / generator
│   │   └── data/seed/        delhi / bengaluru / mumbai / generators
│   ├── scripts/              init_db, train_models, populate_engines, check_db, test_forecast
│   ├── requirements.txt
│   ├── Dockerfile            Render-ready
│   └── render.yaml           one-click deploy
├── frontend/                 React 18 + Vite
│   ├── src/
│   │   ├── pages/            Overview · Map · WardDetail · Enforcement · Compare · HealthOverlay · Story
│   │   ├── components/       Layout · ui · WardMap
│   │   ├── api/              axios client + queries + types
│   │   ├── store/            Zustand (selected city, selected ward)
│   │   └── lib/              AQI helpers
│   ├── vite.config.ts        dev server proxies /api → :8000
│   └── package.json
├── docs/
│   ├── architecture.md       system design (read first)
│   ├── api-contract.md       every endpoint + shape
│   ├── data-dictionary.md    every table + column
│   ├── demo-script.md        3-minute judge demo script
│   └── presentation-outline.md  5-minute pitch
└── PROJECT_STATE.md          authoritative project state
```

## The 9 modules (per `Project_requirements.txt`)

| # | Module | Where in code |
|---|---|---|
| 1 | Multi-City Overview | `frontend/src/pages/Overview.tsx` · `/api/cities/{code}/overview` |
| 2 | Interactive Map | `frontend/src/pages/Map.tsx` + `WardMap.tsx` · `/api/cities/{code}/geo/wards` |
| 3 | Source Attribution (multi-agent) | `engines/attribution/` · `/api/wards/{id}/attribution` |
| 4 | Hyperlocal AQI Forecast | `engines/forecast/` · `/api/wards/{id}/forecast` |
| 5 | Enforcement Intelligence | `engines/enforcement/` · `/api/cities/{code}/enforcement/queue` |
| 6 | Public Health Risk Overlay | `frontend/src/pages/HealthOverlay.tsx` · `/api/cities/{code}/health/overlay` |
| 7 | Multi-City Comparative Dashboard | `frontend/src/pages/Compare.tsx` · `/api/compare/cities` |
| 8 | Multilingual Citizen Advisory | `engines/advisory/` · `/api/wards/{id}/advisory?lang={hi|kn|ta|en}` |
| 9 | Demo / Story Mode | `frontend/src/pages/Story.tsx` · `/api/demo/story` |

## Tech stack rationale

| Choice | Why |
|---|---|
| FastAPI + Pydantic v2 | Async, OpenAPI, fast contract iteration |
| SQLAlchemy 2.0 + SQLite (Postgres-ready) | Zero setup for demo, one-line swap via `DATABASE_URL` |
| scikit-learn GradientBoostingRegressor | Interpretable, fast, no GPU. RMSE 22-29 AQI vs persistence 59-66. |
| React 18 + Vite + TypeScript | Fast HMR, small bundle, the standard for 2026 |
| TanStack Query + Zustand | Server state + minimal client state. No Redux. |
| Leaflet | Free, no API key, perfect for hackathon |
| Recharts | SVG charts, easy to theme |

## Live demo flow (3 minutes)

1. `http://localhost:5173/` — Three cities at a glance. Delhi worst (305.7 mean AQI).
2. `http://localhost:5173/story/DEL` — 4-step storyboard:
   - **Okhla** is the worst ward (AQI 374)
   - Why: **stubble_burning 46%** (4 cooperating agents agree)
   - Forecast: **326 in 24h** vs 374 persistence baseline (-49 AQI advantage)
   - Action: odd-even vehicle scheme (-16.7 AQI est.), waste-burning crackdown (-19.2 AQI est.)
3. `http://localhost:5173/compare` — Delhi worst, but Mumbai's enforcement has the best measured impact (-13.6 AQI per action).
4. `http://localhost:5173/ward/34/advisory?lang=hi` — Hindi advisory in one click.

Full script in [`docs/demo-script.md`](docs/demo-script.md).

## What's mocked vs. real

The platform is built for live data; the demo uses realistic mocks so judges
see a working system offline. To go live, set `DATA_MODE=live` and:

- Wire Sentinel-2 / MODIS thermal-anomaly feed into `backend/app/data/seed/`
  (or a real ingestion job) — schema is ready in `thermal_anomalies` table.
- Wire CPCB / OpenAQ station feed into `aqi_stations` + `aqi_time_series`.
- Replace `engines/advisory/generator.py:compose_text` with a real LLM call —
  the interface is already LLM-ready.
- Swap `engines/forecast/features.py` for a full Gaussian-plume model if
  needed (current features are dispersion-*inspired*, not real CFD).

See [`docs/architecture.md` § 8 Deployment](docs/architecture.md#8-deployment) for
the production env flags and integration points.

## Deploy

### Backend (Render)

`backend/render.yaml` is ready. One-click deploy: connect the repo, Render
auto-detects the Dockerfile, runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Frontend (Vercel / Netlify / static)

`frontend/dist/` is a static build. Set `VITE_API_BASE=https://<your-backend>.onrender.com/api`
before `npm run build` and deploy the `dist/` directory to any static host.

## Read these first

1. **[`docs/RUN_AND_TEST.md`](docs/RUN_AND_TEST.md)** — how to run + test the project locally
2. **[`PROJECT_STATE.md`](PROJECT_STATE.md)** — current state of the project
3. **[`docs/architecture.md`](docs/architecture.md)** — system design
4. **[`docs/api-contract.md`](docs/api-contract.md)** — every endpoint
5. **[`docs/demo-script.md`](docs/demo-script.md)** — judge demo

## License

Hackathon project — see `ReadMe.txt` for the original problem statement and
context.
