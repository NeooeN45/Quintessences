# Réconciliation serveur — GSIE-PROMPT-0033

| Champ | Valeur |
|---|---|
| **Identifiant** | AUDIT-RECONCILIATION-SERVEUR-2026-11-16 |
| **Statut documentaire** | Draft — preuves finales à compléter par l'orchestrateur |
| **État de remise** | EN_REVUE ; aucune auto-approbation ni autorisation de fusion |
| **Version** | 1.0.0 |
| **Date** | 2026-11-16 |
| **Auteur** | Codex, avec analyses indépendantes d'architecture et de qualité |
| **Mission** | [GSIE-PROMPT-0033](../../GSIE/PROMPTS/GSIE-PROMPT-0033-reconciliation-serveur.md) |
| **Branche** | `integration/reconciliation-serveur-2026-11` |
| **Worktree** | `/workspace/quintessences-integration-2026-11` |
| **Décision proposée** | [DEC-000094 — Draft](../../03_DECISIONS/DEC-000094.md) |
| **Autorité finale** | Camille Perraudeau (Fondateur) |

## 1. Résumé et limites de la remise

La réconciliation conserve les deux contrats d'intake équivalents et les
identifiants de migration déjà publiés. Elle prépare une seule lignée Alembic,
avec une création historique et deux validations explicites du schéma, pour
préserver les bases issues de `main` et de `feat/schemas-de-domaine`.

Ce bilan distingue les preuves déjà observées des campagnes encore en attente.
Les résultats de tests, de CI et de sauvegarde distante laissés « EN ATTENTE »
doivent être complétés à partir des artefacts avant acceptation technique.
Aucune base utilisateur n'est migrée par cette mission ; aucun succès local
ne vaut qualification du serveur en production.

## 2. Sources, chronologie et périmètre Git

### 2.1 Snapshots d'origine

| Origine | SHA figé | Rôle |
|---|---|---|
| `feat/schemas-de-domaine` | `9e6864b353c8c03d15c067dffd2b358f7a57d94f` | Départ de l'intégration ; lignée jusqu'à `20260929_0059` |
| `main` | `d7b400cb15d9f2216f3296d92754a6e67e55a63f` | Première fusion |
| `chore/securite-depots-2026-10-18` | `e3e18d47cfae176077473962d910e0df30125cc3` | Seconde fusion, après stabilisation de la première |
| PR nº 73 | Non fusionnée au cadrage | Exclue ; aucun de ses cinq documents n'est copié implicitement |

L'inventaire de l'orchestrateur du 16 novembre porte sur 41 références locales
et distantes : maximum GSIE-PROMPT-0032 et DEC-000093. La mission réserve
GSIE-PROMPT-0033 et la proposition technique DEC-000094 sans renuméroter
les documents déjà publiés.

### 2.2 Jalons de l'intégration

| Jalon | Preuve ou état |
|---|---|
| Cadrage versionné | `efb682b247e8e9e36af179f48af3466775855a54` |
| Fusion de `main` | `e0c71272f9bcd6e01b032b4099615cbf9ea3ee2e` |
| Parents de cette fusion | `efb682b247e8e9e36af179f48af3466775855a54` et `d7b400cb15d9f2216f3296d92754a6e67e55a63f`, relus par `git show -s --format='%H%n%P%n%s' HEAD` |
| Commit de compatibilité des migrations | `c81b5b1` ; durcissement final et correctifs de contrôles dans `df4aea9` |
| Fusion du snapshot sécurité | `2b9f191265bc3475fe417163355ad399dc75eec9` ; parents `c81b5b1` et `e3e18d4` |
| Commit final remis en revue | EN ATTENTE |
| PR vers `main` et URL | EN ATTENTE |
| Sauvegarde distante datée et SHA relu sur GitHub | EN ATTENTE |

L'historique est conservé par des fusions ordinaires. Les publications et la PR
restent limitées à la branche d'intégration ; aucun push sur `main`, aucune
fusion de PR, aucun déploiement et aucune réécriture d'historique n'entrent
dans la remise.

### 2.3 Apports hérités et travail propre à la réconciliation

| Lot | Origine et traitement |
|---|---|
| Serveur déjà présent dans `feat` | Migrations `0052` à `0059`, contrats Forge/TEST, hydratation et préparation stationnelles, BFF GeoSylva et protections existantes sont des apports hérités ; cette mission ne les présente pas comme des fonctionnalités nouvellement développées |
| Apports de `main` | CI et couverture combinée, Docker, tests d'identité/intake et de routeurs, documents qualité/recherche hérités ; conservation du contenu utile des deux branches |
| Apports du snapshot sécurité | Trois commits et 24 fichiers modifiés depuis `main` : contrôles de dépôt, secrets et workflows, verrou API et corrections de dépendances, SECURITY et documents datés ; intégration et vérifications finales encore à tracer |
| Nouveau travail de réconciliation | Résolution des quatre conflits, génération OpenAPI, compatibilité des deux `0051`, validation finale `0060`, tests des historiques et de conservation, revue de fraîcheur, présent bilan et DEC-000094 `Draft` |
| Pilotage documentaire | Textes de synchronisation proposés en section 8 ; aucune réécriture de `PROJECT_MEMORY.md`, `ROADMAP.md` ou `CHANGELOG.md` déduite de ces propositions |

Les preuves historiques du 18 octobre, notamment l'audit d'un export de
128 dépendances et le blocage HA sur le téléchargement de `minio/mc`, restent
des constats datés. Elles ne qualifient ni le verrou final du 16 novembre, ni
les images actuelles, ni la CI de cette branche. DEC-000092 reste une
instruction consignée en `Draft` ; sa présence n'atteste pas que les dépôts
ont changé de visibilité.

L'analyse indépendante identifie les changements PyJWT 2.13.0 → 2.15.0,
multidict 6.7.1 → 6.9.1 et urllib3 2.7.0 → 2.8.0. Elle relève aussi le
retrait du marqueur `sys_platform != 'win32'` sur `eccodeslib → eckitlib` :
la compatibilité Windows n'est pas acquise par les seuls essais Linux.

