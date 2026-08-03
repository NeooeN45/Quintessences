import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { HoverCard, Skeleton, AnimatedCounter, StatusBadge } from "./ui";
import { useToast } from "./ToastProvider";
import { fetchWithAuth, API_URL } from "../lib/api";
import { POLL_INTERVALS } from "../lib/constants";

// --- Constantes ---

const STATS_ENDPOINT = `${API_URL}/api/v1/knowledge/stats`;

const ACCENT_COLOR = "var(--color-accent)";
const BAR_COLORS = [
  "var(--color-accent)",
  "#3b82f6",
  "#6366f1",
  "#8b5cf6",
  "#a855f7",
  "#ec4899",
  "#f43f5e",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#14b8a6",
  "#06b6d4",
];

// --- Types ---

interface KnowledgeStats {
  /** Map type -> count, triée par count décroissant */
  byType: { type: string; count: number }[];
  totalObjects: number;
  distinctTypes: number;
  maxCount: number;
  avgPerType: number;
}

// --- Tooltip personnalisé pour le bar chart ---

/**
 * Extrait les paires type -> count depuis la réponse de l'API.
 *
 * Gère plusieurs formats possibles :
 * - { "concept": 42, "rule": 15, ... }          (flat object)
 * - { "types": { "concept": 42, ... } }          (nested under "types")
 * - { "stats": { "concept": 42, ... } }          (nested under "stats")
 * - { "counts": { "concept": 42, ... } }         (nested under "counts")
 * - { "types": [{ "type": "concept", "count": 42 }] }  (array of objects)
 */
function parseStatsResponse(data: unknown): KnowledgeStats {
  if (typeof data !== "object" || data === null) {
    throw new Error("Format de réponse inattendu : objet attendu");
  }

  const root = data as Record<string, unknown>;

  // Cas 1 : objet plat type -> count
  // Cas 2 : objet imbriqué sous "types", "stats", "counts"
  const candidateKeys = ["types", "stats", "counts"];
  let rawMap: Record<string, unknown> | null = null;
  let rawArray: unknown[] | null = null;

  for (const key of candidateKeys) {
    const val = root[key];
    if (typeof val === "object" && val !== null && !Array.isArray(val)) {
      rawMap = val as Record<string, unknown>;
      break;
    }
    if (Array.isArray(val)) {
      rawArray = val;
      break;
    }
  }

  // Si pas d'imbrication, tester si la racine elle-même est type -> count
  if (!rawMap && !rawArray) {
    const entries = Object.entries(root);
    const allNumeric = entries.every(
      ([, v]) => typeof v === "number" || typeof v === "string",
    );
    if (allNumeric && entries.length > 0) {
      rawMap = root;
    }
  }

  let byType: { type: string; count: number }[] = [];

  if (rawArray) {
    byType = rawArray
      .map((item) => {
        if (typeof item !== "object" || item === null) return null;
        const obj = item as Record<string, unknown>;
        const type = String(obj.type ?? obj.name ?? obj.key ?? obj.label ?? "");
        const count = Number(obj.count ?? obj.value ?? obj.total ?? 0);
        return { type, count };
      })
      .filter((x): x is { type: string; count: number } => x !== null && x.type !== "");
  } else if (rawMap) {
    byType = Object.entries(rawMap)
      .map(([type, val]) => ({ type, count: Number(val) }))
      .filter((x) => !isNaN(x.count));
  }

  // Cas : API retourne { total_objects: 0 } quand le graphe est vide
  if (byType.length === 0) {
    const totalFromRoot = typeof root.total_objects === "number" ? root.total_objects : 0;
    if (totalFromRoot === 0) {
      return { byType: [], totalObjects: 0, distinctTypes: 0, maxCount: 0, avgPerType: 0 };
    }
    throw new Error("Aucune donnée de type trouvée dans la réponse");
  }

  byType.sort((a, b) => b.count - a.count);

  const totalObjects = byType.reduce((sum, x) => sum + x.count, 0);
  const distinctTypes = byType.length;
  const maxCount = byType.length > 0 ? byType[0].count : 0;
  const avgPerType = distinctTypes > 0 ? totalObjects / distinctTypes : 0;

  return { byType, totalObjects, distinctTypes, maxCount, avgPerType };
}

// --- Tooltip personnalisé pour le bar chart ---

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: { type: string; count: number } }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const data = payload[0].payload;
  return (
    <div className="rounded-md border border-border-strong bg-bg-200 px-3 py-2 shadow-lg">
      <p className="font-mono text-[11px] text-fg-400">{data.type}</p>
      <p className="mt-0.5 text-sm font-semibold tabular text-fg-100">
        {data.count.toLocaleString("fr-FR")}
      </p>
    </div>
  );
}

