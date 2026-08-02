import { useCallback, useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { HoverCard, Skeleton, AnimatedCounter } from "./ui";
import { useToast } from "./ToastProvider";
import { fetchWithAuth } from "../lib/api";
import { useDebounce } from "../lib/useDebounce";
import { POLL_INTERVALS } from "../lib/constants";

// --- Constantes ---

type Tab = "danger-feux" | "vigilance";

// Niveaux de danger : 1=faible, 2=modéré, 3=sévère, 4=très sévère
const LEVEL_MAP: Record<number, { label: string; color: string; bg: string }> = {
  1: { label: "Faible", color: "#22c55e", bg: "rgba(34,197,94,0.12)" },
  2: { label: "Modéré", color: "#eab308", bg: "rgba(234,179,8,0.12)" },
  3: { label: "Sévère", color: "#f97316", bg: "rgba(249,115,22,0.12)" },
  4: { label: "Très sévère", color: "#ef4444", bg: "rgba(239,68,68,0.12)" },
};

interface DangerDep {
  dep_code: string;
  dep_nom: string;
  niveau_j1: number;
  niveau_j2: number;
  reference_time: string;
  source?: { auteur?: string; reference?: string };
}

interface VigilanceDomain {
  domain_id: string;
  max_color_id: number;
  phenomenes: { phenomenon_id: string; color_id: number }[];
}

interface VigilanceData {
  requete_id: string;
  echeance: string;
  update_time: string;
  domaines: VigilanceDomain[];
}

// --- Helpers ---

function levelMeta(n: number) {
  return LEVEL_MAP[n] ?? LEVEL_MAP[1];
}

// Couleurs vigilance MétéoFrance (1=vert, 2=jaune, 3=orange, 4=rouge)
const VIGILANCE_COLORS: Record<number, { label: string; color: string }> = {
  1: { label: "Vert", color: "#22c55e" },
  2: { label: "Jaune", color: "#eab308" },
  3: { label: "Orange", color: "#f97316" },
  4: { label: "Rouge", color: "#ef4444" },
};

// --- Composant principal ---

export default function ClimatePanel() {
  const { showToast } = useToast();
  const [tab, setTab] = useState<Tab>("danger-feux");
  const [dangerData, setDangerData] = useState<DangerDep[]>([]);
  const [vigilanceData, setVigilanceData] = useState<VigilanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedQuery = useDebounce(searchQuery, 300);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchDanger = useCallback(async () => {
    try {
      const res = await fetchWithAuth("/api/v1/climate/danger-feux");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: unknown = await res.json();
      if (!Array.isArray(json)) throw new Error("Format inattendu");
      setDangerData(json as DangerDep[]);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      // 401 : fetchWithAuth redirige vers /login automatiquement
      if (err instanceof TypeError) {
        setError("API indisponible");
        showToast("Danger feux : API indisponible", "error");
      } else {
        const msg = err instanceof Error ? err.message : "Erreur";
        setError(msg);
        showToast(`Danger feux : ${msg}`, "error");
      }
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  const fetchVigilance = useCallback(async () => {
    try {
      const res = await fetchWithAuth("/api/v1/climate/vigilance");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: unknown = await res.json();
      if (!json || typeof json !== "object" || !("domaines" in json)) {
        setVigilanceData(null);
        throw new Error("Format inattendu");
      }
      setVigilanceData(json as VigilanceData);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      // 401 : fetchWithAuth redirige vers /login automatiquement
      if (err instanceof TypeError) {
        setError("API indisponible");
        showToast("Vigilance : API indisponible", "error");
      } else {
        const msg = err instanceof Error ? err.message : "Erreur";
        showToast(`Vigilance : ${msg}`, "error");
      }
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  const refresh = useCallback(() => {
    setLoading(true);
    if (tab === "danger-feux") void fetchDanger();
    else void fetchVigilance();
  }, [tab, fetchDanger, fetchVigilance]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto-refresh 60s
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(refresh, POLL_INTERVALS.climate);
    return () => clearInterval(interval);
  }, [autoRefresh, refresh]);

  // --- Stats danger-feux ---

  const dangerStats = useMemo(() => {
    const inAlertJ1 = dangerData.filter((d) => d.niveau_j1 > 1).length;
    const inAlertJ2 = dangerData.filter((d) => d.niveau_j2 > 1).length;
    const maxJ1 = dangerData.reduce((m, d) => Math.max(m, d.niveau_j1), 0);
    const maxJ2 = dangerData.reduce((m, d) => Math.max(m, d.niveau_j2), 0);
    const severeJ1 = dangerData.filter((d) => d.niveau_j1 >= 3).length;
    const byLevelJ1: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0 };
    for (const d of dangerData) byLevelJ1[d.niveau_j1]++;
    return { inAlertJ1, inAlertJ2, maxJ1, maxJ2, severeJ1, byLevelJ1, total: dangerData.length };
  }, [dangerData]);

  const filteredDeps = useMemo(() => {
    const sorted = [...dangerData].sort((a, b) => b.niveau_j1 - a.niveau_j1);
    if (!debouncedQuery) return sorted;
    const q = debouncedQuery.toLowerCase();
    return sorted.filter(
      (d) => d.dep_nom.toLowerCase().includes(q) || d.dep_code.includes(q),
    );
  }, [dangerData, debouncedQuery]);

  const chartData = useMemo(
    () =>
      [1, 2, 3, 4]
        .map((lvl) => ({
          level: LEVEL_MAP[lvl].label,
          count: dangerStats.byLevelJ1[lvl] ?? 0,
          color: LEVEL_MAP[lvl].color,
        }))
        .filter((d) => d.count > 0),
    [dangerStats.byLevelJ1],
  );

  // --- Stats vigilance ---

  const vigilanceStats = useMemo(() => {
    if (!vigilanceData) return null;
    const domains = vigilanceData.domaines ?? [];
    const byColor: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0 };
    for (const d of domains) {
      const c = d.max_color_id ?? 1;
      byColor[c] = (byColor[c] ?? 0) + 1;
    }
    const inAlert = domains.filter((d) => (d.max_color_id ?? 1) > 1).length;
    const maxColor = domains.reduce((m, d) => Math.max(m, d.max_color_id ?? 1), 0);
    return { byColor, inAlert, maxColor, total: domains.length };
  }, [vigilanceData]);

  // --- Rendu ---

  return (
    <div className="space-y-6">
      {/* Tabs + toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 rounded-lg border border-border bg-bg-100 p-1">
          <button
            onClick={() => setTab("danger-feux")}
            className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors ${
              tab === "danger-feux"
                ? "bg-bg-300 text-fg-100"
                : "text-fg-400 hover:text-fg-200"
            }`}
          >
            Danger feux
          </button>
          <button
            onClick={() => setTab("vigilance")}
            className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors ${
              tab === "vigilance"
                ? "bg-bg-300 text-fg-100"
                : "text-fg-400 hover:text-fg-200"
            }`}
          >
            Vigilance MétéoFrance
          </button>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdate && (
            <span className="font-mono text-[11px] text-fg-500">
              MAJ : {lastUpdate.toLocaleTimeString("fr-FR")}
            </span>
          )}
          <label className="flex items-center gap-1.5 text-[12px] text-fg-400">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="h-3.5 w-3.5 rounded accent-accent"
            />
            Auto (60s)
          </label>
          <button
            onClick={refresh}
            aria-label="Actualiser"
            className="flex items-center gap-1.5 rounded-md border border-border bg-bg-100 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
          >
            <motion.svg
              animate={loading ? { rotate: 360 } : { rotate: 0 }}
              transition={loading ? { duration: 1, repeat: Infinity, ease: "linear" } : { duration: 0 }}
              className="h-3.5 w-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </motion.svg>
            Actualiser
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {tab === "danger-feux" ? (
          <motion.div
            key="danger-feux"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-6"
          >
            {loading && dangerData.length === 0 ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  {[0, 1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-24 rounded-lg" />
                  ))}
                </div>
                <Skeleton className="h-64 rounded-lg" />
                <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
                  {[...Array(12)].map((_, i) => (
                    <Skeleton key={i} className="h-16 rounded-lg" />
                  ))}
                </div>
              </div>
            ) : error && dangerData.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
                <div className="rounded-lg border border-error/30 bg-error/10 px-6 py-8">
                  <p className="text-sm font-medium text-error">
                    Impossible de charger les données de danger feux
                  </p>
                  <p className="mt-2 font-mono text-xs text-fg-500">{error}</p>
                </div>
                <button
                  onClick={refresh}
                  className="rounded-md border border-border bg-bg-200 px-4 py-2 text-sm text-fg-200 transition-colors hover:border-border-strong hover:text-fg-100"
                >
                  Réessayer
                </button>
              </div>
            ) : (
              <>
                {/* Stat cards */}
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <HoverCard className="p-5" delay={0}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
                      Départements en alerte (J+1)
                    </span>
                    <div className="mt-2 text-3xl font-semibold tabular text-warning">
                      <AnimatedCounter value={dangerStats.inAlertJ1} />
                    </div>
                    <span className="mt-1 block text-xs text-fg-500">
                      sur {dangerStats.total} total
                    </span>
                  </HoverCard>

                  <HoverCard className="p-5" delay={0.05}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
                      Niveau maximum (J+1)
                    </span>
                    <div className="mt-2 flex items-center gap-2">
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ background: levelMeta(dangerStats.maxJ1).color }}
                      />
                      <span className="text-xl font-semibold text-fg-100">
                        {levelMeta(dangerStats.maxJ1).label}
                      </span>
                    </div>
                  </HoverCard>

                  <HoverCard className="p-5" delay={0.1}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
                      Sévères + très sévères
                    </span>
                    <div className="mt-2 text-3xl font-semibold tabular text-error">
                      <AnimatedCounter value={dangerStats.severeJ1} />
                    </div>
                  </HoverCard>

                  <HoverCard className="p-5" delay={0.15}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
                      Distribution
                    </span>
                    <div className="mt-2 h-12">
                      {chartData.length > 0 && (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={chartData} layout="vertical">
                            <XAxis type="number" hide />
                            <YAxis type="category" dataKey="level" hide />
                            <Bar dataKey="count" radius={[0, 4, 4, 0]} animationDuration={600}>
                              {chartData.map((entry, i) => (
                                <Cell key={i} fill={entry.color} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  </HoverCard>
                </div>

                {/* Search bar */}
                <div className="relative max-w-sm">
                  <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Rechercher un département…"
                    aria-label="Rechercher un département"
                    className="w-full rounded-md border border-border bg-bg-100 py-1.5 pl-9 pr-3 text-[13px] text-fg-100 placeholder-fg-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>

                {/* Departments grid */}
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                  <AnimatePresence>
                    {filteredDeps.map((dep, i) => {
                      const meta = levelMeta(dep.niveau_j1);
                      const metaJ2 = levelMeta(dep.niveau_j2);
                      return (
                        <motion.div
                          key={dep.dep_code}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          transition={{ delay: Math.min(i * 0.01, 0.3), duration: 0.25 }}
                          whileHover={{ y: -2 }}
                          className="relative overflow-hidden rounded-lg border border-border bg-bg-100 p-3 transition-colors hover:border-border-strong"
                          style={{ borderLeftColor: meta.color, borderLeftWidth: 3 }}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-[10px] text-fg-500">{dep.dep_code}</span>
                            <span
                              className="rounded px-1.5 py-0.5 text-[10px] font-medium"
                              style={{ background: meta.bg, color: meta.color }}
                            >
                              {meta.label}
                            </span>
                          </div>
                          <h3 className="mt-1 truncate text-[13px] font-medium text-fg-100">
                            {dep.dep_nom}
                          </h3>
                          <div className="mt-2 flex items-center gap-2 text-[10px] text-fg-500">
                            <span>J+1: <span style={{ color: meta.color }}>●</span></span>
                            <span>J+2: <span style={{ color: metaJ2.color }}>●</span></span>
                          </div>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>

                {/* Legend */}
                <div className="flex flex-wrap items-center gap-4 text-xs text-fg-400">
                  {[1, 2, 3, 4].map((lvl) => (
                    <span key={lvl} className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ background: LEVEL_MAP[lvl].color }} />
                      {LEVEL_MAP[lvl].label}
                      <span className="tabular text-fg-500">({dangerStats.byLevelJ1[lvl] ?? 0})</span>
                    </span>
                  ))}
                </div>

                {/* Source */}
                {dangerData[0]?.source && (
                  <p className="font-mono text-[10px] text-fg-500">
                    Source : {dangerData[0].source.auteur ?? "Météo-France"} — {dangerData[0].source.reference ?? "API Météo des forêts"}
                  </p>
                )}
              </>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="vigilance"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-6"
          >
            {loading && !vigilanceData ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  {[0, 1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-24 rounded-lg" />
                  ))}
                </div>
                <Skeleton className="h-64 rounded-lg" />
              </div>
            ) : vigilanceData && vigilanceStats ? (
              <>
                {/* Vigilance stat cards */}
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <HoverCard className="p-5" delay={0}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
                      Domaines en vigilance
                    </span>
                    <div className="mt-2 text-3xl font-semibold tabular text-warning">
                      <AnimatedCounter value={vigilanceStats.inAlert} />
                    </div>
                    <span className="mt-1 block text-xs text-fg-500">
                      sur {vigilanceStats.total} domaines
                    </span>
                  </HoverCard>

                  <HoverCard className="p-5" delay={0.05}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
                      Niveau max
                    </span>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full" style={{ background: VIGILANCE_COLORS[vigilanceStats.maxColor]?.color }} />
                      <span className="text-xl font-semibold text-fg-100">
                        {VIGILANCE_COLORS[vigilanceStats.maxColor]?.label ?? "—"}
                      </span>
                    </div>
                  </HoverCard>

                  <HoverCard className="p-5" delay={0.1}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Échéance</span>
                    <div className="mt-2 text-xl font-semibold text-fg-100">
                      {vigilanceData.echeance}
                    </div>
                  </HoverCard>

                  <HoverCard className="p-5" delay={0.15}>
                    <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Mise à jour</span>
                    <div className="mt-2 text-sm font-mono text-fg-200">
                      {new Date(vigilanceData.update_time).toLocaleString("fr-FR")}
                    </div>
                  </HoverCard>
                </div>

                {/* Distribution par couleur */}
                <HoverCard className="p-6" delay={0.2}>
                  <h2 className="mb-4 text-sm font-medium text-fg-100">Distribution par niveau de vigilance</h2>
                  <div className="space-y-3">
                    {[4, 3, 2, 1].map((color) => {
                      const count = vigilanceStats.byColor[color] ?? 0;
                      const pct = vigilanceStats.total > 0 ? (count / vigilanceStats.total) * 100 : 0;
                      const meta = VIGILANCE_COLORS[color];
                      return (
                        <div key={color} className="flex items-center gap-4">
                          <span className="flex w-20 items-center gap-2 text-xs text-fg-300">
                            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: meta.color }} />
                            {meta.label}
                          </span>
                          <div className="h-3 flex-1 overflow-hidden rounded-full bg-bg-300">
                            <motion.div
                              className="h-full rounded-full"
                              style={{ background: meta.color }}
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                            />
                          </div>
                          <span className="w-12 text-right tabular text-xs text-fg-200">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </HoverCard>

                {/* Domaines list */}
                <HoverCard className="p-0" delay={0.25}>
                  <div className="border-b border-border px-4 py-3">
                    <h2 className="text-sm font-medium text-fg-100">Domaines vigilance ({vigilanceStats.total})</h2>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {vigilanceData.domaines.map((dom, i) => {
                      const meta = VIGILANCE_COLORS[dom.max_color_id] ?? VIGILANCE_COLORS[1];
                      return (
                        <motion.div
                          key={dom.domain_id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: Math.min(i * 0.01, 0.3) }}
                          className="flex items-center gap-3 border-b border-border-light px-4 py-2.5 hover:bg-bg-100"
                        >
                          <span className="h-2.5 w-2.5 rounded-full" style={{ background: meta.color }} />
                          <span className="font-mono text-[12px] text-fg-200">{dom.domain_id}</span>
                          <span className="ml-auto text-xs text-fg-400">{meta.label}</span>
                          {dom.phenomenes.length > 0 && (
                            <span className="font-mono text-[10px] text-fg-500">
                              {dom.phenomenes.length} phénomène{dom.phenomenes.length > 1 ? "s" : ""}
                            </span>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                </HoverCard>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
                <div className="rounded-lg border border-error/30 bg-error/10 px-6 py-8">
                  <p className="text-sm font-medium text-error">Vigilance indisponible</p>
                </div>
                <button
                  onClick={refresh}
                  className="rounded-md border border-border bg-bg-200 px-4 py-2 text-sm text-fg-200 transition-colors hover:border-border-strong hover:text-fg-100"
                >
                  Réessayer
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
