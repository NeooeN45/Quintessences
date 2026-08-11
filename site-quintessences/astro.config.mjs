// @ts-check
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

// Site public Quintessences — SITE-001/SITE-002/DEC-000057
// Port 4100 : évite les conflits avec l'API (8000), ADMIN_WEB (4000) et les outils viz (3030/8088/8089)
export default defineConfig({
  server: {
    port: 4100,
    host: "127.0.0.1",
  },
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
});
