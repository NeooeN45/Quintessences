# RFC-0038 — Data Registry et contrat de données environnementales GSIE

| Champ | Valeur |
|---|---|
| **Identifiant** | RFC-0038 |
| **Statut** | Validated |
| **Auteur** | Devin, sous autorité du Fondateur |
| **Date** | 2026-08-10 |
| **Motivation** | Découpler les moteurs et applications Quintessences des fournisseurs de données externes |
| **Périmètre** | GSIE Server, Data Registry, métadonnées, licences, versions, provenance et préparation du Data Broker |
| **Décision liée** | DEC-000059 — Validated, adoption formelle du Data Registry |
| **Précédents** | ADR-006, RFC-0029, DEC-000039, DEC-000041, GSIE-CON-005, GSIE-CON-007, GSIE-CON-010 |
| **Complément** | `GSIE-DATA-AUDIT-0001` v1.5.0 et `GSIE-DATA-RESEARCH-0001` |

## 1. Résumé

Cette RFC propose de faire de GSIE Server la couche autoritative de référencement, qualification, versionnement, provenance et distribution des données environnementales. Les applications et moteurs demandent une capacité ou une donnée ; ils ne choisissent plus directement un fournisseur externe.

La proposition réutilise le métamodèle v6.2 existant, ajoute uniquement les projections et attributs nécessaires aux recherches opérationnelles, et conserve STAC, les formats cloud-native et les moteurs analytiques comme projections ou plans de traitement spécialisés.

## 2. Problème

Les sources sont actuellement réparties entre :

- `GSIE/DATASETS/DATASET_CATALOG.md` ;
- `SOURCES_DONNEES_EXHAUSTIVES.md` ;
- le registre juridique déclaratif `SCIENTIFIC_SOURCES` de
  `GSIE/API/src/gsie_api/governance/source_registry.py` ;
- les clients directement attachés aux moteurs Botanical, Climate, GIS et Pedology.

Le métamodèle contient déjà `Dataset`, `DatasetVersion`, `DataAsset`, `Distribution`, `Source`, `Agent`, `RightsStatement`, `QualityAssessment` et les types PROV, mais aucune façade opérationnelle ne les assemble pour :

- rechercher une donnée par thème, zone et période ;
- vérifier sa licence et ses droits d’usage ;
- comparer résolution, fraîcheur, qualité et disponibilité ;
- exposer sa provenance ;
- choisir une source de remplacement ;
- distribuer des fichiers ou projections sans exposer le fournisseur aux clients.

Une nouvelle architecture parallèle serait contraire à DEC-000051 et créerait plusieurs sources de vérité.

## 3. Objectifs

### 3.1 Objectifs inclus

1. Définir l’identité stable d’un dataset GSIE.
2. Définir la relation entre le fournisseur (projection `Agent`/`Source`),
   `Dataset`, `DatasetVersion`, `Distribution` et `DataAsset`, sans créer de
   ressource `Provider` concurrente.
3. Définir les statuts du cycle de qualification et de publication.
4. Définir les métadonnées minimales requises pour la recherche et la sélection.
5. Définir le stockage des contrôles de santé et des versions observées.
6. Garantir la conservation de l’Evidence Level A–F distinct de la qualité
   technique et des évaluations des assertions produites par les moteurs.
7. Préparer une API interne de Registry sans exposer encore un contrat
   fournisseur aux applications.
8. Préparer l’intégration ultérieure des adapters et du Data Selection Engine.

### 3.2 Hors périmètre

- implémentation immédiate des adapters IGN, GBIF, SoilGrids ou Météo-France ;
- ingestion de téraoctets dans PostgreSQL ;
- adoption immédiate d’Iceberg, Spark, Sedona, TileDB ou cuObject ;
- migration des applications clientes ;
- arbitrage d’une licence commerciale externe ;
- ajout d’un nouveau moteur GSIE.

## 4. Principes obligatoires

### 4.1 Une seule autorité GSIE

Le Data Registry GSIE est l’autorité pour :

- l’identité du dataset ;
- la version retenue ;
- le statut d’utilisation ;
- la licence et les droits déclarés ;
- l’Evidence Level ;
- la qualité et la fraîcheur constatées ;
- la provenance et les transformations ;
- la décision de publication en production.

STAC, Iceberg, DuckDB, DataFusion et les catalogues de fournisseurs sont des projections ou des systèmes de lecture. Aucun ne remplace le Registry GSIE.

### 4.2 Données volumineuses hors PostgreSQL

PostgreSQL/PostGIS conserve les métadonnées, les emprises, les index métier, les versions et les relations. Les octets volumineux restent dans MinIO/S3 ou un stockage compatible.

Les formats recommandés sont :

- COG pour les rasters ;
- GeoParquet pour les vecteurs et tables spatiales ;
- COPC/LAZ pour le LiDAR ;
- Zarr pour les cubes spatio-temporels ;
- Parquet pour les tables analytiques.

### 4.3 Qualification avant production

Un dataset ne peut pas être publié en production uniquement parce qu’une URL répond HTTP 200. La licence, la couverture, le schéma, le checksum, la sécurité et la qualité doivent être contrôlés.

