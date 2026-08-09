import { motion } from "framer-motion";
import Skeleton from "./Skeleton.tsx";
import { APPS } from "../lib/apps.ts";

/**
 * Présentation détaillée des applications — une section par app,
 * capture d'écran en réserve (squelette, à remplacer quand les
 * captures existeront) et lien Google Play désactivé tant qu'aucune
 * app n'est publiée sur le store (aucun lien inventé).
 */
export default function ApplicationsList() {
  return (
    <div className="divide-y divide-[var(--color-border)]">
      {APPS.map((app, index) => (
        <motion.article
          key={app.slug}
          className="grid gap-8 py-16 md:grid-cols-2 md:items-center"
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className={index % 2 === 1 ? "md:order-2" : ""}>
            <div className="flex items-center gap-3">
              <img src={app.icon} alt="" aria-hidden="true" className="h-12 w-12 rounded-xl object-cover" />
              <span className="eyebrow" style={{ color: app.accent }}>
                {app.domain}
              </span>
            </div>
            <h2 className="mt-4 text-3xl font-medium tracking-tight text-[var(--color-fg-100)]">
              {app.name}
            </h2>
            <p className="mt-3 max-w-md text-[var(--color-fg-300)]">{app.summary}</p>

            <div className="mt-6 flex items-center gap-3">
              <span
                className="rounded-full border px-3 py-1 text-xs"
                style={{ borderColor: "var(--color-border-strong)", color: "var(--color-fg-400)" }}
              >
                {app.status === "disponible" ? "Disponible" : "Planifiée"}
              </span>

              {app.playStoreUrl ? (
                <a
                  href={app.playStoreUrl}
                  className="text-xs font-medium underline decoration-[var(--color-border-strong)] underline-offset-4 hover:text-[var(--color-fg-100)]"
                >
                  Disponible sur Google Play
                </a>
              ) : (
                <span className="text-xs text-[var(--color-fg-500)]">Bientôt sur Google Play</span>
              )}
            </div>
          </div>

          <div className={index % 2 === 1 ? "md:order-1" : ""}>
            <div className="relative aspect-[9/16] max-w-[280px] overflow-hidden rounded-2xl border border-[var(--color-border)] md:mx-auto">
              <Skeleton className="absolute inset-0 rounded-2xl" />
              <p className="absolute inset-x-0 bottom-4 text-center text-xs text-[var(--color-fg-500)]">
                Capture d'écran à venir
              </p>
            </div>
          </div>
        </motion.article>
      ))}
    </div>
  );
}
