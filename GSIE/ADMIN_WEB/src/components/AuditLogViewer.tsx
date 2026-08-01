"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import { Skeleton } from "./ui";

const API_URL = "http://localhost:8000";
const SESSION_KEY = "gsie_admin_session";
const PAGE_SIZE = 10;

type ActionType = "create" | "update" | "delete" | "export";

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  action: ActionType | string;
  resource: string;
  ip: string;
  details: Record<string, unknown>;
}

const ACTION_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  create: { bg: "bg-accent/10", text: "text-accent", label: "Création" },
  update: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Modification" },
  delete: { bg: "bg-error/10", text: "text-error", label: "Suppression" },
  export: { bg: "bg-purple-500/10", text: "text-purple-400", label: "Export" },
};

const ACTION_OPTIONS: { value: ActionType; label: string }[] = [
  { value: "create", label: "Création" },
  { value: "update", label: "Modification" },
  { value: "delete", label: "Suppression" },
  { value: "export", label: "Export" },
];

function getAuthHeader(): Record<string, string> {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return {};
  try {
    return { Authorization: `Bearer ${JSON.parse(raw).accessToken}` };
  } catch {
    return {};
  }
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function toCSV(logs: AuditLog[]): string {
  const headers = ["timestamp", "utilisateur", "action", "resource", "ip", "details"];
  const rows = logs.map((l) =>
    [l.timestamp, l.user, l.action, l.resource, l.ip, JSON.stringify(l.details)]
      .map((v) => `"${String(v).replace(/"/g, '""')}"`)
      .join(","),
  );
  return [headers.join(","), ...rows].join("\n");
}

function downloadCSV(logs: AuditLog[]): void {
  const blob = new Blob([toCSV(logs)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `audit-logs-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function AuditLogViewer() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const [userFilter, setUserFilter] = useState("");
  const [actionFilter, setActionFilter] = useState<ActionType | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_URL}/api/v1/audit-logs`, {
        headers: { ...getAuthHeader() },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setLogs(Array.isArray(data) ? data : (data.items ?? []));
    } catch (err) {
      console.error("[AuditLogViewer]", err);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const filtered = useMemo(() => {
    return logs.filter((log) => {
      if (userFilter && !log.user.toLowerCase().includes(userFilter.toLowerCase()))
        return false;
      if (actionFilter && log.action !== actionFilter) return false;
      if (dateFrom && new Date(log.timestamp) < new Date(dateFrom)) return false;
      if (dateTo && new Date(log.timestamp) > new Date(dateTo + "T23:59:59"))
        return false;
      return true;
    });
  }, [logs, userFilter, actionFilter, dateFrom, dateTo]);

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE);
  const pageLogs = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  useEffect(() => {
    setPage(0);
  }, [userFilter, actionFilter, dateFrom, dateTo]);

  return (
    <div className="rounded-lg border border-border bg-bg-100">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-fg-100">Journal d'audit</h2>
          <button
            onClick={() => downloadCSV(filtered)}
            disabled={filtered.length === 0}
            className="rounded-md border border-border px-3 py-1 text-xs text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100 disabled:opacity-40"
          >
            Exporter CSV ({filtered.length})
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-3">
        <input
          type="text"
          placeholder="Utilisateur…"
          value={userFilter}
          onChange={(e) => setUserFilter(e.target.value)}
          className="w-40 rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs text-fg-100 placeholder-fg-500 focus:border-accent focus:outline-none"
        />
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value as ActionType | "")}
          className="rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs text-fg-100 focus:border-accent focus:outline-none"
        >
          <option value="">Toutes les actions</option>
          {ACTION_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs text-fg-100 focus:border-accent focus:outline-none"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs text-fg-100 focus:border-accent focus:outline-none"
        />
      </div>

      {loading ? (
        <div className="space-y-2 p-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : error ? (
        <div className="p-8 text-center text-sm text-error">{error}</div>
      ) : pageLogs.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-fg-500">
                <th className="px-4 py-2 font-medium">Horodatage</th>
                <th className="px-4 py-2 font-medium">Utilisateur</th>
                <th className="px-4 py-2 font-medium">Action</th>
                <th className="px-4 py-2 font-medium">Ressource</th>
                <th className="px-4 py-2 font-medium">IP</th>
                <th className="px-4 py-2 font-medium">Détails</th>
              </tr>
            </thead>
            <tbody>
              {pageLogs.map((log, i) => {
                const style = ACTION_STYLES[log.action] ?? {
                  bg: "bg-fg-500/10",
                  text: "text-fg-400",
                  label: log.action,
                };
                return (
                  <motion.tr
                    key={log.id ?? i}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.04 }}
                    className="border-b border-border-light hover:bg-bg-200"
                  >
                    <td className="whitespace-nowrap px-4 py-2.5 text-fg-300 tabular">
                      {formatDate(log.timestamp)}
                    </td>
                    <td className="px-4 py-2.5 text-fg-200">{log.user}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-block rounded-md px-2 py-0.5 text-[11px] font-medium ${style.bg} ${style.text}`}
                      >
                        {style.label}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-fg-300">{log.resource}</td>
                    <td className="px-4 py-2.5 font-mono text-fg-400">{log.ip}</td>
                    <td className="px-4 py-2.5 text-fg-500">
                      {Object.keys(log.details).length > 0
                        ? JSON.stringify(log.details)
                        : "—"}
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!loading && pageCount > 1 && (
        <div className="flex items-center justify-between border-t border-border px-4 py-2">
          <span className="text-xs text-fg-500">
            Page {page + 1} / {pageCount} — {filtered.length} entrées
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-border px-2 py-1 text-xs text-fg-300 transition-colors hover:border-border-strong disabled:opacity-40"
            >
              ←
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              disabled={page >= pageCount - 1}
              className="rounded-md border border-border px-2 py-1 text-xs text-fg-300 transition-colors hover:border-border-strong disabled:opacity-40"
            >
              →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
      <svg
        className="mb-4 h-12 w-12 text-fg-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 17v-2m3 2v-4m3 4v-6m-6 6V5a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-4l-2-2H7z"
        />
      </svg>
      <p className="text-sm text-fg-400">Aucun log d'audit</p>
      <p className="mt-1 text-xs text-fg-500">
        Les actions administratives apparaîtront ici
      </p>
    </div>
  );
}
