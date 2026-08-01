"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useFocusTrap } from "../lib/useFocusTrap";

const SESSION_KEY = "gsie_admin_session";
const ACTIVITY_KEY = "gsie-session-activity";
const WARNING_DURATION_MS = 60_000; // 60s avant expiration
const ACTIVITY_EVENTS = ["mousedown", "keydown", "scroll", "touchstart"];

interface SessionData {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export default function SessionTimeout() {
  const [showWarning, setShowWarning] = useState(false);
  const [remaining, setRemaining] = useState(0);
  const lastActivity = useRef(Date.now());
  const containerRef = useFocusTrap<HTMLDivElement>(showWarning);

  const reset = useCallback(() => {
    lastActivity.current = Date.now();
    setShowWarning(false);
    localStorage.setItem(ACTIVITY_KEY, Date.now().toString());
  }, []);

  const extendSession = useCallback(async () => {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return;
    try {
      const session = JSON.parse(raw) as SessionData;
      const res = await fetch("http://localhost:8000/api/v1/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: session.refreshToken }),
      });
      if (res.ok) {
        const data = await res.json();
        const newSession: SessionData = {
          accessToken: data.access_token,
          refreshToken: data.refresh_token ?? session.refreshToken,
          expiresAt: Date.now() + (data.expires_in ?? 3600) * 1000,
        };
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(newSession));
        reset();
      } else {
        sessionStorage.removeItem(SESSION_KEY);
        window.location.href = "/login";
      }
    } catch {
      sessionStorage.removeItem(SESSION_KEY);
      window.location.href = "/login";
    }
  }, [reset]);

  const logout = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(ACTIVITY_KEY);
    window.location.href = "/login";
  }, []);

  // Track user activity
  useEffect(() => {
    const handleActivity = () => {
      lastActivity.current = Date.now();
      localStorage.setItem(ACTIVITY_KEY, Date.now().toString());
    };
    ACTIVITY_EVENTS.forEach((evt) => window.addEventListener(evt, handleActivity, { passive: true }));
    return () => ACTIVITY_EVENTS.forEach((evt) => window.removeEventListener(evt, handleActivity));
  }, []);

  // Cross-tab sync
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === ACTIVITY_KEY && e.newValue) {
        lastActivity.current = parseInt(e.newValue, 10);
        setShowWarning(false);
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  // Check expiration every second
  useEffect(() => {
    const interval = setInterval(() => {
      const raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) return;

      let session: SessionData;
      try {
        session = JSON.parse(raw);
      } catch {
        return;
      }

      const now = Date.now();
      const timeUntilExpiry = session.expiresAt - now;
      const idleTime = now - lastActivity.current;

      // Si inactivité > 15 min OU token expiré
      if (idleTime > 15 * 60 * 1000 || timeUntilExpiry <= 0) {
        logout();
        return;
      }

      // Warning 60s avant expiration
      if (timeUntilExpiry <= WARNING_DURATION_MS) {
        setShowWarning(true);
        setRemaining(Math.ceil(timeUntilExpiry / 1000));
      } else {
        setShowWarning(false);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [logout]);

  return (
    <AnimatePresence>
      {showWarning && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 p-4"
          onClick={(e) => e.stopPropagation()}
        >
          <motion.div
            ref={containerRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="session-timeout-title"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="w-full max-w-md rounded-lg border border-border bg-bg-100 p-6 shadow-2xl"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-warning/20">
                <svg className="h-5 w-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <h2 id="session-timeout-title" className="text-lg font-semibold text-fg-100">
                  Session expirée bientôt
                </h2>
                <p className="mt-2 text-sm text-fg-300">
                  Votre session expire dans{" "}
                  <span className="font-mono font-bold text-warning tabular">{remaining}s</span>.
                  Voulez-vous la prolonger ?
                </p>
                <div className="mt-4 flex gap-3">
                  <button
                    onClick={extendSession}
                    className="flex-1 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:opacity-90"
                  >
                    Prolonger
                  </button>
                  <button
                    onClick={logout}
                    className="rounded-md border border-border bg-bg-200 px-4 py-2 text-sm font-medium text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
                  >
                    Se déconnecter
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
