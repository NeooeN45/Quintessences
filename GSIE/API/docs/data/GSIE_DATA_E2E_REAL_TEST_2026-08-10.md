# Test réel Data Registry — acquisition → stockage → normalisation → utilisation

**Date :** 10 août 2026

**Trace :** `e2e-data-20260810`

**Exécution :** conteneur `api-api-1`, réseau Docker, MinIO `gsie-assets`
**Résultat :** **4/4 adapters réussis**, nettoyage des objets confirmé

## Périmètre

La campagne utilise les clients réels déjà encapsulés par les adapters. Elle
ne contient ni fixture, ni réponse simulée :

| Adapter | Acquisition bornée | Normalisation/consommation | Résultat |
|---|---|---|---|
| GBIF | `Quercus robur` — Species Match | `usageKey=2878688`, nom scientifique | 1 ligne, 558 octets, checksum `aff9fbf82b46e7461dc13283cad7886211a4bf9818d4801316af80447bd37aa6` |
| IGN | altitude de Paris (`48.8566, 2.3522`) | altitude finie `34.83 m` | 1 ligne, 145 octets, checksum `b136a84ce4464cfff49b2202c47ae88ed8e048ac9ac0aa3b1719570e034b6134` |
| SoilGrids | profil `0–5 cm` à (`48.2, 2.2`) | pH `7.0`, argile `30.3 %`, sable `8.5 %`, limon `61.2 %` | 1 ligne, 143 octets, checksum `80aed24aded8e3102845c2e5cd90382191748249735e830346a0286c33b71cad` |
| Météo-France | carte du danger de feux départementale | 96 départements, premier `01`, niveau J+1 `2` | 96 lignes, 11 828 octets, checksum `176ef2cb76251d97939f86e17cea479a777f9d7794537a1f866c5a361c2ff4e2` |

Pour chaque ligne du tableau, le test a exécuté exactement la chaîne suivante :

1. `health()` de l'adapter, attendu `healthy` ;
2. `query()` sur le fournisseur public ;
3. `normalize()` puis contrôle de domaine (types, bornes physiques, présence) ;
4. sérialisation JSON canonique et `S3Storage.put()` dans MinIO ;
5. `head()` puis `get()`, comparaison octet à octet et recalcul SHA-256 ;
6. projection consommateur minimale (taxonomie, altitude, profil de sol,
   danger départemental) ;
7. sélection par `resolve_candidates`, politique `data-resolver-1`, candidat
   sélectionné et éligible ;
8. suppression de l'objet temporaire.

Le dernier run, effectué après activation du pool S3 partagé, a utilisé le
préfixe temporaire `e2e/registry/2e75fd012456497cae8a891db2f86f08/`
et a terminé avec `cleanup=ok`. Le client a été fermé explicitement après le
nettoyage ; aucun objet de cette campagne n'est resté dans MinIO.

## Rejouer la campagne

Le test reproductible est dans
[`scripts/test_data_registry_e2e.py`](../../scripts/test_data_registry_e2e.py).
Dans le conteneur API, le contenu du fichier peut être envoyé à Python :

```powershell
$script = Get-Content -Raw GSIE/API/scripts/test_data_registry_e2e.py
$script | docker exec -i `
  -e SSL_CERT_FILE=/tmp/gsie-e2e-ca.pem `
  api-api-1 python -
```

`SSL_CERT_FILE` doit pointer vers un bundle CA approuvé par le poste (dans ce
contexte, le certificat racine Kaspersky a été ajouté temporairement au bundle
du conteneur). Le test n'utilise ni `verify=False`, ni `curl -k`, et les
fichiers CA temporaires sont supprimés après la campagne.

`--keep-objects` est disponible uniquement pour une inspection opérateur
explicite. Par défaut, les objets sont toujours supprimés.

## Corrections et limites révélées par le test

- La première écriture MinIO a exposé une erreur de politique : la commande
  Compose imprimait littéralement `arn:aws:s3:::%s`. La génération est
  maintenant formatée avec `printf` et la politique est recréée de façon
  idempotente avant association au compte runtime. L'écriture multipart,
  la lecture et la suppression ont ensuite réussi.
- Paris ne fournit pas de couche SoilGrids exploitable dans cette requête.
  Le client a renvoyé `{}` (sans valeur inventée) ; le test utilise donc le
  point français couvert `48.2,2.2` et conserve ce cas vide comme contrôle de
  non-imputation.
- Les quatre adapters actuels déclarent `QUERY` et `NORMALIZE`, mais pas
  `FETCH`. La campagne prouve donc l'acquisition structurée réelle et
  l'archivage de la représentation normalisée. L'archivage des octets bruts
  fournis par chaque distributeur et la création de `DataAsset` restent une
  étape ultérieure, sans déduire une licence ou un droit de redistribution.
  La santé réelle est désormais persistée séparément : quatre lignes
  `DatasetHealth` ont été créées puis rejouées sans doublon. Voir
  `GSIE_DATA_REGISTRY_MANIFEST_APPLICATION_2026-08-10.md`.
