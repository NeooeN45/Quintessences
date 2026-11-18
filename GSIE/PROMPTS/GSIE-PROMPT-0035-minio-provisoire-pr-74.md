# GSIE-PROMPT-0035 — MinIO provisoire depuis les sources pour la PR nº 74

| Champ | Valeur |
|---|---|
| Statut | EN_REVUE |
| Agent principal | Claude, architecte-relecteur, sur demande explicite du Fondateur |
| Dépôt | NeooeN45/Quintessences |
| Branche | fix/pr74-minio-sources-epinglees |
| Commit de départ | 72e8fe36fb54c44fc491106d0e8af74ba374d807 |
| Date | 2026-11-18 |
| Orchestrateur | Fondateur, mission confiée directement à l'architecte |
| Relecteur | Codex ou agent indépendant, puis Fondateur |
| Autorité finale | Camille Perraudeau (Fondateur) |

## Mission

Rendre exécutables les jobs CI *Data Registry* et *Haute disponibilité/TLS*
de la PR nº 74, bloqués parce que les images `minio/minio` et `minio/mc` ne
sont plus téléchargeables, en construisant MinIO depuis des sources
officielles épinglées et vérifiées par empreinte.

## Pourquoi maintenant

La PR nº 74 réconcilie `main`, `feat/schemas-de-domaine` et les correctifs de
sécurité. Elle ne peut pas être fusionnée tant que *CI Gate* est rouge, et le
serveur de test ne peut pas être déployé tant qu'elle n'est pas fusionnée.

## Documents obligatoires

- `AGENTS.md` et `GSIE/API/AGENTS.md`.
- `23_QUALITY_MANAGEMENT/AUDITS/LEVEE_BLOCAGES_PR74_2026-11-16.md`, §7.1.
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`.
- `GSIE/API/docker-compose.yml`, `.github/workflows/ci.yml`,
  `.github/workflows/ha-linux.yml`.

## Périmètre autorisé

- Recette `GSIE/API/docker/minio/` (Dockerfile et README).
- Références aux images MinIO dans `docker-compose.yml` et `ci.yml`.
- Inscription de la dette et de son échéance.
- Passage de DEC-000094 à `Validated`, validée par le Fondateur le
  16 novembre 2026 dans sa version simplifiée.
- Registre des prompts et `CHANGELOG.md`.

## Décisions du Fondateur appliquées

- 16 novembre 2026 : la proposition E du bilan (sources épinglées, empreintes
  vérifiées) est autorisée **à titre provisoire** ; le remplacement de MinIO
  sera décidé avant toute ouverture à des testeurs.
- 16 novembre 2026 : DEC-000094 est validée dans sa version simplifiée.
- 18 novembre 2026 : l'architecte est chargé de réaliser lui-même ce lot.

## Non-objectifs

- Remplacer MinIO par un autre stockage objet.
- Corriger la course `ix_resource_gsie_id` (point F du bilan), traitée dans
  une demande de fusion distincte.
- Modifier le code applicatif, les migrations ou les tests.

## Interdictions

- Aucun job désactivé, aucun seuil abaissé, aucune vérification d'empreinte
  contournée.
- Aucun binaire téléchargé depuis un miroir tiers.
- Aucun push sur `main`, aucune fusion sans accord explicite du Fondateur.
- Aucune réécriture d'historique.

## Conditions d'arrêt

- Une empreinte d'archive ne correspond plus à celle relevée le 16 novembre.
- La construction exige de désactiver un contrôle de sécurité.
- Le correctif demande une modification hors périmètre.

## Méthode attendue

1. Reprendre la recette de `fix/minio-source-baseline` (28 septembre 2026).
2. Remplacer le clonage Git par les archives officielles vérifiées par
   `ADD --checksum`, et ajouter `go mod verify`.
3. Brancher la recette dans Compose et dans le job *Data Registry*.
4. Pousser sur une branche dédiée et laisser la CI qualifier la construction,
   qui ne peut pas être exécutée dans l'environnement de l'architecte.

## Validations obligatoires

- `python3 tools/check_governance_consistency.py`
- `python3 tools/check_source_of_truth.py`
- `python3 tools/check_ai_prompts.py`
- `python3 tools/check_build_consistency.py`
- CI GitHub : *Data Registry*, *Haute disponibilité/TLS* et *CI Gate*.

## Critères d'acceptation

- Les images MinIO sont construites en CI avec vérification d'empreinte.
- *CI Gate* est vert sans aucun contrôle affaibli.
- La dette et son échéance sont écrites dans le dépôt.

## Rapport obligatoire

Hash du commit, état de la CI job par job, emplacement de l'entrée de dette,
écarts constatés et ce qui reste à faire avant fusion.