Dans l'apport propre `main → sécurité`, la revue préalable n'identifie
aucune modification des migrations, des sources d'authentification ou des
tests API existants. Elle relève Gitleaks masqué et contrôlé par empreinte,
les gardes de fichiers sensibles, les checkouts sans conservation des
identifiants, les rapports privés limités à sept jours, l'arrêt de Pages pour
un dépôt privé et le remplacement du robot de verrou à droits d'écriture par
Dependabot uv natif. Ces constats de diff ne sont pas des tests exécutés.

## 3. Résolution des quatre conflits de la fusion de main

| Fichier | Résolution et raison | Preuve disponible |
|---|---|---|
| `GSIE/API/src/gsie_api/infrastructure/models/__init__.py` | Un seul import `field_intake` ; conservation de `geosylva_analysis` et `geosylva_cubage`, nécessaires aux modèles hérités de `feat` | Registre relu après résolution |
| `GSIE/API/tests/unit/test_routers_coverage_ext.py` | Union intégrale des trois méthodes de mapping de `feat` et des deux méthodes de traduction de `main` ; assertions conservées | 49 scénarios réussis, XML et log en section 6 |
| `GSIE/API/tests/unit/test_migration_contract.py` | Tête attendue alignée sur `20261116_0060` ; assertions de lignée conservées et complétées par des tests des deux identifiants historiques | Résultat final EN ATTENTE |
| `GSIE/API/docs/openapi.json` | Régénération par `scripts/extract_openapi.py` depuis l'application fusionnée, avec son mécanisme de fallback Evidence Python ; aucune fusion manuelle des schémas JSON | 151 chemins, 299 schémas, version 0.1.0 ; commande en section 6 |

Les méthodes `should_map_analyse_hydration_errors`,
`should_map_context_preview_errors` et
`should_map_station_preparation_errors` de `feat` sont conservées avec
`should_translate_hydration_errors_during_analyse` et
`should_translate_hydration_errors_during_preview` de `main`.
Les deux méthodes de `main` gardent l'égalité exacte
`response.json()["detail"] == str(exception)`. Leurs assertions ne sont pas
remplacées par les seuls contrôles de sous-chaîne présents dans l'autre lot.

La génération observée suit la première fusion. Après la fusion sécurité,
une relecture indépendante constate l'égalité avec `app.openapi()` :
aucune route des parents n'est perdue. Le contrôle distant reste distinct.

### 3.1 Conflits supplémentaires de la fusion sécurité

Cette seconde fusion produit cinq conflits, résolus dans `2b9f191` :

| Fichier | Résolution et raison |
|---|---|
| `.gitignore` | Union des exclusions de résultats de tests et des protections des clés et signatures ; aucune protection supprimée |
| `23_QUALITY_MANAGEMENT/SOURCE_OF_TRUTH_REGISTRY.json` | Conservation des dates plus récentes de `feat` pour les corpus sans rapport ; revue ciblée des deux corpus échus décrite en section 7 |
| `PROJECT_MEMORY.md` | Métadonnées et bloc sécurité du 18 octobre, puis historique de `feat` conservé ; lien erroné DEC-000092 corrigé vers le fichier existant |
| `ROADMAP.md` | Bloc daté de sécurité puis historique `feat`, sans clôture nouvelle de tâche |
| `CHANGELOG.md` | Section sécurité du 18 octobre et historique `feat` conservés ; doublons anciens laissés visibles |

Ces trois vues héritent du contenu de la fusion. Leur synchronisation nouvelle
au 16 novembre est seulement proposée en section 8.

## 4. Comparaison des deux créations de field_intake

### 4.1 Méthode et contrat de colonne

Les migrations ont été lues directement dans les snapshots d'origine :

- `9e6864…:GSIE/API/alembic/versions/20260823_0051_field_intake.py` ;
- `d7b400c…:GSIE/API/alembic/versions/20260908_0051_field_intake.py`.

Les 17 colonnes correspondent par nom. « Sans défaut » désigne l'absence de
défaut serveur dans les deux migrations ; les valeurs Python appliquées par
l'ORM ne sont pas des défauts du schéma SQL.

| Colonne | Définition dans `feat` | Définition dans `main` | Conclusion |
|---|---|---|---|
| `id` | UUID, non nul, PK, sans défaut | UUID, non nul, PK explicite, sans défaut | Identique |
| `created_at` | TIMESTAMP WITH TIME ZONE, non nul, `func.now()` | TIMESTAMP WITH TIME ZONE, non nul, `text("now()")` | Même défaut SQL `now()` |
| `updated_at` | TIMESTAMP WITH TIME ZONE, non nul, `func.now()` | TIMESTAMP WITH TIME ZONE, non nul, `text("now()")` | Même défaut SQL `now()` |
| `submitted_by` | UUID, non nul, sans défaut | UUID, non nul, sans défaut | Identique ; aucune FK vers un compte dans ces créations |
| `application_key` | VARCHAR(100), non nul, sans défaut | VARCHAR(100), non nul, sans défaut | Identique |
| `client_event_id` | VARCHAR(200), non nul, sans défaut | VARCHAR(200), non nul, sans défaut | Identique |
| `kind` | VARCHAR(40), non nul, sans défaut | VARCHAR(40), non nul, sans défaut | Identique |
| `observed_at` | TIMESTAMP WITH TIME ZONE, non nul, sans défaut | TIMESTAMP WITH TIME ZONE, non nul, sans défaut | Identique |
| `received_at` | TIMESTAMP WITH TIME ZONE, non nul, `func.now()` | TIMESTAMP WITH TIME ZONE, non nul, `text("now()")` | Même défaut SQL `now()` |
| `status` | VARCHAR(20), non nul, sans défaut | VARCHAR(20), non nul, sans défaut | Identique |
| `payload` | JSONB, non nul, sans défaut | JSONB avec `astext_type=Text()`, non nul, sans défaut | Même type SQL JSONB |
| `provenance` | JSONB, non nul, sans défaut | JSONB avec `astext_type=Text()`, non nul, sans défaut | Même type SQL JSONB |
| `payload_hash` | VARCHAR(64), non nul, sans défaut | VARCHAR(64), non nul, sans défaut | Identique |
| `target_resource_id` | UUID, nullable, FK vers `resource.id`, sans défaut | UUID, nullable, FK explicite vers `resource.id`, sans défaut | Identique |
| `review_notes` | TEXT, nullable, sans défaut | TEXT, nullable, sans défaut | Identique |
| `reviewed_by` | UUID, nullable, sans défaut | UUID, nullable, sans défaut | Identique |
| `reviewed_at` | TIMESTAMP WITH TIME ZONE, nullable, sans défaut | TIMESTAMP WITH TIME ZONE, nullable, sans défaut | Identique |

