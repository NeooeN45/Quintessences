# MinIO construit depuis les sources — solution provisoire

> **Statut : PROVISOIRE.** Décision du Fondateur du 16 novembre 2026
> (GSIE-PROMPT-0035). Échéance : remplacement décidé **avant toute ouverture
> de la plateforme à des testeurs**.

## Pourquoi ce dossier existe

Le stockage objet de développement et de CI repose sur MinIO (API S3). Les
images `minio/minio` et `minio/mc` ne sont plus téléchargeables anonymement :
la CI échouait sur les jobs *Data Registry* et *Haute disponibilité/TLS*
avant tout scénario fonctionnel (bilan
`23_QUALITY_MANAGEMENT/AUDITS/LEVEE_BLOCAGES_PR74_2026-11-16.md`, §7.1).

L'éditeur ne distribue plus l'édition communautaire sous forme d'image ou de
binaire, et la dernière version distribuée en binaire est affectée par
CVE-2025-62506. La seule version corrigée n'existe qu'en sources.

## Ce que fait la recette

`Dockerfile` construit deux cibles depuis des archives officielles épinglées :

| Cible | Composant | Révision | Archive vérifiée (SHA-256) |
|---|---|---|---|
| `client` | `mc` — RELEASE.2025-08-13T08-35-41Z | `7394ce0dd2a80935aded936b09fa12cbb3cb8096` | `95cd293c7119f16921a6dc515a1fb74a2227f19fd994b9c8b770a154e802ac44` |
| `server` | `minio` — RELEASE.2025-10-15T17-29-55Z | `9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a` | `45521908307306e925c98d629e1c17d78c8b72b6ee242b1bfb1409f7d8ee5841` |

- L'empreinte de chaque archive est vérifiée par Docker (`ADD --checksum`) à
  chaque construction ; une empreinte différente arrête la construction.
- `go mod verify` contrôle les dépendances contre `go.sum`.
- Aucun binaire tiers n'est téléchargé ; l'image d'exécution tourne sous
  l'utilisateur non privilégié `10001`.
- Les licences AGPL-3.0 amont sont copiées dans `/licenses`.

Les empreintes ont été relevées le 16 novembre 2026 par deux URL officielles
concordantes. Elles ne remplacent pas une signature amont, qui n'existe pas.

## Utilisation

```bash
# Depuis GSIE/API
docker compose build minio minio-init
docker compose up -d minio minio-init
```

En CI, les images sont étiquetées `gsie-minio:source-9e49d5e` et
`gsie-mc:source-7394ce0`.

### Volume local existant

L'ancienne image officielle s'exécutait en `root`. Un volume `gsie_miniodata`
créé avec elle n'est pas accessible à l'utilisateur `10001`. Les données de
développement étant jetables, recréer le volume :

```bash
docker compose down
docker volume rm gsie-api_gsie_miniodata   # vérifier le nom avec « docker volume ls »
docker compose up -d minio minio-init
```

## Dette ouverte

| Élément | Détail |
|---|---|
| Nature | Dépendance amont archivée, sans correctifs de sécurité futurs |
| Risque | Toute nouvelle vulnérabilité de MinIO restera sans correctif officiel |
| Périmètre actuel | Développement local et CI uniquement ; aucune donnée réelle |
| Échéance | Décision de remplacement avant ouverture à des testeurs |
| Pistes à instruire | Stockage objet géré par l'hébergeur ; autre serveur compatible S3 maintenu |
| Décideur | Camille Perraudeau (Fondateur), sur étude de l'architecte |

Tant que cette dette est ouverte, ne pas exposer ce service sur Internet et
ne pas y stocker de données de clients.
