import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchHealthOverlay, fetchCityOverview } from "@/api/queries";
import { Panel, LoadingRows, Badge } from "@/components/ui";
import { aqiColor, formatNumber } from "@/lib/aqi";
import type { CityCode } from "@/store/app";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ZAxis,
  Cell,
} from "recharts";

const VALID_CODES: CityCode[] = ["DEL", "BLR", "BOM"];

export default function HealthOverlayPage() {
  const { code } = useParams<{ code?: string }>();
  const selected: CityCode = (code && VALID_CODES.includes(code as CityCode)
    ? code
    : "DEL") as CityCode;

  const { data: overlay, isLoading } = useQuery({
    queryKey: ["healthOverlay", selected],
    queryFn: () => fetchHealthOverlay(selected),
  });

  const { data: overview } = useQuery({
    queryKey: ["cityOverview", selected],
    queryFn: () => fetchCityOverview(selected),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          Public Health Risk Overlay
        </h1>
        <div className="ml-auto flex items-center gap-2">
          {VALID_CODES.map((c) => (
            <Link
              key={c}
              to={`/health/${c}`}
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

      {overview && (
        <Panel
          title={`${overview.city?.name ?? selected} · vulnerability × AQI scatter`}
          subtitle="Each dot is a ward. Higher vulnerability + higher AQI = priority for protection."
        >
          {overlay ? (
            <div className="h-[340px]">
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
                  <CartesianGrid stroke="#1f2742" strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="vulnerability_index"
                    name="Vulnerability"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    label={{
                      value: "Vulnerability index",
                      position: "insideBottom",
                      offset: -4,
                      fill: "#94a3b8",
                      fontSize: 11,
                    }}
                  />
                  <YAxis
                    type="number"
                    dataKey="current_aqi"
                    name="AQI"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    label={{
                      value: "Current AQI",
                      angle: -90,
                      position: "insideLeft",
                      fill: "#94a3b8",
                      fontSize: 11,
                    }}
                  />
                  <ZAxis
                    type="number"
                    dataKey="population"
                    range={[40, 400]}
                    name="Population"
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: "3 3" }}
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid #222a44",
                      fontSize: 11,
                    }}
                    formatter={(v: number, k: string) => {
                      if (k === "population") return [formatNumber(v), "Population"];
                      if (k === "vulnerability_index")
                        return [formatNumber(v, 1), "Vulnerability"];
                      if (k === "current_aqi") return [formatNumber(v), "AQI"];
                      return [v, k];
                    }}
                    labelFormatter={(_, p: any) =>
                      p?.[0]?.payload?.ward_name ?? ""
                    }
                  />
                  <Scatter data={overlay}>
                    {overlay.map((d, i) => (
                      <Cell key={i} fill={aqiColor(d.current_aqi)} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LoadingRows rows={3} />
          )}
        </Panel>
      )}

      <Panel title="High-risk wards" subtitle="AQI > 200 AND vulnerability > 50">
        {overlay ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-400 border-b border-ink-600">
                  <th className="text-left py-2">Ward</th>
                  <th className="text-right">AQI</th>
                  <th className="text-right">Vulnerability</th>
                  <th className="text-right">Population</th>
                  <th className="text-right">Nearby institutions</th>
                  <th className="text-right">Risk score</th>
                </tr>
              </thead>
              <tbody>
                {overlay
                  .filter((w) => w.current_aqi > 200 && w.vulnerability_index > 50)
                  .sort(
                    (a, b) =>
                      b.current_aqi * (b.vulnerability_index / 50) -
                      a.current_aqi * (a.vulnerability_index / 50)
                  )
                  .slice(0, 15)
                  .map((w) => {
                    const risk = +(w.current_aqi * (w.vulnerability_index / 50)).toFixed(0);
                    return (
                      <tr key={w.ward_id} className="border-b border-ink-600/40">
                        <td className="py-2">
                          <Link
                            to={`/ward/${w.ward_id}`}
                            className="font-medium hover:text-accent-400"
                          >
                            {w.ward_name}
                          </Link>
                          <div className="text-[10px] text-slate-500">{w.ward_code}</div>
                        </td>
                        <td
                          className="text-right font-mono"
                          style={{ color: aqiColor(w.current_aqi) }}
                        >
                          {formatNumber(w.current_aqi)}
                        </td>
                        <td className="text-right font-mono text-slate-300">
                          {formatNumber(w.vulnerability_index, 1)}
                        </td>
                        <td className="text-right text-slate-300">
                          {formatNumber(w.population)}
                        </td>
                        <td className="text-right">
                          <Badge tone="info">{w.nearby_institutions}</Badge>
                        </td>
                        <td className="text-right font-mono font-semibold text-accent-400">
                          {formatNumber(risk)}
                        </td>
                      </tr>
                    );
                  })}
                {overlay.filter(
                  (w) => w.current_aqi > 200 && w.vulnerability_index > 50
                ).length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center text-slate-500 py-4 text-sm">
                      No high-risk wards match the threshold.
                    </td>
                  </tr>
                )}
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
