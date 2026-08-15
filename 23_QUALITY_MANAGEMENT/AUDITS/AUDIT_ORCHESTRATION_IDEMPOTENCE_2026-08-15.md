# Audit — route métier longue et idempotence d’orchestration

**Date :** 2026-08-15
**Périmètre :** `POST /api/v1/orchestration/analyse`, persistance
`analysis_run`, migration `20260815_0050`, benchmark HA Linux/TLS
**Statut :** validé localement ; preuve GitHub à rejouer après intégration

## Objectif

La route d’orchestration est la première opération métier représentative du
banc HA. Elle exécute Reasoning → Diagnostic → Recommendation → Validation et
persiste une preuve append-only. L’audit vérifie qu’un retry réseau ne réexécute
pas les moteurs, y compris lorsque deux réplicas partagent PostgreSQL.

## Contrat retenu

- `requete_id` est la clé métier stable d’une demande GeoSylva.
- `Idempotency-Key`, lorsqu’il est fourni, doit être égal à `requete_id`.
- L’empreinte SHA-256 couvre le contrat JSON canonique complet.
- Une nouvelle tentative avec la même empreinte retourne exactement la preuve
  persistée ; aucune exécution moteur n’est relancée.
- La même clé avec un contenu différent est rejetée en HTTP 409.
- Une preuve historique sans empreinte est refusée, afin de ne pas réutiliser
  silencieusement une ligne produite avant le contrat d’idempotence.
- Un verrou transactionnel `pg_advisory_xact_lock` sépare les courses entre
  replicas ; un index unique partiel fournit une seconde garantie SQL.

## Cloisonnement des données

Le benchmark refuse toute vérification si les variables suivantes ne désignent
pas explicitement l’environnement de test :

```text
GSIE_DATABASE_ROLE=test
GSIE_DATA_NAMESPACE=gsie-test
GSIE_DB_NAME=gsie
```

Le workflow HA passe ces valeurs explicitement au conteneur de benchmark et
contrôle les lignes `analysis_run` via le rôle applicatif sans accès à une base
de production.

## Corrections découvertes par la preuve

Le premier test d’intégration a détecté que le champ Pydantic calculé
`Recommendation.contournable` était sérialisé dans le JSON de preuve mais
interdit à l’entrée lors de sa relecture. La correction est maintenant
centralisée : les propriétés calculées sont retirées de la représentation
persistée et de la relecture, tandis que `extra=forbid` continue de refuser
toute autre dérive de schéma.

## Vérifications reproduites

| Contrôle | Résultat |
|---|---:|
| Tests unitaires idempotence + routeurs | **35 passants** |
| Tests intégration orchestration PostgreSQL/PostGIS | **7 passants** |
| Tests migration Alembic upgrade/downgrade/reupgrade | **2 passants** |
| Ruff ciblé | **OK** |
| Mypy strict orchestration | **OK** |
| Syntaxe CLI benchmark | **OK** |
| Vérification YAML workflow | **OK** |

Les tests d’intégration prouvent notamment :

- deux POST identiques retournent le même JSON et une seule ligne
  `analysis_run` ;
- un contenu différent avec le même `requete_id` retourne HTTP 409 ;
- huit analyses distinctes concurrentes restent persistées ;
- la migration 0050 et son index partiel restent alignés avec le registre
  SQLAlchemy et réversibles.

## Automatisation HA Linux/TLS

`.github/workflows/ha-linux.yml` ajoute :

1. un replay idempotent HTTPS contrôlé, avec CA éphémère et vérification SQL ;
2. douze requêtes métier sous concurrence pendant le drainage d’un replica ;
3. la charge `/health` existante, drainée dans le même scénario ;
4. la publication des deux rapports JSON comme artefacts CI.

Le workflow n’ouvre pas FETCH, ne modifie aucun SLO et conserve le scénario
Redis dégradé. Le premier run distant après cette modification reste requis
avant toute publication de capacité de production.

## Verdict

La route métier longue et son contrat d’idempotence sont **validés sur
PostgreSQL réel en environnement de test**. La porte de production reste
fermée tant que le workflow Ubuntu/TLS n’a pas reproduit le replay, la charge
pendant drainage et les dépendances dégradées sur le même commit.