### 4.4 Evidence distincte de la qualité

Le niveau de preuve GSIE A–F est conservé tel que défini dans `EVIDENCE_FRAMEWORK.md`. Il ne doit pas être remplacé par un score de fraîcheur, de disponibilité ou de précision technique.

## 5. Contrat conceptuel

### 5.1 Fournisseur, Agent et Source

Aucune ressource ou table `Provider` concurrente n’est créée dans cette RFC.
Le mot « fournisseur » désigne uniquement une projection de l’identité et des
origines suivantes :

- `Agent` de type `organisation` pour l’identité stable du producteur ou de
  l’opérateur ;
- `Source` pour une publication, une API, un catalogue ou un service citable ;
- `ScientificSourceEntry` pour la porte juridique déclarative et l’amorçage
  contrôlé.

`Dataset.publisher_id` référence l’`Agent` producteur. La relation de
provenance vers les origines est matérialisée par `Citation` (`source_id` vers
`target_id` égal au `Dataset` ou à la `DatasetVersion`, avec un rôle
`primary`, `supporting`, `contradicting` ou `cited`). Une version qualifiable
doit posséder au moins une citation primaire ou documenter explicitement
pourquoi elle n’en possède pas ; une URL ou un nom d’organisation en texte
libre ne constitue jamais cette relation.

`Agent` est l’identité organisationnelle, `Source` l’origine citable ou
technique et `Dataset` la ressource logique. Ces concepts ne doivent pas être
fusionnés. La projection « fournisseur » renvoie donc l’`Agent` et les
`Source` citables associés ; elle ne crée pas d’identité supplémentaire.

La liaison entre l’identifiant déclaratif `ScientificSourceEntry.identifiant`
et les resources persistées se fait par `EntityAlias` avec un namespace
explicite (par exemple `scientific_source_registry`). Elle ne repose pas sur un
slug ou une URL mutable. Le registre déclaratif reste un prérequis juridique,
pas une seconde source de vérité métier.

### 5.2 Dataset

`Dataset` représente l’identité logique stable d’un jeu de données. Le modèle
v6.2 possède déjà `title`, `description`, `publisher_id`, `topic` et
`purpose`. Les champs ci-dessous complètent ce socle ; ils ne remplacent pas
les champs existants.

Champs minimaux proposés :

```text
id
slug
title
description
publisher_id → Agent
purpose
primary_domain
domains[]
tags[]
domain_vocabulary_version
```

Règles :

- `slug` est obligatoire pour une entrée qualifiée, unique, immuable, en
  minuscules, au format lisible `^[a-z0-9]+(?:-[a-z0-9]+)*$` ; il ne contient
  ni version ni URL de fournisseur ;
- `primary_domain` est une clé du vocabulaire de domaines GSIE ; `domains[]`
  contient les autres domaines contrôlés et `tags[]` des mots-clés normalisés
  sans doublon ;
- `domain_vocabulary_version` est obligatoire dès qu’un domaine contrôlé est
  renseigné ; il permet de rejouer une sélection historique après évolution
  du vocabulaire ;
- `publisher_id` doit cibler un `Agent` de type `organisation` avant
  `VALIDATED` ; il peut rester nul à l’état `DISCOVERED` pour préserver les
  entrées historiques en cours de qualification ;
- `topic` reste un champ v6.2 libre de compatibilité et d’affichage. Une fois
  `primary_domain` renseigné, le resolver n’utilise plus `topic` comme seconde
  source de vérité.

Le vocabulaire de domaines GSIE n’est pas encore matérialisé dans le modèle
v6.2. Il devra être versionné (identifiant, libellé et date d’effet) avant la
première migration qui rend `primary_domain` obligatoire ; une valeur inconnue
est rejetée et ne peut pas être traitée comme un simple tag. Tant que ce
vocabulaire n’est pas adopté, ces champs restent optionnels pour les entrées
`DISCOVERED` et `topic` ne peut servir qu’à l’affichage ou à une recherche
explicitement non qualifiée.

### 5.3 DatasetVersion

`DatasetVersion` représente une publication immuable d’un `Dataset`. Les
champs de contenu et les empreintes d’une version ne sont pas écrasés ; les
changements de cycle de vie sont des transitions historisées par `Revision`.
Une correction de contenu ou de couverture crée une nouvelle version, jamais
une mise à jour silencieuse de la précédente.

Champs minimaux proposés :

```text
dataset_id
version
release_date
temporal_coverage_start
temporal_coverage_end
changes
schema_hash
stats
status
evidence_level
evidence_basis
evidence_assessed_at
```

Contraintes et nullabilité par étape :

- `version` est obligatoire et unique par `dataset_id` ;
- `release_date` est obligatoire avant `VALIDATED` ;
- `temporal_coverage_start` et `temporal_coverage_end` sont nullables pour
  une donnée non temporelle, sinon ils décrivent une couverture inclusive et
  vérifient `start <= end` ;
- `schema_hash` est obligatoire pour une distribution structurée avant
  `SCHEMA_ANALYZED` ; il s’agit du SHA-256 du schéma canonique, et non du
  checksum des octets ;
- `stats` reste le résumé JSON validé et versionné, jamais une preuve de
  qualité implicite ;
