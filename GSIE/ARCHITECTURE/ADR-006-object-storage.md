# ADR-006 — Object storage : interface MinIO/S3 pour DataAsset

| Champ | Valeur |
|---|---|
| **ID** | ADR-006 |
| **Statut** | Accepté |
| **Date** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000022, RFC-0011 |

## Contexte

Le métamodèle v6.1 introduit le type `DataAsset` (type 35) pour
représenter les actifs physiques archivés localement (rasters, LAZ,
NetCDF, GeoTIFF, Parquet). Ces fichiers peuvent être volumineux
(gigaoctets à téraoctets) et ne doivent pas être stockés dans
PostgreSQL (bytea). Un object storage est nécessaire.

L'arbitrage Fondateur (principe d'indépendance API) exige que les
données soient archivées localement avec traçabilité de l'origine
(`DataAsset.archived_from` + `checksum` + `original_uri`).

## Options envisagées

1. **Système de fichiers local** — stocker les fichiers sur disque
   (chemin dans `DataAsset.url`). Avantage : simple, pas de service.
   Inconvénient : pas de redondance, pas de gestion de versions, pas
   d'API standard, scaling difficile.

2. **MinIO (dev) / S3 (prod)** — object storage compatible S3.
   Avantage : API standard (put/get/delete), redondance, versioning,
   MinIO en local pour le dev, S3 en prod. Inconvénient : service
   supplémentaire.

3. **PostgreSQL Large Objects (lo_*)** — stocker dans PG via
   `lo_import`/`lo_export`. Avantage : un seul service. Inconvénient :
   pas conçu pour gros volumes, performances dégradées, pas d'API
   standard.

## Décision

**Option 2 : MinIO (dev) / S3 (prod), interface standard put/get/delete.**

### Interface

```python
class ObjectStorage(Protocol):
    def put(self, key: str, data: bytes, metadata: dict[str, str]) -> str:
        """Stocke un objet, retourne son URI."""
        ...

    def get(self, key: str) -> bytes:
        """Récupère un objet."""
        ...

    def delete(self, key: str) -> None:
        """Supprime un objet."""
        ...

    def get_metadata(self, key: str) -> dict[str, str]:
        """Récupère les métadonnées d'un objet."""
        ...
```

### Intégration avec DataAsset

```sql
CREATE TABLE data_asset (
    id                   UUID PRIMARY KEY REFERENCES resource(id),
    dataset_version_id   UUID REFERENCES resource(id),
    format               VARCHAR(32) NOT NULL,
    size_bytes           BIGINT NOT NULL,
    checksum             VARCHAR(128) NOT NULL,
    archived_from        UUID REFERENCES resource(id),  -- → Source
    original_uri         TEXT,
    archived_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    storage_uri          TEXT NOT NULL  -- ex. "s3://gsie-dataassets/abc123.nc"
);
```

Le `storage_uri` pointe vers l'object storage. Le `checksum` garantit
l'intégrité. Le `archived_from` + `original_uri` garantissent la
traçabilité de l'origine (indépendance API).

### Configuration

- **Dev** : MinIO en conteneur Docker (port 9000), bucket `gsie-dataassets`
- **Prod** : S3 (ou compatible), bucket `gsie-dataassets-prod`
- **Accès** : via variables d'environnement (`S3_ENDPOINT`,
  `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`)

## Conséquences

- **Positives** : API standard S3, redondance, versioning, scaling
  horizontal, MinIO gratuit pour le dev.
- **Négatives** : service supplémentaire (MinIO en dev). Implémentation
  différée — pas de DataAsset volumineux en Vague 1 (fixtures seulement).
- **Implémentation différée** : spécifiée en Vague 0, implémentée en
  Vague 2+ lorsque l'ingestion de datasets réels (DRIAS, SoilGrids,
  Sentinel) nécessite un stockage objet.

## Statut de suivi

- 2026-07-15 : Proposé (RFC-0011 / DEC-000022)
- Vague 0 : spécification interface `ObjectStorage`
- Vague 2+ : implémentation MinIO + intégration DataAsset

## Validation (2026-07-17)

ADR-006 accepté par le Fondateur, conformément à DEC-000022 (§ « Adopte
les 6 ADR-001 à ADR-006 »), déjà Validated depuis le 2026-07-16.
L'implémentation MinIO reste différée à Vague 2+ (inchangé).
