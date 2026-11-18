import { access, readFile, readdir } from "node:fs/promises";
import { join, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = join(root, "dist");
const failures = [];

async function collectHtml(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectHtml(path)));
    } else if (entry.isFile() && entry.name.endsWith(".html")) {
      files.push(path);
    }
  }
  return files;
}

async function targetExists(pathname) {
  const cleanPath = pathname.split("?", 1)[0].split("#", 1)[0];
  if (!cleanPath || cleanPath === "/") {
    await access(join(dist, "index.html"));
    return;
  }

  const relativePath = cleanPath.replace(/^\/+/, "");
  const candidates = cleanPath.endsWith("/")
    ? [join(dist, relativePath, "index.html")]
    : [join(dist, relativePath), join(dist, `${relativePath}.html`), join(dist, relativePath, "index.html")];

  for (const candidate of candidates) {
    const resolved = resolve(candidate);
    const relativeCandidate = relative(dist, resolved);
    if (!relativeCandidate.startsWith("..") && !relativeCandidate.includes(`..${relative.sep}`)) {
      try {
        await access(resolved);
        return;
      } catch {
        // Essayer le candidat suivant.
      }
    }
  }

  throw new Error(`cible absente : ${pathname}`);
}

const htmlFiles = await collectHtml(dist);
for (const file of htmlFiles) {
  const contents = await readFile(file, "utf8");
  const hrefPattern = /\bhref=["']([^"']+)["']/g;
  for (const match of contents.matchAll(hrefPattern)) {
    const href = match[1];
    if (!href.startsWith("/") || href.startsWith("//")) continue;
    try {
      await targetExists(href);
    } catch (error) {
      failures.push(`${relative(root, file)} → ${error.message}`);
    }
  }
}

if (process.env.PUBLIC_ACCOUNT_ENABLED !== "true") {
  const home = await readFile(join(dist, "index.html"), "utf8");
  if (home.includes('href="/compte/"')) {
    failures.push("le header public expose un lien Compte alors que la zone est fermée");
  }

  for (const accountPath of [
    "compte/index.html",
    "compte/connexion/index.html",
    "compte/inscription/index.html",
  ]) {
    const contents = await readFile(join(dist, accountPath), "utf8");
    if (!contents.includes("Zone Compte non ouverte")) {
      failures.push(`${accountPath} n'affiche pas la page de fermeture attendue`);
    }
    if (/component-url="\/_astro\/(LoginForm|RegisterForm|ProfileView)\./.test(contents)) {
      failures.push(`${accountPath} embarque encore un formulaire Compte fermé`);
    }
  }
}

if (failures.length > 0) {
  console.error("Liens internes invalides dans le build public :");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`Liens internes vérifiés : ${htmlFiles.length} fichier(s) HTML.`);
