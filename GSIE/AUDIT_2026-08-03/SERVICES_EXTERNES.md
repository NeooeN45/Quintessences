# Services externes — GSIE Server

**Date** : 2026-08-03
**Objet** : Liste exhaustive des services externes auxquels le Fondateur de Quintessences doit se connecter pour faire fonctionner le GSIE Server en production.
**Audience** : Fondateur / opérateur de mise en production.

---

## Tableau de synthèse

| # | Service | URL d'inscription | Statut |
|---|---|---|---|
| 1 | Cloudflare Tunnel | <https://dash.cloudflare.com> | Requis |
| 2 | Google Cloud Console (OAuth OIDC) | <https://console.cloud.google.com> | Requis |
| 3 | Météo-France API | <https://portail-api.meteofrance.fr> | Requis |
| 4 | GBIF | <https://www.gbif.org/developer/summary> | Optionnel |
| 5 | PlantNet (Pl@ntNet) | <https://my.plantnet.org> | Requis |
| 6 | IGN (Géoplateforme) | <https://geoservices.ign.fr> | Requis |
| 7 | SoilGrids (ISRIC) | <https://rest.isric.org> | Optionnel |
| 8 | Treekipedia | <https://trekipedia.org> | Optionnel |
| 9 | Wikimedia Commons | <https://commons.wikimedia.org> | Optionnel |
| 10 | SMTP (email transactionnel) | Selon prestataire | Requis |
| 11 | PostgreSQL 16 + PostGIS 3.4 + Apache AGE | Self-hosted / prestataire | Requis |
| 12 | Redis 7.2 | Self-hosted / prestataire | Requis |
| 13 | OpenTelemetry | Selon prestataire | Optionnel |
| 14 | Prometheus | Self-hosted / prestataire | Optionnel |

---

## 1. Cloudflare Tunnel

Tunnel sécurisé permettant d'exposer l'API GSIE sur Internet sans ouvrir de ports sur le serveur hôte. Le trafic entrant transite par l'infrastructure Cloudflare, qui injecte l'en-tête `CF-Connecting-IP` utilisé par le rate limiter pour identifier l'IP réelle du client.

- **Inscription / connexion** : <https://dash.cloudflare.com>
- **Documentation** : <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/>
- **Usage dans GSIE** : exposition de l'API en production ; résolution de l'IP client dans `core/limiter.py` et `core/config.py`.
- **Secrets à récupérer** :
  - `CLOUDFLARE_TUNNEL_TOKEN`
- **Configuration** :
  1. Créer un compte Cloudflare et ajouter le domaine `quintessences.com`.
  2. Naviguer vers **Networks** → **Tunnels** → **Create a tunnel**.
  3. Nommer le tunnel (ex. `gsie-prod`), copier le token généré.
  4. Configurer le hostname (ex. `api.gsie.quintessences.com`) vers le service local `http://localhost:8000`.
  5. Vérifier que l'en-tête `CF-Connecting-IP` est bien transmis (activé par défaut).
- **Variables `config.py`** : `cloudflare_tunnel_enabled`, `cf_connecting_ip_header`.

---

## 2. Google Cloud Console (OAuth OIDC)

Fournisseur d'identité OIDC pour l'authentification Google du compte Quintessences. GSIE valide les ID tokens Google et émet ses propres sessions.

- **Inscription / connexion** : <https://console.cloud.google.com>
- **Documentation** : <https://developers.google.com/identity/openid-connect/openid-connect>
- **Usage dans GSIE** : authentification OIDC dans `auth/google_identity.py` et `auth/google_nonces.py`.
- **Secrets à récupérer** :
  - `GOOGLE_OAUTH_CLIENT_ID`
  - `GOOGLE_OAUTH_CLIENT_SECRET`
