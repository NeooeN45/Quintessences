"use client";

import { useMemo } from "react";
import {
  AreaChart as RAreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

// --- Types ---

export interface AreaChartPoint {
  date: string;
  value: number;
}

export interface AreaChartProps {
  data: AreaChartPoint[];
  color?: string;
  height?: number;
  label?: string;
  loading?: boolean;
  error?: string | null;
}

// --- Constantes ---

const DEFAULT_COLOR = "var(--color-accent)";
const DATE_FMT = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

// --- Helpers ---

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : DATE_FMT.format(d);
}

// --- Tooltip personnalisé ---

interface TooltipPayload {
  value: number;
  payload: AreaChartPoint;
}

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0];
  return (
    <div className="rounded-md border border-border bg-bg-200 px-3 py-2 text-xs shadow-lg">
      <div className="text-fg-500">{formatDate(point.payload.date)}</div>
      <div className="mt-0.5 font-medium tabular text-fg-100">
        {point.value.toLocaleString("fr-FR")}
      </div>
    </div>
  );
}

// --- Composant ---

export default function AreaChart({
  data,
  color = DEFAULT_COLOR,
  height = 200,
  label,
  loading = false,
  error = null,
}: AreaChartProps) {
  const gradientId = useMemo(
    () => `area-grad-${Math.random().toString(36).slice(2, 9)}`,
    [],
  );

  if (loading) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-border bg-bg-100"
        style={{ height }}
      >
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-error/30 bg-error/5 text-xs text-error"
        style={{ height }}
      >
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-border bg-bg-100 text-xs text-fg-500"
        style={{ height }}
      >
        Aucune donnée
      </div>
    );
  }

  return (
    <div className="w-full">
      {label && (
        <div className="mb-2 text-xs font-medium text-fg-400">{label}</div>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RAreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.4} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border-light)"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 10, fill: "var(--color-fg-500)" }}
            stroke="var(--color-border-light)"
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "var(--color-fg-500)" }}
            stroke="var(--color-border-light)"
            width={40}
          />
          <RTooltip content={<ChartTooltip />} cursor={{ stroke: "var(--color-border-strong)", strokeWidth: 1 }} />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            animationDuration={900}
            animationBegin={0}
            isAnimationActive
          />
        </RAreaChart>
      </ResponsiveContainer>
    </div>
  );
}
