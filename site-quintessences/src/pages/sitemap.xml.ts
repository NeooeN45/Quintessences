import { getCollection } from "astro:content";

const SITE = "https://quintessences-platform.com";
const STATIC_ROUTES = [
  "/",
  "/applications/",
  "/actualites/",
  "/contact/",
  "/galerie/",
  "/mentions-legales/",
  "/confidentialite/",
  "/cgu/",
];

function escapeXml(value: string) {
  return value.replace(
    /[<>&'\"]/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&apos;" })[
        character
      ] ?? character,
  );
}

export async function GET() {
  const articles = await getCollection("actualites");
  const routes = [
    ...STATIC_ROUTES,
    ...articles.map((article) => `/actualites/${article.slug}/`),
  ];
  const body = routes
    .map((route) => `  <url><loc>${escapeXml(`${SITE}${route}`)}</loc></url>`)
    .join("\n");

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>`,
    { headers: { "Content-Type": "application/xml; charset=utf-8" } },
  );
}