Dans `feat`, `created_at` et `updated_at` précèdent `submitted_by` ;
dans `main`, elles suivent `reviewed_at`. L'UUID et JSONB importés
directement du dialecte PostgreSQL ou via `postgresql` produisent les mêmes
types SQL. L'ordre physique n'impose aucune réécriture de table.

### 4.2 Contraintes et index

| Objet | Contrat commun aux deux migrations |
|---|---|
| Clé primaire | `id` ; écriture sur la colonne dans `feat`, `PrimaryKeyConstraint("id")` dans `main` |
| Clé étrangère | `target_resource_id → resource.id` ; mêmes options par défaut |
| `uq_field_intake_application_event` | UNIQUE(`application_key`, `client_event_id`), dans cet ordre |
| `ck_field_intake_status` | `status IN ('quarantined', 'accepted', 'rejected')` |
| `ix_field_intake_submitted_by` | Index non unique sur `submitted_by` |
| `ix_field_intake_target_resource_id` | Index non unique sur `target_resource_id` |
| `ix_field_intake_submitted_by_received` | Index non unique sur `submitted_by`, `received_at`, dans cet ordre |
| `ix_field_intake_status_received` | Index non unique sur `status`, `received_at`, dans cet ordre |

Les quatre contraintes de table incluent la PK et la FK. Les quatre index
énumérés sont les créations explicites des migrations ; les index de support
de la PK et de l'unicité ne sont pas comptés comme des créations supplémentaires.

### 4.3 Consommateurs examinés

| Source | Invariant à préserver |
|---|---|
| `infrastructure/models/field_intake.py` et `TimestampMixin` | Même table, UUID, types, nullabilité, contraintes et index |
| `data/field_intake.py` et `data/field_intake_router.py` | Quarantaine, provenance, hash canonique et idempotence sur application/événement ; sauvegarde transactionnelle lors d'une course |
| `data/analysis_bundle_import.py` et `data/gsie_test_bundle.py` | Import TEST persistant dans le sas existant, sans promotion scientifique implicite |
| `engines/orchestration/hydration.py` | Observations `kind="observation"` acceptées uniquement ; bundles Forge exclus, tri déterministe date/UUID |
| `engines/orchestration/preparation.py` | Lecture d'un intake accepté ciblant la station, validation de l'état global et de sa provenance |
| `geosylva/publication.py` | Référence durable à l'UUID d'intake de l'état global |
| `20260929_0058_purge_geosylva_anonymisation_intake.py` | Fonction de finalisation RGPD existante et anonymisation prévue de `submitted_by` ; aucun nouveau comportement de purge dans cette mission |

La comparaison du schéma ne prouve pas à elle seule la conformité de tous ces
usages : leurs tests restent nécessaires. Aucune valeur manquante, qualification,
règle métier ou conversion de JSON n'est fabriquée pendant la réconciliation.

## 5. Solution de migration et sort des bases existantes

La [proposition DEC-000094](../../03_DECISIONS/DEC-000094.md) conserve les
deux fichiers et identifiants. Le helper figé
`GSIE/API/alembic/compatibility/field_intake_v1.py` doit valider le contrat
complet sans importer les modèles applicatifs ni écrire dans les données.
Le fichier `20260908_0051` change volontairement de contenu et de parent,
en conservant son identifiant ; cette modification est versionnée et ne
réécrit pas l'historique Git. La baseline et la création `20260823_0051`
restent inchangées.

~~~text
20260815_0050
  → 20260823_0051  création historique inchangée
  → 20260908_0051  validation de compatibilité, sans DDL
  → 20260826_0052  parent ajusté
  → 0053 → 0054 → 0055 → 0056 → 0057 → 0058 → 0059
  → 20261116_0060  validation commune, sans DDL
~~~

| Base de départ | Exécution attendue | Garantie à prouver |
|---|---|---|
| Neuve | Baseline puis toute la lignée ; création d'intake une seule fois | Schéma complet et une tête |
| À `20260815_0050` | Création par `20260823_0051`, alias de compatibilité, suite | Schéma conforme ; aucune création concurrente |
| `main` à `20260908_0051` | `0052` à `0059`, puis `0060` | Aucune réexécution de l'une ou l'autre `0051` ; données conservées |
| `feat` à `20260929_0059` | `0060` uniquement | Validation finale malgré les changements de parent des anciennes révisions |
| Révision ou schéma divergents | Arrêt et diagnostic ; aucune correction automatique | Refus explicite et absence d'altération des données |

Une base déjà marquée `20260908_0051` ne rejoue pas la migration de
compatibilité du même identifiant. Une base déjà à `0059` ne repasse pas
non plus par cette ancienne étape. C'est la raison de la validation commune
`0060` ; une simple modification du graphe ne constituerait pas une preuve
de compatibilité de ces bases.

La validation doit refuser une colonne manquante ou ajoutée, un type, une
longueur, une nullabilité ou un défaut divergent, une PK/FK/UNIQUE/CHECK
absente ou différente, ou un index incorrect. La table doit être
`public.field_intake` : un homonyme résolu par un autre `search_path`
ne suffit pas.

Le helper examiné vérifie aussi la nature persistante de la table et refuse
partitionnement, héritage, RLS, politiques, règles et déclencheurs utilisateur
inconnus. Il contrôle les index de support PK/UNIQUE, les index supplémentaires,
la disponibilité des index, leurs expressions, prédicats et options. Une
modification locale de ces objets exige un diagnostic ; elle n'est pas ignorée
au seul motif que les 17 noms de colonnes sont présents.

Les upgrades de `20260908_0051` et `20261116_0060` refusent explicitement
`--sql` : leur validation exige une connexion PostgreSQL au catalogue réel.
La compilation SQL des deux anciennes créations peut démontrer leur
équivalence ; elle ne remplace pas ces migrations en ligne.

