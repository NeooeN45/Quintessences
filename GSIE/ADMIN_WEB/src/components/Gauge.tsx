"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";

// --- Types ---

export interface GaugeThresholds {
  warning: number;
  danger: number;
}

export interface GaugeProps {
  value: number;
  max?: number;
  label?: string;
  size?: "sm" | "md" | "lg";
  thresholds?: GaugeThresholds;
  unit?: string;
}

// --- Constantes ---

const SIZES: Record<NonNullable<GaugeProps["size"]>, { w: number; h: number; font: string }> = {
  sm: { w: 120, h: 70, font: "text-base" },
  md: { w: 180, h: 100, font: "text-xl" },
  lg: { w: 240, h: 130, font: "text-2xl" },
};

const EASE_OUT_QUART: [number, number, number, number] = [0.16, 1, 0.3, 1];

// --- Helpers ---

function resolveColor(pct: number, thresholds?: GaugeThresholds): string {
  if (!thresholds) return "var(--color-accent)";
  if (pct >= thresholds.danger) return "var(--color-error)";
  if (pct >= thresholds.warning) return "var(--color-warning)";
  return "var(--color-accent)";
}

// --- Composant ---

export default function Gauge({
  value,
  max = 100,
  label,
  size = "md",
  thresholds,
  unit,
}: GaugeProps) {
  const dims = SIZES[size];
  const pct = Math.min(Math.max((value / max) * 100, 0), 100);
  const color = useMemo(() => resolveColor(pct, thresholds), [pct, thresholds]);

  const data = [{ name: "gauge", value: pct, fill: color }];

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: dims.w, height: dims.h }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="78%"
            outerRadius="100%"
            data={data}
            startAngle={180}
            endAngle={0}
            barSize={dims.w * 0.09}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: "var(--color-bg-300)" }}
              dataKey="value"
              cornerRadius={6}
              angleAxisId={0}
              animationBegin={0}
              animationDuration={900}
              isAnimationActive
            />
          </RadialBarChart>
        </ResponsiveContainer>

        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-end pb-1">
          <motion.span
            className={`font-semibold tabular text-fg-100 ${dims.font}`}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease: EASE_OUT_QUART, delay: 0.2 }}
          >
            {Math.round(value).toLocaleString("fr-FR")}
          </motion.span>
          {unit && <span className="text-[10px] text-fg-500">{unit}</span>}
        </div>
      </div>
      {label && <span className="mt-1 text-xs text-fg-400">{label}</span>}
    </div>
  );
}
