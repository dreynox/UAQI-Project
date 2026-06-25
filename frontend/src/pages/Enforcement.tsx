import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchEnforcementQueue,
  fetchCompareInterventions,
  fetchCompareInterventionsForCity,
} from "@/api/queries";
import { Panel, Badge, LoadingRows } from "@/components/ui";
import {
  formatNumber,
  sourceLabel,
  urgencyColor,
  actionIcon,
  priorityTone,
} from "@/lib/aqi";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";
import type { CityCode } from "@/store/app";

const VALID_CODES: CityCode[] = ["DEL", "BLR", "BOM"];

export default function EnforcementPage() {
  const { code } = useParams<{ code?: string }>();
  const selected: CityCode = (code && VALID_CODES.includes(code as CityCode)
    ? code
    : "DEL") as CityCode;
  const [limit, setLimit] = useState(10);

  const { data: queue } = useQuery({
    queryKey: ["enforcementQueue", selected, limit],
    queryFn: () => fetchEnforcementQueue(selected, limit),
  });

  const { data: interventionsAll } = useQuery({
    queryKey: ["compareInterventions"],
    queryFn: fetchCompareInterventions,
  });

  const { data: interventionsCity } = useQuery({
    queryKey: ["compareInterventionsCity", selected],
    queryFn: () => fetchCompareInterventionsForCity(selected),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Enforcement Intelligence</h1>
        <div className="ml-auto flex items-center gap-2">
          {VALID_CODES.map((c) => (
            <Link
              key={c}
              to={`/enforcement/${c}`}
              className={`px-3 py-1.5 rounded-md text-sm border transition ${
                c === selected
                  ? "bg-accent-500/15 border-accent-500/40 text-accent-400"
                  : "bg-ink-800 border-ink-600 text-slate-300 hover:bg-ink-700"
              }`}
            >
              {c}
            </Link>
          ))}
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-ink-900 border border-ink-600 text-xs rounded px-2 py-1.5"
          >
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={20}>Top 20</option>
          </select>
        </div>
      </div>

      {/* Top priority queue */}
      <Panel
        title={`Priority queue · ${selected}`}
        subtitle="Multi-component urgency (AQI × vuln × forecast × attribution)"
      >
        {queue ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-400 border-b border-ink-600">
                  <th className="text-left py-2">Rank</th>
                  <th className="text-left py-2">Ward</th>
                  <th className="text-right">AQI</th>
                  <th className="text-left">Source</th>
                  <th className="text-right">Priority</th>
                  <th className="text-left">Top action</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((q, i) => (
                  <tr
                    key={q.ward_id}
                    className="border-b border-ink-600/40 hover:bg-ink-700/40"
                  >
                    <td className="py-2 font-mono text-slate-400">{i + 1}</td>
                    <td className="py-2">
                      <Link
                        to={`/ward/${q.ward_id}`}
                        className="font-medium hover:text-accent-400"
                      >
                        {q.ward_name}
                      </Link>
                      <div className="text-[10px] text-slate-500">{q.ward_code}</div>
                    </td>
                    <td className="text-right font-mono">{formatNumber(q.current_aqi)}</td>
                    <td className="text-slate-300">{sourceLabel(q.top_source)}</td>
                    <td className="text-right">
                      <div className="flex flex-col items-end gap-1">
                        <span
                          className="font-mono font-semibold"
                          style={{ color: urgencyColor(q.urgency) }}
                        >
                          {formatNumber(q.priority_score, 1)}
                        </span>
                        <span
                          className={`chip border ${priorityTone(q as any)} text-[10px]`}
                        >
                          {q.urgency}
                        </span>
                      </div>
                    </td>
                    <td className="text-slate-200">
                      {q.recommended_actions.length > 0 ? (
                        <span className="flex items-center gap-1 text-xs">
                          <span>{actionIcon(q.recommended_actions[0].action_code)}</span>
                          <span>{q.recommended_actions[0].title}</span>
                        </span>
                      ) : (
                        "—"
                      )}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Per-city intervention effectiveness */}
        <Panel
          title={`Past intervention effectiveness · ${selected}`}
          subtitle="Mean measured Δ AQI (most negative = best)"
        >
          {interventionsCity ? (
            <div className="h-[280px]">
              <ResponsiveContainer>
                <BarChart
                  data={interventionsCity.map((r) => ({
                    name: r.action_type.replace(/_/g, " "),
                    value: r.mean_aqi_delta,
                    median: r.median_aqi_delta,
                    count: r.count,
                  }))}
                  layout="vertical"
                  margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
                >
                  <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                    tickFormatter={(v) => `${v}`}
                  />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={140}
                    tick={{ fill: "#cbd5e1", fontSize: 10 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                    formatter={(v: number, _k, p: any) => [
                      `${v} (n=${p.payload.count})`,
                      "Δ AQI",
                    ]}
                  />
                  <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                    {interventionsCity.map((r, i) => (
                      <Cell
                        key={i}
                        fill={r.mean_aqi_delta < -20 ? "#22c55e" : r.mean_aqi_delta < -10 ? "#84cc16" : "#f97316"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LoadingRows rows={4} />
          )}
        </Panel>

        {/* All-cities table */}
        <Panel title="All-cities intervention comparison" subtitle="Cross-city benchmark">
          {interventionsAll ? (
            <div className="overflow-x-auto max-h-[280px]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-ink-800">
                  <tr className="text-xs uppercase tracking-wider text-slate-400 border-b border-ink-600">
                    <th className="text-left py-2">City</th>
                    <th className="text-left">Action</th>
                    <th className="text-right">Mean Δ</th>
                    <th className="text-right">N</th>
                  </tr>
                </thead>
                <tbody>
                  {interventionsAll.map((r, i) => (
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
                      <td className="text-slate-300">
                        {r.action_type.replace(/_/g, " ")}
                      </td>
                      <td className="text-right font-mono text-emerald-300">
                        {formatNumber(r.mean_aqi_delta, 1)}
                      </td>
                      <td className="text-right text-slate-400">{r.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <LoadingRows rows={4} />
          )}
        </Panel>
      </div>
    </div>
  );
}