Les passages de compatibilité sont sans DDL et sans conversion de données.
Les downgrades de ces seules étapes ne retirent aucun objet. Le downgrade
historique `20260823_0051 → 20260815_0050` supprime la table ; son essai
est limité aux bases jetables. Aucune suppression, aucun `stamp` et aucun
downgrade préalable n'est prévu pour une base à conserver.

## 6. Preuves, commandes et résultats

### 6.1 Environnement et portée des preuves

Les commandes API sont exécutées depuis `GSIE/API` avec Python 3.12 dans
`.venv`. L'orchestrateur a préparé l'environnement avec uv et le verrou
`--frozen --extra dev` de la branche de départ ; une synchronisation après
la fusion sécurité reste à consigner.

L'image préexistante retenue pour les essais isolés est
`gsie-onboarding-db:local`, identifiant
`sha256:4d9ad9081190c5b4db8ccfd0a951df3d4a1243db832883b31a09ce6fa2f5de4d`.
L'orchestrateur y a vérifié PostgreSQL 16.15 et la présence de PostGIS,
Apache AGE et vector. Cette constatation n'atteste pas la construction du
`Dockerfile.db` courant. Les tests doivent identifier leurs conteneurs et
bases jetables et empêcher un succès dû au seul abandon des scénarios Docker.

### 6.2 Preuves déjà disponibles

~~~bash
# Depuis GSIE/API ; commande exécutée par l'orchestrateur.
GSIE_ENVIRONMENT=development \
PYTHONPATH=/workspace/quintessences-integration-2026-11/GSIE/API/src \
.venv/bin/python scripts/extract_openapi.py

GSIE_ENVIRONMENT=development \
PYTHONPATH=/workspace/quintessences-integration-2026-11/GSIE/API/src \
.venv/bin/python -m pytest tests/unit/test_routers_coverage_ext.py \
  -q -n 0 --no-cov \
  --junitxml=/workspace/outputs/2026-11-16/reconciliation-serveur/routers-union.xml \
  > /workspace/outputs/2026-11-16/reconciliation-serveur/routers-union.log 2>&1
~~~

| Preuve | Résultat | Code de sortie et limite |
|---|---|---|
| Génération OpenAPI après fusion de `main` | 151 chemins, 299 schémas, version 0.1.0 | 0 rapporté par l'orchestrateur ; stabilité sur tête finale EN ATTENTE |
| Union des tests routeurs | 49 réussis, 0 échec, 0 erreur, 0 ignoré ; 3,574 s dans JUnit | 0 rapporté par l'orchestrateur ; micro-suite `--no-cov`, aucune mesure de couverture opposable |
| Lecture du JUnit et du log | Racine `testsuites` ; suite `pytest` avec `tests="49"`, `failures="0"`, `errors="0"`, `skipped="0"` ; log `49 passed in 3.57s` | Artefacts relus par l'agent documentation |
| Comparaison des créations | 17 colonnes, mêmes quatre contraintes et quatre index explicites | Lecture des deux snapshots ; compilation SQL hors connexion et enregistreur d'opérations par l'architecte, code 0 rapporté ; aucun essai PostgreSQL dans cette analyse |

Artefacts locaux : `/workspace/outputs/2026-11-16/reconciliation-serveur/routers-union.xml`
et `routers-union.log`. Ces sorties sont conservées hors du dépôt source.
Le résumé d'un agent ne remplace pas leur relecture ni celle du diff final.

L'analyse indépendante a utilisé SQLAlchemy 2.0.36 et Alembic 1.14.0 pour
compiler les deux anciennes créations et comparer leurs signatures. Elle a
aussi vérifié un graphe hypothétique en mémoire, code 0 ; les tests sur le
graphe réellement implémenté et PostgreSQL restent à consigner. Le modèle
`field_intake.py` est identique dans les trois snapshots, blob
`b481a1f4f8b735d3f96171bf42c28b67df8d7886` ; le fichier B est identique dans
`main` et sécurité, blob `1cadf819c2d297df6872100872b422a7df5263f6`.

### 6.3 Campagnes obligatoires à compléter

« EN ATTENTE » signifie qu'aucun succès n'est attesté par ce bilan à ce stade.
Toute variante réelle de commande, code de sortie non nul, test ignoré et motif
de non-exécution doit être conservé lors de la mise à jour.

| Commande / campagne | Résultat | Code | Artefact |
|---|---|---|---|
| `python3 tools/check_governance_consistency.py`, racine | Aucune incohérence détectée | 0 | Nouvelle exécution finale à consigner |
| `python3 tools/check_source_of_truth.py`, racine | 10 sources conformes au 16 novembre | 0 | Nouvelle exécution finale à consigner |
| `python3 tools/check_ai_prompts.py`, racine | 23 missions conformes | 0 | Nouvelle exécution finale à consigner |
| `python3 tools/check_build_consistency.py`, racine | Construction conforme | 0 | Nouvelle exécution finale à consigner |
| `.venv/bin/python -m alembic heads`, API | `20261116_0060 (head)` ; une tête | 0 | `migration-contract-final.log` |
| Lignée Alembic et contrat unitaire | 11 réussis | 0 | `migration-contract-final.xml` |
| Créations historiques reproduites sur PostgreSQL réel, sans `stamp` ni `create_all` | 50 migrations authentiques de `main` et 58 de `feat` ; blobs contrôlés | 0 | `qa-reconciliation-final-v2.xml` |
| Base neuve et départ `0050` vers la tête | Réussis, compris dans les 155 scénarios ciblés | 0 | Même JUnit |
| Ancienne base `main` et ancienne base `feat` vers la tête | Réussis avec leurs créations réelles | 0 | Même JUnit |
| Conservation complète des lignes, UUID et identité de table pendant les validations | Comparaison des 17 colonnes et OID ; réussie | 0 | Même JUnit |
| Schémas divergents refusés sans altération des lignes | 87 dérives et trois attaques de catalogue refusées ; 155 scénarios ciblés réussis au total, aucun ignoré | 0 | Même JUnit, 280,132 s |
| Sauvegarde et restauration d'une base de test jetable | EN ATTENTE | EN ATTENTE | À joindre |
| Python final, `pytest tests/ -q -n 2`, API, première exécution | 3 562 réussis, 11 échoués, 64 ignorés ; couverture 95,8107 %, seuil non atteint | 1 | `full-suite.xml`, `coverage-full.json` ; reprise après corrections EN ATTENTE |
| Reproduction ciblée bundle/contact après correction | 16 réussis ; deux routeurs à 100 % | 0 | `qa-bundle-contact.xml`, `coverage-qa-bundle-contact.json` |
| Lint, typage, couverture combinée et mutation prévus par la CI | EN ATTENTE | EN ATTENTE | À joindre |
| Revue indépendante migration et union des tests | Aucun blocage signalé dans ce périmètre ; helper final vérifié par empreinte | Sans objet | Revue des correctifs de CI en cours ; aucune homologation globale du serveur |

