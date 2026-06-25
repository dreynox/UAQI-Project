# Architecture

> Urban Air Quality Intelligence (UAQI) — end-to-end system design.

---

## 1. What is UAQI?

A multi-city decision-support platform for Indian smart cities (Delhi, Bengaluru, Mumbai) that converts raw AQI readings into actionable, ward-level intervention guidance. Built for ET-AI-2026.

The system is composed of **9 modules** stitched together by a single backend that fuses 4 cooperating AI agents, a per-city forecast model, a priority queue, an action library, and a multilingual advisory generator. A React frontend visualises every module.

---

## 2. High-level components

```
                            ┌──────────────────────────────┐
                            │   React 18 + Vite + Leaflet  │
                            │   TanStack Query + Zustand    │
                            └──────────────┬───────────────┘
                                           │  /api/* (HTTP)
                                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                            │
│                                                                     │
│   ┌────────┐  ┌────────┐  ┌────────────┐  ┌─────────────┐         │
│   │Health  │  │Cities  │  │Wards/Geo   │  │Compare      │  Routers│
│   └────────┘  └────────┘  └────────────┘  └─────────────┘         │
│   ┌────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐        │
│   │Attribution │  │Forecast  │  │Enforcement │  │Advisory  │        │
│   └────────────┘  └──────────┘  └────────────┘  └──────────┘        │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │  Engines (pure Python; no I/O outside the session)        │   │
│   │  • Orchestrator + 4 agents (spatial, satellite, traffic,  │   │
│   │    land_use)                                                │   │
│   │  • Forecast: dispersion-inspired features → GBR per city   │   │
│   │  • Enforcement: priority.py + action_library + impact     │   │
│   │  • Advisory: templates × languages × severity × audience   │   │
│   └──────────────────────────────────────────────────────────┘    │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │  Data layer                                                │   │
│   │  • 15 SQLAlchemy ORM models (SQLite/Postgres)              │   │
│   │  • Seed: deterministic mock data → 30d history, 3 cities   │   │
│   └──────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
                       ┌──────────────────────────────┐
                       │  SQLite (./uaqi.db)          │
                       │  15 tables, ~90K AQI rows,   │
                       │  178 interventions, 250 adv. │
                       └──────────────────────────────┘
```

---

## 3. Directory layout

```
backend/
├── app/
│   ├── main.py                       # FastAPI app + lifespan
│   ├── core/                         # config, database, CORS, logging
│   ├── models/                       # 15 ORM models
│   ├── schemas/common.py             # Pydantic envelope types
│   ├── utils/                        # geo, time, id_gen, envelope
│   ├── data/
│   │   ├── seed/                     # delhi, bengaluru, mumbai
│   │   │                             # + aqi_generator, weather_generator
│   │   │                             # + interventions_generator, advisories_generator
│   │   │                             # + ward_geometries, seed_all
│   │   └── models/                   # city_{1,2,3}_gbr-v1.joblib (forecast)
│   ├── routers/                      # 11 routers under /api
│   │   ├── health.py
│   │   ├── cities.py
│   │   ├── wards.py
│   │   ├── geo.py
│   │   ├── attribution.py
│   │   ├── forecast.py
│   │   ├── enforcement.py
│   │   ├── health_risk.py
│   │   ├── advisory.py
│   │   ├── compare.py
│   │   └── demo.py
│   └── engines/
│       ├── attribution/              # 4 agents + orchestrator + wind + explainer
│       ├── forecast/                 # features + model
│       ├── enforcement/              # priority + action_library + impact_estimator
│       └── advisory/                 # templates + languages + generator
├── scripts/                          # init_db, train_models, populate_engines
├── requirements.txt
├── Dockerfile
├── render.yaml
└── uaqi.db                           # SQLite database

frontend/
├── src/
│   ├── api/                          # axios client + endpoint fns + types
│   ├── components/                   # Layout, WardMap, ui primitives
│   ├── lib/aqi.ts                    # CPCB color scale + helpers
│   ├── pages/                        # 7 page components (9 modules)
│   ├── store/app.ts                  # Zustand store
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts                    # /api proxy → :8000
├── tsconfig.json
└── package.json

docs/
├── architecture.md                   # (this file)
├── api-contract.md
├── demo-script.md
├── presentation-outline.md
└── data-dictionary.md
```

---

## 4. Backend architecture

### 4.1 Application entry

`backend/app/main.py` wires everything together:

1. `init_db()` — creates tables on first boot.
2. `run_seed()` (only if `data_mode=mock`) — wipes + re-seeds the database.
3. After seed:
   - `compute_attribution(...)` for every ward → persists `Attribution` rows.
   - Trains per-city forecast models (skipped if cached `*.joblib` exist).
   - `forecast_ward(...)` for every ward → persists 3 forecast horizons.
