# Audit de l’architecture des données GSIE — Phase 0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-AUDIT-0001 |
| **Statut** | Draft |
| **Version** | 1.9.0 |
| **Date** | 2026-08-10 |
| **Périmètre** | GSIE Server — `GSIE/API/` |
| **Objet** | Audit du Data Registry, des adapters et du Data Selection Engine |
| **Phase projet** | Phase 4 — Implémentation |
| **Décisions structurantes** | RFC-0029 / DEC-000039 ; DEC-000041 ; DEC-000051 |
| **Veille complémentaire** | `GSIE-DATA-RESEARCH-0001` — technologies ouvertes et émergentes |
| **Phase 2** | RFC-0038 v1.2.0 / DEC-000059 Validated — implémentation autorisée par tranches |

## 1. Résumé

GSIE Server possède déjà les fondations d’une plateforme de données : métamodèle v6.2, table racine `resource`, types `Dataset`, `DatasetVersion`, `DataAsset` et `Distribution`, provenance PROV, droits, qualité, révisions, ingestion bulk, stockage objet abstrait, clients HTTP résilients, Redis, workers et observabilité.

La tranche Phase 2 matérialise désormais le `Data Registry` comme composant unifié en lecture : modèle enrichi, cycle de vie, droits, santé par distribution, DTOs, curseurs et API `/api/v1/data/*`. La Phase 3 stabilise le contrat commun et le registre lazy des plugins, puis fournit quatre façades fournisseurs non enregistrées par défaut : GBIF, IGN, SoilGrids et Météo-France. Elles délèguent aux clients existants et n’ouvrent aucun réseau à leur construction. Le cache partagé, la validation périodique et la résolution policy-driven restent hors périmètre ; la migration des consommateurs demeure progressive.

La veille externe confirme que GSIE doit rester fondé sur des standards ouverts : **STAC, COG, GeoParquet, COPC, Zarr et Parquet**, avec DuckDB/Polars comme baseline CPU, cuDF/Dask-cuDF comme accélération optionnelle et Iceberg comme évolution différée des tables analytiques versionnées.

**Recommandation principale :** étendre le métamodèle existant et encapsuler les clients actuels derrière une couche data GSIE, sans créer de second registre ni de nouvelle architecture parallèle. STAC, Iceberg et les moteurs analytiques doivent rester des projections ou des plans de traitement, jamais des autorités concurrentes de la gouvernance GSIE.

## 2. Périmètre et méthode

L’audit a porté sur :

- la gouvernance, la mémoire projet et les décisions applicables ;
- `GSIE/API/` : modèles SQLAlchemy, migrations Alembic, CRUD générique, ingestion, clients externes, stockage, cache, workers, santé, métriques et tests ;
- les documents d’architecture et de données GSIE ;
- le catalogue `DS-001` à `DS-029` et l’inventaire élargi des sources ;
- les conventions de licence, de provenance et de niveau de preuve.

La mise à jour combine audit documentaire, lecture statique du code et vérifications ciblées des tranches Phase 2 et Phase 3. Aucun appel de fournisseur externe ni téléchargement de dataset n’a été exécuté. La migration PostgreSQL a été appliquée dans Docker jusqu’à `20260810_0046` et contrôlée par requêtes d’intégrité en lecture seule.

## 3. Architecture actuellement trouvée

### 3.1 Flux actuel

Le flux documenté est :

```text
Sources externes
      ↓
Import / clients spécifiques aux moteurs
      ↓
Evidence Engine
      ↓
Knowledge Engine / ressources v6.2
      ↓
Moteurs domaine et moteurs transverses
      ↓
API GSIE / WebSocket
      ↓
Applications clientes et Hub
```

Le principe de qualification par l’Evidence Engine et la traçabilité des connaissances sont déjà établis. La partie « registre de datasets → recherche/couverture/santé » est maintenant matérialisée par la tranche Phase 2 ; la découverte fournisseur, la sélection policy-driven et le cache/fallback restent les capacités transverses à construire.

### 3.2 Noyau de persistance réutilisable

Le métamodèle et la migration baseline contiennent déjà les types suivants :

