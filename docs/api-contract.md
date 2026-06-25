# API Contract — Urban Air Quality Intelligence (UAQI)

> Every endpoint the backend exposes, what it returns, and what the frontend consumes.
> Base URL in dev: `http://127.0.0.1:8000`. In dev the Vite dev server proxies `/api/*`
> straight to the backend (see `frontend/vite.config.ts`), so the frontend always calls
> relative `/api/...`.

---

## 0. Envelope

Every successful response is wrapped:

```json
{
  "data": <payload>,
  "meta": {
    "generated_at": "2026-06-25T10:07:45.801927+00:00",
    "city": "DEL",
    "model_version": "v1",
    "metric": "aqi",
    "count": 3
  },
  "warnings": [],
  "error": null
}
```

Errors return standard FastAPI HTTP errors with `{"detail": "..."}`. The frontend
axios interceptor in `frontend/src/api/client.ts` unwraps `data` and surfaces the
`error.message` / `detail` / `error` field as the rejection reason.

---

## 1. System

### `GET /api/health`

Liveness + DB connectivity.

```json
{
  "data": {
    "status": "ok",
    "service": "Urban Air Quality Intelligence",
    "version": "1.0.0",
    "env": "development",
    "data_mode": "mock",
    "database_ok": true,
    "database_error": null,
    "timestamp": "2026-06-25T10:07:45.801927+00:00"
  }
}
```

Polls every 30s from `Layout.tsx`.

---

## 2. Cities & Overview

### `GET /api/cities`

List all seeded cities with at-a-glance summary.

| Field | Type | Notes |
|---|---|---|
| `code` | string | `DEL` / `BLR` / `BOM` |
| `name` | string | Display name |
| `state` | string | Indian state |
| `country` | string | Always `IN` |
| `center_lat`, `center_lon` | float | Map center |
| `bbox` | [4]float | `[min_lat, min_lon, max_lat, max_lon]` |
| `population_millions` | float | |
| `primary_language` | string | `hi` / `kn` / `mr` |
| `wards_count` | int | |
| `mean_aqi` | float \| null | Across all wards |
| `latest_reading_at` | ISO8601 \| null | |

### `GET /api/cities/{code}`

Single city metadata.

### `GET /api/cities/{code}/overview`

Full city dashboard payload. Used by `Overview.tsx`.

```json
{
  "data": {
    "city": { "code", "name", "center_lat", "center_lon", "population_millions", "primary_language" },
    "kpis": {
      "mean_aqi", "top10_mean_aqi", "max_aqi", "min_aqi",
      "wards_count", "institutions_count",
      "construction_sites_count", "industrial_sites_count", "thermal_anomalies_count"
    },
    "hotspots": [
      {
        "ward_id", "ward_code", "ward_name",
        "centroid_lat", "centroid_lon",
        "current_aqi", "aqi_category",
        "vulnerability_index", "population"
      }
    ],
    "weather": {
      "temperature_c", "humidity_pct", "wind_speed_kmh", "wind_dir_deg",
      "stability_class", "timestamp"
    },
    "generated_at"
  }
}
```

### `GET /api/cities/{code}/wards`

All wards for a city, sorted by AQI desc.

### `GET /api/cities/{code}/hotspots?limit=10`

Top-N wards by current AQI (same shape as hotspots above).

---

## 3. Wards

### `GET /api/wards/{ward_id}`

Single ward detail (id, code, name, lat/lon, population, current_aqi, vulnerability).

### `GET /api/wards/{ward_id}/attribution`

Multi-agent attribution result. Used by `WardDetail.tsx`.

```json
{
  "data": {
    "ward_id", "ward_name",
    "top_source",      // "traffic" | "construction" | "industrial" | "stubble_burning" | ...
    "confidence",      // 0-1
    "source_breakdown",// { source: share, ... }  sums to 1.0
    "agent_evidence",  // { spatial: {...}, satellite: {...}, traffic: {...}, land_use: {...} }
    "explanation",     // 1-2 sentence human-readable narrative
    "computed_at"
  }
}
```

