import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchCompareCities,
  fetchCompareInterventions,
} from "@/api/queries";
import { Panel, Kpi, Badge, LoadingRows } from "@/components/ui";
import { aqiColor, formatNumber, sourceLabel, SOURCE_CHART_COLORS } from "@/lib/aqi";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Cell,
} from "recharts";

const METRICS = [
  { id: "aqi", label: "Mean AQI" },
  { id: "vulnerability", label: "Vulnerability" },
  { id: "interventions", label: "Intervention impact" },
];

export default function ComparePage() {
  const [metric, setMetric] = useState("aqi");

  const { data: cities } = useQuery({
    queryKey: ["compareCities", metric],
    queryFn: () => fetchCompareCities(metric),
  });

  const { data: interventions } = useQuery({
    queryKey: ["compareInterventions"],
    queryFn: fetchCompareInterventions,
  });

  // Aggregate source counts across cities for radar/bar
  const citySourcesData = cities
    ? cities.map((c) => ({
        name: c.name,
        code: c.code,
        ...Object.fromEntries(
          Object.entries(c.source_share ?? {}).map(([k, v]) => [k, +(v * 100).toFixed(1)])
        ),
      }))
    : [];

  // Top sources by mean share (averaged across cities)
  const sourceAverages: Array<{ source: string; avg: number }> = cities
    ? (() => {
        const sums: Record<string, number> = {};
        cities.forEach((c) => {
          Object.entries(c.source_share ?? {}).forEach(([k, v]) => {
            sums[k] = (sums[k] || 0) + v * 100;
          });
        });
        return Object.entries(sums)
          .map(([source, total]) => ({
            source,
            avg: +(total / cities.length).toFixed(1),
          }))
          .sort((a, b) => b.avg - a.avg);
      })()
    : [];

  // Top city KPIs
  const top = cities?.[0];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Multi-City Comparative Dashboard</h1>
        <div className="ml-auto flex items-center gap-2">
          {METRICS.map((m) => (
            <button
              key={m.id}
              onClick={() => setMetric(m.id)}
              className={`px-3 py-1.5 rounded-md text-sm border transition ${
                m.id === metric
                  ? "bg-accent-500/15 border-accent-500/40 text-accent-400"
                  : "bg-ink-800 border-ink-600 text-slate-300 hover:bg-ink-700"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {top && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Kpi
            label="Worst city (by mean AQI)"
            value={top.name}
            hint={`${top.code} · ${formatNumber(top.mean_aqi)} AQI`}
            tone="bad"
          />
          <Kpi label="Worst ward" value={top.worst_ward ?? "—"} hint={formatNumber(top.worst_ward_aqi)} />
          <Kpi label="Dominant source" value={sourceLabel(top.dominant_source)} tone="info" />
          <Kpi
            label="Total interventions logged"
            value={cities?.reduce((s, c) => s + c.interventions_count, 0) ?? "—"}
            hint="across 3 cities"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel
          title="Mean AQI by city"
          subtitle="Sorted by selected metric"
        >
          {cities ? (
            <div className="h-[280px]">
              <ResponsiveContainer>
                <BarChart
                  data={cities.map((c) => ({
                    name: c.code,
                    mean: c.mean_aqi,
                    max: c.max_aqi,
                    vuln: c.mean_vulnerability,
                  }))}
                  margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
                >
                  <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fill: "#cbd5e1", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="mean" fill="#7dd3fc" name="Mean AQI" radius={[3, 3, 0, 0]}>
                    {cities.map((c, i) => (
                      <Cell key={i} fill={aqiColor(c.mean_aqi)} />
                    ))}
                  </Bar>
                  <Bar dataKey="max" fill="#ef4444" name="Max AQI" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LoadingRows rows={3} />
          )}
        </Panel>

        <Panel
          title="Source attribution share by city"
          subtitle="Mean share across wards (%)"
        >
          {citySourcesData.length > 0 ? (
            <div className="h-[280px]">
              <ResponsiveContainer>
                <BarChart
                  data={citySourcesData}
                  margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
                >
                  <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                  <XAxis dataKey="code" tick={{ fill: "#cbd5e1", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {[
                    "stubble_burning",
                    "biomass_burning",
                    "construction",
                    "traffic",
                    "industrial",
                    "waste_burning",
                    "urban_form",
                    "mixed",
                  ].map((src) => (
                    <Bar
                      key={src}
                      dataKey={src}
                      stackId="a"
                      fill={SOURCE_CHART_COLORS[src]}
                      name={sourceLabel(src)}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LoadingRows rows={3} />
          )}
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Source share ranking (avg across cities)">
          {sourceAverages.length > 0 ? (
            <div className="space-y-2">
              {sourceAverages.slice(0, 8).map((s) => (
                <div key={s.source}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="flex items-center gap-2">
                      <span
                        className="inline-block w-3 h-3 rounded"
                        style={{ background: SOURCE_CHART_COLORS[s.source] }}
                      />
                      {sourceLabel(s.source)}
                    </span>
                    <span className="font-mono text-slate-300">{s.avg}%</span>
                  </div>
                  <div className="h-2 bg-ink-700 rounded overflow-hidden">
                    <div
                      className="h-full transition-all"
                      style={{
                        width: `${Math.min(100, s.avg)}%`,
                        background: SOURCE_CHART_COLORS[s.source],
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <LoadingRows rows={5} />
          )}
        </Panel>

        <Panel title="City vulnerability vs AQI" subtitle="Multi-axis comparison">
          {cities ? (
            <div className="h-[260px]">
              <ResponsiveContainer>
                <RadarChart
                  data={cities.map((c) => ({
                    city: c.code,
                    aqi: c.mean_aqi,
                    vuln: c.mean_vulnerability,
                    worst: c.worst_ward_aqi ?? 0,
                  }))}
                >
                  <PolarGrid stroke="#1f2742" />
                  <PolarAngleAxis dataKey="city" tick={{ fill: "#cbd5e1", fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Radar
                    name="Mean AQI"
                    dataKey="aqi"
                    stroke="#7dd3fc"
                    fill="#7dd3fc"
                    fillOpacity={0.3}
                  />
                  <Radar
                    name="Vulnerability"
                    dataKey="vuln"
                    stroke="#f97316"
                    fill="#f97316"
                    fillOpacity={0.2}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LoadingRows rows={3} />
          )}
        </Panel>
      </div>

      <Panel title="Intervention impact benchmark" subtitle="Cross-city, all action types">
        {interventions ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-400 border-b border-ink-600">
                  <th className="text-left py-2">City</th>
                  <th className="text-left">Action</th>
                  <th className="text-right">Mean Δ</th>
                  <th className="text-right">Median Δ</th>
                  <th className="text-right">N</th>
                  <th className="text-right">Best</th>
                </tr>
              </thead>
              <tbody>
                {interventions.map((r, i) => (
                  <tr key={i} className="border-b border-ink-600/40">
                    <td className="py-2">
                      <Badge
                        tone={
                          r.city_code === "DEL"
                            ? "orange"
                            : r.city_code === "BLR"
                            ? "purple"
                            : "info"
                        }
                      >
                        {r.city_code}
                      </Badge>
                    </td>
                    <td className="text-slate-200">{r.action_type.replace(/_/g, " ")}</td>
                    <td className="text-right font-mono text-emerald-300">
                      {formatNumber(r.mean_aqi_delta, 1)}
                    </td>
                    <td className="text-right font-mono text-slate-300">
                      {formatNumber(r.median_aqi_delta, 1)}
                    </td>
                    <td className="text-right text-slate-400">{r.count}</td>
                    <td className="text-right font-mono text-emerald-400">
                      {formatNumber(r.best_delta, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <LoadingRows rows={5} />
        )}
      </Panel>
    </div>
  );
}
