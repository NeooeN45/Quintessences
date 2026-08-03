import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import { getHealth, getReady, fetchWithAuth, type HealthResponse } from "../lib/api";
import { ENGINES, POLL_INTERVALS } from "../lib/constants";
import { AnimatedCounter, HoverCard, Skeleton, Sparkline, StatusBadge } from "./ui";

interface HealthPoint {
  t: number;
  latency: number;
  status: number; // 0=down, 1=degraded, 2=healthy
}

export default function OverviewPanel() {
  const [liveness, setLiveness] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<HealthPoint[]>([]);
  const [engineStats, setEngineStats] = useState<{ healthy: number; degraded: number; down: number }>({
    healthy: 0, degraded: 0, down: 0,
  });

  const fetchHealth = useCallback(async () => {
    const start = performance.now();
    try {
      const [live, ready] = await Promise.all([
        getHealth().catch(() => null),
        getReady().catch(() => null),
      ]);
      const latency = performance.now() - start;
      const status = ready?.status === "healthy" ? 2 : ready?.status === "degraded" ? 1 : 0;
      setLiveness(live);
      setReadiness(ready);
      setHistory((h) => [...h.slice(-29), { t: Date.now(), latency, status }]);
      setLoading(false);
    } catch {
      setHistory((h) => [...h.slice(-29), { t: Date.now(), latency: 0, status: 0 }]);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, POLL_INTERVALS.health);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  // Poll engine statuses (one-shot on mount)
  useEffect(() => {
    let cancelled = false;
    let healthy = 0, degraded = 0, down = 0;
    Promise.allSettled(
      ENGINES.map(async (e) => {
        try {
          const resp = await fetchWithAuth(`/api/v1/${e}/status`);
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          return await resp.json();
        } catch {
          return null;
        }
      }),
    ).then((results) => {
      if (cancelled) return;
      results.forEach((r) => {
        if (r.status === "fulfilled" && r.value) {
          const s = r.value?.status;
          if (s === "healthy" || s === "ok" || s === "active") healthy++;
          else if (s === "degraded") degraded++;
          else down++;
        } else {
          down++;
        }
      });
      setEngineStats({ healthy, degraded, down });
    });
    return () => { cancelled = true; };
  }, []);

  const donutData = [
    { name: "Healthy", value: engineStats.healthy, color: "var(--color-accent)" },
    { name: "Degraded", value: engineStats.degraded, color: "var(--color-warning)" },
    { name: "Down", value: engineStats.down, color: "var(--color-error)" },
  ].filter((d) => d.value > 0);

  const latencyData = history.map((h) => ({
    time: new Date(h.t).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    latency: Math.round(h.latency),
  }));

  const isApiUp = liveness?.status === "healthy";
  const deps = readiness?.dependencies ?? {};
  const depCount = Object.keys(deps).length;
  const healthyDeps = Object.values(deps).filter((v) => v.startsWith("healthy")).length;

  return (
    <div className="space-y-8">
      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Statut API"
          value={isApiUp ? "Opérationnel" : "Indisponible"}
          status={isApiUp ? "healthy" : "unhealthy"}
          delay={0}
          loading={loading}
        />
        <StatCard
          label="Latence"
          value={history.length > 0 ? `${Math.round(history[history.length - 1].latency)}ms` : "—"}
          sparklineData={history.map((h) => h.latency)}
          delay={0.05}
          loading={loading}
        />
        <StatCard
          label="Dépendances"
          value={`${healthyDeps}/${depCount}`}
          counterValue={healthyDeps}
          status={healthyDeps === depCount ? "healthy" : "degraded"}
          delay={0.1}
          loading={loading}
        />
        <StatCard
          label="Moteurs actifs"
          value={`${engineStats.healthy}/${ENGINES.length}`}
          counterValue={engineStats.healthy}
          status={engineStats.healthy === ENGINES.length ? "healthy" : engineStats.healthy > 0 ? "degraded" : "unhealthy"}
          delay={0.15}
          loading={loading}
        />
      </div>

      {/* Charts grid */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Latency area chart */}
        <HoverCard className="col-span-2 p-6" delay={0.2}>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-fg-100">Latence API</h2>
              <p className="text-xs text-fg-500">30 derniers échantillons (5s intervalle)</p>
            </div>
            <StatusBadge
              status={history.length > 0 && history[history.length - 1].latency < 200 ? "healthy" : "degraded"}
              label={history.length > 0 ? `${Math.round(history[history.length - 1].latency)}ms` : "—"}
            />
          </div>
          {latencyData.length > 1 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={latencyData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="var(--color-fg-500)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="var(--color-fg-500)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `${v}ms`}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-bg-200)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "var(--color-fg-400)" }}
                />
                <Area
                  type="monotone"
                  dataKey="latency"
                  stroke="var(--color-accent)"
                  strokeWidth={2}
                  fill="url(#latencyGrad)"
                  animationDuration={300}
                  isAnimationActive={true}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <Skeleton className="h-[200px] w-full" />
          )}
        </HoverCard>

        {/* Engine donut */}
        <HoverCard className="p-6" delay={0.25}>
          <div className="mb-4">
            <h2 className="text-sm font-medium text-fg-100">Moteurs</h2>
            <p className="text-xs text-fg-500">Répartition par statut</p>
          </div>
          {donutData.length > 0 ? (
            <div className="relative">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={donutData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    animationDuration={600}
                  >
                    {donutData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-bg-200)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "6px",
                      fontSize: "12px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-semibold tabular text-fg-100">
                  <AnimatedCounter value={engineStats.healthy} />
                </span>
                <span className="text-xs text-fg-500">/ {ENGINES.length}</span>
              </div>
            </div>
          ) : (
            <Skeleton className="h-[200px] w-full rounded-full mx-auto" />
          )}
          <div className="mt-4 space-y-1.5">
            {donutData.map((d) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-fg-300">
                  <span className="h-2 w-2 rounded-sm" style={{ background: d.color }} />
                  {d.name}
                </span>
                <span className="tabular text-fg-200">{d.value}</span>
              </div>
            ))}
          </div>
        </HoverCard>
      </div>

      {/* Dependencies bar chart */}
      {depCount > 0 && (
        <HoverCard className="p-6" delay={0.3}>
          <div className="mb-4">
            <h2 className="text-sm font-medium text-fg-100">Dépendances système</h2>
            <p className="text-xs text-fg-500">État temps réel</p>
          </div>
          <div className="space-y-3">
            <AnimatePresence>
              {Object.entries(deps).map(([key, val], i) => {
                const isHealthy = val.startsWith("healthy");
                return (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-4"
                  >
                    <span className="w-24 text-xs font-mono text-fg-300">{key}</span>
                    <div className="flex-1 h-2 rounded-full bg-bg-300 overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${isHealthy ? "bg-accent" : "bg-error"}`}
                        initial={{ width: 0 }}
                        animate={{ width: "100%" }}
                        transition={{ duration: 0.8, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
                      />
                    </div>
                    <span className={`text-xs font-mono ${isHealthy ? "text-accent" : "text-error"}`}>
                      {val.split(" ")[0]}
                    </span>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </HoverCard>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  counterValue,
  status,
  sparklineData,
  delay = 0,
  loading = false,
}: {
  label: string;
  value: string;
  counterValue?: number;
  status?: "healthy" | "degraded" | "unhealthy";
  sparklineData?: number[];
  delay?: number;
  loading?: boolean;
}) {
  return (
    <HoverCard className="p-5" delay={delay}>
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-fg-500">{label}</span>
        {status && <StatusBadge status={status} />}
      </div>
      <div className="mt-3 flex items-end justify-between">
        {loading ? (
          <Skeleton className="h-7 w-20" />
        ) : (
          <span className="text-2xl font-semibold tabular text-fg-100">
            {counterValue !== undefined ? <AnimatedCounter value={counterValue} /> : value}
          </span>
        )}
        {sparklineData && sparklineData.length > 1 && (
          <Sparkline data={sparklineData} />
        )}
      </div>
    </HoverCard>
  );
}


