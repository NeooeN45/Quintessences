import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getEngineStatus, type EngineStatusResponse } from "../lib/api";
import { HoverCard, Skeleton, StatusBadge, AnimatedCounter } from "./ui";

const ENGINES = [
  "evidence",
  "knowledge",
  "correlation",
  "reasoning",
  "diagnostic",
  "recommendation",
  "validation",
  "gis",
  "climate",
  "pedology",
  "botanical",
  "forest_dynamics",
  "learning",
  "simulation",
];

const ENGINE_DESCRIPTIONS: Record<string, string> = {
  evidence: "Collecte et validation des preuves",
  knowledge: "Base de connaissances structurée",
  correlation: "Détection de corrélations",
  reasoning: "Chaînage et inférence",
  diagnostic: "Diagnostic forestier",
  recommendation: "Recommandations sylvicoles",
  validation: "Validation des recommandations",
  gis: "Moteur géospatial (PostGIS, IGN)",
  climate: "Données climatiques (AROME, MétéoFrance)",
  pedology: "Sols et pédologie (SoilGrids)",
  botanical: "Botanique (GBIF, Taxref)",
  forest_dynamics: "Dynamique forestière",
  learning: "Apprentissage et amélioration",
  simulation: "Simulations et scénarios",
};

export default function EnginesPanel() {
  const [statuses, setStatuses] = useState<Record<string, EngineStatusResponse | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [loading, setLoading] = useState(true);
  const [hoveredEngine, setHoveredEngine] = useState<string | null>(null);

  useEffect(() => {
    Promise.allSettled(
      ENGINES.map((engine) => getEngineStatus(engine)),
    ).then((results) => {
      const newStatuses: Record<string, EngineStatusResponse | null> = {};
      const newErrors: Record<string, string | null> = {};
      results.forEach((r, i) => {
        const engine = ENGINES[i];
        if (r.status === "fulfilled") {
          newStatuses[engine] = r.value;
          newErrors[engine] = null;
        } else {
          newStatuses[engine] = null;
          newErrors[engine] = r.reason instanceof Error ? r.reason.message : "N/A";
        }
      });
      setStatuses(newStatuses);
      setErrors(newErrors);
      setLoading(false);
    });
  }, []);

  const stats = {
    healthy: ENGINES.filter((e) => {
      const s = statuses[e]?.status;
      return s === "healthy" || s === "ok";
    }).length,
    degraded: ENGINES.filter((e) => statuses[e]?.status === "degraded").length,
    down: ENGINES.filter((e) => !statuses[e] || (statuses[e]?.status !== "healthy" && statuses[e]?.status !== "ok" && statuses[e]?.status !== "degraded")).length,
  };

  const donutData = [
    { name: "Healthy", value: stats.healthy, color: "var(--color-accent)" },
    { name: "Degraded", value: stats.degraded, color: "var(--color-warning)" },
    { name: "Down", value: stats.down, color: "var(--color-error)" },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-6">
      {/* Stats + donut */}
      <div className="grid gap-4 lg:grid-cols-4">
        <HoverCard className="p-5" delay={0}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Total moteurs</span>
          <div className="mt-2 text-3xl font-semibold tabular text-fg-100">
            <AnimatedCounter value={ENGINES.length} />
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.05}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Opérationnels</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tabular text-accent">
              <AnimatedCounter value={stats.healthy} />
            </span>
            <span className="text-sm text-fg-500">/ {ENGINES.length}</span>
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.1}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Dégradés</span>
          <div className="mt-2 text-3xl font-semibold tabular text-warning">
            <AnimatedCounter value={stats.degraded} />
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.15}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Distribution</span>
          </div>
          <div className="mt-2 flex items-center gap-3">
            <ResponsiveContainer width={60} height={60}>
              <PieChart>
                <Pie data={donutData} cx="50%" cy="50%" innerRadius={18} outerRadius={28} paddingAngle={2} dataKey="value" animationDuration={600}>
                  {donutData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-0.5">
              {donutData.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5 text-[11px]">
                  <span className="h-2 w-2 rounded-sm" style={{ background: d.color }} />
                  <span className="tabular text-fg-300">{d.value} {d.name.toLowerCase()}</span>
                </div>
              ))}
            </div>
          </div>
        </HoverCard>
      </div>

      {/* Engine grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <AnimatePresence>
          {ENGINES.map((engine, i) => {
            const status = statuses[engine];
            const error = errors[engine];
            const isHealthy = status?.status === "healthy" || status?.status === "ok";
            const isDegraded = status?.status === "degraded";
            const stat: "healthy" | "degraded" | "unhealthy" | "unknown" = loading
              ? "unknown"
              : isHealthy ? "healthy" : isDegraded ? "degraded" : "unhealthy";

            return (
              <motion.div
                key={engine}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.03, duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                onHoverStart={() => setHoveredEngine(engine)}
                onHoverEnd={() => setHoveredEngine(null)}
                className={`group relative cursor-pointer rounded-lg border p-4 transition-colors ${
                  isHealthy
                    ? "border-border bg-bg-100 hover:border-accent/40"
                    : isDegraded
                    ? "border-warning/20 bg-warning/5 hover:border-warning/40"
                    : "border-error/20 bg-error/5 hover:border-error/40"
                }`}
              >
                {/* Status indicator bar */}
                <motion.div
                  className={`absolute left-0 top-0 h-full w-0.5 rounded-l-lg ${
                    isHealthy ? "bg-accent" : isDegraded ? "bg-warning" : "bg-error"
                  }`}
                  initial={{ scaleY: 0 }}
                  animate={{ scaleY: 1 }}
                  transition={{ delay: i * 0.03 + 0.2, duration: 0.4 }}
                  style={{ originY: 0 }}
                />

                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-mono text-[13px] font-medium text-fg-100">{engine}</h3>
                    <p className="mt-0.5 text-[11px] text-fg-500">
                      {ENGINE_DESCRIPTIONS[engine] ?? "Moteur GSIE"}
                    </p>
                  </div>
                  {loading ? (
                    <Skeleton className="h-5 w-16" />
                  ) : (
                    <StatusBadge status={stat} label={status?.status ?? "N/A"} />
                  )}
                </div>

                {/* Hover details */}
                <AnimatePresence>
                  {hoveredEngine === engine && status && !loading && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-3 overflow-hidden border-t border-border pt-3"
                    >
                      <dl className="space-y-1 text-[11px]">
                        {status.version && (
                          <div className="flex justify-between">
                            <dt className="text-fg-500">Version</dt>
                            <dd className="font-mono text-fg-300">{status.version}</dd>
                          </div>
                        )}
                        {status.message && (
                          <div className="flex justify-between">
                            <dt className="text-fg-500">Message</dt>
                            <dd className="font-mono text-fg-300 truncate max-w-[140px]">{status.message}</dd>
                          </div>
                        )}
                        {status.planned_week !== undefined && (
                          <div className="flex justify-between">
                            <dt className="text-fg-500">Semaine</dt>
                            <dd className="font-mono text-fg-300">S{status.planned_week}</dd>
                          </div>
                        )}
                        {status.language && (
                          <div className="flex justify-between">
                            <dt className="text-fg-500">Langage</dt>
                            <dd className="font-mono text-fg-300">{status.language}</dd>
                          </div>
                        )}
                      </dl>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