| Capacité cible | Existant réutilisable | État constaté |
|---|---|---|
| Dataset | `DatasetModel` | Présent, slug/domaines/tags/vocabulaire versionné ajoutés en Phase 2 |
| Version de dataset | `DatasetVersionModel` | Présent, couverture temporelle, statut, hash de schéma et preuve ajoutés |
| Actif archivé | `DataAssetModel` | Présent, format, taille, checksum, URI d’origine et date d’archivage |
| Distribution | `DistributionModel` | Présent, méthode d’accès, URL, licence et `scale_context_id` |
| Fournisseur / source | `SourceModel`, `AgentModel`, `ScientificSourceEntry` | Présent sous plusieurs formes, pas encore unifié |
| Droits | `RightsStatementModel` + `DataRightsStatementModel` | RGPD séparé des droits d’usage dataset ; projection Phase 2 dans `gsie_gouvernance` |
| Qualité | `QualityAssessmentModel` | Présent par dimension et score |
| Preuve | `EvidenceAssessmentModel`, `EvidenceLevel` | Présent pour les assertions ; qualification Registry de `DatasetVersion` à expliciter |
| Provenance | `ActivityModel`, `ProvEntityModel`, `CitationModel` | Présent, lineage élémentaire possible |
| Versionnement | `RevisionModel`, `ResourceDiffModel`, CRUD générique | Présent et append-only selon CON-010 |
| Échelle/résolution | `ScaleContextModel`, `distribution.scale_context_id` | Présent depuis la migration `20260728_0008` |
| Santé | `DatasetHealthModel` | Présente par distribution, append-only attendu ; jobs périodiques encore absents |
| Validation de payload | validateurs dynamiques du CRUD | Présente et spécialisée dataset/version/santé |

Le CRUD générique `/api/v1/resources` peut donc constituer une fondation interne, sous réserve de ne pas l’exposer comme contrat final du Data Registry sans DTOs et politiques dédiés.

### 3.3 Sources et catalogue documentaire

Le dépôt possède trois niveaux actuellement distincts :

1. `GSIE/DATASETS/DATASET_CATALOG.md` : catalogue de 29 datasets `DS-*` avec producteur, résolution, licence et usages ;
2. `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md` : inventaire élargi d’environ 179 sources, majoritairement descriptif ;
3. `gsie_api.governance.source_registry` : registre déclaratif des sources évaluées juridiquement, avec `SourceLegalStatus`, `IngestionMode` et la porte `require_ingestible`.

Le troisième registre est une **porte juridique d’ingestion**, pas encore le catalogue autoritatif opérationnel demandé pour la recherche, la santé, les versions, la couverture et la sélection.

### 3.4 Clients externes existants

Les clients sont actuellement localisés dans les moteurs :

- Botanical : GBIF, TAXREF, PlantNet, Treekipedia, Wikimedia ;
- Climate : AROME, DPClim, Météo-France, Paquet Observations, SYNOP, Vigilance ;
- GIS : IGN et téléchargement Géoplateforme ;
- Pedology : SoilGrids.

Ils héritent déjà de `ResilientHttpClient` ou `ResilientCsvClient`, qui fournit retries réseau, traitement HTTP, parsing, quotas/authentification et protection SSRF. Cette résilience doit être conservée et réutilisée par les futurs adapters.

Les quatre clients ciblés disposent maintenant d’une façade `DataSourceAdapter`
non activée par défaut. Les URLs et contrats de réponse restent définis dans
les clients historiques, ce qui préserve les moteurs pendant la migration ; une
activation opérationnelle et la migration des consommateurs restent à planifier.

### 3.5 Ingestion, workers et événements

Les capacités existantes sont :

- `BulkIngestService` : lots jusqu’à 1000 resources, SAVEPOINT par élément et transaction finale ;
- `ingestion_progress` : checkpoint de reprise d’un pipeline ;
- pipeline `EvidenceKnowledgePipeline` : qualification puis ingestion conditionnelle dans Knowledge ;
- outbox et `outbox-worker` : livraison transactionnelle d’événements ;
- `ActivityType` : extraction, transformation, ingestion, validation, révision et simulation.

