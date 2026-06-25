# UAQI Frontend

React 18 + TypeScript + Vite + Tailwind + Leaflet + Recharts + Zustand + TanStack Query.

## Run

The dev server is configured to proxy `/api` → `http://127.0.0.1:8000`, so make
sure the FastAPI backend is running first.

```bash
npm install
npm run dev
```

Open http://localhost:5173

## Build

```bash
npm run build
npm run preview
```

## Modules

- `/` Multi-City Overview
- `/map` Interactive ward map (Leaflet choropleth + toggleable layers)
- `/enforcement` Priority queue + intervention effectiveness
- `/compare` Cross-city comparative dashboard
- `/health` Public health risk overlay
- `/story` Guided 4-step demo script
- `/ward/:id` Deep ward detail (attribution + forecast + enforcement + advisory)
