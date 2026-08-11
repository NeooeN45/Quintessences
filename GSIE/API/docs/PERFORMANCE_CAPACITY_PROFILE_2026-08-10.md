# Profil de capacité HTTP GSIE — 10 août 2026

## Objectif

Expliquer le plafond d'environ 19 requêtes/s observé lors de DEC-000062, isoler
le coût du port publié Docker Desktop et vérifier le comportement de Gunicorn
lors du recyclage de ses workers.

## Outil reproductible

Le script `scripts/profile_http_capacity.py` utilise un client HTTP asynchrone
réutilisé, ignore les proxys du poste et dimensionne son pool à la concurrence.

Exemple dans le réseau Compose :

```powershell
docker run --rm --network api_default `
  -v "${PWD}/scripts/profile_http_capacity.py:/profile_http_capacity.py:ro" `
  --entrypoint python api-api /profile_http_capacity.py `
  --url http://api:8000/health --requests 6000 --concurrency 5
```

## Localisation du goulot principal

Campagne de 500 requêtes à concurrence 20 :

| Chemin | Débit | p95 | Succès |
|---|---:|---:|---:|
| Hôte Windows vers `127.0.0.1:8000` | 23,40 req/s | 1 857,59 ms | 500/500 |
| Réseau Docker vers `api:8000` | 405,14 req/s | 108,11 ms | 500/500 |

Le chemin publié Docker Desktop est donc environ 17 fois plus lent dans cette
configuration locale. Cette valeur ne qualifie ni Linux, ni Cloudflare, ni une
future infrastructure de production.

À concurrence 5, une campagne interne courte a atteint 459,72 req/s avant la
correction, et 669,34 req/s après redémarrage avec le réglage 5000/5000.

## Incident de recyclage reproduit

Le réglage historique était :

```text
max_requests        = 1000
max_requests_jitter = 50
workers             = 5
keepalive           = 5 s
```

Sous charge homogène, les cinq workers atteignaient leur seuil dans la même
fenêtre. La campagne de 6 000 requêtes a produit :

- 5 992 réponses 200 ;
- trois `RemoteProtocolError` ;
- cinq `ReadTimeout` à 30 secondes ;
- débit 123,38 req/s ;
- p50 8,40 ms, p95 60,26 ms, maximum 30 045,92 ms.

Les logs corrèlent les sorties groupées aux erreurs `Bad file descriptor`.

## Correction retenue

```text
max_requests        = 5000
max_requests_jitter = 5000
keepalive           = 5 s
```

Les valeurs sont configurables par `GSIE_GUNICORN_MAX_REQUESTS` et
`GSIE_GUNICORN_MAX_REQUESTS_JITTER`. Les valeurs non positives provoquent un
échec de démarrage explicite.

Comparatif strict après correction, 6 000 requêtes à concurrence 5 :

- 6 000 réponses 200 ;
- aucune erreur ;
- 669,34 req/s ;
- p50 6,43 ms ;
- p95 11,47 ms ;
- maximum 72,43 ms.

La campagne de 40 000 requêtes franchissant réellement les nouveaux seuils a
produit 39 996 réponses 200, quatre déconnexions, aucun timeout, 386,98 req/s
et un p95 de 33,30 ms. Les quatre sorties de worker étaient étalées sur plus
d'une minute : la panne groupée est supprimée, mais chaque recycle peut encore
fermer une connexion persistante sur ce conteneur unique.

## Expérience rejetée

`keepalive=0` a été essayé avec des seuils abaissés pour provoquer rapidement
les recyclages. Résultat : seulement 11 338 succès sur 12 000 et 121,75 req/s.
La configuration a été immédiatement annulée et l'API remise à `keepalive=5`.

## État final

- API saine, `/health` et `/ready` à 200 ;
- zéro restart et zéro OOM ;
- cinq workers, seuil 5 000, jitter 5 000, keep-alive 5 secondes ;
- FETCH SoilGrids et les autres politiques de données inchangés.

## Suite avant production

1. Exécuter le même script en CI Linux, sans Docker Desktop.
2. Tester au moins deux réplicas derrière la bordure avec retrait gracieux.
3. Définir un SLO et tester des routes représentatives, pas seulement santé.
4. Mesurer mémoire et latence pendant plusieurs cycles de recyclage.
5. Ne publier une capacité de production qu'après ces preuves.