Il n’existe pas encore de job générique de validation périodique des datasets, de scheduler dédié ou de job de découverte/versionnement. Le suivi persisté `DatasetHealth` est désormais disponible pour ces futurs contrôles.

### 3.6 Stockage et cache

PostgreSQL/PostGIS est la source de vérité des métadonnées. L’abstraction `ObjectStorage` utilise le filesystem local en développement simple et un backend S3-compatible en staging/production. La Phase 1 implémente `S3Storage` avec `aiobotocore`, compatible MinIO et AWS S3, upload multipart par blocs, metadata SHA-256, lecture en flux, plages HTTP, HEAD, suppression et URLs présignées. Les clés sont validées contre les traversées de chemin et les erreurs externes sont ramenées à des exceptions métier sans secrets.

Le Compose de développement fournit MinIO sur les ports localhost `9000` (S3) et `9001` (console), avec volume persistant, healthcheck et job `minio-init` idempotent qui crée le bucket configuré. Les tests unitaires utilisent exclusivement un faux client asynchrone : MinIO n’est pas une précondition de la suite.

`data_asset.storage_uri` et `data_asset.checksum_algorithm` sont nullable afin de préserver les actifs historiques et sont ajoutés par la migration réversible `20260809_0044`.

Redis est déjà présent pour le rate limiting, le Pub/Sub, les WebSockets et certains contrôles de santé. Les clients de données ne disposent pas encore d’un cache partagé GSIE ; SYNOP possède notamment un cache LRU en mémoire, non partagé entre workers.

### 3.7 API et observabilité

L’API expose :

- CRUD générique des resources ;
- endpoints des moteurs ;
- santé `/health` et `/ready` ;
- métriques Prometheus protégées selon l’environnement ;
- WebSocket Hub et événements ;
- traces OpenTelemetry conditionnelles.

La tranche Phase 2 expose les projections authentifiées et paginées `/api/v1/data/catalog`, `/data/datasets/{id}`, `/data/providers`, `/data/search`, `/data/health` et `/data/coverage`. `/data/resolve` reste explicitement réservé au Data Selection Engine de la Phase 5.

## 4. Contrats et contraintes de gouvernance

### 4.1 Niveau de preuve

GSIE possède déjà une nomenclature officielle **A à F**, définie dans `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md`. Elle ne doit pas être remplacée par les niveaux conceptuels `E0` à `E5` proposés dans le prompt.

Le registre cible devra distinguer :

- le niveau de preuve scientifique de la donnée ou connaissance ;
- les scores opérationnels de fraîcheur, complétude, disponibilité et qualité ;
- la confiance de sélection d’une source pour une requête donnée.

Ces valeurs ne sont pas interchangeables et ne doivent pas être réduites à un booléen.

### 4.2 Licences et ingestion

Les règles existantes sont strictes :

- une source non cataloguée est bloquée pour l’ingestion automatique ;
- une licence non formalisée permet au mieux le recensement et l’étude, pas l’ingestion ;
- `OPEN_COPY` est le seul mode autorisant le pipeline automatique complet ;
- les droits de redistribution, d’indexation, de dérivation et d’entraînement IA doivent être séparés ;
- une donnée utilisée dans une conclusion citable doit être archivée ou prouvée inchangée par un checksum daté.

Ces règles doivent être reprises par le futur `Data Registry` et non recodées dans chaque adapter.

### 4.3 Résolution et couverture

`NOMENCLATURE_SOURCES.md` impose le grain natif en `m²` lorsqu’une source est spatiale. La résolution native doit rester distincte de la résolution du produit dérivé après rééchantillonnage.

La migration `20260728_0008` a déjà rattaché `distribution` à `scale_context` pour éviter une seconde source de vérité. Le futur registre doit donc utiliser cette relation, et non ajouter un champ concurrent comme `native_grain_m2`.

### 4.4 Organisation physique

RFC-0029, validée par DEC-000039, établit :

