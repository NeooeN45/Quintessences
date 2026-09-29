import { useEffect, useRef, useState, type SyntheticEvent } from "react";

import { PUBLIC_API_V1, PUBLIC_TURNSTILE_SITE_KEY } from "../lib/publicConfig";

// Migration directe du formulaire de landing-quintessences/ (DEC-000055).
const CONTACT_URL = `${PUBLIC_API_V1}/public/contact`;

const CATEGORIES = [
  { value: "partenariat", label: "Partenariat" },
  { value: "presse", label: "Presse" },
  { value: "securite", label: "Signalement de sécurité" },
  { value: "support", label: "Support" },
  { value: "autre", label: "Autre" },
];

declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => void;
    };
  }
}

export default function ContactForm() {
  const widgetRef = useRef<HTMLDivElement>(null);
  const [feedback, setFeedback] = useState<{ message: string; isError: boolean } | null>(null);
  const [submitting, setSubmitting] = useState(false);

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

  function getToken(): string {
    const input = widgetRef.current?.querySelector<HTMLInputElement>(
      'input[name="cf-turnstile-response"]',
    );
    return input?.value?.trim() ?? "";
  }

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFeedback(null);
    const token = getToken();
    const form = event.currentTarget;
    const formData = new FormData(form);

    try {
      if (!token) {
        throw new Error("Veuillez valider le défi Turnstile.");
      }
      const response = await fetch(CONTACT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.get("email"),
          category: formData.get("category"),
          message: formData.get("message"),
          turnstile_token: token,
          website: formData.get("website") ?? "",
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Le service de contact est temporairement indisponible. Écrivez directement à contact@quintessences-platform.com.",
        );
      }
      setFeedback({
        message: "Votre message a bien été transmis. Une réponse vous sera envoyée à cette adresse.",
        isError: false,
      });
      form.reset();
    } catch (err) {
      setFeedback({
        message: err instanceof Error ? err.message : "Une erreur est survenue.",
        isError: true,
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-lg space-y-4">
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
          placeholder="vous@exemple.com"
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        />
      </div>

      <div aria-hidden="true" className="sr-only">
        <label htmlFor="website">Ne pas remplir ce champ</label>
        <input id="website" name="website" type="text" tabIndex={-1} autoComplete="off" />
      </div>

      <div>
        <label htmlFor="category" className="block text-sm font-medium text-[var(--color-fg-200)]">
          Catégorie
        </label>
        <select
          id="category"
          name="category"
          required
          defaultValue=""
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        >
          <option value="" disabled>
            Choisir une catégorie
          </option>
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="message" className="block text-sm font-medium text-[var(--color-fg-200)]">
          Message
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          placeholder="Votre message…"
          className="mt-1.5 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-100)] px-3 py-2 text-sm text-[var(--color-fg-100)] outline-none focus-visible:border-[var(--color-signature)]"
        />
      </div>

      <div ref={widgetRef} className="cf-turnstile" data-sitekey={PUBLIC_TURNSTILE_SITE_KEY} />

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md px-5 py-2.5 text-sm font-medium text-white transition-opacity disabled:opacity-60"
        style={{ background: "var(--color-signature)" }}
      >
        {submitting ? "Envoi…" : "Envoyer"}
      </button>

      {feedback && (
        <p
          role="status"
          aria-live="polite"
          className="text-sm"
          style={{ color: feedback.isError ? "var(--color-error)" : "var(--color-success)" }}
        >
          {feedback.message}
        </p>
      )}
    </form>
  );
}
