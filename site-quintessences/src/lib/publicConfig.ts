// Configuration publique du site, sans secret côté navigateur.

const configuredOrigin = import.meta.env.PUBLIC_API_ORIGIN?.trim();
const defaultOrigin = import.meta.env.DEV
  ? "http://localhost:4000"
  : "https://api.quintessences-platform.com";

export const PUBLIC_API_ORIGIN = (configuredOrigin || defaultOrigin).replace(/\/+$/, "");
export const PUBLIC_API_V1 = `${PUBLIC_API_ORIGIN}/api/v1`;

// La zone Compte reste fermée par défaut tant que la session web n'est pas
// alignée sur IDENTITE-001 (notamment stockage et protection contre XSS/CSRF).
export const PUBLIC_ACCOUNT_ENABLED = import.meta.env.PUBLIC_ACCOUNT_ENABLED === "true";
