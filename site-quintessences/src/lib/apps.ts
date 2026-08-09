export interface AppEntry {
  slug: string;
  name: string;
  domain: string;
  summary: string;
  icon: string;
  accent: string; // variable CSS --color-app-*
  status: "disponible" | "planifiee";
  /** null tant que l'application n'est pas publiée sur le store. */
  playStoreUrl: string | null;
}

// Domaines repris tels quels de CLAUDE.md §10 et GSIE-DIR-0009 §3/§227 — aucune invention.
// playStoreUrl reste null pour toutes les apps : aucune n'est encore publiée.
export const APPS: AppEntry[] = [
  {
    slug: "geosylva",
    name: "GeoSylva",
    domain: "Forêt",
    summary:
      "Diagnostics stationnels, analyse des sols, recommandations de gestion forestière adaptées au terrain.",
    icon: "/icons/geosylva.png",
    accent: "var(--color-app-geosylva)",
    status: "disponible",
    playStoreUrl: null,
  },
  {
    slug: "ignis",
    name: "Ignis",
    domain: "Incendies",
    summary:
      "Surveillance et analyse des feux de forêt — jumeau numérique de propagation, aide à la décision du COS/CODIS.",
    icon: "/icons/ignis.png",
    accent: "var(--color-app-ignis)",
    status: "planifiee",
    playStoreUrl: null,
  },
  {
    slug: "hydro",
    name: "Hydro",
    domain: "Eau",
    summary:
      "Cartographie du réseau hydrographique, des zones humides et des régimes hydriques.",
    icon: "/icons/hydro.png",
    accent: "var(--color-app-hydro)",
    status: "planifiee",
    playStoreUrl: null,
  },
  {
    slug: "flora",
    name: "Flora",
    domain: "Végétation",
    summary: "Flore, taxonomie, cartographie végétale et phénologie.",
    icon: "/icons/flora.png",
    accent: "var(--color-app-flora)",
    status: "planifiee",
    playStoreUrl: null,
  },
  {
    slug: "artemis",
    name: "Artemis",
    domain: "Faune",
    summary: "Suivi de la faune terrain — comptages, pièges photo, observations, populations.",
    icon: "/icons/artemis.png",
    accent: "var(--color-app-artemis)",
    status: "planifiee",
    playStoreUrl: null,
  },
  {
    slug: "terra",
    name: "Terra",
    domain: "Sols / géologie",
    summary: "Caractérisation et classification des sols — texture, pH, drainage, réserve utile en eau.",
    icon: "/icons/terra.png",
    accent: "var(--color-app-terra)",
    status: "planifiee",
    playStoreUrl: null,
  },
  {
    slug: "aeris",
    name: "Aeris",
    domain: "Atmosphère / météo",
    summary: "Observations, prévisions et variables bioclimatiques, projections climatiques scénarisées.",
    icon: "/icons/aeris.png",
    accent: "var(--color-app-aeris)",
    status: "planifiee",
    playStoreUrl: null,
  },
  {
    slug: "atlas",
    name: "Atlas",
    domain: "Cartographie globale",
    summary: "Couches géospatiales de référence et services d'analyse spatiale communs à tout l'écosystème.",
    icon: "/icons/atlas.png",
    accent: "var(--color-app-atlas)",
    status: "planifiee",
    playStoreUrl: null,
  },
];
