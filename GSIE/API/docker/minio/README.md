# MinIO local et CI — construction depuis les sources

## Périmètre

Ce Dockerfile remplace les références d'images amont indisponibles du Compose
local et de la validation Data Registry. Il ne définit pas le stockage objet
de production OVHcloud. La politique S3 et les comptes existants sont conservés.
Suivi : [baseline #65](https://github.com/NeooeN45/Quintessences/issues/65).

Les sources officielles sont épinglées : MinIO `9e49d5e` (release du 15 octobre
2025), mc `7394ce0` (release du 13 août 2025). Go et Debian sont figés par digest.
`-mod=readonly`, `GOTOOLCHAIN=local` et `CGO_ENABLED=0` évitent respectivement
la réécriture des dépendances, un compilateur implicite et une libc inattendue.
Les paquets Debian proviennent du dépôt configuré à la construction ; la
construction n'est pas revendiquée identique octet pour octet.

Sources : [MinIO officiel](https://github.com/minio/minio),
[go.mod épinglé](https://github.com/minio/minio/blob/9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a/go.mod),
[mc officiel](https://github.com/minio/mc/tree/7394ce0dd2a80935aded936b09fa12cbb3cb8096).
Les licences sont incluses dans les images ; ce périmètre de développement
ne qualifie pas leur exploitation publique ni la maintenance amont.

## Construction et compatibilité

Depuis `GSIE/API`, construire via le Compose canonique :

```sh
docker compose build minio minio-init
```

Le serveur fonctionne sous UID/GID 10001, avec certificats CA, curl et shell
pour les sondes existantes. Les ports restent liés à localhost. Un volume
ancien possédé par root doit être préparé explicitement après sauvegarde ;
aucun volume n'est effacé ni réattribué automatiquement par ce correctif.
Le stockage de configuration du client est placé dans `/tmp` comme le tmpfs
du service d'initialisation. La CI utilise des conteneurs de données synthétiques.

## Qualification

Le daemon Docker local était arrêté lors de la préparation. Les manifestes
des deux images de base ont été vérifiés sur leur registre officiel ; la
compilation et les scénarios S3 doivent être confirmés sur la PR CI exacte.
Ce correctif ne renouvelle pas la revue expirée du registre de vérité et ne
masque aucune vulnérabilité Trivy. Ces deux chantiers restent distincts.
