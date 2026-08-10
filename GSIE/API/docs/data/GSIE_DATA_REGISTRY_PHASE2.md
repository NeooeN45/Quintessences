# DATA REGISTRY GSIE — PHASE 2 [GSIE-DATA-REGISTRY-PHASE2-0001] [1.0.0]

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-REGISTRY-PHASE2-0001 |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Date** | 2026-08-10 |
| **Auteur** | Codex — sous contrôle du Fondateur |
| **Décision** | RFC-0038 v1.2.0 / DEC-000059 — Validated |

## 1. Résumé

La Phase 2 livre le socle read-only du Data Registry GSIE : modèle enrichi,
cycle de vie, droits d’usage, santé par distribution, recherche, couverture et
API authentifiée. Cette tranche ne télécharge aucune donnée et ne sélectionne
aucun fournisseur ; les adapters, les jobs périodiques et le resolver restent
des livrables ultérieurs.

## 2. Contexte

Le registre s’appuie sur le métamodèle `resource` existant et conserve les
types `Dataset`, `DatasetVersion`, `Distribution`, `Source`, `Agent` et
`Citation`. La migration `20260810_0046_data_registry_phase2` est additive et
réversible. Les droits d’usage (`DataRightsStatement`) sont séparés des
droits RGPD (`RightsStatement`) conformément à RFC-0038.

## 3. Contenu principal

### 3.1 Données et cycle de vie

`DatasetModel` porte un `slug` unique, un domaine principal, des domaines et
tags contrôlés ainsi que la version du vocabulaire. `DatasetVersionModel`
porte les couvertures temporelles, le hash de schéma, le niveau de preuve et
les éléments de justification. `DistributionModel` référence les droits,
la couverture géographique, le format et le CRS.

Les transitions de `DatasetStatus` sont contrôlées par une table blanche :

```text
DISCOVERED → LINK_CHECKED → METADATA_EXTRACTED → LICENSE_ANALYZED
             → COVERAGE_ANALYZED → SCHEMA_ANALYZED → SECURITY_CHECKED
             → VALIDATED → STAGING → PRODUCTION
```

Les branches `BROKEN`, `UNKNOWN_LICENSE`, `LICENSE_RESTRICTED`,
`EXPERIMENTAL`, `DEPRECATED`, `UNAVAILABLE` et `ARCHIVED` sont explicites.
Les états `BROKEN` et `ARCHIVED` sont terminaux. Une modification de statut
passant par le CRUD historique est refusée si elle ne figure pas dans la table
blanche.

### 3.2 Santé et intégrité

`DatasetHealthModel` est rattaché à une version et à une distribution. La clé
étrangère composite interdit d’enregistrer une santé pour une distribution
appartenant à une autre version. Les contrôles de latence et de statut HTTP
sont bornés côté validation et côté SQL. Les lignes de santé sont destinées à
être append-only ; le scheduler de contrôle périodique sera ajouté avec les
adapters.

### 3.3 API Phase 2

Toutes les routes exigent une authentification, la permission de lecture des
datasets, le rate limiting et le contexte de trace existant. Les listes sont
cursor-paginées avec un curseur opaque lié à l’empreinte des filtres.

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/api/v1/data/catalog` | Catalogue filtrable par statut, domaine et éditeur |
| `GET` | `/api/v1/data/datasets/{dataset_id}` | Détail, versions, distributions et droits |
| `GET` | `/api/v1/data/providers` | Projection `Agent`/`Source`/`Citation` |
| `GET` | `/api/v1/data/search` | Recherche par domaine, dates, emprise, grain et preuve |
| `GET` | `/api/v1/data/health` | Derniers contrôles de santé persistés |
| `GET` | `/api/v1/data/coverage` | Projection des couvertures géographiques |

Les URLs de distribution ne sont exposées que si elles sont HTTP(S), sans
identifiants, requête ou fragment. Les chemins locaux, URI S3 et URLs
présignées sont masqués dans cette API. Aucun resolver `/data/resolve` n’est
implémenté en Phase 2.

### 3.4 Recherche et règles bloquantes

La recherche retourne des candidats et leurs motifs de blocage ; elle ne
retourne pas une décision d’ingestion ou de téléchargement. Sont signalés au
minimum : licence absente ou non compatible avec l’usage commercial, niveau
de qualité insuffisant et absence d’actif archivé pour une utilisation
d’inférence. Le niveau de preuve A–F reste distinct des scores de qualité, de
fraîcheur et de disponibilité.

### 3.5 Vérification

La tranche est couverte par 39 tests unitaires ciblés sur les contrats,
modèles, validateurs, service et routes. Ruff et mypy strict passent sur les
modules modifiés. Le smoke test de migration PostgreSQL reste à exécuter dans
un environnement Docker/Linux avec PostGIS disponible.

## 4. Sources et références

- `02_RFC/RFC-0038-data-registry-gsie.md` — contrat adopté du Data Registry ;
- `03_DECISIONS/DEC-000059.md` — décision d’adoption ;
- `GSIE/API/docs/data/GSIE_DATA_ARCHITECTURE_AUDIT.md` — audit et séquencement ;
- `GSIE/API/src/gsie_api/data/` — contrats, DTOs, cycle de vie, service et routes ;
- `GSIE/API/src/gsie_api/infrastructure/models/` — modèles SQLAlchemy ;
- `GSIE/API/alembic/versions/20260810_0046_data_registry_phase2.py` — migration ;
- `GSIE/API/tests/unit/test_data_registry_*.py` — tests de la tranche.

## 5. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-10 | Création de la documentation de la tranche Phase 2. |
