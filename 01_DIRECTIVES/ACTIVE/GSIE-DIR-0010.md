# ============================================================================
# GSIE REPOSITORY RESTRUCTURING DIRECTIVE
# Directive ID : GSIE-DIR-0010
# Version : 1.0
# Statut : ACTIVE
# Priorité : CRITIQUE
# Classification : FONDATION
# Auteur : Camille Perraudeau
# Date : 2026-07-13
# ============================================================================

# Titre : Réorganisation de l'arborescence du dépôt — Quintessences,
# GSIE et apps

## Résumé exécutif

Le Fondateur acte une réorganisation de l'arborescence du dépôt pour
refléter la hiérarchie réelle de l'écosystème Quintessences :

1. **Racine** : documents transverses (Constitution, directives, RFC,
   décisions, specs, légal, finance, mémoire, qualité).
2. **GSIE/** : tout ce qui appartient au moteur central (architecture,
   recherche, connaissances, datasets, moteurs, algorithmes, modèles,
   API, SDK, tests, outils, documentation).
3. **apps/** : les applications clientes, au même niveau que GSIE
   (GeoSylva, Artemis, Ignis, Hydro, Flora, QGISIA).

---

## 1. Structure cible

```
Quintessences/                    (racine du dépôt)
│
├── 00_CONSTITUTION/              ← primauté constitutionnelle
├── 01_DIRECTIVES/                ← directives fondatrices
├── 02_RFC/                       ← propositions d'évolution
├── 03_DECISIONS/                 ← décisions tracées
├── 05_SPECIFICATIONS/            ← exigences transverses
│
├── GSIE/                         ← moteur central
│   ├── ARCHITECTURE/             ← était 04_ARCHITECTURE/
│   ├── RESEARCH/                 ← était 06_RESEARCH/
│   ├── KNOWLEDGE/                ← était 07_KNOWLEDGE/
│   ├── DATASETS/                 ← était 08_DATASETS/
│   ├── ENGINES/                  ← était 09_ENGINES/
│   ├── ALGORITHMS/               ← était 10_ALGORITHMS/
│   ├── MODELS/                   ← était 11_MODELS/
│   ├── APPLICATIONS/             ← était 12_APPLICATIONS/
│   ├── API/                      ← était 13_API/
│   ├── SDK/                      ← était 14_SDK/
│   ├── TESTS/                    ← était 15_TESTS/
│   ├── TOOLS/                    ← était 16_TOOLS/
│   └── DOCUMENTATION/            ← était 17_DOCUMENTATION/
│
├── apps/                         ← applications clientes
│   ├── GeoSylva/                 ← forêt
│   ├── Artemis/                  ← faune
│   ├── Ignis/                    ← incendies
│   ├── Hydro/                    ← eau
│   ├── Flora/                    ← végétation
│   └── QGISIA/                   ← plugin QGIS
│
├── 18_FINANCING/                 ← transverse
├── 19_LEGAL/                     ← transverse
├── 20_PARTNERSHIPS/              ← transverse
├── 21_EXPERIMENTS/               ← transverse
├── 22_PROJECT_MEMORY/            ← mémoire transverse
├── 23_QUALITY_MANAGEMENT/        ← transverse
│
├── README.md
├── ROADMAP.md
├── CHANGELOG.md
├── PROJECT_MEMORY.md
└── CLAUDE.md
```

---

## 2. Logique de la réorganisation

### 2.1 Racine — transverse à Quintessences

Les documents à la racine concernent **tout l'écosystème** Quintessences,
pas seulement GSIE. La Constitution (CON-000) prime sur tout — elle est
au sommet.

| Dossier | Raison |
|---|---|
| 00_CONSTITUTION | Primauté constitutionnelle — sommet de la hiérarchie |
| 01_DIRECTIVES | Directives fondatrices — s'appliquent à tout l'écosystème |
| 02_RFC | Propositions d'évolution — transverses |
| 03_DECISIONS | Décisions tracées — transverses |
| 05_SPECIFICATIONS | Exigences transverses (fonctionnelles/non fonctionnelles) |
| 18_FINANCING | Financement de l'écosystème |
| 19_LEGAL | Conformité, licences — transverse |
| 20_PARTNERSHIPS | Partenariats — transverse |
| 21_EXPERIMENTS | Prototypes — transverse |
| 22_PROJECT_MEMORY | Mémoire du projet — transverse |
| 23_QUALITY_MANAGEMENT | Qualité — transverse |

### 2.2 GSIE/ — le moteur central

Tout ce qui appartient au moteur GSIE est regroupé sous `GSIE/`. Cela
inclut l'architecture, la recherche, la base de connaissances, les
datasets, les 14 moteurs, les algorithmes, les modèles, l'API, le SDK,
les tests, les outils et la documentation technique.

### 2.3 apps/ — les applications clientes

Les applications sont **au même niveau que GSIE**, pas à l'intérieur.
Elles sont des clientes de GSIE, pas des sous-modules. Chaque app a son
propre dossier avec sa mémoire, ses livrables et (en Phase 4) son code.

---

## 3. Mappings de déplacement

| Ancien chemin | Nouveau chemin |
|---|---|
| `04_ARCHITECTURE/` | `GSIE/ARCHITECTURE/` |
| `06_RESEARCH/` | `GSIE/RESEARCH/` |
| `07_KNOWLEDGE/` | `GSIE/KNOWLEDGE/` |
| `08_DATASETS/` | `GSIE/DATASETS/` |
| `09_ENGINES/` | `GSIE/ENGINES/` |
| `10_ALGORITHMS/` | `GSIE/ALGORITHMS/` |
| `11_MODELS/` | `GSIE/MODELS/` |
| `12_APPLICATIONS/` | `GSIE/APPLICATIONS/` |
| `13_API/` | `GSIE/API/` |
| `14_SDK/` | `GSIE/SDK/` |
| `15_TESTS/` | `GSIE/TESTS/` |
| `16_TOOLS/` | `GSIE/TOOLS/` |
| `17_DOCUMENTATION/` | `GSIE/DOCUMENTATION/` |
| `22_PROJECT_MEMORY/Ignis/` | `apps/Ignis/` |
| `22_PROJECT_MEMORY/Ignis.md` | `apps/Ignis/REGISTRE.md` |
| `22_PROJECT_MEMORY/GSIE-FEU/` | `apps/Ignis/archive-GSIE-FEU/` |

### 3.1 Nouveaux dossiers apps créés

| Dossier | Statut |
|---|---|
| `apps/GeoSylva/` | Créé avec README |
| `apps/Artemis/` | Créé avec README |
| `apps/Ignis/` | Déménagé depuis 22_PROJECT_MEMORY/ |
| `apps/Hydro/` | Créé avec README |
| `apps/Flora/` | Créé avec README |
| `apps/QGISIA/` | Créé avec README |

---

## 4. Mise à jour des références croisées

Toutes les références de chemins dans les documents doivent être mises
à jour. Par exemple :

| Ancien chemin | Nouveau chemin |
|---|---|
| `04_ARCHITECTURE/...` | `GSIE/ARCHITECTURE/...` |
| `06_RESEARCH/...` | `GSIE/RESEARCH/...` |
| `07_KNOWLEDGE/...` | `GSIE/KNOWLEDGE/...` |
| `08_DATASETS/...` | `GSIE/DATASETS/...` |
| `09_ENGINES/...` | `GSIE/ENGINES/...` |
| `17_DOCUMENTATION/...` | `GSIE/DOCUMENTATION/...` |
| `22_PROJECT_MEMORY/Ignis/...` | `apps/Ignis/...` |

---

## 5. Décisions validées

1. L'arborescence est réorganisée en trois niveaux : racine, GSIE/,
   apps/.
2. 13 dossiers sont déplacés vers `GSIE/`.
3. 6 dossiers apps sont créés dans `apps/`.
4. Le contenu de `22_PROJECT_MEMORY/Ignis/` déménage vers `apps/Ignis/`.
5. Toutes les références croisées sont mises à jour.
6. CLAUDE.md, README, .gitignore sont mis à jour.
7. Les préfixes numériques sont conservés pour les dossiers racines
   transverses.
8. Les dossiers GSIE/ et apps/ n'ont pas de préfixe numérique — ils
   sont des conteneurs logiques.

---

## 6. Garde-fous

- La Constitution prime sur tout (CON-000).
- Aucun document Locked n'est modifié (sauf chemins).
- Le code métier reste interdit en Phase 3.
- L'historique git est préservé (git mv).

---

> L'arborescence reflète la hiérarchie : Quintessences > GSIE > apps.
