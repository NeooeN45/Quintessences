# Levée des blocages PR74 — GSIE-PROMPT-0034

| Champ | Valeur |
|---|---|
| **Identifiant** | AUDIT-LEVEE-BLOCAGES-PR74-2026-11-16 |
| **Statut** | Draft |
| **Version** | 1.2.0 |
| **Date** | 2026-11-16 |
| **Auteur** | Codex, consortium spécialisé et relecteur indépendant |
| **Mission** | [GSIE-PROMPT-0034](../../GSIE/PROMPTS/GSIE-PROMPT-0034-lever-blocages-pr-74.md) |
| **Branche** | `integration/reconciliation-serveur-2026-11` |
| **PR** | [nº 74](https://github.com/NeooeN45/Quintessences/pull/74) |
| **Départ** | `ffdc260c03703b5a196e24cb73f308ebc29b16a0` |
| **Code API testé et scanné** | `fdc1da7906e3fb30b5a9d4b8a3ae6e93d18be16e` ; clôture documentaire distincte |
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
| A — Documents | Fusion de `57121c81729c98ef882157f4b27f0ef660336bfe` ; union des missions 0032, 0033 et 0034 sans renumérotation | FAIT | Fusion `a7d494e7c4353a729f5e7f1c76b7ba0a328ac184` ; quatre contrôles à 0 |
| B — Migrations | Une création `20260823_0051`, parent direct de `0052` ; B/helper/`0060` retirés ; tête `20260929_0059` | FAIT | `5405a74` ; tests ciblés et suite complète réussis, SQL hors ligne exécuté ; originaux conservés |
| C — Cubage | Retrait exact des deux lignes autorisées après B, sans exclusion de couverture | FAIT après accord | `4fddebf` ; huit tests ciblés et suite complète réussis ; module couvert 154/154 lignes |
| D — Sécurité | Versions correctrices des 21 occurrences ; image API réellement reconstruite et scannée | FAIT pour les 21 ; risques résiduels explicités | `fdc1da7` ; 21 couples absents, porte corrigeables à 0 ; 118 résiduelles sans version corrigée indiquée |
| E — MinIO | Refus anonyme reproduit sur Hub et Quay ; sources officielles corrigées épinglées et hachées | FAIT pour diagnostic et proposition ; construction/intégration non réalisées | Sources vérifiées en octets ; ancienne release vulnérable écartée de la proposition durable ; Registry/HA restent rouges |
| F — Concurrence | Course reproduite avec huit sessions indépendantes ; proposition sans cible complétée par des contrôles d'identité à définir | FAIT pour reproduction et proposition ; correctif non appliqué | 94 succès et 2 erreurs natives sur 96 analyses baseline ; 96 succès prototype ; deux limites d'identité reproduites |

## 3. A — Union documentaire et traçabilité

Le commit de fusion observé a pour parents
`ac20c334694e2b07118e6ea046589efc6bdcfe04` et
`57121c81729c98ef882157f4b27f0ef660336bfe`. Il intègre GSIE-PROMPT-0032,
exclu du lot précédent, par l'autorisation propre au point A.
Cela n'atteste aucune fusion des PR nº 73 ou nº 74 dans `main`.

REGISTER conserve GSIE-PROMPT-0032 `EN_REVUE`, GSIE-PROMPT-0033 `EN_REVUE`
et GSIE-PROMPT-0034 `EN_REVUE` à la remise. DEC-000093 enregistre la validation avec
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
et quatre index explicites. Les essais ciblés vérifient le schéma, les lignes
complètes et les données liées ; la suite globale incluant quarantaine,
idempotence, hydratation et préparation est également terminée, voir §8.

| Élément | Traitement attendu |
|---|---|
| `20260823_0051_field_intake.py` | Création conservée, sans réécriture |
| `20260826_0052_billing_schema_usage.py` | Parent direct remis à `20260823_0051` |
| `20260908_0051_field_intake.py` et `20261116_0060_reconciliation_field_intake.py` | Retrait du dossier actif |
| `alembic/compatibility/field_intake_v1.py` | Retrait après vérification de l'absence d'autre usage métier |
| `20260801_0027_indexes_enrichissement.py` | Garde anti-doublons maintenue dans le SQL hors ligne avant l'index unique |
| Tests de lignée et migration | Adapter à une création, une tête, SQL hors ligne et invariants utiles |

La génération `--sql` réussit sans connexion et contient la garde
anti-doublons avant l'index. Les essais exécutent aussi ce SQL sur PostgreSQL :
la preuve dépasse sa seule émission. Le corps de la garde en ligne `0027`
reste identique ; le mode hors ligne émet un bloc `DO` avec le même diagnostic,
sans réparation ni suppression automatique de données.
L'orchestrateur confirme la baseline et A inchangées, et `0052` identique
au fichier `feat`. Le bilan GSIE-PROMPT-0033 reste le relevé historique de
la solution B/`0060`, sans être réécrit par ce rôle.

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

### 4.4 Preuves ciblées et rouges conservés

Les artefacts se trouvent sous
`/workspace/outputs/2026-11-16/pr74-blocages/qa/`.

| Exécution | Résultat et code | Portée |
|---|---|---|
| `qa0034-as-sql-initial.xml` | Rouge transitoire | Retrait B commencé avant réécriture du parent `0052` ; distinct du défaut causal `0027` |
| `qa0034-as-sql-0027-red.xml` | Code 1 ; 2 échecs, 1 réussite, 1,284 s | Upgrade complet et `0026 → 0027` bloqués sur `None.fetchall` ; downgrade complet réussi |
| `qa0034-target-initial.xml` et `.log` | Code 0 ; 21 réussis, 0 échec/erreur/ignoré ; 137,991 s JUnit, 138,08 s journal | 11 unitaires/contrat et 10 PostgreSQL après correction |
| `qa0034-unit-final.xml` | Code 0 ; 11 réussis, 1,289 s | Reprise de la partie unitaire après assertion exacte du CHECK à trois statuts ; aucun ajout au total de 21 cas distincts |

La matrice `qa0034-matrice-invariants.json` relie les anciens tests aux
invariants conservés et aux contrats volontairement retirés avec le validateur.
Elle atteste notamment :

- une base et une tête uniques, absence de branche et de dépendance, et retrait
  de B/`0060` ;
- schéma canonique exact d'intake, PK/FK/UNIQUE/CHECK, quatre index de lecture
  et deux supports, types, nullabilité, défauts et propriétés du catalogue ;
- conservation des lignes entièrement renseignées, UUID, dates, JSONB,
  provenance, empreintes, revues, données liées et OID lors des transitions
  non destructrices ; données BFF à `0059` ;
- cycle neuf en ligne et cycle complet à partir du SQL hors ligne réellement
  exécuté ; extensions conservées après retour à `base` ;
- sauvegarde custom et restauration A/`0059` avec contrôle des 17 champs,
  trois statuts, ordre physique et sources de test inchangées ;
- garde `0027` prouvée en ligne et par SQL hors ligne : sept paires dupliquées,
  35 lignes, total et Top 5 exacts, SQLSTATE `P0001` hors ligne, version `0026`,
  données et tables inchangées après refus, index absent ; reprise après
  réparation explicite des identifiants synthétiques, sans supprimer de ligne ;
- sept fonctions et 21 assertions du contrat de migration inchangées hors
  constante HEAD, tests baseline/RGPD identiques à `ffdc260`, aucun nouveau
  `skip`/`xfail` ni baisse de seuil.

## 5. C — Retrait borné de la garde cubage

Dans `geosylva/cubage_schemas.py`, `visit(value)` ajoute une position valide
ou lève une erreur pour les structures JSON finies acceptées. Le refus
`if not positions` placé juste après n'est donc pas une frontière accessible.
L'accord reçu autorise son seul retrait de deux lignes, après B et les huit
tests requis.

Le commit `4fddebf` retire exactement les deux lignes autorisées.
`cubage-c-apres-retrait.xml` donne 8 réussites, 0 échec/erreur/ignoré,
5,460 s ; code de sortie 0 rapporté par l'orchestrateur. Les huit noms de
cas correspondent à la campagne préalable `review-cubage-geometry-c.xml`
(8 réussis, 4,489 s), avec les refus WGS84, structures invalides, empreintes
et acceptation de géométrie imbriquée conservés.

La première invocation sur un chemin invalide n'a collecté aucun test :
`cubage-c-chemin-initial-invalide.xml` indique zéro cas ; elle ne constitue
pas une validation et reste conservée. Le passage après correction du chemin
est la preuve des huit cas. Aucun taux global ni 100 % de couverture n'est
déduit de cette micro-suite ; la politique DEC-000066 reste applicable.

## 6. D — Dépendances et scan réel de l'image

`/workspace/outputs/2026-11-16/pr74-blocages/dep-baseline-21.json` extrait
la baseline du scan d'image précédent : 21 occurrences corrigeables,
17 HIGH et 4 CRITICAL, dont 10 système et 11 Python. Ce relevé ne constitue
pas un nouveau scan de l'image corrigée.

Le commit `fdc1da7` modifie le Dockerfile canonique, `pyproject.toml` et
`uv.lock`. Cinq versions du verrou changent : aiohttp 3.14.3 → 3.14.4,
certifi 2026.6.17 → 2026.10.18, dnspython 2.8.0 → 2.9.2, pyasn1 0.6.4 →
0.6.5 et yarl 1.24.5 → 1.25.1, imposé par aiohttp. Les 130 autres
enregistrements de paquets restent identiques selon le relevé du lot D.
Le verrou et sa synchronisation `--locked --extra dev` dans un nouvel
environnement externe ont été vérifiés, code 0.

Les stages Python retiennent
`python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`.
Le digest du manifeste officiel téléchargé correspond au SHA-256 calculé,
et les versions système ci-dessous ont été relevées dans cette base,
code 0. Cette inspection de la base est distincte de la construction et
du scan API réel documentés ci-dessous. uv est fixé à 0.13.4 ; son installation
est également journalisée dans le build CI.

### 6.1 Correspondance des 21 occurrences

La colonne finale indique une version vérifiée dans la base Python officielle,
dans le verrou corrigé ou dans le Dockerfile. Le scan réel de l'image
reconstruite confirme ensuite l'absence de chacun des 21 couples paquet/alerte
ci-dessous ; la preuve ne repose donc pas sur les seules versions.

| Paquet | Alerte | Niveau | Version de la baseline | Version correctrice retenue et vérifiée |
|---|---|---|---|---|
| apt | CVE-2026-109518 | HIGH | 2.6.1 | 2.6.2 — base Python |
| libapt-pkg6.0 | CVE-2026-109518 | HIGH | 2.6.1 | 2.6.2 — base Python |
| libpcre2-8-0 | CVE-2026-103111 | HIGH | 10.42-1+deb12u1 | 10.42-1+deb12u2 — base Python |
| libssl3 | CVE-2026-84782 | HIGH | 3.0.20-1~deb12u2 | 3.0.22-1~deb12u2 — base Python |
| openssl | CVE-2026-84782 | HIGH | 3.0.20-1~deb12u2 | 3.0.22-1~deb12u2 — base Python |
| perl-base | CVE-2026-13221 | CRITICAL | 5.36.0-7+deb12u3 | 5.36.0-7+deb12u4 — base Python |
| perl-base | CVE-2026-42496 | CRITICAL | 5.36.0-7+deb12u3 | 5.36.0-7+deb12u4 — base Python |
| perl-base | CVE-2026-42497 | HIGH | 5.36.0-7+deb12u3 | 5.36.0-7+deb12u4 — base Python |
| perl-base | CVE-2026-48962 | HIGH | 5.36.0-7+deb12u3 | 5.36.0-7+deb12u4 — base Python |
| perl-base | CVE-2026-57432 | HIGH | 5.36.0-7+deb12u3 | 5.36.0-7+deb12u4 — base Python |
| aiohttp | CVE-2026-111064 | HIGH | 3.14.3 | 3.14.4 — verrou |
| aiohttp | CVE-2026-111066 | HIGH | 3.14.3 | 3.14.4 — verrou |
| aiohttp | CVE-2026-123817 | HIGH | 3.14.3 | 3.14.4 — verrou |
| certifi | GHSA-6q48-6c7w-9gw2 | CRITICAL | 2026.6.17 | 2026.10.18 — verrou |
| dnspython | CVE-2026-114605 | HIGH | 2.8.0 | 2.9.2 — verrou, supérieure au correctif 2.9.0 de cette occurrence |
| dnspython | CVE-2026-128089 | HIGH | 2.8.0 | 2.9.2 — verrou |
| pyasn1 | CVE-2026-119194 | HIGH | 0.6.4 | 0.6.5 — verrou |
| pyasn1 | CVE-2026-119195 | HIGH | 0.6.4 | 0.6.5 — verrou |
| pyasn1 | CVE-2026-119196 | HIGH | 0.6.4 | 0.6.5 — verrou |
| pyasn1 | CVE-2026-119197 | HIGH | 0.6.4 | 0.6.5 — verrou |
| uv | GHSA-hq85-5cpj-mr62 | CRITICAL | 0.12.10 | 0.13.4 — Dockerfile |

### 6.2 Compatibilité ciblée et limites

Les imports, versions, contexte TLS avec certificat et nom d'hôte exigés,
validation d'adresse sans DNS, aller-retour ASN.1 et création de contexte
client S3 sans requête rendent le code 0. Le nouvel environnement local est
Python 3.12.14 ; la base d'image inspectée contient Python 3.12.16. Les tests
locaux ne constituent donc pas une exécution de l'API dans cette image.

Commande relevée depuis `GSIE/API` :

~~~bash
GSIE_ENVIRONMENT=development PYTHONPATH=src \
/workspace/.onboarding/venvs/quintessences-pr74-security-0034/bin/python \
  -m pytest tests/unit/test_google_identity.py \
  tests/unit/test_object_storage.py tests/unit/test_auth_type_jeton.py \
  --no-cov -q -n 2
~~~

`dep-compatibility-tests.json` atteste 58 réussis, 0 échec/erreur/ignoré,
5,407 s, code 0. Le digest du JUnit y est conservé. Ruff et mypy strict
rendent aussi 0 selon l'orchestrateur ; `mypy-final-0034.log` indique
« Success: no issues found in 272 source files ».

| Preuve D attendue | État |
|---|---|
| Versions correctrices reliées aux 21 occurrences | 21 couples absents du scan réel après construction |
| Compatibilité avec les nouvelles dépendances | 58 tests réussis et contrôles sans réseau à 0 ; portée ciblée |
| Construction réelle depuis le Dockerfile canonique, SHA/digest de l'image | Réussie en CI ; manifeste `sha256:2352dd5755ec1fb639e09e015a2753e649ad4e8359d85cef83f0673bab7ed654` |
| Scan Trivy de cette image, scanner/base, code et rapport | Job `133511159588` vert ; Trivy 0.70.0, porte HIGH/CRITICAL corrigeables à 0, aucun repli filesystem |

Artefacts du lot D sous `pr74-blocages/` : `dep-after-lock.json`,
`dep-final-implementation.json`, `dep-import-compatibility.json`,
`dep-compatibility-tests.json`, `dep-python-image-manifest.json` et
`dep-python-image-packages.json`. Le relevé final précise
`api_image_built_locally=false` et `api_image_scanned_locally=false`.
Aucune exclusion n'est ajoutée ; seuils et politique de scan sont inchangés.

Le scan CI est fait sur le checkout `4efecee` qui réunit `fdc1da7` et
`main` (`d7b400c`). L'image n'est pas publiée. Sa configuration est
`sha256:f66ad8e9c363768bf238bb32328b273ed90f9cbc1a2ef12a2231ae279ebce3d9`.
La base Trivy est téléchargée de `mirror.gcr.io/aquasec/trivy-db:2` entre
18:24:21 et 18:24:26 UTC ; digest du contenu et date interne ne sont pas
journalisés et restent inconnus.

**118 couples paquet/alerte OS restent signalés**, 116 HIGH et 2 CRITICAL,
sur 32 paquets et 48 identifiants distincts ; aucune version corrigée n'est
indiquée pour eux dans ce scan bookworm. Les dépendances Python ont zéro
alerte HIGH/CRITICAL rapportée. L'[annexe exhaustive](TRIVY_PR74_RESIDUELLES_2026-11-16.md)
donne chaque ligne, raison, risque rapporté et limites d'applicabilité.
Les deux CRITICAL sont SQLite `CVE-2025-7458` et zlib `CVE-2023-45853` ;
la note Debian sur MiniZip et l'association anormale zlib/webpack y sont
conservées. Les deux exclusions préexistantes restent inchangées et sont
nommées dans l'annexe ; aucune nouvelle n'est ajoutée. Une porte verte
ne constitue pas une validation de sécurité de production.

## 7. E et F — Propositions sans implémentation implicite

### 7.1 MinIO

Le refus est reproduit sur Docker Hub et Quay pour les références serveur
et client : authentification anonyme HTTP 200, droits `access=[]`, puis
manifeste HTTP 401 `UNAUTHORIZED`. Des images publiques de contrôle rendent
200 sur les deux registres, avec empreinte calculée égale au digest annoncé.
La cause opérationnelle est donc l'absence de droit de téléchargement anonyme
sur ces références, avant tout scénario Registry/HA. Ces preuves ne tranchent
pas la cause administrative : retrait, dépôt privé ou autre politique du
fournisseur ne sont pas déduits du seul 401. Un changement vers Quay seul
ne corrige pas le problème observé.

Les anciens binaires officiels GitHub sont disponibles : leurs SHA calculés
concordent avec les digests GitHub et fichiers `.sha256sum` ; un smoke S3
jetable réalise health 200, création, écriture, lecture identique et nettoyage.
**Ce smoke est un diagnostic, pas la solution retenue** : le serveur de
septembre est affecté par [CVE-2025-62506 / GHSA-jjjj-jwhf-8rgr](https://github.com/minio/minio/security/advisories/GHSA-jjjj-jwhf-8rgr), corrigée
en octobre. La release corrigée ne publie aucun binaire précompilé.

Proposition à qualifier : construire depuis les archives officielles suivantes,
dont les octets ont été réellement téléchargés et vérifiés via deux URL
officielles concordantes. Les empreintes ci-dessous sont calculées localement,
sans leur attribuer une signature amont absente.

| Composant | Révision et archive officielle | SHA-256 calculé |
|---|---|---|
| Serveur `RELEASE.2025-10-15T17-29-55Z` | [minio/minio, commit 9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a](https://codeload.github.com/minio/minio/tar.gz/9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a), 24 232 282 octets | `45521908307306e925c98d629e1c17d78c8b72b6ee242b1bfb1409f7d8ee5841` |
| Client `RELEASE.2025-08-13T08-35-41Z` | [minio/mc, commit 7394ce0dd2a80935aded936b09fa12cbb3cb8096](https://codeload.github.com/minio/mc/tar.gz/7394ce0dd2a80935aded936b09fa12cbb3cb8096), 564 228 octets | `95cd293c7119f16921a6dc515a1fb74a2227f19fd994b9c8b770a154e802ac44` |

Leurs `go.mod`, `go.sum`, licences et fichier de correction concordent avec
les fichiers du commit. La future recette doit épingler outils et sources,
vérifier `go mod verify`, conserver licences/provenance, produire SBOM et
scan, puis prouver S3/IAM et HA avant de mesurer ses véritables digests OCI.
Une plateforme linux/amd64 a servi au smoke historique ; la construction
des sources corrigées reste à exécuter sur un runner adapté. Aucun digest
d'image MinIO nouvelle n'est inventé. L'exécution du compilateur candidat
et la recette existant sur une autre branche n'ont pas été qualifiées ici.

Les dépôts amont sont archivés : reproductibilité des octets et disponibilité
ne garantissent pas une maintenance en sécurité. Ce risque reste ouvert.
Ni Compose, ni workflows Registry/HA ne sont modifiés au point E. Emplacements
d'une future correction : `GSIE/API/docker-compose.yml:195,224`,
`.github/workflows/ci.yml:447,460` et `.github/workflows/ha-linux.yml:75`.
Le refus continue donc de rendre ces jobs rouges.

Preuves : `pr74-blocages/minio-e/rapport-e.json`, `registres-anonymes.json`,
`sources-verifiees.json`, `binaires-verifies.json` et `ci-extraits.json`.
Processus, binaires et données propres au smoke sont supprimés ; aucun
volume original ni déploiement n'est concerné.

### 7.2 Course ix_resource_gsie_id

La campagne unique du 16 novembre, de 18:21:33 à 18:22:05 UTC, a fixé son
budget avant lancement : 12 salves de huit analyses par variante, sur une
base vierge distincte clonée du même template migré à `20260929_0059`.
Les analyses reprennent la fixture du test
`test_analyses_concurrentes_avec_sessions_independantes_sont_persistantes`
et exécutent les moteurs réels avec huit sessions/transactions indépendantes.
Une barrière externe juste avant l'insertion de l'agent rend leur arrivée
simultanée ; elle n'ajoute aucune reprise ni sérialisation.

| Variante | Analyses | Réussites | Échecs conservés |
|---|---:|---:|---:|
| Code courant, `ON CONFLICT (id) DO NOTHING` | 96 | 94 | 2 |
| Prototype externe, `ON CONFLICT DO NOTHING` sur la racine uniquement | 96 | 96 | 0 |

Les deux erreurs baseline, salve 1/session 3 et salve 9/session 6, sont
`asyncpg.exceptions.UniqueViolationError`, SQLSTATE `23505`, contrainte
`ix_resource_gsie_id`. Les huit sessions utilisaient le même UUID moteur et
le même `gsie_id` canonique. L'arbitre explicite sur la PK dans
[engine.py:433](../../GSIE/API/src/gsie_api/engines/recommendation/engine.py#L433)
ne couvre pas l'autre unicité déclarée dans
[base.py:68](../../GSIE/API/src/gsie_api/infrastructure/models/base.py#L68).
Le prototype élargit uniquement cette clause de conflit, hors du dépôt.

Les 192 arrivées et libérations de barrière, huit PID/XID par salve, les
190 analyses réellement persistées et l'absence de timeout ont été contrôlés.
Le code 0 du harnais signifie « campagne terminée et preuves cohérentes » ;
il n'efface pas les deux erreurs du code courant. Ce n'est pas une nouvelle
exécution du nœud pytest exact. Les sources et le test suivi restent inchangés.

Deux sondes bornent la proposition : `gsie_id` déjà lié à un autre UUID donne
un échec FK `agent_id_fkey` (`23503`) ; un UUID racine de type `concept` peut
recevoir un enfant Agent. Retirer la cible ne garantit donc pas seul la
cohérence. Proposition à relire : insertion racine sans cible, relecture
réellement fraîche du tuple UUID/type `agent`/`gsie_id` attendu avant l'enfant,
contrôle du type Agent après son insertion, refus des incohérences sans
écrasement ni alias d'identité. Un verrou est à envisager pour maintenir la
garantie jusqu'au commit. Aucune immuabilité du nom n'est inventée.
Ces gardes complémentaires ne sont ni implémentées ni testées ici ; les
96 succès du prototype ne prouvent pas une correction universelle.

Preuves : `pr74-blocages/concurrence-f/plan.json`, `harnais_f.py`,
`campagne-01/bilan.json`, `constat.json`, `evenements.ndjson`, les 24 salves
et `manifest-final.json`. Conteneur, volume et Ryuk propres à la campagne
ont été retirés et contrôlés absents ; aucun original n'a été monté.

## 8. Contrôles finaux et publication

Les résultats complets ci-dessous portent sur le code `fdc1da7`.
Le venv local externe est
`/workspace/.onboarding/venvs/quintessences-pr74-security-0034` ; la CI utilise
Python 3.12.16 et le même verrou. Les quatre contrôles sont aussi réexécutés
sur la clôture documentaire. Les résultats de cette dernière CI seront ajoutés
à la description de la PR avec son SHA après publication, sans les attribuer
au run antérieur.

| Commande ou preuve | Résultat / code |
|---|---|
| Racine : `python3 tools/check_governance_consistency.py` | 0 |
| Racine : `python3 tools/check_source_of_truth.py` | 0 ; 10 sources contrôlées |
| Racine : `python3 tools/check_ai_prompts.py` | 0 ; 25 missions contrôlées |
| Racine : `python3 tools/check_build_consistency.py` | 0 |
| API : `python -m alembic heads` | 0 ; `20260929_0059 (head)` |
| API : SQL `upgrade base:head --sql` sans connexion | Réussi dans B ; une création et garde anti-doublons vérifiées |
| API : migrations et invariants PostgreSQL jetable | 21 ciblés réussis, dont 10 PostgreSQL ; SQL réellement exécuté, puis 11 unitaires finaux réussis |
| API : huit tests cubage et couverture | 8 réussis, code 0 ; module 154/154 lignes, aucune exclusion |
| API : venv de sécurité, `python -m pytest tests/ -q -n 2` | 0 ; 3 588 réussis, 64 ignorés, aucun échec/erreur ; 3 652 cas, 783,34 s pytest |
| `scripts/check_coverage_policy.py --report coverage-full-0034.json` | 0 ; 19 532 / 20 097 lignes, 97,19 % ; contrats publics 100 %, autres seuils respectés |
| Lint, typage et mutation | Ruff et mypy strict à 0 ; CI : 72/72 mutations détectées |
| Image reconstruite, compatibilité, Trivy réel | 58 tests ciblés réussis ; Docker et Trivy verts, avec les limites §6 |
| Reproductions et propositions MinIO / concurrence | Réalisées ; E/F proposés et non appliqués, rouges conservés |
| Revue indépendante | Rôles architecture, implémentation, QA, documentation et revue séparés ; preuves B/C/D/F relues |
| Gel de la suite locale | Empreinte des 733 fichiers API suivis identique avant/après : `a0eb2aa72c0747de889c2756ca12495bba391a4a1ffb8f8cffb9429226505abe` |
| Clôture documentaire après tests | Dans l'API, seule la paire de fences README change ; source, tests, verrou, Dockerfile et migrations inchangés |
| CI source complète | Run `43926095467`, tête `fdc1da7`, événement `pull_request`, checkout `4efecee` ; détail ci-dessous |
| PR et sauvegarde | Même PR74 ; branche de remise `backup/quintessences-pr74-2026-11-16-gsie-prompt-0034`, SHA relu après publication et indiqué dans la remise |

Les 64 ignorés sont préexistants : 46 seeds legacy v6.1, 14 schéma legacy
v6.1, trois tests nécessitant le module Rust absent du venv Python, un CSV
Treekipedia réel indisponible. Aucun n'est compté comme réussi ; aucun nouveau
`skip` n'est ajouté. Le job Rust est vérifié séparément. Le JUnit, le relevé
des motifs et le gel avant/après sont dans `full-suite-0034.xml`,
`full-suite-0034-inventaire.json` et `full-suite-0034-state.json` ;
`api-normalized-diff-apres-tests.json` vérifie le seul delta README ensuite.

### CI complète du code API `fdc1da7`

| Job | Résultat observé |
|---|---|
| Lint Markdown | ROUGE — MD048 README ; correction locale vérifiée ensuite, ci-dessous |
| Consistency Checks | VERT |
| Governance Guard | VERT |
| Python lint + type + test | VERT — 3 210 réussis, 64 ignorés |
| Python integration tests (PostGIS + Redis) | VERT — 378 réussis, aucun ignoré |
| Python mutation harness | VERT — 72/72 mutations détectées |
| Python couverture combinée | VERT — 97,19 %, politique par couche respectée |
| Rust clippy + test | VERT |
| Docker build | VERT |
| Data Registry (PostgreSQL + MinIO) | ROUGE — refus de téléchargement `minio/minio` |
| Scan de sécurité (Trivy) | VERT — image réelle, 21 couples corrigés, résiduelles §6 |
| Analyse SAST Python (Bandit) | VERT |
| CI Gate (bloque merge) | ROUGE — Markdown et Data Registry rouges |

[Run CI et logs](https://github.com/NeooeN45/Quintessences/actions/runs/43926095467).
Autres workflows sur la même tête :
[Source governance](https://github.com/NeooeN45/Quintessences/actions/runs/43926095444)
VERT ; [Sécurité du dépôt](https://github.com/NeooeN45/Quintessences/actions/runs/43926095583)
VERT ; [GSIE HA Linux TLS](https://github.com/NeooeN45/Quintessences/actions/runs/43926095492)
ROUGE au téléchargement `minio/mc`, avant preuve HA.

La CI de `fdc1da7` a signalé un échec Markdown sur
`GSIE/API/README.md:317` : MD048 attend des backticks et trouve un fence tilde,
dans un fichier qui utilise déjà des backticks. Ce rouge est conservé.
Après la fin du gel API, seules les deux fences de cet exemple sont remises
en backticks ; le lint du README rend 0. Le résultat rouge de ce run reste
conservé ; le résultat CI du commit documentaire suivant doit être lu
séparément. Les jobs MinIO restent bloqués tant que la proposition E n'est
pas implémentée et qualifiée. Le vert ponctuel du test concurrent dans la
suite globale ne clôt pas la course reproduite au point F.

Aucune fusion de PR, aucun push sur `main` et aucun déploiement n'est autorisé
par la remise. E et F restent limités à leur proposition.

## 9. Risques et limites

| Risque ou limite | Traitement |
|---|---|
| Bases B/`0060` inconnues de la nouvelle lignée | Nouvelle base vide ; pas de conversion conservatoire |
| Révision `20261003_0052` de la recette hiérarchie | Original intact, diagnostic séparé |
| Inventaire limité aux volumes connus | Déclaration du Fondateur distinguée ; arrêt si donnée réelle découverte |
| Confusion entre SQL émis et exécuté | Les deux sont prouvés par B ; conserver leur portée jetable et les rouges initiaux |
| Retrait cubage et couverture | Deux lignes, huit tests et 154/154 lignes démontrés ; autres validations conservées |
| Versions ou images incompatibles | Verrou, construction, tests et scan de l'image effective |
| MinIO indisponible et amont archivé | Sources corrigées vérifiées ; construction, sécurité, S3/IAM et HA à qualifier avant adoption |
| Course reproduite mais non corrigée | Deux erreurs causales conservées ; proposition et gardes d'identité à relire, moteur inchangé |
| 118 résiduelles Trivy sans version corrigée indiquée | Annexe exhaustive, deux CRITICAL et réserves d'applicabilité ; aucune validation de sécurité de production |
| CI Registry/HA rouge | Remise en revue avec réserves ; aucune fusion ou acceptation globale |
| Markdown README rouge MD048 dans le run source | Correction documentaire après gel, lint local à 0 ; CI suivante séparée |
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
| 2026-11-16 | Ajout des preuves ciblées B/C/D, des 21 correspondances de sécurité et du rouge Markdown ; suite globale, image API, Trivy et travaux E/F toujours distincts et en attente |
| 2026-11-16 | Clôture technique : suite et couverture conformes, vrai scan d'image et 118 résiduelles publiées, E/F reproduits et proposés ; relecture et intégrations E/F encore ouvertes |