### `GET /api/wards/{ward_id}/forecast?horizons=24,48,72`

Per-horizon forecast with confidence bands + persistence baseline.

```json
{
  "data": {
    "ward_id", "ward_name", "current_aqi",
    "forecasts": [
      {
        "horizon_hours": 24,
        "target_time", "generated_at",
        "predicted_aqi", "baseline_aqi",  // baseline = persistence ("tomorrow = today")
        "confidence_low", "confidence_high",
        "model_version": "gbr-v1"
      }
    ]
  }
}
```

`model_advantage = baseline_aqi - predicted_aqi` (positive = our model beats persistence).

### `GET /api/wards/{ward_id}/forecast/compare`

Compact forecast-vs-baseline view for the "show our value" panel.

### `GET /api/wards/{ward_id}/advisory?lang=hi|en|kn|ta`

Multilingual advisory. Audience is derived from ward vulnerability
(`general` or `children_elderly`).

```json
{
  "data": {
    "ward_id", "ward_name", "language", "audience",
    "severity",   // "good" | "satisfactory" | "moderate" | "poor" | "very_poor" | "severe"
    "category",   // human-readable category
    "title", "body",  // body in requested language
    "valid_from", "valid_until"
  }
}
```

Fallback chain: requested lang → city's `primary_language` → `en`.

### `GET /api/cities/{code}/advisory`

