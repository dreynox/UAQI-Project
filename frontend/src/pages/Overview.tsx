import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  fetchCities,
  fetchCityHotspots,
  fetchCityOverview,
  fetchCompareCities,
  fetchDemoScenario,
} from "@/api/queries";
import { Panel, Kpi, Badge, LoadingRows } from "@/components/ui";
import { aqiColor, aqiLabel, formatNumber, sourceLabel } from "@/lib/aqi";
import type { CityCode } from "@/store/app";

const VALID_CODES: CityCode[] = ["DEL", "BLR", "BOM"];

export default function OverviewPage() {
  const { code } = useParams<{ code?: string }>();
  const selected: CityCode = (code && VALID_CODES.includes(code as CityCode)
    ? code
    : "DEL") as CityCode;

  const { data: cities } = useQuery({
    queryKey: ["cities"],
    queryFn: fetchCities,
  });

  const { data: overview, isLoading } = useQuery({
    queryKey: ["cityOverview", selected],
    queryFn: () => fetchCityOverview(selected),
  });

  const { data: hotspots } = useQuery({
    queryKey: ["cityHotspots", selected, 5],
    queryFn: () => fetchCityHotspots(selected, 5),
  });

  const { data: demo } = useQuery({
    queryKey: ["demoScenario", selected],
    queryFn: () => fetchDemoScenario(selected),
  });

  const { data: compare } = useQuery({
    queryKey: ["compareCities"],
    queryFn: () => fetchCompareCities("aqi"),
  });

  return (
    <div className="space-y-6">
      {/* Header strip: city selector */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Multi-City Overview</h1>
        <div className="ml-auto flex items-center gap-2">
          {VALID_CODES.map((c) => (
            <Link
              key={c}
              to={`/city/${c}`}
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

      {/* Cross-city strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cities?.map((c) => (
          <Link
            key={c.code}
            to={`/city/${c.code}`}
            className={`panel hover:border-accent-500/40 transition ${
              c.code === selected ? "border-accent-500/40" : ""
            }`}
          >
            <div className="flex items-baseline justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-slate-400">{c.code}</div>
                <div className="text-lg font-semibold">{c.name}</div>
                <div className="text-xs text-slate-400">{c.state} · {c.population_millions}M</div>
              </div>
              <div className="text-right">
                <div
                  className="text-3xl font-bold"
                  style={{ color: aqiColor(c.mean_aqi ?? 0) }}
                >
                  {formatNumber(c.mean_aqi ?? 0)}
                </div>
                <div className="text-[10px] uppercase text-slate-400 tracking-wider">
                  mean AQI
                </div>
              </div>
            </div>
            <div className="mt-2 text-xs text-slate-400">
              {c.wards_count} wards · default {c.primary_language}
            </div>
          </Link>
        ))}
      </div>

      {/* City KPIs */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Kpi
            label="Mean AQI"
            value={formatNumber(overview.kpis.mean_aqi)}
            hint={`${overview.kpis.wards_count} wards`}
            tone={overview.kpis.mean_aqi > 300 ? "bad" : overview.kpis.mean_aqi > 200 ? "warn" : "info"}
          />
          <Kpi label="Top-10 mean" value={formatNumber(overview.kpis.top10_mean_aqi)} tone="bad" />
          <Kpi label="Max AQI" value={formatNumber(overview.kpis.max_aqi)} tone="bad" />
          <Kpi label="Vuln. index (avg)" value="— " hint="see Compare tab" />
          <Kpi
            label="Wind"
            value={
              overview.weather.wind_speed_kmh != null
                ? `${formatNumber(overview.weather.wind_speed_kmh)} km/h`
                : "—"
            }
            hint={
              overview.weather.stability_class
                ? `Stability ${overview.weather.stability_class}`
                : undefined
            }
            tone="info"
          />
        </div>
      )}

      {/* Two-column: hotspots + headline scenario */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel
          title={`Top hotspots · ${selected}`}
          subtitle="Highest-AQI wards in the city"
          className="lg:col-span-2"
        >
          {isLoading ? (
            <LoadingRows rows={5} />
          ) : hotspots && hotspots.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wider text-slate-400 border-b border-ink-600">
                    <th className="text-left py-2">Ward</th>
                    <th className="text-right">AQI</th>
                    <th className="text-right">Category</th>
                    <th className="text-right">Vuln.</th>
                    <th className="text-right">Population</th>
                  </tr>
                </thead>
                <tbody>
                  {hotspots.map((w) => (
                    <tr
                      key={w.id}
                      className="border-b border-ink-600/40 hover:bg-ink-700/40 cursor-pointer"
                      onClick={() => (window.location.href = `/ward/${w.id}`)}
                    >
                      <td className="py-2">
                        <div className="font-medium">{w.name}</div>
                        <div className="text-xs text-slate-500">{w.ward_code}</div>
                      </td>
                      <td className="text-right font-mono" style={{ color: aqiColor(w.current_aqi) }}>
                        {formatNumber(w.current_aqi)}
                      </td>
                      <td className="text-right">
                        <Badge
                          tone={
                            w.current_aqi > 300 ? "bad" : w.current_aqi > 200 ? "warn" : "info"
                          }
                        >
                          {aqiLabel(w.current_aqi)}
                        </Badge>
                      </td>
                      <td className="text-right text-slate-300">
                        {formatNumber(w.vulnerability_index)}
                      </td>
                      <td className="text-right text-slate-300">{formatNumber(w.population)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-sm text-slate-500">No hotspots</div>
          )}
        </Panel>

        <Panel title="Headline scenario" subtitle={`Worst ward in ${selected}`}>
          {demo ? (
            <div className="space-y-3">
              <div className="text-lg font-medium leading-snug">{demo.scenario.headline}</div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <div className="text-xs text-slate-400">Ward</div>
                  <div className="font-medium">{demo.scenario.ward.name}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">AQI</div>
                  <div
                    className="font-mono text-xl font-bold"
                    style={{ color: aqiColor(demo.scenario.ward.current_aqi) }}
                  >
                    {formatNumber(demo.scenario.ward.current_aqi)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Top source</div>
                  <div className="font-medium">
                    {demo.attribution
                      ? sourceLabel(demo.attribution.top_source)
                      : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Confidence</div>
                  <div className="font-mono">
                    {demo.attribution
                      ? `${(demo.attribution.confidence * 100).toFixed(0)}%`
                      : "—"}
                  </div>
                </div>
              </div>
              <Link
                to={`/ward/${demo.scenario.ward.id}`}
                className="block text-center text-xs py-2 px-3 rounded bg-accent-500/20 hover:bg-accent-500/30 text-accent-400 border border-accent-500/40 transition"
              >
                Open ward detail →
              </Link>
            </div>
          ) : (
            <LoadingRows rows={4} />
          )}
        </Panel>
      </div>

      {/* Compare strip */}
      <Panel title="Cross-city comparison" subtitle="Sorted by mean AQI (worst first)">
        {compare ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-400 border-b border-ink-600">
                  <th className="text-left py-2">City</th>
                  <th className="text-right">Mean AQI</th>
                  <th className="text-right">Max AQI</th>
                  <th className="text-left">Dominant source</th>
                  <th className="text-right">Interventions</th>
                  <th className="text-right">Mean Δ</th>
                </tr>
              </thead>
              <tbody>
                {compare.map((c) => (
                  <tr key={c.code} className="border-b border-ink-600/40">
                    <td className="py-2">
                      <div className="font-medium">{c.name}</div>
                      <div className="text-xs text-slate-500">{c.code} · {c.state}</div>
                    </td>
                    <td className="text-right font-mono" style={{ color: aqiColor(c.mean_aqi) }}>
                      {formatNumber(c.mean_aqi)}
                    </td>
                    <td className="text-right font-mono text-slate-300">
                      {formatNumber(c.max_aqi)}
                    </td>
                    <td className="text-slate-300">{sourceLabel(c.dominant_source)}</td>
                    <td className="text-right text-slate-300">{c.interventions_count}</td>
                    <td className="text-right font-mono text-emerald-300">
                      {c.interventions_mean_delta != null
                        ? formatNumber(c.interventions_mean_delta, 1)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <LoadingRows rows={3} />
        )}
      </Panel>
    </div>
  );
}