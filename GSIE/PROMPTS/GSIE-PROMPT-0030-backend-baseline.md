# GSIE-PROMPT-0030 — Baseline backend pour développement collaboratif

| Champ | Valeur |
|---|---|
| Statut | PRÊTE |
| Agent cible | Codex |
| Snapshot | Branche locale de préparation, à relever au lancement |
| Priorité | P0 |

## Mission

Rendre l'environnement backend GSIE reproductible pour développer le lot B00
et préparer B01 sans modifier les textes Locked ni publier d'infrastructure.
Inventorier les services, migrations, routes OpenAPI et tests exécutables.

## Documents obligatoires

- `AGENTS.md`, `GSIE/API/AGENTS.md`, `GSIE/API/docs/development/README.md`.
- `GSIE/API/docs/development/BACKEND_WORK_PACKAGES.md` et `CONTRACT_HANDOFF.md`.
- Constitution, RFC-0037 à RFC-0042, `PROJECT_MEMORY.md`, `ROADMAP.md`.

## Interdictions

- Aucun déploiement, commit, push, migration destructive ou accès à une base réelle.
- Aucun secret, token ou donnée personnelle dans les rapports.
- Aucun contrat futur inventé pour le frontend.

## Rapport obligatoire

Remettre commandes, versions, résultats, limites, OpenAPI régénéré si possible,
et prérequis du lot suivant. Signaler toute dépendance ou service indisponible.
