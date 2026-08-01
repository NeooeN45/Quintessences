"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

// --- Types ---

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  read: boolean;
  created_at: string;
}

interface ApiNotification {
  id: string;
  title: string;
  message: string;
  type?: string;
  read?: boolean;
  created_at?: string;
  created_at_iso?: string;
}

// --- Constantes ---

const API_URL = "http://localhost:8000";
const API_PREFIX = "/api/v1";
const SESSION_KEY = "gsie_admin_session";
const POLL_INTERVAL = 30000;
const EASE_OUT_QUART: [number, number, number, number] = [0.16, 1, 0.3, 1];

const TYPE_CONFIG: Record<
  Notification["type"],
  { color: string; bg: string; icon: string }
> = {
  info: { color: "text-fg-300", bg: "bg-bg-300", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
  success: { color: "text-accent", bg: "bg-accent/10", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" },
  warning: { color: "text-warning", bg: "bg-warning/10", icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" },
  error: { color: "text-error", bg: "bg-error/10", icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" },
};

// --- Helpers ---

function getAuthHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return {};
  try {
    const s = JSON.parse(raw) as { accessToken: string };
    return { Authorization: `Bearer ${s.accessToken}` };
  } catch {
    return {};
  }
}

function normalizeType(raw?: string): Notification["type"] {
  if (raw === "success" || raw === "warning" || raw === "error") return raw;
  return "info";
}

function normalizeNotification(raw: ApiNotification): Notification {
  return {
    id: raw.id,
    title: raw.title,
    message: raw.message,
    type: normalizeType(raw.type),
    read: raw.read ?? false,
    created_at: raw.created_at ?? raw.created_at_iso ?? new Date().toISOString(),
  };
}

function relativeTime(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diffSec = Math.max(0, Math.floor((now - then) / 1000));
  if (diffSec < 60) return `il y a ${diffSec}s`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `il y a ${diffMin}min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `il y a ${diffH}h`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 30) return `il y a ${diffD}j`;
  const diffMo = Math.floor(diffD / 30);
  return `il y a ${diffMo}mo`;
}

// --- Composant ---

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}${API_PREFIX}/notifications`, {
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const body = await resp.json();
      const items: ApiNotification[] = Array.isArray(body) ? body : (body.items ?? []);
      setNotifications(items.map(normalizeNotification));
      setError(null);
    } catch {
      setError("Impossible de charger les notifications");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const timer = setInterval(fetchNotifications, POLL_INTERVAL);
    return () => clearInterval(timer);
  }, [fetchNotifications]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      await fetch(`${API_URL}${API_PREFIX}/notifications/read-all`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
      });
    } catch {
      // Échec silencieux — l'UI reste à jour localement
    }
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-bg-100 text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
        aria-label="Notifications"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <motion.span
            className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-error px-1 text-[9px] font-bold text-white"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 15 }}
            key={unreadCount}
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </motion.span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: EASE_OUT_QUART }}
            className="absolute right-0 top-11 z-50 w-80 overflow-hidden rounded-lg border border-border bg-bg-100 shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-border-light px-4 py-3">
              <span className="text-sm font-medium text-fg-100">Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  className="text-xs text-accent transition-opacity hover:opacity-80"
                >
                  Tout marquer comme lu
                </button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
                </div>
              ) : error && notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-xs text-fg-500">
                  Aucune notification
                </div>
              ) : notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-xs text-fg-500">
                  Aucune notification
                </div>
              ) : (
                <AnimatePresence initial={false}>
                  {notifications.map((n, i) => {
                    const cfg = TYPE_CONFIG[n.type];
                    return (
                      <motion.div
                        key={n.id}
                        initial={{ opacity: 0, x: -12 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -12 }}
                        transition={{
                          duration: 0.25,
                          ease: EASE_OUT_QUART,
                          delay: i * 0.04,
                        }}
                        className={`flex gap-3 border-b border-border-light px-4 py-3 transition-colors hover:bg-bg-200 ${!n.read ? "bg-accent/[0.03]" : ""}`}
                      >
                        <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${cfg.bg}`}>
                          <svg className={`h-4 w-4 ${cfg.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d={cfg.icon} />
                          </svg>
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate text-xs font-medium text-fg-100">{n.title}</span>
                            {!n.read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />}
                          </div>
                          <p className="mt-0.5 line-clamp-2 text-xs text-fg-400">{n.message}</p>
                          <span className="mt-1 block text-[10px] text-fg-500">{relativeTime(n.created_at)}</span>
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