- `status` est porté par l’enum dédié `DatasetStatus` décrit au §6.1, distinct
  de `DatasetPurpose` et de `LifecycleStatus`.
- `evidence_level`, `evidence_basis` et `evidence_assessed_at` forment la
  qualification Registry de cette version. Ils sont nuls à la découverte et
  deviennent obligatoires avant `PRODUCTION` pour une distribution destinée à
  l’inférence ; une absence de qualification bloque `use=inference`, sans
  être remplacée par le niveau F.
- `evidence_basis` est un JSON validé contenant au minimum les identifiants de
  sources/citations, la portée et la justification de la qualification ; il ne
  peut pas être un texte libre non traçable.

Une version dépréciée reste interrogeable pour la provenance historique mais
ne peut plus être sélectionnée par défaut. Les lignes v6.2 existantes sont
initialisées à `DISCOVERED` lors de la migration, sauf manifeste de qualification
revu explicitement ; aucune promotion automatique en `PRODUCTION` n’est
autorisée.

### 5.4 Distribution

`Distribution` décrit un canal ou un produit d’accès à une DatasetVersion :

```text
dataset_version_id
access_method
access_url
licence
data_rights_statement_id
scale_context_id
coverage_place_id
format
crs[]
```

Une version peut avoir plusieurs distributions : API, STAC, COG, GeoParquet,
COPC ou Zarr. La résolution native est portée par `ScaleContext` et ne doit
pas être dupliquée dans un champ concurrent. `coverage_place_id` référence un
`Place` PostGIS lorsque la distribution est spatiale ; il autorise la recherche
par emprise sans ajouter une géométrie concurrente à `DatasetVersion`. Une
couverture inconnue reste nulle et ne satisfait pas un filtre spatial. Les
empreintes propres à chaque scène ou fichier pourront être projetées dans STAC
ultérieurement ; elles ne sont pas inventées à partir d’une couverture globale.

Le modèle v6.2 expose actuellement `rights_statement_id`. Pour préserver la
compatibilité du CRUD générique, l’adoption ajoute
`data_rights_statement_id` comme champ canonique pour les distributions de
datasets ; `rights_statement_id` reste nullable, en lecture seule pour les
anciennes lignes, et ne doit plus être renseigné pour une nouvelle distribution
qualifiée. Une migration ne remplit pas ce champ par approximation : chaque
reprise doit être justifiée par une correspondance juridique vérifiée.

### 5.4.1 DataRightsStatement

`DataRightsStatement` est distinct de `RightsStatement`.

- `RightsStatement` reste dans `gsie_rgpd` pour les politiques et déclarations de droits liées aux données sensibles ou personnelles ;
- `DataRightsStatement` vit dans `gsie_gouvernance` pour les licences et droits d’usage des datasets environnementaux ;
- `Distribution.data_rights_statement_id` pointe vers cette déclaration de droits générale ;
- aucun rôle de moteur ne reçoit un accès au schéma RGPD pour lire une licence ouverte.

Les deux types portent donc des contrats différents, même si l’ancien champ
`rights_statement_id` est conservé temporairement pour les lignes historiques.

`Distribution.licence` est conservé comme libellé ou snapshot fourni par la
source pour compatibilité et affichage. La décision juridique et les filtres
de sélection utilisent exclusivement `data_rights_statement_id` ; une
divergence entre les deux doit être signalée et bloque la qualification, elle
ne doit pas être arbitrée silencieusement par le resolver.

Champs minimaux :

```text
licence
usage_rights
commercial_use_allowed
redistribution_allowed
attribution_required
ai_training_allowed
notes
```

### 5.5 DataAsset

`DataAsset` représente l’objet physique ou logique archivé :

```text
dataset_version_id
format
size_bytes
checksum
checksum_algorithm
storage_uri
original_uri
archived_from
archived_at
```

`storage_uri` pointe vers MinIO/S3. `original_uri` pointe vers l’origine externe. `checksum` et `archived_at` permettent de prouver l’octet utilisé.

Après archivage, `checksum`, `checksum_algorithm`, `size_bytes` et
`storage_uri` sont immuables. Un remplacement d’octets ou de contenu crée un
nouvel `DataAsset`, une nouvelle révision et, si le contenu publié change, une
nouvelle `DatasetVersion`.

Pour un actif `STAGING` ou `PRODUCTION` possédé par GSIE, `storage_uri`,
`checksum`, `checksum_algorithm` et `archived_at` sont obligatoires. Le schéma
`s3://` (ou un endpoint S3 compatible configuré) est obligatoire en staging et
en production ; `local:///…` est réservé au développement/test et ne peut
jamais être transformé en URL présignée ou exposé comme chemin serveur. Un
actif distant seulement référencé reste possible pour l’affichage, mais il ne
peut pas fonder une conclusion citable sans archivage ou checksum daté,
conformément à RFC-0029 et `NOMENCLATURE_SOURCES.md`.

### 5.6 DatasetHealth

Un nouveau contrôle de santé doit être une table satellite ou une resource
spécialisée, sans remplacer `HealthResponse` de l’API. Il porte sur une
`Distribution`, pas seulement sur une `DatasetVersion` : une API et un asset
S3 d’une même version peuvent avoir des états différents.