Le helper testé porte le SHA-256
`887a4b49afbe10b645ba1f14bbd6d38ad26b0903b5a1a7de687cff3e32e543e4`.
Les premières tentatives rouges restent conservées : drapeau PostgreSQL
`connoinherit`, opérateur texte homonyme, puis masquage de `unnest` et d'une
comparaison OID. La version finale qualifie les accès par `pg_catalog` et les
155 tests ciblés passent. Ces rouges ne sont pas présentés comme des régressions
encore ouvertes sur ce helper.

Les 11 échecs de la première suite complète ont deux causes : sept tests
cherchent un exemple dans le dépôt externe Forge absent du clone CI ; quatre
appellent la route contact avec une ancienne signature sans `Response`.
La fixture est désormais une copie locale exacte du blob Forge
`a8ee220d725936a72b7b4d825fe9257ba8bbe962`, sans donnée scientifique inventée.
L'appel contact est réaligné sans retirer d'assertion et quatre cas de refus
sont ajoutés. La reproduction ciblée passe, mais ne remplace pas la nouvelle
suite complète. Les 64 ignorés existaient : 46 seeds v6.1 retirés, 14 API
KnowledgeObject retirées, trois cas Rust natif indisponible et un CSV réel
Treekipedia absent. Aucun nouveau marqueur d'ignorance n'est ajouté.

### 6.3.1 Ajustements nécessaires aux contrôles hérités

- Python 3.12 est explicitement choisi pour PyO3 0.24.2 dans le job Rust ;
  le Python 3.14 du runner dépasse sa version prise en charge. Aucun contrôle
  ABI n'est contourné.
- La campagne ciblée de gouvernance des sources utilise `--no-cov` : elle
  exécutait seule le seuil global et échouait avec 19,1 % malgré ses tests
  réussis. La campagne complète et la porte combinée gardent tous leurs seuils,
  dont 97,10 % global et 100 % pour les contrats publics.
- Ruff reformate les fichiers hérités sans changement d'arbre syntaxique.
- Les en-têtes de DEC-000082 et DEC-000084 à DEC-000091 sont normalisés aux
  champs déjà exigés par Governance Guard. Le statut et le corps sont conservés ;
  les propositions 88 à 91 restent explicitement en attente de validation.
  Le garde existant n'est pas affaibli.

### 6.4 CI distante et sauvegarde

| Élément attendu | État |
|---|---|
| Run(s), URL, événement et SHA réellement testés | EN ATTENTE |
| Résultat de chaque job, dont jobs ignorés ou annulés et cause | EN ATTENTE |
| `ci-gate` et politique de couverture combinée DEC-000066 | EN ATTENTE |
| Sécurité, dépendances et secrets sur la tête finale | EN ATTENTE |
| HA et dépendances d'infrastructure | EN ATTENTE ; le blocage historique `minio/mc` doit être requalifié |
| Référence distante de sauvegarde datée | EN ATTENTE |
| SHA relu sur GitHub et correspondance avec le commit remis | EN ATTENTE |

Un contrôle local réussi ou un ancien run vert ne remplace pas les résultats
de la tête soumise à la PR. Le bilan doit conserver les jobs rouges, ignorés,
annulés ou non déclenchés et leur impact réel sur l'acceptation.

## 7. Revue du registre des sources de vérité

### 7.1 État initial et méthode

Le registre initial de `feat` indiquait `last_reviewed=2026-09-29` pour les deux
corpus, avec `next_review=2026-10-29` pour `etat_projet` et
`2026-11-14` pour `directives_actives`. Ces deux revues étaient donc
échues au 16 novembre dans ce snapshot. Le snapshot sécurité porte une revue
`etat_projet` du 18 octobre avec échéance au 18 novembre ; cette différence
héritée ne constitue pas la nouvelle revue du 16 novembre. Une date neuve
seule ne corrige pas une non-conformité :
le contenu, les propriétaires, les statuts, les liens et les contradictions
doivent être examinés conformément à DOCUMENT_CONTROL, section 7.

| Corpus | Preuve de revue à consigner | Conclusion et limites |
|---|---|---|
| `etat_projet` | Lecture des en-têtes et sections récentes de `PROJECT_MEMORY.md`, `ROADMAP.md` et `CHANGELOG.md` ; confrontation au contrat d'intake et aux preuves disponibles ; inspection structurelle des liens par le relecteur | État RLS/migration `0059` du 1er octobre, pilotage GeoSylva/G1–G5 et chantiers ouverts relus. Les ajouts de sécurité datent du 18 octobre ; une nouvelle proposition figure en section 8. La lecture n'autorise pas une réécriture et la tête finale reste à vérifier |
| `directives_actives` | Lecture intégrale indépendante des sept directives actives et des décisions levant les anciennes restrictions ; comparaison des blobs entre les trois sources | Sept blobs identiques, relus par l'agent documentation avec `git rev-parse SHA:chemin` ; inventaire ci-dessous |
| Propriétaire et statut | Lecture des champs `owner` / `status` et confrontation aux auteurs et arbitrages pertinents | Initialement Direction technique / canonique pour `etat_projet` ; Fondateur / canonique pour `directives_actives`, cohérent avec les auteurs. Maintien des propriétaires proposé ; mandats non confirmés par une source externe |
| Liens et doublons | Inspection structurelle des liens Markdown relatifs des trois vues par le relecteur ; comptage indépendant des titres `##` suivi d’un espace dans chaque snapshot | Aucune cible locale absente détectée par cette inspection ; ancres non contrôlées, aucun appel réseau. Le même titre d'assainissement apparaît 69 fois dans chacun des trois CHANGELOG ; défaut préexistant, conservé |
| Hypothèses externes | Séparer l'état du dépôt, les preuves locales, les preuves historiques et les services réellement vérifiés | Pas de qualification scientifique, réglementaire, fournisseur, production ou visibilité GitHub déduite de cette revue |

