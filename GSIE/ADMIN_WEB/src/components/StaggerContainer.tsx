"use client";

import { type ReactNode, type ElementType } from "react";
import { motion, type Variants } from "framer-motion";

// --- Constantes ---

const EASE_OUT_QUART: [number, number, number, number] = [0.16, 1, 0.3, 1];

export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: EASE_OUT_QUART },
  },
};

// --- Types ---

export interface StaggerContainerProps {
  children: ReactNode;
  className?: string;
  stagger?: number;
  as?: ElementType;
  delayChildren?: number;
}

// --- Composant ---

export default function StaggerContainer({
  children,
  className = "",
  stagger = 0.08,
  as = "div",
  delayChildren = 0,
}: StaggerContainerProps) {
  const MotionTag = motion[as as keyof typeof motion] as typeof motion.div;

  const containerVariants: Variants = {
    hidden: {},
    visible: {
      transition: { staggerChildren: stagger, delayChildren },
    },
  };

  return (
    <MotionTag
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {children}
    </MotionTag>
  );
}