Champs minimaux proposés :

```text
dataset_version_id
distribution_id
checked_at
health_status
http_status
latency_ms
last_modified
observed_version
schema_hash
checksum_verified
error_code
```

`health_status` est un enum distinct de `DatasetStatus` :
`healthy`, `degraded`, `unavailable`, `invalid`, `unknown`. `http_status` et
`latency_ms` sont nuls pour un contrôle non HTTP ; `latency_ms` ne peut pas
être négatif. Les contrôles sont append-only ou historisés. Le dernier
résultat est une projection ; les contrôles précédents restent consultables et
ne sont jamais supprimés physiquement. Un contrôle de santé ne promeut pas à
lui seul une version : la politique Registry et, lorsque requis, une revue
humaine décident de la transition de cycle de vie.

La cohérence `distribution_id → dataset_version_id` est vérifiée par une
contrainte ou un validateur de service ; elle ne peut pas être laissée à la
seule convention du DTO. `distribution_id` est obligatoire pour tout nouveau
contrôle ; un état de santé non rattaché à une distribution n’est pas
persisté.

### 5.7 Provenance et lineage

Le lineage réutilise `Activity`, `ProvEntity` et `was_derived_from`. Le
diagramme ci-dessous est conceptuel : le lien entre un `DataAsset` et une
activité passe par une entité PROV matérialisée ; il ne doit pas être déduit
des seuls horodatages ou checksums.

```text
DatasetVersion / Distribution
        ↓ (entité PROV utilisée)
ExtractionActivity
        ↓ (entité PROV générée)
RawDataAsset
        ↓
NormalizationActivity
        ↓
NormalizedDataAsset
        ↓
DerivationActivity
        ↓
DerivedDataAsset / EngineProjection
```

Chaque activité doit pouvoir conserver :

- adapter ou pipeline ;
- paramètres ;
- version du code ;
- date ;
- résolution source et cible ;
- CRS source et cible ;
- conversions d’unités ;
- interpolation ;
- pertes d’information ;
- niveau d’incertitude.

### 5.8 Evidence Level et qualité

Le Registry conserve une qualification A–F de la version lorsqu’elle a été
explicitement évaluée (provenance, catégorie de source, convergence, méthode
et date). Cette qualification réutilise l’enum officiel `EvidenceLevel`, mais
ne transforme pas une licence, un checksum ou le nombre de citations en preuve
scientifique. Elle ne remplace jamais un `EvidenceAssessment`, qui reste
attaché à une assertion produite par un moteur. Une version sans qualification
est **non qualifiée** ; elle n’est pas assimilée au niveau F. Le resolver
applique l’ordre de `EVIDENCE_FRAMEWORK.md` (A est le plus fort, F le plus
faible) et conserve la justification, les sources et la date de l’évaluation.

Les DTOs et l’interface utilisateur doivent nommer cette valeur
**qualification Registry** et ne jamais la présenter comme le niveau de preuve
d’une assertion scientifique.

L’affectation de cette qualification Registry est donc une étape explicite de
revue ; elle n’est pas déduite automatiquement du registre juridique. Les
champs `evidence_level`, `evidence_basis` et `evidence_assessed_at` de
`DatasetVersion` portent cette projection interrogeable. Leur absence bloque
`use=inference` dès qu’un niveau minimal est requis, sans rétrograder la
version à F.

Les scores de qualité technique (`QualityAssessment`) restent distincts de
l’Evidence Level. Un score global de sélection, s’il est exposé, est une
projection normalisée dans `[0, 1]` avec ses dimensions et sa méthode ; il ne
modifie jamais le niveau de preuve.

## 6. Cycle de vie proposé

```text
DISCOVERED
    ↓
LINK_CHECKED
    ↓
METADATA_EXTRACTED
    ↓
LICENSE_ANALYZED
    ↓
COVERAGE_ANALYZED
    ↓
SCHEMA_ANALYZED
    ↓
SECURITY_CHECKED
    ↓
VALIDATED
    ↓
STAGING
    ↓
PRODUCTION
```

États de sortie ou d’exception :

```text
DEPRECATED
BROKEN
UNAVAILABLE
LICENSE_RESTRICTED
UNKNOWN_LICENSE
ARCHIVED
EXPERIMENTAL
```

La sélection par défaut ne considère que `PRODUCTION`. `STAGING` exige un appel explicite et `EXPERIMENTAL` ne doit jamais alimenter automatiquement une conclusion scientifique.

### 6.1 Enum et transitions

Le cycle est porté par `DatasetVersion.status` dans l’enum applicatif
`DatasetStatus` (type SQL `dataset_status`), distinct de `LifecycleStatus`
utilisé par les assertions.

Les constantes exposées par l’API sont en capitales pour la lisibilité ; les
valeurs persistées suivent la convention `StrEnum` du code (`discovered`,
`link_checked`, etc.). `DatasetPurpose` (`production`, `training`,
`evaluation`, `reference`) reste un usage sémantique et ne remplace pas cet
état opérationnel.

