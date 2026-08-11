import { useEffect, useRef, useState } from "react";
import { loginPassword, friendlyErrorMessage } from "../lib/authApi.ts";

const TURNSTILE_SITE_KEY = "0x4AAAAAAEIpP0qaRpOz5IdW";

export default function LoginForm() {
  const widgetRef = useRef<HTMLDivElement>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    return () => {
      document.head.removeChild(script);
    };
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const turnstileToken =
      widgetRef.current?.querySelector<HTMLInputElement>('input[name="cf-turnstile-response"]')?.value ?? "";
    try {
      await loginPassword(String(form.get("email")), String(form.get("password")), turnstileToken);
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
          autoComplete="current-password"
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        />
      </div>

      <div ref={widgetRef} className="cf-turnstile" data-sitekey={TURNSTILE_SITE_KEY} />

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-full px-5 py-2.5 text-sm font-medium text-white transition-opacity disabled:opacity-60"
        style={{ background: "var(--color-fg-100)" }}
      >
        {submitting ? "Connexion…" : "Se connecter"}
      </button>

      {error && (
        <p role="alert" className="text-sm" style={{ color: "var(--color-error)" }}>
          {error}
        </p>
      )}

      <p className="text-center text-sm text-[var(--color-fg-400)]">
        Pas encore de compte ?{" "}
        <a href="/compte/inscription/" className="underline decoration-[var(--color-border-strong)] underline-offset-4">
          Créer un compte
        </a>
      </p>
    </form>
  );
}
