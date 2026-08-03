"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

// --- Types ---

type NodeType = "concept" | "rule" | "observation" | "assertion";

interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  x: number;
  y: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// --- Constantes ---

const NODE_COLORS: Record<NodeType, { fill: string; stroke: string; label: string }> = {
  concept: { fill: "rgba(59,130,246,0.18)", stroke: "#3b82f6", label: "Concept" },
  rule: { fill: "rgba(168,85,247,0.18)", stroke: "#a855f7", label: "Règle" },
  observation: { fill: "rgba(34,197,94,0.18)", stroke: "#22c55e", label: "Observation" },
  assertion: { fill: "rgba(249,115,22,0.18)", stroke: "#f97316", label: "Assertion" },
};

const NODE_RADIUS = 28;

// --- Helpers ---

function bezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.hypot(dx, dy) || 1;
  const offset = Math.min(dist * 0.4, 80);
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const cx = mx - (dy / dist) * offset;
  const cy = my + (dx / dist) * offset;
  return `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
}

// --- Composant ---

export default function KnowledgeGraph({ nodes, edges }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>(
    () => Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }])),
  );
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState<{ type: "node" | "edge"; id: string } | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const panRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null);

  const nodeMap = useMemo(() => Object.fromEntries(nodes.map((n) => [n.id, n])), [nodes]);

  const resolvedEdges = useMemo(
    () =>
      edges
        .map((e) => {
          const s = positions[e.source];
          const t = positions[e.target];
          if (!s || !t) return null;
          return { ...e, sx: s.x, sy: s.y, tx: t.x, ty: t.y };
        })
        .filter((e): e is NonNullable<typeof e> => e !== null),
    [edges, positions],
  );

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.3, Math.min(3, z * delta)));
  }, []);

  const handlePanStart = useCallback((e: React.PointerEvent) => {
    if (e.target !== svgRef.current) return;
    panRef.current = { startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
  }, [pan]);

  const handlePanMove = useCallback((e: React.PointerEvent) => {
    if (!panRef.current) return;
    setPan({
      x: panRef.current.panX + (e.clientX - panRef.current.startX),
      y: panRef.current.panY + (e.clientY - panRef.current.startY),
    });
  }, []);

  const handlePanEnd = useCallback(() => {
    panRef.current = null;
  }, []);

  const handleNodeDrag = useCallback((id: string, dx: number, dy: number) => {
    setPositions((prev) => {
      const cur = prev[id];
      if (!cur) return prev;
      return { ...prev, [id]: { x: cur.x + dx / zoom, y: cur.y + dy / zoom } };
    });
  }, [zoom]);

  const showTooltip = useCallback(
    (type: "node" | "edge", id: string, e: React.PointerEvent) => {
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
      setHovered({ type, id });
    },
    [],
  );

  if (nodes.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-border bg-bg-100 text-center">
        <svg className="h-12 w-12 text-fg-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <circle cx="6" cy="6" r="3" />
          <circle cx="18" cy="18" r="3" />
          <path strokeLinecap="round" d="M8 8l8 8" strokeDasharray="2 2" />
        </svg>
        <p className="mt-4 text-[14px] text-fg-400">Graphe vide — ingérez des connaissances</p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-bg-100">
      <svg
        ref={svgRef}
        className="h-[560px] w-full cursor-grab active:cursor-grabbing"
        onWheel={handleWheel}
        onPointerDown={handlePanStart}
        onPointerMove={handlePanMove}
        onPointerUp={handlePanEnd}
        onPointerLeave={handlePanEnd}
      >
        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Arêtes */}
          {resolvedEdges.map((e, i) => {
            const id = `edge-${i}`;
            const isHovered = hovered?.type === "edge" && hovered.id === id;
            return (
              <g key={id}>
                <path
                  d={bezierPath(e.sx, e.sy, e.tx, e.ty)}
                  fill="none"
                  stroke={isHovered ? "var(--color-accent)" : "var(--color-border-strong)"}
                  strokeWidth={isHovered ? 2 : 1.2}
                  className="cursor-pointer transition-colors"
                  onPointerEnter={(ev) => showTooltip("edge", id, ev)}
                  onPointerMove={(ev) => showTooltip("edge", id, ev)}
                  onPointerLeave={() => setHovered(null)}
                />
                {e.label && (
                  <text
                    x={(e.sx + e.tx) / 2}
                    y={(e.sy + e.ty) / 2 - 4}
                    textAnchor="middle"
                    className="pointer-events-none fill-fg-500 text-[10px]"
                  >
                    {e.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nœuds */}
          {nodes.map((n) => {
            const pos = positions[n.id];
            if (!pos) return null;
            const colors = NODE_COLORS[n.type] ?? NODE_COLORS.concept;
            const isHovered = hovered?.type === "node" && hovered.id === n.id;
            return (
              <motion.g
                key={n.id}
                drag
                dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
                onDrag={(_, info) => handleNodeDrag(n.id, info.delta.x, info.delta.y)}
                dragElastic={0}
                dragMomentum={false}
                style={{ cursor: "grab" }}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={NODE_RADIUS}
                  fill={colors.fill}
                  stroke={colors.stroke}
                  strokeWidth={isHovered ? 2.5 : 1.5}
                  className="cursor-pointer transition-all"
                  onPointerEnter={(ev) => showTooltip("node", n.id, ev)}
                  onPointerMove={(ev) => showTooltip("node", n.id, ev)}
                  onPointerLeave={() => setHovered(null)}
                />
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  className="pointer-events-none select-none fill-fg-200 text-[11px] font-medium"
                >
                  {n.label.length > 14 ? `${n.label.slice(0, 13)}…` : n.label}
                </text>
              </motion.g>
            );
          })}
        </g>
      </svg>

      {/* Tooltip */}
      {hovered && (
        <div
          className="pointer-events-none absolute z-10 max-w-xs rounded-lg border border-border-strong bg-bg-300 px-3 py-2 text-[12px] text-fg-200 shadow-lg"
          style={{ left: tooltipPos.x + 12, top: tooltipPos.y + 12 }}
        >
          {hovered.type === "node"
            ? (() => {
                const n = nodeMap[hovered.id];
                return n ? (
                  <div>
                    <div className="font-semibold text-fg-100">{n.label}</div>
                    <div className="mt-0.5 text-fg-400">
                      {NODE_COLORS[n.type]?.label ?? n.type}
                    </div>
                  </div>
                ) : null;
              })()
            : (() => {
                const e = resolvedEdges[parseInt(hovered.id.replace("edge-", ""), 10)];
                return e ? (
                  <div>
                    <div className="font-semibold text-fg-100">{e.label ?? "Arête"}</div>
                    <div className="mt-0.5 text-fg-400">
                      {nodeMap[e.source]?.label} → {nodeMap[e.target]?.label}
                    </div>
                  </div>
                ) : null;
              })()}
        </div>
      )}

      {/* Légende */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-3 rounded-lg border border-border bg-bg-200/90 px-3 py-2 backdrop-blur">
        {(Object.entries(NODE_COLORS) as [NodeType, typeof NODE_COLORS[NodeType]][]).map(
          ([type, c]) => (
            <div key={type} className="flex items-center gap-1.5 text-[11px] text-fg-300">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: c.stroke }}
              />
              {c.label}
            </div>
          ),
        )}
      </div>

      {/* Contrôles zoom */}
      <div className="absolute right-3 top-3 flex flex-col gap-1">
        <button
          onClick={() => setZoom((z) => Math.min(3, z * 1.2))}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-bg-200 text-fg-300 transition-colors hover:bg-bg-300"
          aria-label="Zoom +"
        >
          +
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(0.3, z * 0.8))}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-bg-200 text-fg-300 transition-colors hover:bg-bg-300"
          aria-label="Zoom -"
        >
          −
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-bg-200 text-[10px] text-fg-300 transition-colors hover:bg-bg-300"
          aria-label="Réinitialiser"
        >
          ⟲
        </button>
      </div>
    </div>
  );
}