```text
DISCOVERED
LINK_CHECKED
METADATA_EXTRACTED
LICENSE_ANALYZED
COVERAGE_ANALYZED
SCHEMA_ANALYZED
SECURITY_CHECKED
VALIDATED
STAGING
PRODUCTION
DEPRECATED
BROKEN
UNAVAILABLE
LICENSE_RESTRICTED
UNKNOWN_LICENSE
ARCHIVED
EXPERIMENTAL
```

Transitions autorisées :

```text
DISCOVERED → LINK_CHECKED | BROKEN
LINK_CHECKED → METADATA_EXTRACTED | BROKEN
METADATA_EXTRACTED → LICENSE_ANALYZED | BROKEN
LICENSE_ANALYZED → COVERAGE_ANALYZED | UNKNOWN_LICENSE | LICENSE_RESTRICTED
COVERAGE_ANALYZED → SCHEMA_ANALYZED | BROKEN
SCHEMA_ANALYZED → SECURITY_CHECKED | BROKEN
SECURITY_CHECKED → VALIDATED | BROKEN
VALIDATED → STAGING | EXPERIMENTAL
STAGING → PRODUCTION | EXPERIMENTAL | BROKEN
PRODUCTION → DEPRECATED | UNAVAILABLE
DEPRECATED → ARCHIVED
EXPERIMENTAL → STAGING | ARCHIVED

Récupérations explicites, exceptionnelles et historisées :
UNAVAILABLE → LINK_CHECKED
UNKNOWN_LICENSE → LICENSE_ANALYZED
LICENSE_RESTRICTED → LICENSE_ANALYZED
```

`BROKEN` signifie que le contenu ou le contrat est invalide (checksum, schéma,
format) et impose une nouvelle version pour corriger le contenu ;
`UNAVAILABLE` signifie que l’accès est momentanément indisponible. Une
récupération ne peut être enregistrée qu’après un contrôle réussi et une
révision justifiée. Pour `UNKNOWN_LICENSE` et `LICENSE_RESTRICTED`, le retour
vers `LICENSE_ANALYZED` exige une preuve juridique nouvelle et, lorsque la
licence est interprétée, une validation humaine. Une version `DEPRECATED` ou
`ARCHIVED` n’est jamais réactivée : une nouvelle publication crée une nouvelle
`DatasetVersion`.

Les transitions sont contrôlées par le service Registry et historisées par
`Revision`. Aucun retour vers un statut antérieur n’est implicite et aucun
contrôle de santé ne contourne la machine d’état.

`UNAVAILABLE` est réservé à une indisponibilité de la version ou de toutes les
distributions requises ; l’indisponibilité d’une distribution secondaire reste
portée par `DatasetHealth` et ne dégrade pas silencieusement le statut de la
version entière.

La transition `SECURITY_CHECKED → VALIDATED` exige au minimum une licence
qualifiée, une emprise et une couverture temporelle connues lorsqu’elles sont
pertinentes, un checksum vérifiable pour tout actif possédé, et une évaluation
de qualité avec sa méthode. `VALIDATED → STAGING` puis `STAGING → PRODUCTION`
ajoutent la validation de l’usage prévu. Pour un usage d’inférence, une
distribution distante seule (`WMS`, `WMTS`, API ou autre proxy) ne suffit pas :
un `DataAsset` archivé et traçable est requis. Une distribution distante peut
néanmoins être publiée pour l’affichage ou l’exploration si cette restriction
est explicitement exposée au client.

### 6.2 Schémas PostgreSQL cibles

La baseline actuelle conserve `resource` et les tables v6.2 dans `public`,
conformément à `20260728_0012_role_applicatif` et DEC-000040. Cette RFC ne
renomme pas ces tables.

- `public` : `dataset`, `dataset_version`, `distribution`, `data_asset` et
  les resources v6.2 existantes ;
- `gsie_gouvernance` : `data_rights_statement` et `dataset_health` ;
- `gsie_rgpd` : `rights_statement`, inchangé et réservé aux droits sensibles ;
- `gsie_rgpd_identites` : identité des comptes, inchangée.

Une future migration de noyau vers `gsie_noyau` devra faire l’objet d’une RFC
séparée, car elle modifierait les cibles de nombreuses clés étrangères.

## 7. Recherche et contrat futur du Data Broker

Le Registry doit fournir un contrat de recherche conceptuel :

```json
{
  "theme": "soil_moisture",
  "bbox": [-1.2, 44.1, -0.8, 44.5],
  "bbox_crs": "EPSG:4326",
  "date_start": "2026-08-09T00:00:00Z",
  "date_end": "2026-08-09T23:59:59Z",
  "max_grain_m2": 1000000,
  "minimum_evidence_level": "C",
  "minimum_quality_score": 0.75,
  "commercial_use_required": true,
  "use": "inference",
  "prefer": ["freshness", "quality", "offline_availability"]
}
```

`soil_moisture` est une valeur illustrative ; une requête réelle doit utiliser
une clé présente dans le vocabulaire de domaines adopté et transmettre sa
version lorsque le contrat l’exige.

Règles minimales du contrat :

- `theme` est une clé ou un alias résolu par le vocabulaire de domaines
  versionné ; pour une entrée qualifiée, il ne déclenche pas une recherche
  libre sur `Dataset.topic` ;
