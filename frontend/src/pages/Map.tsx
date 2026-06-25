import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  fetchWardGeo,
  fetchLayer,
  fetchCityOverview,
  fetchCityAdvisory,
} from "@/api/queries";
import { Panel, LoadingRows } from "@/components/ui";
import { aqiColor, aqiLabel } from "@/lib/aqi";
import type { CityCode } from "@/store/app";
import WardMap from "@/components/WardMap";

const VALID_CODES: CityCode[] = ["DEL", "BLR", "BOM"];

const LAYERS = [
  { id: "institutions", label: "Schools / Hospitals" },
  { id: "industry", label: "Industrial sites" },
  { id: "construction", label: "Construction sites" },
  { id: "thermal", label: "Thermal anomalies" },
] as const;

export default function MapPage() {
  const { code } = useParams<{ code?: string }>();
  const selected: CityCode = (code && VALID_CODES.includes(code as CityCode)
    ? code
    : "DEL") as CityCode;

  const [activeLayers, setActiveLayers] = useState<Set<string>>(new Set());

  const { data: overview } = useQuery({
    queryKey: ["cityOverview", selected],
    queryFn: () => fetchCityOverview(selected),
  });

  const { data: wardGeo } = useQuery({
    queryKey: ["wardGeo", selected],
    queryFn: () => fetchWardGeo(selected),
  });

  const { data: cityAdvisory } = useQuery({
    queryKey: ["cityAdvisory", selected],
    queryFn: () => fetchCityAdvisory(selected),
  });

  // Fetch each layer independently so toggling enables / disables hooks safely
  const institutionsQ = useQuery({
    queryKey: ["layer", selected, "institutions"],
    queryFn: () => fetchLayer(selected, "institutions"),
    enabled: activeLayers.has("institutions"),
    staleTime: 60_000,
  });
  const industryQ = useQuery({
    queryKey: ["layer", selected, "industry"],
    queryFn: () => fetchLayer(selected, "industry"),
    enabled: activeLayers.has("industry"),
    staleTime: 60_000,
  });
  const constructionQ = useQuery({
    queryKey: ["layer", selected, "construction"],
    queryFn: () => fetchLayer(selected, "construction"),
    enabled: activeLayers.has("construction"),
    staleTime: 60_000,
  });
  const thermalQ = useQuery({
    queryKey: ["layer", selected, "thermal"],
    queryFn: () => fetchLayer(selected, "thermal"),
    enabled: activeLayers.has("thermal"),
    staleTime: 60_000,
  });

  const layerOverlays = {
    institutions: institutionsQ.data,
    industry: industryQ.data,
    construction: constructionQ.data,
    thermal: thermalQ.data,
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Interactive Map</h1>
        <div className="ml-auto flex items-center gap-2">
          {VALID_CODES.map((c) => (
            <Link
              key={c}
              to={`/map/${c}`}
              className={`px-3 py-1.5 rounded-md text-sm border transition ${
                c === selected
                  ? "bg-accent-500/15 border-accent-500/40 text-accent-400"
                  : "bg-ink-800 border-ink-600 text-slate-300 hover:bg-ink-700"
              }`}
            >
              {c}
            </Link>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <Panel
          title="Ward AQI choropleth"
          subtitle={
            overview
              ? `${overview.city?.name ?? selected} · ${
                  wardGeo?.features?.length ?? 0
                } ward polygons · click any ward to drill in`
              : "Loading…"
          }
          className="overflow-hidden"
        >
          <div className="h-[640px] -mx-4 -mb-4">
            {wardGeo && overview ? (
              <WardMap
                cityCode={selected}
                geojson={wardGeo}
                center={[
                  overview.city?.center_lat ?? 28.6,
                  overview.city?.center_lon ?? 77.2,
                ]}
                zoom={11}
                layerOverlays={layerOverlays}
              />
            ) : (
              <div className="h-full flex items-center justify-center">
                <LoadingRows rows={5} />
              </div>
            )}
          </div>
        </Panel>

        <div className="space-y-4">
          <Panel title="Layers" subtitle="Toggle point overlays">
            <div className="space-y-2">
              {LAYERS.map((l) => {
                const checked = activeLayers.has(l.id);
                return (
                  <label
                    key={l.id}
                    className="flex items-center gap-2 text-sm cursor-pointer hover:bg-ink-700/40 px-2 py-1.5 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const next = new Set(activeLayers);
                        if (e.target.checked) next.add(l.id);
                        else next.delete(l.id);
                        setActiveLayers(next);
                      }}
                      className="accent-accent-500"
                    />
                    <span>{l.label}</span>
                  </label>
                );
              })}
            </div>
            <div className="mt-3 text-[11px] text-slate-500 leading-relaxed border-t border-ink-600/40 pt-2">
              Polygons coloured by current AQI. Click a polygon for ward pop-up;
              click "open detail" to drill in.
            </div>
          </Panel>

          <Panel title="Color scale" subtitle="CPCB AQI breakpoints">
            <div className="space-y-1">
              {[
                { label: "Good", range: "0–50", color: aqiColor(20) },
                { label: "Satisfactory", range: "51–100", color: aqiColor(80) },
                { label: "Moderate", range: "101–200", color: aqiColor(150) },
                { label: "Poor", range: "201–300", color: aqiColor(250) },
                { label: "Very Poor", range: "301–400", color: aqiColor(350) },
                { label: "Severe", range: "401+", color: aqiColor(450) },
              ].map((s) => (
                <div key={s.label} className="flex items-center gap-2 text-xs">
                  <span
                    className="inline-block w-4 h-4 rounded"
                    style={{ background: s.color }}
                  />
                  <span className="font-medium">{s.label}</span>
                  <span className="text-slate-400 ml-auto">{s.range}</span>
                </div>
              ))}
            </div>
          </Panel>

          {cityAdvisory && (
            <Panel title="Citizen voice" subtitle={`Default ${cityAdvisory.default_language}`}>
              <div className="text-xs text-slate-400 mb-1">
                Sample advisory for {cityAdvisory.sample_advisory?.ward_name}
              </div>
              {cityAdvisory.sample_advisory && (
                <div className="space-y-1">
                  <div className="text-sm font-semibold">
                    {cityAdvisory.sample_advisory.title}
                  </div>
                  <div className="text-xs text-slate-300 leading-relaxed">
                    {cityAdvisory.sample_advisory.body}
                  </div>
                  <Link
                    to={`/ward/${cityAdvisory.sample_advisory.ward_id}`}
                    className="text-[11px] text-accent-400 hover:underline block mt-1"
                  >
                    Open advisory →
                  </Link>
                </div>
              )}
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}