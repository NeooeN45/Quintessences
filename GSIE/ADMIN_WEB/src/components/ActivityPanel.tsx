import { useEffect, useState, useRef, useCallback } from "react";
import { fetchWithAuth, API_URL } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { HoverCard, Skeleton } from "./ui";
import { useToast } from "./ToastProvider";

// --- Constantes ---

const SESSION_KEY = "gsie_admin_session";
const WS_RECONNECT_BASE_DELAY = 1000; // backoff exponentiel de base
const WS_RECONNECT_MAX_DELAY = 30000; // plafond du backoff
const WS_PING_INTERVAL = 30000; // 30s heartbeat

interface WSEvent {
  event_type: string;
  event_id?: string;
  resource_id?: string;
  resource_type?: string;
  data: Record<string, unknown>;
  timestamp: string;
  trace_id?: string;
}

const EVENT_ICONS: Record<string, string> = {
  "resource.created": "M12 4v16m8-8H4",
  "resource.updated": "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  "resource.deleted": "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16",
  "phenomenon.detected": "M13 10V3L4 14h7v7l9-11h-7z",
  "model.completed": "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  "recommendation.ready": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  "alert.fire_risk": "M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2-6 1.5 1 2 4 2 6 2-1 2.657-2.657 2.657-2.657z",
  "alert.drought": "M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z",
  "alert.storm": "M13 10V3L4 14h7v7l9-11h-7z",
  "alert.pest": "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
  "observation.received": "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z",
  "assertion.validated": "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  "correlation.detected": "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
};

const EVENT_COLORS: Record<string, string> = {
  "resource.created": "var(--color-accent)",
  "resource.updated": "var(--color-accent)",
  "resource.deleted": "var(--color-error)",
  "phenomenon.detected": "var(--color-warning)",
  "model.completed": "var(--color-accent)",
  "recommendation.ready": "var(--color-accent)",
  "alert.fire_risk": "var(--color-error)",
  "alert.drought": "var(--color-warning)",
  "alert.storm": "var(--color-warning)",
  "alert.pest": "var(--color-warning)",
  "observation.received": "var(--color-fg-400)",
  "assertion.validated": "var(--color-accent)",
  "correlation.detected": "var(--color-accent)",
};

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

