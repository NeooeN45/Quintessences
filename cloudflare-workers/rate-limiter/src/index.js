/**
 * Rate-limiter edge — Cloudflare Worker
 *
 * Objectif : bloquer les attaques par force brute et les scanners avant
 * qu'ils n'atteignent l'origine GSIE, en utilisant Cloudflare KV comme
 * stockage distribué de compteurs.
 *
 * Seuils (configurables via variables d'environnement) :
 * - /api/v1/auth/*  : 10 requêtes / minute / IP
 * - /api/v1/turnstile/* : 30 requêtes / minute / IP
 * - le reste         : 100 requêtes / minute / IP
 *
 * Si le Worker n'a pas accès à KV (absent ou quota épuisé), il laisse
 * passer la requête : le rate limiting applicatif (slowapi) reste le
 * garde-fou principal.
 */

const DEFAULT_LIMIT = 100;
const DEFAULT_WINDOW = 60;

const BUCKETS = [
  { prefix: "/api/v1/auth/", limit: 10, window: 60 },
  { prefix: "/api/v1/auth/turnstile/", limit: 30, window: 60 },
  { prefix: "/api/v1/", limit: 100, window: 60 },
];

function getBucket(pathname) {
  // Le plus spécifique d'abord
  for (const bucket of BUCKETS) {
    if (pathname.startsWith(bucket.prefix)) {
      return bucket;
    }
  }
  return { limit: DEFAULT_LIMIT, window: DEFAULT_WINDOW };
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const clientIP = request.headers.get("CF-Connecting-IP") || "unknown";
    const bucket = getBucket(url.pathname);

    if (env.RATE_LIMITS) {
      const now = Math.floor(Date.now() / 1000);
      const windowStart = Math.floor(now / bucket.window) * bucket.window;
      const key = `rate:${clientIP}:${url.hostname}:${bucket.prefix || "all"}:${windowStart}`;

      try {
        const current = Number(await env.RATE_LIMITS.get(key)) || 0;
        if (current >= bucket.limit) {
          return new Response(
            JSON.stringify({ detail: "Too Many Requests" }),
            {
              status: 429,
              headers: {
                "Content-Type": "application/json",
                "Retry-After": String(bucket.window),
                "X-RateLimit-Limit": String(bucket.limit),
                "X-RateLimit-Window": String(bucket.window),
              },
            },
          );
        }
        await env.RATE_LIMITS.put(key, String(current + 1), {
          expirationTtl: bucket.window * 2,
        });
      } catch (err) {
        // En cas d'indisponibilité KV, on ne bloque pas le trafic.
        // L'API conserve son propre rate limiting en dernier recours.
        console.error("rate-limiter-kv-error", { error: err.message });
      }
    }

    const response = await fetch(request);
    const newResponse = new Response(response.body, response);
    newResponse.headers.set("X-Rate-Limiter-Active", env.RATE_LIMITS ? "yes" : "no");
    newResponse.headers.set("X-Client-IP", clientIP);
    return newResponse;
  },
};