// --- Composant principal ---

export default function KnowledgePanel() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  const fetchStats = useCallback(async () => {
    try {
      const resp = await fetchWithAuth(STATS_ENDPOINT);

      if (!resp.ok) {
        let detail = `Erreur ${resp.status}`;
        try {
          const body = await resp.json();
          detail = body.detail ?? body.title ?? detail;
        } catch {
          // corps non JSON — on garde le message par défaut
        }
        throw new Error(detail);
      }

      const data = await resp.json();
      let parsed: KnowledgeStats;
      try {
        parsed = parseStatsResponse(data);
      } catch {
        // Format inattendu — afficher "—" au lieu de crasher
        parsed = { byType: [], totalObjects: 0, distinctTypes: 0, maxCount: 0, avgPerType: 0 };
      }
      setStats(parsed);
      setError(null);
    } catch (err) {
      // fetchWithAuth lance ApiError(401) après redirection vers /login
      const msg =
        err instanceof Error
          ? `Stats connaissance : ${err.message}`
          : "Impossible de récupérer les statistiques du graphe de connaissances";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, POLL_INTERVALS.knowledge);
    return () => clearInterval(interval);
  }, [fetchStats]);

  // --- États : loading ---

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 0.05, 0.1, 0.15].map((delay) => (
            <HoverCard key={delay} className="p-5" delay={delay}>
              <Skeleton className="h-3 w-24" />
              <Skeleton className="mt-3 h-8 w-16" />
            </HoverCard>
          ))}
        </div>
        <HoverCard className="p-6" delay={0.2}>
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-4 h-64 w-full" />
        </HoverCard>
      </div>
    );
  }

  // --- États : erreur ---

  if (error) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 0.05, 0.1, 0.15].map((delay) => (
            <HoverCard key={delay} className="p-5" delay={delay}>
              <Skeleton className="h-3 w-24" />
              <Skeleton className="mt-3 h-8 w-16" />
            </HoverCard>
          ))}
        </div>
        <HoverCard className="p-6" delay={0.2}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-fg-100">
                Graphe de connaissances
              </h2>
              <p className="font-mono text-[11px] text-fg-500">
                {STATS_ENDPOINT}
              </p>
            </div>
            <StatusBadge status="unhealthy" label="Erreur" />
          </div>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 text-[13px] text-error"
          >
            {error}
          </motion.p>
          <button
            onClick={() => {
              setLoading(true);
              setError(null);
              fetchStats();
            }}
            className="mt-4 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
          >
            Réessayer
          </button>
        </HoverCard>
      </div>
    );
  }

  // --- États : données chargées ---

  if (!stats) return null;

  // État : graphe vide (total_objects = 0)
  if (stats.totalObjects === 0) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <HoverCard className="p-5" delay={0}>
            <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Total objets</span>
            <div className="mt-2 text-3xl font-semibold tabular text-fg-100">
              <AnimatedCounter value={0} />
            </div>
          </HoverCard>
          <HoverCard className="p-5" delay={0.05}>
            <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Types distincts</span>
            <div className="mt-2 text-3xl font-semibold tabular text-accent">
              <AnimatedCounter value={0} />
            </div>
          </HoverCard>
          <HoverCard className="p-5" delay={0.1}>
            <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Type dominant</span>
            <div className="mt-2 text-lg font-semibold text-fg-500">—</div>
          </HoverCard>
          <HoverCard className="p-5" delay={0.15}>
            <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Moyenne / type</span>
            <div className="mt-2 text-3xl font-semibold tabular text-fg-100">0.0</div>
          </HoverCard>
        </div>
        <HoverCard className="p-12" delay={0.2}>
          <div className="flex flex-col items-center justify-center text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full border border-border bg-bg-200">
              <svg className="h-8 w-8 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.121 4.834 7.5 4.5 5.5 4.5c-1.5 0-3 .5-3 .5v13s1.5-.5 3-.5c2 0 4.621.334 6.5 1.753m0-13C13.879 4.834 16.5 4.5 18.5 4.5c1.5 0 3 .5 3 .5v13s-1.5-.5-3-.5c-2 0-4.621.334-6.5 1.753" />
              </svg>
            </div>
            <p className="mt-4 text-[14px] font-medium text-fg-200">Graphe de connaissances vide</p>
            <p className="mt-1 max-w-md text-[13px] text-fg-400">
              Aucune connaissance n'a encore été ingérée dans le graphe.
              Utilisez l'endpoint <span className="font-mono text-fg-300">POST /api/v1/knowledge/ingest</span> pour ajouter des connaissances.
            </p>
            <button
              onClick={() => { setLoading(true); fetchStats(); }}
              className="mt-4 rounded-md border border-border bg-bg-100 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
            >
              Actualiser
            </button>
          </div>
        </HoverCard>
      </div>
    );
  }

  const chartData = stats.byType.slice(0, 12); // top 12 pour la lisibilité
  const topType = stats.byType[0];

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <HoverCard className="p-5" delay={0}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
            Total objets
          </span>
          <div className="mt-2 text-3xl font-semibold tabular text-fg-100">
            <AnimatedCounter value={stats.totalObjects} />
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.05}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
            Types distincts
          </span>
          <div className="mt-2 text-3xl font-semibold tabular text-accent">
            <AnimatedCounter value={stats.distinctTypes} />
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.1}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
            Type dominant
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-lg font-semibold text-fg-100">
              {topType?.type ?? "—"}
            </span>
            <span className="text-sm tabular text-fg-500">
              {topType?.count.toLocaleString("fr-FR") ?? 0}
            </span>
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.15}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">
            Moyenne / type
          </span>
          <div className="mt-2 text-3xl font-semibold tabular text-fg-100">
            <AnimatedCounter
              value={stats.avgPerType}
              format={(n) => n.toFixed(1)}
            />
          </div>
        </HoverCard>
      </div>

      {/* Bar chart */}
      <HoverCard className="p-6" delay={0.2}>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-medium text-fg-100">
              Distribution par type de connaissance
            </h2>
            <p className="mt-0.5 text-[11px] text-fg-500">
              {chartData.length}
              {stats.byType.length > chartData.length &&
                ` sur ${stats.byType.length}`}{" "}
              types affichés
            </p>
          </div>
          <StatusBadge status="healthy" label="Synchronisé" />
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.25 }}
          className="h-80 w-full"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
            >
              <XAxis
                type="number"
                stroke="var(--color-fg-500)"
                tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey="type"
                stroke="var(--color-fg-400)"
                tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
                tickLine={false}
                axisLine={false}
                width={120}
              />
              <Tooltip
                content={<ChartTooltip />}
                cursor={{ fill: "var(--color-bg-300)", opacity: 0.3 }}
              />
              <Bar
                dataKey="count"
                radius={[0, 4, 4, 0]}
                animationDuration={800}
                animationEasing="ease-out"
              >
                {chartData.map((entry, i) => (
                  <Cell
                    key={entry.type}
                    fill={BAR_COLORS[i % BAR_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </HoverCard>

      {/* Tableau détaillé */}
      <HoverCard className="p-6" delay={0.3}>
        <h2 className="mb-4 text-sm font-medium text-fg-100">
          Détail par type
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="pb-2 pr-4 text-xs font-medium uppercase tracking-wide text-fg-500">
                  Type
                </th>
                <th className="pb-2 pr-4 text-right text-xs font-medium uppercase tracking-wide text-fg-500">
                  Count
                </th>
                <th className="pb-2 text-right text-xs font-medium uppercase tracking-wide text-fg-500">
                  Part
                </th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {stats.byType.map((item, i) => {
                  const pct =
                    stats.totalObjects > 0
                      ? (item.count / stats.totalObjects) * 100
                      : 0;
                  return (
                    <motion.tr
                      key={item.type}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{
                        delay: i * 0.02,
                        duration: 0.3,
                        ease: [0.16, 1, 0.3, 1],
                      }}
                      className="border-b border-border-light last:border-0"
                    >
                      <td className="py-2 pr-4">
                        <div className="flex items-center gap-2">
                          <span
                            className="h-2 w-2 rounded-sm"
                            style={{
                              background: BAR_COLORS[i % BAR_COLORS.length],
                            }}
                          />
                          <span className="font-mono text-fg-200">
                            {item.type}
                          </span>
                        </div>
                      </td>
                      <td className="py-2 pr-4 text-right tabular text-fg-100">
                        {item.count.toLocaleString("fr-FR")}
                      </td>
                      <td className="py-2 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="h-1.5 w-24 overflow-hidden rounded-full bg-bg-300">
                            <motion.div
                              className="h-full rounded-full"
                              style={{
                                background: BAR_COLORS[i % BAR_COLORS.length],
                              }}
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{
                                delay: i * 0.02 + 0.2,
                                duration: 0.6,
                                ease: [0.16, 1, 0.3, 1],
                              }}
                            />
                          </div>
                          <span className="tabular text-fg-400 w-12 text-right">
                            {pct.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </HoverCard>
    </div>
  );
}
