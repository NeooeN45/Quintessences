import { motion } from "framer-motion";

/**
 * Chaîne d'intelligence GSIE — SITE-F-002, moment d'interaction SITE-002 §5.2.
 * Chaque étape s'anime à son entrée dans le viewport (whileInView), avec
 * une micro-explication. Respecte prefers-reduced-motion via le CSS global.
 */
const STEPS = [
  {
    name: "Evidence",
    description: "Qualifie la preuve scientifique en amont — matrice de décision A à F.",
  },
  {
    name: "Knowledge",
    description: "Centralise les connaissances qualifiées, versionnées et sourcées.",
  },
  {
    name: "Correlation",
    description: "Recherche des corrélations multiparamètres entre connaissances.",
  },
  {
    name: "Reasoning",
    description: "Applique un raisonnement explicable sur les corrélations retenues.",
  },
  {
    name: "Diagnostic",
    description: "Produit un diagnostic stationnel traçable jusqu'à sa preuve d'origine.",
  },
  {
    name: "Recommendation",
    description: "Formule une recommandation explicable et toujours contournable.",
  },
  {
    name: "Validation",
    description: "Valide la sortie avant qu'elle n'atteigne le forestier, décideur final.",
  },
];

export default function EngineChain() {
  return (
    <ol className="relative border-l border-[var(--color-border)] pl-6">
      {STEPS.map((step, index) => (
        <motion.li
          key={step.name}
          className="relative mb-8 last:mb-0"
          initial={{ opacity: 0, x: -12 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.35, delay: index * 0.04 }}
        >
          <span
            className="absolute -left-[31px] top-1 h-3 w-3 rounded-full border-2"
            style={{ borderColor: "var(--color-signature)", background: "var(--color-bg-000)" }}
            aria-hidden="true"
          />
          <p className="font-mono text-sm text-[var(--color-fg-100)]">
            <span className="text-[var(--color-fg-500)]">{String(index + 1).padStart(2, "0")}</span> {step.name}
          </p>
          <p className="mt-1 max-w-xl text-sm text-[var(--color-fg-400)]">{step.description}</p>
        </motion.li>
      ))}
      <motion.li
        initial={{ opacity: 0, x: -12 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.35, delay: STEPS.length * 0.04 }}
        className="relative"
      >
        <span
          className="absolute -left-[31px] top-1 h-3 w-3 rounded-full"
          style={{ background: "var(--color-signature)" }}
          aria-hidden="true"
        />
        <p className="font-mono text-sm font-medium text-[var(--color-fg-100)]">Forestier</p>
        <p className="mt-1 max-w-xl text-sm text-[var(--color-fg-400)]">
          Décideur final (GSIE-CON-001). L'IA assiste, ne décide jamais seule.
        </p>
      </motion.li>
    </ol>
  );
}
