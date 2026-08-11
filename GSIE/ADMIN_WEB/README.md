# GSIE Admin Web — Tableau de contrôle

> Tableau de contrôle administrateur pour GSIE.
> Astro 5 + React 19 Islands (hydratation sélective) + Tailwind CSS 4.
> Design calqué sur [Tabler](https://github.com/tabler/tabler) (dashboard
> open-source, Bootstrap 5) — reproduit en Tailwind 4 sans dépendance Bootstrap.

## Démarrer

```bash
cd GSIE/ADMIN_WEB
npm install
npm run dev
```

→ http://localhost:4000

## Design — style Tabler

Le dashboard reproduit l'esthétique Tabler en Tailwind 4 :

- **Layout** : sidebar gauche (56px) + topbar sticky (search + notifications + user menu)
- **Cards** : `card` + `card-header` + `card-body` (border + rounded 4px)
- **Stat cards** : icône en haut à droite, valeur 2xl bold, trend avec flèche colorée
- **Tables** : borderless avec hover, en-têtes uppercase tracking-wide, tabular-nums
- **Badges** : fond semi-transparent (20% opacity) + texte coloré
- **Palette dark mode** : surface `#1a2234`, primary bleu `#206bc4`, sémantique green/yellow/red/azure/purple

## Architecture

```
src/
├── layouts/
│   └── AdminLayout.astro       # Layout (sidebar + topbar, 0 JS)
├── pages/
│   ├── index.astro             # Vue d'ensemble (stat cards + santé système)
│   ├── engines.astro           # Monitoring 14 moteurs
│   ├── users.astro             # Gestion utilisateurs
│   └── data.astro              # Catalogue datasets Data Registry
├── components/
│   ├── Sidebar.astro           # Navigation groupée par sections (statique)
│   ├── Topbar.astro            # Search + notifications + user menu (statique)
│   ├── StatCard.astro          # Cartes métriques avec icône + trend (statique)
│   ├── SystemHealth.tsx        # React Island — santé système
│   ├── EngineStatusGrid.tsx    # React Island — moteurs
│   ├── UserTable.tsx           # React Island — utilisateurs
│   └── DataCatalogPanel.tsx    # React Island — catalogue Data Registry
├── lib/
│   ├── api.ts                  # Client authentifié vers l'API GSIE
│   ├── constants.ts            # Constantes du dashboard
│   └── useDebounce.ts          # Utilitaire de recherche
└── styles/
    └── global.css              # Tailwind 4 + thème Tabler dark mode
```

## Connexion API GSIE

Le site utilise les données de l'API GSIE avec une session Bearer stockée
temporairement dans `sessionStorage`. Il n'y a pas de fallback silencieux vers
des données simulées : une API indisponible est affichée comme une erreur.

Pour configurer la connexion à l'API :

```bash
cp .env.example .env
# Éditer .env : GSIE_API_URL=http://localhost:8000
```

Le client utilise `PUBLIC_GSIE_API_URL/health` et les routes authentifiées
réelles dès que la session est établie.

## Pages

| Page | URL | Type | Données |
|---|---|---|---|
| Vue d'ensemble | `/` | Statique + 1 island | 4 stat cards + santé système |
| Moteurs | `/engines` | 1 island | 14 moteurs, filtres par catégorie |
| Utilisateurs | `/users` | 1 island | Tableau, recherche, filtres rôle |
| Données | `/data` | 1 island | Catalogue Data Registry réel, recherche et filtres par domaine |

## Tests

```bash
npx astro check    # 0 erreur (les hints préexistants sont listés)
npm run build      # 13 routes statiques, îles React hydratées à la demande
```

## Préparation version serveur

L'architecture est découplée :
- `lib/api.ts` centralise tous les appels de données
- `lib/api.ts` définit les contrats et centralise les appels (compatibles avec l'API FastAPI)
- Les composants React consomment uniquement les types, pas l'API directement

Quand la version serveur GSIE sera déployée :
1. Définir `GSIE_API_URL` dans `.env`
2. L'API FastAPI doit exposer : `/health`, `/ready`, les routes de contrôle,
   et le Data Registry `/api/v1/data/catalog`, `/api/v1/data/search` et
   `/api/v1/data/resolve`.
3. Aucune modification de l'UI n'est nécessaire
