# GSIE-PROMPT-0034 — Lever les blocages de la PR nº 74

| Champ | Valeur |
|---|---|
| Statut | EN_COURS |
| Agent principal | Codex, consortium spécialisé avec revue indépendante |
| Dépôt | NeooeN45/Quintessences |
| Branche | integration/reconciliation-serveur-2026-11 |
| Commit de départ | ffdc260c03703b5a196e24cb73f308ebc29b16a0 |
| Date | 2026-11-16 |
| Orchestrateur | Codex |
| Relecteur | Agent indépendant, puis architecte-relecteur et Fondateur |
| Autorité finale | Camille Perraudeau (Fondateur) |

## Mission

Lever les blocages de la PR nº 74 dans le périmètre fixé, en respectant
l'ordre A à F de la mission consolidée du Fondateur du 16 novembre 2026.
La déclaration du Fondateur est explicite : aucune base hébergée ni donnée
réelle n'existe ; la base Docker locale est jetable. DEC-000094 n'est pas
validée en l'état et doit être révisée vers la solution la plus simple.

L'inventaire de 43 références locales et distantes trouve un maximum de
GSIE-PROMPT-0033 ; le présent prompt réserve le numéro 0034.

## Pourquoi maintenant

La relecture de `ffdc260` confirme les trois branches réunies et les contrôles
de gouvernance conformes. Les blocages restants concernent le corpus de
GSIE-PROMPT-0032, la complexité de réconciliation des migrations, une garde
de géométrie inaccessible, les alertes de sécurité, MinIO et la concurrence.

## Documents obligatoires

- `AGENTS.md`, `GSIE/API/AGENTS.md`, `GSIE/API/README.md`.
- Constitution applicable, ADR-009 et processus d'orchestration des agents.
- `GSIE/PROMPTS/TEMPLATE_TASK.md`, `REGISTER.md`, prompts 0032 et 0033.
- DEC-000073, DEC-000093, DEC-000094 et RFC-0041.
- Bilan de réconciliation serveur du 16 novembre, contrats des migrations,
  Dockerfile canonique, verrou des dépendances et workflows réels.
- Skills `consortium-agents`, `securite-gsie`, `tests-gsie`,
  `gsie-governance`, `git-flow-gsie` et `deploiement`.

## Périmètre autorisé

1. **A — Documents.** Intégrer le commit
   `57121c81729c98ef882157f4b27f0ef660336bfe` par une fusion locale dans la
   branche d'intégration. Résoudre REGISTER par union sans renumérotation.
2. **B — Migrations.** Inventorier les bases connues avant toute suppression.
   Si une base hors test/CI porte `20260908_0051`, suspendre la suppression
   et le signaler. Sinon conserver la seule création `20260823_0051`,
   parent direct de `20260826_0052`, retirer les seuls éléments de compatibilité
   sans autre usage et rétablir `as_sql`. Réviser DEC-000094 en `Draft` et
   documenter la recréation des anciennes bases de développement. Adapter
   les tests à cette spécification sans perdre les invariants utiles.
3. **C — Cubage.** Déterminer si la garde non couverte protège une entrée
   réelle. La tester si elle est accessible ; sinon proposer son retrait
   précis, mais ne pas le réaliser sans accord explicite.
4. **D — Sécurité.** Corriger les 21 alertes corrigeables par montée de version
   des dépendances et images concernées. Garder des versions et empreintes
   vérifiées. Pour chaque impossibilité, consigner raison, preuve et risque.
5. **E — MinIO.** Identifier la cause du refus et proposer une source durable,
   épinglée et vérifiée par empreinte. Aucune substitution de fournisseur
   ni mise en production n'est déduite d'une simple proposition.
6. **F — Concurrence.** Reproduire la course `ix_resource_gsie_id`, expliquer
   sa cause et proposer un correctif. Ne pas ajouter de tentative automatique
   dans le test ni modifier le moteur au titre d'une proposition seule.

La traçabilité du lot et les mentions de tête/procédure devenues inexactes
sont actualisées de manière ciblée ; aucune refonte documentaire générale.

## Non-objectifs

- Fusionner une demande de fusion ou écrire sur `main`.
- Déployer, migrer des données réelles ou qualifier scientifiquement le serveur.
- Implémenter les corrections seulement demandées en proposition, sans accord.
- Modifier une règle scientifique ou élargir les fonctionnalités BFF.

## Interdictions

- Aucun push sur `main`, aucune fusion de PR, aucune réécriture d'historique.
- La seule fusion locale autorisée est celle explicitement demandée au point A.
- Aucun document `Locked` modifié et aucune promotion de DEC-000094.
- Aucun test affaibli, seuil abaissé, exclusion de couverture ou CVE masquée.
- Aucune suppression avant l'inventaire des bases et des usages réels.
- Aucun secret dans les commits, rapports ou sorties affichées.
- Aucune suppression de volume ou base existante pour contourner une vérification.

## Conditions d'arrêt

Suspendre l'action concernée en présence d'une révision historique sur une base
connue hors test/CI, d'une donnée réelle contredisant la déclaration initiale,
d'un besoin scientifique absent, d'un document Locked à modifier ou d'un accord
explicite requis non reçu. Continuer les travaux indépendants autorisés.

## Méthode attendue

- Vérifier les références et le périmètre avant chaque incrément.
- Séparer architecte, implémenteur, testeur et reviewer ; un seul auteur par fichier.
- Exécuter l'ordre A à F, garder les propositions distinctes des modifications.
- Conserver les preuves rouges, leurs causes et les résultats après correction.
- Contrôler le diff, les tests utiles et les sorties des outils avant publication.
- Actualiser la même PR et pousser une sauvegarde distante datée en fin de session.

## Validations obligatoires

```text
python3 tools/check_governance_consistency.py
python3 tools/check_source_of_truth.py
python3 tools/check_ai_prompts.py
python3 tools/check_build_consistency.py
python -m alembic heads
python -m pytest tests/ -q
```

Ajouter la génération SQL hors ligne et les tests de schéma/migration utiles,
les contrôles de compatibilité des dépendances et un vrai scan de l'image
construite. Ne pas présenter un scan de verrou comme un scan de l'image.

## Critères d'acceptation

- Union documentaire de 0032/0033/0034, sans conflit ni renumérotation.
- Inventaire préalable des bases consigné ; décision de simplification respectée.
- Une tête, une création d'intake, SQL hors ligne et procédure de recréation.
- Résultats vérifiables pour les alertes, sans exceptions silencieuses.
- Propositions cubage, MinIO et concurrence concrètes et soumises aux limites fixées.
- Aucun changement de statut Draft sans relecture/validation applicable.
- Publication sur la branche d'intégration et sauvegarde distante relue.

## Rapport final obligatoire

Remettre le hash final, `alembic heads`, les tests et quatre contrôles avec
codes de sortie, la CI job par job et, pour chaque point A à F : fait,
non fait ou bloqué avec la raison. Indiquer les accords reçus, les limites
de vérification, les risques résiduels et la référence de sauvegarde.
