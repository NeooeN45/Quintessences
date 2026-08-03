# Veille technologique GSIE — Outils de visualisation de base de données — 2026-07-31

## Objet

Recenser les outils de visualisation de base de données applicables à
GSIE (PostgreSQL 16 + PostGIS 3.4 + Apache AGE), pour l'exploration
analytique, la cartographie géospatiale et l'administration SQL. Cette
veille alimente le choix de la stack de visualisation de l'écosystème
Quintessences.

## Évaluation

### 1. BI / Dashboards (exploration analytique)

| Outil | Source | Licence | Prix | Pertinence GSIE | Action |
|---|---|---|---|---|---|
| Metabase | [metabase.com](https://www.metabase.com/) | Open source (AGPL) | Gratuit (OSS) / $100-575/mo (cloud) | Haute — self-service pour non-tech, connecteur PostgreSQL natif, RLS préservée | À évaluer (déploiement Docker) |
| Apache Superset | [superset.apache.org](https://superset.apache.org/) | Open source (Apache 2.0) | Gratuit | Haute — SQL Lab, 40+ chart types, 80+ connecteurs, scale petabyte | À évaluer (déploiement Docker) |
| Grafana | [grafana.com](https://grafana.com/) | Open source (AGPL) | Gratuit / $20/user/mo | Moyenne — déjà intégré pour métriques API (Prometheus), moins pour BI métier | Déjà présent (monitoring) |
| Redash | [redash.io](https://redash.io/) | Open source (BSD) | Gratuit | Basse — simple, orienté SQL, moins riche que Superset | Non retenu |
| Lightdash | [lightdash.com](https://lightdash.com/) | Open source (MIT) | Gratuit | Basse — utile seulement si dbt adopté | Non retenu |
| Evidence | [evidence.dev](https://evidence.dev/) | Open source (MIT) | Gratuit | Basse — code-first reporting, niche | Non retenu |
| Power BI | [powerbi.microsoft.com](https://powerbi.microsoft.com/) | Propriétaire | $10/user/mo | Basse — écosystème Microsoft, moins adapté | Non retenu |
| Tableau | [tableau.com](https://www.tableau.com/) | Propriétaire | $75-200k/an | Basse — cher, overkill pour GSIE | Non retenu |
| Basedash | [basedash.com](https://www.basedash.com/) | Propriétaire | $1000/mo | Basse — AI-native mais SaaS, pas self-hosted | Non retenu |
| Sigma Computing | [sigmacomputing.com](https://www.sigmacomputing.com/) | Propriétaire | Sur devis | Basse — SaaS, interface spreadsheet | Non retenu |

### 2. Carto / Géospatial (spécifique PostGIS)

| Outil | Source | Licence | Pertinence GSIE | Action |
|---|---|---|---|---|
| Kepler.gl | [kepler.gl](https://kepler.gl/) / [GitHub](https://github.com/keplergl/kepler.gl) | Open source (MIT) | Haute — rendu WebGL millions de points, agrégations spatiales, basé MapLibre + deck.gl. Idéal pour occurrences GBIF, incendies BDIFF, tuiles Treekipedia | À évaluer (intégration web) |
| Dekart | [dekart.xyz](https://github.com/dekart-xyz/dekart) / [dekart.dev](https://dekart.dev/) | Open source (AGPLv3) | Haute — backend SQL self-hosted pour Kepler.gl, connecteur PostgreSQL natif + MCP pour agents IA. Alternative self-hosted à CARTO/Felt | À évaluer (déploiement Docker) |
| deck.gl | [deck.gl](https://deck.gl/) | Open source (MIT) | Moyenne — librairie WebGL/WebGPU pour intégration custom (GeoSylva web, QGISIA) | À évaluer (intégration custom) |
| MapLibre GL JS 5 | [maplibre.org](https://maplibre.org/) | Open source (BSD) | Moyenne — basemap open source, WebGL2, successeur de Mapbox GL open | À évaluer (basemap Kepler.gl) |
| Felt | [felt.com](https://felt.com/) | Propriétaire (SaaS) | Basse — éditeur collaboratif SaaS, pas self-hosted | Non retenu |
| QGIS 3.40 | [qgis.org](https://qgis.org/) | Open source (GPL) | Haute — déjà utilisé via QGISIA, plugin Python, connecteur PostGIS natif | Déjà présent (via QGISIA) |
| CesiumJS | [cesium.com](https://cesium.com/) / [cesiumjs.org](https://cesiumjs.org/) | Open source (Apache 2.0) | Moyenne — globe 3D / 3D Tiles, pour le Hub UE5.8 | Déjà prévu (Hub UE5.8) |
| CARTO | [carto.com](https://carto.com/) | Propriétaire (SaaS) | Basse — SaaS, alternative commerciale à Dekart | Non retenu |
| Foursquare Studio | [location.foursquare.com](https://location.foursquare.com/) | Propriétaire (SaaS) | Basse — SaaS, basé sur Kepler.gl | Non retenu |
| Protomaps / PMTiles | [protomaps.com](https://protomaps.com/) / [GitHub](https://github.com/protomaps/PMTiles) | Open source (BSD/MIT) | Moyenne — format de tuiles vectorielles statique, single-file, idéal pour hosting léger | À évaluer (tuiles Treekipedia) |
| Mapeo | [mapeo.zone](https://mapeo.zone/) | Open source (MIT) | Basse — carto offline, orienté terrain communautaire | Non retenu |

### 3. Explorateurs SQL (administration + schéma)

| Outil | Source | Licence | Prix | Pertinence GSIE | Action |
|---|---|---|---|---|---|
| pgAdmin | [pgadmin.org](https://www.pgadmin.org/) | Open source | Gratuit | Moyenne — GUI officiel PostgreSQL, DDL complet, ERD, explain plan. v9.13 (mars 2026) | À évaluer (alternative DBeaver) |
| DBeaver | [dbeaver.io](https://dbeaver.io/) | Community OSS / Pro $11+/mo | Gratuit (CE) | Haute — polyvalent (90+ DBs), ERD visuel, import/export multi-format, extensions PostgreSQL (FDW, mat views) | Recommandé (exploration schéma 116 tables) |
| DataGrip | [jetbrains.com/datagrip](https://www.jetbrains.com/datagrip/) | Propriétaire | $229/an | Moyenne — excellent si déjà JetBrains, autocomplétion contextuelle | Optionnel (si licence JetBrains) |
| Beekeeper Studio | [beekeeperstudio.io](https://www.beekeeperstudio.io/) | OSS / $7/mo (AI) | Gratuit (CE) | Moyenne — UI intuitive, AI Shell pour requêtes NL, schema-aware | À évaluer (alternative moderne) |
| TablePlus | [tableplus.com](https://tableplus.com/) | Propriétaire | $99 one-time | Basse — Mac-first, léger | Non retenu |
| Navicat | [navicat.com](https://navicat.com/) | Propriétaire | $23/mo | Basse — cher, peu de valeur ajoutée vs DBeaver | Non retenu |
| SchemaSpy | [schemaspy.org](https://schemaspy.org/) / [GitHub](https://github.com/schemaspy/schemaspy) | Open source (LGPL) | Gratuit | Haute — générateur ERD statique HTML, documentation automatique du schéma | Recommandé (doc schéma 116 tables) |
| Mako | [mako.ai](https://mako.ai/) | Propriétaire | Freemium | Basse — web, NL queries, niche | Non retenu |
| QueryPlane | [queryplane.com](https://queryplane.com/) | Propriétaire | SaaS | Basse — AI-native app builder, SaaS | Non retenu |

## Stack recommandée pour GSIE

```text
Exploration SQL       : DBeaver Community (schéma 116 tables, ERD)
Documentation schéma : SchemaSpy (HTML statique auto-généré)
BI self-service      : Metabase (forestiers, non-tech)
BI avancée           : Apache Superset (data teams, SQL Lab)
Monitoring API       : Grafana (déjà intégré via Prometheus)
Carto web            : Kepler.gl + Dekart (occurrences, incendies, tuiles)
Carto desktop        : QGIS (déjà via QGISIA)
Globe 3D             : CesiumJS (déjà prévu Hub UE5.8)
Tuiles vectorielles  : Protomaps/PMTiles (hosting léger, tuiles Treekipedia)
```

Toute la stack recommandée est **open source** et **self-hostable** —
cohérent avec la philosophie GSIE. Les connexions directes à PostgreSQL
préservent la RLS (migrations `20260727_0004` + `20260728_0022/0023`).

## Sources documentaires

### Articles de comparaison

- [Metabase vs Superset vs Grafana (2026)](https://www.modern-datatools.com/compare/metabase-vs-superset-vs-grafana) — Modern DataTools
- [Best BI tools for PostgreSQL in 2026](https://www.basedash.com/blog/best-bi-dashboarding-tools-for-postgresql-2026) — Basedash
- [Apache Superset vs Metabase vs Grafana (2026)](https://bixtech.ai/apache-superset-vs-metabase-vs-grafana-2026-the-definitive-open-source-bi-and-analytics-guide/) — BixTech
- [Best open source BI tools compared 2026](https://www.basedash.com/blog/best-open-source-bi-tools-compared-2026) — Basedash
- [Metabase vs Apache Superset 2026](https://ossalt.com/guides/metabase-vs-apache-superset-2026) — OSSAlt

### Stack géospatiale

- [Geospatial Stack 2026 Deep Dive](https://www.youngju.dev/blog/culture/2026-05-16-geospatial-stack-2026-postgis-maplibre-mapbox-deckgl-kepler-protomaps-overture-h3-deep-dive.en) — PostGIS, MapLibre, deck.gl, Kepler.gl, Protomaps, Overture, H3, S2
- [Map & Geospatial Tools 2026](https://www.youngju.dev/blog/culture/2026-05-16-map-geospatial-tools-2026-mapbox-maplibre-deck-gl-leaflet-protomaps-felt-deep-dive.en) — Mapbox, MapLibre, deck.gl, Leaflet, ProtoMaps, Felt, QGIS, ArcGIS
- [Kepler.gl documentation](https://docs.kepler.gl/) — docs officielles
- [Dekart — backend for Kepler.gl](https://github.com/dekart-xyz/dekart) — GitHub
- [Foursquare Studio / FSQ Spatial Desktop](https://madewithmaplibre.com/products/foursquare/) — MapLibre

### Explorateurs PostgreSQL

- [Best PostgreSQL GUI Clients 2026](https://queryplane.com/docs/blog/top-postgresql-gui-clients) — QueryPlane
- [Beekeeper Studio — PostgreSQL client](https://www.beekeeperstudio.io/db/postgres-client/) — Beekeeper
- [PostgreSQL GUI Clients 2026](https://mako.ai/guides/postgresql-gui-client) — Mako
- [pgAdmin vs DBeaver](https://queryplane.com/blog/pgadmin-vs-dbeaver/) — QueryPlane
- [6 PostgreSQL Schema Diagram Tools](https://schemalens.net/blog/visualize-postgresql-schema) — SchemaLens

## Conditions avant adoption

1. **Validation de la licence** : vérifier la compatibilité avec la
   gouvernance Quintessences (AGPL → attention pour intégration, Apache 2.0
   et MIT → OK).
2. **Test de connexion** : valider la connexion directe à PostgreSQL GSIE
   avec RLS activée (rôles `gsie_app` / `gsie_readonly`).
3. **Déploiement Docker** : préférer un déploiement Docker Compose
   cohérent avec l'existant (`GSIE/API/docker-compose.yml`).
4. **Performance** : tester sur le volume cible (116 tables, millions
   de lignes après ingestion Treekipedia/GBIF).
5. **Traçabilité** : toute adoption formalisée par une DEC dans
   `03_DECISIONS/`.

## Prochaines étapes

- Évaluer Metabase + Superset en Docker Compose (BI)
- Évaluer Kepler.gl + Dekart en Docker (carto web)
- Générer la documentation du schéma avec SchemaSpy
- Comparer DBeaver vs pgAdmin pour l'exploration quotidienne
- Formaliser le choix par une DEC si adoption

## Liens

- `GSIE/API/docker-compose.yml` — stack Docker existante
- `GSIE/API/alembic/versions/20260727_0004_rls_tables_sensibles.py` — RLS
- `GSIE/API/alembic/versions/20260728_0022_roles_par_moteur.py` — rôles par moteur
- `22_PROJECT_MEMORY/analyses/ANALYSE_CONCURRENTIELLE_2026-07-31.md` — analyse concurrentielle (§4.10 déploiement)