Les directives lues par le relecteur indépendant sont :

| Directive | Statut en tête | Blob identique dans les trois sources |
|---|---|---|
| GSIE-DIR-0001 — Foundation | ACTIVE | `e42464902d07687477617a42656c48e83808a0e7` |
| GSIE-DIR-0004 — Genesis | ACTIVE | `cf7e9e0db149f4d90c260c1a8cbeac89fcdd8b9d` |
| GSIE-DIR-0008 — Encyclopédie | ACTIVE, amendée par DEC-000022 / RFC-0011 | `de81dec882f06266453593279f6515b67e4a0a33` |
| GSIE-DIR-0009 — Restructuration de l'écosystème | ACTIVE | `a38461b125e308127034059c1b94354d43464f60` |
| GSIE-DIR-0010 — Réorganisation du dépôt | ACTIVE | `c45c5b59b96a4bc52cf625fe2866f00ae7f7ddee` |
| GSIE-DIR-0011 — Lancement Phase 4 | ACTIVE | `19bdebd2dfe18bff3cbd514e47ac7d1a16ce6b05` |
| GSIE-DIR-0013 — Territorial Mesh | Active | `aa51a5680a6663fe086b8d1150387a7d333a7f24` |

Le comptage a lu `CHANGELOG.md` dans les trois SHA via `git show`, puis
compté les lignes commençant par `##` suivi d’un espace : le titre exact
`## [ASSAINISSEMENT TRANSVERSAL PHASES 1-4] - 2026-08-13` compte
69 occurrences dans chaque snapshot. Aucun titre n'a été supprimé.

Les arbitrages déjà signalés par le relecteur sont les suivants :

- l'ancienne restriction de Phase 1 est levée pour l'implémentation par
  GSIE-DIR-0011 et DEC-000017 ;
- GSIE-DIR-0008 doit être lue avec son annexe, RFC-0011 et DEC-000022 ;
- GSIE-DIR-0013 active n'est pas assimilée à GSIE-DIR-0012 restée `Draft`.

Le relecteur a lu intégralement DEC-000017, DEC-000022 et
`02_RFC/annexes/annexe-dir0008.md` ; il a contrôlé de façon ciblée
DEC-000054 (Validé), DEC-000053 (Draft), la directive 0012 proposée,
RFC-0036 (Draft) et DEC-000083 (Proposé). La revue des trois vues de pilotage
combine leur structure complète (titres/liens) et une lecture ciblée :
`PROJECT_MEMORY.md` lignes 1 à 160, `ROADMAP.md` lignes 1 à 180,
`CHANGELOG.md` lignes 1 à 130, plus l'apport propre sécurité complet.
Elle ne prétend pas relire intégralement les 11 160 lignes de ces trois vues,
ni requalifier chacune de leurs preuves historiques.

La revue préalable indépendante n'a exécuté aucun test ni contacté de base.
L'examen adversarial du diff final reste à joindre. Ces constats ne valident
pas de nouveaux contenus, et le statut global
`canonique` d'un corpus ne transforme pas un DEC ou une directive `Draft`
en décision applicable.

### 7.2 Métadonnées proposées après revue effective

| Corpus | Statut proposé | Dernière revue proposée | Prochaine revue maximale proposée | Justification |
|---|---|---|---|---|
| `etat_projet` | `reference` provisoire | `2026-11-16`, avec portée et réserves explicites | `2026-11-23` (sept jours), et immédiatement après changement d'état | Le champ courant de PROJECT_MEMORY indique encore `0059`, alors que l'intégration vise `0060` ; la synchronisation reste une proposition. Un renouvellement canonique mensuel ferait croire à un état consolidé démontré. Le délai de sept jours reste inférieur au maximum mensuel |
| `directives_actives` | `canonique` | `2026-11-16`, après conclusion de la revue des sept directives | `2027-02-16` au plus tard ; revue anticipée dès nouvelle directive, décision de remplacement ou contradiction | Textes intégralement relus, stabilité des sept blobs dans les trois snapshots et propriété cohérente localement ; limite trimestrielle DOCUMENT_CONTROL |

Le statut provisoire `reference` d'`etat_projet` est la recommandation du
relecteur indépendant au titre de DOCUMENT_CONTROL, section 7. La portée
proposée pour le registre est : « Revue documentaire ciblée ; écarts
historiques et synchronisation seulement proposée ; aucune qualification
serveur ou applicative. » Le retour à `canonique` nécessite une mise en
cohérence autorisée des vues et une revue des preuves de l'état qu'elles
déclarent ; il ne découle pas d'une simple nouvelle date.

L'orchestrateur met à jour le registre à partir des preuves effectives. La
date proposée ne constitue ni une revue exécutée par anticipation, ni une
autorisation d'appliquer les propositions de synchronisation.

## 8. Textes proposés pour les vues de pilotage

Les blocs suivants sont des propositions à relire. Ils ne sont pas appliqués
par ce lot documentaire ; les résultats entre crochets ne doivent être
remplacés que par des preuves effectivement acquises.

### 8.1 PROJECT_MEMORY.md

Proposition de nouvelle entrée, sans effacer le contexte historique :

~~~markdown
### Réconciliation serveur — 2026-11-16 — EN_REVUE

La branche integration/reconciliation-serveur-2026-11 réunit les snapshots
feat/schemas-de-domaine (9e6864b), main (d7b400c) et sécurité (e3e18d4).
Les quatre conflits de la première fusion sont résolus en conservant les tests
et assertions ; OpenAPI est régénéré depuis l'application.

DEC-000094 (Draft) propose de conserver les deux révisions FieldIntake :
20260823_0051 garde la création ; 20260908_0051 valide le schéma ; 0052
change de parent ; 20261116_0060 valide aussi les bases déjà migrées.
Le contrat reste de 17 colonnes, quatre contraintes et quatre index explicites,
sans stamp, downgrade préalable ni conversion de données.

