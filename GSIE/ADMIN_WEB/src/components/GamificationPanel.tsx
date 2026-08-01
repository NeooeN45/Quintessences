"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton } from "./ui";

const API_URL = "http://localhost:8000";
const SESSION_KEY = "gsie_admin_session";

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
}

interface ProgressGoal {
  id: string;
  label: string;
  current: number;
  target: number;
  unit: string;
}

interface GamificationStats {
  badges: Badge[];
  goals: ProgressGoal[];
  streak: number;
}

const EMPTY_STATS: GamificationStats = {
  badges: [],
  goals: [],
  streak: 0,
};

const FALLBACK_STATS: GamificationStats = {
  badges: [
    { id: "first-login", name: "Première connexion", description: "Connexion au dashboard", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z", unlocked: true },
    { id: "data-explorer", name: "Explorateur de données", description: "Consulté 50 ressources", icon: "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z", unlocked: true },
    { id: "centurion", name: "Centurion", description: "100 parcelles surveillées", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z", unlocked: false },
    { id: "night-owl", name: "Veilleur nocturne", description: "Actif après minuit", icon: "M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z", unlocked: false },
  ],
  goals: [
    { id: "parcels", label: "Parcelles surveillées", current: 73, target: 100, unit: "parcelles" },
    { id: "alerts", label: "Alertes traitées", current: 28, target: 50, unit: "alertes" },
    { id: "reports", label: "Rapports générés", current: 12, target: 20, unit: "rapports" },
  ],
  streak: 7,
};

function getAuthHeader(): Record<string, string> {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return {};
  try {
    return { Authorization: `Bearer ${JSON.parse(raw).accessToken}` };
  } catch {
    return {};
  }
}

export default function GamificationPanel() {
  const [stats, setStats] = useState<GamificationStats>(EMPTY_STATS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch(`${API_URL}/api/v1/gamification/stats`, {
          headers: { ...getAuthHeader() },
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (!cancelled) setStats(data);
      } catch (err) {
        console.error("[GamificationPanel]", err);
        if (!cancelled) setStats(EMPTY_STATS);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="space-y-4 rounded-lg border border-border bg-bg-100 p-4">
        <Skeleton className="h-6 w-40" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
      </div>
    );
  }

  const hasData = stats.badges.length > 0 || stats.goals.length > 0;
  const displayStats = hasData ? stats : FALLBACK_STATS;

  return (
    <div className="space-y-6 rounded-lg border border-border bg-bg-100 p-4">
      <StreakSection streak={displayStats.streak} />
      <BadgesSection badges={displayStats.badges} />
      <ProgressSection goals={displayStats.goals} />
    </div>
  );
}

function StreakSection({ streak }: { streak: number }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border-light bg-bg-200 px-4 py-3">
      <motion.div
        initial={{ scale: 0, rotate: -20 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning/10"
      >
        <svg
          className="h-6 w-6 text-warning"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.46 7.93 4 10.86 4 14.17c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z" />
        </svg>
      </motion.div>
      <div>
        <div className="text-2xl font-bold tabular text-fg-100">{streak}</div>
        <div className="text-xs text-fg-500">jours consécutifs d'activité</div>
      </div>
    </div>
  );
}

function BadgesSection({ badges }: { badges: Badge[] }) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-fg-500">
        Badges
      </h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {badges.map((badge, i) => (
          <motion.div
            key={badge.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              type: "spring",
              stiffness: 200,
              damping: 15,
              delay: i * 0.08,
            }}
            whileHover={badge.unlocked ? { y: -2 } : undefined}
            className={`flex flex-col items-center rounded-lg border p-3 text-center transition-colors ${
              badge.unlocked
                ? "border-border bg-bg-200"
                : "border-border-light bg-bg-300 opacity-50"
            }`}
          >
            <div
              className={`mb-2 flex h-10 w-10 items-center justify-center rounded-full ${
                badge.unlocked ? "bg-accent/10" : "bg-fg-500/10"
              }`}
            >
              <svg
                className={`h-5 w-5 ${
                  badge.unlocked ? "text-accent" : "text-fg-500"
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d={badge.icon}
                />
              </svg>
            </div>
            <div className="text-xs font-medium text-fg-200">{badge.name}</div>
            <div className="mt-0.5 text-[10px] text-fg-500">
              {badge.description}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function ProgressSection({ goals }: { goals: ProgressGoal[] }) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-fg-500">
        Progression
      </h3>
      <div className="space-y-4">
        {goals.map((goal, i) => {
          const pct = Math.min(100, (goal.current / goal.target) * 100);
          return (
            <div key={goal.id}>
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="text-fg-200">{goal.label}</span>
                <span className="tabular text-fg-500">
                  {goal.current} / {goal.target} {goal.unit}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-bg-300">
                <motion.div
                  className="h-full rounded-full bg-accent"
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.8, delay: i * 0.15, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
