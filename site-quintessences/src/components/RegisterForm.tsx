import { useState } from "react";
import { register, friendlyErrorMessage } from "../lib/authApi.ts";

export default function RegisterForm() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      await register(
        String(form.get("email")),
        String(form.get("password")),
        String(form.get("display_name") || ""),
      );
      window.location.href = "/compte/";
    } catch (err) {
      setError(friendlyErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="mx-auto max-w-sm space-y-4">
      <div>
        <label htmlFor="display_name" className="block text-sm font-medium text-[var(--color-fg-200)]">
          Nom affiché
        </label>
        <input
          id="display_name"
          name="display_name"
          type="text"
          autoComplete="name"
          maxLength={200}
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        />
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-[var(--color-fg-200)]">
          Adresse e-mail
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-[var(--color-fg-200)]">
          Mot de passe
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={12}
          maxLength={128}
          autoComplete="new-password"
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        />
        <p className="mt-1.5 text-xs text-[var(--color-fg-500)]">12 caractères minimum.</p>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-full px-5 py-2.5 text-sm font-medium text-white transition-opacity disabled:opacity-60"
        style={{ background: "var(--color-fg-100)" }}
      >
        {submitting ? "Création…" : "Créer mon compte"}
      </button>

      {error && (
        <p role="alert" className="text-sm" style={{ color: "var(--color-error)" }}>
          {error}
        </p>
      )}

      <p className="text-center text-sm text-[var(--color-fg-400)]">
        Déjà un compte ?{" "}
        <a href="/compte/connexion/" className="underline decoration-[var(--color-border-strong)] underline-offset-4">
          Se connecter
        </a>
      </p>
    </form>
  );
}
