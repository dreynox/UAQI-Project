import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchDemoStory, fetchDemoScenario } from "@/api/queries";
import { Panel, Badge, Kpi, LoadingRows } from "@/components/ui";
import {
  aqiColor,
  formatNumber,
  sourceLabel,
  actionIcon,
  languageLabel,
} from "@/lib/aqi";
import type { CityCode } from "@/store/app";
import type { DemoScenario, DemoStory } from "@/api/types";

const VALID_CODES: CityCode[] = ["DEL", "BLR", "BOM"];

const STEP_BLURBS = [
  "Where is the pollution worst?",
  "Why is it bad here?",
  "What will it be tomorrow?",
  "What should authorities do?",
];

export default function StoryPage() {
  const { code } = useParams<{ code?: string }>();
  const selected: CityCode = (code && VALID_CODES.includes(code as CityCode)
    ? code
    : "DEL") as CityCode;
  const [activeStep, setActiveStep] = useState(0);

  const { data: story, isLoading: storyLoading } = useQuery({
    queryKey: ["demoStory", selected],
    queryFn: () => fetchDemoStory(selected),
  });

  const { data: scenario, isLoading: scenarioLoading } = useQuery({
    queryKey: ["demoScenario", selected],
    queryFn: () => fetchDemoScenario(selected),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Demo Story Mode</h1>
        <span className="text-xs text-slate-400">
          {storyLoading ? "Loading…" : story?.title}
        </span>
        <div className="ml-auto flex items-center gap-2">
          {VALID_CODES.map((c) => (
            <Link
              key={c}
              to={`/story/${c}`}
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

      {/* Hero strip */}
      {scenario && (
        <Panel>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <div className="text-xs uppercase tracking-wider text-slate-400">
                {scenario.scenario.city.name} · Worst ward
              </div>
              <div className="text-2xl font-semibold mt-1">
                {scenario.scenario.ward.name}
              </div>
              <div className="text-sm text-slate-300 mt-2 leading-relaxed">
                {scenario.scenario.headline}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Kpi
                label="AQI"
                value={formatNumber(scenario.scenario.ward.current_aqi)}
                tone="bad"
              />
              <Kpi
                label="Vulnerability"
                value={formatNumber(scenario.scenario.ward.vulnerability_index, 1)}
                tone="warn"
              />
              <Kpi
                label="Top source"
                value={
                  scenario.attribution
                    ? sourceLabel(scenario.attribution.top_source)
                    : "—"
                }
              />
              <Kpi
                label="Confidence"
                value={
                  scenario.attribution
                    ? `${(scenario.attribution.confidence * 100).toFixed(0)}%`
                    : "—"
                }
                tone="info"
              />
            </div>
          </div>
        </Panel>
      )}

      {/* Step nav */}
      <div className="grid grid-cols-4 gap-2">
        {STEP_BLURBS.map((blurb, i) => {
          const active = activeStep === i;
          return (
            <button
              key={i}
              onClick={() => setActiveStep(i)}
              className={`text-left p-3 rounded-lg border transition ${
                active
                  ? "bg-accent-500/15 border-accent-500/40"
                  : "bg-ink-800 border-ink-600/60 hover:bg-ink-700"
              }`}
            >
              <div className="text-xs uppercase tracking-wider text-slate-400">
                Step {i + 1}
              </div>
              <div
                className={`text-sm font-medium mt-1 ${
                  active ? "text-accent-400" : "text-slate-100"
                }`}
              >
                {blurb}
              </div>
            </button>
          );
        })}
      </div>

      {/* Active step content */}
      {story && scenario && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            {activeStep === 0 && <Step1Overview story={story} scenario={scenario} />}
            {activeStep === 1 && (
              <Step2Attribution story={story} scenario={scenario} />
            )}
            {activeStep === 2 && <Step3Forecast scenario={scenario} />}
            {activeStep === 3 && (
              <Step4Enforcement scenario={scenario} story={story} />
            )}
          </div>

          <div className="space-y-4">
            {/* Live advisory */}
            <Panel title="Live citizen advisory" subtitle="In ward's default language">
              {(() => {
                const lang = scenario.advisory.default_language;
                type Sample = {
                  language: string;
                  severity: string;
                  audience: string;
                  title: string;
                  body: string;
                };
                const raw =
                  scenario.advisory[
                    `sample_${lang}` as keyof typeof scenario.advisory
                  ];
                const sample: Sample | undefined =
                  raw && typeof raw === "object"
                    ? (raw as Sample)
                    : scenario.advisory.sample_en;
                if (!sample) return <div className="text-sm text-slate-500">—</div>;
                return (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-1">
                      <Badge tone="info">{languageLabel(sample.language)}</Badge>
                      <Badge tone="bad">{sample.severity.replace("_", " ")}</Badge>
                      <Badge tone="slate">
                        {sample.audience.replace("_", " ")}
                      </Badge>
                    </div>
                    <div className="font-semibold text-sm">{sample.title}</div>
                    <div className="text-xs text-slate-300 leading-relaxed">
                      {sample.body}
                    </div>
                  </div>
                );
              })()}
            </Panel>

            {/* Past interventions */}
            <Panel title="Recent interventions on this ward">
              {scenario.interventions.recent.length === 0 ? (
                <div className="text-xs text-slate-500">No past interventions.</div>
              ) : (
                <div className="space-y-2 text-xs">
                  {scenario.interventions.recent.map((r) => (
                    <div key={r.id} className="panel-tight">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">
                          {actionIcon(r.action_type)} {r.action_type.replace(/_/g, " ")}
                        </span>
                        <Badge tone={r.status === "completed" ? "good" : "warn"}>
                          {r.status}
                        </Badge>
                      </div>
                      {r.measured_aqi_delta != null && (
                        <div className="text-emerald-300 mt-1">
                          Δ AQI: {formatNumber(r.measured_aqi_delta, 1)}
                        </div>
                      )}
                      {r.notes && (
                        <div className="text-slate-500 mt-0.5 italic">{r.notes}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            {/* Next-step links */}
            <Panel title="Continue exploring">
              <div className="space-y-2 text-xs">
                <Link
                  to={`/ward/${scenario.scenario.ward.id}`}
                  className="block panel-tight hover:bg-ink-700/40"
                >
                  → Open ward detail page
                </Link>
                <Link
                  to={`/map/${selected}`}
                  className="block panel-tight hover:bg-ink-700/40"
                >
                  → See ward on the city map
                </Link>
                <Link
                  to={`/enforcement/${selected}`}
                  className="block panel-tight hover:bg-ink-700/40"
                >
                  → View full enforcement queue
                </Link>
                <Link
                  to="/compare"
                  className="block panel-tight hover:bg-ink-700/40"
                >
                  → Compare with other cities
                </Link>
              </div>
            </Panel>
          </div>
        </div>
      )}

      {(storyLoading || scenarioLoading) && (
        <Panel>
          <LoadingRows rows={6} />
        </Panel>
      )}
    </div>
  );
}

function Step1Overview({
  story,
  scenario,
}: {
  story: DemoStory;
  scenario: DemoScenario;
}) {
  const step1 = story.steps[0];
  return (
    <Panel title="Step 1 — Where is pollution worst?" subtitle={step1.title}>
      <p className="text-sm text-slate-300 leading-relaxed">{step1.description}</p>
      <div className="grid grid-cols-3 gap-2 mt-4">
        <Kpi label="Worst AQI" value={formatNumber(scenario.scenario.ward.current_aqi)} tone="bad" />
        <Kpi label="Category" value={scenario.scenario.ward.aqi_category.replace("_", " ")} />
        <Kpi
          label="Population"
          value={formatNumber(scenario.context.population as number)}
        />
      </div>
      <div className="text-[11px] text-slate-500 mt-3 font-mono">
        Endpoint: {step1.endpoint}
      </div>
    </Panel>
  );
}

function Step2Attribution({
  story,
  scenario,
}: {
  story: DemoStory;
  scenario: DemoScenario;
}) {
  const step2 = story.steps[1];
  return (
    <Panel title="Step 2 — Why is it bad here?" subtitle={step2.title}>
      <p className="text-sm text-slate-300 leading-relaxed">{step2.description}</p>
      {scenario.attribution && (
        <div className="mt-4 space-y-2">
          <div className="text-xs uppercase tracking-wider text-slate-400">
            Source breakdown
          </div>
          <div className="space-y-1">
            {Object.entries(scenario.attribution.source_breakdown)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([k, v]) => {
                const pct = ((v as number) * 100).toFixed(1);
                return (
                  <div key={k}>
                    <div className="flex items-center justify-between text-xs">
                      <span>{sourceLabel(k)}</span>
                      <span className="font-mono text-slate-300">{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-ink-700 rounded overflow-hidden">
                      <div
                        className="h-full bg-accent-500"
                        style={{
                          width: `${Math.min(100, Number(pct))}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
          <div className="text-xs text-slate-300 mt-3 leading-relaxed">
            <strong className="text-slate-200">Explanation:</strong>{" "}
            {scenario.attribution.explanation}
          </div>
        </div>
      )}
      <div className="text-[11px] text-slate-500 mt-3 font-mono">
        Endpoint: {step2.endpoint}
      </div>
    </Panel>
  );
}

function Step3Forecast({
  scenario,
}: {
  scenario: DemoScenario;
}) {
  const step3 = scenario.forecast;
  return (
    <Panel title="Step 3 — What will it be tomorrow?" subtitle="24 / 48 / 72h forecast">
      <div className="grid grid-cols-3 gap-2 mt-2">
        {step3.horizons.map((h) => (
          <div key={h.horizon_hours} className="panel-tight">
            <div className="text-xs text-slate-400">+{h.horizon_hours}h</div>
            <div
              className="text-2xl font-bold font-mono mt-1"
              style={{ color: aqiColor(h.predicted_aqi) }}
            >
              {formatNumber(h.predicted_aqi)}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              baseline {formatNumber(h.baseline_aqi)}
            </div>
            <div className="text-[11px] text-emerald-300 font-mono mt-0.5">
              −{formatNumber(h.improvement_vs_baseline)} vs persistence
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              CI: {formatNumber(h.confidence_low)}–{formatNumber(h.confidence_high)}
            </div>
          </div>
        ))}
      </div>
      <div className="text-[11px] text-slate-500 mt-3 font-mono">
        Model: {step3.model_version ?? "—"}
      </div>
    </Panel>
  );
}

function Step4Enforcement({
  scenario,
  story,
}: {
  scenario: DemoScenario;
  story: DemoStory;
}) {
  const step4 = story.steps[3];
  const enf = scenario.enforcement;
  return (
    <Panel title="Step 4 — What should authorities do?" subtitle={step4.title}>
      <p className="text-sm text-slate-300 leading-relaxed">{step4.description}</p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
        {enf.recommended_actions.map((a) => {
          const est = a.estimated_aqi_delta ?? a.expected_aqi_delta;
          return (
            <div key={a.action_code} className="panel-tight">
              <div className="flex items-center justify-between mb-1">
                <span className="text-lg">{actionIcon(a.action_code)}</span>
                <Badge tone={a.priority === "primary" ? "bad" : "slate"}>
                  {a.priority}
                </Badge>
              </div>
              <div className="text-sm font-semibold">{a.title}</div>
              <div className="text-[10px] text-slate-400 leading-snug mt-1 mb-1">
                {a.description}
              </div>
              <div className="font-mono text-emerald-300">
                {est != null ? formatNumber(est, 1) : "—"} Δ AQI
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                ₹{a.estimated_cost_inr.toLocaleString("en-IN")} · {a.lead_time_hours}h
              </div>
            </div>
          );
        })}
      </div>
      <div className="text-[11px] text-slate-500 mt-3 font-mono">
        Endpoint: {step4.endpoint}
      </div>
    </Panel>
  );
}
