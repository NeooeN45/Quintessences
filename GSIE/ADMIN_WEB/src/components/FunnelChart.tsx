"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";

// --- Types ---

interface FunnelStage {
  name: string;
  value: number;
  color?: string;
}

interface Props {
  stages: FunnelStage[];
}

// --- Helpers -----

function lerpColor(a: string, b: string, t: number): string {
  const pa = parseInt(a.slice(1), 16);
  const pb = parseInt(b.slice(1), 16);
  const ar = (pa >> 16) & 0xff;
  const ag = (pa >> 8) & 0xff;
  const ab = pa & 0xff;
  const br = (pb >> 16) & 0xff;
  const bg = (pb >> 8) & 0xff;
  const bb = pb & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return `#${((r << 16) | (g << 8) | bl).toString(16).padStart(6, "0")}`;
}

const COLOR_START = "#22c55e";
const COLOR_END = "#ef4444";

// --- Composant ---

export default function FunnelChart({ stages }: Props) {
  const [hovered, setHovered] = useState<number | null>(null);

  const total = useMemo(() => stages.reduce((s, st) => s + st.value, 0), [stages]);
  const maxValue = useMemo(() => stages.reduce((m, st) => Math.max(m, st.value), 0), [stages]);

  const rows = useMemo(() => {
    return stages.map((stage, i) => {
      const prev = i > 0 ? stages[i - 1].value : stage.value;
      const dropOff = i > 0 && prev > 0 ? ((prev - stage.value) / prev) * 100 : 0;
      const pctTotal = total > 0 ? (stage.value / total) * 100 : 0;
      const widthPct = maxValue > 0 ? (stage.value / maxValue) * 100 : 0;
      const color = stage.color ?? lerpColor(COLOR_START, COLOR_END, stages.length > 1 ? i / (stages.length - 1) : 0);
      return { ...stage, index: i, dropOff, pctTotal, widthPct, color };
    });
  }, [stages, total, maxValue]);

  if (stages.length === 0) {
    return (
      <div className="flex min-h-[200px] items-center justify-center rounded-xl border border-border bg-bg-100 text-[13px] text-fg-400">
        Aucune donnée à afficher
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {rows.map((row) => (
        <div key={row.index} className="space-y-0.5">
          {/* Drop-off */}
          {row.index > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: row.index * 0.15 + 0.05 }}
              className="flex items-center gap-2 pl-2 text-[11px] text-fg-500"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
              <span>
                Drop-off : <span className="text-fg-400">−{row.dropOff.toFixed(1)}%</span>
              </span>
            </motion.div>
          )}

          {/* Barre */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: row.index * 0.15, duration: 0.4, ease: "easeOut" }}
            className="flex items-center gap-3"
            onPointerEnter={() => setHovered(row.index)}
            onPointerLeave={() => setHovered(null)}
          >
            <div className="w-28 shrink-0 truncate text-right text-[12px] font-medium text-fg-300">
              {row.name}
            </div>
            <div className="relative h-9 flex-1 overflow-hidden rounded-md bg-bg-200">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${row.widthPct}%` }}
                transition={{ delay: row.index * 0.15 + 0.1, duration: 0.5, ease: "easeOut" }}
                className="flex h-full items-center justify-end rounded-md pr-3"
                style={{
                  background: `linear-gradient(90deg, ${row.color}88, ${row.color})`,
                }}
              >
                <span className="text-[12px] font-semibold text-white drop-shadow">
                  {row.value.toLocaleString("fr-FR")}
                </span>
              </motion.div>

              {/* Tooltip */}
              {hovered === row.index && (
                <div className="absolute right-0 top-full z-10 mt-1 rounded-lg border border-border-strong bg-bg-300 px-3 py-2 text-[12px] text-fg-200 shadow-lg">
                  <div className="font-semibold text-fg-100">{row.name}</div>
                  <div className="mt-0.5 text-fg-400">
                    Valeur : <span className="text-fg-200">{row.value.toLocaleString("fr-FR")}</span>
                  </div>
                  <div className="text-fg-400">
                    Du total : <span className="text-fg-200">{row.pctTotal.toFixed(1)}%</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      ))}
    </div>
  );
}