- `bbox` est `[min_lon, min_lat, max_lon, max_lat]` en `EPSG:4326`, avec des
  coordonnées finies dans les bornes WGS84 ; le franchissement de
  l’antiméridien utilise deux emprises ou une géométrie GeoJSON explicite ;
- les dates sont en UTC et le filtre de couverture est un chevauchement
  inclusif ; une borne de couverture inconnue ne satisfait pas une contrainte
  temporelle explicite ;
- `max_grain_m2` signifie `grain_m2 <= max_grain_m2`. Un grain natif inconnu
  n’est pas rendu plus fin par rééchantillonnage et ne satisfait pas ce filtre ;
- l’ordre de preuve est `A > B > C > D > E > F`. Demander `C` accepte A, B ou
  C, jamais D, E ou F ; le resolver n’upgrade jamais un niveau ;
- `minimum_evidence_level` est obligatoire pour `use=inference`. Pour
  `use=display`, son absence signifie « ne pas filtrer sur la preuve », jamais
  « preuve suffisante » ;
- `minimum_quality_score` s’applique à un score agrégé `[0, 1]` dont les
  dimensions et la méthode sont retournées. Une qualité manquante échoue à
  cette contrainte, elle n’est pas remplacée par zéro silencieusement ; la
  fonction d’agrégation et ses pondérations sont versionnées, jamais choisies
  implicitement par le resolver ;
- `freshness` est calculée à partir de `last_modified`, `observed_version` et
  `checked_at` selon une politique versionnée. Une fraîcheur inconnue ne
  satisfait pas une contrainte explicite ; elle reste seulement un critère de
  préférence si la requête ne l’exige pas ;
- `offline_availability` est dérivée de l’existence d’un `DataAsset` archivé,
  de son accès GSIE et des droits de redistribution. Ce n’est pas un booléen
  indépendant pouvant contredire les actifs ou les droits ;
- `commercial_use_required` exige `commercial_use_allowed=true` dans la
  déclaration de droits retenue ;
- `use` vaut `display` ou `inference`. Pour `inference`, un actif archivé est
  bloquant ; pour `display`, une distribution distante peut être retenue si
  son régime est signalé ;
- les critères bloquants sont évalués avant le scoring `prefer`. Les préférences
  ne peuvent jamais faire passer un candidat qui échoue à une licence, une
  couverture, une preuve, une qualité ou une disponibilité requise ;
- pour une disponibilité requise, `unknown` et `unavailable` sont bloquants ;
  `degraded` n’est admissible que si la politique de requête le déclare ;
- les résultats sont triés de manière déterministe par une version de
  politique déclarée, puis par les critères préférés et un identifiant stable
  en cas d’égalité.

Chaque blocage retourne un code stable (`LICENSE_MISSING`, `COVERAGE_UNKNOWN`,
`EVIDENCE_MISSING`, `QUALITY_MISSING`, `ASSET_NOT_ARCHIVED`, etc.) et sa
justification. Les codes, la version de politique et les règles de priorité
font partie du contrat observable ; un texte libre seul ne permet pas de
rejouer une décision.

Le resolver n’est pas implémenté par cette RFC. Il devra cependant retourner une décision explicable :

- candidats évalués ;
- critères bloquants ;
- score par critère ;
- source retenue ;
- version ;
- éventuel fallback ;
- fraîcheur ;
- provenance.

Une réponse sans candidat admissible doit exposer les critères bloquants et ne
doit pas fournir un fallback qui les contourne. Un fallback explicite peut
être proposé uniquement s’il est évalué par la même politique et présenté
comme tel au client.

## 8. API cible du Registry

Les endpoints suivants sont proposés pour une tranche ultérieure :

```text
GET  /api/v1/data/catalog
GET  /api/v1/data/datasets/{id}
GET  /api/v1/data/providers
GET  /api/v1/data/search
GET  /api/v1/data/health
GET  /api/v1/data/coverage
POST /api/v1/data/resolve
```

Cette RFC ne les implémente pas et ne modifie pas les contrats existants de `/api/v1/resources`.

`/data/providers` est une projection paginée des relations
`Agent`/`Source`/`Citation` ; il ne correspond ni à une table ni à un type de
ressource `Provider`.

Toutes les listes devront être paginées par curseur (limite bornée, `next_cursor`
opaque et ordre stable). Les filtres de `/health` et `/coverage` doivent
identifier respectivement la distribution et le système de coordonnées. Les
endpoints seront authentifiés, soumis au rate limiting, corrélés par
`trace_id`, et ne renverront jamais directement un secret, un chemin local ou
une URL présignée persistante.

## 9. Sécurité

- Les URLs d’adapters sont soumises à la protection SSRF existante.
- La validation distingue `storage_uri` (`s3://` en production, `local:///…`
  uniquement en développement/test) et `original_uri` (`https://` ou
  `http://` selon la source). Les schémas `file://`, les identifiants dans
  l’autorité URI et les hôtes privés non explicitement autorisés sont refusés.
- Le CRUD générique n’effectue aucun fetch à partir d’une URI de métadonnée ;
  seul un adapter autorisé peut ouvrir une connexion sortante, avec allowlist,
  timeouts, taille maximale et journalisation sans secret.
