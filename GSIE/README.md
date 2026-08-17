# GSIE — General System Intelligence Engine

> Moteur central de l'écosystème Quintessences. Toutes les applications
> clientes (GeoSylva, Artemis, Ignis, Hydro, Flora, QGISIA) consomment
> les données, simulations et interopérabilités fournies par GSIE.

---

## Objectif

GSIE est le moteur de données, d'IA, de simulations et d'interopérabilité
au cœur de l'écosystème Quintessences. Il orchestre **14 moteurs** spécialisés
qui transforment les connaissances scientifiques en recommandations
explicables pour le forestier décideur.

## Structure

| Dossier | Rôle |
|---|---|
| `ENGINES/` | 14 moteurs GSIE (Evidence, Knowledge, Correlation, Reasoning, Diagnostic, Recommendation, Validation, GIS, Climate, Pedology, Botanical, Forest Dynamics, Learning, Simulation) |
| `API/` | API FastAPI — point d'entrée HTTP pour toutes les applications clientes |
| `SDK/` | SDK Python — client async avec JWT RS256 auto-refresh |
| `ADMIN_WEB/` | Tableau de contrôle admin — Astro 5 + React 19 Islands + Tailwind 4 |
| `ARCHITECTURE/` | Architecture logicielle et scientifique |
| `RESEARCH/` | Travaux scientifiques, bibliographie |
| `KNOWLEDGE/` | Base de connaissances structurée |
| `DATASETS/` | Jeux de données référencés |
| `ALGORITHMS/` | Algorithmes |
| `MODELS/` | Modèles scientifiques |
| `APPLICATIONS/` | Applications GSIE internes |
| `TESTS/` | Tests transverses |
| `TOOLS/` | Outils |
| `DOCUMENTATION/` | Documentation technique |
| `PROMPTS/` | Prompts versionnés pour l'orchestration d'agents IA |

## Chaîne principale

```
Evidence → Knowledge → Correlation → Reasoning → Diagnostic
→ Recommendation → Validation → Utilisateur
```

Moteurs domaine : GIS, Climate, Pedology, Botanical, Forest Dynamics.
Moteurs transverses : Learning, Simulation.

### Orchestration stationnelle — état au 2026-08-17

L'API expose déjà l'orchestration interne et l'hydratation fail-closed par
`station_id` : `Place` prioritaire, `FieldIntake accepted` en repli, quarantaine
et rejet exclus. Le rapport d'hydratation est persisté avec la preuve d'analyse.

La façade GeoSylva est cadrée mais non encore livrée : RFC-0041 est `Draft` et
DEC-000073 est `Proposé`. La prochaine tranche doit d'abord fournir côté
serveur les règles qualifiées, leurs sources et un état global sourcé ; en leur
absence, l'analyse est bloquée sans valeur par défaut. Le lien entre identifiant
local GeoSylva et UUID GSIE sera explicite, contrôlé par compte et révocable.

Chaque moteur a **une responsabilité unique**, documentée dans
`ENGINES/<NOM>_ENGINE/` (README + ENGINE.md + contrat d'interface).

## Phase courante

**Phase 4 — Implémentation** (lancée par DEC-000017 / GSIE-DIR-0011).
Voir `PROJECT_MEMORY.md` pour l'état d'implémentation courant.

## Voir aussi

- `../PROJECT_MEMORY.md` — État courant du projet
- `../ROADMAP.md` — Phases et livrables
- `../CHANGELOG.md` — Journal des évolutions
- `../CLAUDE.md` — Guide opérationnel pour agents IA
