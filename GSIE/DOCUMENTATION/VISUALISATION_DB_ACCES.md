# Outils de visualisation de base de données — accès

> Date : 2026-08-01
> Décision associée : DEC-000040 (Treekipedia + visualisation)
> Veille : `GSIE/RESEARCH/VEILLE_OUTILS_VISUALISATION_DB_2026-07-31.md`
> Compose : `GSIE/docker-compose.viz.yml`

---

## 1. Outils déployés

| Outil | Rôle | URL | Conteneur |
|---|---|---|---|
| **Metabase** | BI self-service (non-tech) | http://localhost:3030 | `gsie-metabase` |
| **Apache Superset** | BI avancée (SQL Lab, dashboards) | http://localhost:8088 | `gsie-superset` |
| **Dekart** | Carto web Kepler.gl (PostGIS) | http://localhost:8089 | `gsie-dekart` |

Tous les ports sont liés à `127.0.0.1` (pas d'exposition externe).

---

## 2. Identifiants

> **Les mots de passe ne sont jamais commités dans le dépôt.**
> Ils sont lus depuis les variables d'environnement du fichier
> `GSIE/.env` (non versionné). Voir `GSIE/.env.example` pour les clés.

### Superset

| Champ | Valeur |
|---|---|
| URL | http://localhost:8088 |
| Utilisateur | `admin` |
| Mot de passe | `GSIE_SUPERSET_ADMIN_PASSWORD` (voir `.env`) |

La connexion DB « GSIE PostGIS » est pré-configurée via CLI
(`superset set-database-uri`).

### Metabase

| Champ | Valeur |
|---|---|
| URL | http://localhost:3030 |
| Utilisateur | `GSIE_METABASE_ADMIN_EMAIL` (voir `.env`) |
| Mot de passe | `GSIE_METABASE_ADMIN_PASSWORD` (voir `.env`) |
| Source de données | « GSIE PostGIS » pré-configurée (sync complète, PG 16.14) |
| Setup | Initialisé via API `/api/setup` (admin + DB + locale fr) |

### Dekart

| Champ | Valeur |
|---|---|
| URL | http://localhost:8089 |
| Auth | Aucune (dev only) |
| Source de données | Pré-configurée : `postgresql://gsie_viz:••••@db:5432/gsie` |

---

## 3. Compte de base de données `gsie_viz`

Les trois outils se connectent à PostgreSQL via le compte **`gsie_viz`**,
créé par `docker/comptes-de-connexion.sql` et autorisé par la migration
Alembic `20260801_0025`.

| Propriété | Valeur |
|---|---|
| Rôle | `gsie_viz` (LOGIN, NOSUPERUSER, NOBYPASSRLS) |
| Groupe | `gsie_viz_lecture` (NOLOGIN) |
| Droits | `SELECT` sur `public` + 7 schémas de domaine |
| Schémas accessibles | `public`, `gsie_botanique`, `gsie_foret`, `gsie_gouvernance`, `gsie_climat`, `gsie_pedologie`, `gsie_hydro`, `gsie_feu` |
| Schémas **interdits** | `gsie_rgpd`, `gsie_rgpd_identites` (REVOKE explicite) |
| Mot de passe | Voir `GSIE/.env` → `GSIE_VIZ_DB_PASSWORD` |

> La barrière RGPD est en base, pas dans l'outil : un outil de BI ne
> peut pas défiler le pseudonymat, quel que soit le SQL soumis.

---

## 4. Commandes Docker

```bash
# Démarrer les outils de visualisation
cd GSIE
docker compose -f docker-compose.viz.yml --profile viz up -d

# Arrêter
docker compose -f docker-compose.viz.yml --profile viz down

# Voir les logs
docker compose -f docker-compose.viz.yml logs -f metabase
docker compose -f docker-compose.viz.yml logs -f superset
docker compose -f docker-compose.viz.yml logs -f dekart

# Statut
docker compose -f docker-compose.viz.yml --profile viz ps
```

---

## 5. Documentation du schéma

La doc du schéma est générée par un script SQL + Python (remplace
SchemaSpy qui est incompatible PG16 et tbls qui ne supporte pas
l'héritage class-table de PostgreSQL).

```bash
# 1. Extraire les métadonnées depuis PostgreSQL
docker cp GSIE/TOOLS/generate_schema_doc.sql api-db-1:/tmp/
docker exec api-db-1 psql -U gsie -d gsie -f /tmp/generate_schema_doc.sql
docker cp api-db-1:/tmp/schema_schemas.csv GSIE/TOOLS/
docker cp api-db-1:/tmp/schema_tables.csv GSIE/TOOLS/
docker cp api-db-1:/tmp/schema_columns.csv GSIE/TOOLS/

# 2. Assembler le markdown
python GSIE/TOOLS/generate_schema_doc.py
```

Résultat : `GSIE/DOCUMENTATION/SCHEMA_DB.md` — 120 tables, 2122
colonnes, 7 schémas documentés avec types, contraintes, commentaires et
tailles.

---

## 6. Architecture réseau

```
┌─────────────────────────────────────────────────────┐
│  Réseau Docker : api_default (bridge)               │
│                                                     │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐   │
│  │ Metabase  │    │ Superset  │    │  Dekart   │   │
│  │  :3030    │    │  :8088    │    │  :8089    │   │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘   │
│        │                │                │         │
│        └────────────────┼────────────────┘         │
│                         │                           │
│                  ┌──────┴──────┐                   │
│                  │  api-db-1   │                   │
│                  │  PostgreSQL │                   │
│                  │  16 + PGIS  │                   │
│                  │  + pgvector │                   │
│                  └─────────────┘                   │
└─────────────────────────────────────────────────────┘
```

Tous les conteneurs viz rejoignent le réseau `api_default` (déclaré
`external: true` dans le compose) et se connectent à la DB via le
hostname `db` (nom du service dans le compose de l'API).

---

## 7. Sécurité

- **Ports liés à 127.0.0.1** : aucun accès depuis l'extérieur
- **Profil `viz`** : les conteneurs ne démarrent pas avec `up -d` sans
  `--profile viz` (audit sécurité 2026-08-01, constat D)
- **Compte `gsie_viz`** : NOSUPERUSER, NOBYPASSRLS, SELECT seul
- **Schémas RGPD isolés** : REVOKE explicite sur `gsie_rgpd` et
  `gsie_rgpd_identites`
- **Clé de chiffrement Metabase** : `MB_ENCRYPTION_SECRET_KEY` configurée
  (les identifiants de sources sont chiffrés au repos)
- **Clé secrète Superset** : `SUPERSET_SECRET_KEY` configurée (signe les
  cookies de session)
- **CORS Dekart** : `DEKART_CORS_ORIGIN` restreint à `localhost:8089`