- une base PostgreSQL avec schémas par domaine, plutôt que des bases séparées ;
- un noyau partagé pour les resources, sources, citations, provenance, versionnement et référentiels ;
- les octets volumineux hors base, la référence et le checksum restant dans le noyau ;
- un stockage objet et un stockage fichiers spécialisés, sans transformer PostgreSQL en dépôt de rasters ou séries volumineuses.

Toute migration du registre devra respecter cette décision et vérifier l’état réel d’implémentation des schémas avant d’ajouter des tables.

## 5. Écarts par rapport à l’architecture cible

| Écart | Impact | Priorité |
|---|---|---|
| Service Data Registry dédié absent | Tranche lecture livrée ; écriture métier, adapters et resolver restent séparés | P0 — résiduel |
| Modèle `Dataset` incomplet pour la résolution | Champs de recherche et couverture ajoutés ; sélection policy-driven encore absente | P0 — résiduel |
| Projection fournisseur unifiée absente | Projection API `Agent`/`Source`/`Citation` livrée, ingestion et catalogue fournisseur complet restent à faire | P0 — résiduel |
| Pas de DatasetHealth ni historique de contrôles | Modèle et lecture santé livrés ; jobs périodiques et append-only opérationnel restent à brancher | P1 — résiduel |
| Pas de lifecycle dataset explicite | `DatasetStatus`, transitions et validation CRUD livrés | Résolu Phase 2 |
| Clients directement attachés aux moteurs | Couplage résiduel fournisseur/applicatif ; quatre façades délèguent désormais aux clients historiques | P0 — migration progressive |
| Pas d’interface `DataSourceAdapter` | Contrat commun, capacités, bornes, registre lazy et quatre façades livrés ; bootstrap/activation encore absents | Résolu Phase 3 — tranche façades |
| Pas de Data Selection Engine | Aucun choix policy-driven entre résolution, fraîcheur, qualité, coût, licence et offline | P0 |
| Pas de fallback data-level | Résilience réseau existante, mais pas de cascade fournisseur → cache → dernière version valide | P1 |
| Cache data partagé absent | Cache local non cohérent entre workers et instances | P1 |
| Validation réelle du stockage MinIO encore bloquée par le daemon Docker local | Le contrat Compose est valide, mais le smoke test réseau reste à exécuter sur Docker/Linux | P1 |
| Lineage explicite incomplet | PROV permet une base, mais pas encore les paramètres et pertes d’information d’une transformation | P1 |
| Validation périodique absente | Pas de vérification automatisée des URLs, schémas, checksums, licences ou versions | P1 |
| API `/data/*` absente | Catalogue, détail, recherche, santé et couverture sont exposés en lecture | Résolu Phase 2 |
| Documentation cible absente | Contrat Phase 2 documenté ; contrat adapters/resolver encore à écrire | P1 — résiduel |

## 6. Capacités à réutiliser

### À conserver sans duplication

- `ResourceModel` et `RESOURCE_TYPES` pour l’identité, l’organisation et le versionnement ;
- `DatasetModel`, `DatasetVersionModel`, `DataAssetModel`, `DistributionModel` ;
- `SourceModel`, `ActivityModel`, `ProvEntityModel`, `CitationModel` ;
- `RightsStatementModel` et `source_registry.require_ingestible` ;
- `QualityAssessmentModel` et `EvidenceAssessment` ;
- `ScaleContextModel` et `distribution.scale_context_id` ;
- `ResourceService`, ses validateurs et son historique `Revision` ;
- `ResilientHttpClient` / `ResilientCsvClient` et la convention `respx` ;
- `BulkIngestService` et `ingestion_progress` ;
- Redis, outbox, Prometheus, OpenTelemetry et les endpoints de santé ;
- le catalogue documentaire `DS-*` comme source d’amorçage à qualifier, pas comme base de vérité runtime.

### À ne pas réutiliser comme contrat final

- les URLs codées directement dans les moteurs ;
- les dictionnaires de métadonnées ad hoc comme seul schéma de recherche ;
- le registre juridique in-memory comme catalogue complet ;
- les endpoints métier actuels comme interface fournisseur pour les applications ;
- le cache LRU local comme cache distribué ;
- le stockage local comme fallback de production.

## 7. Architecture cible incrémentale recommandée

