# Migration des identités Registry I0 — 2026-08-13

| Champ | Valeur |
|---|---|
| **Statut** | Préparée — non exécutée |
| **Décision** | DEC-000068 |
| **Base active** | Inchangée |
| **FETCH** | Fermé |

## 1. Correspondances

| Identité historique | Successeurs canoniques | Migration automatique |
|---|---|---|
| `gbif` | `gbif-species-api`, `gbif-occurrence-datasets` | Non |
| `soilgrids` | `soilgrids-wcs`, `soilgrids-rest-beta` | Non |
| `ign-apicarto-geopf` | Cadastre, limites administratives, WFS | Non |
| `meteofrance-portail-api` | Météo des forêts, SAFRAN, ARPEGE/AROME, observations | Non |

Chaque ligne est une scission un-vers-plusieurs. La seule présence d'un ancien
identifiant ne permet donc pas de déterminer la cible sans lire le dataset, sa
distribution et l'adapter réellement utilisé.

## 2. Comportement implémenté

`source_reconciliation.py` fournit deux opérations pures :

- inventorier les références historiques d'un manifeste ;
- refuser un manifeste contenant encore une identité agrégée.

Le manifeste actif remonte volontairement quatre références historiques. Le
manifeste I0 candidat n'en remonte aucune. Aucun code ne met à jour la base.

## 3. Séquence d'exécution future

```text
sauvegarde et restauration prouvée
    ↓
lecture des quatre chaînes persistées
    ↓
plan de correspondance explicite par slug/version/distribution
    ↓
dry-run avec diff de ressources
    ↓
validation opérateur
    ↓
transaction PostgreSQL
    ↓
contrôles d'identité et d'intégrité
    ↓
rejeu idempotent
```

Une migration ne doit pas modifier un `DataAsset` existant ni transformer une
distribution `metadata_only` en `archive_copy`. Les alias historiques restent
conservés comme preuve de provenance.

## 4. État des quatre chaînes

- `gbif-occurrences` doit être requalifié : le code actuel consomme Species
  API, mais son nom historique prétend représenter des occurrences.
- `soilgrids-properties` doit pointer vers `soilgrids-wcs`; l'ancien REST reste
  une distribution distincte et interdite.
- `ign-apicarto` doit être ventilé selon le module/couche réellement utilisé.
- `meteofrance-services` ne peut pas être ventilé sans identifier le produit ;
  l'adapter actuel Météo des forêts ne prouve pas SAFRAN ou AROME.

## 5. Critères avant exécution PostgreSQL

- sauvegarde/restauration rejouée sur le head courant ;
- inventaire SQL en lecture seule des 32 ressources historiques ;
- mapping complet sans cible ambiguë ;
- tests upgrade/downgrade si une migration Alembic est nécessaire ;
- `dry-run` sans changement de statut ni d'actif ;
- autorisation opérateur explicite.

## 7. Résultat de l'audit SQL

L'audit réel du 13 août 2026 a trouvé 36 ressources actives (4 groupes de 9),
quatre datasets `discovered`, quatre snapshots `healthy` et un seul
`DataAsset` RAW. La différence avec l'ancien compteur de 32 vient des quatre
agents persistés.

Le DataAsset SoilGrids de 569 octets est rattaché à la version historique
`soilgrids-properties`. Il sera conservé avec son alias, son checksum, son URI
MinIO et DEC-000061 ; aucune migration automatique de slug n'est autorisée.

Le mapping GBIF, IGN et Météo-France reste ambigu et nécessite la lecture des
adapters et des traces d'utilisation avant tout `dry-run` de mutation.

La comparaison statique du 13 août 2026 confirme toutefois deux sous-cibles :
`GBIFAdapter` consomme la Species API et `MeteoFranceAdapter` consomme Météo
des forêts. Cette preuve ne résout pas les occurrences GBIF, les modules IGN
ni le rattachement du micro-extrait WCS SoilGrids ; les traces et le contenu
persisté restent obligatoires.

La lecture des versions historiques montre que `stats` est nul et que les
métadonnées ne conservent que `operation=metadata_only`. Aucun appel, couche,
propriété ou jeu d'occurrences n'est donc reconstructible depuis PostgreSQL.
Le `dry-run` devra produire une sortie `UNRESOLVED` pour toute cible qui ne
dispose pas d'une preuve externe qualifiée.

## 8. Exécution du dry-run d'identité

Le script `GSIE/API/scripts/dry_run_registry_identity_migration.py` (DEC-000069) a été
exécuté le 13 août 2026 avec le manifeste actif et le manifeste candidat. Le
rapport reproductible est
`GSIE/DATASETS/DRY_RUN_RECONCILIATION_I0_2026-08-13.json`.

Résultat :

- `gbif-occurrences` : `UNRESOLVED` ;
- `ign-apicarto` : `UNRESOLVED` ;
- `meteofrance-services` : `UNRESOLVED` ;
- `soilgrids-properties` : `PRESERVE_LINEAGE`, sans déplacement du DataAsset ;
- deux propositions futures limitées aux opérations effectivement codées :
  GBIF Species API et Météo des forêts.

Le rapport confirme `writes=0`, `fetch_enabled=false` et
`promotion_allowed=false`. Il ne constitue pas une autorisation de migration.

## 9. Validation locale de la préparation

```text
Tests SCI-001 / manifeste / réconciliation / FETCH   51 passed
Ruff                                                  All checks passed
mypy --strict                                         aucune erreur
Base PostgreSQL                                       non modifiée
Manifeste candidat                                    non appliqué
FETCH                                                  fermé
```
