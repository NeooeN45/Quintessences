# GSIE-PROMPT-0028 — Trajectoire territoriale et fiabilité du rejeu

| Champ | Valeur |
|---|---|
| Statut | EN_REVUE |
| Agent cible | Codex |
| Environnement | Copie locale isolée |
| Dépôt | NeooeN45/Quintessences |
| Branche | docs/trajectoire-simulation-territoriale |
| Commit de départ | d7b400cb15d9f2216f3296d92754a6e67e55a63f |
| Orchestrateur | Codex |
| Relecteur | Agent revue indépendant : aucun blocage sur le diff, clarification du compte intégrée |
| Priorité | P1 |

## Mission

Rendre la vision du Fondateur vérifiable dans la documentation et corriger
les acquittements de synchronisation lors d'une collision d'identifiant.
Intégrer comptes, référentiels parcellaires multiples, historique, rapports,
simulation et application PC de dialogue environnemental.

## Documents obligatoires

- `AGENTS.md`, `GSIE/API/AGENTS.md`, `PROJECT_MEMORY.md`, `ROADMAP.md`.
- README racine et API ; contrats RFC-0037 à RFC-0041.
- Constitution, skills documentation-gsie, gsie-governance, architecture-gsie,
  api-fastapi, tests-gsie et consortium-agents.
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`.

## Périmètre autorisé

RFC-0042, DEC-000074 Draft, README racine et API, index d'architecture,
ROADMAP, PROJECT_MEMORY, CHANGELOG, présent prompt et son registre.
Code : `GSIE/API/src/gsie_api/sync/geosylva.py` et tests unitaires associés.

## Méthode et critères d'acceptation

1. Inspecter le code au SHA annoncé ; citer les écarts et les limites.
2. Produire un cadrage sans nouveau registre ni adoption implicite d'une RFC.
3. Écrire les tests de collisions avant correction et constater leur échec.
4. Corriger le service, puis vérifier replays identiques, collisions,
   versions, changements de type et instants exprimés dans différents fuseaux.
5. Contrôler le diff, le formatage, le typage et la gouvernance documentaire.
6. Soumettre le résultat à une revue indépendante, ou en signaler l'absence.

## Interdictions

- Aucun texte Locked modifié ; aucune migration, modification des droits,
  nouvelle API publique, connexion à une base réelle ou activation de modèle.
- Aucun commit, push, merge ou déploiement sans autorisation explicite.
- Aucune confusion entre correction testée, historique livré et simulation
  scientifiquement validée.

## Rapport obligatoire

Remettre le SHA de départ, le diff, les commandes et résultats réellement
observés, la disponibilité de la revue et les limites restantes. Livrer un
patch local réversible et la proposition de trajectoire à lire.

## Résultat local

Sept régressions ont échoué avant correction, puis les 20 tests ciblés du
service ont réussi. Ruff et mypy strict ciblés sont conformes. La revue
indépendante a examiné le diff, sans reproduire les tests ni les sources
externes. Les contrôles de gouvernance, prompts, construction et structure
des moteurs sont conformes ; le registre des sources signale la revue
`etat_projet` expirée le 2026-09-14, préexistante et non renouvelée sans audit
complet. Aucune CI distante ni validation PostgreSQL/mobile n'est revendiquée.