```text
Catalogues de découverte
        │
        ▼
Discovery Service
        │  métadonnées candidates, sans confiance implicite
        ▼
GSIE Data Registry
        ├── Dataset / fournisseur (projection Agent/Source) / DatasetVersion
        ├── Distribution / AccessMethod / Coverage
        ├── Rights / Licence / Evidence
        ├── Quality / Health / Lifecycle
        ├── Provenance / Lineage
        └── ML usage rights
        │
        ▼
DataSourceAdapter (contrat commun)
        ├── IGN / Géoplateforme
        ├── SoilGrids
        ├── GBIF / TAXREF
        └── Météo-France / SYNOP ou AROME
        │
        ▼
Validation → Ingestion → Normalisation
        │
        ├── raw
        ├── normalized
        └── derived
        │
        ▼
PostgreSQL/PostGIS + Object Storage + Redis
        │
        ▼
Data Selection Engine policy-driven
        │
        ▼
GSIE Data API
        │
        ├── GeoSylva
        ├── Ignis
        ├── Hydro
        ├── Terra
        ├── Flora
        ├── Aeris
        ├── Artemis
        ├── Atlas
        └── Hub Unreal
```

Le `Data Selection Engine` doit retourner une décision explicable : candidats évalués, critères appliqués, source retenue, éventuel fallback, fraîcheur, résolution native et chaîne de provenance. Il ne doit pas modifier silencieusement les niveaux de preuve ni masquer l’obsolescence d’une donnée.

## 8. Points de pilotage avant le code

1. **Adoption du contrat** : `RFC-0038` v1.2.0 et `DEC-000059` sont `Validated` par le Fondateur le 2026-08-10. L’implémentation est autorisée, mais reste séquencée et n’est pas implicite.
2. **Modèle fournisseur adopté** : projection `Agent`/`Source` reliée par `Citation`, sans type ou table `Provider` persistant.
3. **Statuts dataset adoptés** : `DatasetStatus`/`dataset_status`, distinct de `LifecycleStatus`, avec transitions et récupérations explicites.
4. **Résolution de requête adoptée** : contraintes bloquantes de couverture, licence, qualification Registry A–F, fraîcheur, offline, qualité et usage `display`/`inference`, avec vocabulaire de domaines versionné.
5. **Exécution des validations** : confirmer si le worker outbox existant porte les contrôles périodiques ou si une capacité de job séparée est nécessaire.
6. **Stockage de production** : backend S3-compatible implémenté en Phase 1 ; exécuter le smoke test MinIO sur un daemon Docker/Linux avant l’ingestion volumineuse.
7. **Évolution des clients** : les façades IGN, SoilGrids, GBIF et Météo-France délèguent d’abord aux clients existants ; préparer ensuite un bootstrap contrôlé et une migration par moteur.
8. **Limite Phase 2** : l’API Registry est en lecture seule ; aucun resolver, téléchargement, URL présignée persistante ou accès fournisseur ne doit être ajouté à cette tranche.

## 9. Plan d’implémentation séquencé

### Phase 0 — Audit

- Livrable : ce document, enrichi par `GSIE-DATA-RESEARCH-0001`.
- Audit documentaire terminé.

### Phase 1 — Object Storage

- `S3Storage` asynchrone MinIO/S3 avec `aiobotocore` ;
- upload multipart par blocs et checksum SHA-256 ;
- lecture en flux, lecture par plage, HEAD, suppression et URL présignée ;
- `DataAsset.storage_uri` et `checksum_algorithm` ;
- migration réversible `20260809_0044` ;
- `DataAsset` validé par le CRUD générique : taille non négative, `BIGINT`,
  checksum cohérent avec l’algorithme déclaré, URI limitées à `local://`,
  `s3://`, `http://` et `https://` selon le champ, sans identifiants ;
- migration `20260810_0045` : `size_bytes` passe en `BIGINT` et reçoit la
  contrainte SQL `ck_data_asset_size_non_negative` ;
- le backend local renvoie un identifiant opaque `local:///…` et refuse les
  URLs présignées ; aucun chemin du serveur ne devient une donnée d’API ;
