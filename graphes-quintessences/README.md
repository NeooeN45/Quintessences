# Graphes — Quintessences / GSIE

Site statique local affichant les diagrammes Mermaid de synthèse du
projet : écosystème, chaîne d'intelligence, métamodèle, applications,
gouvernance, identité, phases, moteurs, décisions, data registry et
infrastructure territoriale. Aucune dépendance à builder — HTML statique
généré par un script Python, Mermaid rendu côté client via CDN.

## Fonctionnalités

- **14 diagrammes** répartis en **4 catégories** (Écosystème, Gouvernance,
  Progression, Infrastructure), tous sourcés depuis la documentation
  réelle du projet (`README.md`, `PROJECT_MEMORY.md`, `ROADMAP.md`,
  `03_DECISIONS/`, `02_RFC/`, `GSIE/ARCHITECTURE/`).
- **Navigation latérale** groupée par catégorie avec compteur, et
  surbrillance automatique de la section visible au défilement.
- **Filtres par catégorie** (puces en haut de page) combinés à la
  **recherche instantanée** (raccourci clavier `/`).
- **Thème clair/sombre**, persisté dans `localStorage`, avec palette
  Mermaid adaptée (`base` / `dark`) et police Space Grotesk / Space Mono.
- **Zoom / pan** par diagramme : boutons `+` / `−` / réinitialiser,
  `Ctrl`/`Cmd` + molette, glisser pour déplacer.
- **Vue plein écran** par diagramme (superposition modale, fermeture par
  `Échap` ou clic hors-diagramme).
- **Téléchargement en SVG** du rendu de chaque diagramme.
- **Voir le code source** : bascule inline du code Mermaid brut, en plus
  du bouton **Copier**.
- **Lien direct** (`#<id>`) par diagramme, partageable.
- Badge de **type de diagramme** détecté automatiquement (Flowchart,
  Séquence, États, Chronologie, etc.) et badge de **catégorie**.

## Démarrer

```bash
cd graphes-quintessences
python -m http.server 4300 --directory public
```

→ http://127.0.0.1:4300

(Port 4300 : évite les conflits avec `site-quintessences` 4100,
`GSIE/ADMIN_WEB` 4000, l'API 8000, les outils viz 3030/8088/8089.)

## Publication GitHub Pages

Le workflow `.github/workflows/deploy-graphes-pages.yml` régénère et publie
`public/` sur GitHub Pages après un push sur `main` touchant les graphes, les
RFC, les décisions ou les fichiers de suivi. Les actions GitHub sont épinglées
par SHA.

La première activation nécessite de sélectionner **GitHub Actions** comme source
dans `Settings → Pages → Build and deployment` du dépôt GitHub. La publication
ne se déclenche pas depuis une branche de fonctionnalité tant qu'elle n'est pas
fusionnée sur `main`.

## Régénérer les graphes

Les diagrammes sources vivent dans `diagrams/*.mmd`, référencés dans
l'ordre par `diagrams/meta.json` (id, titre, catégorie, description,
source documentaire, date de mise à jour).

1. Éditer le `.mmd` concerné (ou en ajouter un + une entrée `meta.json`).
2. Régénérer `public/index.html` :

```bash
python generate_site.py
```

Le script est idempotent et ne dépend que de la bibliothèque standard
Python. Aucune build step supplémentaire. Vérifier après régénération :

```bash
python -m ruff check generate_site.py
python -m mypy generate_site.py
```

## Diagrammes actuels

| Fichier | Catégorie | Type | Contenu | Source |
|---|---|---|---|---|
| `01_ecosysteme.mmd` | Écosystème | Graphe | Vue d'ensemble de l'écosystème Quintessences | `README.md` |
| `02_chaine_intelligence.mmd` | Écosystème | Flowchart | Flux de preuve à décision (7 moteurs) | `README.md` |
| `06_metamodele_encyclopedie.mmd` | Écosystème | Graphe | 73 types noyau de l'Encyclopédie, 5 niveaux | `README.md` |
| `13_applications_ecosysteme.mmd` | Écosystème | Graphe | État de déploiement des 9 applications + Hub | `PROJECT_MEMORY.md`, `DEC-000056` |
| `03_hierarchie_documentaire.mmd` | Gouvernance | Flowchart | Vision → Constitution → ... → Code | `README.md` |
| `08_cycle_vie_document.mmd` | Gouvernance | États | Draft → Review → Validated → Locked | `CLAUDE.md`, `AGENTS.md` |
| `07_identite_quintessences.mmd` | Gouvernance | Flowchart | Fournisseurs de connexion, jetons GSIE | `IDENTITE_QUINTESSENCES.md`, `DEC-000044` |
| `04_phases_projet.mmd` | Progression | Flowchart | État des 4 phases du projet | `PROJECT_MEMORY.md`, `ROADMAP.md` |
| `05_moteurs_gsie.mmd` | Progression | Graphe | État des 14 moteurs GSIE | `PROJECT_MEMORY.md` |
| `12_timeline_decisions.mmd` | Progression | Chronologie | Décisions structurantes jusqu'à DEC-000073 et RFC-0041 | `03_DECISIONS/`, `02_RFC/` |
| `14_fascade_geosylva_gsie.mmd` | Écosystème | Flowchart | Façade GeoSylva–GSIE, identité stationnelle, préparation fail-closed et preuves | `RFC-0041`, `DEC-000073`, `DEC-000072` |
| `09_pipeline_data_registry.mmd` | Progression | Flowchart | Pipeline Agent → Source → ... → Resolver | `RFC-0038`, `PROJECT_MEMORY.md` |
| `10_architecture_mesh.mmd` | Infrastructure | Graphe | Server Meshing — composants | `SERVER_MESHING_DIAGRAMS.md`, `RFC-0035` |
| `11_hierarchie_territoriale.mmd` | Infrastructure | Graphe | Territorial Mesh — hiérarchie territoriale | `TERRITORIAL_MESH_DIAGRAMS.md`, `RFC-0036` |

## Structure

```
graphes-quintessences/
├── generate_site.py         ← générateur HTML (stdlib uniquement)
├── diagrams/
│   ├── meta.json             ← ordre, catégorie, description, source, date
│   └── *.mmd                 ← code Mermaid source
└── public/
    ├── index.html            ← généré, ne jamais éditer à la main
    ├── favicon.svg
    ├── css/main.css           ← thème clair/sombre, sidebar, cartes, modale
    └── js/site.js             ← recherche, filtres, zoom/pan, thème, copie,
                                  code, plein écran, export SVG, nav active
```

## Mise à jour automatique

Le skill `.devin/skills/graphes-progression/SKILL.md` documente le
processus de mise à jour de ces graphes après une grosse progression du
projet (clôture de phase, décision structurante, moteur livré, etc.).