export default function ActivityPanel() {
  const { showToast } = useToast();
  const [events, setEvents] = useState<WSEvent[]>([]);
  const [state, setState] = useState<ConnectionState>("connecting");
  const [filter, setFilter] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const pingTimer = useRef<number | null>(null);
  const pausedRef = useRef(paused);
  const [sessionExpired, setSessionExpired] = useState(false);
  pausedRef.current = paused;

  const connect = useCallback(() => {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) {
      setSessionExpired(true);
      setState("error");
      return;
    }

    let token: string;
    try {
      token = JSON.parse(raw).accessToken;
    } catch {
      setSessionExpired(true);
      setState("error");
      return;
    }

    setState("connecting");

    let ws: WebSocket;
    try {
      ws = new WebSocket(`${API_URL.replace("http", "ws")}/api/v1/ws/events`, ["gsie.jwt", token]);
      wsRef.current = ws;
    } catch {
      setState("error");
      return;
    }

    ws.onopen = () => {
      setState("connected");
      reconnectAttempts.current = 0;
      // Heartbeat : ping toutes les 30s pour garder la connexion active
      pingTimer.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, WS_PING_INTERVAL);
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        // Le serveur envoie des WSEvent avec event_type, data, timestamp
        const event: WSEvent = {
          event_type: msg.event_type ?? "unknown",
          event_id: msg.event_id,
          resource_id: msg.resource_id,
          resource_type: msg.resource_type,
          data: msg.data ?? {},
          timestamp: msg.timestamp ?? new Date().toISOString(),
          trace_id: msg.trace_id,
        };
        // Ne pas ajouter si paused
        if (!pausedRef.current) {
          setEvents((prev) => [event, ...prev].slice(0, 200));
        }
      } catch {
        // Message non JSON (pong, etc.) — ignore
      }
    };

    ws.onerror = () => {
      setState("error");
    };

    ws.onclose = () => {
      setState("disconnected");
      if (pingTimer.current) clearInterval(pingTimer.current);
      // Reconnexion automatique avec backoff exponentiel
      const delay = Math.min(
        WS_RECONNECT_BASE_DELAY * 2 ** reconnectAttempts.current,
        WS_RECONNECT_MAX_DELAY,
      );
      reconnectAttempts.current += 1;
      reconnectTimer.current = window.setTimeout(connect, delay);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pingTimer.current) clearInterval(pingTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Test broadcast pour valider la connexion
  const sendTestBroadcast = async () => {
    try {
      const res = await fetchWithAuth("/api/v1/ws/broadcast-test", {
        method: "POST",
        body: JSON.stringify({
          channel: "all",
          event_type: "observation.received",
          message: "Test broadcast dashboard",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Broadcast envoyé — ${data.subscribers} abonné(s)`, "success");
      } else {
        showToast(`Broadcast échoué : HTTP ${res.status}`, "error");
      }
    } catch (err) {
      showToast(`Broadcast : ${err instanceof Error ? err.message : "Erreur"}`, "error");
    }
  };

  // Stats dérivées
  const eventTypes = events.reduce((acc, e) => {
    acc[e.event_type] = (acc[e.event_type] ?? 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const filteredEvents = filter ? events.filter((e) => e.event_type === filter) : events;

  const stateMeta: Record<ConnectionState, { label: string; color: string }> = {
    connecting: { label: "Connexion…", color: "var(--color-warning)" },
    connected: { label: "Connecté", color: "var(--color-accent)" },
    disconnected: { label: "Déconnecté", color: "var(--color-error)" },
    error: { label: sessionExpired ? "Session expirée" : "Erreur", color: "var(--color-error)" },
  };

  return (
    <div className="space-y-6">
      {/* Connection status + stats */}
      <div className="grid gap-4 sm:grid-cols-4">
        <HoverCard className="p-5" delay={0}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">WebSocket</span>
          <div className="mt-2 flex items-center gap-2">
            <motion.span
              className="h-2.5 w-2.5 rounded-full"
              style={{ background: stateMeta[state].color }}
              animate={state === "connected" ? { opacity: [1, 0.3, 1] } : { opacity: 1 }}
              transition={{ duration: 2, repeat: state === "connected" ? Infinity : 0 }}
            />
            <span className="text-lg font-semibold" style={{ color: stateMeta[state].color }}>
              {stateMeta[state].label}
            </span>
          </div>
          <p className="mt-1 font-mono text-[10px] text-fg-500">/api/v1/ws/events</p>
        </HoverCard>

        <HoverCard className="p-5" delay={0.05}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Événements reçus</span>
          <div className="mt-2 text-2xl font-semibold tabular text-fg-100">{events.length}</div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.1}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Types distincts</span>
          <div className="mt-2 text-2xl font-semibold tabular text-fg-100">
            {Object.keys(eventTypes).length}
          </div>
        </HoverCard>

        <HoverCard className="p-5" delay={0.15}>
          <span className="text-xs font-medium uppercase tracking-wide text-fg-500">Actions</span>
          <div className="mt-2 flex flex-col gap-1.5">
            <button
              onClick={sendTestBroadcast}
              disabled={state !== "connected"}
              className="rounded-md border border-border bg-bg-200 px-2.5 py-1 text-[11px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100 disabled:opacity-30"
            >
              Test broadcast
            </button>
            <button
              onClick={() => setPaused((p) => !p)}
              className="rounded-md border border-border bg-bg-200 px-2.5 py-1 text-[11px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
            >
              {paused ? "▶ Reprendre" : "⏸ Pause"}
            </button>
          </div>
        </HoverCard>
      </div>

      {/* Event type filters */}
      {Object.keys(eventTypes).length > 0 && (
        <HoverCard className="p-3" delay={0.2}>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setFilter(null)}
              className={`rounded-md px-2.5 py-1 font-mono text-[11px] transition-colors ${
                filter === null
                  ? "bg-accent text-white"
                  : "border border-border bg-bg-200 text-fg-300 hover:text-fg-100"
              }`}
            >
              Tous ({events.length})
            </button>
            {Object.entries(eventTypes).map(([type, count]) => (
              <button
                key={type}
                onClick={() => setFilter(type)}
                className={`rounded-md px-2.5 py-1 font-mono text-[11px] transition-colors ${
                  filter === type
                    ? "bg-accent text-white"
                    : "border border-border bg-bg-200 text-fg-300 hover:text-fg-100"
                }`}
              >
                {type} ({count})
              </button>
            ))}
            {events.length > 0 && (
              <button
                onClick={() => setEvents([])}
                className="ml-auto rounded-md px-2.5 py-1 font-mono text-[11px] text-fg-500 transition-colors hover:text-error"
              >
                Vider
              </button>
            )}
          </div>
        </HoverCard>
      )}

      {/* Event feed */}
      <HoverCard className="p-0" delay={0.25}>
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div>
            <h2 className="text-sm font-medium text-fg-100">Flux d'événements temps réel</h2>
            <p className="font-mono text-[11px] text-fg-500">
              WebSocket /api/v1/ws/events — canal: all
              {paused && <span className="ml-2 text-warning">⏸ en pause</span>}
            </p>
          </div>
          {state === "disconnected" || state === "error" ? (
            <button
              onClick={connect}
              className="rounded-md border border-border bg-bg-200 px-3 py-1 text-[11px] text-fg-300 transition-colors hover:border-accent hover:text-accent"
            >
              Reconnecter
            </button>
          ) : null}
        </div>

        <div className="max-h-[500px] overflow-y-auto">
          {state === "connecting" && events.length === 0 ? (
            <div className="space-y-2 p-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (state === "disconnected" || state === "error") && events.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full border border-error/30 bg-error/10">
                <svg className="h-6 w-6 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.5 18.5l3.536-3.536m0-5.656L9.5 5.636" />
                </svg>
              </div>
              <p className="mt-3 text-[13px] font-medium text-fg-200">WebSocket indisponible</p>
              <p className="mt-1 max-w-sm text-xs text-fg-500">
                L'API GSIE doit supporter les WebSocket sur /api/v1/ws/events.
                Reconnexion automatique dans {WS_RECONNECT_MAX_DELAY / 1000}s.
              </p>
              <button
                onClick={connect}
                className="mt-4 rounded-md border border-border bg-bg-200 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-accent hover:text-accent"
              >
                Reconnecter maintenant
              </button>
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full border border-border bg-bg-200">
                <motion.svg
                  className="h-6 w-6 text-fg-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  animate={state === "connected" && !paused ? { opacity: [0.5, 1, 0.5] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </motion.svg>
              </div>
              <p className="mt-3 text-[13px] text-fg-300">
                {filter ? `Aucun événement de type "${filter}"` : "En attente d'événements…"}
              </p>
              <p className="mt-1 text-xs text-fg-500">
                {state === "connected"
                  ? "Les événements système apparaîtront ici en temps réel."
                  : "Reconnexion en cours…"}
              </p>
              {state === "connected" && (
                <button
                  onClick={sendTestBroadcast}
                  className="mt-4 rounded-md border border-border bg-bg-200 px-3 py-1.5 text-[12px] text-fg-300 transition-colors hover:border-accent hover:text-accent"
                >
                  Envoyer un event de test
                </button>
              )}
            </div>
          ) : (
            <AnimatePresence initial={false}>
              {filteredEvents.map((event, i) => {
                const icon = EVENT_ICONS[event.event_type] ?? "M13 10V3L4 14h7v7l9-11h-7z";
                const color = EVENT_COLORS[event.event_type] ?? "var(--color-fg-400)";
                return (
                  <motion.div
                    key={`${event.event_id ?? i}-${event.timestamp}`}
                    initial={{ opacity: 0, x: -20, height: 0 }}
                    animate={{ opacity: 1, x: 0, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    className="flex items-start gap-3 border-b border-border-light px-4 py-3 hover:bg-bg-100"
                  >
                    <div
                      className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md border"
                      style={{ borderColor: `${color}40`, background: `${color}10` }}
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke={color} strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[12px] font-medium" style={{ color }}>
                          {event.event_type}
                        </span>
                        {event.resource_type && (
                          <span className="rounded bg-bg-300 px-1.5 py-0.5 font-mono text-[10px] text-fg-400">
                            {event.resource_type}
                          </span>
                        )}
                        <span className="ml-auto font-mono text-[10px] text-fg-500">
                          {new Date(event.timestamp).toLocaleTimeString("fr-FR")}
                        </span>
                      </div>
                      <p className="mt-0.5 truncate font-mono text-[11px] text-fg-400">
                        {JSON.stringify(event.data).slice(0, 150)}
                      </p>
                      {event.trace_id && (
                        <p className="mt-0.5 font-mono text-[10px] text-fg-500">
                          trace: {event.trace_id}
                        </p>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          )}
        </div>
      </HoverCard>
    </div>
  );
}
