/**
 * Constantes partagées du dashboard GSIE Admin.
 * Source unique pour éviter la duplication entre composants.
 */

// --- Moteurs GSIE (14) ---
export const ENGINES = [
  "evidence",
  "knowledge",
  "correlation",
  "reasoning",
  "diagnostic",
  "recommendation",
  "validation",
  "gis",
  "climate",
  "pedology",
  "botanical",
  "forest_dynamics",
  "learning",
  "simulation",
] as const;

export const ENGINE_DESCRIPTIONS: Record<string, string> = {
  evidence: "Collecte et validation des preuves",
  knowledge: "Base de connaissances structurée",
  correlation: "Détection de corrélations",
  reasoning: "Chaînage et inférence",
  diagnostic: "Diagnostic forestier",
  recommendation: "Recommandations sylvicoles",
  validation: "Validation des recommandations",
  gis: "Moteur géospatial (PostGIS, IGN)",
  climate: "Données climatiques (AROME, MétéoFrance)",
  pedology: "Sols et pédologie (SoilGrids)",
  botanical: "Botanique (GBIF, Taxref)",
  forest_dynamics: "Dynamique forestière",
  learning: "Apprentissage et amélioration",
  simulation: "Simulations et scénarios",
};

// --- Niveaux de danger feu ---
export const LEVEL_COLORS: Record<string, string> = {
  low: "var(--color-accent)",
  moderate: "var(--color-warning)",
  high: "#f97316",
  very_high: "#ef4444",
  extreme: "#991b1b",
};

// --- Intervals de polling (ms) ---
export const POLL_INTERVALS = {
  health: 5_000,
  engines: 30_000,
  notifications: 30_000,
  knowledge: 30_000,
  healthPanel: 10_000,
  climate: 60_000,
  clock: 1_000,
  sessionCountdown: 1_000,
  apiStatus: 30_000,
} as const;

// --- Délais (ms) ---
export const DELAYS = {
  batch: 100,
  toastDismiss: 5_000,
  loadingBarHide: 500,
  announce: 50,
  gKeyTimeout: 1_000,
} as const;