Sample advisory for the city (uses city's primary language).

---

## 4. Geo Layers

All return `GeoJSON FeatureCollection`.

| Endpoint | Layer | Geometry |
|---|---|---|
| `GET /api/cities/{code}/geo/wards` | Ward polygons | `Polygon` |
| `GET /api/cities/{code}/geo/layers/{layer}` | `institutions` / `industry` / `construction` / `thermal` | `Point` |
| `GET /api/cities/{code}/geo/traffic` | Traffic density grid (⚠ not implemented — returns 404) | — |

Each `Feature.properties` includes the relevant domain fields (ward_id, intensity,
capacity, etc.) so the frontend can render popups without a second round-trip.

---

## 5. Enforcement

### `GET /api/cities/{code}/enforcement/queue?limit=10`

Prioritized inspector action list across all wards in the city.

```json
{
  "data": [
    {
      "ward_id", "ward_code", "ward_name",
      "current_aqi", "top_source",
      "urgency_score",   // 0-100
      "actions": [
        {
          "action_code", "label",
          "rationale",
          "estimated_aqi_delta"   // negative = AQI reduction expected
        }
      ]
    }
  ]
}
```

Sorted by `urgency_score` desc.

### `GET /api/cities/{code}/enforcement/{ward_id}`

Same shape but a single ward, with full breakdown of priority components:

```json
{
  "data": {
    "ward_id", "ward_name", "current_aqi", "top_source",
    "urgency_score",
    "components": {
      "aqi_severity", "vulnerability", "forecast_trend",
      "attribution_confidence", "institution_density"
    },
    "actions": [ ... ]
  }
}
```

---

## 6. Public Health Overlay

### `GET /api/cities/{code}/health/overlay`

Per-ward vulnerability breakdown.

```json
{
  "data": [
    {
      "ward_id", "ward_name", "centroid_lat", "centroid_lon",
      "vulnerability_index",
      "schools", "hospitals", "elderly_care",
      "outdoor_workers", "anganwadis", "orphanages",
      "total_sensitive_population"
    }
  ]
}
```

---

## 7. Compare (Cross-City)

### `GET /api/compare/cities?metric=aqi|vulnerability|interventions`

```json
{
  "data": [
    {
      "code", "name", "state",
      "mean_aqi", "max_aqi", "mean_vulnerability",
      "population_millions", "primary_language",
      "wards_count",
      "worst_ward", "worst_ward_aqi", "worst_ward_id",
      "dominant_source",       // most common top_source across wards
      "source_counts",         // { source: ward_count, ... }
      "source_share",          // { source: mean_share, ... }
      "interventions_count", "interventions_mean_delta"
    }
  ]
}
```

### `GET /api/compare/interventions`

Effectiveness across all cities.

```json
{
  "data": [
    {
      "city_code", "action_type",
      "count", "mean_aqi_delta", "median_aqi_delta",
      "best_delta", "worst_delta"
    }
  ]
}
```

Sorted by `mean_aqi_delta` asc (best reductions first).

### `GET /api/compare/interventions/{city_code}`

Same shape, filtered to one city.

---

## 8. Demo / Story Mode

### `GET /api/demo/scenario?city_code=DEL|BLR|BOM`

Pre-canned "what's happening right now in {city}" bundle.

```json
{
  "data": {
    "headline": { "city", "current_aqi", "category", "top_source", "worst_ward_name", "summary" },
    "attribution": { ... same shape as /wards/{id}/attribution ... },
    "forecast":    { ... same shape as /wards/{id}/forecast ... },
    "enforcement": { "urgency_score", "actions": [...] },
    "advisory":    { "en": {...}, "<local_lang>": {...} },
    "interventions": {
      "total", "recent": [ { action_type, timestamp, status, measured_aqi_delta } ]
    },
    "context": {
      "institutions_nearby", "constructions_nearby",
      "industries_nearby", "thermals_nearby",
      "weather": { ... }
    }
  }
}
```

### `GET /api/demo/story?city_code=DEL|BLR`

Guided 4-step Story Mode flow.

```json
{
  "data": {
    "city_code", "city_name",
    "steps": [
      {
        "step": 1, "title", "subtitle",
        "ward_id", "ward_name", "ward_code",
        "current_aqi", "category", "top_source",
        "explanation",
        "api_calls": [ "/api/wards/{id}/attribution", "..." ]
      },
      ...
    ]
  }
}
```

The frontend (`Story.tsx`, 425 lines) renders one step per screen with a
"Next →" button that resolves the next ward ID from the previous step.

---

## 9. Source buckets (canonical)

`top_source` / `source_breakdown` keys across all endpoints:

```
traffic, construction, industrial, stubble_burning,
biomass_burning, waste_burning, urban_form, mixed
```

---

## 10. Frontend ↔ Backend query surface

The full set of axios calls the frontend makes (see `frontend/src/api/queries.ts`):

| Query fn | Endpoint |
|---|---|
| `fetchHealth` | `GET /health` |
| `fetchCities` | `GET /cities` |
| `fetchCityOverview` | `GET /cities/{code}/overview` |
| `fetchCityWards` | `GET /cities/{code}/wards` |
| `fetchCityHotspots` | `GET /cities/{code}/hotspots?limit=N` |
| `fetchWard` | `GET /wards/{wardId}` |
| `fetchWardGeo` | `GET /cities/{code}/geo/wards` |
| `fetchLayer` | `GET /cities/{code}/geo/layers/{layer}` |
| `fetchAttribution` | `GET /wards/{wardId}/attribution` |
| `fetchForecast` | `GET /wards/{wardId}/forecast?horizons=24,48,72` |
| `fetchEnforcementQueue` | `GET /cities/{code}/enforcement/queue?limit=N` |
| `fetchWardEnforcement` | `GET /cities/{code}/enforcement/{wardId}` |
| `fetchHealthOverlay` | `GET /cities/{code}/health/overlay` |
| `fetchAdvisory` | `GET /wards/{wardId}/advisory?lang={lang}` |
| `fetchCityAdvisory` | `GET /cities/{code}/advisory` |
| `fetchCompareCities` | `GET /compare/cities?metric={metric}` |
| `fetchCompareInterventions` | `GET /compare/interventions` |
| `fetchCompareInterventionsForCity` | `GET /compare/interventions/{code}` |
| `fetchDemoScenario` | `GET /demo/scenario?city_code={code}` |
| `fetchDemoStory` | `GET /demo/story?city_code={code}` |
