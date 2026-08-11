import { useCallback, useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getDataCatalog, type DataCatalogResponse, type DatasetSummary } from "../lib/api";
import { useDebounce } from "../lib/useDebounce";
import { HoverCard, Skeleton, StatusBadge } from "./ui";
import { useToast } from "./ToastProvider";

function purposeLabel(purpose: DatasetSummary["purpose"]): string {
  return {
    production: "Production",
    training: "Entraînement",
    evaluation: "Évaluation",
    reference: "Référence",
  }[purpose];
}

export default function DataCatalogPanel() {
  const { showToast } = useToast();
  const [catalog, setCatalog] = useState<DataCatalogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState<string>("");
  const debouncedSearch = useDebounce(search, 250);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDataCatalog();
      setCatalog(data);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "API Data Registry indisponible";
      setError(message);
      showToast(`Catalogue datasets : ${message}`, "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const domains = useMemo(() => {
    const values = new Set<string>();
    for (const item of catalog?.items ?? []) {
      if (item.primary_domain) values.add(item.primary_domain);
      for (const value of item.domains) values.add(value);
    }
    return [...values].sort();
  }, [catalog]);

  const filteredItems = useMemo(() => {
    const query = debouncedSearch.trim().toLowerCase();
    return (catalog?.items ?? []).filter((item) => {
      const matchesDomain = !domain || item.primary_domain === domain || item.domains.includes(domain);
      if (!matchesDomain) return false;
      if (!query) return true;
      return [item.title, item.slug ?? "", item.description, item.primary_domain ?? "", ...item.tags]
        .join(" ")
        .toLowerCase()
        .includes(query);
    });
  }, [catalog, debouncedSearch, domain]);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <HoverCard className="p-5" delay={0}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Datasets catalogués</span>
          <div className="mt-2 text-3xl font-semibold tabular text-fg-100">{catalog?.items.length ?? 0}</div>
          <span className="mt-1 block text-xs text-fg-500">projection Data Registry</span>
        </HoverCard>
        <HoverCard className="p-5" delay={0.05}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Domaines</span>
          <div className="mt-2 text-3xl font-semibold tabular text-accent">{domains.length}</div>
          <span className="mt-1 block text-xs text-fg-500">vocabulaire versionné</span>
        </HoverCard>
        <HoverCard className="p-5" delay={0.1}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Source de vérité</span>
          <div className="mt-2 text-lg font-semibold text-fg-100">GSIE Server</div>
          <span className="mt-1 block text-xs text-fg-500">aucune donnée inventée côté UI</span>
        </HoverCard>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[220px] flex-1">
          <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.35-4.35m2.1-5.4a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z" />
          </svg>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Rechercher un dataset…"
            aria-label="Rechercher un dataset"
            className="w-full rounded-md border border-border bg-bg-100 py-2 pl-9 pr-3 text-[13px] text-fg-100 placeholder-fg-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        <select
          value={domain}
          onChange={(event) => setDomain(event.target.value)}
          aria-label="Filtrer par domaine"
          className="rounded-md border border-border bg-bg-100 px-3 py-2 text-[13px] text-fg-200 focus:border-accent focus:outline-none"
        >
          <option value="">Tous les domaines</option>
          {domains.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <button
          onClick={() => void refresh()}
          className="rounded-md border border-border bg-bg-100 px-3 py-2 text-[12px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
        >
          Actualiser
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((item) => <Skeleton key={item} className="h-20 w-full" />)}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-error/30 bg-error-bg p-6">
          <p className="text-sm font-medium text-error">Le catalogue Data Registry est indisponible.</p>
          <p className="mt-1 font-mono text-xs text-fg-500">{error}</p>
          <button onClick={() => void refresh()} className="mt-4 rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs text-fg-200">Réessayer</button>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-lg border border-border bg-bg-100 p-10 text-center">
          <p className="text-sm font-medium text-fg-200">Aucun dataset dans cette vue</p>
          <p className="mt-1 text-xs text-fg-500">Le manifeste est validé localement ; la persistance DB sera activée après la tranche d'application idempotente.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-[13px]">
            <thead className="border-b border-border bg-bg-100">
              <tr className="text-left text-xs uppercase tracking-wide text-fg-500">
                <th className="px-4 py-3 font-medium">Dataset</th>
                <th className="px-4 py-3 font-medium">Domaine</th>
                <th className="px-4 py-3 font-medium">Usage</th>
                <th className="px-4 py-3 font-medium">Vocabulaire</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-light">
              <AnimatePresence>
                {filteredItems.map((item, index) => (
                  <motion.tr key={item.id} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }} className="hover:bg-bg-100">
                    <td className="max-w-xl px-4 py-3">
                      <div className="font-medium text-fg-100">{item.title}</div>
                      <div className="mt-0.5 font-mono text-[11px] text-fg-500">{item.slug ?? item.id}</div>
                      <p className="mt-1 line-clamp-2 text-xs text-fg-400">{item.description}</p>
                    </td>
                    <td className="px-4 py-3 align-top">
                      <div className="flex flex-wrap gap-1.5">
                        {[item.primary_domain, ...item.domains].filter(Boolean).map((value) => <span key={value} className="rounded bg-bg-300 px-1.5 py-0.5 font-mono text-[10px] text-fg-300">{value}</span>)}
                      </div>
                    </td>
                    <td className="px-4 py-3 align-top"><StatusBadge status="healthy" label={purposeLabel(item.purpose)} /></td>
                    <td className="px-4 py-3 align-top font-mono text-[11px] text-fg-400">{item.domain_vocabulary_version ?? "—"}</td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