- Les credentials ne sont jamais stockés dans les métadonnées du Registry.
- Les sources non cataloguées restent bloquées par `require_ingestible`, qui
  demeure la porte juridique déclarative avant le Registry opérationnel.
- Une licence inconnue ne permet pas la promotion en production.
- Les fichiers RAW sont isolés avant validation.
- Les archives sont soumises à des limites de taille, de nombre de fichiers, de profondeur et de chemin.
- Les buckets de production sont privés et les URLs présignées sont temporaires.
- Les logs ne contiennent ni secret, ni URL présignée, ni données personnelles.

## 10. Impact

### Fichiers et composants susceptibles d’évoluer après adoption

- `GSIE/API/src/gsie_api/infrastructure/models/models_ai.py` ;
- `GSIE/API/src/gsie_api/infrastructure/models/governance.py` et
  `GSIE/API/src/gsie_api/infrastructure/models/spatial_temporal.py` pour les
  droits de dataset et la couverture `Place` ;
- `GSIE/API/src/gsie_api/infrastructure/models/prov.py` ;
- `GSIE/API/src/gsie_api/infrastructure/models/enums.py` ;
- `GSIE/API/src/gsie_api/resources/validators.py` ;
- nouveaux DTOs et service Registry dans `GSIE/API/src/gsie_api/data/` ;
- nouvelle migration Alembic pour les champs strictement nécessaires ;
- tests unitaires et intégration Registry ;
- documentation `GSIE/API/docs/data/`.

### Compatibilité

- aucune suppression de type v6.2 ;
- aucune rupture du CRUD générique ;
- aucune modification des clients GeoSylva, Ignis ou Hub ;
- les clients externes existants pourront être encapsulés progressivement ;
- les assets existants sans `storage_uri` restent lisibles grâce à la
  nullabilité introduite par `20260809_0044` ; ils ne sont pas sélectionnables
  pour une inférence tant qu’ils ne sont pas archivés ou prouvés inchangés ;
- les migrations sont additives au premier passage : les liens et attributs
  qualifiants sans preuve (`data_rights_statement_id`, couverture, preuve,
  qualité et vocabulaire) restent nuls pour l’historique, avec backfill par
  manifeste vérifié ; `DatasetVersion.status` est explicitement initialisé à
  `DISCOVERED` selon la règle ci-dessous ; aucune suppression ni renommage
  destructif de `rights_statement_id` ;
- les `DatasetVersion` existantes sont initialisées à `DISCOVERED` si leur
  statut n’est pas démontré par une preuve conservée. Les champs manquants ne
  sont rendus obligatoires qu’après qualification des nouvelles entrées ;
- les index et contraintes minimaux à prévoir sont l’unicité
  `(dataset_id, version)`, l’unicité du `slug`, les index de statut/publisher,
  les bornes temporelles et l’emprise de `Place`. Les noms exacts relèvent de
  la migration post-adoption.

### Stratégie de migration en deux temps

1. **Ajout compatible** : créer l’enum `DatasetStatus`, les colonnes et tables
   satellites nullable, `DataRightsStatement`, `DatasetHealth` et les index
   non bloquants ; enregistrer l’état de chaque backfill dans une `Revision`.
2. **Durcissement qualifié** : après audit des lignes historiques, activer les
   contraintes exigées pour `VALIDATED`, `STAGING` et `PRODUCTION`. Une ligne
   non qualifiable reste consultable en `DISCOVERED`, `UNKNOWN_LICENSE` ou
   `BROKEN` ; elle n’est jamais promue par défaut.

### Risques

| Risque | Mitigation |
|---|---|
| Trois identités Provider/Source/Agent incohérentes | Pas de `Provider` persistant ; `Agent` = identité, `Source` = origine, `Citation` = relation |
| Registry et STAC divergents | STAC généré comme projection du Registry |
| Explosion des tables de métadonnées | Ajouter uniquement les champs filtrés et historisés nécessaires |
| Résolution trop permissive | Contraintes bloquantes avant scoring |
| Licence mal interprétée | Validation humaine et porte juridique existante |
| Migration de schéma incorrecte | Alembic upgrade/downgrade sur base de test |
| Contrat prématurément public | API dédiée uniquement après validation du contrat |

## 11. Alternatives considérées

### 11.1 Créer une table Provider indépendante

**Rejetée pour cette tranche.** Elle dupliquerait `Agent`, `Source` et `ScientificSourceEntry`, avec un risque de divergence d’identité et de licence.

### 11.2 Utiliser uniquement le CRUD générique

**Rejetée comme contrat final.** Le CRUD reste une fondation interne, mais il ne fournit pas les DTOs, filtres, politiques, pagination métier et réponses explicables du Registry.

### 11.3 Utiliser STAC comme base unique

**Rejetée.** STAC décrit très bien les assets spatio-temporels, mais ne porte pas à lui seul les droits GSIE, l’Evidence Level A–F, les validations humaines, les ressources non géospatiales et les contrats des moteurs.

### 11.4 Ajouter Iceberg dès maintenant

