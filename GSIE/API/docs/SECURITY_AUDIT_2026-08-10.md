# Audit de sécurité Phase 4 — GSIE-SEC-AUDIT-0002 v1.0.0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-SEC-AUDIT-0002 |
| **Statut** | Review |
| **Version** | 1.0.0 |
| **Date** | 2026-08-10 |
| **Auteur** | Quintessences — audit assisté par Codex |
| **Périmètre** | `GSIE/API/` : stockage objet, configuration, Compose et traçabilité Data Registry |

## 1. Résumé

L’audit a identifié et corrigé quatre expositions confirmées : journalisation
des paramètres SQL, utilisation du compte racine MinIO par l’API, divulgation
de chemins locaux via `file://` et durée excessive des URLs présignées. Les
tests ciblés sont verts. Le smoke test MinIO réel et l’autorisation applicative
des futurs endpoints DataAsset restent des prérequis de validation finale.

## 2. Méthode et périmètre

La revue a couvert le diff Phase 4 au 2026-08-10, en particulier :

- `core/config.py` et les variables d’environnement ;
- `infrastructure/object_storage.py` et ses tests ;
- `docker-compose.yml`, MinIO, PostgreSQL et Cloudflare Tunnel ;
- `RFC-0038`, `DEC-000059`, `PROJECT_MEMORY.md`, `ROADMAP.md` et le changelog.

Il s’agit d’une revue statique et de tests ciblés. Aucun scan Internet, aucun
test intrusif, aucun déploiement et aucun accès à une donnée de production n’ont
été réalisés.

## 3. Constats et corrections

| ID | Sévérité initiale | Constat | Correction | État |
|---|---|---|---|---|
| SEC-01 | Haute | `pgaudit.log_parameter=on` journalisait les paramètres des écritures SQL, potentiellement personnels ou secrets. | Désactivation de `pgaudit.log_parameter`; l’opération, le rôle et le journal d’audit restent disponibles. | Corrigé |
| SEC-02 | Haute | L’API utilisait le compte racine MinIO, sans séparation des privilèges. | Compte MinIO runtime distinct, créé par `minio-init`, avec politique limitée au bucket GSIE. | Corrigé, smoke test requis |
| SEC-03 | Moyenne | Le backend local retournait un URI `file://` révélant le chemin du serveur. | `LocalStorage.put` retourne désormais un identifiant opaque `local:///…`; les URLs présignées locales sont refusées et un téléchargement doit passer par un endpoint API autorisé. | Corrigé |
| SEC-04 | Moyenne | Les liens présignés pouvaient vivre jusqu’à sept jours. | Durée par défaut ramenée à cinq minutes, maximum à quinze minutes. | Corrigé |
| SEC-05 | Faible | Les métriques internes Cloudflared écoutaient toutes les interfaces du conteneur. | Liaison sur `127.0.0.1:2000`. | Corrigé |

Le chiffrement côté serveur est obligatoire en staging/production et explicite
(`AES256` ou `aws:kms`). Le développement MinIO reste compatible sans KMS ; la
compatibilité du mode chiffré doit être confirmée par le smoke test de staging.

## 4. Contrôles effectués

| Contrôle | Résultat |
|---|---|
| Compilation syntaxique Python | Réussi |
| `docker compose config --no-interpolate --quiet` | Réussi |
| `git diff --check` | Réussi |
| Ruff sur le stockage et ses tests | Réussi |
| Tests ciblés sécurité/configuration/stockage | 85 passés sur 85 |

La première exécution ciblée a retourné le code 1 uniquement car le dépôt impose
100 % de couverture sur l’ensemble de l’API : une sous-suite n’atteint pas ce
seuil global. La même sous-suite relancée avec `--no-cov` est verte. Ce n’est
pas une dérogation au garde-fou CI ; la suite complète reste la preuve de
couverture globale.

## 5. Risques résiduels et prérequis

1. Exécuter le script `scripts/test_minio_storage_security.ps1` : création de
   bucket, création/rotation du compte runtime, upload réel, lecture,
   suppression et refus d’un second bucket.
2. Avant d’exposer un endpoint DataAsset, contrôler l’autorisation au niveau de
   la ressource et de l’organisation avant toute lecture, suppression ou URL
   présignée. Une clé S3 valide ne constitue jamais une autorisation métier.
3. Les objets doivent adopter un préfixe déterministe par organisation et actif;
   une URL présignée ne doit être délivrée qu’après cette vérification métier.
4. La politique MinIO locale est limitée au bucket, mais ne remplace pas les
   politiques IAM dédiées et un chiffrement KMS géré pour la production.
5. Exécuter la suite complète, le scan de dépendances et les tests d’intégration
   PostgreSQL/MinIO sur l’environnement staging avant déploiement public.
6. Les métadonnées `DataAsset` sont validées par le CRUD générique et la taille
   est protégée en base par `BIGINT` + `ck_data_asset_size_non_negative`. Les
   endpoints `/api/v1/data/*` restent toutefois interdits tant que RFC-0038
   n’est pas adoptée.

## 6. Gouvernance Data Registry

`DEC-000059` est validée comme cadrage architectural : elle fixe les concepts
et les limites du Data Registry. `RFC-0038` reste en statut Draft. Cette
validation ne vaut ni adoption de la RFC, ni autorisation d’ajouter les
migrations Registry, les endpoints `/api/v1/data/*`, les adapters ou le
resolver. Ces travaux restent soumis au passage de la RFC par le cycle prévu.

## 7. Sources et références

- [SEC-01 à SEC-05] Diff audité dans `GSIE/API/docker-compose.yml` et
  `GSIE/API/src/gsie_api/infrastructure/object_storage.py`, 2026-08-10.
- [TEST-SEC-01] Tests `GSIE/API/tests/unit/test_object_storage.py`,
  `test_config.py`, `test_ws_allowed_origins_security.py` et
  `tests/integration/test_auth_dev_production_blocker.py`.
- [DEC-000059] `03_DECISIONS/DEC-000059.md`.
- [RFC-0038] `02_RFC/RFC-0038-data-registry-gsie.md`.
- [SEC-SKILL] `.devin/skills/securite-gsie/SKILL.md`.

## 8. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-10 | Création de l’audit et enregistrement des corrections vérifiées. |
