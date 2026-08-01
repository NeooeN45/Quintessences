"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

// --- Constantes ---

const API_URL = "http://localhost:8000";
const SESSION_KEY = "gsie_admin_session";

const LEVEL_COLORS: Record<number, { label: string; color: string }> = {
  1: { label: "Faible", color: "#22c55e" },
  2: { label: "Modéré", color: "#eab308" },
  3: { label: "Sévère", color: "#f97316" },
  4: { label: "Très sévère", color: "#ef4444" },
};

const HEX_SIZE = 22;
const HEX_W = HEX_SIZE * Math.sqrt(3);
const HEX_H = HEX_SIZE * 1.5;

// Grille hexagonale simplifiée des départements français métropolitains.
// col/ligne approximent la position géographique (Ouest→Est, Nord→Sud).
const DEP_GRID: { code: string; nom: string; col: number; row: number }[] = [
  { code: "29", nom: "Finistère", col: 0, row: 1 },
  { code: "22", nom: "Côtes-d'Armor", col: 1, row: 0 },
  { code: "56", nom: "Morbihan", col: 1, row: 2 },
  { code: "35", nom: "Ille-et-Vilaine", col: 2, row: 1 },
  { code: "50", nom: "Manche", col: 3, row: 0 },
  { code: "14", nom: "Calvados", col: 4, row: 0 },
  { code: "61", nom: "Orne", col: 4, row: 2 },
  { code: "53", nom: "Mayenne", col: 3, row: 2 },
  { code: "44", nom: "Loire-Atlantique", col: 2, row: 3 },
  { code: "49", nom: "Maine-et-Loire", col: 3, row: 3 },
  { code: "85", nom: "Vendée", col: 3, row: 4 },
  { code: "79", nom: "Deux-Sèvres", col: 4, row: 4 },
  { code: "17", nom: "Charente-Maritime", col: 4, row: 5 },
  { code: "16", nom: "Charente", col: 5, row: 5 },
  { code: "33", nom: "Gironde", col: 4, row: 6 },
  { code: "40", nom: "Landes", col: 3, row: 7 },
  { code: "64", nom: "Pyrénées-Atlantiques", col: 4, row: 8 },
  { code: "24", nom: "Dordogne", col: 5, row: 6 },
  { code: "47", nom: "Lot-et-Garonne", col: 5, row: 7 },
  { code: "31", nom: "Haute-Garonne", col: 6, row: 8 },
  { code: "65", nom: "Hautes-Pyrénées", col: 5, row: 8 },
  { code: "32", nom: "Gers", col: 6, row: 7 },
  { code: "82", nom: "Tarn-et-Garonne", col: 7, row: 6 },
  { code: "46", nom: "Lot", col: 6, row: 6 },
  { code: "48", nom: "Lozère", col: 7, row: 5 },
  { code: "30", nom: "Gard", col: 8, row: 5 },
  { code: "34", nom: "Hérault", col: 7, row: 6 },
  { code: "11", nom: "Aude", col: 7, row: 7 },
  { code: "66", nom: "Pyrénées-Orientales", col: 8, row: 7 },
  { code: "81", nom: "Tarn", col: 7, row: 5 },
  { code: "09", nom: "Ariège", col: 7, row: 8 },
  { code: "19", nom: "Corrèze", col: 6, row: 4 },
  { code: "23", nom: "Creuse", col: 6, row: 3 },
  { code: "87", nom: "Haute-Vienne", col: 5, row: 3 },
  { code: "36", nom: "Indre", col: 6, row: 2 },
  { code: "37", nom: "Indre-et-Loire", col: 5, row: 2 },
  { code: "41", nom: "Loir-et-Cher", col: 6, row: 1 },
  { code: "28", nom: "Eure-et-Loir", col: 5, row: 1 },
  { code: "27", nom: "Eure", col: 5, row: 0 },
  { code: "76", nom: "Seine-Maritime", col: 4, row: 1 },
  { code: "80", nom: "Somme", col: 6, row: 0 },
  { code: "60", nom: "Oise", col: 7, row: 0 },
  { code: "02", nom: "Aisne", col: 8, row: 0 },
  { code: "59", nom: "Nord", col: 9, row: 0 },
  { code: "62", nom: "Pas-de-Calais", col: 9, row: 1 },
  { code: "51", nom: "Marne", col: 8, row: 1 },
  { code: "08", nom: "Ardennes", col: 9, row: 1 },
  { code: "10", nom: "Aube", col: 8, row: 2 },
  { code: "52", nom: "Haute-Marne", col: 9, row: 2 },
  { code: "89", nom: "Yonne", col: 7, row: 2 },
  { code: "21", nom: "Côte-d'Or", col: 8, row: 3 },
  { code: "58", nom: "Nièvre", col: 7, row: 3 },
  { code: "71", nom: "Saône-et-Loire", col: 8, row: 4 },
  { code: "39", nom: "Jura", col: 9, row: 3 },
  { code: "25", nom: "Doubs", col: 10, row: 3 },
  { code: "70", nom: "Haute-Saône", col: 10, row: 2 },
  { code: "90", nom: "Territoire de Belfort", col: 11, row: 3 },
  { code: "68", nom: "Haut-Rhin", col: 11, row: 2 },
  { code: "67", nom: "Bas-Rhin", col: 10, row: 1 },
  { code: "57", nom: "Moselle", col: 10, row: 1 },
  { code: "54", nom: "Meurthe-et-Moselle", col: 10, row: 2 },
  { code: "55", nom: "Meuse", col: 9, row: 2 },
  { code: "88", nom: "Vosges", col: 11, row: 2 },
  { code: "18", nom: "Cher", col: 7, row: 1 },
  { code: "45", nom: "Loiret", col: 7, row: 1 },
  { code: "77", nom: "Seine-et-Marne", col: 8, row: 1 },
  { code: "78", nom: "Yvelines", col: 7, row: 0 },
  { code: "91", nom: "Essonne", col: 8, row: 0 },
  { code: "95", nom: "Val-d'Oise", col: 8, row: 0 },
  { code: "75", nom: "Paris", col: 8, row: 0 },
  { code: "92", nom: "Hauts-de-Seine", col: 8, row: 0 },
  { code: "93", nom: "Seine-Saint-Denis", col: 9, row: 0 },
  { code: "94", nom: "Val-de-Marne", col: 9, row: 0 },
  { code: "69", nom: "Rhône", col: 9, row: 4 },
  { code: "42", nom: "Loire", col: 9, row: 4 },
  { code: "43", nom: "Haute-Loire", col: 9, row: 5 },
  { code: "63", nom: "Puy-de-Dôme", col: 8, row: 4 },
  { code: "03", nom: "Allier", col: 8, row: 3 },
  { code: "15", nom: "Cantal", col: 8, row: 5 },
  { code: "07", nom: "Ardèche", col: 10, row: 5 },
  { code: "26", nom: "Drôme", col: 10, row: 4 },
  { code: "38", nom: "Isère", col: 11, row: 4 },
  { code: "73", nom: "Savoie", col: 12, row: 4 },
  { code: "74", nom: "Haute-Savoie", col: 12, row: 3 },
  { code: "01", nom: "Ain", col: 11, row: 3 },
  { code: "05", nom: "Hautes-Alpes", col: 11, row: 5 },
  { code: "04", nom: "Alpes-de-Haute-Provence", col: 11, row: 6 },
  { code: "06", nom: "Alpes-Maritimes", col: 11, row: 7 },
  { code: "83", nom: "Var", col: 10, row: 7 },
  { code: "13", nom: "Bouches-du-Rhône", col: 10, row: 6 },
  { code: "84", nom: "Vaucluse", col: 10, row: 5 },
  { code: "2A", nom: "Corse-du-Sud", col: 13, row: 8 },
  { code: "2B", nom: "Haute-Corse", col: 13, row: 7 },
];

