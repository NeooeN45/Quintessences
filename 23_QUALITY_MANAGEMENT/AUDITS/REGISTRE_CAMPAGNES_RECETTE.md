# Registre opérationnel des campagnes de recette

| Champ | Valeur |
|---|---|
| **Statut** | Draft opérationnel |
| **Date de création** | 2026-08-29 |
| **Périmètre** | Quintessences, GSIE API, GeoSylva, Forge et preuves de recette associées |
| **Autorité de classement** | GEO-005, DEC-000074, processus qualité GSIE |

## 1. Règles du registre

Ce registre est la liste de référence des campagnes de recette exécutées ou
préparées pour la V1 GeoSylva → GSIE. Une campagne ne devient pas une preuve de
production par sa seule présence dans le registre.

Chaque entrée doit conserver :

- un identifiant stable de campagne ;
- la date et le gate concerné ;
- le dépôt, le commit ou l’empreinte de l’artefact testé ;
- l’environnement et les versions utiles ;
- les identités de test synthétiques, sans secret ni adresse personnelle réelle ;
- les cas exécutés et le résultat ;
- le rapport ou les logs de preuve ;
- les limites et actions restantes ;
- la politique de conservation applicable.

Les campagnes destructives doivent cibler une identité synthétique créée pour la
campagne et préciser la clause de ciblage. Aucun refresh token, mot de passe,
code, nonce, secret, adresse personnelle réelle ou contenu de donnée sensible ne
doit être copié dans ce registre.

## 2. Statuts

| Statut | Signification |
|---|---|
| `PLANIFIÉE` | Périmètre défini, aucune preuve exécutée |
| `EN COURS` | Exécution commencée, résultat non final |
| `PASS` | Tous les critères de la campagne sont prouvés |
| `PASS PARTIEL` | Le sous-périmètre annoncé est prouvé, des portes restent ouvertes |
| `ÉCHEC` | Au moins un critère bloquant est démontré comme non satisfait |
| `NON CONCLUANTE` | L’environnement ou la preuve ne permet pas de conclure |
| `ANNULÉE` | Campagne arrêtée avant exécution ou remplacée |

## 3. Campagnes enregistrées

| Identifiant | Date | Gate | Périmètre | Environnement | Identité | Résultat | Preuve | Limites restantes |
|---|---|---|---|---|---|---|---|---|
| `REC-20260907-L0-CI-01` | 2026-09-07 | L0 / préparation G2 | Contrats GeoSylva, dendrométrie, garde du lanceur Docker et JUnit | Windows, environnement `.venv-gsie-api-validation` ; base HEAD `e55c369` avec modifications locales, pas une release immuable | Configuration contact synthétique ; aucun compte créé | `PASS PARTIEL` | 25 tests, 0 erreur, 0 échec, 0 skip, 4,636 s ; `GSIE/API/tests/perf/results/junit-launch-baseline.xml` local ; YAML parsé et garde Docker vérifié ; diff ciblé sans erreur d'espacement | Aucun test Docker réel, E2E appareil ou GitHub exécuté ; le test géométrique ne clôt pas l'ambiguïté diamètre moyen/quadratique ; rapport local à archiver avec le snapshot avant preuve de release |
| `REC-20260829-G0-API-TEST-01` | 2026-08-29 | G0 | API, PostgreSQL/PostGIS, Redis, MinIO, Mailpit, workers | Docker Compose isolé `gsie-test` ; ports hôte temporaires `15432`, `16379`, `18000`, `19000`, `19001`, `18025`, `11025` | Aucune identité métier | `PASS` | `/health` = 200 ; `/ready` = 200 ; DB `gsie_test` ; PostGIS/AGE/pgvector présents ; revision Alembic `20260826_0055` ; `gsie_api` non-superuser ; API et workers sains ; correctif RLS/export tracé par DEC-000077 | Ce résultat est local et ne constitue pas une preuve staging/production. L’override de ports est temporaire. |
| `REC-20260829-G0-MATRIX-01` | 2026-08-29 | G0 | Matrice écrans, calculs, Room, endpoints, fichiers et données personnelles | Poste de travail + dépôt parent et repo GeoSylva indépendant | Aucune identité métier | `PASS` | `23_QUALITY_MANAGEMENT/AUDITS/2026-08-29_G0_RECONCILIATION_GEOSYLVA.md` | La matrice est approuvée comme baseline G0 ; cette approbation ne valide ni G1, ni G2, ni la production. |
| `REC-20260829-G1-NATIVE-REGISTER-01` | 2026-08-29 | G1/G2 | Page native d’inscription GeoSylva, navigation et validation locale | APK debug installé par ADB sur S25 Ultra | Aucune création réelle | `PASS PARTIEL` | DEC-000076 et preuve UI ADB reportée dans `GEO-005` | Création réelle avec adresse de test, vérification e-mail et rattachement des consentements restent à recetter. |
| `REC-20260826-G2-CPT16-01` | 2026-08-26 | G2 | Fonction SQL de finalisation RGPD d’un compte synthétique | Docker local, migration `0055` | Compte synthétique dédié, identifiant non recopié | `PASS PARTIEL` | `23_QUALITY_MANAGEMENT/AUDITS/2026-08-26_G2_CPT16_FINALISATION_COMPTE_SYNTHETIQUE.md` | Smoke test du worker, restauration, purge locale complète, isolation de deux comptes et Google restent ouverts. |
| `REC-20260825-REGISTRY-SOILGRIDS-01` | 2026-08-25 | Data Registry | Replay RAW SoilGrids, qualité append-only et garde de promotion | PostgreSQL/PostGIS via Docker | Aucune donnée personnelle | `PASS PARTIEL` | `GSIE/API/tests/integration/test_soilgrids_registry_vertical.py` | Unités à qualifier ; aucune ouverture FETCH ni promotion effective ; preuve limitée à l’actif autorisé. |
| `REC-20260829-FORGE-IFN-HANDOFF-01` | 2026-08-29 | Préparation G3 | Handoff IFN Forge → Data Registry | Repo Forge, worktree local | Aucune identité métier | `EN COURS` | `Forge/src/dataset_forge/gsie_acquisition.py`, `Forge/tests/test_gsie_acquisition.py` | Tests et revue du diff à exécuter ; `scratch_ifn/` doit rester hors commit ; aucune acquisition ou promotion production. |

