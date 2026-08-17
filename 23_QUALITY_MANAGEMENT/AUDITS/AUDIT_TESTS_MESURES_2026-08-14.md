# Audit des tests et mesures — 14 août 2026

## Verdict

La qualité locale du code est validée. Le premier contrôle Docker de la journée
avait été bloqué par l’accès local au démon, mais la reprise avec Docker
Desktop disponible est maintenant verte. La campagne complète d’intégration
est également validée : 349 tests passent avec deux workers et Docker
obligatoire.

## Résultats reproductibles

| Périmètre | Résultat | Statut |
|---|---:|---|
| Tests unitaires backend | 2 935 passants, 63 ignorés | PASS |
| Nouveaux tests sécurité/garde Docker | 55 passants (50 ciblés + 5 garde) | PASS |
| Campagne moteurs/pipeline | 316 passants, 1 ignoré | PASS |
| Campagne domaines/adapters | 166 passants | PASS |
| Audit statique des moteurs | 14/14 | PASS |
| Isolation d’environnement valide | `ISOLATION_OK` | PASS |
| Isolation production avec rôle staging | rejet explicite | PASS négatif |
| Migration PostgreSQL 0049 | 2 passants | PASS (campagne ciblée) |
| Orchestration HTTP PostgreSQL | 4 passants | PASS (campagne ciblée) |
| Couverture routeurs | 33 passants | PASS |
| WebSocket sécurité | 112 passants | PASS |
| Compilation Python | `COMPILEALL_OK` | PASS |
| Tests Android GeoSylva JVM | `BUILD SUCCESSFUL` | PASS |
| Smoke Docker Compose isolé (`gsie-test`) | 6 services sains | PASS |
| Intégration ciblée base/migrations/E2E API | 33 passants, 1 avertissement | PASS |
| Intégration complète PostgreSQL/Docker | 349 passants, 12 avertissements | PASS |
| Bandit SAST (seuil CI moyen/haut) | aucun problème moyen/haut | PASS |

Les campagnes unitaires, migration, orchestration et Android ont été exécutées
avant cette passe et leurs commandes sont conservées dans l’historique de
travail. Le script `scripts/audit_engines.py` reproduit ici les 14/14 moteurs.
La relance globale post-ajout a été rejouée après correction avec deux workers,
TTL de test explicite et secret de développement dédié ; elle a produit le
rapport final vert décrit ci-dessous.

## Vérification Docker et campagne ciblée

Le moteur Docker répond correctement : version client/serveur 29.6.2, 6 CPU
et environ 20 Gio de mémoire disponibles. La configuration Compose de test a
été validée avec `.env.test.example`, puis la stack isolée a été démarrée avec
les services PostgreSQL, Redis, MinIO, Mailpit, API et outbox-worker.

Les six conteneurs sont restés `running` et `healthy`. PostgreSQL expose
PostGIS 3.4 ainsi que AGE, pgvector et pgaudit ; la migration Alembic est à la
révision `20260813_0049`. Redis répond `PONG`, MinIO a été initialisé avec le
bucket et la politique de test, et l’API répond :

```text
GET /health  -> 200, status=healthy
GET /ready   -> 200, database healthy, redis healthy
```

La suite ciblée exécutée contre `gsie_test` est :

```text
tests/integration/test_database.py
tests/integration/test_e2e_api.py
→ 33 passed, 1 warning, 117,78 s
```

## Campagne d’intégration complète

La collecte confirme **349 tests** dans `tests/integration`. La tentative
historique du 14 août :

```text
pytest tests/integration -q --no-cov --tb=short
→ timeout après 1 204 s (code 124), aucun rapport final
```

Cette tentative est classée **NON_CONCLUANTE_ENV** et ne doit pas être
interprétée comme un échec applicatif. Après correction des fixtures de secrets,
du TTL de test et de l’identité GBIF, la campagne de référence a été rejouée :

```text
GSIE_REQUIRE_DOCKER=1 pytest tests/integration -q --no-cov \
  --tb=short --durations=30 -n 2
→ 349 passed, 12 warnings, 1393,34 s (23 min 13 s)
```

## Mesures de performance disponibles

Les dernières mesures HTTP valides restent celles de la campagne Linux/HA et
du profil Docker Desktop :

- réseau Compose interne : 405,14 req/s, p95 108,11 ms sur 500 requêtes,
  concurrence 20 ;
- configuration Gunicorn corrigée : 6 000/6 000 réponses, 669,34 req/s,
  p95 11,47 ms, concurrence 5 ;
- test à 40 000 requêtes : 39 996 réponses, 386,98 req/s, p95 33,30 ms ;
- port publié Docker Desktop : environ 18,7–18,9 req/s sous forte
  concurrence, valeur non représentative de la production.

Ces valeurs ne mesurent pas encore la route d’orchestration complète avec
écriture `analysis_run`. Cette mesure est explicitement reportée jusqu’à la
disponibilité d’un environnement Docker sain.

## Sécurité et qualité statique

- `ruff` et `mypy --strict` : campagnes ciblées passées précédemment ;
- Bandit 1.7.10 : aucun problème moyen/haut sur 43 132 lignes ; les quatre
  alertes faibles restantes sont sous le seuil CI ;
- les marqueurs `REMPLACER_PAR_SECRET_MANAGER`/équivalents sont désormais
  refusés avant démarrage en staging/production pour PostgreSQL, Redis, S3 et
  la clé MFA ;
- les valeurs faibles documentaires (`change-me`, `password`, `secret`) sont
  également refusées hors développement ;
- le lanceur `scripts/run_integration_guarded.py` borne désormais la sonde
  Docker à 30 secondes et pytest à 40 minutes, avec codes de sortie distincts
  (`DOCKER_BLOCKED`/timeout), accepte un fichier d’environnement optionnel
  sans écraser les variables explicites, applique des défauts de test sûrs et
  limite par défaut pytest à deux workers ;
- la fixture Windows ferme explicitement les boucles événementielles qu’elle
  crée ; les avertissements internes de couverture sont traités par catégories
  explicites dans la configuration pytest ;
- aucune désactivation TLS, aucun FETCH canonique ouvert et aucune nouvelle
  donnée RAW produite pendant cette passe.

## Actions obligatoires avant clôture

1. Mesurer la route d’orchestration réelle : **réalisé le 15 août** — deux
   campagnes sans erreur (20/20 puis 40/40), p50/p95/p99 et persistance
   `analysis_run` vérifiés. Voir
   `AUDIT_PERFORMANCE_ORCHESTRATION_2026-08-15.md`.
2. Archiver le rapport Bandit dans la CI lors du prochain run distant ; le
   contrôle local avec le même seuil que la CI est déjà vert.

Les tests unitaires et les garde-fous Docker sont exécutés. L’interpréteur
géré par `uv` reste sensible aux ACL locales ; les campagnes reproductibles
utilisent directement l’environnement `.venv` quand cela est nécessaire.

## Cloisonnement

Aucune base de test, benchmark ou production n’a été mélangée par cette passe.
Les conteneurs temporaires Testcontainers ont été supprimés automatiquement ;
aucune promotion ni décision de capacité n’est déduite de cette campagne.