- MinIO Compose et configuration sécurisée ;
- la suite unitaire complète passe (2 703 tests, 63 ignorés, 100 % de
  couverture) ; deux scénarios d’intégration DataAsset sont ajoutés et
  attendent l’environnement Docker/PostgreSQL.

Reste : smoke test réel lorsque Docker Desktop/Linux sera disponible.

### Phase 2 — Registry et contrat

- modèle enrichi et migration réversible `20260810_0046` : slug, domaines,
  tags, couverture temporelle, statut, preuve, droits d’usage, santé par
  distribution et contraintes d’intégrité ;
- cycle de vie `DatasetStatus` explicite avec transitions et récupérations
  contrôlées ;
- DTOs Pydantic stricts et vocabulaire de domaines versionné ;
- `DataRegistryService` read-only et routes authentifiées, rate-limités,
  cursor-paginées : catalogue, détail, providers, recherche, santé et
  couverture ;
- projection fournisseur `Agent`/`Source`/`Citation` avec masquage RBAC des
  agents et URLs externes réduites à des références HTTP publiques sûres ;
- validation dataset/version/santé intégrée au CRUD historique, sans modifier
  les contrats consommateurs existants ;
- tests ciblés : 39 scénarios Phase 2 passants ; Ruff et mypy stricts passants.

Reste : appliquer la migration et exécuter le smoke test PostgreSQL lorsque
Docker/Linux sera disponible ; les adapters, jobs de santé et resolver sont
reportés aux phases suivantes.

### Phase 3 — Adapters

- interface `DataSourceAdapter`, descripteurs de capacités, contexte borné et
  flux de fetch ;
- factory/registre lazy de plugins avec allowlist d’hôtes et erreurs stables ;
- tests de contrat sans accès réseau ;
- façades de référence IGN, SoilGrids, GBIF et Météo-France, non enregistrées par défaut ;
- délégation temporaire aux clients résilients existants.

Tranche façades livrée le 2026-08-10 : `GBIFAdapter`, `IGNAdapter`,
`SoilGridsAdapter` et `MeteoFranceAdapter` sont disponibles comme façades non
enregistrées par défaut, avec mode offline, health contrôlé, allowlists
explicites et requêtes déléguées aux clients résilients existants. Les tests
utilisent des ports simulés et n’ouvrent aucun réseau. Le bootstrap, les jobs
de santé et le resolver restent à réaliser.

### Phase 4 — Validation et ingestion

- health check sans téléchargement massif ;
- metadata/schema/license/freshness/checksum ;
- états staging et production soumis à validation humaine ;
- provenance PROV complète des transformations.

### Phase 5 — Resolver et sélection

- resolver pur et policy-driven ;
- fallback explicite fournisseur → cache → dernière version valide ;
- enrichissement de l’API read-only Phase 2 par les décisions de sélection,
  les critères et les fallbacks ;
- observabilité des requêtes, adapters, cache et validations.

### Phase 6 — Migration des consommateurs

- migration progressive des moteurs vers la façade data ;
- aucun accès fournisseur ajouté aux applications clientes ;
- contrats de compatibilité vérifiés pour GeoSylva, Ignis et Hub.

### Phase 7 — Accélération et formats cloud-native

- STAC, COG, GeoParquet, COPC et Zarr ;
- baseline DuckDB/Polars/PyArrow ;
- cuDF/Dask-cuDF/cuSpatial après benchmark ;
- Iceberg, DataFusion, cuFile et cuObject uniquement après mesure.

## 10. Risques prioritaires