## 4. WIP concurrents déclarés hors livraison G0

Ces modifications sont enregistrées afin d’éviter qu’un agent ne les écrase ou
ne les mélange avec une preuve G0. Elles ne sont pas considérées comme livrées
par ce registre.

| Dépôt | WIP observé | Livraison autorisée | Propriétaire à confirmer |
|---|---|---|---|
| Quintessences | identité, migrations RGPD, API, public contact, site, recherche, documentation et acquisition | Aucun mélange avec l’audit G0 sans diff séparé | Fondateur / agent de la tranche concernée |
| `apps/GeoSylva` | identité, navigation, création forêt, carte/recherche, haptique et mémoire Obsidian | Repo indépendant ; pas de commit parent | Fondateur / agent Android concerné |
| `Forge` | connecteur IFN, CLI, handoff d’acquisition et tests | Repo indépendant ; `scratch_ifn/` exclu | Fondateur / agent Forge concerné |

## 5. Campagne G0-API-TEST — fiche détaillée

### 5.1 Préparation

- environnement sélectionné : `.env.test.example` ;
- namespace Compose : `gsie-test` ;
- bases et buckets de test distincts ;
- stack de développement `gsie-*` conservé et non arrêté ;
- ports hôte remappés temporairement pour éviter les conflits locaux ;
- aucun secret lu ou ajouté au dépôt.

### 5.2 Exécution

1. validation `docker compose config` avec le profil de test ;
2. création du réseau et des services `gsie-test` ;
3. reconstruction des images API et workers avec le code courant ;
4. application explicite des migrations `20260813_0049` à
   `20260826_0055` ;
5. vérification des services, de l’API, de PostgreSQL/PostGIS et des rôles ;
6. contrôle des workers après migration.

### 5.3 Observations

- API : `healthy` ;
- PostgreSQL : `healthy` ;
- Redis : `healthy` ;
- MinIO : `healthy` ;
- Mailpit : `healthy` ;
- outbox worker : `healthy` ;
- account deletion worker : `healthy` après migration `0055` ;
- `/health` : réponse HTTP 200 ;
- `/ready` : réponse HTTP 200 ;
- rôle `gsie` : administrateur de migration ;
- rôle `gsie_api` : non-superuser pour l’exécution applicative.

### 5.4 Arrêt et conservation

Le stack `gsie-test` reste disponible pour les campagnes suivantes. Son arrêt
normal doit utiliser le projet Compose `gsie-test` et le même profil de test.
Aucune suppression de volume n’est autorisée sans confirmation explicite et sans
vérifier qu’aucune campagne ne l’utilise.

Les preuves sont conservées sous forme de rapports, commandes, versions et
résultats minimisés. La durée juridique définitive des données de recette reste à
confirmer dans la politique de conservation ; les identités utilisées doivent
rester synthétiques et révocables.

## 6. Règle d’acceptation

Une campagne peut être déclarée `PASS` uniquement si :

- son périmètre est borné ;
- l’environnement est identifié ;
- le commit ou l’artefact est traçable ;
- les tests annoncés ont réellement été exécutés ;
- les erreurs et limites sont conservées ;
- aucune preuve locale n’est présentée comme une preuve de production ;
- aucune donnée personnelle ou secret n’est exposé.

## 7. Historique

| Date | Modification |
|---|---|
| 2026-08-29 | Création du registre ; enregistrement des campagnes G0, G2, Data Registry, Forge en cours et inscription native GeoSylva. |
| 2026-08-30 | Recontrôle G0 : API `gsie-test` saine, matrice approuvée et README Room réaligné ; G0 clôturé pour la réconciliation uniquement. |
