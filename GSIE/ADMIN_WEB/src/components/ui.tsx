import { useEffect, useRef, useState } from "react";
import { animate, useMotionValue, useTransform, motion } from "framer-motion";

/**
 * Compteur animé — count-up fluide avec easing.
 * Style : Vercel/Linear metrics.
 */
export function AnimatedCounter({
  value,
  duration = 1.2,
  format = (n: number) => Math.round(n).toLocaleString("fr-FR"),
  className = "",
}: {
  value: number;
  duration?: number;
  format?: (n: number) => string;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(0);
  const rounded = useTransform(motionValue, (latest) => format(latest));

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration,
      ease: [0.16, 1, 0.3, 1], // ease-out-quart
    });
    return controls.stop;
  }, [value, duration, motionValue]);

  useEffect(() => {
    return rounded.on("change", (v) => {
      if (ref.current) ref.current.textContent = v;
    });
  }, [rounded]);

  return (
    <span ref={ref} className={`tabular ${className}`}>
      {format(0)}
    </span>
  );
}

/**
 * Card avec hover lift + glow accent.
 */
export function HoverCard({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
      className={`rounded-lg border border-border bg-bg-100 transition-colors hover:border-border-strong ${className}`}
    >
      {children}
    </motion.div>
  );
}

/**
 * Skeleton avec shimmer — loading state.
 */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded bg-bg-300 ${className}`}
      style={{
        background:
          "linear-gradient(90deg, var(--color-bg-300) 0%, var(--color-bg-400) 50%, var(--color-bg-300) 100%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s infinite",
      }}
    >
      <style>{`@keyframes shimmer { 0% { background-position: 200% 0 } 100% { background-position: -200% 0 } }`}</style>
    </div>
  );
}

/**
 * Badge statut avec pulse animation pour les états actifs.
 */
export function StatusBadge({
  status,
  label,
}: {
  status: "healthy" | "degraded" | "unhealthy" | "unknown";
  label?: string;
}) {
  const colors = {
    healthy: { bg: "bg-accent/10", text: "text-accent", dot: "bg-accent" },
    degraded: { bg: "bg-warning/10", text: "text-warning", dot: "bg-warning" },
    unhealthy: { bg: "bg-error/10", text: "text-error", dot: "bg-error" },
    unknown: { bg: "bg-fg-500/10", text: "text-fg-400", dot: "bg-fg-500" },
  };
  const c = colors[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`}>
        {status === "healthy" && (
          <motion.span
            className="block h-full w-full rounded-full bg-accent"
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
      </span>
      {label ?? status}
    </span>
  );
}

/**
 * Toast notification — en bas à droite, auto-dismiss.
 */
export function Toast({
  message,
  type = "error",
  onClose,
}: {
  message: string;
  type?: "error" | "success" | "info";
  onClose: () => void;
}) {
  const colors = {
    error: "border-error/30 bg-error-bg text-error",
    success: "border-accent/30 bg-accent/10 text-accent",
    info: "border-border bg-bg-200 text-fg-200",
  };
  return (
    <motion.div
      initial={{ opacity: 0, x: 40, y: 0 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed bottom-6 right-6 z-50 rounded-lg border px-4 py-3 text-[13px] shadow-lg ${colors[type]}`}
    >
      <div className="flex items-center gap-3">
        <span>{message}</span>
        <button
          onClick={onClose}
          className="text-fg-500 hover:text-fg-100 transition-colors"
          aria-label="Fermer"
        >
          ×
        </button>
      </div>
    </motion.div>
  );
}

/**
 * Sparkline — mini line chart pour stat cards.
 */
export function Sparkline({
  data,
  color = "var(--color-accent)",
  width = 80,
  height = 24,
}: {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}) {
  if (data.length < 2) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");
  const areaPoints = `0,${height} ${points} ${width},${height}`;

  return (
    <svg width={width} height={height} className="overflow-visible">
      <motion.polygon
        points={areaPoints}
        fill={color}
        fillOpacity={0.1}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      />
      <motion.polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
      />
    </svg>
  );
}