| Risque | Conséquence | Mesure immédiate |
|---|---|---|
| Ajouter un registre parallèle | Deux vérités divergentes | Étendre `resource`/Dataset et relier le registre juridique |
| Assimiler preuve, qualité et fraîcheur | Sélections scientifiquement trompeuses | Conserver des axes distincts et explicables |
| Exposer un dataset sans licence vérifiée | Risque juridique et blocage de redistribution | Réutiliser la porte `require_ingestible` et les droits explicites |
| Sélectionner une source hors couverture | Conclusion fausse mais techniquement valide | Contrat de couverture obligatoire et refus par défaut |
| Rééchantillonner en surestimant la précision | Fausse résolution scientifique | Préserver le grain natif et tracer les transformations |
| Ajouter un adapter sans SSRF/limites | SSRF, fichiers piégés, OOM ou zip bomb | Réutiliser le client résilient et ajouter des limites de fetch |
| Promettre une disponibilité S3 sans smoke test réel | Écart possible entre tests simulés et réseau MinIO/S3 | Exécuter le smoke test sur Docker/Linux avant l’ingestion volumineuse |
| Migrer trop vite les moteurs | Régression des contrats existants | Adapters façades et migration par moteur |
| Ajouter une migration sans décision | Rupture de hiérarchie documentaire | RFC/DEC avant modification structurante du schéma |

## 11. Vérifications réalisées

- Lecture des règles racine et API GSIE ;
- lecture de `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md` ;
- lecture des README GSIE, API, DATASETS et ARCHITECTURE ;
- lecture des contrats `SCIENTIFIC_DATA_MODEL`, `GSIE_DATA_FLOW`, `NOMENCLATURE_SOURCES`, `EVIDENCE_FRAMEWORK` ;
- lecture de RFC-0013, RFC-0029, DEC-000038 et DEC-000051 ;
- recherche des modèles, migrations, routes, clients, workers, caches, stockage et métriques ;
- vérification de l’état Git avant modification : des changements préexistants dans `GSIE/API/pyproject.toml`, `GSIE/API/uv.lock` et `GSIE/API/tests/perf/results/` n’ont pas été touchés.
- vérification Phase 2 : 39 tests ciblés passants sans couverture globale, Ruff
  sur les fichiers modifiés et mypy strict sur 12 modules ;
- vérification Phase 3 : 9 tests du contrat d’adapters et 20 tests des quatre
  façades passants, avec Ruff et mypy strict ;
- vérification des façades GBIF, IGN, SoilGrids et Météo-France avec clients
  simulés, sans appel externe ;
- contrôle de la migration `20260810_0046` et de la cohérence de la clé
  composite santé → distribution → version.

Les tests de la Phase 1 couvrent le stockage local, le faux client S3, le multipart, le checksum, l’abandon d’upload, les plages, le path traversal et la validation de configuration. Les validations suivantes devront respecter les commandes de `GSIE/API/AGENTS.md` : ruff, mypy, tests complets, couverture et harnais de mutation.

## 12. Conclusion

La Phase 1 a rendu disponible le socle de stockage objet MinIO/S3, sans modifier les applications clientes ni introduire de fallback local en staging/production.

La tranche Phase 2 a livré le socle du Data Registry : projection du fournisseur
par `Agent`/`Source`/`Citation`, statut `DatasetStatus`, relation entre `Source`,
`Dataset`, `DatasetVersion` et `Distribution`, droits d’usage, santé par
 distribution, couverture, recherche et API read-only. Ces points suivent
 `RFC-0038` v1.2.0 et `DEC-000059`, désormais `Validated`. La Phase 3 fournit
 maintenant les quatre façades fournisseurs, mais leur bootstrap, la
 qualification périodique, le resolver et la migration des consommateurs restent
 à réaliser ; aucun accès fournisseur ne doit encore être exposé directement
 aux applications.

La veille externe complète ce plan : STAC doit servir de projection géospatiale, COG/GeoParquet/COPC/Zarr de formats de service, DuckDB/Polars de baseline CPU, cuDF/Dask-cuDF de backend GPU optionnel et Iceberg de piste différée pour les tables analytiques à snapshots. Cette combinaison est préférable à l’adoption immédiate d’une plateforme monolithique ou d’un fournisseur unique.

## 13. Sources et références

