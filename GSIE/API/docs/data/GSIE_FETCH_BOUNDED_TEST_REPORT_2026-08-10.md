# Rapport de tests — récepteur FETCH borné — 2026-08-10

## Verdict

**56 tests sur 56 passent.** Aucun test n'active FETCH, ne contacte SoilGrids,
ne crée de `DataAsset RAW` ou ne promeut une version.

## Couverture reproduite

- qualification fermée avant l'adapter ;
- source absente et décisions dupliquées refusées ;
- endpoint et URL non sûrs refusés ;
- propriété, profondeur, quantile et emprise WCS bornés ;
- MIME inattendu refusé avant écriture ;
- `Content-Length` excessif refusé ;
- dépassement réel au fil des chunks refusé ;
- corps/chunk invalides refusés ;
- timeout global déclenchant `abort()` ;
- SHA-256 calculé pendant le flux ;
- checksum attendu invalide refusé par le contrat ;
- divergence de checksum déclenchant `abort()` sans `commit()` ;
- `commit()` uniquement après succès complet ;
- qualité implicite dans `DatasetVersion.stats` ignorée ;
- run incomplet sans score global ;
- promotion générique STAGING/PRODUCTION refusée.

## PostgreSQL et Docker

- image testée : `gsie-api:quality-0048` ;
- Alembic : `20260810_0048 (head)` ;
- run transactionnel : cinq dimensions, score global `0.8` ;
- unicité run/dimension : contrainte vérifiée ;
- score hors `[0,1]` : contrainte vérifiée ;
- fin du test : `ROLLBACK`, aucune donnée conservée.

## Qualité statique

- Ruff : aucune erreur ;
- mypy strict : aucune erreur sur 19 fichiers ;
- `git diff --check` : propre.

## Réserve conservée

La réserve sur `sink.abort()` est levée : l'abandon dispose désormais d'un
timeout propre configurable, borné à 30 secondes. Un blocage produit
`FETCH_ABORT_TIMEOUT` sans attendre indéfiniment.

## Sink MinIO transactionnel

Le sink conserve les chunks dans un `SpooledTemporaryFile` privé. Aucun objet
distant n'existe avant `commit()`. Le commit appelle l'upload multipart S3,
dont la visibilité intervient seulement après finalisation ; le backend S3
annule déjà le multipart sur exception. Une clé existante n'est jamais écrasée
et seules les clés `raw/fetch/...` sont admises.

Preuves MinIO réelles :

- absence avant commit ;
- publication d'un objet unique après commit ;
- relecture et identité exacte des octets ;
- suppression et absence finale confirmées ;
- chemin abort : aucun objet publié ;
- réponse S3 ambiguë après tentative de commit : suppression anti-orphelin ;
- 96 tests ciblés incluant les 41 tests du stockage objet : passants.

La réserve d'observabilité sur les sondes d'absence MinIO est levée. Les
`HEAD 404` attendus sont convertis en `ObjectNotFoundError`, journalisés au
niveau `debug`, puis exposés par `exists()` sous la forme `False`. Ils ne
polluent plus les alertes d'exploitation. Les codes S3 non liés à une absence
restent journalisés au niveau `error` et remontent en `ObjectStorageError`.

La campagne après correction conserve **96 tests sur 96 passants**. Ruff ne
signale aucune erreur et mypy strict valide les 21 fichiers Data Registry et
ObjectStorage contrôlés.

L'image candidate `gsie-api:quality-0048` a été reconstruite sans redéployer
les services actifs (`sha256:9fb17c5d8b29f8c2f2f5dbd6da9c08d7d71a601635715cd9a9acd0eb9714915d`).
Un smoke test interne confirme la conversion d'un `NoSuchKey` en absence au
niveau `debug`.
