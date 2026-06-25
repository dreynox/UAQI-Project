# PROJECT_STATE — Urban Air Quality Intelligence (UAQI)

Last updated: 2026-06-25 (end of session 3 — backend + frontend E2E verified live; all docs complete; demo video still needed). Re-read on 2026-06-25 at start of session 4 — no state drift; P9 user actions remain the only outstanding work.

## Goal

Multi-city decision-support platform for Indian smart cities (Delhi, Bengaluru, Mumbai) that turns raw AQI data into actionable intervention guidance. Nine modules per the original architecture: Multi-City Overview, Interactive Map, Multi-Agent Source Attribution, Hyperlocal AQI Forecast, Enforcement Intelligence, Public Health Risk Overlay, Multi-City Comparative Dashboard, Multilingual Citizen Advisory, and Demo Story Mode. Built for the ET-AI-2026 hackathon.

## Architecture

### Tech Stack
- **Backend:** FastAPI + SQLAlchemy 2.0 + SQLite (Postgres-ready) + Pydantic v2 + scikit-learn
- **Frontend:** React 18 + TypeScript + Vite + Tailwind + Leaflet + Recharts + Zustand + TanStack Query + axios (✅ scaffold + 7 pages built, build verified, E2E against backend ✅ VERIFIED LIVE)
- **AI:** 4 cooperating agents (Spatial, Satellite, Traffic, Land Use) fused by an orchestrator; per-city scikit-learn GradientBoostingRegressor with dispersion-inspired features
- **Deployment:** Dockerfile + render.yaml ready

### Directory Layout
```
D:/Hackathons/ET-AI-2026/
├── ReadMe.txt                 # Full project history
├── PROJECT_STATE.md           # This file
├── README.md                  # ✅ Top-level README (172 lines)
├── Project_requirements.txt
├── Problem_statement.txt
├── ET_AI_Hackathon_2026_Problem_Statements.pdf
├── backend/                   # ✅ Built and verified end-to-end
│   ├── app/
│   │   ├── core/              # config, database, cors, logging
│   │   ├── models/            # 15 ORM models
│   │   ├── schemas/           # common envelope
│   │   ├── utils/             # geo, time, id_gen, envelope
│   │   ├── data/seed/         # delhi/bengaluru/mumbai + ward_geometries + generators
│   │   │                      # + interventions_generator + advisories_generator
│   │   ├── data/models/       # city_{1,2,3}_gbr-v1.joblib
│   │   ├── routers/           # 11 routers under /api
│   │   ├── engines/
│   │   │   ├── attribution/   # spatial/satellite/traffic/land_use/wind/orchestrator/explainer
│   │   │   ├── forecast/      # features/model
│   │   │   ├── enforcement/   # priority/action_library/impact_estimator
│   │   │   └── advisory/      # templates/languages/generator
│   │   └── main.py
│   ├── scripts/               # init_db, train_models, populate_engines, check_db, test_forecast
│   ├── requirements.txt, Dockerfile, render.yaml, README.md
│   ├── uaqi.db                # 27 MB SQLite (3 cities seeded)
│   └── run_dev.bat, run_dev.sh
├── frontend/                  # ✅ Built (scaffold + 7 pages + components), E2E VERIFIED LIVE
│   ├── index.html
│   ├── package.json / vite.config.ts / tailwind.config.js / tsconfig*
│   ├── src/
│   │   ├── main.tsx, App.tsx           # React Router with 7 routes (Layout-wrapped)
│   │   ├── components/                 # Layout, ui, WardMap
│   │   ├── pages/                      # Overview, Map, WardDetail, Enforcement, Compare, HealthOverlay, Story
│   │   ├── api/                        # client.ts (axios + envelope unwrap), queries.ts, types.ts
│   │   ├── store/                      # Zustand: selectedCity (DEL/BLR/BOM) + selectedWardId
│   │   └── lib/aqi.ts                  # AQI category + color helpers
│   └── dist/                           # Production build output (verified tsc + vite build OK)
└── docs/                      # ✅ ALL DOCS COMPLETE
    ├── architecture.md        # ✅ (319 lines) — system design + 9 sections
    ├── api-contract.md        # ✅ (419 lines) — every endpoint + shape + frontend query surface
    ├── data-dictionary.md     # ✅ (294 lines) — every table + column + canonical enums
    ├── demo-script.md         # ✅ (166 lines) — 3-minute judge walkthrough with live numbers
    ├── presentation-outline.md # ✅ (204 lines) — 8-slide pitch + 4 backup slides
    └── RUN_AND_TEST.md        # ✅ (~500 lines) — complete run + test guide with every curl verified live
```

## What Is Implemented