- **Configuration** :
  1. Créer un projet Google Cloud (ex. `quintessences-gsie`).
  2. Activer l'écran de consentement OAuth (**APIs & Services** → **OAuth consent screen**).
  3. Créer des identifiants OAuth 2.0 de type **Web application**.
  4. Ajouter l'URI de redirection autorisée : `https://api.gsie.quintessences.com/api/v1/auth/google/callback`.
  5. Copier le Client ID et le Client Secret.
- **Variables `config.py`** : `google_oauth_client_id`, `google_oauth_client_secret`, `google_oauth_issuer`.

---

## 3. Météo-France API

Fournisseur de données climatiques pour le Climate Engine. Six clients distincts couvrent les différents produits Météo-France.

- **Inscription / connexion** : <https://portail-api.meteofrance.fr>
- **Documentation** : <https://portail-api.meteofrance.fr/web/en/api>
- **Usage dans GSIE** : Climate Engine (`engines/climate/`), 6 clients.
- **Secrets à récupérer** :
  - `METEOFRANCE_API_KEY`
  - `METEOFRANCE_API_SECRET`
- **Endpoints utilisés** :

  | Produit | Source | Clé requise |
  |---|---|---|
  | SYNOP | data.gouv.fr (licence ouverte 2.0) | Non |
  | AROME | API Météo-France | Oui |
  | DPClim | API Météo-France (flux asynchrone) | Oui |
  | Vigilance | API Météo-France | Oui |
  | Météo des forêts | API Météo-France | Oui |
  | Package Observations | API Météo-France | Oui |

- **Configuration** :
  1. Créer un compte sur le portail API Météo-France.
  2. Demander l'accès aux API AROME, DPClim, Vigilance, Météo des forêts et Package Observations.
  3. Copier la clé et le secret dans les variables d'environnement.
- **Variables `config.py`** : `meteofrance_api_key`, `meteofrance_api_secret`.

---

## 4. GBIF (Global Biodiversity Information Facility)

Résolution taxonomique pour le Botanical Engine. L'API publique ne requiert pas de clé.

- **Inscription / connexion** : <https://www.gbif.org/developer/summary>
- **Documentation** : <https://www.gbif.org/api>
- **Usage dans GSIE** : Botanical Engine (`engines/botanical/gbif_client.py`).
- **Secrets à récupérer** : aucun (API publique, rate limiting par IP). Clé optionnelle pour un usage intensif au-delà des limites par IP.
- **Configuration** : aucune configuration côté GSIE. En cas d'usage intensif, créer un compte GBIF et demander une clé d'API.
- **Variables `config.py`** : aucune.

---

## 5. PlantNet (Pl@ntNet)

Identification botanique par image pour le Botanical Engine.

- **Inscription / connexion** : <https://my.plantnet.org>
- **Documentation** : <https://my.plantnet.org/account/doc>
- **Usage dans GSIE** : Botanical Engine (`engines/botanical/plantnet_client.py`).
- **Secrets à récupérer** :
  - `PLANTNET_API_KEY`
- **Configuration** :
  1. Créer un compte sur <https://my.plantnet.org>.
  2. Souscrire à une offre d'API (free tier disponible avec quotas).
  3. Copier la clé d'API dans la variable d'environnement.
- **Variables `config.py`** : `plantnet_api_key`.

---

## 6. IGN (Institut Géographique National)

Données géospatiales pour le GIS Engine : cadastre, altimétrie, BD Forêt, BD TOPO, ADMIN-EXPRESS-COG, LiDAR HD. Trois clients distincts couvrent les différents services IGN.

- **Inscription / connexion** : <https://geoservices.ign.fr>
- **Documentation** : <https://geoservices.ign.fr/documentation>
- **Usage dans GSIE** : GIS Engine (`engines/gis/`), 3 clients.
- **Secrets à récupérer** :
  - `IGN_API_KEY` (clé Géoplateforme)
- **Endpoints utilisés** :

  | Service | Produit |
  |---|---|
  | API Carto | Cadastre |
  | API Calcul altimétrique | RGE ALTI |
  | Géoplateforme | BD Forêt, BD TOPO, ADMIN-EXPRESS-COG, LiDAR HD (téléchargement) |

