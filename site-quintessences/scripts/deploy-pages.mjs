import { spawnSync } from "node:child_process";

const projectName = process.env.CLOUDFLARE_PAGES_PROJECT?.trim();
if (!projectName) {
  console.error(
    "Déploiement refusé : définissez CLOUDFLARE_PAGES_PROJECT avec le nom exact du projet Pages.",
  );
  process.exit(2);
}

const branch = process.env.CLOUDFLARE_PAGES_BRANCH?.trim();
const command = process.platform === "win32" ? "npx.cmd" : "npx";
const args = ["--no-install", "wrangler", "pages", "deploy", "dist", "--project-name", projectName];
if (branch) args.push("--branch", branch);

const result = spawnSync(command, args, {
  cwd: process.cwd(),
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  console.error(
    "Déploiement refusé : Wrangler n'est pas installé dans ce projet. " +
      "Installez-le avec `npm install --save-dev wrangler@latest` puis relancez.",
  );
  process.exit(2);
}

process.exit(result.status ?? 1);