4. Mounts 11 routers under `/api`.

### 4.2 Response envelope

Every endpoint returns the same shape:

```json
{
  "data": <endpoint-specific payload>,
  "meta": { "generated_at": "...", ...endpoint-specific fields },
  "warnings": [],
  "error": null
}
```

`utils/envelope.py` provides `ok(data, **meta)` for convenience.

### 4.3 Configuration

`core/config.py` reads from environment variables (and `.env`):

| var | default | purpose |
|---|---|---|
| `APP_ENV` | `development` | toggles debug / production behaviour |
| `CORS_ORIGINS` | `http://localhost:5173,...` | comma-separated allowlist |
| `DATABASE_URL` | `sqlite:///./uaqi.db` | `postgresql://...` for production |
| `DATA_MODE` | `mock` | `mock` seeds on startup; `live` does not |
| `SEED_ON_STARTUP` | `True` | gate for seeding (debug only) |
| `FORECAST_RETRAIN_ON_STARTUP` | `False` | force model retrain |
| `FORECAST_MODEL_DIR` | `./app/data/models` | where `*.joblib` is read/written |

---

## 5. Engines

### 5.1 Multi-agent source attribution

**Goal:** given a ward, return `(top_source, confidence, source_breakdown, evidence)`.

Four cooperating agents each emit a `[0, 1]` score and a list of evidence:

| Agent | Inputs | Output |
|---|---|---|
| `spatial_agent` | bbox + centroid, nearby industries, constructions | which nearby source types contribute most |
| `satellite_agent` | thermal anomalies (biomass / industrial) within last 24h, wind | biomass contribution vs industrial thermals |
| `traffic_agent` | city traffic patterns, ward centroid | traffic intensity score |
| `land_use_agent` | city land-use distribution, bbox | built-up vs open-industrial mix |

The **orchestrator** (`engines/attribution/orchestrator.py`):

1. Pulls latest wind from `WeatherForecast`.
2. Runs all 4 agents in parallel (in the same process).
3. Applies **city-specific fusion weights** (Delhi weights biomass; Bengaluru weights traffic + construction; Mumbai weights industrial).
4. Maps per-agent outputs to **5 canonical buckets** (traffic, construction, industrial, biomass_burning, urban_form).
5. Normalises the breakdown to sum to 1.0.
6. **Confidence** = `(top share) − (second share) + 0.35`, clamped to [0, 1].
7. Renders a human-readable `explanation` via `explainer.py`.
8. Persists an `Attribution` row.

### 5.2 Hyperlocal AQI forecast

**Goal:** for each ward, return 24/48/72h AQI predictions with confidence intervals.

**Features** (`engines/forecast/features.py`, 28 dimensions):

- Diurnal cycle: `sin(2π h/24)`, `cos(2π h/24)`
- Day-of-week cyclical encoding
- Wind: `speed`, `sin(dir)`, `cos(dir)`
- Pasquill-Gifford stability one-hot (A–F)
- Weather snapshot: temp, humidity, pressure, cloud, precip
- **Dispersion-inspired source exposure** (Gaussian plume kernel):
  - `downwind_biomass_intensity` — sum of biomass thermal anomalies upwind, weighted by `exp(-d²/2σ²) · cos²(angle/2)`
  - `downwind_industrial_intensity` — same for industrial thermals
  - `nearby_construction_intensity` — distance-only sum
  - `nearby_industrial_intensity` — distance-only sum
- Lag features: AQI 1h, 3h, 6h, 24h, 48h
- Baseline: `current_aqi`, `current_aqi_delta_24h`

**Model** (`engines/forecast/model.py`):

- `sklearn.ensemble.GradientBoostingRegressor` per city.
- Hyperparameters: `n_estimators=200`, `max_depth=4`, `learning_rate=0.05`.
- Trained on `(feature_row, observed_aqi_at_horizon)` pairs.
- Persisted as `city_{id}_gbr-v1.joblib`.
- **Baseline comparison** (persistence: predict current AQI) — model wins by 30–44 AQI on average.

**Inference** runs the model at 3 horizons per ward, producing `predicted_aqi`, `baseline_aqi`, `confidence_low/high`.

### 5.3 Enforcement intelligence

Three files compose the engine:

| File | Purpose |
|---|---|
| `priority.py` | `compute_urgency(ward, attribution)` — single 0–100 score: `0.55·aqi_severity + 0.3·vulnerability + forecast_trend + attribution_confidence`. Bucketed into `low`/`medium`/`high`/`critical`. |
| `action_library.py` | 8 action types (inspection, dust_control, traffic_diversion, waste_burning, industrial_audit, public_advisory, odd_even, construction_shutdown). Per-source ranked recommendations. |
| `impact_estimator.py` | `estimate_for_action_codes(...)` — blends modeled max-delta with empirical mean from past interventions in DB. Returns `expected_aqi_delta`, `confidence`, `method`. |

