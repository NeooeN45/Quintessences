# QualityAssessment et préparation FETCH — 2026-08-10

## Résultat

La qualité technique devient une preuve persistée, versionnée et distincte de
la santé fournisseur comme de l'Evidence Level A–F. La politique
`registry-quality-1` exige cinq dimensions. Un run incomplet conserve ses
mesures, mais son score global reste `null`.

La migration `20260810_0048` ajoute l'identifiant de campagne, la version de
politique, le poids, les détails et le caractère automatisé. Elle borne score
et poids en base, interdit les doublons dimensionnels au sein d'un run et
préserve les lignes historiques sous la politique `legacy`.

Le resolver et le filtre `minimum_quality_score` utilisent désormais
uniquement le dernier run complet persisté. Les champs libres contenus dans
`DatasetVersion.stats` ne sont plus une preuve de qualité exploitable.
Le fallback historique `quality_score_from_stats` a été supprimé du resolver
pur ; un test injecte volontairement `stats.quality_score=0.99` et vérifie que
le candidat reste bloqué avec `QUALITY_MISSING` sans métadonnée persistée.

## Évaluation des quatre sources

L'évaluation locale reproductible du manifeste donne le même état pour GBIF,
IGN API Carto, SoilGrids et Météo-France :

- complétude déclarative : `1.0` ;
- cohérence logique du mode `metadata_only/discovered` : `1.0` ;
- exactitudes positionnelle, temporelle et thématique : non mesurées ;
- bilan complet : non ;
- score global : `null` ;
- promotion autorisée : non.

Commande :

```powershell
python scripts/assess_registry_manifest_quality.py ../DATASETS/REGISTRY_MANIFEST.json
```

## Porte FETCH

`BoundedFetchWorker` consulte le registre de qualification avant l'adapter,
le réseau ou le stockage. Il exige ensuite la capacité `FETCH`, l'allowlist et
les limites de taille de la décision et du contexte. Les quatre décisions
canoniques restent fermées ; un test prouve que l'adapter n'est jamais appelé.

Dans l'état initial de cette tranche, la copie RAW, son checksum et la
promotion n'étaient pas exécutés : il s'agissait d'un blocage de gouvernance
volontaire. La qualification SoilGrids puis DEC-000061 ont depuis autorisé un
unique micro-extrait. Le streaming borné, SHA-256, MinIO et un DataAsset RAW
ont été prouvés ; aucune promotion ou ouverture canonique n'en découle.

Le streaming borné et SHA-256 restent derrière la porte fermée, via une
destination transactionnelle `write/commit/abort`. Avant DEC-000061, la
liaison MinIO et la création du DataAsset RAW étaient volontairement absentes.
Depuis cette décision consommée, un seul actif a été créé et le registre FETCH
canonique demeure fermé.

## Validation locale et Docker

- nouveaux tests qualité/FETCH : `7 passed` ;
- non-régression resolver/service/qualité/FETCH : `25 passed` ;
- campagne ciblée élargie : `34 passed` ;
- Ruff : aucune erreur ; mypy strict : aucune erreur sur 18 fichiers ;
- image `gsie-api:quality-0048` construite depuis l'état courant ;
- migration PostgreSQL réelle : `20260810_0048 (head)` ;
- transaction de preuve puis `ROLLBACK` : cinq dimensions persistées, score
  global 0.8, doublon refusé, score 1.1 refusé ;
- nouvelle image démarrée en parallèle sous le même durcissement `read_only` :
  conteneur sain, Alembic `0048`, `/health` 200 et `/ready` 200, puis supprimé ;
- le conteneur API actif reste sur l'image précédente et n'a pas été remplacé
  sans ordre explicite de redéploiement ; la base, elle, est déjà en 0048 ;
- le downgrade de la base partagée n'a pas été exécuté, car il supprimerait
  potentiellement des données. Sa structure est couverte par la revue et le
  cycle devra être exécuté sur une base jetable en CI.