Preuves sur le commit [SHA final] : [tests et contrôles réellement exécutés,
résultats, ignorés, limites et CI par job]. Rapport :
23_QUALITY_MANAGEMENT/AUDITS/RECONCILIATION_SERVEUR_2026-11-16.md.
PR [numéro/URL] et sauvegarde [référence/SHA relu]. Le lot reste en revue ;
aucune fusion, migration de base utilisateur ou qualification de production.
La PR nº 73 et les écarts métier E01 à E06 restent hors périmètre.
~~~

Le champ « Dernière mise à jour » et la référence de tête Alembic ne seraient
modifiés qu'après confirmation du SHA final, des preuves et de l'état retenu.
DEC-000094 ne serait pas ajoutée aux décisions actives comme une décision
validée.

### 8.2 ROADMAP.md

Proposition de tranche dédiée, avec cases cochées seulement sur preuve :

~~~markdown
## Réconciliation serveur — 2026-11-16 — EN_REVUE

- [ ] Réunir main et le snapshot sécurité sur la branche d'intégration et
  publier le SHA final sans fusionner la PR.
- [ ] Conserver l'union des tests et régénérer OpenAPI.
- [ ] Prouver une seule tête 20261116_0060 et les chemins neuf, 0050,
  ancien main et ancien feat sur PostgreSQL isolé.
- [ ] Prouver la conservation des lignes et le refus des schémas divergents.
- [ ] Reproduire les quatre contrôles, la suite API et la CI par job ;
  documenter les tests ignorés et les limites.
- [ ] Joindre la revue indépendante, la procédure locale avec restauration
  testée et la sauvegarde distante datée.
- [ ] Soumettre DEC-000094 Draft et la PR à l'autorité compétente.

Cette tranche ne clôture aucun gate produit GeoSylva, ne corrige pas E01 à E06
et n'atteste aucun déploiement ou essai en production.
~~~

La tâche historique « renommer ou fermer feat/schemas-de-domaine » ne doit pas
être cochée au seul motif que cette PR d'intégration existe.

### 8.3 CHANGELOG.md

Proposition d'entrée :

~~~markdown
## [RÉCONCILIATION SERVEUR EN REVUE] - 2026-11-16

- Réconciliation des snapshots feat/schemas-de-domaine, main et sécurité sur
  une branche isolée ; quatre conflits résolus, union des assertions de tests
  et OpenAPI régénéré.
- Comparaison des deux créations FieldIntake : 17 colonnes, mêmes contraintes
  et index ; identifiants historiques conservés et validation commune 0060.
- DEC-000094 rédigée en Draft ; bilan, risques, preuves et procédure de reprise
  dans RECONCILIATION_SERVEUR_2026-11-16.md.
- Vérifications sur [SHA final] : [résultats effectivement acquis, ignorés et
  limites]. PR [URL], sauvegarde [référence et SHA relu].
- Remise EN_REVUE ; aucune fusion de PR, migration de base utilisateur ou
  qualification de production.
~~~

Les anciens titres dupliqués ne sont pas nettoyés implicitement par cette
entrée ; une correction séparée doit conserver l'historique et ses renvois.

## 9. Procédure locale proposée et reprise

### 9.1 Préconditions

Cette procédure est une proposition opérationnelle à exécuter ultérieurement
sur la base locale choisie par son responsable. La mission ne s'est connectée
à aucune base utilisateur. Les noms de services libpq ci-dessous sont des
exemples à configurer explicitement, avec authentification hors de l'historique
shell ; aucune URL ou sortie contenant un secret ne doit être ajoutée au dépôt.

Avant toute opération, identifier le commit candidat et les services source,
copie et restauration, distincts les uns des autres. Vérifier PostgreSQL 16,
PostGIS, Apache AGE, vector, les propriétaires et les rôles nécessaires à la
restauration. Maintenir l'ancienne version du code disponible. Arrêter les
écrivains : API, workers, ordonnanceurs et imports ; vérifier qu'aucun autre
client ne continue d'écrire et conserver cette preuve.

### 9.2 Sauvegarde et restauration d'essai avant upgrade

1. Avec le service source choisi, relever `alembic_version`, le nom de la
   base, le schéma, le nombre de lignes d'intake et une empreinte par ligne
   portant sur toutes les colonnes. Conserver les preuves hors du dépôt,
   avec accès limité ; une date ou un simple compte de lignes ne suffit pas.
2. Faire une sauvegarde PostgreSQL au format custom et en calculer le SHA-256.
   Restaurer cette sauvegarde dans une base jetable distincte et vérifier
   révision, contraintes, index et empreintes. Une sauvegarde dont la
   restauration n'a pas réussi ne permet pas de poursuivre.
3. N'exécuter les migrations candidates que sur cette copie. Capturer les
   commandes, versions et codes de sortie ; comparer les empreintes, les UUID,
   la provenance, les horodatages, les JSONB et les cibles avant/après.

Exemples de commandes à adapter ; elles ne sont pas exécutées sur une base
utilisateur dans le cadre de cette mission :

~~~bash
set -euo pipefail
psql 'service=gsie_reconciliation_source' -X -v ON_ERROR_STOP=1 \
  -c 'SELECT current_database(), version_num FROM public.alembic_version;'

pg_dump --dbname='service=gsie_reconciliation_source' --format=custom \
  --file=/chemin/local/protege/gsie-avant-reconciliation.dump
sha256sum /chemin/local/protege/gsie-avant-reconciliation.dump

# La cible est une base jetable vide et explicitement distincte de la source.
pg_restore --dbname='service=gsie_reconciliation_copie' --exit-on-error \
  /chemin/local/protege/gsie-avant-reconciliation.dump

psql 'service=gsie_reconciliation_copie' -X -v ON_ERROR_STOP=1 \
  -c 'SELECT current_database(), version_num FROM public.alembic_version;'
~~~

### 9.3 Cible explicite de migration et vérifications

Depuis le checkout candidat et `GSIE/API`, définir explicitement
`GSIE_MIGRATION_DATABASE_URL` pour la copie. `alembic/env.py` utilise cette
valeur, puis retombe sur `GSIE_DATABASE_URL` si elle est absente : cette
absence est interdite dans la procédure. Le compte de migration doit avoir
les droits de DDL nécessaires ; le compte applicatif restreint ne le remplace pas.
Ne pas se fier à la seule valeur de `sqlalchemy.url` dans `alembic.ini`.

