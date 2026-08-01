import { useEffect, useState, useMemo } from "react";
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
import { getResourceTypes, getResources, type ResourceList } from "../lib/api";
import { HoverCard, Skeleton, StatusBadge } from "./ui";
import { useToast } from "./ToastProvider";

type SortField = "id" | "type" | "status" | "created_at";
type SortDir = "asc" | "desc";

export default function ResourcesPanel() {
  const { showToast } = useToast();
  const [types, setTypes] = useState<string[]>([]);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [resources, setResources] = useState<ResourceList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeCounts, setTypeCounts] = useState<Record<string, number>>({});
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    getResourceTypes()
      .then((data) => {
        setTypes(data);
        if (data.length > 0) setSelectedType(data[0]);
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : "Erreur";
        setError(msg);
        showToast(msg, "error");
        setLoading(false);
      });
  }, [showToast]);

  useEffect(() => {
    if (!selectedType) return;
    setLoading(true);
    setPage(1);
    getResources(selectedType, 1, 100)
      .then((data) => {
        setResources(data);
        setError(null);
        setTypeCounts((prev) => ({ ...prev, [selectedType]: data.total }));
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : "Erreur";
        setError(msg);
        showToast(msg, "error");
      })
      .finally(() => setLoading(false));
  }, [selectedType, showToast]);

  useEffect(() => {
    if (types.length === 0) return;
    // Sérialisation : on évite 10 requêtes parallèles qui saturent le rate limit (60/min)
    const sample = types.slice(0, 10);
    const counts: Record<string, number> = {};

    const fetchSequentially = async () => {
      for (const t of sample) {
        try {
          const r = await getResources(t, 1, 1);
          counts[t] = r.total;
          setTypeCounts({ ...counts });
        } catch {
          // Skip sur erreur (rate limit ou autre) — on garde les counts déjà obtenus
        }
        // Petit délai entre chaque requête pour éviter le burst
        await new Promise((resolve) => setTimeout(resolve, 200));
      }
    };

    void fetchSequentially();
  }, [types]);

  // Tri + filtrage côté client
  const sortedItems = useMemo(() => {
    if (!resources) return [];
    let items = [...resources.items];

    // Filtrage par recherche
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      items = items.filter((item: any) =>
        JSON.stringify(item).toLowerCase().includes(q),
      );
    }

    // Tri
    items.sort((a: any, b: any) => {
      const av = a[sortField] ?? "";
      const bv = b[sortField] ?? "";
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

    return items;
  }, [resources, sortField, sortDir, searchQuery]);

  // Pagination côté client
  const totalPages = Math.ceil(sortedItems.length / pageSize);
  const paginatedItems = sortedItems.slice(
    (page - 1) * pageSize,
    page * pageSize,
  );

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const exportCSV = () => {
    if (!sortedItems.length) return;
    const headers = ["id", "type", "status", "created_at"];
    const rows = sortedItems.map((item: any) =>
      headers.map((h) => `"${item[h] ?? ""}"`).join(","),
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gsie-resources-${selectedType}-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Export CSV téléchargé", "success");
  };

  const exportJSON = () => {
    if (!sortedItems.length) return;
    const blob = new Blob([JSON.stringify(sortedItems, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gsie-resources-${selectedType}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Export JSON téléchargé", "success");
  };

  if (error) {
    const isRateLimit = error.includes("429") || error.includes("Rate limit");
    return (
      <div className="rounded-lg border border-error/30 bg-error-bg p-6">
        <div className="flex items-start gap-3">
          <svg className="h-5 w-5 flex-shrink-0 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-[13px] font-medium text-error">{error}</p>
            <p className="mt-1 text-xs text-fg-400">
              {isRateLimit
                ? "Trop de requêtes — réessayez dans quelques secondes."
                : "L'API GSIE doit être démarrée pour accéder aux ressources."}
            </p>
            <button
              onClick={() => {
                setError(null);
                setLoading(true);
                getResourceTypes()
                  .then((data) => {
                    setTypes(data);
                    if (data.length > 0) setSelectedType(data[0]);
                  })
                  .catch((err) => {
                    const msg = err instanceof Error ? err.message : "Erreur";
                    setError(msg);
                    showToast(msg, "error");
                    setLoading(false);
                  });
              }}
              className="mt-3 inline-flex items-center gap-2 rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs font-medium text-fg-200 transition-colors hover:border-border-strong hover:text-fg-100"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  const chartData = Object.entries(typeCounts)
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const SortIcon = ({ field }: { field: SortField }) => (
    <span className="ml-1 inline-flex flex-col">
      <svg
        className={`h-2.5 w-2.5 ${sortField === field && sortDir === "asc" ? "text-accent" : "text-fg-500"}`}
        viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"
      >
        <path d="M6 2L2 7h8z" />
      </svg>
      <svg
        className={`h-2.5 w-2.5 ${sortField === field && sortDir === "desc" ? "text-accent" : "text-fg-500"}`}
        viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"
      >
        <path d="M6 10L2 5h8z" />
      </svg>
    </span>
  );

  return (
    <div className="space-y-6">
      {/* Bar chart */}
      {chartData.length > 0 && (
        <HoverCard className="p-6" delay={0}>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-fg-100">Top 10 types de ressources</h2>
              <p className="text-xs text-fg-500">Volume par type (échantillon)</p>
            </div>
            <StatusBadge status="healthy" label={`${types.length} types`} />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 30 }}>
              <XAxis dataKey="type" stroke="var(--color-fg-500)" fontSize={10} tickLine={false} axisLine={false} angle={-35} textAnchor="end" height={50} interval={0} />
              <YAxis stroke="var(--color-fg-500)" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: "var(--color-bg-200)", border: "1px solid var(--color-border)", borderRadius: "6px", fontSize: "12px" }}
                cursor={{ fill: "var(--color-bg-300)", fillOpacity: 0.3 }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} animationDuration={800}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.type === selectedType ? "var(--color-accent)" : "var(--color-bg-500)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </HoverCard>
      )}

      {/* Type filter chips */}
      {types.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {types.map((type, i) => (
            <motion.button
              key={type}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.01, duration: 0.2 }}
              onClick={() => setSelectedType(type)}
              className={`rounded-md px-3 py-1 font-mono text-[12px] transition-all ${
                selectedType === type
                  ? "bg-accent text-white"
                  : "border border-border bg-bg-100 text-fg-300 hover:border-border-strong hover:text-fg-100"
              }`}
            >
              {type}
              {typeCounts[type] !== undefined && (
                <span className={`ml-1.5 text-[10px] ${selectedType === type ? "text-white/70" : "text-fg-500"}`}>
                  {typeCounts[type]}
                </span>
              )}
            </motion.button>
          ))}
        </div>
      )}

      {/* Toolbar : search + export */}
      {resources && sortedItems.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Filtrer les ressources…"
              aria-label="Filtrer les ressources"
              className="w-full rounded-md border border-border bg-bg-100 py-1.5 pl-9 pr-3 text-[13px] text-fg-100 placeholder-fg-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          <button
            onClick={exportCSV}
            aria-label="Exporter en CSV"
            className="flex items-center gap-1.5 rounded-md border border-border bg-bg-100 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            CSV
          </button>
          <button
            onClick={exportJSON}
            aria-label="Exporter en JSON"
            className="flex items-center gap-1.5 rounded-md border border-border bg-bg-100 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            JSON
          </button>
        </div>
      )}

      {/* Table */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </motion.div>
        ) : paginatedItems.length > 0 ? (
          <motion.div
            key={`table-${selectedType}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="overflow-x-auto rounded-lg border border-border"
          >
            <table className="w-full text-[13px]">
              <thead className="border-b border-border bg-bg-100">
                <tr className="text-left text-xs uppercase tracking-wide text-fg-500">
                  <th className="cursor-pointer px-4 py-2 font-medium hover:text-fg-200" onClick={() => toggleSort("id")}>
                    ID <SortIcon field="id" />
                  </th>
                  <th className="cursor-pointer px-4 py-2 font-medium hover:text-fg-200" onClick={() => toggleSort("type")}>
                    Type <SortIcon field="type" />
                  </th>
                  <th className="cursor-pointer px-4 py-2 font-medium hover:text-fg-200" onClick={() => toggleSort("status")}>
                    Statut <SortIcon field="status" />
                  </th>
                  <th className="cursor-pointer px-4 py-2 font-medium hover:text-fg-200" onClick={() => toggleSort("created_at")}>
                    Créé le <SortIcon field="created_at" />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-light">
                {paginatedItems.map((item: any, i: number) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="hover:bg-bg-100"
                  >
                    <td className="px-4 py-2.5 font-mono text-xs text-fg-300">{item.id ?? "—"}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-fg-300">{item.type ?? selectedType}</td>
                    <td className="px-4 py-2.5 text-fg-300">{item.status ?? "—"}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-fg-400">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString("fr-FR") : "—"}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        ) : (
          !loading && (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-bg-100 p-12 text-center"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full border border-border bg-bg-200">
                <svg class="h-8 w-8 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
              </div>
              <p className="mt-4 text-[14px] font-medium text-fg-200">Aucune ressource</p>
              <p className="mt-1 text-[13px] text-fg-400">
                {searchQuery
                  ? `Aucun résultat pour « ${searchQuery} »`
                  : `Le type « ${selectedType} » ne contient aucune ressource`}
              </p>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="mt-4 rounded-md border border-border bg-bg-100 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
                >
                  Effacer le filtre
                </button>
              )}
            </motion.div>
          )
        )}
      </AnimatePresence>

      {/* Pagination controls */}
      {sortedItems.length > 0 && (
        <div className="flex items-center justify-between text-xs text-fg-400">
          <span>
            {sortedItems.length} ressource{sortedItems.length > 1 ? "s" : ""}
            {searchQuery && ` (filtré${sortedItems.length > 1 ? "s" : ""})`}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              aria-label="Page précédente"
              className="rounded-md border border-border bg-bg-100 px-2.5 py-1 text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100 disabled:opacity-30 disabled:hover:border-border"
            >
              ←
            </button>
            <span className="tabular">
              {page} / {totalPages || 1}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              aria-label="Page suivante"
              className="rounded-md border border-border bg-bg-100 px-2.5 py-1 text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100 disabled:opacity-30 disabled:hover:border-border"
            >
              →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
