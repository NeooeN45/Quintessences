# Levée des blocages PR74 — GSIE-PROMPT-0034

| Champ | Valeur |
|---|---|
| **Identifiant** | AUDIT-LEVEE-BLOCAGES-PR74-2026-11-16 |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Date** | 2026-11-16 |
| **Auteur** | Codex, consortium spécialisé et relecteur indépendant |
| **Mission** | [GSIE-PROMPT-0034](../../GSIE/PROMPTS/GSIE-PROMPT-0034-lever-blocages-pr-74.md) |
| **Branche** | `integration/reconciliation-serveur-2026-11` |
| **PR** | [nº 74](https://github.com/NeooeN45/Quintessences/pull/74) |
| **Départ** | `ffdc260c03703b5a196e24cb73f308ebc29b16a0` |
| **Décision technique** | [DEC-000094 révisée — Draft](../../03_DECISIONS/DEC-000094.md) |
| **Autorité finale** | Camille Perraudeau (Fondateur) |

## 1. Objet et accords reçus

La mission reprend les six points A à F fixés le 16 novembre : union
documentaire, simplification des migrations, garde cubage, alertes Trivy,
accès MinIO et course concurrente. Les preuves de la solution antérieure
ne remplacent pas celles de la nouvelle lignée ou de l'image corrigée.
Les résultats non reçus restent **EN ATTENTE**.

Le Fondateur a déclaré qu'aucune base hébergée ni donnée métier réelle n'existe
et que la base Docker locale est jetable. L'inventaire a déclenché l'arrêt
prévu en retrouvant deux bases locales marquées B hors d'un périmètre
explicitement labellisé test/CI. Après signalement, l'accord complémentaire
**« Autoriser la simplification et la recréation documentée »** a été reçu.
Il porte sur le code et la procédure ; aucune base ni aucun volume original
n'est supprimé dans ce lot.

Un accord explicite a aussi été reçu pour retirer uniquement les deux lignes
de la garde cubage inaccessible, après les huit tests prévus et après B.
E et F demandent une reproduction, une analyse et une proposition ; aucune
modification de fournisseur, du moteur ou du test de course n'en est déduite.
DEC-000094 reste `Draft`.

## 2. Matrice d'avancement A à F

| Point | Faits et décision applicable | État à la rédaction | Preuve et suite |
|---|---|---|---|
| A — Documents | Fusion de `57121c81729c98ef882157f4b27f0ef660336bfe` ; union des missions 0032, 0033 et 0034 sans renumérotation | FAIT pour la fusion locale ; contrôles finaux à refaire | Fusion `a7d494e7c4353a729f5e7f1c76b7ba0a328ac184` ; quatre contrôles à 0 rapportés après A |
| B — Migrations | Une création `20260823_0051`, parent direct de `0052` ; retrait B/helper/`0060` sans autre usage métier identifié ; tête `20260929_0059` | AUTORISÉ ; implémentation et preuves finales EN ATTENTE | Inventaire relu, arrêt puis accord reçus ; DEC-000094 et procédure révisées |
| C — Cubage | `if not positions` après `visit(value)` inaccessible pour une entrée JSON finie normale ; retrait des deux lignes autorisé | AUTORISÉ ; retrait, huit tests et couverture EN ATTENTE | Conserver bornes WGS84 et refus des structures invalides ; aucune exclusion de couverture |
| D — Sécurité | Baseline de 21 alertes corrigeables : 10 système et 11 bibliothèques, 17 HIGH et 4 CRITICAL | Corrections, construction et rescan EN ATTENTE | `dep-baseline-21.json` ; versions/digests et compatibilité à prouver, aucune alerte masquée |
| E — MinIO | Derniers jobs bloqués sur `minio/minio` ; refus de `minio/mc` dans un premier run | Reproduction actuelle et proposition durable EN ATTENTE | Source, version, digest et téléchargement à prouver ; aucun changement de fournisseur présumé |
| F — Concurrence | Échec CI hérité sur `ix_resource_gsie_id` avec huit sessions indépendantes | Reproduction ciblée et proposition EN ATTENTE | Aucun retry ajouté au test, aucun correctif moteur déduit de la proposition |

## 3. A — Union documentaire et traçabilité

Le commit de fusion observé a pour parents
`ac20c334694e2b07118e6ea046589efc6bdcfe04` et
`57121c81729c98ef882157f4b27f0ef660336bfe`. Il intègre GSIE-PROMPT-0032,
exclu du lot précédent, par l'autorisation propre au point A.
Cela n'atteste aucune fusion des PR nº 73 ou nº 74 dans `main`.

REGISTER conserve GSIE-PROMPT-0032 `EN_REVUE`, GSIE-PROMPT-0033 `EN_REVUE`
et GSIE-PROMPT-0034 `EN_COURS`. DEC-000093 enregistre la validation avec
mise à jour des principes GeoSylva et du chemin BFF ; RFC-0041 reste `Draft`.
Cette intégration n'homologue pas les écarts métier E01 à E06 et ne modifie
aucune règle scientifique.

L'inventaire des identifiants couvre 43 références, maximum 0033 ; 0034 est
réservé sans renuméroter l'historique. Preuve :
`/workspace/outputs/2026-11-16/pr74-blocages/inventaire-identifiants.json`.
Les quatre contrôles après A ont été rapportés à 0 ; ils restent à reproduire
sur le commit final.

## 4. B — Inventaire, arrêt et simplification

### 4.1 Sources inspectées

L'inventaire `2026-11-16T17:31:21.835334+00:00` a monté les originaux
en lecture seule et inspecté des copies jetables, sans réseau ni ports publiés.
Il ne consulte que les bases et marqueurs Alembic. Les deux inspections ont
réussi ; les copies d'audit ont été retirées.

| Volume original, conservé | Bases constatées | Marqueurs |
|---|---|---|
| `gsie-onboarding-pgdata` | `gsie`, `postgres` | Aucune table Alembic détectée |
| `gsie-onboarding-pgdata-v2` | `gsie` ; `gsie_pack_recipe_20261002` | `20260908_0051` dans chacune |
| Même volume | `gsie_hierarchy_full_test_20261003` | `20261003_0052`, inconnue de cette branche |
| Même volume | `gsie_hierarchy_test_20261003` ; `postgres` | Aucune table Alembic détectée |

Les volumes onboarding n'ont pas de label Docker explicite test/CI.
`has_revision_B_outside_identified_tests_ci=true` a donc déclenché l'arrêt.
L'accord complémentaire a ensuite autorisé la simplification et sa procédure
de recréation. Aucune suppression d'original n'en a été déduite. Aucune base
`0060` n'est signalée par cet inventaire.

L'absence de marqueur ne prouve pas qu'une base est vide. L'absence de données
réelles et d'hébergement repose sur la déclaration explicite du Fondateur,
sans recherche externe. La recette hiérarchie à révision inconnue reste
intacte et ne reçoit aucun chemin de conversion inventé.

Preuves locales hors du dépôt :

- `/workspace/outputs/2026-11-16/pr74-blocages/revisions-locales.json` ;
- `/workspace/outputs/2026-11-16/pr74-blocages/inspecter-revisions-locales.py`.

### 4.2 Lignée et éléments retirés

~~~text
20260726_0001 → … → 20260815_0050
  → 20260823_0051 → 20260826_0052
  → 0053 → 0054 → 0055 → 0056 → 0057 → 0058
  → 20260929_0059
~~~

Le contrat reste celui de la création A : 17 colonnes, quatre contraintes
et quatre index explicites. Quarantaine, provenance, idempotence, hydratation
et préparation stationnelles restent à vérifier sans ajout de données.

| Élément | Traitement attendu |
|---|---|
| `20260823_0051_field_intake.py` | Création conservée, sans réécriture |
| `20260826_0052_billing_schema_usage.py` | Parent direct remis à `20260823_0051` |
| `20260908_0051_field_intake.py` et `20261116_0060_reconciliation_field_intake.py` | Retrait du dossier actif |
| `alembic/compatibility/field_intake_v1.py` | Retrait après vérification de l'absence d'autre usage métier |
| `20260801_0027_indexes_enrichissement.py` | Garde anti-doublons maintenue dans le SQL hors ligne avant l'index unique |
| Tests de lignée et migration | Adapter à une création, une tête, SQL hors ligne et invariants utiles |

La génération `--sql` doit réussir sans connexion et contenir la garde
anti-doublons avant l'index. Son émission ne prouve pas l'exécution PostgreSQL ;
les deux modes sont contrôlés séparément. Le bilan GSIE-PROMPT-0033 décrit
la solution B/`0060` alors testée. Son annotation historique relève de
l'orchestrateur ; il n'est pas réécrit par ce rôle.

### 4.3 Procédure de recréation, à exécuter ultérieurement

La procédure est dans le
[README API](../../GSIE/API/README.md#contrat-de-migration).
Elle identifie la source, arrête seulement ses écrivains et crée une nouvelle
base vide distincte. Les services libpq et l'URL de migration sont explicites,
sans affichage de secret. La nouvelle base reçoit `20260929_0059` avant
vérification du schéma et des tests.

Les anciennes bases de développement B ou `0060` ne sont pas mises à niveau
par `stamp`, modification du marqueur ou downgrade. L'originale reste conservée,
associée à son ancienne version applicative. Aucune base existante, aucun
volume global ni donnée MinIO n'est supprimé par cette mission.

## 5. C — Retrait borné de la garde cubage

Dans `geosylva/cubage_schemas.py`, `visit(value)` ajoute une position valide
ou lève une erreur pour les structures JSON finies acceptées. Le refus
`if not positions` placé juste après n'est donc pas une frontière accessible.
L'accord reçu autorise son seul retrait de deux lignes, après B et les huit
tests requis.

À joindre : diff exact, commande et JUnit des huit tests, maintien des refus
sur entrées invalides et couverture du module. Aucun passage à 100 % n'est
déclaré à ce stade. Les bornes WGS84, le refus des booléens et des structures
invalides, ainsi que la politique DEC-000066 restent applicables.

## 6. D — Dépendances et image à rescanner

`/workspace/outputs/2026-11-16/pr74-blocages/dep-baseline-21.json` extrait
la baseline du scan d'image précédent : 21 occurrences corrigeables,
17 HIGH et 4 CRITICAL, dont 10 système et 11 Python. Ce relevé ne constitue
pas un nouveau scan de l'image corrigée.

Le lot D doit relier chaque occurrence à la version effectivement installée
après correction ou à un blocage motivé. Le Dockerfile canonique reste
`GSIE/API/Dockerfile` ; versions, digests et verrou effectif sont à contrôler.
L'audit du verrou ne remplace pas le scan du runtime construit.

| Preuve D attendue | État |
|---|---|
| Avant/après des 21 occurrences, versions et impossibilités motivées | EN ATTENTE |
| Compatibilité avec les nouvelles dépendances | EN ATTENTE |
| Construction réelle depuis le Dockerfile canonique, SHA/digest de l'image | EN ATTENTE |
| Scan Trivy de cette image, scanner/base, code et rapport | EN ATTENTE |

Aucune CVE n'est masquée, aucun seuil n'est abaissé et aucune exclusion n'est
déduite de ce bilan. Les versions corrigées ne sont pas annoncées sans preuve.

## 7. E et F — Propositions sans implémentation implicite

### 7.1 MinIO

Le dernier bilan documente le refus de `minio/minio` avant Data Registry
et HA ; un premier run avait aussi échoué sur `minio/mc`. La reproduction
actuelle, la cause exacte et une source durable sont encore attendues.
La proposition devra donner version, plateforme, digest, empreinte et test
de téléchargement. Une alternative disponible ne vaut ni autorisation de
substitution de fournisseur, ni validation HA.

### 7.2 Course ix_resource_gsie_id

Le bilan précédent relève un échec CI avec huit sessions indépendantes dans
`tests/integration/test_orchestration.py` :
`test_analyses_concurrentes_avec_sessions_independantes_sont_persistantes`.
La collision apparaît pendant la matérialisation de l'agent moteur dans
`engines/recommendation/engine.py`. Une reproduction ciblée de cette mission
reste attendue.

L'ancien diagnostic opposait `ON CONFLICT (id) DO NOTHING` à l'autre unicité
sur `gsie_id` et proposait une variante sans cible pour la racine.
Ce n'est pas un correctif appliqué par ce lot. La nouvelle analyse doit
confirmer cause, collisions cohérentes/incohérentes et invariants de métadonnées
avant une proposition précise. Aucun retry automatique n'est ajouté au test.

## 8. Contrôles finaux et publication

Pour chaque exécution, joindre commande réelle, environnement, SHA testé,
code, artefact et inventaire des ignorés. « EN ATTENTE » n'est pas un succès.

| Commande ou preuve | Résultat / code |
|---|---|
| Racine : `python3 tools/check_governance_consistency.py` | Après A : 0 rapporté ; tête finale EN ATTENTE |
| Racine : `python3 tools/check_source_of_truth.py` | Après A : 0 rapporté ; tête finale EN ATTENTE |
| Racine : `python3 tools/check_ai_prompts.py` | Après A : 0 rapporté ; tête finale EN ATTENTE |
| Racine : `python3 tools/check_build_consistency.py` | Après A : 0 rapporté ; tête finale EN ATTENTE |
| API : `.venv/bin/python -m alembic heads` | EN ATTENTE ; cible unique `20260929_0059 (head)` |
| API : SQL `upgrade base:head --sql` sans connexion | EN ATTENTE ; une création et garde anti-doublons exigées |
| API : migrations et invariants PostgreSQL jetable | EN ATTENTE ; bases/containers à identifier |
| API : huit tests cubage et couverture | EN ATTENTE |
| API : `.venv/bin/python -m pytest tests/ -q` | EN ATTENTE ; aucun ignoré présumé passé |
| Lint, typage, mutation et couverture combinée | EN ATTENTE ; mêmes portes et seuils |
| Image reconstruite, compatibilité, Trivy réel | EN ATTENTE |
| Reproductions et propositions MinIO / concurrence | EN ATTENTE ; échecs conservés |
| Revue indépendante du diff final | EN ATTENTE |
| Commit final identique au worktree testé | EN ATTENTE |
| CI : URL, SHA, événement et résultat de chaque job | EN ATTENTE ; ignorés/annulés et causes explicites |
| Mise à jour de PR nº 74 et sauvegarde distante datée | EN ATTENTE ; SHA de sauvegarde relu à distance |

Aucune fusion de PR, aucun push sur `main` et aucun déploiement n'est autorisé
par la remise. E et F restent limités à leur proposition.

## 9. Risques et limites

| Risque ou limite | Traitement |
|---|---|
| Bases B/`0060` inconnues de la nouvelle lignée | Nouvelle base vide ; pas de conversion conservatoire |
| Révision `20261003_0052` de la recette hiérarchie | Original intact, diagnostic séparé |
| Inventaire limité aux volumes connus | Déclaration du Fondateur distinguée ; arrêt si donnée réelle découverte |
| SQL seulement émis | Exécution PostgreSQL et garde anti-doublons à prouver séparément |
| Retrait cubage dépassant les deux lignes autorisées | Diff et tests adversariaux avant acceptation |
| Versions ou images incompatibles | Verrou, construction, tests et scan de l'image effective |
| MinIO indisponible | Aucun Registry/HA annoncé passé avant exécution réelle |
| Course non reproduite ou non corrigée | Test concurrent conservé ; proposition distincte du code |
| Contrôles ou CI incomplets | Remise en revue avec réserves, sans acceptation globale |
| Floorplan indisponible | Aucune carte créée ou actualisée ; analyse des sources |

## 10. Sources et historique

- [GSIE-PROMPT-0034](../../GSIE/PROMPTS/GSIE-PROMPT-0034-lever-blocages-pr-74.md),
  instruction et accord complémentaire du Fondateur le 16 novembre.
- [DEC-000094 révisée — Draft](../../03_DECISIONS/DEC-000094.md),
  [README API](../../GSIE/API/README.md#contrat-de-migration) et
  [bilan historique de GSIE-PROMPT-0033](RECONCILIATION_SERVEUR_2026-11-16.md).
- [DEC-000093](../../03_DECISIONS/DEC-000093.md) et
  [RFC-0041](../../02_RFC/RFC-0041-contrat-facade-geosylva-identite-stationnelle.md) :
  intégration A, sans extension de cette mission au métier.
- [DEC-000066](../../03_DECISIONS/DEC-000066.md),
  [contrôle documentaire](../PROCESSES/DOCUMENT_CONTROL.md) et
  [orchestration IA](../PROCESSES/AI_AGENT_ORCHESTRATION.md).
- Inventaires et artefacts locaux indiqués, conservés hors du dépôt.

| Date | Événement |
|---|---|
| 2026-11-16 | Bilan A–F créé : fusion A, inventaire et accords tracés, procédure révisée ; autres résultats à compléter avant remise |