- **Configuration** :
  1. Créer un compte sur <https://geoservices.ign.fr>.
  2. Générer une clé Géoplotteforme dans l'espace personnel.
  3. Vérifier que la clé couvre les services API Carto, Calcul altimétrique et Géoplateforme.
- **Variables `config.py`** : `ign_api_key`.

---

## 7. SoilGrids (ISRIC)

Données pédologiques globales (pH, texture, matière organique) pour le Pedology Engine. API REST publique sans authentification.

- **Inscription / connexion** : <https://rest.isric.org>
- **Documentation** : <https://www.isric.org/explore/soilgrids/faq-soilgrids>
- **Usage dans GSIE** : Pedology Engine (`engines/pedology/soilgrids_client.py`).
- **Secrets à récupérer** : aucun (API REST publique, rate limiting par IP).
- **Configuration** : aucune configuration côté GSIE.
- **Variables `config.py`** : aucune.

---

## 8. Treekipedia

Catalogue d'espèces forestières pour le Botanical Engine. Un fallback CSV local est disponible si l'API est indisponible ou si aucune clé n'est configurée.

- **Inscription / connexion** : <https://trekipedia.org>
- **Documentation** : <https://trekipedia.org/api>
- **Usage dans GSIE** : Botanical Engine (`engines/botanical/trekipedia_client.py`).
- **Secrets à récupérer** :
  - `TREEKIPEDIA_API_KEY` (optionnel — fallback CSV local en l'absence de clé)
- **Configuration** : créer un compte sur <https://trekipedia.org> et demander une clé d'API. Sans clé, GSIE utilise le fichier CSV local de fallback.
- **Variables `config.py`** : `trekipedia_api_key` (optionnel).

---

## 9. Wikimedia Commons

Images et extraits Wikipédia pour les espèces botaniques et forestières. API publique sans authentification.

- **Inscription / connexion** : <https://commons.wikimedia.org>
- **Documentation** : <https://www.mediawiki.org/wiki/API:Main_page>
- **Usage dans GSIE** : Botanical Engine (`engines/botanical/wikimedia_client.py`).
- **Secrets à récupérer** : aucun (API publique, rate limiting par IP).
- **Configuration** : aucune configuration côté GSIE. Respecter le User-Agent obligatoire (GSIE/1.0).
- **Variables `config.py`** : aucune.

---

## 10. SMTP (email transactionnel)

Envoi des codes de vérification email et des liens de réinitialisation de mot de passe. Le prestataire SMTP est au choix du Fondateur (Mailgun, SendGrid, Amazon SES, etc.).

- **Inscription / connexion** : selon le prestataire choisi :
  - Mailgun : <https://www.mailgun.com>
  - SendGrid : <https://sendgrid.com>
  - Amazon SES : <https://aws.amazon.com/ses/>
- **Documentation** : selon le prestataire.
- **Usage dans GSIE** : authentification (`auth/transactional_email.py`).
- **Secrets à récupérer** :
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`
  - `SMTP_FROM_EMAIL`
- **Configuration** :
  1. Choisir un prestataire SMTP transactionnel.
  2. Créer un compte et vérifier le domaine d'envoi (`quintessences.com`).
  3. Récupérer les identifiants SMTP fournis par le prestataire.
  4. Définir l'adresse d'expédition (ex. `noreply@quintessences.com`).
- **Variables `config.py`** : `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_from_email`.
- **Alternative développement** : Mailpit (conteneur Docker, port 1025) via `docker-compose`.

---

## 11. PostgreSQL 16 + PostGIS 3.4 + Apache AGE

Base de données principale de GSIE. Combine données relationnelles, géospatiales (PostGIS), graphe (Apache AGE) et vectorielles (pgvector).

- **Inscription / connexion** : self-hosted (Docker) ou prestataire managé (Supabase, Neon, Tembo, etc.).
- **Documentation** :
  - PostgreSQL : <https://www.postgresql.org/docs/16/>
  - PostGIS : <https://postgis.net/documentation/>
  - Apache AGE : <https://age.apache.org/>
- **Usage dans GSIE** : persistance principale (`infrastructure/database.py`).
- **Secrets à récupérer** :
  - `DATABASE_URL` (format : `postgresql+asyncpg://user:pass@host:port/dbname`)
- **Extensions requises** : `postgis`, `age`, `pgvector`.
- **Configuration** :
  1. Déployer une instance PostgreSQL 16.
  2. Installer les extensions `postgis`, `age` et `pgvector`.
  3. Créer la base de données GSIE et un utilisateur dédié.
  4. Construire l'URL de connexion au format `asyncpg`.
  5. En production, activer le SSL (`db_ssl_mode`).
- **Variables `config.py`** : `database_url`, `db_ssl_mode`, `db_pgbouncer_mode`.

---

## 12. Redis 7.2

Cache distribué, Pub/Sub WebSocket, stockage des refresh tokens, des nonces Google et du rate limiting.

- **Inscription / connexion** : self-hosted (Docker) ou prestataire managé (Upstash, Redis Cloud, etc.).
- **Documentation** : <https://redis.io/docs/>
- **Usage dans GSIE** : cache et coordination (`infrastructure/redis_client.py`).
- **Secrets à récupérer** :
  - `REDIS_URL` (format : `redis://user:pass@host:port/0`)
- **Configuration** :
  1. Déployer une instance Redis 7.2.
  2. Activer l'authentification par mot de passe (ACL).
  3. En production, activer TLS.
  4. Construire l'URL de connexion.
- **Variables `config.py`** : `redis_url`.

---

## 13. OpenTelemetry (observabilité)

Traces distribuées pour l'observabilité de l'API et des moteurs GSIE. Le collector OTLP peut être self-hosted ou délégué à un prestataire.

- **Inscription / connexion** : selon le prestataire choisi :
  - Honeycomb : <https://ui.honeycomb.io>
  - Grafana Cloud : <https://grafana.com>
  - Datadog : <https://www.datadoghq.com>
- **Documentation** : <https://opentelemetry.io/docs/>
- **Usage dans GSIE** : traces distribuées (`core/logging.py`).
- **Secrets à récupérer** :
  - `OTEL_EXPORTER_OTLP_ENDPOINT` (endpoint du collector OTLP)
  - En-tête d'authentification du prestataire (ex. `OTEL_EXPORTER_OTLP_HEADERS`)
- **Configuration** :
  1. Choisir un prestataire ou déployer un collector OTLP self-hosted.
  2. Créer un dataset / service nommé `gsie-server`.
  3. Récupérer l'endpoint OTLP et le token d'authentification.
- **Variables `config.py`** : `otel_exporter_otlp_endpoint`, `otel_service_name`.

---

## 14. Prometheus (métriques)

Métriques custom GSIE : complétude de la base de données, fraîcheur des données, cohérence référentielle. Prometheus scrape l'endpoint `/metrics` exposé par l'API.

- **Inscription / connexion** : self-hosted ou prestataire managé :
  - Grafana Cloud : <https://grafana.com>
  - Self-hosted : <https://prometheus.io/download>
- **Documentation** : <https://prometheus.io/docs/>
- **Usage dans GSIE** : métriques de qualité de données (`metrics/db_quality.py`).
- **Secrets à récupérer** : aucun côté API (Prometheus scrape l'endpoint `/metrics` en pull).
- **Configuration** :
  1. Déployer une instance Prometheus (ou utiliser Grafana Cloud).
  2. Configurer un job de scrape ciblant `https://api.gsie.quintessences.com/metrics`.
  3. Définir l'intervalle de scrape (ex. 60 s).
  4. Configurer des alertes sur les métriques de complétude et de fraîcheur.
- **Variables `config.py`** : aucune (endpoint `/metrics` exposé par l'API).

---

## Checklist de mise en production

Ordre recommandé de configuration. Les étapes 1 à 5 sont les prérequis infrastructure ; les étapes 6 à 10 concernent les API métier ; les étapes 11 à 14 concernent l'observabilité.

- [ ] **1. PostgreSQL 16 + PostGIS + Apache AGE** — déployer la base, installer les extensions, créer `DATABASE_URL`.
- [ ] **2. Redis 7.2** — déployer l'instance, activer l'auth, créer `REDIS_URL`.
- [ ] **3. SMTP** — choisir un prestataire, vérifier le domaine, récupérer les identifiants.
- [ ] **4. Cloudflare Tunnel** — créer le tunnel, configurer le hostname, récupérer `CLOUDFLARE_TUNNEL_TOKEN`.
- [ ] **5. Google Cloud Console** — créer le projet OAuth, configurer l'URI de redirection, récupérer `GOOGLE_OAUTH_CLIENT_ID` et `GOOGLE_OAUTH_CLIENT_SECRET`.
- [ ] **6. Météo-France API** — créer le compte, demander les accès, récupérer `METEOFRANCE_API_KEY` et `METEOFRANCE_API_SECRET`.
- [ ] **7. IGN** — créer le compte, générer la clé Géoplateforme, récupérer `IGN_API_KEY`.
- [ ] **8. PlantNet** — créer le compte, souscrire à l'API, récupérer `PLANTNET_API_KEY`.
- [ ] **9. Treekipedia** (optionnel) — créer un compte, récupérer `TREEKIPEDIA_API_KEY`.
- [ ] **10. GBIF / SoilGrids / Wikimedia** — aucun secret requis, vérifier la connectivité.
- [ ] **11. OpenTelemetry** (optionnel) — choisir un prestataire, configurer `OTEL_EXPORTER_OTLP_ENDPOINT`.
- [ ] **12. Prometheus** (optionnel) — déployer l'instance, configurer le job de scrape `/metrics`.
- [ ] **13. Tests de connectivité** — lancer l'API avec toutes les variables d'environnement et vérifier les healthchecks.
- [ ] **14. Validation end-to-end** — authentification Google, envoi email, requête météo, requête IGN, identification PlantNet.

---

## Variables d'environnement complètes

Tableau récapitulatif de toutes les variables d'environnement à définir en production.

| Variable | Service | Requise | Format / exemple |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL | Oui | `postgresql+asyncpg://user:pass@host:5432/gsie` |
| `REDIS_URL` | Redis | Oui | `redis://user:pass@host:6379/0` |
| `SMTP_HOST` | SMTP | Oui | `smtp.mailgun.org` |
| `SMTP_PORT` | SMTP | Oui | `587` |
| `SMTP_USERNAME` | SMTP | Oui | `postmaster@quintessences.com` |
| `SMTP_PASSWORD` | SMTP | Oui | `••••••••` |
| `SMTP_FROM_EMAIL` | SMTP | Oui | `noreply@quintessences.com` |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare | Oui | `••••••••` |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Cloud | Oui | `••••••••.apps.googleusercontent.com` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Cloud | Oui | `••••••••` |
| `METEOFRANCE_API_KEY` | Météo-France | Oui | `••••••••` |
| `METEOFRANCE_API_SECRET` | Météo-France | Oui | `••••••••` |
| `IGN_API_KEY` | IGN | Oui | `••••••••` |
| `PLANTNET_API_KEY` | PlantNet | Oui | `••••••••` |
| `TREEKIPEDIA_API_KEY` | Treekipedia | Non | `••••••••` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry | Non | `https://api.honeycomb.io` |
| `OTEL_EXPORTER_OTLP_HEADERS` | OpenTelemetry | Non | `x-honeycomb-team=••••••••` |
| `OTEL_SERVICE_NAME` | OpenTelemetry | Non | `gsie-server` |

**Note** : les variables marquées « Non » sont optionnelles. GSIE fonctionne sans elles, avec des fonctionnalités dégradées (fallback CSV pour Treekipedia, absence de traces pour OpenTelemetry).
