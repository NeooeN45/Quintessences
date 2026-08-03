import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchWithAuth, type HealthResponse } from "../lib/api";
import { POLL_INTERVALS } from "../lib/constants";
import { HoverCard, Skeleton, StatusBadge, AnimatedCounter } from "./ui";

function Gauge({
  label,
  value,
  max,
  unit,
  status,
}: {
  label: string;
  value: number;
  max: number;
  unit: string;
  status: "healthy" | "degraded" | "unhealthy";
}) {
  const pct = Math.min((value / max) * 100, 100);
  const color = status === "healthy" ? "var(--color-accent)" : status === "degraded" ? "var(--color-warning)" : "var(--color-error)";
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-32 w-32">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="var(--color-bg-300)"
            strokeWidth="6"
          />
          <motion.circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-semibold tabular text-fg-100">
            <AnimatedCounter value={value} />
          </span>
          <span className="text-[10px] text-fg-500">{unit}</span>
        </div>
      </div>
      <span className="mt-2 text-xs text-fg-400">{label}</span>
    </div>
  );
}

function HealthCard({
  title,
  endpoint,
  health,
  loading,
  error,
  delay = 0,
}: {
  title: string;
  endpoint: string;
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
  delay?: number;
}) {
  const deps = health?.dependencies ?? {};
  const depEntries = Object.entries(deps);
  const healthyCount = depEntries.filter(([, v]) => v.startsWith("healthy")).length;

  return (
    <HoverCard className="p-6" delay={delay}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-medium text-fg-100">{title}</h2>
          <p className="font-mono text-[11px] text-fg-500">{endpoint}</p>
        </div>
        {loading ? (
          <Skeleton className="h-5 w-20" />
        ) : error ? (
          <StatusBadge status="unhealthy" label="Erreur" />
        ) : health ? (
          <StatusBadge status={health.status as "healthy" | "degraded" | "unhealthy"} label={health.status} />
        ) : null}
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3 text-[13px] text-error"
        >
          {error}
        </motion.p>
      )}

      {health && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.1 }}
          className="mt-4 space-y-4"
        >
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
            <dt className="text-fg-400">Version</dt>
            <dd className="font-mono text-fg-200">{health.version}</dd>
            <dt className="text-fg-400">Environnement</dt>
            <dd className="font-mono text-fg-200">{health.environment}</dd>
            <dt className="text-fg-400">Timestamp</dt>
            <dd className="font-mono text-xs text-fg-300">
              {new Date(health.timestamp).toLocaleString("fr-FR")}
            </dd>
            {depEntries.length > 0 && (
              <>
                <dt className="text-fg-400">Dépendances saines</dt>
                <dd className="font-mono text-fg-200">
                  {healthyCount} / {depEntries.length}
                </dd>
              </>
            )}
          </dl>

          {depEntries.length > 0 && (
            <div className="border-t border-border pt-3">
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-fg-500">
                Dépendances
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <AnimatePresence>
                  {depEntries.map(([key, val], i) => {
                    const isHealthy = val.startsWith("healthy");
                    return (
                      <motion.div
                        key={key}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.05 }}
                        className={`flex items-center gap-2 rounded-md border px-3 py-2 ${
                          isHealthy
                            ? "border-accent/20 bg-accent/5"
                            : "border-error/20 bg-error/5"
                        }`}
                      >
                        <span className={`h-2 w-2 rounded-full ${isHealthy ? "bg-accent" : "bg-error"}`}>
                          {isHealthy && (
                            <motion.span
                              className="block h-full w-full rounded-full bg-accent"
                              animate={{ opacity: [1, 0.3, 1] }}
                              transition={{ duration: 2, repeat: Infinity }}
                            />
                          )}
                        </span>
                        <span className="text-[12px] font-mono text-fg-300">{key}</span>
                        <span className={`ml-auto text-[11px] font-mono ${isHealthy ? "text-accent" : "text-error"}`}>
                          {val.split(" ")[0]}
                        </span>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </HoverCard>
  );
}

export default function HealthPanel() {
  const [liveness, setLiveness] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<HealthResponse | null>(null);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [readyError, setReadyError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [latency, setLatency] = useState(0);

  useEffect(() => {
    const pollHealth = async () => {
      const start = performance.now();
      const results = await Promise.allSettled([
        fetchWithAuth("/health")
          .then(async (r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return (await r.json()) as HealthResponse;
          })
          .then((d) => { setLiveness(d); setLiveError(null); }),
        fetchWithAuth("/ready")
          .then(async (r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return (await r.json()) as HealthResponse;
          })
          .then((d) => { setReadiness(d); setReadyError(null); }),
      ]);
      setLatency(performance.now() - start);
      if (results[0].status === "rejected") {
        setLiveError(results[0].reason instanceof Error ? results[0].reason.message : "API indisponible");
      }
      if (results[1].status === "rejected") {
        setReadyError(results[1].reason instanceof Error ? results[1].reason.message : "API indisponible");
      }
      setLoading(false);
    };
    pollHealth();
    const interval = setInterval(pollHealth, POLL_INTERVALS.healthPanel);
    return () => clearInterval(interval);
  }, []);

  const deps = readiness?.dependencies ?? {};
  const depCount = Object.keys(deps).length;
  const healthyDeps = Object.values(deps).filter((v) => v.startsWith("healthy")).length;
  const healthPct = depCount > 0 ? (healthyDeps / depCount) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Gauges */}
      <div className="grid gap-4 sm:grid-cols-3">
        <HoverCard className="flex flex-col items-center p-6" delay={0}>
          <Gauge
            label="Latence API"
            value={Math.round(latency)}
            max={500}
            unit="ms"
            status={latency < 100 ? "healthy" : latency < 300 ? "degraded" : "unhealthy"}
          />
        </HoverCard>
        <HoverCard className="flex flex-col items-center p-6" delay={0.05}>
          <Gauge
            label="Dépendances saines"
            value={healthyDeps}
            max={depCount || 1}
            unit={`/ ${depCount}`}
            status={healthyDeps === depCount ? "healthy" : healthyDeps > 0 ? "degraded" : "unhealthy"}
          />
        </HoverCard>
        <HoverCard className="flex flex-col items-center p-6" delay={0.1}>
          <Gauge
            label="Score santé"
            value={Math.round(healthPct)}
            max={100}
            unit="%"
            status={healthPct === 100 ? "healthy" : healthPct > 50 ? "degraded" : "unhealthy"}
          />
        </HoverCard>
      </div>

      {/* Liveness + Readiness cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <HealthCard
          title="Liveness"
          endpoint="GET /health"
          health={liveness}
          loading={loading && !liveness}
          error={liveError}
          delay={0.15}
        />
        <HealthCard
          title="Readiness"
          endpoint="GET /ready"
          health={readiness}
          loading={loading && !readiness}
          error={readyError}
          delay={0.2}
        />
      </div>

      {liveError && readyError && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-error/30 bg-error-bg p-4"
        >
          <p className="text-[13px] text-error">
            L'API GSIE est indisponible. Vérifiez que l'API tourne sur
            <span className="font-mono"> localhost:8000</span> et que Docker
            (PostgreSQL + Redis) est démarré.
          </p>
        </motion.div>
      )}
    </div>
  );
}