**Reportée.** Iceberg sera évalué pour les tables analytiques volumineuses après le pilote S3 et la baseline Parquet. Il ne doit pas être imposé au noyau transactionnel.

### 11.5 Créer un microservice Registry séparé

**Reportée.** Tant que le Registry partage les resources, les droits, les révisions et la provenance de GSIE, un module interne de l’API limite la duplication opérationnelle. L’extraction en service séparé pourra être décidée sur des mesures de charge réelles.

## 12. Critères d’acceptation de la RFC

La RFC est prête pour la décision du Fondateur lorsque les points suivants
sont relus comme un contrat testable :

- un fixture `Agent`/`Source`/`Dataset`/`DatasetVersion` est résolu sans table
  `Provider`, avec citation primaire et alias juridique traçable ;
- une qualification Registry A–F est enregistrée avec sa méthode, sa date et
  sa justification ; elle reste distincte d’un `EvidenceAssessment` d’assertion
  et une version sans qualification est refusée pour `use=inference` ;
- une valeur `primary_domain` inconnue est rejetée par le vocabulaire versionné
  et la version de ce vocabulaire est retournée dans la décision ;
- une version sans licence, sans grain requis ou sans checksum requis est
  refusée avant `PRODUCTION`, avec un motif stable ;
- chaque transition valide de `DatasetStatus` est acceptée et chaque transition
  invalide est rejetée avec une `Revision` explicative ; les récupérations
  d’exception du §6.1 sont couvertes ;
- `DatasetHealth` est append-only, lié à une `Distribution`, et son dernier
  résultat ne remplace pas l’historique ;
- le contrat de recherche applique les contraintes avant le score, vérifie
  `A > … > F`, `grain_m2 <= max_grain_m2`, le CRS de l’emprise et le mode
  `display`/`inference` ;
- la migration est additive, réversible sur une base de test, n’interprète pas
  les droits RGPD comme des droits de dataset et ne promeut aucun historique
  silencieusement ;
- l’ordre canonique est Registry → qualification/adapters → resolver →
  projections (dont STAC) → applications/Data Broker. STAC ne devient jamais
  une autorité concurrente.

## 13. Proposition de séquencement après adoption

1. Versionner le vocabulaire de domaines, puis ajouter les champs strictement
   nécessaires à `Dataset`, `DatasetVersion`, `Distribution` et aux tables
   satellites, avec migration additive.
2. Ajouter les statuts et validateurs de cycle de vie.
3. Ajouter `DatasetHealth` historisé par distribution.
4. Créer le service Registry et ses DTOs, puis les endpoints
   `catalog/search/health/coverage` en lecture paginée.
5. Ajouter les adapters derrière l’interface commune et qualifier les
   premières sources.
6. Implémenter le Data Selection Engine avec décision explicable et fallback
   explicite.
7. Produire les projections STAC et les contrats de distribution.
8. Migrer progressivement les applications, sans exposer de fournisseur
   directement.

## 14. Sources et références

- `GSIE/API/docs/data/GSIE_DATA_ARCHITECTURE_AUDIT.md` — audit Phase 0 et Phase 1 ;
- `GSIE/RESEARCH/ETUDE_DATA_PLATFORM_EMERGENTE_2026-08-09.md` — étude des technologies ouvertes ;
- `GSIE/API/src/gsie_api/infrastructure/models/models_ai.py` — Dataset, DatasetVersion, DataAsset et Distribution ;
- `GSIE/API/src/gsie_api/infrastructure/models/prov.py` — Agent, Source, Activity et PROV ;
- `GSIE/API/src/gsie_api/infrastructure/models/governance.py` — RightsStatement ;
- `GSIE/API/src/gsie_api/infrastructure/models/observation.py` — QualityAssessment ;
- `GSIE/API/src/gsie_api/infrastructure/models/spatial_temporal.py` — Place et TemporalContext ;
- `GSIE/API/src/gsie_api/governance/source_registry.py` — porte juridique d’ingestion ;
- `GSIE/DATASETS/NOMENCLATURE_SOURCES.md` — régimes d’accès, licences et grain natif ;
- `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` — niveaux de preuve A à F ;
- `GSIE/ARCHITECTURE/ADR-006-object-storage.md` — MinIO/S3 et DataAsset ;
- `02_RFC/RFC-0029-organisation-physique-des-donnees.md` — organisation physique validée ;
- STAC Specification — <https://stacspec.org/> ;
- Apache Iceberg — <https://iceberg.apache.org/> ;
- NASA EarthCatalog — <https://github.com/nasa-itslive/earthcatalog>.

## 15. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-09 | Création de la proposition Data Registry. |
| 1.1.0 | 2026-08-10 | Passe de logique : statut de décision non anticipé, relation Agent/Source explicite, qualification Registry A–F, vocabulaire de domaines versionné, couverture et droits séparés, santé par distribution, transitions récupérables, recherche déterministe et migration additive. Statut RFC conservé à `Draft`. |
| 1.2.0 | 2026-08-10 | Validation formelle par le Fondateur ; RFC adoptée comme contrat de la Phase 2 Data Registry. L’implémentation reste séquencée selon le §13 et n’est pas réalisée par cette mise à jour documentaire. |
