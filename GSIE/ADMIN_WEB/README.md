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
│   └── data.astro              # Catalogue datasets
├── components/
│   ├── Sidebar.astro           # Navigation groupée par sections (statique)
│   ├── Topbar.astro            # Search + notifications + user menu (statique)
│   ├── StatCard.astro          # Cartes métriques avec icône + trend (statique)
│   ├── SystemHealth.tsx        # React Island — santé système
│   ├── EngineStatusGrid.tsx    # React Island — moteurs
│   ├── UserTable.tsx           # React Island — utilisateurs
│   └── DataCatalog.tsx         # React Island — datasets
├── lib/
│   ├── api.ts                  # Client hybride (mock → API GSIE)
│   ├── mock-data.ts            # Données simulées
│   └── types.ts                # Types partagés
└── styles/
    └── global.css              # Tailwind 4 + thème Tabler dark mode
```

## Connexion API GSIE

Par défaut, le site utilise des **données simulées** (mock data).
Quand l'API GSIE est disponible, le client bascule automatiquement.

Pour forcer la connexion à l'API :

```bash
cp .env.example .env
# Éditer .env : GSIE_API_URL=http://localhost:8000
```

Le client tente un ping sur `GSIE_API_URL/health` au démarrage.
Si l'API répond, toutes les requêtes utilisent l'API réelle.

## Pages

| Page | URL | Type | Données |
|---|---|---|---|
| Vue d'ensemble | `/` | Statique + 1 island | 4 stat cards + santé système |
| Moteurs | `/engines` | 1 island | 14 moteurs, filtres par catégorie |
| Utilisateurs | `/users` | 1 island | Tableau, recherche, filtres rôle |
| Données | `/data` | 1 island | Catalogue, filtres par source |

## Tests

```bash
npx astro check    # 0 erreur, 0 warning, 0 hint
npm run build      # 4 pages, islands 3.5-4.5 KB chacun
```

## Préparation version serveur

L'architecture est découplée :
- `lib/api.ts` centralise tous les appels de données
- `lib/types.ts` définit les contrats (compatibles avec l'API FastAPI)
- Les composants React consomment uniquement les types, pas l'API directement

Quand la version serveur GSIE sera déployée :
1. Définir `GSIE_API_URL` dans `.env`
2. L'API FastAPI doit exposer : `/health`, `/api/v1/system/health`,
   `/api/v1/system/stats`, `/api/v1/engines`, `/api/v1/users`,
   `/api/v1/datasets`
3. Aucune modification de l'UI n'est nécessaire