~~~bash
# Exécuter ce bloc dans un script Bash qui s'arrête à la première erreur.
set -euo pipefail
# Définir GSIE_MIGRATION_DATABASE_URL de manière protégée pour la COPIE.
# Aucun secret n'est affiché ni inscrit dans le bilan.
: "${GSIE_MIGRATION_DATABASE_URL:?Une URL explicite de la copie est obligatoire}"
.venv/bin/python -m alembic current --verbose
.venv/bin/python -m alembic heads
.venv/bin/python -m alembic upgrade 20261116_0060
.venv/bin/python -m alembic current --verbose
~~~

Avant l'upgrade, exiger une révision connue et la comparaison du contrat.
Après l'upgrade, exiger la révision unique `20261116_0060` et les invariants
de conservation. Ne pas utiliser `stamp`, `downgrade`, `create_all` ou une
recréation de table pour contourner un échec. Exécuter les tests fonctionnels
de la copie, y compris idempotence/quarantaine et lectures stationnelles, et
conserver leurs résultats.

Une exécution ultérieure sur la source exige que la restauration d'essai et
l'upgrade de la copie aient réussi et que les écrivains soient toujours
arrêtés. Refaire une sauvegarde finale si la source a changé depuis la copie,
relever à nouveau sa révision, définir explicitement son URL de migration et
appliquer le même upgrade ciblé. Redémarrer les écrivains seulement après les
vérifications de schéma, de données et de santé.

### 9.4 Échec et reprise

En cas de schéma divergent, révision inconnue ou erreur de migration, arrêter
l'opération et conserver logs et sauvegarde ; aucune donnée manquante ne doit
être déduite ou synthétisée. Vérifier l'état transactionnel réellement obtenu.
Restaurer la sauvegarde validée dans une nouvelle base distincte, contrôler
révision et empreintes, puis reconnecter l'ancienne version applicative à cette
base restaurée. Une éventuelle suppression de l'ancienne base défaillante est
une action séparée, jamais une étape automatique de cette procédure.

Le retour arrière de la mission Git ne remplace pas un retour de données.
Le downgrade qui traverse la création d'intake est destructif : il est réservé
aux essais sur des bases jetables et ne constitue pas une procédure de reprise
pour une base à conserver.

## 10. Risques résiduels et conditions d'acceptation

| Risque ou limite | Traitement / preuve requise |
|---|---|
| Bases historiques déjà migrées sautant la validation de l'alias | Validation finale `0060` et tests réels des deux historiques |
| Schéma local différent des migrations publiées | Validation complète avec refus ; diagnostic et arbitrage séparés, aucune conversion automatique |
| Données conservées en apparence mais contenu modifié | Comparaison de toutes les colonnes des lignes synthétiques et preuve de conservation physique pendant les validations |
| Permissions, `search_path` ou homonyme de table | Validation explicite de `public` et essais avec compte de migration identifié |
| Tests ignorés ou dépendances Docker indisponibles | Garde d'exécution et inventaire des ignorés ; ne pas les compter comme réussis |
| Image de base préexistante | Prouve les essais dans cet environnement seulement ; construction du Dockerfile courant et CI à attester séparément |
| Sécurité documentaire datée d'octobre | Rejouer les contrôles utiles sur le verrou et le SHA final ; conserver l'ancien blocage HA tant qu'il n'est pas requalifié |
| Écarts de fraîcheur des vues de pilotage | Revue documentée, propositions distinctes, réserves conservées et dates liées au risque |
| 69 occurrences d'un même titre CHANGELOG préexistantes | Constat mesuré dans les trois snapshots ; correction non incluse implicitement dans la réconciliation |
| Marqueur Windows modifié dans `eccodeslib → eckitlib` | Qualification Windows séparée si cette plateforme entre dans l'acceptation ; les essais Linux ne suffisent pas |
| Défaut `received_at` écrit différemment dans l'ORM existant | L'architecte relève que `server_default="now()"` compile en `DEFAULT 'now()'`, tandis que les migrations figées produisent `DEFAULT now()` ; point préexistant dans les trois snapshots, non corrigé ici. Le helper se fonde sur les migrations |
| Revue et CI finales incomplètes | Remise EN_REVUE ; aucune conclusion d'acceptation avant les preuves manquantes |
| Floorplan indisponible | Aucune carte créée ou actualisée ; analyse des sources utilisée, aucune installation tentée |

La remise doit encore rassembler le diff final relu, toutes les preuves de la
section 6, la conclusion des deux revues de corpus, les résultats CI par job
et le SHA de sauvegarde relu à distance. DEC-000094 reste `Draft` jusqu'à
décision explicite du Fondateur. Le présent rapport ne prononce aucune
validation produit, autorisation de fusion ni autorisation de migration d'une
base utilisateur.

## 11. Sources et historique

- [Règles racine](../../AGENTS.md), [règles API](../../GSIE/API/AGENTS.md)
  et [README API](../../GSIE/API/README.md).
- [Pacte IA](../../00_CONSTITUTION/PACT_FOR_AI_AGENTS.md),
  [CON-001](../../00_CONSTITUTION/GSIE-CON-001.md),
  [CON-005](../../00_CONSTITUTION/GSIE-CON-005.md),
  [CON-010](../../00_CONSTITUTION/GSIE-CON-010.md) et
  [ADR-009](../../GSIE/ARCHITECTURE/ADR-009-garde-fou-anti-invention.md).
- [README QMS](../README.md),
  [DOCUMENT_CONTROL](../PROCESSES/DOCUMENT_CONTROL.md),
  [AI_AGENT_ORCHESTRATION](../PROCESSES/AI_AGENT_ORCHESTRATION.md) et
  [registre des sources](../SOURCE_OF_TRUTH_REGISTRY.json).
- [DEC-000066](../../03_DECISIONS/DEC-000066.md) : politique de couverture
  combinée ; une micro-suite `--no-cov` ne la remplace pas.
- Les trois SHA figés et les chemins sources indiqués dans les sections
  techniques ; seules les sources effectivement consultées fondent les constats.

| Date | Événement |
|---|---|
| 2026-11-16 | Création du bilan de travail : comparaison complète du schéma, propositions de synchronisation et procédure locale ; preuves finales en attente |
