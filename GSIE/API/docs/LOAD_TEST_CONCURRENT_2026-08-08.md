# Rapport — Benchmark de charge concurrente (Gate 6 Performance)

| Champ | Valeur |
|---|---|
| **Référence** | ROADMAP.md — Gate 6 « Performance », reste « benchmark charge concurrente, mémoire conteneur Docker, production » |
| **Date** | 2026-08-08 |
| **Périmètre** | API GSIE en local (Docker Desktop / Windows), base de dev réelle |
| **Complète** | `scripts/validation_benchmark.py` (S3, séquentiel, `DEC-000043`) |
| **Script** | `scripts/load_test_concurrent.py` |

---

## 0. Synthèse

`scripts/validation_benchmark.py` (S3) prouve la latence nominale en
séquentiel (une requête à la fois). Il ne dit rien du comportement sous
charge réelle — plusieurs requêtes en vol simultanément. Ce rapport comble
ce trou avec trois volets indépendants, et découvre **un vrai problème de
capacité mémoire** qui n'était pas visible avant.

| Volet | Résultat |
|---|---|
| 1. Capacité HTTP brute | ✅ 100% de succès, mais révèle la trouvaille §2 |
| 2. Rate limiting sous rafale | ✅ Tient sous 60 requêtes simultanées, cohérent avec le test séquentiel du pentest du 2026-08-07 |
| 3. Pool de connexions DB | ✅ **Validé empiriquement pour la première fois** — dégradation gracieuse, zéro erreur |
| **Mémoire conteneur** | ⚠️ **Trouvaille critique** — voir §2 |

---

## 1. Volet 3 — Pool de connexions DB (le plus important à valider)

`DEC-000037` fixe la formule `workers × (pool_size + max_overflow) ≤
max_connections` mais elle n'avait jamais été vérifiée empiriquement —
seulement calculée sur le papier. Ce volet ouvre directement 24 sessions
SQLAlchemy concurrentes (le même `async_session_factory` que l'API utilise)
contre une capacité configurée d'un worker de 14 (`pool_size=4` +
`max_overflow=10`).

**Piège méthodologique rencontré et corrigé** : une première mesure
comptait la concurrence à l'ouverture du context manager
`async with async_session_factory()`, qui n'acquiert pas de connexion
physique (checkout paresseux — seule l'exécution d'une requête le
déclenche). Résultat : un pic mesuré de 24 alors que la latence (jusqu'à
1,2s pour un `pg_sleep(0.2)`) trahissait une file d'attente invisible au
compteur. Corrigé en interrogeant directement `engine.pool.checkedout()`
— l'information authentique de SQLAlchemy.

**Résultat corrigé** :

```text
24 sessions demandées, capacité configurée 14
Connexions checked-out simultanément (pic réel) : 14
Statuts : {'ok': 24}
```

Le pic ne dépasse jamais 14 : les 10 sessions excédentaires ont attendu en
file d'attente sans lever d'erreur. **La formule de DEC-000037 est
confirmée empiriquement pour la première fois.**

---

## 2. Trouvaille critique — mémoire du conteneur `api` proche de la limite, au repos

`docker stats` échantillonné pendant et après les tests :

| État | `api-api-1` (limite configurée : 768 MB) |
|---|---|
| **Repos, aucune charge** | **725,8 MiB / 768 MiB (94,5 %)** |
| Sous charge (60 requêtes concurrentes `/health`) | jusqu'à 767,1 MiB / 768 MiB (99,9 %) |
| `api-db-1` (limite 1 GB) | 89–107 MiB (< 11 %) — aucun problème |
| `api-redis-1` (limite 512 MB) | 8 MiB (< 2 %) — aucun problème |

**Ce n'est pas un effet de la charge — c'est l'empreinte de base.** Une
mesure au repos (1,5 % CPU, aucune requête active) donne déjà 94,5 % de la
limite mémoire configurée. Le conteneur n'a quasiment aucune marge : la
charge ne fait que le pousser du bord du gouffre au bord du gouffre.

Détail par processus (`/proc/*/status`, RSS) :

| PID | RSS | Rôle |
|---|---|---|
| 632 | 333,7 MB | Worker gunicorn (a traité des requêtes) |
| 11 | 294,2 MB | Worker gunicorn (a traité des requêtes) |
| 8 | 108,0 MB | Worker gunicorn |
| 9 | 102,5 MB | Worker gunicorn |
| 10 | 82,7 MB | Worker gunicorn |
| 1 | 13,9 MB | Master gunicorn |

