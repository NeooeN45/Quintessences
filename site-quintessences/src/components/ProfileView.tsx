import { useEffect, useState } from "react";
import { getSession, getProfile, logout, type Profile } from "../lib/authApi.ts";
import Skeleton from "./Skeleton.tsx";

type State =
  | { kind: "checking" }
  | { kind: "anonymous" }
  | { kind: "loaded"; profile: Profile }
  | { kind: "error" };

export default function ProfileView() {
  const [state, setState] = useState<State>({ kind: "checking" });

  useEffect(() => {
    if (!getSession()) {
      setState({ kind: "anonymous" });
      return;
    }
    getProfile()
      .then((profile) => setState({ kind: "loaded", profile }))
      .catch(() => setState({ kind: "error" }));
  }, []);

  if (state.kind === "checking") {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-4 w-52" />
      </div>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <div className="rounded-xl border border-dashed border-[var(--color-border)] p-10 text-center">
        <p className="text-[var(--color-fg-300)]">Vous n'êtes pas connecté.</p>
        <div className="mt-6 flex justify-center gap-3">
          <a
            href="/compte/connexion/"
            className="rounded-full px-5 py-2.5 text-sm font-medium text-white"
            style={{ background: "var(--color-fg-100)" }}
          >
            Se connecter
          </a>
          <a
            href="/compte/inscription/"
            className="rounded-full border border-[var(--color-border-strong)] px-5 py-2.5 text-sm font-medium text-[var(--color-fg-200)]"
          >
            Créer un compte
          </a>
        </div>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="rounded-xl border border-[var(--color-border)] p-10 text-center">
        <p style={{ color: "var(--color-error)" }}>
          Impossible de charger votre profil. Votre session a peut-être expiré.
        </p>
        <a
          href="/compte/connexion/"
          className="mt-4 inline-block underline decoration-[var(--color-border-strong)] underline-offset-4"
        >
          Se reconnecter
        </a>
      </div>
    );
  }

  const { profile } = state;

  return (
    <div className="max-w-md">
      <p className="eyebrow">Compte</p>
      <p className="mt-2 text-2xl font-medium text-[var(--color-fg-100)]">
        {profile.display_name || profile.email || "Compte Quintessences"}
      </p>

      <dl className="mt-6 divide-y divide-[var(--color-border)] border-y border-[var(--color-border)]">
        <div className="flex justify-between py-3">
          <dt className="text-sm text-[var(--color-fg-400)]">E-mail</dt>
          <dd className="text-sm text-[var(--color-fg-200)]">{profile.email ?? "—"}</dd>
        </div>
        <div className="flex justify-between py-3">
          <dt className="text-sm text-[var(--color-fg-400)]">E-mail vérifié</dt>
          <dd className="text-sm text-[var(--color-fg-200)]">{profile.email_verified ? "Oui" : "Non"}</dd>
        </div>
        <div className="flex justify-between py-3">
          <dt className="text-sm text-[var(--color-fg-400)]">Fournisseurs</dt>
          <dd className="text-sm text-[var(--color-fg-200)]">{profile.providers.join(", ") || "—"}</dd>
        </div>
        <div className="flex justify-between py-3">
          <dt className="text-sm text-[var(--color-fg-400)]">Rôles</dt>
          <dd className="text-sm text-[var(--color-fg-200)]">{profile.roles.join(", ") || "—"}</dd>
        </div>
      </dl>

      <button
        type="button"
        onClick={() => logout().then(() => window.location.reload())}
        className="mt-8 rounded-full border border-[var(--color-border-strong)] px-5 py-2.5 text-sm font-medium text-[var(--color-fg-200)] transition-colors hover:border-[var(--color-fg-100)]"
      >
        Se déconnecter
      </button>
    </div>
  );
}