The router (`/cities/{code}/enforcement/queue`) pre-loads the latest attribution per ward to avoid N+1, then sorts the entire city by urgency and returns the top N.

### 5.4 Multilingual advisory

| File | Purpose |
|---|---|
| `templates.py` | 48 cells: `severity × audience × language → title + body`. Audiences: `general`, `children_elderly`. Languages: `en`, `hi`, `kn`, `ta`. |
| `languages.py` | `normalize()`, `default_language_for_city()`, `SUPPORTED_LANGUAGES`. |
| `generator.py` | `compose_text(...)` is LLM-ready — today it fills placeholders; swapping in an LLM is one function override. |

Severity is derived from AQI via CPCB breakpoints (good/satisfactory/moderate/poor/very_poor/severe). Audience is selected by `vulnerability_index ≥ 55`. Default language per city: `DEL → hi`, `BLR → kn`, `BOM → ta`, fallback `en`.

---

## 6. Data model (15 tables)

See `docs/data-dictionary.md` for the full per-column reference. Summary:

| Table | Rows | Notes |
|---|---|---|
| `cities` | 3 | Delhi, Bengaluru, Mumbai |
| `wards` | 125 | 50 + 40 + 35; polygons stored as GeoJSON strings |
| `aqi_stations` | 41 | CPCB-style monitoring stations |
| `aqi_time_series` | 90 000 | 30 days × 125 wards, hourly |
| `weather_forecasts` | 504 | 7 days × 3 cities, hourly |
| `industrial_sites` | 160 | emission_type, intensity, compliance_score |
| `construction_sites` | 550 | area_sqm, intensity, is_compliant |
| `thermal_anomalies` | 390 | satellite-derived heat signatures |
| `institutions` | 890 | schools, hospitals, anganwadis |
| `vulnerable_population` | 125 | per-ward vulnerability breakdown |
| `traffic_counts` | ~ | feed for traffic agent |
| `source_registry` | 1 | static catalog of pollution sources |
| `attributions` | 125 | computed at startup, one per ward |
| `forecasts` | 375 | 3 horizons × 125 wards |
| `interventions` | 178 | past enforcement actions |
| `advisories` | 250 | one per (ward, language) |

---

## 7. Request lifecycle — the demo scenario

When the frontend hits `/api/demo/scenario?city_code=DEL`:

1. `cities.py` resolver finds `Delhi NCR`.
2. Worst ward selected by `current_aqi DESC`.
3. `attribution.py` returns latest `Attribution` row.
4. `forecast.py` returns 3 horizons.
5. `enforcement_block` recomputes the priority + actions + impact estimates.
6. `advisory_block` generates a sample English + local-language advisory.
7. `interventions_block` returns 5 most recent + total completed.
8. `context_block` counts nearby institutions/constructions/industries/thermals within bbox and pulls latest weather.

The whole bundle resolves in one round-trip; the frontend renders it as the Story Mode hero.

---

## 8. Deployment

The backend is a stateless FastAPI app. `Dockerfile` and `render.yaml` are ready for one-click deploy on Render.

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For production, set:

- `DATA_MODE=live` (skip seed)
- `DATABASE_URL=postgresql://...` (Postgres)
- `CORS_ORIGINS=https://<frontend-host>`
- `FORECAST_RETRAIN_ON_STARTUP=False` (train offline, ship the `.joblib`)

The frontend is a static Vite build (`dist/`) — deploy to Vercel, Netlify, Render static, or any CDN. Set `VITE_API_BASE` to the production API URL.

---

## 9. Gotchas

- **SQLAlchemy mapper init order**: when importing in a fresh script, eagerly import `app.models.city` and `app.models.aqi` before `app.models.attribution` to avoid "AQISation name not located" errors. Already handled.
- **`AQISation`** is the SQLAlchemy class name (intentional pun: "Ambient Air Quality Monitoring Station"). All code uses it; the table is still `aqi_stations`.
- **Forecast models persist** to `backend/app/data/models/city_{id}_gbr-v1.joblib`. Lifespan auto-trains if missing.
- **City-specific weights** in `orchestrator.py`: DEL emphasises satellite/biomass, BLR emphasises traffic+construction, BOM emphasises industrial.
- **Lifespan always re-seeds** on startup by default. Demo reliability > startup speed (~30s). For production, gate with `DATA_MODE=live`.
- **All AQI readings** are anchored at `2026-06-25 23:00:00` (the seed's "now"). Forecasts target +24/48/72h from there.
- **Interventions seed** uses `(aqi/100)^2.0` ward weights + force-injects top-3 wards with 3/2/1 completed interventions so `/api/demo/scenario` always has intervention history on the worst ward.
