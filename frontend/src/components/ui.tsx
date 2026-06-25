import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  actions,
  children,
  className = "",
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <header className="flex items-start justify-between gap-4 mb-3">
          <div>
            {title && (
              <h3 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
                {title}
              </h3>
            )}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function Kpi({
  label,
  value,
  hint,
  tone,
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "default" | "good" | "warn" | "bad" | "info";
  icon?: ReactNode;
}) {
  const toneClass = {
    default: "text-slate-50",
    good: "text-emerald-300",
    warn: "text-amber-300",
    bad: "text-red-300",
    info: "text-accent-400",
  }[tone || "default"];
  return (
    <div className="panel-tight">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-slate-400">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`stat-num mt-1 ${toneClass}`}>{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  );
}

export function Badge({
  children,
  tone = "slate",
  className = "",
}: {
  children: ReactNode;
  tone?: "slate" | "good" | "warn" | "bad" | "info" | "purple" | "orange";
  className?: string;
}) {
  const tones = {
    slate: "bg-slate-500/15 text-slate-200 border-slate-500/30",
    good: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    warn: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    bad: "bg-red-500/15 text-red-300 border-red-500/30",
    info: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    purple: "bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30",
    orange: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  };
  return (
    <span className={`chip border ${tones[tone]} ${className}`}>{children}</span>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-sm text-slate-500 italic flex items-center justify-center py-8">
      {message}
    </div>
  );
}

export function LoadingRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 rounded bg-ink-700/60 animate-pulse" />
      ))}
    </div>
  );
}

export function AqiBar({ aqi, max = 500 }: { aqi: number; max?: number }) {
  const pct = Math.min(100, Math.max(0, (aqi / max) * 100));
  return (
    <div className="w-full h-1.5 rounded bg-ink-700 overflow-hidden">
      <div
        className="h-full transition-all"
        style={{ width: `${pct}%`, background: "currentColor" }}
      />
    </div>
  );
}
