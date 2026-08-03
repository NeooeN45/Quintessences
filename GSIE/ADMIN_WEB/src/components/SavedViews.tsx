"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface SavedView {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  createdAt: number;
}

interface SavedViewsProps {
  scope: string;
  currentFilters: Record<string, unknown>;
  onApply: (filters: Record<string, unknown>) => void;
}

const STORAGE_PREFIX = "gsie-saved-views-";

function storageKey(scope: string): string {
  return `${STORAGE_PREFIX}${scope}`;
}

function loadViews(scope: string): SavedView[] {
  const raw = localStorage.getItem(storageKey(scope));
  if (!raw) return [];
  try {
    return JSON.parse(raw) as SavedView[];
  } catch {
    return [];
  }
}

function saveViews(scope: string, views: SavedView[]): void {
  localStorage.setItem(storageKey(scope), JSON.stringify(views));
}

export default function SavedViews({
  scope,
  currentFilters,
  onApply,
}: SavedViewsProps) {
  const [open, setOpen] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [views, setViews] = useState<SavedView[]>([]);
  const [viewName, setViewName] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setViews(loadViews(scope));
  }, [scope]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const persist = useCallback(
    (next: SavedView[]) => {
      setViews(next);
      saveViews(scope, next);
    },
    [scope],
  );

  const handleSave = useCallback(() => {
    const name = viewName.trim();
    if (!name) return;
    const view: SavedView = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name,
      filters: { ...currentFilters },
      createdAt: Date.now(),
    };
    persist([...views, view]);
    setViewName("");
    setShowSaveDialog(false);
  }, [viewName, currentFilters, views, persist]);

  const handleDelete = useCallback(
    (id: string) => {
      persist(views.filter((v) => v.id !== id));
    },
    [views, persist],
  );

  const handleApply = useCallback(
    (view: SavedView) => {
      onApply(view.filters);
      setOpen(false);
    },
    [onApply],
  );

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-md border border-border bg-bg-200 px-3 py-1.5 text-xs text-fg-200 transition-colors hover:border-border-strong"
      >
        <svg
          className="h-3.5 w-3.5 text-fg-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
          />
        </svg>
        Vues sauvegardées
        {views.length > 0 && (
          <span className="rounded-full bg-bg-300 px-1.5 text-[10px] text-fg-400">
            {views.length}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.97 }}
            transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
            className="absolute right-0 top-full z-40 mt-1 w-64 overflow-hidden rounded-lg border border-border bg-bg-100 shadow-xl"
          >
            <div className="border-b border-border px-3 py-2">
              <span className="text-[11px] font-medium uppercase tracking-wide text-fg-500">
                Vues — {scope}
              </span>
            </div>

            <div className="max-h-60 overflow-y-auto">
              {views.length === 0 ? (
                <div className="px-3 py-6 text-center text-xs text-fg-500">
                  Aucune vue sauvegardée
                </div>
              ) : (
                views.map((view) => (
                  <div
                    key={view.id}
                    className="group flex items-center justify-between px-3 py-2 transition-colors hover:bg-bg-200"
                  >
                    <button
                      onClick={() => handleApply(view)}
                      className="flex-1 text-left text-xs text-fg-200"
                    >
                      {view.name}
                    </button>
                    <button
                      onClick={() => handleDelete(view.id)}
                      className="ml-2 text-fg-500 opacity-0 transition-opacity hover:text-error group-hover:opacity-100"
                      aria-label="Supprimer la vue"
                    >
                      <svg
                        className="h-3.5 w-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={1.5}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="border-t border-border p-2">
              <button
                onClick={() => setShowSaveDialog(true)}
                className="flex w-full items-center justify-center gap-2 rounded-md bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent transition-colors hover:bg-accent/20"
              >
                <svg
                  className="h-3.5 w-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Sauvegarder la vue actuelle
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showSaveDialog && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowSaveDialog(false)}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: -8 }}
              transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
              className="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-xl border border-border bg-bg-100 shadow-2xl"
              role="dialog"
              aria-modal="true"
              aria-label="Nommer la vue"
            >
              <div className="border-b border-border px-4 py-3">
                <h2 className="text-sm font-semibold text-fg-100">
                  Sauvegarder la vue
                </h2>
                <p className="text-xs text-fg-500">
                  Donnez un nom à cette configuration de filtres
                </p>
              </div>
              <div className="p-4">
                <input
                  type="text"
                  autoFocus
                  value={viewName}
                  onChange={(e) => setViewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSave()}
                  placeholder="Nom de la vue…"
                  className="w-full rounded-md border border-border bg-bg-200 px-3 py-2 text-sm text-fg-100 placeholder-fg-500 focus:border-accent focus:outline-none"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button
                    onClick={() => {
                      setShowSaveDialog(false);
                      setViewName("");
                    }}
                    className="rounded-lg border border-border px-4 py-2 text-xs text-fg-300 transition-colors hover:border-border-strong"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={!viewName.trim()}
                    className="rounded-lg bg-accent px-4 py-2 text-xs font-medium text-bg-000 transition-colors hover:bg-accent/90 disabled:opacity-40"
                  >
                    Sauvegarder
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
