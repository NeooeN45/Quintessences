import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const requiredFiles = [
  "public/robots.txt",
  "public/_headers",
  "public/.well-known/security.txt",
  "src/pages/sitemap.xml.ts",
];
const legalFiles = [
  "src/pages/mentions-legales.astro",
  "src/pages/confidentialite.astro",
];
const requiredLegalSections = {
  "src/pages/mentions-legales.astro": [
    "Éditeur du site",
    "Directeur de la publication",
    "Hébergement",
    "Données personnelles",
  ],
  "src/pages/confidentialite.astro": [
    "Responsable de traitement",
    "Bases juridiques",
    "Destinataires et prestataires",
    "Durée de conservation",
    "Vos droits",
  ],
};
const placeholders = ["[À COMPLÉTER", "[À CONFIRMER", "TODO", "FIXME"];
const failures = [];

if (process.env.PUBLIC_ACCOUNT_ENABLED === "true") {
  failures.push(
    "zone Compte activée : la session web n'est pas encore approuvée pour la production",
  );
}

for (const relativePath of requiredFiles) {
  try {
    await readFile(resolve(root, relativePath), "utf8");
  } catch {
    failures.push(`fichier requis absent : ${relativePath}`);
  }
}

for (const relativePath of legalFiles) {
  const contents = await readFile(resolve(root, relativePath), "utf8");
  for (const section of requiredLegalSections[relativePath] ?? []) {
    if (!contents.includes(section)) {
      failures.push(`section juridique absente dans ${relativePath} : ${section}`);
    }
  }
  for (const placeholder of placeholders) {
    if (contents.includes(placeholder)) {
      failures.push(`placeholder juridique présent dans ${relativePath} : ${placeholder}`);
    }
  }
}

if (failures.length > 0) {
  console.error("Publication bloquée : le site public n'est pas prêt légalement.");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exitCode = 1;
} else {
  console.log("Site public prêt pour la revue légale et la mise en production.");
}