// --- Types ---

interface DangerDep {
  dep_code: string;
  dep_nom: string;
  niveau_j1: number;
  niveau_j2: number;
}

interface HexCell {
  code: string;
  nom: string;
  cx: number;
  cy: number;
}

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

function hexPoints(cx: number, cy: number, size: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    pts.push(`${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`);
  }
  return pts.join(" ");
}

function hexCenter(col: number, row: number): { cx: number; cy: number } {
  const offset = row % 2 === 0 ? 0 : HEX_W / 2;
  return { cx: col * HEX_W + offset + HEX_W, cy: row * HEX_H + HEX_H };
}

// --- Composant ---

export default function MapPanel() {
  const [data, setData] = useState<DangerDep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hovered, setHovered] = useState<HexCell | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/climate/danger-feux`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: unknown = await res.json();
      if (!Array.isArray(json)) throw new Error("Format inattendu");
      setData(json as DangerDep[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const levelByCode = useMemo(() => {
    const map: Record<string, number> = {};
    for (const d of data) map[d.dep_code] = d.niveau_j1;
    return map;
  }, [data]);

  const cells: HexCell[] = useMemo(
    () =>
      DEP_GRID.map((d) => {
        const { cx, cy } = hexCenter(d.col, d.row);
        return { code: d.code, nom: d.nom, cx, cy };
      }),
    [],
  );

  const bounds = useMemo(() => {
    let maxCol = 0;
    let maxRow = 0;
    for (const d of DEP_GRID) {
      maxCol = Math.max(maxCol, d.col);
      maxRow = Math.max(maxRow, d.row);
    }
    return { width: (maxCol + 2) * HEX_W + HEX_W, height: (maxRow + 2) * HEX_H + HEX_H };
  }, []);

  const svgContainerRef = useRef<HTMLDivElement>(null);

  const handleHover = useCallback((cell: HexCell, e: React.PointerEvent) => {
    const rect = svgContainerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    setHovered(cell);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center rounded-xl border border-border bg-bg-100">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
          <p className="text-[13px] text-fg-400">Chargement des données de risque…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-border bg-bg-100 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-error/30 bg-error/10">
          <svg className="h-6 w-6 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <p className="mt-4 text-[14px] text-fg-300">Impossible de charger les données</p>
        <p className="mt-1 text-[12px] text-fg-500">{error}</p>
        <button
          onClick={() => {
            setLoading(true);
            void fetchData();
          }}
          className="mt-4 rounded-md border border-border bg-bg-200 px-4 py-2 text-[13px] text-fg-200 transition-colors hover:border-border-strong"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-bg-100 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-[14px] font-semibold text-fg-200">
          Danger feux par département — J+1
        </h2>
        <span className="font-mono text-[11px] text-fg-500">
          {data.length} départements
        </span>
      </div>

      <div ref={svgContainerRef} className="relative">
        <svg
          className="w-full"
          viewBox={`0 0 ${bounds.width} ${bounds.height}`}
          style={{ maxHeight: "560px" }}
        >
          {cells.map((cell, i) => {
            const level = levelByCode[cell.code] ?? 1;
            const meta = LEVEL_COLORS[level] ?? LEVEL_COLORS[1];
            return (
              <motion.g
                key={cell.code}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.008, duration: 0.3, ease: "easeOut" }}
                onPointerEnter={(e) => handleHover(cell, e)}
                onPointerMove={(e) => handleHover(cell, e)}
                onPointerLeave={() => setHovered(null)}
                style={{ cursor: "pointer" }}
              >
                <polygon
                  points={hexPoints(cell.cx, cell.cy, HEX_SIZE - 1.5)}
                  fill={meta.color}
                  fillOpacity={0.7}
                  stroke="var(--color-border)"
                  strokeWidth={1}
                  className="transition-all"
                />
                <text
                  x={cell.cx}
                  y={cell.cy + 3}
                  textAnchor="middle"
                  className="pointer-events-none select-none fill-white text-[8px] font-bold"
                >
                  {cell.code}
                </text>
              </motion.g>
            );
          })}
        </svg>

        {/* Tooltip */}
        {hovered && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg border border-border-strong bg-bg-300 px-3 py-2 text-[12px] text-fg-200 shadow-lg"
            style={{ left: tooltipPos.x + 12, top: tooltipPos.y + 12 }}
          >
            <div className="font-semibold text-fg-100">{hovered.nom}</div>
            <div className="mt-0.5 flex items-center gap-1.5 text-fg-400">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: LEVEL_COLORS[levelByCode[hovered.code] ?? 1].color }}
              />
              {LEVEL_COLORS[levelByCode[hovered.code] ?? 1].label}
            </div>
          </div>
        )}
      </div>

      {/* Légende */}
      <div className="mt-4 flex flex-wrap gap-4 border-t border-border pt-3">
        {(Object.entries(LEVEL_COLORS) as [string, typeof LEVEL_COLORS[number]][]).map(
          ([lvl, meta]) => (
            <div key={lvl} className="flex items-center gap-2 text-[12px] text-fg-300">
              <span
                className="h-3 w-3 rounded"
                style={{ backgroundColor: meta.color, opacity: 0.7 }}
              />
              Niveau {lvl} — {meta.label}
            </div>
          ),
        )}
      </div>
    </div>
  );
}
