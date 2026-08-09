import { useEffect, useState } from "react";

interface Props {
  label: string;
  /** Champ attendu dans la réponse JSON de l'endpoint public de stats. */
  field: string;
}

type State = { kind: "loading" } | { kind: "ok"; value: number } | { kind: "unavailable" };

// GSIE-F-006 : endpoint public d'agrégats non sensibles.
// Non livré à ce jour côté API (voir SITE_PUBLIC_ARCHITECTURE.md §3) —
// ce composant échoue donc systématiquement vers l'état "unavailable"
// tant que PUBLIC_STATS_API_URL n'est pas configuré, conformément à
// SITE-F-007 (jamais de valeur périmée présentée comme actuelle).
const STATS_URL = import.meta.env.PUBLIC_STATS_API_URL as string | undefined;

export default function LiveStat({ label, field }: Props) {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    if (!STATS_URL) {
      setState({ kind: "unavailable" });
      return;
    }

    fetch(STATS_URL)
      .then((res) => {
        if (!res.ok) throw new Error("réponse non OK");
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        const value = data?.[field];
        if (typeof value === "number") {
          setState({ kind: "ok", value });
        } else {
          setState({ kind: "unavailable" });
        }
      })
      .catch(() => {
        if (!cancelled) setState({ kind: "unavailable" });
      });

    return () => {
      cancelled = true;
    };
  }, [field]);

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-100)] p-5">
      <p className="text-2xl font-semibold tabular-nums text-[var(--color-fg-100)]">
        {state.kind === "ok" ? state.value.toLocaleString("fr-FR") : "—"}
      </p>
      <p className="mt-1 text-sm text-[var(--color-fg-400)]">{label}</p>
      {state.kind === "unavailable" && (
        <p className="mt-2 text-xs text-[var(--color-warning)]">Donnée indisponible</p>
      )}
    </div>
  );
}
