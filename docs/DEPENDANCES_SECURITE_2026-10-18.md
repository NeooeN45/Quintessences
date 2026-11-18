# Dépendances : vérification de sécurité du 18 octobre 2026

| Champ | Valeur |
|---|---|
| Identifiant | AUDIT-DEPS-2026-10-18 |
| Statut | Draft |
| Version | 1.0 |
| Date | 2026-10-18 |
| Auteur | Codex, pour revue du mainteneur |


Ce relevé porte sur les dépendances verrouillées utilisées par les contrôles du
projet ; ce n’est pas une certification de sécurité du déploiement.
Les rapports détaillés et commandes sont conservés dans les livrables de la session.

## Correctifs

PyJWT 2.13.0 → 2.15.0, multidict 6.7.1 → 6.9.1 et urllib3 2.7.0 → 2.8.0.
Audit `pip-audit 2.9.0` sur l’export du verrou API avec extra dev : aucune
vulnérabilité connue retournée après correction à cette date (128 dépendances).
Cela ne couvre pas les images Docker, Rust, le mobile ou les extras non exportés.

## Vérifications distinctes

Les tests d’identité sont rejoués avec le verrou corrigé. Les contrôles de
secrets et de gouvernance sont indépendants de cet audit de paquets.
Le contrôle HA GitHub échoue sur le téléchargement de `minio/mc` (accès refusé),
avant le test des deux replicas. La cause n’est pas masquée par un changement
de seuil ou un remplacement non vérifié d’image. Cette dépendance d’infrastructure
reste à qualifier avant fusion et avant toute conclusion de validation serveur complète.
