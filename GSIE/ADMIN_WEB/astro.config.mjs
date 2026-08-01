// @ts-check
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

// Tableau de contrôle admin GSIE
// Astro 5 + React Islands — hydratation sélective
// Le port 4000 évite les conflits avec l'API (8000) et les outils viz (3030/8088/8089)
export default defineConfig({
  server: {
    port: 4000,
    host: "127.0.0.1",
  },
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
});
