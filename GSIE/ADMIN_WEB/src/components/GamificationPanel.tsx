"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton } from "./ui";
import { fetchWithAuth } from "../lib/api";

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

export default function GamificationPanel() {
  const [stats, setStats] = useState<GamificationStats>(EMPTY_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetchWithAuth("/api/v1/gamification/stats");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (!cancelled) setStats(data);
      } catch (err) {
        // 401 : fetchWithAuth redirige vers /login automatiquement
        if (!cancelled) {
          if (err instanceof TypeError) {
            setError("API indisponible");
          } else {
            setError(err instanceof Error ? err.message : "Erreur");
          }
          setStats(EMPTY_STATS);
        }
        console.error("[GamificationPanel]", err);
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

  const hasData = stats.badges.length > 0 || stats.goals.length > 0 || stats.streak > 0;

  if (!hasData && !loading && !error) {
    return (
      <div className="rounded-lg border border-border bg-bg-100 p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-border bg-bg-200">
          <svg className="h-6 w-6 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-sm font-medium text-fg-200">Aucune donnée de gamification</h3>
        <p className="mt-1 text-xs text-fg-500">
          Les statistiques d'engagement apparaîtront ici quand l'endpoint /gamification/stats sera disponible.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 rounded-lg border border-border bg-bg-100 p-4">
      <StreakSection streak={stats.streak} />
      <BadgesSection badges={stats.badges} />
      <ProgressSection goals={stats.goals} />
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
