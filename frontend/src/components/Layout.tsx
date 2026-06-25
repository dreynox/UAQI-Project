import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/api/queries";

const NAV = [
  { to: "/", label: "Overview" },
  { to: "/map", label: "Map" },
  { to: "/enforcement", label: "Enforcement" },
  { to: "/compare", label: "Compare" },
  { to: "/health", label: "Health" },
  { to: "/story", label: "Story" },
];

export default function Layout() {
  const location = useLocation();
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });

  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-ink-600/60 bg-ink-900/80 backdrop-blur sticky top-0 z-30">
        <div className="mx-auto max-w-[1600px] px-6 py-3 flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md bg-gradient-to-br from-accent-500 to-emerald-400 flex items-center justify-center font-bold text-ink-950">
              U
            </div>
            <div className="flex flex-col leading-none">
              <span className="font-semibold tracking-tight">UAQI</span>
              <span className="text-[10px] uppercase tracking-widest text-slate-400">
                Urban Air Quality Intelligence
              </span>
            </div>
          </div>

          <nav className="flex items-center gap-1 ml-4">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm transition-colors ${
                    isActive
                      ? "bg-ink-700 text-slate-50"
                      : "text-slate-300 hover:bg-ink-700/60 hover:text-slate-50"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.database_ok ? "bg-emerald-400 animate-pulse" : "bg-red-400"
                }`}
              />
              <span className="text-slate-400">
                {health?.status ?? "…"} · {health?.service ?? "UAQI"} v{health?.version ?? "—"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-[1600px] px-6 py-6">
        <Outlet key={location.pathname} />
      </main>

      <footer className="border-t border-ink-600/60 py-3 text-center text-xs text-slate-500">
        Built for ET-AI-2026 · Backend FastAPI + SQLAlchemy · Frontend React + Vite + Tailwind
      </footer>
    </div>
  );
}
