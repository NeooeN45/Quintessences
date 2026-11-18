const siteOrigin = (process.env.LIVE_SITE_ORIGIN || "https://quintessences-platform.com").replace(/\/+$/, "");
const apiOrigin = (process.env.LIVE_API_ORIGIN || "https://api.quintessences-platform.com").replace(/\/+$/, "");
const failures = [];

async function fetchLive(path, origin) {
  const url = `${origin}${path}`;
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(20_000) });
    return {
      url,
      status: response.status,
      headers: response.headers,
      body: await response.text(),
    };
  } catch (error) {
    failures.push(`${url} : requête impossible (${error.message})`);
    return null;
  }
}

function requireStatus(result, expected, label) {
  if (!result || result.status !== expected) {
    failures.push(`${label} : statut attendu ${expected}, obtenu ${result?.status ?? "inconnu"}`);
  }
}

function requireHeader(result, name, label) {
  if (!result?.headers.get(name)) {
    failures.push(`${label} : en-tête ${name} absent`);
  }
}

function requireContentType(result, expected, label) {
  const contentType = result?.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes(expected)) {
    failures.push(`${label} : Content-Type attendu ${expected}, obtenu ${contentType || "absent"}`);
  }
}

const root = await fetchLive("/", siteOrigin);
requireStatus(root, 200, "site public");
for (const header of [
  "content-security-policy",
  "referrer-policy",
  "permissions-policy",
  "x-frame-options",
  "x-content-type-options",
]) {
  requireHeader(root, header, "site public");
}

const robots = await fetchLive("/robots.txt", siteOrigin);
requireStatus(robots, 200, "robots.txt");
requireContentType(robots, "text/plain", "robots.txt");
if (!robots?.body.includes("Sitemap:")) failures.push("robots.txt : directive Sitemap absente");

const security = await fetchLive("/.well-known/security.txt", siteOrigin);
requireStatus(security, 200, "security.txt");
requireContentType(security, "text/plain", "security.txt");
for (const field of ["Contact:", "Expires:", "Canonical:"]) {
  if (!security?.body.includes(field)) failures.push(`security.txt : champ ${field} absent`);
}

const sitemap = await fetchLive("/sitemap.xml", siteOrigin);
requireStatus(sitemap, 200, "sitemap.xml");
requireContentType(sitemap, "xml", "sitemap.xml");

const apiHealth = await fetchLive("/health", apiOrigin);
requireStatus(apiHealth, 200, "API /health");

if (failures.length > 0) {
  console.error("Audit live échoué :");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("Audit live réussi : site, fichiers publics, headers et API sont cohérents.");
