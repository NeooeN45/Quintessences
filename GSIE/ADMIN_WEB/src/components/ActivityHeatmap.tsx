"use client";

import { useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

// --- Types ---

export interface HeatmapPoint {
  date: string;
  count: number;
}

export interface ActivityHeatmapProps {
  data: HeatmapPoint[];
  weeks?: number;
  loading?: boolean;
  error?: string | null;
}

// --- Constantes ---

const DEFAULT_WEEKS = 12;
const CELL_SIZE = 13;
const CELL_GAP = 3;
const DAY_LABELS = ["L", "M", "M", "J", "V", "S", "D"];
const VISIBLE_DAY_ROWS = [1, 3, 5]; // L, J, S (indices de jour dans la semaine, lundi=0)
const EASE_OUT_QUART: [number, number, number, number] = [0.16, 1, 0.3, 1];
const DATE_FMT = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

// --- Helpers ---

/** Convertit un ISO string en clé de jour YYYY-MM-DD. */
function dayKey(iso: string): string {
  const d = new Date(iso);
  d.setHours(0, 0, 0, 0);
  return d.toISOString().slice(0, 10);
}

/** Index du jour dans la semaine (lundi=0 ... dimanche=6). */
function dayOfWeek(iso: string): number {
  const d = new Date(iso).getDay();
  return d === 0 ? 6 : d - 1;
}

/** Construit une grille semaines × 7 jours à partir des données. */
function buildGrid(
  data: HeatmapPoint[],
  weeks: number,
): { cells: (HeatmapPoint | null)[][]; maxCount: number } {
  const map = new Map<string, number>();
  for (const p of data) {
    const key = dayKey(p.date);
    map.set(key, (map.get(key) ?? 0) + p.count);
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const totalDays = weeks * 7;
  const start = new Date(today);
  start.setDate(start.getDate() - totalDays + 1);

  const grid: (HeatmapPoint | null)[][] = [];
  let maxCount = 0;

  for (let w = 0; w < weeks; w++) {
    const column: (HeatmapPoint | null)[] = [];
    for (let d = 0; d < 7; d++) {
      const cellDate = new Date(start);
      cellDate.setDate(start.getDate() + w * 7 + d);
      const key = cellDate.toISOString().slice(0, 10);
      const count = map.get(key);
      if (cellDate > today) {
        column.push(null);
      } else if (count !== undefined) {
        maxCount = Math.max(maxCount, count);
        column.push({ date: cellDate.toISOString(), count });
      } else {
        column.push({ date: cellDate.toISOString(), count: 0 });
      }
    }
    grid.push(column);
  }

  return { cells: grid, maxCount: maxCount || 1 };
}

/** Retourne la couleur d'une cellule selon l'intensité (0-4). */
function cellColor(intensity: number): string {
  if (intensity === 0) return "var(--color-bg-300)";
  const opacity = 0.25 + intensity * 0.1875;
  return `rgba(34, 197, 94, ${opacity.toFixed(2)})`;
}

function intensityFor(count: number, max: number): number {
  if (count === 0) return 0;
  const ratio = count / max;
  if (ratio < 0.25) return 1;
  if (ratio < 0.5) return 2;
  if (ratio < 0.75) return 3;
  return 4;
}

// --- Tooltip ---

function CellTooltip({
  point,
  x,
  y,
}: {
  point: HeatmapPoint;
  x: number;
  y: number;
}) {
  return (
    <div
      className="pointer-events-none absolute z-20 rounded-md border border-border bg-bg-200 px-2.5 py-1.5 text-xs shadow-lg"
      style={{ left: x, top: y, transform: "translate(-50%, -110%)" }}
    >
      <div className="text-fg-500">{DATE_FMT.format(new Date(point.date))}</div>
      <div className="font-medium tabular text-fg-100">
        {point.count} activité{point.count > 1 ? "s" : ""}
      </div>
    </div>
  );
}

// --- Composant ---

export default function ActivityHeatmap({
  data,
  weeks = DEFAULT_WEEKS,
  loading = false,
  error = null,
}: ActivityHeatmapProps) {
  const [hovered, setHovered] = useState<{
    point: HeatmapPoint;
    x: number;
    y: number;
  } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  const { cells, maxCount } = useMemo(
    () => buildGrid(data, weeks),
    [data, weeks],
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-border bg-bg-100 p-8">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-error/30 bg-error/5 p-8 text-xs text-error">
        {error}
      </div>
    );
  }

  const gridWidth = weeks * (CELL_SIZE + CELL_GAP);
  const gridHeight = 7 * (CELL_SIZE + CELL_GAP);

  return (
    <div className="w-full">
      <div className="flex items-start gap-2">
        {/* Labels de jours */}
        <div className="flex flex-col gap-[3px] pt-0.5 text-[9px] text-fg-500">
          {DAY_LABELS.map((lbl, i) => (
            <div
              key={i}
              style={{ height: CELL_SIZE, lineHeight: `${CELL_SIZE}px` }}
              className={VISIBLE_DAY_ROWS.includes(i) ? "opacity-100" : "opacity-0"}
            >
              {lbl}
            </div>
          ))}
        </div>

        {/* Grille */}
        <div
          className="relative"
          ref={gridRef}
          onMouseLeave={() => setHovered(null)}
        >
          <svg width={gridWidth} height={gridHeight} className="overflow-visible">
            {cells.map((column, wIdx) =>
              column.map((point, dIdx) => {
                if (!point) return null;
                const intensity = intensityFor(point.count, maxCount);
                const x = wIdx * (CELL_SIZE + CELL_GAP);
                const y = dIdx * (CELL_SIZE + CELL_GAP);
                const cellIndex = wIdx * 7 + dIdx;
                return (
                  <motion.rect
                    key={`${wIdx}-${dIdx}`}
                    x={x}
                    y={y}
                    width={CELL_SIZE}
                    height={CELL_SIZE}
                    rx={2.5}
                    fill={cellColor(intensity)}
                    initial={{ opacity: 0, scale: 0.4 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{
                      duration: 0.3,
                      ease: EASE_OUT_QUART,
                      delay: Math.min(cellIndex * 0.006, 0.8),
                    }}
                    style={{ transformOrigin: `${x + CELL_SIZE / 2}px ${y + CELL_SIZE / 2}px` }}
                    onMouseEnter={() => {
                      const parent = gridRef.current;
                      if (!parent) return;
                      const px = x + CELL_SIZE / 2;
                      const py = y;
                      setHovered({ point, x: px, y: py });
                    }}
                    className="cursor-pointer transition-opacity hover:opacity-80"
                  />
                );
              }),
            )}
          </svg>

          {hovered && <CellTooltip point={hovered.point} x={hovered.x} y={hovered.y} />}
        </div>
      </div>

      {/* Légende */}
      <div className="mt-3 flex items-center gap-1.5 text-[10px] text-fg-500">
        <span>Moins</span>
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            style={{
              width: CELL_SIZE - 2,
              height: CELL_SIZE - 2,
              background: cellColor(i),
            }}
            className="rounded-[2px]"
          />
        ))}
        <span>Plus</span>
      </div>
    </div>
  );
}
