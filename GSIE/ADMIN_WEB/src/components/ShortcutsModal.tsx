import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const SHORTCUTS = [
  { keys: ["⌘", "K"], description: "Ouvrir la Command Palette", group: "Global" },
  { keys: ["?"], description: "Afficher cette aide", group: "Global" },
  { keys: ["Esc"], description: "Fermer la fenêtre active", group: "Global" },
  { keys: ["↑", "↓"], description: "Naviguer dans la liste", group: "Command Palette" },
  { keys: ["↵"], description: "Sélectionner", group: "Command Palette" },
  { keys: ["G", "O"], description: "Vue d'ensemble", group: "Navigation" },
  { keys: ["G", "H"], description: "Santé système", group: "Navigation" },
  { keys: ["G", "R"], description: "Ressources", group: "Navigation" },
  { keys: ["G", "E"], description: "Moteurs", group: "Navigation" },
];

export default function ShortcutsModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Ouvrir avec "?" (Shift+/)
      if (e.key === "?" || (e.shiftKey && e.key === "/")) {
        // Ne pas déclencher si on tape dans un input
        const target = e.target as HTMLElement;
        if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Navigation rapide G+lettre
  useEffect(() => {
    let gPressed = false;
    let gTimer: number | null = null;

    const handler = (e: KeyboardEvent) => {
      if (open) return;
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;

      if (e.key === "g" && !gPressed) {
        gPressed = true;
        gTimer = window.setTimeout(() => { gPressed = false; }, 1000);
        return;
      }

      if (gPressed) {
        const map: Record<string, string> = {
          o: "/",
          h: "/health",
          r: "/resources",
          e: "/engines",
          k: "/knowledge",
          c: "/climate",
          m: "/map",
          a: "/activity",
          u: "/audit",
          g: "/gamification",
        };
        const path = map[e.key.toLowerCase()];
        if (path) {
          e.preventDefault();
          window.location.href = path;
        }
        gPressed = false;
        if (gTimer) clearTimeout(gTimer);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open]);

  const groups = [...new Set(SHORTCUTS.map((s) => s.group))];

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -8 }}
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-xl border border-border bg-bg-100 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-label="Raccourcis clavier"
          >
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold text-fg-100">Raccourcis clavier</h2>
              <p className="text-xs text-fg-500">Appuyez sur ? pour ouvrir/fermer</p>
            </div>
            <div className="max-h-96 overflow-y-auto p-4">
              {groups.map((group) => (
                <div key={group} className="mb-4 last:mb-0">
                  <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wide text-fg-500">{group}</h3>
                  <div className="space-y-1.5">
                    {SHORTCUTS.filter((s) => s.group === group).map((s, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <span className="text-[13px] text-fg-300">{s.description}</span>
                        <div className="flex items-center gap-1">
                          {s.keys.map((k, j) => (
                            <kbd
                              key={j}
                              className="rounded border border-border bg-bg-200 px-1.5 py-0.5 font-mono text-[11px] text-fg-200"
                            >
                              {k}
                            </kbd>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="border-t border-border px-4 py-2 text-[11px] text-fg-500">
              <kbd className="rounded border border-border px-1 py-0.5">Esc</kbd> pour fermer
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
