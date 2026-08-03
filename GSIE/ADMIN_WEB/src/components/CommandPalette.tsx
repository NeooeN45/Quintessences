import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

const COMMANDS = [
  { id: "overview", label: "Vue d'ensemble", href: "/", icon: "M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3", group: "Navigation" },
  { id: "health", label: "Santé système", href: "/health", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z", group: "Navigation" },
  { id: "resources", label: "Ressources", href: "/resources", icon: "M4 6h16M4 12h16M4 18h16", group: "Navigation" },
  { id: "engines", label: "Moteurs", href: "/engines", icon: "M13 10V3L4 14h7v7l9-11h-7z", group: "Navigation" },
  { id: "knowledge", label: "Connaissances", href: "/knowledge", icon: "M12 6.253v13m0-13C10.121 4.834 7.5 4.5 5.5 4.5c-1.5 0-3 .5-3 .5v13s1.5-.5 3-.5c2 0 4.621.334 6.5 1.753m0-13C13.879 4.834 16.5 4.5 18.5 4.5c1.5 0 3 .5 3 .5v13s-1.5-.5-3-.5c-2 0-4.621.334-6.5 1.753", group: "Navigation" },
  { id: "climate", label: "Climat", href: "/climate", icon: "M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z", group: "Navigation" },
  { id: "map", label: "Carte des risques", href: "/map", icon: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7", group: "Navigation" },
  { id: "activity", label: "Activité temps réel", href: "/activity", icon: "M13 10V3L4 14h7v7l9-11h-7z", group: "Navigation" },
  { id: "audit", label: "Audit", href: "/audit", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", group: "Navigation" },
  { id: "gamification", label: "Engagement", href: "/gamification", icon: "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z", group: "Navigation" },
  { id: "logout", label: "Déconnexion", href: null, icon: "M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1", group: "Action" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);

  const filtered = COMMANDS.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase()),
  );

  const execute = useCallback((cmd: typeof COMMANDS[0]) => {
    if (cmd.id === "logout") {
      sessionStorage.removeItem("gsie_admin_session");
      window.location.href = "/login";
      return;
    }
    if (cmd.href) {
      window.location.href = cmd.href;
    }
    setOpen(false);
    setQuery("");
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") {
        setOpen(false);
        setQuery("");
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setSelected(0);
    }
  }, [open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelected((s) => Math.min(s + 1, filtered.length - 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelected((s) => Math.max(s - 1, 0));
      }
      if (e.key === "Enter" && filtered[selected]) {
        e.preventDefault();
        execute(filtered[selected]);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, filtered, selected, execute]);

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
            className="fixed left-1/2 top-1/4 z-50 w-full max-w-lg -translate-x-1/2 overflow-hidden rounded-xl border border-border bg-bg-100 shadow-2xl"
          >
            {/* Input */}
            <div className="flex items-center gap-3 border-b border-border px-4 py-3">
              <svg className="h-4 w-4 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                autoFocus
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelected(0);
                }}
                placeholder="Rechercher une commande…"
                className="flex-1 bg-transparent text-[14px] text-fg-100 placeholder-fg-500 focus:outline-none"
              />
              <kbd className="rounded border border-border px-1.5 py-0.5 text-[10px] text-fg-500">ESC</kbd>
            </div>

            {/* Results */}
            <div className="max-h-80 overflow-y-auto p-2">
              {filtered.length === 0 ? (
                <div className="px-3 py-8 text-center text-[13px] text-fg-500">
                  Aucun résultat pour « {query} »
                </div>
              ) : (
                filtered.map((cmd, i) => (
                  <button
                    key={cmd.id}
                    onClick={() => execute(cmd)}
                    onMouseEnter={() => setSelected(i)}
                    className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-[13px] transition-colors ${
                      i === selected ? "bg-bg-300 text-fg-100" : "text-fg-300"
                    }`}
                  >
                    <svg className="h-4 w-4 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d={cmd.icon} />
                    </svg>
                    <span>{cmd.label}</span>
                    <span className="ml-auto text-[10px] text-fg-500">{cmd.group}</span>
                  </button>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-border px-4 py-2 text-[11px] text-fg-500">
              <span className="flex items-center gap-2">
                <kbd className="rounded border border-border px-1 py-0.5">↑↓</kbd> naviguer
                <kbd className="ml-2 rounded border border-border px-1 py-0.5">↵</kbd> sélectionner
              </span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