### Backend (✅ complete and verified end-to-end)
1. **Data layer** — 15 ORM models, fully seeded:
   - 3 cities (DEL: 50 wards, BLR: 40, BOM: 35)
   - 41 AQI stations + 90,000 hourly AQI readings (30 days × 3 cities)
   - 504 hourly weather rows (7 days × 3 cities)
   - 160 industrial sites, 550 construction sites, 390 thermal anomalies
   - 890 institutions, 125 vulnerable-population records
   - **178 interventions** (60 DEL + 45 BLR + 55 BOM + 18 force-injected on top-AQI wards)
   - **250 advisories** (en + city-language for every ward)
2. **Attribution engine** — 4 cooperating agents (spatial/satellite/traffic/land_use) fused by orchestrator with city-specific weights. Verified city-specific stories: DEL→stubble_burning, BLR→construction, BOM→traffic/construction/industrial.
3. **Forecast engine** — Per-city GradientBoostingRegressor with dispersion-inspired features. Model RMSE 22-29 AQI vs persistence baseline 59-66 (~30-44 AQI advantage).
4. **Enforcement engine** — priority.py (multi-component urgency = AQI severity × vuln × forecast trend × attribution confidence), action_library.py (8 action types + per-source ranking), impact_estimator.py (modeled + empirical AQI delta blending past intervention history).
5. **Advisory engine** — templates.py (severity × audience × language = 48 cells in en/hi/kn/ta), languages.py (registry + city defaults), generator.py (LLM-ready `compose_text` interface, persists to DB).
6. **Compare + Demo polish** — `/compare/cities` returns per-source breakdowns + dominant_source + per-city intervention stats. `/compare/interventions/{city}` new per-city endpoint. `/demo/scenario` returns a full bundle (headline + attribution + forecast + enforcement + advisory in en+local + interventions + context). `/demo/story` resolves to live ward IDs and real numbers.
7. **Past interventions seed** — 178 rows; biased toward high-AQI wards via `(aqi/100)^2.0` weights + top-3 force-inject so demo's worst ward always has 4-5 visible interventions.
8. **Routers** — 11 routers live under `/api`: health, cities, wards, geo, attribution, forecast, enforcement, health_risk, advisory, compare, demo.
9. **Lifespan** — On startup: init_db → seed (wipe + reseed) → train forecast models if no cached .joblib → compute attribution for all wards → compute forecasts for all wards → serve.
10. **Deployment** — Dockerfile + render.yaml ready.