- `CLAUDE.md`, `AGENTS.md` et `GSIE/API/AGENTS.md` — gouvernance et règles d’exécution ;
- `GSIE/API/README.md` — stack, métamodèle, endpoints et contrat de migration ;
- `GSIE/API/src/gsie_api/infrastructure/models/models_ai.py` — Dataset, DatasetVersion, DataAsset et Distribution ;
- `GSIE/API/src/gsie_api/infrastructure/models/prov.py` — provenance PROV ;
- `GSIE/API/src/gsie_api/infrastructure/models/governance.py` — droits et qualité ;
- `GSIE/API/src/gsie_api/data/` — contrats, cycle de vie, DTOs, service et routes du Registry Phase 2 ;
- `GSIE/API/src/gsie_api/data/adapters.py` — contrat commun et registre de plugins Phase 3 ;
- `GSIE/API/src/gsie_api/data/gbif_adapter.py` — façade GBIF non activée par défaut ;
- `GSIE/API/docs/data/GSIE_DATA_ADAPTER_CONTRACT_PHASE3.md` — documentation de la tranche adapter ;
- `GSIE/API/alembic/versions/20260810_0046_data_registry_phase2.py` — migration du Registry Phase 2 ;
- `GSIE/API/src/gsie_api/governance/source_registry.py` — registre juridique déclaratif ;
- `GSIE/API/src/gsie_api/shared/http_client.py` — résilience HTTP et protection SSRF ;
- `GSIE/API/src/gsie_api/ingestion/bulk.py` et `infrastructure/models/enrichment.py` — ingestion et checkpoints ;
- `GSIE/API/src/gsie_api/infrastructure/object_storage.py` — abstraction de stockage objet ;
- `GSIE/DATASETS/DATASET_CATALOG.md` et `SOURCES_DONNEES_EXHAUSTIVES.md` — catalogues documentaires ;
- `GSIE/DATASETS/NOMENCLATURE_SOURCES.md` — licence, grain et régimes d’accès ;
- `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` — niveaux de preuve A à F ;
- `GSIE/ARCHITECTURE/GSIE_DATA_FLOW.md` et `SCIENTIFIC_DATA_MODEL.md` — flux et modèle scientifique ;
- `02_RFC/RFC-0013-ingestion-donnees-onf-cnpf.md` — ingestion forestière proposée ;
- `02_RFC/RFC-0029-organisation-physique-des-donnees.md` — organisation physique validée ;
- `03_DECISIONS/DEC-000038.md` et `DEC-000051.md` — domaine de validité et gouvernance du développement ;
- `02_RFC/RFC-0038-data-registry-gsie.md` et `03_DECISIONS/DEC-000059.md` — contrat du Registry adopté (`Validated`) ;
- `GSIE/RESEARCH/ETUDE_DATA_PLATFORM_EMERGENTE_2026-08-09.md` — veille externe ciblée et plan final proposé.

## 14. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-09 | Création de l’audit Phase 0 en lecture seule. |
| 1.1.0 | 2026-08-09 | Intégration de la veille externe et des choix de plateforme ouverts. |
| 1.2.0 | 2026-08-09 | État post-Phase 1 : Object Storage MinIO/S3 implémenté et tests synchronisés. |
| 1.3.0 | 2026-08-10 | Validation DataAsset renforcée, taille BIGINT/contrainte SQL et URI locales opaques. |
| 1.4.0 | 2026-08-10 | Relecture logique de RFC-0038 : fournisseur projeté Agent/Source/Citation, qualification Registry A–F, droits/couverture, statut et santé clarifiés ; adoption Fondateur toujours requise. |
| 1.5.0 | 2026-08-10 | Adoption formelle de RFC-0038/DEC-000059 par le Fondateur ; Phase 2 autorisée par tranches, sans implémentation réalisée dans cette mise à jour. |
| 1.6.0 | 2026-08-10 | Implémentation de la tranche Phase 2 : modèles/migration, cycle de vie, validateurs, service et API read-only ; 39 tests ciblés passants. |
| 1.7.0 | 2026-08-10 | Vérification Docker de la migration jusqu’à `20260810_0046` et livraison du contrat/registre lazy des adapters Phase 3 ; 9 tests de contrat passants. |
| 1.8.0 | 2026-08-10 | Première façade GBIF non activée par défaut, tests simulés et vérification sans réseau externe. |
| 1.9.0 | 2026-08-10 | Façades IGN, SoilGrids et Météo-France ajoutées ; 29 tests contrat/façades, Ruff et mypy strict passants, sans accès fournisseur. |