`GSIE_GUNICORN_WORKERS=5` (défaut `gunicorn.conf.py`). Les workers qui ont
traité des requêtes pendant le test pèsent 3 à 4× plus que ceux restés
inactifs — cohérent avec le chargement paresseux des dépendances lourdes
(scipy, xarray, cfgrib, geopandas, bindings Rust de l'Evidence Engine)
au premier import déclenché par une requête, plutôt qu'au démarrage.

**Recommandation** (non appliquée dans ce rapport — décision d'infrastructure) :

1. Augmenter `deploy.resources.limits.memory` du service `api` dans
   `docker-compose.yml` (768M → au moins 1.5–2 GB), ou
2. Réduire `GSIE_GUNICORN_WORKERS` (5 → 2-3) si la charge de production
   attendue ne justifie pas 5 workers, ou
3. Profiler précisément quelles dépendances (scipy/xarray/cfgrib
   notamment) gonflent chaque worker et évaluer un import paresseux /
   partagé.

Sans correction, un pic de trafic réel (pas seulement un test synthétique)
risque un **OOM-kill** du conteneur par le cgroup Docker — c'est
exactement le mode de panne que ce gate est censé prévenir avant
extension.

---

## 3. Volet 2 — Rate limiting sous rafale

`SECURITY_AUDIT_2026-08-07.md` avait vérifié le rate limit en séquentiel
(11 requêtes lentes → 429 après épuisement). Ce volet envoie 60 requêtes
**simultanées** sur un endpoint à 120/min (`GET /api/v1/resources`) :

```text
60 requêtes simultanées en 9.58s
200 OK : 60 — 429 Too Many Requests : 0
```

Toutes acceptées (60 < 120/min), cohérent avec la limite configurée. Le
compteur Redis (`slowapi`) ne montre pas de dérive sous rafale par rapport
au comportement séquentiel déjà vérifié.

---

## 4. Volet 1 — Capacité HTTP brute et limite de la méthodologie

600 requêtes concurrentes sur `/health` (sans authentification, sans DB) :
100 % de succès dans tous les cas testés. En revanche, **les chiffres de
latence absolus ne sont pas exploitables tels quels** :

| Où tourne le générateur de charge | p50 | p95 |
|---|---|---|
| À l'intérieur du conteneur `api-api-1` (réseau Docker interne) | 207 ms | 362 ms |
| Sur l'hôte Windows, via le port exposé `127.0.0.1:8000` | 1 382 ms | 3 305 ms |

Écart de 5 à 10× selon que le trafic traverse ou non la couche de
port-forwarding NAT de Docker Desktop sous Windows. C'est un artefact de
l'environnement de développement local, pas une caractéristique de
l'API elle-même — en production, le trafic entre par le tunnel Cloudflare
directement vers le conteneur, sans cette couche.

**Conséquence méthodologique** : les latences absolues de ce rapport ne
doivent pas être citées comme représentatives de la production. Seules
les conclusions relatives (le pool se comporte correctement, le rate
limit tient, la mémoire est proche de la limite) sont fiables — elles ne
dépendent pas de la topologie réseau du test.

---

## 5. Ce que ce rapport ne couvre pas (reste du Gate 6)

- **Mesure en production** — ce rapport tourne en local (Docker Desktop
  Windows). Le comportement mémoire/latence doit être re-mesuré sur
  l'hôte Linux de production une fois déployé, avec un vrai profil de
  trafic (pas seulement `/health` et une liste de resources vide).
- **Charge sur la chaîne métier complète** (`/orchestration/analyse`) —
  son rate limit strict (20/min) rend un test de charge concurrente sur
  cet endpoint peu informatif au-delà de ce que le pentest a déjà vérifié
  en séquentiel ; un test de charge utile nécessiterait un environnement
  dédié avec rate limit desserré, hors périmètre de ce rapport.
- **Terrain réel / données multi-sources** — reste du Gate 4 (Science),
  pas de ce rapport.

---

## 6. Reproduire

```bash
# Depuis l'hôte, copie le script dans le conteneur via stdin (rootfs
# read-only — docker cp échoue, /dev/stdin fonctionne) :
docker exec -i api-api-1 python /dev/stdin \
  --url http://localhost:8000 --concurrency 60 --requests 600 \
  --output /tmp/load_test_resultat.json \
  < scripts/load_test_concurrent.py

# Récupérer le rapport JSON complet :
docker cp api-api-1:/tmp/load_test_resultat.json ./load_test_resultat.json
```

---

*Rapport produit le 2026-08-08. Aucune modification de configuration
appliquée — la recommandation §2 (mémoire) reste une décision
d'infrastructure à trancher par le Fondateur.*