### Frontend (✅ scaffold + 7 pages built, E2E verified live against backend)
- Vite + React 18 + TypeScript + Tailwind + react-router-dom + TanStack Query + Zustand + axios + leaflet + react-leaflet + recharts — installed via package.json
- App.tsx mounts 7 routes inside `<Layout />` outlet: `/`, `/city/:code`, `/map`, `/map/:code`, `/ward/:wardId`, `/enforcement`, `/enforcement/:code`, `/compare`, `/health`, `/health/:code`, `/story`, `/story/:code`
- Components built: Layout (header nav + 6 nav items), ui (shared primitives), WardMap (Leaflet wrapper)
- Pages built (7): Overview, Map, WardDetail, Enforcement, Compare, HealthOverlay, Story (Story.tsx is 425 lines — largest module, anchored on `/api/demo/story`)
- API client: axios with `VITE_API_BASE` env (defaults to `/api`), envelope unwrap helper, error interceptor that surfaces backend error messages
- Zustand store: `selectedCity` (DEL/BLR/BOM, defaults DEL), `selectedWardId` (for drilldown)
- **Build verified 2026-06-25:** `tsc -b && vite build` succeeded (chunk-size warning only, no errors)
- **E2E verified live 2026-06-25 (session 3):** Backend uvicorn :8000 + frontend Vite :5173 booted; all 20 frontend-called endpoints probed through Vite proxy returned 200; all 14 page/component TSX modules transformed cleanly; BLR + BOM variants + all 4 geo layers returned 200; `/api/cities/{code}/geo/traffic` returns 404 (frontend doesn't call it — not a bug).

### Verified Live (curl-tested 2026-06-25)

- `/api/health` → 200 ok, DB connected
- `/api/cities` → 3 cities with mean AQI (DEL=305.7, BOM=206.3, BLR=176.3)
- `/api/cities/DEL/wards` → 50 wards, sorted by AQI
- `/api/cities/DEL/geo/wards` → GeoJSON FeatureCollection
- `/api/cities/DEL/geo/layers/{institutions|industry|construction|thermal}` → all 200
- `/api/wards/34/attribution` → Okhla: top=stubble_burning, conf=0.457, source_breakdown (biomass 0.42, construction 0.32, traffic 0.15, industrial 0.10, urban_form 0.01)
- `/api/wards/34/forecast` → 24h=325.5, 48h=335.1, 72h=326.6 (vs persistence 374.4 → +24h advantage 48.9 AQI)
- `/api/wards/34/forecast/compare` → compact forecast-vs-baseline summary
- `/api/cities/DEL/enforcement/queue?limit=3` → Narela (priority 79.6, high), Tilak Nagar (79.1), all stubble_burning
- `/api/cities/DEL/enforcement/34` → Okhla: priority_score 69.3, actions odd_even (-16.7), public_advisory (-2.6), waste_burning (-19.2)
- `/api/wards/34/advisory?lang=hi` → Hindi advisory (very_poor / general)
- `/api/wards/34/advisory?lang=kn` → Kannada fallback works
- `/api/wards/93/advisory?lang=ta` → Tamil with `audience=children_elderly` (high-vuln ward)
- `/api/cities/BLR/advisory` → default_language=kn, sample Kannada ward
- `/api/compare/interventions` → 23 (city, action) buckets with mean + median delta
- `/api/compare/interventions/DEL` → 8 action types ranked; construction_shutdown -30.0 best
- `/api/compare/cities?metric=aqi` → DEL 50/50 → stubble_burning, BLR 40/40 → construction, BOM distributed
- `/api/compare/cities?metric=interventions` → sorted by mean intervention delta
- `/api/demo/scenario?city_code=DEL|BLR|BOM` → enriched bundle with headline + advisory + 4-5 completed interventions
- `/api/demo/story?city_code=DEL|BLR` → 4 steps resolving to live ward IDs and real numbers

### Verified Build (2026-06-25)
- Backend re-booted during session 2 → `/api/health` returned 200 ok (background curl confirmed)
- Backend re-booted during session 3 (warning log level) → seeded, attributed, forecasted, served on :8000
- Frontend `npm run build` (tsc + vite) → succeeded with only a chunk-size warning (no errors)
- Frontend `npm run dev` → Vite ready in 369ms on :5173; zustand optimised; all 14 page modules served 200

### Documentation (✅ ALL COMPLETE)
- `docs/architecture.md` — 319 lines — system design, components, data flow, deployment, gotchas
- `docs/api-contract.md` — 419 lines — every endpoint with shape + frontend query surface mapping
- `docs/data-dictionary.md` — 294 lines — every table, every column, canonical enums, row counts
- `docs/demo-script.md` — 166 lines — 3-minute judge demo with live numbers (Okhla 374, forecast 326, etc.)
- `docs/presentation-outline.md` — 204 lines — 8-slide pitch + 4 backup slides + stage directions
- `docs/RUN_AND_TEST.md` — ~500 lines — beginner-friendly run/test guide; every curl command in §5.2 verified to return 200 live during session 3
- `README.md` (top-level) — 172 lines — quick-start, modules table, deploy guide, links to all docs

### Hackathon Readiness Assessment (session 3 review)

**Verdict: hackathon-ready and shippable as-is.** All 5 challenge modules and 3 of 4 expected deliverables are in the repo. The 4th deliverable (demo video) is not built — but `docs/demo-script.md` provides the exact 3-minute flow to record or perform live.

| Module | Status |
|---|---|
| Geospatial Source Attribution (multi-agent, statistical confidence) | ✅ Done |
| Hyperlocal Predictive AQI Forecast (24-72h, dispersion features) | ✅ Done |
| Enforcement Intelligence & Prioritisation | ✅ Done |
| Multi-City Comparative Intelligence Dashboard | ✅ Done |
| Citizen Health Risk Advisory (multilingual hi/kn/ta/en) | ✅ Done |
| Working Prototype | ✅ Verified live |
| Architecture Diagram | ✅ `docs/architecture.md` |
| Presentation Deck | ✅ `docs/presentation-outline.md` |
| Demo Video | ⚠ **Not built** — script ready in `docs/demo-script.md` |

**Honest caveats:** Sentinel/MODIS, CAAQMS, real atmospheric dispersion, and real LLM calls are simulated via realistic mocks + clean integration points. Multi-agent "agents" are Python functions with weighted fusion (not distributed processes). Both trade-offs are deliberate for hackathon reliability and documented in `docs/architecture.md` §8.

## What Is Pending

### P9 — Final ship (NOT STARTED — user actions required)

The codebase is complete and verified. The remaining items are user/deploy actions, not code work:

- ❌ **Record the demo video** (3-minute screen-record of `/story/DEL` walkthrough) — script in `docs/demo-script.md`. Only deliverable in the spec not on disk.
- ❌ **Capture 5–7 screenshots** for the presentation deck (optional but recommended)
- ❌ **Choose deploy target and deploy**:
  - Backend → Render (Dockerfile + render.yaml ready, one-click)
  - Frontend → Vercel/Netlify/Cloudflare Pages (static build, set `VITE_API_BASE` to deployed backend URL)
- ❌ **(Optional) Wire live feeds** for production:
  - Set `DATA_MODE=live`, `SEED_ON_STARTUP=false`
  - Populate `aqi_stations` + `aqi_time_series` from OpenAQ/CPCB
  - Populate `thermal_anomalies` from Sentinel-2/MODIS
  - Replace `engines/advisory/generator.py:compose_text` with real LLM call

## Quick Reference

### Run backend
```bash
cd backend
pip install -r requirements.txt
python scripts/init_db.py        # one-time seed (or just boot uvicorn)
uvicorn app.main:app --reload --port 8000
```

### Force retrain forecasts
```bash
cd backend
python scripts/train_models.py --retrain
```

### Test endpoints
```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/cities
curl http://127.0.0.1:8000/api/wards/34/attribution
curl http://127.0.0.1:8000/api/wards/34/forecast
curl http://127.0.0.1:8000/api/demo/scenario?city_code=DEL
curl http://127.0.0.1:8000/api/demo/story?city_code=DEL
curl http://127.0.0.1:8000/api/compare/cities
```

### Run frontend (dev mode)
```bash
cd frontend
npm install                # if not yet
npm run dev                # Vite dev server (default :5173, proxies /api via VITE_API_BASE)
npm run build              # Production build → frontend/dist/
```

### Full run + test guide
See `docs/RUN_AND_TEST.md` for the complete beginner-friendly walkthrough (every curl command verified live, troubleshooting section, env var reference, smoke-test loop, etc.).

## Immediate Next Steps (where the previous session stopped)

P7 and P8 are now COMPLETE. The only remaining item from PROJECT_STATE.md is **P9 — Final E2E verification + ship**, which is the deployment step. That's not code work — it requires:

1. **User action**: Record the demo video (3 min screen-record of `/story/DEL`)
2. **User action**: Pick deploy target (Render for backend + Vercel/Netlify for frontend)
3. **User action**: Create accounts and deploy (or run locally for the hackathon demo)

The codebase is in a "ready to ship or demo" state.

## Key Files to Read First
- `backend/app/main.py` — lifespan + router mounting
- `backend/app/engines/attribution/orchestrator.py` — multi-agent fusion
- `backend/app/engines/forecast/model.py` — per-city GBR training + inference
- `backend/app/engines/forecast/features.py` — dispersion-inspired feature engineering
- `backend/app/engines/enforcement/priority.py` — multi-component urgency scoring
- `backend/app/engines/enforcement/action_library.py` — 8 action types + per-source mapping
- `backend/app/engines/advisory/generator.py` — multilingual advisory composition
- `backend/app/engines/advisory/templates.py` — severity × audience × language templates
- `backend/app/routers/forecast.py`, `attribution.py`, `enforcement.py`, `advisory.py`, `compare.py`, `demo.py` — API surface
- `docs/RUN_AND_TEST.md` — how to run + test everything
- `docs/architecture.md` — system design
- `docs/api-contract.md` — every endpoint

## Notes / Gotchas
- SQLAlchemy mapper init order matters: when importing in a fresh script, eagerly import `app.models.city` and `app.models.aqi` before `app.models.attribution` to avoid "AQISation name not located" errors. Already handled in scripts via explicit module imports.
- The DB class is named `AQISation` (intentional — stands for "Ambient Air Quality Monitoring Station").
- Forecast models persist to `backend/app/data/models/city_{id}_gbr-v1.joblib`. Lifespan auto-trains if missing.
- City-specific weights in `orchestrator.py`: DEL emphasizes satellite/biomass, BLR emphasizes traffic+construction, BOM emphasizes industrial.
- The lifespan currently always re-seeds and re-runs engines on startup. This is intentional for demo reliability but slow (~30s). For production, gate with env flags.
- All AQI readings are anchored at `2026-06-25 23:00:00` (the seed's "now"). Forecasts target +24/48/72h from there.
- Interventions seed uses `(aqi/100)^2.0` ward weights + force-injects top-3 wards with 3/2/1 completed interventions so `/api/demo/scenario` always has intervention history on the worst ward.
- Enforcement API field is `priority_score` (not `urgency_score`); action list is `recommended_actions` (not `actions`).
- `/api/cities/{code}/geo/traffic` is NOT implemented (returns 404). Frontend never calls it.
- The Vite dev server on :5173 proxies `/api/*` to :8000 transparently — so the frontend always uses relative `/api/...` URLs.