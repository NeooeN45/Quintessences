import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { APPS, type AppEntry } from "../lib/apps";

/**
 * Grille des applications — SITE-F-003/004.
 * Fiches façon "case study" (papacreative.com : PROJECT TYPE / INDUSTRY)
 * adaptées en DOMAINE / STATUT. Un clic ouvre un panneau détaillé sans
 * quitter la page (SITE-002 §5.3).
 */
export default function AppGrid() {
  const [selected, setSelected] = useState<AppEntry | null>(null);

  return (
    <div>
      <div className="divide-y divide-[var(--color-border)] border-y border-[var(--color-border)]">
        {APPS.map((app) => {
          const isSelected = selected?.slug === app.slug;
          return (
            <button
              key={app.slug}
              type="button"
              aria-pressed={isSelected}
              onClick={() => setSelected(isSelected ? null : app)}
              className="group flex w-full items-center gap-6 py-5 text-left transition-colors hover:bg-[var(--color-bg-100)]"
            >
              <img
                src={app.icon}
                alt=""
                aria-hidden="true"
                width={44}
                height={44}
                className="h-11 w-11 shrink-0 rounded-lg object-cover"
              />

              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-[var(--color-fg-100)]">{app.name}</p>
              </div>

              <div className="hidden shrink-0 sm:block">
                <p className="eyebrow !text-[10px] text-[var(--color-fg-500)]">Domaine</p>
                <p className="text-sm text-[var(--color-fg-300)]">{app.domain}</p>
              </div>

              <div className="hidden w-28 shrink-0 md:block">
                <p className="eyebrow !text-[10px] text-[var(--color-fg-500)]">Statut</p>
                <p className="text-sm text-[var(--color-fg-300)]">
                  {app.status === "disponible" ? "Disponible" : "Planifiée"}
                </p>
              </div>

              <span
                className="hidden h-2 w-2 shrink-0 rounded-full sm:block"
                style={{ background: app.accent }}
                aria-hidden="true"
              />

              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
                className={`shrink-0 text-[var(--color-fg-400)] transition-transform ${isSelected ? "rotate-90" : ""}`}
              >
                <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        {selected && (
          <motion.div
            key={selected.slug}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="flex items-start gap-4 border-b border-[var(--color-border)] bg-[var(--color-bg-100)] px-6 py-8">
              <img src={selected.icon} alt="" aria-hidden="true" className="h-14 w-14 rounded-lg object-cover" />
              <div>
                <p className="eyebrow" style={{ color: selected.accent }}>
                  {selected.domain}
                </p>
                <p className="mt-1 text-lg font-medium text-[var(--color-fg-100)]">{selected.name}</p>
                <p className="mt-2 max-w-2xl text-sm text-[var(--color-fg-300)]">{selected.summary}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
