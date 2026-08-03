"use client";

import { useRef, type ReactNode } from "react";
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  type MotionValue,
} from "framer-motion";

const SPRING_CONFIG = { stiffness: 150, damping: 20, mass: 0.5 };

interface ParallaxCardProps {
  children: ReactNode;
  className?: string;
  intensity?: number;
}

export default function ParallaxCard({
  children,
  className = "",
  intensity = 8,
}: ParallaxCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const reduceMotion = usePrefersReducedMotion();

  const rotateX = useSpring(useMotionValue(0), SPRING_CONFIG);
  const rotateY = useSpring(useMotionValue(0), SPRING_CONFIG);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (reduceMotion || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    rotateY.set(px * intensity);
    rotateX.set(-py * intensity);
  };

  const handleMouseLeave = () => {
    rotateX.set(0);
    rotateY.set(0);
  };

  if (reduceMotion) {
    return (
      <div className={`rounded-lg border border-border bg-bg-100 ${className}`}>
        {children}
      </div>
    );
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: "preserve-3d",
        perspective: 1000,
      }}
      className={`rounded-lg border border-border bg-bg-100 transition-colors hover:border-border-strong ${className}`}
    >
      {children}
    </motion.div>
  );
}

function usePrefersReducedMotion(): boolean {
  const ref = useRef(false);
  if (typeof window !== "undefined") {
    ref.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }
  return ref.current;
}

export function ParallaxLayer({
  children,
  depth = 0,
  className = "",
}: {
  children: ReactNode;
  depth?: number;
  className?: string;
}) {
  const reduceMotion = usePrefersReducedMotion();
  if (reduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      style={{ transform: `translateZ(${depth}px)` }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export type { MotionValue };
