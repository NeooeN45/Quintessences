# Pipeline Data Registry — SoilGrids RAW vers SILVER v0.1

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-PIPELINE-SOILGRIDS-001 |
| **Statut** | Draft |
| **Version** | 0.1.0 |
| **Date** | 2026-08-12 |
| **Source** | SoilGrids WCS 2.0.1 |
| **Portée** | Micro-extrait déjà autorisé par DEC-000061 |

## Objectif

Fournir le premier contrat de transformation d'une source externe existante
vers le registre GSIE. Cette tranche normalise les métadonnées d'un GeoTIFF
RAW ; elle ne lit pas les pixels et ne déduit aucune unité scientifique.

## Chaîne

```text
DataAsset RAW vérifié
  -> checksum SHA-256 et taille bornée
  -> normalisation du code métier / code WCS
  -> CRS EPSG:152160 et format GEOTIFF_INT16
  -> URI MinIO conservée
  -> drapeaux de qualité
  -> décision de promotion vers STAGING
```

## Invariants

- `wv003` reste le code métier ; `wv0033` reste uniquement le code d'accès WCS.
- Les propriétés, profondeurs, quantiles et emprises viennent de l'allowlist
  `soilgrids_wcs_policy.py`.
- Un checksum SHA-256, une URI `s3://` et une taille positive sont obligatoires.
- La taille Silver ne dépasse pas 8 MiB dans cette première tranche.
- Les unités restent `null` avec le drapeau
  `UNIT_PENDING_PROPERTY_QUALIFICATION` ; elles ne sont jamais inventées à
  partir du nom de fichier ou du type GeoTIFF.
- Le résultat est marqué `NOT_GOLD` et ne peut pas alimenter une inférence.

## Garde de promotion

La fonction `evaluate_promotion` exige : source validée, asset RAW présent,
checksum vérifié, schéma normalisé, droits qualifiés, QualityAssessment
complet et décision opérateur. `production` exige en plus une source déjà en
`staging`. La fonction est pure : elle ne modifie pas PostgreSQL.

Le dépôt `SilverPromotionEvidenceRepository` charge désormais la version,
l'asset RAW, les droits et le dernier run QualityAssessment cohérent. Le
service `SilverPromotionService` écrit ensuite la transition
`validated → staging` après réception d'un snapshot de preuves vérifiées,
conserve la décision dans `DatasetVersion.stats` et refuse toute écriture
partielle avant `flush`. Le commit reste sous la responsabilité de la session
API ; aucun endpoint public n'est ouvert par cette fiche.

## Limites scientifiques

Le passage Silver ne certifie ni les unités de chaque propriété SoilGrids, ni
la qualité pédologique, ni l'aptitude à une recommandation forestière. La
qualification des unités, de la profondeur et de l'emprise doit précéder toute
promotion Gold ou utilisation par un moteur.
