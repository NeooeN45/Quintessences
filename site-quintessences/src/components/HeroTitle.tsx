import { motion } from "framer-motion";

const WORDS = ["De", "la", "preuve", "à", "la", "décision", "du", "forestier."];

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.09, delayChildren: 0.1 },
  },
};

const line = {
  hidden: { opacity: 0, y: "100%" },
  show: {
    opacity: 1,
    y: "0%",
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
  },
};

/**
 * Titre du hero animé mot par mot à l'entrée — animation originale
 * (stagger + reveal vertical), pas une reprise du code d'un tiers.
 * Respecte prefers-reduced-motion via le CSS global (SITE-X-002).
 */
export default function HeroTitle() {
  return (
    <motion.h1
      className="text-[13vw] font-medium leading-[0.94] tracking-tight text-[var(--color-fg-100)] sm:text-[6.5rem]"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {WORDS.map((word, index) => (
        <span key={`${word}-${index}`} className="block overflow-hidden">
          <motion.span
            className="block"
            variants={line}
            style={word === "décision" ? { color: "var(--color-accent)" } : undefined}
          >
            {word}
          </motion.span>
        </span>
      ))}
    </motion.h1>
  );
}
