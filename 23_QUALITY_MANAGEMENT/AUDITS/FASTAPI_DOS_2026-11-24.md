# Correctif FastAPI — GHSA-f56c-v883-vx8r

| Champ | Valeur |
|---|---|
| Date | 2026-11-24 |
| État | Préparé sur branche dédiée, en relecture |
| Base | `47be2044e1af9082a47dc1ad2d673fd16080f592` |
| Branche | `fix/fastapi-dos-2026-11-24` |
| Suivi | [Ticket #89](https://github.com/NeooeN45/Quintessences/issues/89) et registre #37 |
| Environnement | Linux x86_64, Python 3.12.14, uv 0.13.4 pour le verrou |

## Problème et correction

L'[avis officiel](https://github.com/fastapi/fastapi/security/advisories/GHSA-f56c-v883-vx8r)
décrit un traitement quadratique de certains paramètres query/header/form
dans FastAPI `>=0.123.2,<0.163.2`. La version épinglée `0.134.0` est concernée.
Le correctif préparé retient la [version minimale corrigée `0.163.2`](https://github.com/fastapi/fastapi/releases/tag/0.163.2).

La comparaison TOML des deux verrous confirme que FastAPI est le seul paquet
dont la version change, sur 135 entrées de résolution. Les nouvelles dépendances
directes `anyio` et `opentelemetry-api` étaient déjà verrouillées pour d'autres
usages, sans mise à jour. uv `0.13.4`, également épinglé dans le Dockerfile,
écrit le format de verrou révision 5 au lieu de 3 ; aucune réécriture globale
des marqueurs ni dérive `eccodeslib/eckitlib` n'est observée.

## Preuve de régression bornée

Six scénarios ASGI locaux utilisent 64 ou 256 paramètres inconnus, une liste
de valeurs répétées et, pour le formulaire, un fichier de quatre octets.
Ils n'émettent aucun trafic réseau externe. Les balayages `getlist` Starlette
sont comptés : chacun parcourt les entrées reçues, donc leur multiplication
par le nombre de paramètres révèle le défaut sans test de temps instable.

| Entrée | 64 paramètres, FastAPI 0.134.0 | 256 paramètres, FastAPI 0.134.0 | FastAPI 0.163.2 |
|---|---:|---:|---|
| Query | 66 balayages | 258 balayages | Budget de 8 respecté |
| Headers | 72 balayages | 264 balayages | Budget de 8 respecté |
| Formulaire multipart + upload | 65 balayages | 257 balayages | Budget de 8 respecté |

Les six tests échouent sur l'ancienne version et passent après mise à jour.
Les réponses gardent les deux valeurs répétées et le contenu exact du fichier.
Ce compteur prouve cette régression algorithmique ; il ne mesure ni la latence
en production ni la totalité des parseurs HTTP. La baseline générale reste
`UNMEASURED` et aucun gain de performance chiffré n'est annoncé.

## Compatibilité et validation

FastAPI représente désormais les routeurs inclus par des contextes, et leur
inventaire direct avec `app.routes` ne garantit plus le parcours des endpoints.
Cinq tests d'inventaire sont adaptés à `fastapi.routing.iter_route_contexts`.
Le contrôle du contrat SlowAPI parcourt aussi ces contextes et échoue si aucun
endpoint limité n'a été inspecté. Ses assertions de signature sont conservées.

- Les six tests de régression ciblés réussissent.
- OpenAPI régénérée : **aucun diff**, 151 chemins et 299 schémas.
- mypy strict : **272 fichiers source**, aucune erreur.
- Ruff et contrôle de format : **548 fichiers**, conformes.
- `uv lock --check`, gouvernance et catalogue des prompts : conformes.
- Suite unitaire complète après préparation du banc : **3 216 réussis,
  64 ignorés, zéro échec**, en 210,33 secondes sur deux workers pytest.
  Dix avertissements de bibliothèques restent visibles.
- Revue indépendante et probe ASGI en mémoire : deux routeurs imbriqués,
  `SlowAPIASGIMiddleware`, quota de deux appels par minute et trois valeurs
  différentes du paramètre de chemin donnent **200, 200, 429**. Les en-têtes
  de quota sont conservés (`Remaining` 1, 0, 0 ; `Retry-After` 60).
  Cette preuve ne couvre pas Redis partagé ni plusieurs workers Gunicorn.

La première suite complète a servi à identifier les prérequis du banc :
205 échecs étaient dus à `ALL_PROXY` SOCKS sans `socksio`, un à l'absence de
la paire JWT de test et cinq aux inventaires de routes. La reprise utilise la
paire de test générée par le script officiel, les transports HTTP simulés
sans `ALL_PROXY`/`all_proxy`, tout en conservant `HTTP_PROXY` et `HTTPS_PROXY`.
Ce réglage est limité au processus de test et ne modifie pas l'application.

Commandes de reproduction depuis `GSIE/API` :

```bash
uv tool run --from uv==0.13.4 uv sync --locked --extra dev
sh docker/generate-jwt-keys.sh # seulement si la paire de test est absente
env -u ALL_PROXY -u all_proxy .venv/bin/python -m pytest tests/unit -q -n 2 --no-cov
.venv/bin/mypy src --strict
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/python scripts/extract_openapi.py
git diff --exit-code -- docs/openapi.json
```

## Limites et conditions de fusion

- La release a été publiée le 17 novembre à 18 h 29 UTC. Le commentaire
  de `GSIE/API/pyproject.toml` exige une maturité supérieure à sept jours ;
  cette condition n'est satisfaite qu'après le
  **24 novembre 2026 à 18 h 29 min 04 s UTC**. Cette branche prépare une
  correction de sécurité avant cette échéance ; aucune dérogation n'est
  déclarée validée et aucune fusion n'est effectuée.
- Intégration PostgreSQL/PostGIS, harnais de mutation, couverture combinée,
  Data Registry, HA/TLS, construction et scan d'image restent à qualifier.
- Les limites edge query/header/formulaire demandées par #89 ne sont pas
  ajoutées dans ce lot. Le correctif de dépendance ne remplace pas ce volet.
- La PR #88 et les constats #75/#76 sont inchangés. Aucun invariant n'est
  promu et le ticket #89 reste ouvert.
- Aucune installation validée de Floorplan accessible n'a été retrouvée ;
  aucune carte n'est présentée comme créée ou actualisée.

Retour arrière : revert du lot, sans migration de données. Cela rétablirait
aussi la dépendance vulnérable et n'est donc pas une solution de sécurité.
