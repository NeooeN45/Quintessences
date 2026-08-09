import { motion } from "framer-motion";

export interface HeadingLine {
  text: string;
  accent?: boolean;
}

interface Props {
  lines: HeadingLine[];
  size?: "hero" | "page";
  as?: "h1" | "h2";
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

const line = {
  hidden: { opacity: 0, y: "100%" },
  show: {
    opacity: 1,
    y: "0%",
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] },
  },
};

const SIZE_CLASS = {
  hero: "text-[13vw] leading-[0.94] sm:text-[6.5rem]",
  page: "text-[10vw] leading-[0.96] sm:text-6xl",
};

/**
 * Titre animé réutilisé sur toutes les pages — même syntaxe visuelle
 * que le hero (stagger + reveal vertical par ligne), implémentation
 * originale (Framer Motion). Un titre court n'anime qu'une ligne : on
 * ne remplit jamais artificiellement les lignes manquantes.
 */
export default function AnimatedHeading({ lines, size = "page", as = "h1" }: Props) {
  const Tag = motion[as];
  return (
    <Tag
      className={`font-medium tracking-tight text-[var(--color-fg-100)] ${SIZE_CLASS[size]}`}
      variants={container}
      initial="hidden"
      animate="show"
    >
      {lines.map((l, index) => (
        <span key={`${l.text}-${index}`} className="block overflow-hidden">
          <motion.span
            className="block"
            variants={line}
            style={l.accent ? { color: "var(--color-accent)" } : undefined}
          >
            {l.text}
          </motion.span>
        </span>
      ))}
    </Tag>
  );
}
