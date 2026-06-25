import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  fetchAttribution,
  fetchForecast,
  fetchWard,
  fetchWardEnforcement,
} from "@/api/queries";
import { Panel, Kpi, Badge, LoadingRows } from "@/components/ui";
import {
  aqiColor,
  aqiLabel,
  formatNumber,
  sourceLabel,
  SOURCE_CHART_COLORS,
  actionIcon,
  priorityTone,
  urgencyColor,
  languageLabel,
} from "@/lib/aqi";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  Legend,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { useState } from "react";

export default function WardDetailPage() {
  const { wardId: wardIdStr } = useParams<{ wardId: string }>();
  const wardId = Number(wardIdStr);
  const navigate = useNavigate();
  const [lang, setLang] = useState<string>("en");

  const { data: ward, isLoading } = useQuery({
    queryKey: ["ward", wardId],
    queryFn: () => fetchWard(wardId),
    enabled: Number.isFinite(wardId),
  });

  const { data: attribution } = useQuery({
    queryKey: ["attribution", wardId],
    queryFn: () => fetchAttribution(wardId),
    enabled: Number.isFinite(wardId),
  });

  const { data: forecast } = useQuery({
    queryKey: ["forecast", wardId],
    queryFn: () => fetchForecast(wardId),
    enabled: Number.isFinite(wardId),
  });

  const { data: enforcement } = useQuery({
    queryKey: ["enforcement", ward?.city_code, wardId],
    queryFn: () => fetchWardEnforcement(ward!.city_code!, wardId),
    enabled: !!ward?.city_code,
  });

  const advisoryQ = useQuery({
    queryKey: ["advisory", wardId, lang],
    queryFn: () => fetchAdvisory(wardId, lang),
    enabled: Number.isFinite(wardId),
  });

  if (isLoading) {
    return (
      <div className="panel">
        <LoadingRows rows={6} />
      </div>
    );
  }
  if (!ward) {
    return (
      <div className="panel">
        <div className="text-sm text-slate-400">Ward {wardId} not found.</div>
        <Link to="/" className="text-accent-400 text-sm hover:underline">
          ← Back to overview
        </Link>
      </div>
    );
  }

  const sourceBreakdownData = attribution
    ? Object.entries(attribution.source_breakdown)
        .map(([k, v]) => ({
          name: sourceLabel(k),
          key: k,
          value: Number(((v as number) * 100).toFixed(1)),
        }))
        .sort((a, b) => b.value - a.value)
    : [];

  const forecastData = forecast
    ? forecast.forecasts.map((f) => ({
        horizon: `+${f.horizon_hours}h`,
        predicted: f.predicted_aqi,
        baseline: f.baseline_aqi,
        low: f.confidence_low,
        high: f.confidence_high,
      }))
    : [];

  const seriesData = ward.aqi_series_48h?.map((s) => ({
    t: new Date(s.timestamp).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
    }),
    aqi: s.aqi,
    pm25: s.pm25,
  }));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          ← Back
        </button>
        <h1 className="text-2xl font-semibold tracking-tight">{ward.name}</h1>
        <span className="text-xs text-slate-400">
          {ward.city_name ?? ward.city_code} · {ward.ward_code}
        </span>
        <Badge
          tone={
            ward.current_aqi > 300
              ? "bad"
              : ward.current_aqi > 200
              ? "warn"
              : "info"
          }
          className="ml-2"
        >
          {aqiLabel(ward.current_aqi)}
        </Badge>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Kpi
          label="Current AQI"
          value={formatNumber(ward.current_aqi)}
          tone={ward.current_aqi > 300 ? "bad" : "warn"}
        />
        <Kpi label="Vulnerability index" value={formatNumber(ward.vulnerability_index, 1)} tone="info" />
        <Kpi label="Population" value={formatNumber(ward.population)} />
        <Kpi label="Area (km²)" value={ward.area_km2 != null ? formatNumber(ward.area_km2, 1) : "—"} />
        <Kpi
          label="Priority"
          value={
            enforcement
              ? formatNumber(enforcement.priority_score, 1)
              : "—"
          }
          hint={enforcement?.urgency}
          tone={
            enforcement?.urgency === "critical"
              ? "bad"
              : enforcement?.urgency === "high"
              ? "warn"
              : "info"
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Attribution (multi-agent fusion) */}
        <Panel
          title="Multi-agent source attribution"
          subtitle="Why is it bad?"
          className="lg:col-span-2"
        >
          {attribution ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                  Top source
                </div>
                <div
                  className="text-3xl font-bold mb-1"
                  style={{ color: SOURCE_CHART_COLORS[attribution.top_source] || "#7dd3fc" }}
                >
                  {sourceLabel(attribution.top_source)}
                </div>
                <div className="text-sm text-slate-400 mb-3">
                  Confidence:{" "}
                  <span className="font-mono text-slate-200">
                    {(attribution.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="text-xs text-slate-300 leading-relaxed">
                  {attribution.explanation}
                </div>
              </div>
              <div className="h-[200px]">
                <ResponsiveContainer>
                  <BarChart
                    data={sourceBreakdownData}
                    layout="vertical"
                    margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                    <XAxis
                      type="number"
                      tick={{ fill: "#94a3b8", fontSize: 10 }}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      width={110}
                      tick={{ fill: "#cbd5e1", fontSize: 10 }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#0f1424",
                        border: "1px solid #222a44",
                        fontSize: 11,
                      }}
                      formatter={(v: number) => [`${v}%`, "share"]}
                    />
                    <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                      {sourceBreakdownData.map((entry) => (
                        <Cell
                          key={entry.key}
                          fill={SOURCE_CHART_COLORS[entry.key] || "#7dd3fc"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="md:col-span-2 mt-2 pt-3 border-t border-ink-600/40">
                <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                  Agent evidence
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {Object.entries(attribution.agent_evidence).map(([agent, ev]) => (
                    <div key={agent} className="panel-tight text-xs">
                      <div className="font-medium capitalize text-slate-200 mb-1">
                        {agent}
                      </div>
                      <pre className="text-[10px] text-slate-400 whitespace-pre-wrap font-mono leading-snug">
                        {JSON.stringify(ev, null, 1).slice(0, 200)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-500">No attribution computed.</div>
          )}
        </Panel>

        {/* Advisory */}
        <Panel
          title="Multilingual advisory"
          subtitle="Severity × audience × language"
          actions={
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="bg-ink-900 border border-ink-600 text-xs rounded px-2 py-1"
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="kn">ಕನ್ನಡ</option>
              <option value="ta">தமிழ்</option>
            </select>
          }
        >
          {advisoryQ.data ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge tone="info">{languageLabel(advisoryQ.data.language)}</Badge>
                <Badge tone="bad">{advisoryQ.data.severity.replace("_", " ")}</Badge>
                <Badge tone="slate">{advisoryQ.data.audience.replace("_", " ")}</Badge>
              </div>
              <div className="text-sm font-semibold">{advisoryQ.data.title}</div>
              <div className="text-sm text-slate-200 leading-relaxed">
                {advisoryQ.data.body}
              </div>
              <div className="text-[11px] text-slate-500 pt-2 border-t border-ink-600/40">
                Valid: {new Date(advisoryQ.data.valid_from).toLocaleString()} →{" "}
                {new Date(advisoryQ.data.valid_until).toLocaleString()}
              </div>
            </div>
          ) : (
            <LoadingRows rows={3} />
          )}
        </Panel>
      </div>

      {/* Forecast + enforcement */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel
          title="Hyperlocal AQI forecast"
          subtitle="24 / 48 / 72h"
          className="lg:col-span-2"
        >
          {forecast && forecast.forecasts.length > 0 ? (
            <div className="h-[260px]">
              <ResponsiveContainer>
                <LineChart data={forecastData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                  <XAxis dataKey="horizon" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line
                    type="monotone"
                    dataKey="baseline"
                    stroke="#94a3b8"
                    strokeDasharray="4 4"
                    name="Persistence baseline"
                    dot
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#7dd3fc"
                    strokeWidth={2.5}
                    name="Model prediction"
                    dot
                  />
                  <Line
                    type="monotone"
                    dataKey="low"
                    stroke="#475569"
                    strokeDasharray="2 4"
                    name="Lower CI"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="high"
                    stroke="#475569"
                    strokeDasharray="2 4"
                    name="Upper CI"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-sm text-slate-500">No forecast data</div>
          )}
          {forecast && forecast.forecasts.length > 0 && (
            <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
              {forecast.forecasts.map((f) => (
                <div key={f.horizon_hours} className="panel-tight">
                  <div className="text-slate-400">+{f.horizon_hours}h</div>
                  <div
                    className="font-mono text-lg font-semibold"
                    style={{ color: aqiColor(f.predicted_aqi) }}
                  >
                    {formatNumber(f.predicted_aqi)}
                  </div>
                  <div className="text-[10px] text-emerald-300">
                    −{formatNumber(f.baseline_aqi - f.predicted_aqi)} vs baseline
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Enforcement priority" subtitle="Multi-component urgency">
          {enforcement ? (
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <div
                  className="text-3xl font-bold"
                  style={{ color: urgencyColor(enforcement.urgency) }}
                >
                  {formatNumber(enforcement.priority_score, 1)}
                </div>
                <span
                  className={`chip border ${priorityTone({
                    ward_id: enforcement.ward_id,
                    priority_score: enforcement.priority_score,
                    urgency: enforcement.urgency as "low" | "medium" | "high" | "critical",
                    components: enforcement.components,
                  })}`}
                >
                  {enforcement.urgency}
                </span>
              </div>
              <div className="space-y-1">
                {Object.entries(enforcement.components).map(([k, v]) => (
                  <div key={k} className="text-xs flex items-center justify-between">
                    <span className="text-slate-400 capitalize">
                      {k.replace("_", " ")}
                    </span>
                    <span className="font-mono text-slate-200">{formatNumber(v, 2)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <LoadingRows rows={3} />
          )}
        </Panel>
      </div>

      {/* Recommended actions */}
      {enforcement && (
        <Panel
          title="Recommended actions"
          subtitle={`Targeting ${sourceLabel(enforcement.top_source)}`}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {enforcement.recommended_actions.map((a) => {
              const est = a.estimated_aqi_delta ?? a.expected_aqi_delta;
              return (
                <div key={a.action_code} className="panel-tight">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-lg">{actionIcon(a.action_code)}</span>
                    <Badge tone={a.priority === "primary" ? "bad" : "slate"}>
                      {a.priority}
                    </Badge>
                  </div>
                  <div className="font-semibold text-sm">{a.title}</div>
                  <div className="text-xs text-slate-400 leading-snug mt-1 mb-2">
                    {a.description}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-emerald-300 font-mono text-lg">
                      {est != null ? formatNumber(est, 1) : "—"}
                    </span>
                    <span className="text-[10px] text-slate-400">Δ AQI est.</span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    ₹{a.estimated_cost_inr.toLocaleString("en-IN")} · {a.lead_time_hours}h lead
                  </div>
                  {a.estimation_method && (
                    <div className="text-[10px] text-slate-500 italic mt-1">
                      {a.estimation_method}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      {/* 48h series + vulnerability */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel
          title="48-hour AQI series"
          subtitle="Latest hourly readings"
          className="lg:col-span-2"
        >
          {seriesData && seriesData.length > 0 ? (
            <div className="h-[240px]">
              <ResponsiveContainer>
                <LineChart data={seriesData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                  <XAxis
                    dataKey="t"
                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                    interval={Math.floor(seriesData.length / 6)}
                  />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line
                    type="monotone"
                    dataKey="aqi"
                    stroke="#7dd3fc"
                    strokeWidth={2}
                    dot={false}
                    name="AQI"
                  />
                  <Line
                    type="monotone"
                    dataKey="pm25"
                    stroke="#f97316"
                    strokeWidth={1.5}
                    dot={false}
                    name="PM2.5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-sm text-slate-500">No series data</div>
          )}
        </Panel>

        <Panel title="Vulnerable population">
          {ward.vulnerable_population ? (
            <div className="space-y-2 text-sm">
              <Row label="Children under 5" v={ward.vulnerable_population.children_under_5} />
              <Row label="Elderly (65+)" v={ward.vulnerable_population.elderly_65_plus} />
              <Row label="Outdoor workers" v={ward.vulnerable_population.outdoor_workers} />
              <Row
                label="Asthma prevalence"
                v={`${ward.vulnerable_population.asthma_prev_pct}%`}
              />
              <Row label="Pregnant women" v={ward.vulnerable_population.pregnant_women} />
              <Row
                label="Vulnerability index"
                v={formatNumber(ward.vulnerable_population.vulnerability_index, 1)}
                highlight
              />
            </div>
          ) : (
            <div className="text-sm text-slate-500">No data</div>
          )}
        </Panel>
      </div>
    </div>
  );
}

function Row({
  label,
  v,
  highlight,
}: {
  label: string;
  v: string | number;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span
        className={
          highlight
            ? "font-mono text-accent-400 font-semibold"
            : "font-mono text-slate-200"
        }
      >
        {typeof v === "number" ? formatNumber(v) : v}
      </span>
    </div>
  );
}

// Re-export advisory import for the JSX above
import { fetchAdvisory } from "@/api/queries";
