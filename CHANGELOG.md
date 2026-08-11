# CHANGELOG — Quintessences / GSIE

Format : `## [version] - YYYY-MM-DD`

---

## [ARCHITECTURE — DURABILITÉ ÉVOLUTIVE ET INTÉGRATION IA] - 2026-08-10

- Création de `GSIE-ARCH-EVOLUTION-001` en statut Draft pour formaliser les
  migrations expand/backfill/contract, la compatibilité API, le versionnement
  scientifique, l'invalidation des données dérivées, la fraîcheur, les licences,
  la performance et les portes de qualité.
- Définition du benchmark propriétaire GSIE : scénarios versionnés, baselines
  non-IA et expertes, vérités terrain, mesures par sous-groupe, prévention des
  fuites et garde de promotion.
- Définition de la frontière d'intégration des modèles IA spécialisés après la
  bêta fonctionnelle : entrées GSIE versionnées, sorties typées, incertitude,
  provenance, shadow mode, validation humaine et rollback.

## [GSIE DATA PLATFORM — QUALITÉ TECHNIQUE ET PORTE FETCH] - 2026-08-10

- Politique `registry-quality-1` : cinq dimensions, aucun score global pour
  un bilan incomplet et séparation stricte de la santé et de l'Evidence Level.
- Migration réversible `20260810_0048` pour les campagnes append-only et les
  contraintes de score, poids et unicité par dimension.
- Resolver et recherche alimentés uniquement par les évaluations persistées,
  sans confiance implicite dans `DatasetVersion.stats`.
- Suppression du dernier fallback `quality_score_from_stats` dans le resolver
  pur et ajout d'une non-régression prouvant que `stats.quality_score` est ignoré.
- Évaluation reproductible des quatre sources : manifeste complet et cohérent,
  mais trois dimensions non mesurées, donc aucune promotion.
- Worker FETCH fail-closed ajouté ; les quatre sources restent désactivées et
  aucun appel adapter, téléchargement RAW ou changement de statut n'a lieu.
- Migration 0048 appliquée sur PostgreSQL Docker réel ; contraintes d'unicité
  et de score vérifiées dans une transaction annulée.
- CRUD générique fermé pour les promotions STAGING/PRODUCTION : un futur
  service dédié devra vérifier qualité, droits, actif RAW et opérateur.
- Qualification SoilGrids approfondie : licence CC BY 4.0 confirmée, mais API
  REST officiellement en pause ; candidat WCS borné préparé sans activer FETCH.
- Contrat WCS fermé ajouté : endpoint fixe, 12 propriétés, six profondeurs,
  quatre sorties, EPSG:152160, GeoTIFF INT16, 1 Mpx, 8 Mio et 30 secondes.
- Sonde TLS réelle maintenue fail-closed face à l'interception antivirus ;
  aucune désactivation de certificat et aucune activation FETCH.
- Récepteur FETCH transactionnel ajouté : MIME, `Content-Length`, octets réels,
  timeout global et SHA-256 contrôlés avant `commit`, avec `abort` sur erreur.
- Aucun raccordement MinIO ni `DataAsset RAW` tant que la source reste fermée.
- Campagne élargie du worker : 56/56 tests, head PostgreSQL 0048 et contraintes
  SQL rejouées sous transaction annulée ; rapport de preuve versionné.
- Sink ObjectStorage/MinIO transactionnel : spool privé, clé RAW non écrasable,
  publication au commit seulement et timeout propre autour de `abort()`.
- Round-trips MinIO réels commit/relecture/suppression et abort sans publication
  validés ; nettoyage anti-orphelin après commit ambigu et 96 tests passants.
- Les `HEAD 404` attendus par `ObjectStorage.exists()` ne remontent plus comme
  erreurs d'exploitation ; les autres échecs S3 restent journalisés et propagés.
- Image candidate `gsie-api:quality-0048` reconstruite et smoke-testée, sans
  redéploiement de l'API active et sans activation de FETCH.
- Sonde TLS SoilGrids réelle réussie : WCS 2.0, EPSG:152160 et résolution
  250 m confirmés. Divergence identifiée entre le code métier `wv003` et le
  service actif `wv0033` ; aucun `GetCoverage` exécuté.
- Mapping contractuel `wv003` vers `wv0033` ajouté pour l'accès WCS, sans
  modifier l'identifiant métier ni ouvrir l'allowlist à `wv0033` ; 99 tests
  Data Registry/FETCH passants.
- DEC-000061 : premier `GetCoverage` SoilGrids réel exécuté sur 100 pixels ;
  569 octets vérifiés par SHA-256, DataAsset RAW unique publié dans MinIO et
  version maintenue à l'état `discovered` sans promotion automatique.
- DEC-000062 : API et worker redéployés depuis `6986e80`, migration 0048,
  fail-closed, manifeste idempotent et DataAsset TIFF MinIO revérifiés. Charge
  stable à 100 % de succès, avec un plafond local d'environ 19 req/s à profiler.
- DEC-000063 : le port publié Docker Desktop est identifié comme goulot local
  principal (23,4 req/s contre 405,1 req/s dans le réseau Docker). Le recyclage
  Gunicorn passe de 1000/50 à 5000/5000, devient configurable et refuse les
  valeurs non positives ; 6 000/6 000 requêtes internes réussissent à
  669,34 req/s, p95 11,47 ms. La haute disponibilité multi-réplicas reste à
  qualifier sous Linux avant toute annonce de capacité de production.
- DEC-000064 : banc HA Linux conteneurisé à deux replicas derrière HAProxy,
  readiness de drainage privée, résolution DNS dynamique et grâce de 45 s.
  Drainage : 6 000/6 000 succès ; rechargements séquencés : 8 000/8 000 ;
  lecture PostgreSQL authentifiée : 100/100. Les essais volontairement mal
  séquencés prouvent que le retour explicite du backend est une porte
  obligatoire. Les SLO de production restent non publiés.
- DEC-000065 : workflow GitHub Actions Ubuntu pour reconstruire la plateforme,
  terminer TLS avec une CA éphémère vérifiée, drainer un replica sous 6 000
  requêtes et bloquer sur statuts, erreurs, p95, p99 ou débit. Le câblage TLS
  local passe 500/500 ; la preuve distante attend le premier run après push.

## [GSIE DATA PLATFORM — CLÔTURE TECHNIQUE DATA REGISTRY] - 2026-08-10

- Ajout d'une commande reproductible unique pour les trois campagnes de
  validation, avec rapport JSON horodaté : 151 tests Data Registry, 103 P0/P1
  et 121 infrastructure/lifespan.
- Ajout du job CI obligatoire PostgreSQL/PostGIS/AGE + MinIO : migrations,
  application/rejeu du manifeste, round-trip S3, SHA-256 et nettoyage.
- Ajout du scheduler périodique de santé : verrou Redis avec jeton/TTL,
  concurrence et tailles bornées, métriques Prometheus et historique
  `DatasetHealth`. Il reste désactivé par défaut.
- Ajout de `FETCH_QUALIFICATION.json` et d'une porte fail-closed. GBIF, IGN,
  SoilGrids et Météo-France restent fermés jusqu'à levée de leurs blocages
  juridiques ou techniques propres.
- Reconstruction des trois images et redéploiement API/outbox. `/health` et
  `/ready` sont sains ; le smoke réel confirme le head `20260810_0047`, le
  rejeu idempotent et le nettoyage MinIO.
- Preuve :
  `GSIE/API/docs/data/GSIE_DATA_REGISTRY_CLOTURE_2026-08-10.md`.

## [GSIE DATA PLATFORM — MANIFESTE APPLIQUÉ ET SANTÉ PERSISTÉE] - 2026-08-10

- Ajout de `ManifestRegistryService` et du CLI
  `scripts/apply_dataset_manifest.py` : `dry-run` par défaut, transaction
  explicite, identifiants stables et rejeu idempotent.
- Projection complète des quatre entrées vers Agent, Source, EntityAlias,
  droits, Dataset, DatasetVersion, Distribution et Citation : 32 ressources
  créées, puis rejeu à 0 création/0 mise à jour.
- Ajout de `scripts/collect_manifest_health.py` ; contrôle TLS réel 4/4
  `healthy`, quatre `DatasetHealth` persistés, rejeu identique sans doublon.
- Migration `20260810_0047` et durcissement de `0046` : enums Registry
  déterministes dans `public`. Cycle réel sur base jetable
  `upgrade head → downgrade 0044 → upgrade head` validé.
- Correction des blocages de revue : paquet `gsie_api.data` sans réexports,
  test d'import en processus froid, bytes UTF-8 valide et Ruff/mypy verts.
- Refactor des validateurs DataAsset/DatasetVersion par invariant ; fermeture
  symétrique des fichiers temporaires en erreur.
- Réutilisation d'un client/pool aiobotocore S3 par instance, singleton
  applicatif et fermeture propre au shutdown FastAPI.
- Preuves initiales : 136 tests Data Registry, 103 tests P0/P1 et 121 tests
  cycle de vie/infrastructure, tous passants. Documentation :
  `GSIE/API/docs/data/GSIE_DATA_REGISTRY_MANIFEST_APPLICATION_2026-08-10.md`.

## [OUTILLAGE — SITE DES GRAPHES MERMAID ENRICHI] - 2026-08-10

- Extension de `graphes-quintessences/` de 5 à **13 diagrammes** répartis en
  **4 catégories** (Écosystème, Gouvernance, Progression, Infrastructure) :
  ajout du métamodèle Encyclopédie, des applications clientes, de l'identité
  Quintessences, du cycle de vie documentaire, de la chronologie des
  décisions structurantes, du pipeline Data Registry, du Server Meshing et
  du Territorial Mesh — tous sourcés depuis la documentation réelle
  (`README.md`, `PROJECT_MEMORY.md`, `03_DECISIONS/`, `GSIE/ARCHITECTURE/`).
- Refonte du site généré : sidebar par catégorie avec compteurs, puces de
  filtre combinées à la recherche, thème clair/sombre persistant (police
  Space Grotesk/Space Mono), zoom/pan par diagramme, vue plein écran,
  téléchargement SVG, bascule « voir le code source », badge de type de
  diagramme détecté automatiquement.
- `generate_site.py` réécrit (stdlib uniquement, ruff + mypy strict verts) ;
  `diagrams/meta.json` enrichi (`categorie`, `description`, `date_maj`).
- Port 4300 (évite conflits avec les autres services locaux).
- Skill Devin `.devin/skills/graphes-progression/SKILL.md` mis à jour avec
  la table de correspondance événement → diagramme à maintenir.

## [GSIE DATA PLATFORM — TEST E2E RÉEL] - 2026-08-10

- Ajout de `GSIE/API/scripts/test_data_registry_e2e.py` : campagne réelle
  bornée GBIF, IGN, SoilGrids et Météo-France, sans fixture ni réponse simulée.
- Vérification de bout en bout : santé fournisseur, acquisition, normalisation,
  projection métier, écriture/lecture MinIO avec égalité octet à octet et
  SHA-256, sélection `data-resolver-1`, puis nettoyage automatique.
- Résultat reproductible : 4/4 adapters sains, 96 départements Météo-France,
  `cleanup=ok` et aucun objet de test résiduel. Preuves :
  `GSIE/API/docs/data/GSIE_DATA_E2E_REAL_TEST_2026-08-10.md`.
- Correction de la politique MinIO Compose : le bucket est désormais injecté
  dans l'ARN généré (au lieu du littéral `%s`) et la politique est recréée de
  manière idempotente avant association au compte runtime.
- Limite explicitée : les adapters exposent encore `QUERY`/`NORMALIZE`, pas
  `FETCH`; l'archivage des octets bruts et la promotion `DataAsset` restent à
  planifier.

## [GSIE DATA PLATFORM — PHASE 6 MANIFESTE] - 2026-08-10

- Ajout du manifeste versionné `GSIE/DATASETS/REGISTRY_MANIFEST.json` pour
  GBIF, IGN, SoilGrids et Météo-France, sans téléchargement ni écriture DB.
- Ajout de la porte `gsie_api.ingestion.manifest` : identité dataset/version,
  vocabulaire de domaines, licence alignée sur SCI-001, URLs HTTPS sûres et
  distinction explicite `metadata_only` / `archive_copy`.
- Les sources restreintes ne peuvent pas franchir la porte de copie ; un pack
  hors ligne exige une copie et un droit de redistribution déclaré.
- Ajout du validateur CLI et de 12 tests unitaires ; Ruff et mypy strict
  passent. Documentation : `GSIE/API/docs/data/GSIE_DATA_MANIFEST_PHASE6.md`.
- Ajout de la page `/data` au site `GSIE/ADMIN_WEB` : catalogue réel,
  recherche, filtre par domaine et état vide explicable ; `astro check` sans
  erreur et build 13 routes validé.
- Audit du contrat GeoSylva : la synchronisation parcellaire existante reste
  isolée du Data Registry ; la future consommation mobile attend un manifeste
  de pack, une santé persistée et un checksum vérifié. Documentation :
  `GSIE/API/docs/data/GEOSYLVA_DATA_REGISTRY_MIGRATION_PHASE7.md`.

## [GSIE DATA PLATFORM — PHASE 5 RESOLVER] - 2026-08-10

- Ajout du `Data Selection Engine` déterministe et explicable dans
  `gsie_api.data.resolver`.
- Ajout de `POST /api/v1/data/resolve`, authentifié, rate-limitée et corrélée
  par trace ID ; aucun adapter ni téléchargement n'est déclenché.
- Contraintes évaluées avant score : statut, qualification Registry A–F,
  licence commerciale, qualité et archive ; blocages stables exposés.
- Préférences fraîcheur/qualité/offline et fallback opt-in soumis à une
  politique versionnée ; tests ciblés, Ruff et mypy strict passent.
- Documentation : `GSIE/API/docs/data/GSIE_DATA_RESOLVER_PHASE5.md`.

## [STABILISATION DOCKER + BOOTSTRAP DATA REGISTRY] - 2026-08-10

- Correction TLS des builds PostgreSQL/Apache AGE et API sous inspection HTTPS
  Kaspersky : certificat injecté uniquement par secret BuildKit éphémère,
  `UV_SYSTEM_CERTS=true` pour uv, sans désactivation de la validation.
- Ajout de `GSIE/API/scripts/build_images.ps1` et construction vérifiée des
  images `api-db`, `api-api` et `api-outbox-worker`.
- Correction du bloc `command` PostgreSQL, du démarrage Redis sous UID 999 et
  de l'initialiseur MinIO (shell POSIX, configuration temporaire et opérations
  idempotentes). Aucun volume n'a été supprimé.
- Vérification Docker : API `/health`/`/ready` 200, migration head
  `20260810_0046`, DB/Redis/MinIO/outbox/Mailpit/Uptime Kuma sains ; bucket et
  politique MinIO créés.
- Bootstrap explicite `gsie_api.data.bootstrap` pour GBIF, IGN, SoilGrids et
  Météo-France, campagne `AdapterHealthService` offline et tests ciblés verts.
  Les résultats ne sont pas encore persistés dans `DatasetHealth` sans
  distribution qualifiée.

## [GSIE DATA PLATFORM — PHASE 3 ADAPTERS] - 2026-08-10

- Contrat commun `DataSourceAdapter` livré avec capacités explicites :
  découverte, métadonnées, santé, requête, fetch et normalisation.
- `AdapterPluginRegistry` ajouté avec factories lazy, cache d’instances,
  refus des doublons et vérification des descripteurs retournés.
- Bornes de sécurité ajoutées : trace ID, timeout, taille maximale, allowlist
  d’hôtes, URLs sans identifiants/query/fragment et flux de fetch non chargés
  entièrement en mémoire.
- Aucun fournisseur ni appel réseau activé par défaut ; les façades IGN, GBIF,
  SoilGrids et Météo-France délèguent aux clients résilients existants et sont
  enregistrables uniquement par bootstrap explicite.
- 29 tests de contrat/façades passent (9 contrat + 20 fournisseurs), avec
  clients simulés et aucun appel externe ; Ruff et mypy strict passent.
- Docker relancé : migrations `20260809_0044` → `20260810_0046` appliquées,
  `20260810_0046` confirmé comme head et contraintes SQL vérifiées.

## [GSIE DATA PLATFORM — PHASE 2 DATA REGISTRY] - 2026-08-10

- Tranche read-only de RFC-0038 implémentée après validation de `DEC-000059`.
- Migration réversible `20260810_0046` : statuts `DatasetStatus`, domaines,
  tags, couverture temporelle, preuve, droits d’usage, santé par distribution
  et contraintes d’intégrité.
- Ajout des contrats/DTOs versionnés, du cycle de vie contrôlé, de la
  pagination par curseur opaque et de `DataRegistryService`.
- Routes authentifiées `/api/v1/data/catalog`, `datasets/{id}`, `providers`,
  `search`, `health` et `coverage`, avec RBAC, rate limiting, trace ID et
  masquage des URLs sensibles.
- Validation spécialisée intégrée au CRUD historique : transitions de statut,
  bornes santé, licence/preuve et clé composite distribution-version.
- 39 tests ciblés passent ; Ruff et mypy strict passent. Le smoke test
  PostgreSQL reste à exécuter lorsque Docker/Linux sera disponible.
- Adapters, scheduler de santé, cache partagé et resolver restent hors de la
  Phase 2.

## [DATASET/API — INTÉGRITÉ DES DATA ASSET] - 2026-08-10

- Le CRUD générique valide désormais les métadonnées `DataAsset` : taille
  entière non négative, checksum compatible avec l’algorithme déclaré, URI
  autorisées et refus des identifiants dans les URI.
- `size_bytes` est stocké en `BIGINT` avec la contrainte SQL
  `ck_data_asset_size_non_negative` (`20260810_0045`), pour couvrir les assets
  COG/COPC volumineux sans troncature.
- Le stockage local ne renvoie plus de chemin `file://` : il renvoie un URI
  opaque `local:///…` et refuse les URLs présignées. La suite unitaire complète
  passe : 2 703 tests, 63 ignorés et 100 % de couverture ; les deux tests
  PostgreSQL DataAsset attendent Docker.

## [BILAN HEBDOMADAIRE — TRAÇABILITÉ DES TRAVAUX] - 2026-08-10

- Ajout du bilan [`GSIE-WEEKLY-2026-08-03`](GSIE/DOCUMENTATION/BILAN_HEBDOMADAIRE_2026-08-03_2026-08-10.md).
- La chronologie relie les commits du 03 au 09 août et les changements du
  10 août encore présents dans l’espace de travail aux décisions, RFC,
  spécifications, fichiers de code et preuves de tests.
- Les statuts sont séparés entre livré, en revue et en attente ; le smoke test
  MinIO/Docker, les configurations opérateur et l’adoption de RFC-0038 restent
  explicitement ouverts.

## [AUDIT SÉCURITÉ — STOCKAGE OBJET ET COMPOSE] - 2026-08-10

- Désactivation de la journalisation des paramètres SQL par pgaudit pour ne pas
  exposer de données personnelles, jetons ou secrets dans les logs.
- Compte MinIO runtime séparé du compte racine et politique restreinte au bucket
  GSIE ; chiffrement serveur AES256 demandé lors des uploads S3.
- Les URLs présignées sont limitées à quinze minutes et le backend local ne
  divulgue plus de chemin `file://`.
- Métriques Cloudflared liées à `127.0.0.1`; 85 tests ciblés passent, Ruff et
  validation Compose sont verts. Rapport : `GSIE/API/docs/SECURITY_AUDIT_2026-08-10.md`.

## [GSIE DATA PLATFORM — OBJECT STORAGE MINIO/S3] - 2026-08-09

- Phase 1 du Data Registry livrée côté stockage objet dans `GSIE/API/`.
- `S3Storage` asynchrone compatible MinIO/AWS S3 via `aiobotocore==3.7.0`.
- Upload multipart par blocs, checksum SHA-256 en métadonnée, abandon sûr
  des uploads incomplets, lecture en flux, lecture par plage, HEAD,
  suppression et URLs présignées.
- `DataAsset` enrichi de `storage_uri` et `checksum_algorithm` par la
  migration réversible `20260809_0044`.
- MinIO ajouté au Compose de développement, avec ports limités à localhost,
  volume persistant, healthcheck et initialisation idempotente du bucket.
- Validation : 51 tests stockage/configuration, 112 tests infrastructure,
  ruff, mypy, migration head et `docker compose config` passants.
- Smoke test réseau réel reporté : le daemon Docker Desktop n’était pas
  disponible sur l’environnement Windows de développement.
- Veille externe intégrée au plan : STAC, COG, GeoParquet, COPC, Zarr,
  DuckDB, Iceberg et accélérations GPU optionnelles.

## [GSIE DATA PLATFORM — RFC-0038 DATA REGISTRY] - 2026-08-10

- Passe de logique de `RFC-0038` : v1.1.0 conserve le statut `Draft` et
  clarifie Agent/Source/Citation, couverture spatiale, droits de dataset
  séparés du RGPD, santé par distribution, transitions récupérables,
  qualification Registry A–F distincte des assertions, vocabulaire de domaines
  versionné et recherche déterministe par preuve/grain/licence.
- `DEC-000059` est alignée en `Draft` ; aucune adoption n’est anticipée avant
  la décision explicite du Fondateur.
- L’audit complémentaire passe en v1.4.0. Aucun endpoint Registry, adapter,
  resolver ou migration Phase 2 n’est appliqué avant adoption de la RFC.

## [GSIE DATA PLATFORM — ADOPTION RFC-0038] - 2026-08-10

- Validation formelle du Fondateur : `RFC-0038` v1.2.0 et `DEC-000059` passent
  à `Validated`.
- La Phase 2 Data Registry est autorisée par tranches : Registry, DTOs,
  recherche, health checks, adapters puis Data Selection Engine.
- Aucun code Registry, endpoint `/api/v1/data/*`, adapter ou resolver n’est
  ajouté par cette seule validation documentaire.
- L’audit architecture données est synchronisé en v1.5.0.

## [ORCHESTRE GSIE — CYCLES CVE, QA ET VEILLE] - 2026-08-09

- Cycle 2 Sécurité+Perf : audit `pip-audit` sur 138 packages, 24 CVE
  sur 7 packages, dont 6 HIGH ; escalade #001 résolue par l'option B.
- Cycle QA : 2667 tests passés, 63 ignorés, 100 % couverture,
  70/70 mutations détectées, ruff et mypy sans erreur.
- Cycle Veille : rapport `GSIE/RESEARCH/VEILLE_2026-08-09.md` produit
  sur six domaines ; aucune ressource téléchargée ou ingérée.
- Les workers de l'Orchestre utilisent désormais **SWE 1.7 max**.
- Escalade #001 résolue par l'option B : `pyjwt==2.13.0`,
  `python-multipart==0.0.32`, `cryptography==50.0.0`. Les tests ciblés
  auth/JWT/SSRF passent 60/60 ; l'audit pip-audit reste bloqué par TLS.
- Cycle 3 performance : `numpy.corrcoef` mesure 30x à 1521x plus rapide
  que scipy pairwise sur les matrices de corrélation GSIE.
- Qualification Starlette/FastAPI : l’upgrade coordonné est nécessaire
  pour corriger les CVE Starlette ; escalade #002 ouverte avant toute
  modification du framework public.
- Upgrade coordonné appliqué sur branche dédiée : FastAPI 0.134.0 et
  Starlette 0.52.1. Validation complète : 2667 tests passants, 100 %
  couverture, 70/70 mutations, ruff/mypy verts.
- Nettoyage FastAPI : suppression de l’ORJSONResponse global déprécié,
  remplacement de la constante 422 et suppression du warning Stripe ;
  warnings réduits de 187 à 3. Les trois restants sont des warnings
  `runpy` de tests de points d’entrée, sans régression fonctionnelle.
- Revalidation `pip-audit` dans le venv réel après correction TLS :
  Starlette 1.3.1 et toutes les dépendances HIGH sont propres. L'audit
  intermédiaire a identifié quatre avis sur trois packages ; ils ont été
  traités dans l'option A ci-dessous.
- Option A appliquée : `app-store-server-library==3.1.2`,
  `orjson==3.11.6`, `pytest==9.0.3` et `pytest-asyncio==1.3.0`.
  `pip-audit` est maintenant propre ; billing, suite complète, couverture,
  ruff et mypy sont validés.

## [SITE PUBLIC QUINTESSENCES — APPLICATIONS, COMPTE, FOND VIDÉO] - 2026-08-09

- **Hero** : titre réorganisé en 3 lignes lisibles au lieu d'un mot par
  ligne ; fond passé en vidéo de fond en boucle (`VideoBackdrop.astro`,
  fichier à fournir dans `public/video/`), dégradé animé conservé en
  repli si la vidéo est absente.
- **Titres animés génériques** : `AnimatedHeading.tsx` factorise
  l'animation du hero et l'applique à toutes les pages du site — même
  syntaxe visuelle partout, sans jamais fabriquer de contenu pour
  remplir une ligne manquante.
- **Chargement fantôme** : `Skeleton.tsx` (pulsation) appliqué aux
  indicateurs live et aux futures captures d'écran d'application.
- **QGISIA retiré** de la liste des applications, à la demande du
  Fondateur.
- **Nouvelle page `/applications/`** : une section détaillée par
  application (icône, domaine, description, statut, capture d'écran
  en réserve, lien Google Play — jamais de lien inventé, "Bientôt sur
  Google Play" par défaut).
- **Pages Compte fonctionnelles** : `/compte/inscription/`,
  `/compte/connexion/`, `/compte/` branchées sur les vrais endpoints
  `IDENTITE-001` (`/auth/register`, `/auth/login/password`,
  `/auth/me`, `/auth/logout`). Jetons en sessionStorage — limite déjà
  documentée en `SITE-001` §9, non résolue par ce changement.
- Vérifié par `npm run build` (13 pages) et navigation en direct.

## [SITE PUBLIC QUINTESSENCES — PIVOT THÈME CLAIR (PAPA CREATIVE)] - 2026-08-09

- **SITE-002 v1.1.0** : décision directe du Fondateur — thème clair
  exclusif (retrait du sombre par défaut de la v1.0.0), direction
  éditoriale inspirée de `papacreative.com` : typographie Space
  Grotesk + Space Mono, hero en titre empilé sur plusieurs lignes,
  légendes capitales très espacées, fiches applications façon
  « case study » (DOMAINE/STATUT au lieu de PROJECT TYPE/INDUSTRY).
  `SITE-001` `SITE-X-007` amendée en conséquence.
- **Implémentation** : `ThemeToggle` retiré, palette entièrement
  réécrite (fond quasi blanc, texte quasi noir, accent teal sombre
  `#00786a` utilisé avec parcimonie). Polices chargées via Google
  Fonts (`<link>`, pas `@import` CSS — évite un avertissement de build
  Tailwind sur l'ordre des règles).
- **Accessibilité** : contraste mesuré en direct dans le navigateur
  après implémentation — `--color-fg-400`/`--color-fg-500` étaient
  sous le seuil AA (4,5:1) sur fond blanc, corrigés et revérifiés
  (5,49:1 et 6,58:1).
- Vérifié par `npm run build` (7 pages) et test navigateur en direct,
  aucune erreur console.

## [SITE PUBLIC QUINTESSENCES — SPÉCIFICATION, ARCHITECTURE ET V1] - 2026-08-09

- **DEC-000057** : validation de `SITE-001` (spécification fonctionnelle)
  et `SITE-002` (vision créative) — Draft → Validé. Nouveau dossier
  `05_SPECIFICATIONS/SITE/` couvrant 5 zones : landing, compte,
  actualités, galerie, contact.
- **Architecture** : `GSIE/ARCHITECTURE/SITE_PUBLIC_ARCHITECTURE.md` —
  Astro 5 + React 19 (îlots) + Tailwind 4 + Framer Motion, même stack
  qu'`GSIE/ADMIN_WEB` pour cohérence d'outillage.
- **Implémentation** : nouveau projet `site-quintessences/`, distinct
  de `landing-quintessences/` (conservé en production sans changement).
  - Landing : hero, chaîne d'intelligence GSIE animée au scroll (7
    moteurs), grille interactive des 9 applications (icônes
    `DEC-000056`), indicateurs live avec état « donnée indisponible »
    explicite, principes fondateurs.
  - Actualités : fil chronologique, contenu versionné en Markdown
    (`src/content/actualites/`), 2 entrées publiées.
  - Contact : formulaire migré depuis `landing-quintessences/` avec
    vérification Turnstile réelle, catégorisation ajoutée (non encore
    routée côté serveur).
  - Galerie et Compte : scaffoldées, état « en construction » explicite
    (prérequis non résolus, voir `SITE-001` §9).
  - `npm run build` vérifié (7 pages générées) et testé en direct dans
    le navigateur, aucune erreur console.
- **Reste à faire** : endpoint public `GET /public/stats` côté API,
  processus de vérification vie privée pour la galerie, vérification
  des hypothèses `IDENTITE-001` pour un client web, déploiement
  Cloudflare Pages (étape humaine, `wrangler login`).

## [APPLICATIONS CLIENTES — ACTIVATION TERRA/AERIS/ATLAS + ICÔNES DES 8 APPS] - 2026-08-09

- **DEC-000056** : les trois applications futures réservées par
  `GSIE-DIR-0009` §3/§227 — **Terra** (sols/géologie), **Aeris**
  (atmosphère/météo), **Atlas** (cartographie globale) — sont créées
  dans `apps/` avec `README.md` + `GSIE_INTEGRATION.md` (statut
  Planifiée, Phase 4), sur le modèle d'Artemis/Flora/Hydro.
- **Icônes** : le fondateur a fourni des packs d'icônes complets (PNG
  48–1024 px, assets Android `mipmap-hdpi/mdpi/xhdpi/xxhdpi/xxxhdpi`,
  assets store Google Play/App Store) pour les 8 applications
  clientes (GeoSylva, Artemis, Ignis, Hydro, Flora, QGISIA, Terra,
  Aeris, Atlas). Rangées dans `apps/<App>/branding/icons/` pour les 7
  apps sans scaffolding applicatif ; intégrée immédiatement pour
  **GeoSylva** (`app/src/main/res/drawable-nodpi/app_icon.png`,
  foreground de l'adaptive icon, minSdk 26).
- **Documentation** : `CLAUDE.md` §10 (table des apps + note sur
  GSIE-DIR-0009/DEC-000056), `PROJECT_MEMORY.md` (section RFC-0037 et
  dernière mise à jour), `README.md` (diagramme + sections Terra/Aeris/
  Atlas), `03_DECISIONS/DEC-000056.md`.
- **RFC-0037 amendée** (même jour) : §3.1 (tableau des projections
  métier) et nouvelle §5.5 intègrent Terra/Aeris/Atlas comme projections
  transverses fournissant des données de référence aux autres domaines.
- **Reste à faire** : scaffolding applicatif complet (Architecture +
  Specification + code, comme pour GeoSylva) de Terra, Aeris, Atlas,
  Artemis, Flora, Hydro, Ignis — aucun n'existe encore hors GeoSylva.

## [APPLICATIONS FUTURES — AERIS ET RÉDUCTION DE LA LISTE] - 2026-08-08

- **Aeris** : l'application future **Atmos** est renommée **Aeris**
  (atmosphère / météo).
- **Retrait de la liste réservée** : **Aether**, **Chronos** et **Nexus**
  ne sont plus retenus comme applications futures réservées.
  La liste réservée est désormais : **Terra, Aeris, Atlas**.
- **Fichiers mis à jour** : `01_DIRECTIVES/ACTIVE/GSIE-DIR-0009.md`,
  `GSIE/ARCHITECTURE/HUB_UNREAL_TECHNOLOGY_STACK.md`,
  `landing-quintessences/public/index.html`,
  `QUINTESSENCES_DOMAIN_AND_CLOUDFLARE_BOOTSTRAP.md`,
  `22_PROJECT_MEMORY/notes/modification_architecture_globale.txt`.
- **Non modifiés** : `GSIE/AUDIT_2026-08-03/GSIE_CURRENT_ARCHITECTURE.md`
  (audit daté), `21_EXPERIMENTS/VEILLE_TECHNO_2026-08-02.md` (contient
  le modèle *Chronos-2*, sans lien avec le nom d'application) et
  `22_PROJECT_MEMORY/notes/possible_changement_de_noms.txt` (note de
  brainstorming historique).

## [APPLICATIONS CLIENTES — IGNIS MOBILE] - 2026-08-08

- **Ignis** : ajout d'une **application mobile terrain** dans le périmètre
  de la branche fonctionnelle Ignis (RFC-0004, ADOPTÉ). L'application
  mobile complète le Centre de Commandement GSIE (Unreal Engine 5.8) et
  l'intégration API : prise de terrain, remontée d'observations, suivi de
  sinistre, accès offline aux simulations et aux ressources locales.
- **Documentation** : mise à jour de `README.md` (table des interfaces
  Ignis), `CLAUDE.md` §10 (colonne « Type / interfaces » indiquant le
  mobile pour GeoSylva, Artemis et Ignis), `PROJECT_MEMORY.md`
  (applications mobiles reconnues et lien RFC-0004).

## [GATE 5 INTÉGRATION — MAILLON AMONT GBIF/TAXREF→EVIDENCE→KNOWLEDGE] - 2026-08-08

- **Suite des connecteurs SoilGrids/PlantNet/Météo-France** (voir entrées
  précédentes) : même pattern répliqué sur les deux référentiels
  taxonomiques déjà clients du Botanical Engine — `EvidenceKnowledgePipeline`
  a désormais cinq appelants réels en production.
- **GBIF** : `BotanicalEngine.query_and_ingest()` + endpoint
  `POST /botanical/query-and-ingest` (`EngineWriteUser`). Réutilise
  `query()` (même persistance `entity`/`entity_alias`, aucune double
  requête GBIF) puis fait passer le taxon accepté par l'Evidence Engine.
- **TAXREF** : `BotanicalEngine.resolve_taxref_and_ingest()` + endpoint
  `POST /botanical/taxref-and-ingest` (`EngineWriteUser`). Réutilise
  `resolve_taxref()`.
- **Différence assumée avec PlantNet/SYNOP** : GBIF Backbone Taxonomy et
  TAXREF (MNHN) sont des référentiels taxonomiques officiels consultés
  directement — pas une inférence ML ni une mesure brute instantanée.
  `ContentType.referentiel` + `SourceType.referentiel_officiel` plafonnent
  à `evidence_level=B` dans la matrice de décision, donc statut `accepte`
  et ingestion automatique, comme SoilGrids. C'est la matrice de
  l'Evidence Engine qui en décide, aucun code spécifique ajouté pour
  forcer ce comportement.
- **Nouveaux schémas** : `BotanicalIngestResult`/`BotanicalIngestResponse`,
  `TaxrefIngestResult`/`TaxrefIngestResponse` (`botanical/schemas.py`) —
  même forme que `PedologyIngestResult`/`PlantNetIngestResult`/
  `ClimateIngestResult`.
- **Tests** : `test_botanical_gbif_taxref_ingest.py` (succès, absence de
  résultat, échec de la source amont, échec d'ingestion Knowledge Engine
  rapporté comme `refused` sans interrompre la requête),
  `test_routers_coverage.py` (401/502/200 sur les deux nouveaux
  endpoints). 100% de couverture sur `botanical/engine.py`,
  `botanical/router.py`.

## [GATE 5 INTÉGRATION — MAILLON AMONT SOILGRIDS→EVIDENCE→KNOWLEDGE] - 2026-08-08

- **Constat** : `EvidenceKnowledgePipeline` (`engines/pipeline.py`) connecte
  déjà Evidence Engine → Knowledge Engine, testé (unitaire + intégration),
  mais n'avait **aucun appelant en production** — aucune source externe
  réelle ne le traversait jamais. C'est le « maillon amont » que
  ROADMAP.md donnait comme reste du Gate 5.
- **Connecteur livré** : `PedologyEngine.query_and_ingest()` (réutilise
  `query()` existant, aucune double requête SoilGrids) + endpoint
  `POST /pedology/query-and-ingest` (`EngineWriteUser`). Chaque
  caractéristique de sol (pH, argile, sable, limon) devient une
  soumission `RawKnowledgeSubmission` distincte, passe par l'Evidence
  Engine (SoilGrids = peer-reviewed + référentiel → plafond B → statut
  `accepte` dans la matrice de décision, sans changement de code), puis
  s'ingère comme connaissance atomique versionnée dans le Knowledge
  Engine — réutilisable par Correlation/Diagnostic au lieu de rester une
  valeur jetable renvoyée au seul appelant HTTP.
- **Nouveaux schémas** : `PedologyIngestResult`/`PedologyIngestResponse`
  (`pedology/schemas.py`) — un résultat par caractéristique, échec de
  l'une n'empêche pas l'ingestion des autres.
- **`query()` existant inchangé** — reste transitoire, comportement
  historique préservé ; `query_and_ingest()` est un chemin additionnel.
- **Limite connue, non traitée** : pas de déduplication — requêter deux
  fois le même point crée deux connaissances distinctes plutôt qu'une
  révision (`KnowledgeEngine.revise()` existe mais suppose un
  `connaissance_id` déjà connu ; identifier « le même fait » exigerait
  une clé stable point+propriété+source, hors périmètre de cette tranche).
- **Tests** : `test_pedology_engine_coverage.py` (succès, échec partiel
  d'une caractéristique, propagation de l'échec SoilGrids),
  `test_routers_coverage.py` (401/502/200 sur le nouvel endpoint).
  100% de couverture sur `engine.py`, `router.py`, `schemas.py`,
  `pipeline.py`. Un branch mort détecté et supprimé en cours de route
  (`except KnowledgeEngineError` au niveau router — l'exception est déjà
  capturée à l'intérieur du pipeline, ne remonte jamais jusqu'au router).


## [GATE 5 INTÉGRATION — MAILLON AMONT PLANTNET/MÉTÉO-FRANCE→EVIDENCE→KNOWLEDGE] - 2026-08-08

- **Suite du connecteur SoilGrids** (voir entrée précédente) : même
  pattern répliqué sur les deux autres sources externes déjà clientes
  (PlantNet, Météo-France SYNOP) — `EvidenceKnowledgePipeline` a
  désormais trois appelants réels en production.
- **PlantNet** : `BotanicalEngine.identify_and_ingest()` (nouveau
  paramètre injectable `plantnet_client`, même schéma que
  `gbif_client`/`taxref_client`) + endpoint
  `POST /botanical/identify-and-ingest` (`EngineWriteUser`). Réutilise
  le même client que `/botanical/identify` (aucune double requête) —
  la logique de parsing de la réponse brute PlantNet est factorisée
  dans `parse_plantnet_results()` (`botanical/engine.py`), appelée par
  les deux endpoints. Chaque espèce candidate devient une soumission
  distincte. **Différence assumée avec SoilGrids** : une identification
  PlantNet est une inférence par apprentissage automatique sur une
  photo précise, pas un produit peer-reviewed — `ContentType.observation`
  + `SourceType.referentiel_officiel` plafonnent à `evidence_level=D`
  dans la matrice de décision, donc statut `quarantine` systématique
  (validation humaine requise, CON-001), jamais d'ingestion automatique.
  C'est la matrice de l'Evidence Engine qui en décide, aucun code
  spécifique n'a été ajouté pour forcer ce comportement.
- **Météo-France** : `ClimateEngine.query_and_ingest()` (réutilise
  `query()` existant) + endpoint `POST /climate/query-and-ingest`
  (`EngineWriteUser`). Chaque paramètre mesuré présent (température,
  humidité, pression, vent, précipitations — un champ CSV vide reste
  omis, jamais soumis, ADR-009) devient une soumission distincte. Même
  plafond D/`quarantine` que PlantNet : une observation SYNOP est une
  mesure brute instantanée, pas un produit modélisé avec incertitude
  quantifiée comme SoilGrids.
- **Nouveaux schémas** : `PlantNetIngestResult`/`PlantNetIngestResponse`
  (`botanical/schemas.py`), `ClimateIngestResult`/`ClimateIngestResponse`
  (`climate/schemas.py`) — même forme que `PedologyIngestResult` (un
  résultat par candidat/paramètre, `statut`/`evidence_level`/
  `connaissance_id`/`version`/`raison`).
- **Tests** : `test_botanical_identify_and_ingest.py`,
  `test_climate_query_and_ingest.py` (succès, absence de résultat,
  échec de la source amont, confirmation qu'`ingest()` n'est jamais
  appelé puisque D/`quarantine` ne déclenche jamais l'ingestion),
  `test_routers_coverage.py` (401/400/502/200 sur les deux nouveaux
  endpoints). 100% de couverture sur `botanical/engine.py`,
  `botanical/router.py`, `botanical/schemas.py`, `climate/engine.py`,
  `climate/router.py`, `climate/schemas.py`.


## [FIX — LIMITE MÉMOIRE CONTENEUR API 768M → 2G] - 2026-08-08

- **Correction** de la trouvaille du benchmark de charge concurrente
  (voir entrée suivante) : `docker-compose.yml`, service `api`,
  `deploy.resources.limits.memory` passé de `768M` à `2G`.
- **Appliqué et vérifié en direct** : conteneur recréé
  (`docker compose up -d api`), healthcheck vert, `/health` et
  `/api/v1/auth/providers` répondent normalement.
- **Mémoire au repos avant/après** : 725,8 MiB / 768M (94,5%, quasi-OOM)
  → ~1,36 GiB / 2 GiB (68%, marge réelle rétablie).
- **Reste à surveiller** : la consommation de base reste élevée
  (~270 MB/worker × 5 workers gunicorn, dépendances scientifiques
  lourdes — scipy/xarray/cfgrib/geopandas/bindings Rust). Si la marge se
  resserre à nouveau sous charge de production réelle,
  `GSIE_GUNICORN_WORKERS` (actuellement 5) est le levier à ajuster.

## [GATE 6 PERFORMANCE — BENCHMARK CHARGE CONCURRENTE] - 2026-08-08

- **Nouveau** : `scripts/load_test_concurrent.py`, complète
  `validation_benchmark.py` (S3, séquentiel) avec 3 volets concurrents :
  capacité HTTP brute (`/health`), rate limiting sous rafale
  (`/api/v1/resources`), pool de connexions DB (bypass HTTP, sessions
  SQLAlchemy directes).
- **Pool DB validé empiriquement pour la première fois** : `DEC-000037`
  fixait la formule `workers × (pool_size + max_overflow) ≤ max_connections`
  sur le papier seulement. 24 sessions concurrentes contre une capacité de
  14 (pool_size=4 + max_overflow=10) → dégradation gracieuse confirmée via
  `engine.pool.checkedout()`, zéro erreur.
  - Piège méthodologique corrigé en cours de route : une première mesure
    comptait la concurrence à l'ouverture du context manager
    (`async with async_session_factory()`), qui n'acquiert pas de
    connexion physique (checkout paresseux) — pic mesuré à 24 au lieu de
    14 alors que la latence trahissait une file d'attente invisible au
    compteur. Corrigé via l'introspection directe du pool SQLAlchemy.
- **Rate limiting confirmé sous rafale concurrente** (pas seulement
  séquentielle comme le pentest du 2026-08-07) : 60 requêtes simultanées,
  toutes dans le budget 120/min, aucune dérive du compteur Redis.
- **Trouvaille critique** : le conteneur `api` (limite Docker 768M) tourne
  à **94,5 % de sa mémoire au repos, sans aucune charge** (725,8 MiB).
  Sous charge légère (60 requêtes `/health` concurrentes), pic à 99,9 %
  (767,1 MiB) — à un pas d'un OOM-kill par le cgroup Docker. Ce n'est pas
  un effet de charge : c'est l'empreinte de base des 5 workers gunicorn
  avec dépendances scientifiques lourdes (scipy, xarray, cfgrib,
  geopandas, bindings Rust). Décision d'infrastructure non prise dans ce
  rapport : augmenter la limite mémoire ou réduire `GSIE_GUNICORN_WORKERS`.
- **Limite méthodologique documentée** : les latences absolues varient de
  5 à 10× selon que le trafic traverse le port-forwarding Docker
  Desktop/Windows ou non (207ms p50 en interne vs 1382ms via l'hôte) — un
  artefact de l'environnement de dev local, à ne pas citer comme
  représentatif de la production.
- **Rapport complet** : `GSIE/API/docs/LOAD_TEST_CONCURRENT_2026-08-08.md`.

## [SÉCURITÉ — MFA ADMINISTRATEUR OBLIGATOIRE + GUIDE OAUTH GOOGLE] - 2026-08-08

- **MFA obligatoire pour le rôle `admin`** : un compte avec le rôle le plus
  privilégié de la plateforme ne reçoit plus jamais de token complet tant
  que son second facteur n'est pas actif — corrige la lacune restante du
  gate Sécurité (ROADMAP §3).
  - Nouveau type de jeton restreint `mfa_setup_required`
    (`core/auth.py::create_mfa_setup_token`, 15 min) : rejeté par
    `get_current_user`/RBAC comme n'importe quel jeton non-`access` (même
    garde déjà utilisée pour le jeton de challenge MFA), donc inutilisable
    hors de `/mfa/setup` et `/mfa/verify` (nouvelle dependency
    `get_current_user_or_mfa_setup`, seule à l'accepter en plus du token
    d'accès normal).
  - `_issue_tokens` (choke point unique d'émission de session, tous
    fournisseurs confondus — local, Google, OIDC, MFA) renvoie
    `AdminMfaSetupRequiredResponse` au lieu de tokens si le compte a le
    rôle `admin` sans MFA actif. Le compte n'est jamais bloqué : chaque
    connexion réémet un nouveau jeton de bootstrap.
  - `@overload` sur `_issue_tokens` pour que `register_local` (comptes
    neufs, jamais admin par défaut) garde un type de retour exact
    `TokenResponse`, vérifié par mypy --strict.
  - Nouveaux tests : `test_auth_type_jeton.py` (jeton de bootstrap rejeté
    comme accès, `get_current_user_or_mfa_setup` accepte les deux types,
    claims réservés), `test_identity_coverage.py` (admin sans MFA reçoit
    le bootstrap, admin avec MFA suit le flux normal existant, le bootstrap
    fonctionne sur `/mfa/setup`+`/mfa/verify` et est rejeté sur `/me`).
  - 100% de couverture maintenue (13 194 statements), 2555 tests passants,
    ruff et mypy --strict verts.
- **Guide OAuth Google production** : `GSIE/API/docs/GOOGLE_OAUTH_PRODUCTION_SETUP.md`
  — étapes Google Cloud Console (écran de consentement, Client IDs Web +
  Android `com.forestry.counter`, soumission à vérification). Aucune étape
  automatisable (compte Google, vérification humaine par Google).
- `docs/openapi.json` resynchronisé (nouveaux schémas de réponse).

## [P0-1 — SAUVEGARDES DB PGBACKREST + WAL ARCHIVING] - 2026-08-08

- **Implémentation** : `pgbackrest` installé dans `Dockerfile.db`,
  `archive_mode=on` + `archive_command` + `max_wal_senders=6` sur le
  service `db` (`docker-compose.yml`), dépôt persistant sur volumes
  Docker nommés (`gsie_pgbackrest_repo`, `gsie_pgbackrest_log`),
  chiffrement AES-256-CBC via `PGBACKREST_REPO1_CIPHER_PASS` (jamais dans
  `docker/pgbackrest.conf` — lu nativement depuis l'environnement).
- **2 bugs corrigés dans le template DEC-000037 avant mise en service** :
  `pg1-host=/var/run/postgresql` (option réservée à SSH distant, faisait
  échouer `stanza-create`) remplacé par `pg1-socket-path` ; rôle
  `pg1-user=gsie_migrator` (jamais câblé dans l'initdb réel) remplacé par
  `gsie` (le rôle superuser effectivement déployé) ; `repo1-cipher-pass=${VAR}`
  (interpolation shell non supportée par `pgbackrest.conf`) supprimé au
  profit de la lecture d'environnement native.
- **Validation live (2026-08-08)** sur la base de dev réelle (52 MB, 151
  tables) : `stanza-create` online, archivage WAL manuel + automatique,
  sauvegarde complète chiffrée (52 MB → 5,8 MB), restauration dans un
  répertoire isolé avec promotion automatique — 151 = 151 tables, PostGIS
  fonctionnel. Base de dev live non affectée, laissée dans un état
  fonctionnel (archivage + backup actifs, non chiffrés en attendant le
  rebuild d'image).
- **Nouveaux fichiers** : `scripts/pgbackrest_backup.sh` (wrapper
  `docker exec`, cron full/diff/incr), `.env.example`
  (`PGBACKREST_REPO1_CIPHER_PASS`).
- **Documentation** : `GSIE/API/docs/BACKUP_RESTORE.md` passé de Draft à
  Implémenté (§3.5/3.6) ; `GSIE/DOCUMENTATION/DR-RESTAURATION.md` §3.5 ;
  `ROADMAP.md` P0-1.
- **Reste** : `docker compose build db` pour figer pgbackrest dans l'image
  de façon permanente (bloqué au moment de la validation par un problème
  réseau/certificat sans rapport avec pgBackRest — échec du téléchargement
  de la source Apache AGE) ; repo2 S3 cross-région (identifiants cloud à
  provisionner).

## [TESTS — 100% COVERAGE ET MASTER TEST] - 2026-08-07

- **Couverture** : la suite unitaire atteint **100 % de couverture** sur
  `src/gsie_api` (13 170 statements). Les 14 dernières lignes non couvertes
  l'ont été par des tests ciblés dans `test_app.py`, `test_audit_service.py`,
  `test_auth_hardening.py`, `test_auth_type_jeton.py`, `test_config.py` et
  `test_turnstile.py`.
- **Garde-fous** :
  - `tool.coverage.report.fail_under = 100` dans `pyproject.toml`.
  - `scripts/run-master-tests.ps1` et `scripts/run-master-tests.sh` pour
    exécuter en une commande : ruff, ruff format, mypy, tests unitaires à
    100 % et (optionnel) harnais de mutation.
  - `.github/workflows/ci.yml` : `cov-fail-under` porté à 100.
- **Harnais de mutation** : 67 mutations, score maintenu.

## [HUB UNREAL — STACK TECHNOLOGIQUE] - 2026-08-07

- **Document architectural ajouté** :
  `GSIE/ARCHITECTURE/HUB_UNREAL_TECHNOLOGY_STACK.md` (Draft). Présentation
  des langages et technologies autour du Centre de Commandement Unreal,
  organisée en quatre catégories : fondamentaux (C++, Rust, Python,
  Kotlin, PostGIS), stratégiques (Elixir, Julia, WebAssembly),
  accélérateurs spécialisés (Futhark, Taichi, Mojo) et recherche/validation
  (P, Dafny, Pony, Unison, MoonBit, Zig).
- **Respect des décisions validées** : DEC-000010 (UE 5.8 + Cesium),
  DEC-000019 (Python + Rust + Go + TypeScript), DEC-000053 (Server Meshing).
- **Principes affermis** : le Hub Unreal est une projection interactive du
  `State Fabric` ; GSIE State ≠ Unreal World ; chaque langage doit apporter
  un avantage structurel mesurable pour être adopté.
- **Références croisées** : `GSIE/ARCHITECTURE/README.md` et
  `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` mis à jour.

## [PENTEST — CORRECTIFS RESTANTS] - 2026-08-07

- **DNS** : enregistrements CAA ajoutés sur `quintessences-platform.com`
  (`issue letsencrypt.org`, `issue pki.goog; cansignhttpexchanges=yes`,
  `issuewild` pour les deux, `iodef` mailto security).
- **HSTS preload** : paramètre Cloudflare `preload: true` + `max-age: 63072000`
  activé. Domaine soumis à `hstspreload.org` (statut `pending`).
- **Worker edge rate limiter** : `cloudflare-workers/rate-limiter/` déployé
  sous `gsie-rate-limiter`, route `api.quintessences-platform.com/*`.
  Seuils : 10 req/min pour `/api/v1/auth/*`, 100 req/min pour le reste.
  KV `gsie-rate-limiter-RATE_LIMITS` créé. Script + `deploy.ps1` versionnés.
- **Protection `/metrics`** : token Bearer optionnel `GSIE_METRICS_BEARER_TOKEN`.
  Si défini, exigé partout ; sinon, rôle `admin` requis hors développement.
  Tests ajoutés dans `tests/unit/test_metrics.py`.
- **Prompt Claude pentest** : `PROMPT_PENTEST_CLAUDE.md` à la racine,
  prêt pour audit défensif ciblé.
- **Validation** : ruff, mypy et tests unitaires passants.

## [PENTEST — AUTHENTIFICATION ET CONNEXION] - 2026-08-07

- **Rapport** : `PENTEST_AUTH_CONNEXION_2026-08-07.md`. Revue statique
  complémentaire à `SECURITY_AUDIT_2026-08-07.md`, centrée sur le code des
  flux d'authentification, d'identité fédérée et de RBAC (3 revues ciblées
  indépendantes).
- **Corrections appliquées** :
  - `auth/identity_router.py`, `auth/router.py`, `audit/middleware.py` :
    remplacement de `request.client.host` par `core.limiter.get_client_address()`
    partout — l'audit trail et le lockout utilisaient l'IP interne du tunnel
    Cloudflare au lieu de l'IP réelle du client, faussant la traçabilité
    (`GSIE-CON-005`) et le score anti-robot Turnstile.
  - `auth/lockout.py` : `AccountLockoutService` verrouille désormais aussi
    sur une clé par compte seul (en plus de la clé composite email+IP) —
    la clé composite seule permettait de contourner le lockout par rotation
    d'IP (proxys rotatifs / botnet).
- **Validation** : 192 tests unitaires auth/identité/RBAC passants après
  correctifs, aucune régression.

## [PENTEST — NONCE OIDC GÉNÉRIQUE] - 2026-08-07

- Correction du troisième constat (Moyen) du pentest ci-dessus : le flux
  OIDC générique (`auth/oidc_generic.py`) ne validait pas de `nonce`,
  contrairement au flux Google, exposant un ID token intercepté à un rejeu.
- Nouveau module `auth/oidc_nonces.py` (miroir de `google_nonces.py`,
  store mémoire/Redis, GETDEL atomique, préfixe `gsie:auth:oidc-nonce:`).
- `oidc_authorize` génère et retourne un nonce serveur, inclus dans l'URL
  d'autorisation ; `login_oidc` l'exige, le consomme à usage unique et le
  fait vérifier par `GenericOidcVerifier` (claim `nonce` requis, comparaison
  `hmac.compare_digest`).
- Nouveaux réglages `GSIE_OIDC_NONCE_STORAGE_URL` / `GSIE_OIDC_NONCE_EXPIRE_SECONDS`.
- `PENTEST_AUTH_CONNEXION_2026-08-07.md` mis à jour : les 3 constats Moyens
  identifiés sont désormais tous corrigés, aucun constat ouvert.
- 117 tests unitaires auth/identité re-exécutés, aucune régression.

## [VEILLE — BEAM/OTP ET VÉRIFICATION FORMELLE] - 2026-08-07

- **Document** : `GSIE/RESEARCH/VEILLE_BEAM_OTP_SERVER_MESHING_2026-08-07.md`
  (Draft). Synthèse d'une discussion externe (ChatGPT, non sourcée
  indépendamment) sur Erlang/OTP/Elixir/Gleam et langages émergents pour GSIE.
- **Constat** : ne modifie pas le verdict déjà tracé dans
  `EMERGING_LANGUAGES_STUDY.md` (DEC-000019, stack Python+Rust+Go+TypeScript
  validée ; Elixir à surveiller, Gleam ignoré).
- **Apports retenus pour mémoire** (aucune décision, aucun code) :
  - Patron OTP « supervision par isolation de panne » comme critère de
    conception si/quand le futur GSIE Server Meshing est spécifié
    (indépendant du langage retenu).
  - **P** (machines à états, Microsoft Research) et **Dafny** (preuve
    d'invariants) ajoutés au plan de surveillance comme outils de
    vérification formelle pour le protocole de transfert d'autorité
    (drones/cellules) du Server Meshing.
- **Sécurité** : durcissement `Strict-Transport-Security` en
  `max-age=63072000; includeSubDomains; preload` dans
  `src/gsie_api/shared/middleware.py` (recommandation restante du pentest du
  2026-08-07).

## [PENTEST DÉFENSIF POST-DÉPLOIEMENT] - 2026-08-07

- **Rapport d'audit** : `SECURITY_AUDIT_2026-08-07.md` couvre Cloudflare, DNS,
  API, landing, admin web, Docker et secrets. Score global 8.2/10.
- **Tests live** : headers, CORS, rate limiting, DNSSEC, WAF, SSL/TLS, firewall rules.
- **Corrections immédiates** :
  - `src/gsie_api/auth/router.py` : comparaison dev login en `hmac.compare_digest`.
  - `src/gsie_api/core/auth.py` : refus des clés JWT auto-générées en staging et prod.
  - `.env.example` : `GSIE_AUTH_DEV_LOGIN_ENABLED=false` par défaut.
- **Recommandations restantes** : CAA record, HSTS preload, restriction `/metrics`, rate
  limiting edge Cloudflare (plan payant/Worker).
- **Nettoyage sécurité** : révoquer la Global API Key utilisée pour l'audit ; regénérer
  le secret Turnstile si nécessaire.

## [GSIE API v0.1.0 — DEPLOIEMENT CLOUDFLARE + DOMAINE PERMANENT] - 2026-08-06

- **Domaine permanent acquis** : `quintessences-platform.com` via
  Cloudflare Registrar (prix coutant, 10,46 $/an, WHOIS privacy gratuit).
- **Tunnel Cloudflare nomme** : `gsie-api` (ID `07e329c5-7e1f-4bdd-898f-bc38a10ad287`)
  deploye avec 2 connexions QUIC HA vers les PoP CDG07/CDG14.
- **DNS configure** : `api.quintessences-platform.com` en CNAME vers le tunnel.
- **HTTPS actif** : certificat SSL/Cloudflare, HSTS, headers de securite
  (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy).
- **API GSIE exposee publiquement** : endpoints `/health`, `/docs`, `/redoc`,
  `/api/v1/openapi.json` accessibles en `https://api.quintessences-platform.com`.
- **Mode proxy Cloudflare active** : `GSIE_EDGE_PROXY_MODE=cloudflare_tunnel`,
  rate-limiting base sur `CF-Connecting-IP`, CORS autorises pour
  `https://api.quintessences-platform.com` et `https://quintessences-platform.com`.
- **Fix logging colorama** : fallback JSON renderer quand `stderr` n'est pas un TTY
  (evite `OSError: [Errno 22] Invalid argument` sur Windows avec Docker/pipe).
- **Redis expose pour le dev host** : port `127.0.0.1:6379` ajoute a
  `docker-compose.yml` pour l'API lancee localement.
- **Document d'architecture Cloudflare** : `QUINTESSENCES_DOMAIN_AND_CLOUDFLARE_BOOTSTRAP.md`
  avec arborescence des sous-domaines, strategie free-first, offres gratuites,
  couts, securite, permissions API token et procedure de retour arriere.
- **Landing page statique** : creation de `landing-quintessences/` (HTML/CSS,
  `wrangler.toml`, script de deploiement Cloudflare Pages). Déployée sur
  `https://quintessences-platform.com` et `https://www.quintessences-platform.com`.
- **Adresse e-mail transactionnelle** : `GSIE_EMAIL_SENDER` mis a jour vers
  `noreply@quintessences-platform.com` dans `.env`, `.env.example`,
  `docker-compose.yml` et `src/gsie_api/core/config.py`.
- **Verification des mises a jour cloudflared** : script
  `GSIE/API/cloudflared/check-update.ps1`.
- **DNSSEC + SSL/TLS Full + HSTS + Always Use HTTPS + TLS 1.2** actifs via Cloudflare.
- **WAF Managed Free Ruleset + custom firewall ruleset** pour bloquer les scanners
  et challenger les user-agents vides sur `/auth/`.
- **DNS records** : `www.quintessences-platform.com` et `status.quintessences-platform.com`
  créés, apex en CNAME flattening vers Cloudflare Pages.
- **Email Routing** activé sur `quintessences-platform.com`.
- **Nettoyage securite** : suppression des tokens API temporaires (`Wrangler-Pages-Temp`) et des
  fichiers secrets locaux (`.cloudflare_credentials`, `.cloudflare_api_token`, `.cloudflare_zone_id`).
- **Page de statut** : creation de `status-quintessences/` (HTML/CSS/JS), deploiement
  sur `status.quintessences-platform.com` via Cloudflare Pages.
- **Turnstile** : service `gsie_api.shared.turnstile`, endpoint `POST /auth/turnstile/verify`,
  verification du challenge sur `POST /auth/login` et `POST /auth/login/password`,
  widget sur la landing page et sur la page de connexion de l'admin web.
- **SMTP transactionnel** : port Mailpit `127.0.0.1:1025` mappe, variables d'environnement `.env`
  pretes, tests unitaires `test_transactional_email.py`.
- **Migration Docker API** : l'API tourne dans le conteneur `api-api-1`, `cloudflared\migrate-to-docker.ps1`
  documente le basculement.
- **Fichiers de configuration ajoutes** :
  - `GSIE/API/cloudflared/config.yml`
  - `GSIE/API/cloudflared/setup-tunnel.ps1`
  - `GSIE/API/cloudflared/start-tunnel.ps1`
- **Audit final valide** :
  - endpoints publics 200 OK,
  - 2080 tests unitaires passes, 63 skipped, 4 warnings non bloquantes,
  - `ruff` et `mypy` OK,
  - migrations DB a jour (`20260806_0043`),
  - services Docker `healthy`,
  - SSL/TLS valide via Cloudflare.

## [GSIE ENVIRONMENTAL DIGITAL TWIN PLATFORM — CADRAGE FÉDÉRATEUR] - 2026-08-06

- **RFC-0037 ouverte en Draft** : GSIE est formalisé comme un jumeau
  numérique environnemental fédéré. GeoSylva, Ignis, Hydro, Flora et
  Artemis sont des projections métier spécialisées du même jumeau ;
  QGISIA fournit la projection SIG et analytique ; les Hubs Unreal sont
  les environnements immersifs permettant d'explorer, simuler et
  interagir sous contrôle humain.
- **Architecture de référence ajoutée** :
  `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md`.
  Elle définit les ressources communes, les scénarios branchés, la
  séparation réel/dérivé/prévision/simulé/proposé/décidé, les flux
  GeoSylva ↔ Ignis ↔ Hydro, les classes de performance et les règles
  d'action contrôlée.
- **HUB-002 étendu en Draft 1.1.0** : ressources multi-domaines,
  provenance, fraîcheur, `scenario_id` et `ActionRequest` auditées ; le
  Hub reste passif pour les calculs et ne commande pas directement un
  système physique.
- **Documentation des projections ajoutée** dans GeoSylva, Ignis, Hydro,
  Flora, Artemis et QGISIA. Ces documents ne modifient aucun contrat
  applicatif existant et n'autorisent aucune commande opérationnelle.
- La RFC-0037 ne crée pas encore de décision d'adoption, de migration de
  schéma ou de nouvelle dépendance technique.

## [GSIE ENVIRONMENTAL DIGITAL TWIN — CAS D'USAGE RÉELS] - 2026-08-06

- **Catalogue de cas d'usage réels ajouté** :
  `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_USE_CASES.md`. Six cas
  fédérés sourcés : ruissellement post-incendie (Maures, Landiras),
  crise scolytes du sapin pectiné (Grand-Est, Vosges), SITAC multi-moyens
  (Haute-Corse, NexSIS), crues éclair et karst (Gard 2002, Larzac),
  biodiversité forestière et corridors (BioDT, Forest DTC, SenseForest),
  tempêtes et récupération forestière (Lothar, Klaus, DestinE Finland).
- **Références croisées** ajoutées dans `GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md`
  et `02_RFC/RFC-0037-gsie-environmental-digital-twin-platform.md`. Le
  catalogue oriente le phasage P1 (tranche Ignis), P3 (Hydro) et P4-P5
  (Flora, Artemis).

## [GSIE TERRITORIAL MESH — CADRAGE ARCHITECTURAL] - 2026-08-06

- **Chantier annexe complémentaire au Server Meshing** ouvert par décision
  Fondateur (DEC-000054, GSIE-DIR-0013, RFC-0036). Couche logique de
  gouvernance territoriale superposée à l'exécution technique du Server
  Meshing (RFC-0035) : là où le Server Meshing organise l'exécution
  (serveurs de zone, autorité de rendu, streaming), le Territorial Mesh
  organise la hiérarchie administrative et opérationnelle
  (France → Région → Département → Territoire Opérationnel → Cellule
  Spatiale → Sous-cellule) et ses états (Froid, Chaud, Opérationnel,
  Crise).
- **Périmètre prototype v0** : Nouvelle-Aquitaine (Charente 16,
  Deux-Sèvres 79), 1 RCH, 2 DOD, 2 cellules spatiales, 1 drone edge
  traversant, simulation IGNIS simplifiée. NCP optionnel/simulé.
- **20 livrables dédiés produits** (RFC-0036 et 17 documents
  d'architecture/cadrage en Draft, GSIE-DIR-0013 Active, DEC-000054 Validé),
  complétés par un lot de synchronisation des trois fichiers racine, dans `GSIE/ARCHITECTURE/` et
  `02_RFC/`, `01_DIRECTIVES/`, `03_DECISIONS/` :
  1. RFC-0036 (vision + 10 principes P-TERR-01 à P-TERR-10)
  2. GSIE-DIR-0013 (directive fondatrice)
  3. DEC-000054 (décision d'ouverture)
  4. `TERRITORIAL_MESH_TARGET.md` (architecture cible long terme)
  5. `TERRITORIAL_MESH_NATIONAL_CONTROL_PLANE.md` (NCP)
  6. `TERRITORIAL_MESH_REGIONAL_HUB.md` (RCH)
  7. `TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md` (DOD)
  8. `TERRITORIAL_MESH_DYNAMIC_CELLS.md` (cellules spatiales dynamiques)
  9. `TERRITORIAL_MESH_STATE_FABRIC.md` (State Fabric fédéré)
  10. `TERRITORIAL_MESH_EVENT_BUS.md` (bus d'événements fédéré)
  11. `TERRITORIAL_MESH_MATRICES.md` (matrices responsabilités/autorités/réplication)
  12. `TERRITORIAL_MESH_DIAGRAMS.md` (10 diagrammes ASCII)
  13. `TERRITORIAL_MESH_ROADMAP.md` (phasage Phases 5-9)
  14. `TERRITORIAL_MESH_BACKLOG.md` (backlog phasé TERR-T/TERR-P5/P6/P7/P8)
  15. `TERRITORIAL_MESH_ADR.md` (registre ADR-020 à ADR-028)
  16. `TERRITORIAL_MESH_RISKS.md` (16 risques, 2 Critiques, 4 Élevés)
  17. `TERRITORIAL_MESH_ACCEPTANCE.md` (critères d'acceptation par phase)
  18. `TERRITORIAL_MESH_TEST_STRATEGY.md` (stratégie de test)
  19. `TERRITORIAL_MESH_PROTOTYPE_V0.md` (prototype Nouvelle-Aquitaine)
  20. `TERRITORIAL_MESH_COMPLEXITY.md` (estimation complexité/chemin critique)
- **10 principes fondateurs** (P-TERR-01 à P-TERR-10) : hiérarchie
  configurable, orthogonalité avec le Server Meshing, concentration
  dynamique par la demande, états opérationnels explicites, PostgreSQL
  source de vérité sans consensus distribué, offline-first territorial,
  autorité unique par périmètre, frontières scientifiques réconciliées,
  subordination à la connaissance, traçabilité multi-niveaux.
- **9 ADR** (ADR-020 à ADR-028) : hiérarchie configurable, orthogonalité
  Territorial/Server Meshing, réplication logique PostgreSQL cross-région,
  Redis Pub/Sub fédéré multi-niveaux, capsules territoriales pour edge,
  états opérationnels comme signal de gouvernance, RBAC territorial,
  autorité unique par périmètre, frontières scientifiques réconciliées.
- **Orthogonalité actée avec le Server Meshing** (ADR-021) : les deux
  chantiers restent indépendants, la jonction se fait par interfaces
  abstraites (ADR-015 réutilisée). Réutilisation encadrée des ADR-005 (Outbox),
  ADR-008 (capsules signées, encore Proposé), ADR-011 (PostgreSQL source de vérité),
  ADR-013 (Redis Pub/Sub), ADR-017 (mTLS).
- **N'interrompt pas la Phase 4** — préparation par interfaces abstraites
  et réutilisation des briques existantes. Phase 5 (prototype
  Nouvelle-Aquitaine) requiert validation préalable des documents par
  le Fondateur.
- **Roadmap générale mise à jour** : section Territorial Mesh ajoutée
  à la Phase 4 de `ROADMAP.md`.

## [GSIE SERVER MESHING — CADRAGE ARCHITECTURAL] - 2026-08-03

- **Chantier annexe d'architecture distribuée ouvert** par décision
  Fondateur (DEC-000053, GSIE-DIR-0012, RFC-0035). Inspiration :
  Server Meshing de Star Citizen, adapté à un jumeau numérique
  environnemental persistant et distribué.
- **Périmètre prototype v0** : mono-région Landiras, autorité hybride
  zone + type, compatibilité UE6 anticipée par interfaces abstraites
  (pas de dépendance hard).
- **17 documents Draft produits** dans `GSIE/ARCHITECTURE/` :
  1. RFC-0035 (vision + 8 principes P-MESH-01 à P-MESH-08)
  2. GSIE-DIR-0012 (directive fondatrice)
  3. DEC-000053 (décision d'ouverture)
  4. `SERVER_MESHING_TARGET.md` (architecture cible long terme)
  5. `SERVER_MESHING_PROTOTYPE_V0.md` (prototype Landiras)
  6. `SERVER_MESHING_ROADMAP.md` (phasage Phases 5-7)
  7. `SERVER_MESHING_ADR.md` (registre ADR-010 à ADR-019)
  8. `SERVER_MESHING_RISKS.md` (16 risques, 1 Critique, 4 Élevés)
  9. `SERVER_MESHING_DIAGRAMS.md` (8 diagrammes ASCII)
  10. `SERVER_MESHING_BACKLOG.md` (backlog phasé MESH-PREP/P5/P6/P7)
  11. `SERVER_MESHING_ACCEPTANCE.md` (critères d'acceptation par phase)
  12. `SERVER_MESHING_TEST_STRATEGY.md` (stratégie de test)
  13. `SERVER_MESHING_UE6_MIGRATION.md` (stratégie migration UE6)
  14. `SERVER_MESHING_EXPERIMENTAL.md` (features expérimentales gated)
  15. `SERVER_MESHING_COMPLEXITY.md` (estimation complexité/chemin critique)
- **8 principes fondateurs** (P-MESH-01 à P-MESH-08) : continuité
  spatiale, persistance externe obligatoire, autorité hybride,
  concentration dynamique, offline-first, traçabilité, modularité,
  subordination à la connaissance.
- **10 ADR** (ADR-010 à ADR-019) : autorité hybride, persistance
  PostgreSQL, réplication par pertinence, Redis Pub/Sub, bitemporalité,
  interfaces abstraites UE6, orchestrateur centralisé, mTLS, grille
  adaptative, mode dégradé offline-first.
- **N'interrompt pas la Phase 4** — préparation par interfaces
  abstraites et persistance externe. Phase 5 (prototype Landiras)
  requiert validation préalable des documents par le Fondateur.
- **Roadmap générale mise à jour** : section Server Meshing ajoutée
  à la Phase 4 de `ROADMAP.md`.

## [GSIE/API — HARDENING AUTH V1] - 2026-08-05

- **7 lacunes d'authentification comblées** pour un système de connexion
  très avancé :
  1. **MFA TOTP** (RFC 6238) + codes de récupération à usage unique
     (Argon2id, chiffrés Fernet côté serveur).
  2. **Lockout progressif** — blocage temporaire après N tentatives échouées
     (Redis distribué ou mémoire locale, fenêtre glissante).
  3. **Sessions actives** — traçage par appareil, liste et révocation
     sélective (logout par appareil, logout-all sauf session courante).
  4. **OIDC générique** — vérificateur OIDC standard pour Keycloak,
     Microsoft Entra ID, GitHub, etc. (découverte JWKS, validation
     audience/issuer).
  5. **Force mot de passe** — HIBP k-anonymity (préfixe SHA-1 uniquement)
     + score zxcvbn avec seuil minimum configurable.
  6. **Détection réutilisation refresh token** — log d'avertissement
     quand un token déjà rotaté est réutilisé (vol détecté).
  7. **Événements auth dans audit_log** — bridge fire-and-forget vers
     le journal d'audit append-only (login, lockout, MFA, sessions).
- **Migration 20260803_0034** : 5 nouvelles tables
  (`mfa_secret`, `mfa_recovery_code`, `active_session`,
  `failed_login_attempt`, `revoked_refresh_token`).
- **Dépendances** : `pyotp` (TOTP), `zxcvbn` (force mot de passe).
- **Configuration** : 11 nouvelles variables d'environnement documentées
  dans `.env.example`.
- **Tests** : 24 nouveaux tests unitaires (`test_auth_hardening.py`)
  couvrant MFA, lockout, sessions, force mot de passe.

## [GOUVERNANCE — SYSTÈME DE DÉVELOPPEMENT IA V1] - 2026-08-05

- **DEC-000051 validée** : adoption du système de développement assisté par IA
  Quintessences v1.
- La hiérarchie documentaire existante reste la seule source de vérité ; aucun
  second coffre d'idées, registre de prompts ou arborescence `docs/` parallèle
  n'est créé.
- La limite de travail en cours du Fondateur est fixée à `1+1+1` : une tranche
  produit, une recherche et une correction urgente.
- Ajout de `/ingestion-idee` et `/ingestion-ressource` en mode proposition par
  défaut, ainsi que `/pilotage-wip` et `/audit-skills-devin`.
- `IDEA-0003` enregistre IGNIS-FOLD comme hypothèse de recherche inspirée de
  G-FOLD ; aucune classe de drone n'est choisie et aucun code n'est autorisé.
- Le pilote de méthode est la synchronisation multi-client GeoSylva.
- Passe qualité reprise le 2026-08-05 : caractère d'encodage corrompu retiré de `ROADMAP.md` et d'une analyse historique ; frontmatter rétabli pour les 36 skills Devin ; conventions `pytest-asyncio` auto documentées dans `/tests-gsie`.

## [DOCUMENTATION — GEOSYLVA-003 V0.9.1] - 2026-08-04

- **Nettoyage** — 8 corrections résiduelles avant gel de la spec.
- **CORR 1** : §3.1 — « parent » unique → relations
  structurelles/contextuelles/workspace (pas de `parentId` universel).
- **CORR 2** : 8 mentions résiduelles « Données » → « Explorer ».
- **CORR 3** : §29.1 tableau de cadrage actualisé (Explorer, cartes
  conditionnelles au lieu d'onglets).
- **CORR 4** : « 16 sections » → « 4 domaines, 16 destinations
  secondaires » (4 occurrences).
- **CORR 5** : §12.8 — P0-P7 « plan d'exécution immédiat » →
  « archivées pour traçabilité, lots 0-10 = plan actuel ».
- **CORR 6** : §12.5 — déclencheurs P0/P2/P3/P4/P5/P6 →
  Lot 0/3/2/5/9/10.
- **CORR 7** : avertissement routes altérées (Devin doit relire le code
  source, pas les chaînes Markdown).
- **CORR 8** : §14 et §15 marqués **NON NORMATIF** (endpoints, tables,
  JSON, WorkManager = exemples de cadrage, pas contrats avant RFC).
- GeoSylva spec passe en v0.9.1 — Candidate for Review (commit `7c0ae53`
  sur `fix/enterprise-reliability-2026-07-21`, +63/-32 lignes).
- **Prochaines étapes** : gel de GEOSYLVA-003 comme spécification produit,
  audit du code réel, extraction RFC-UI-001, extraction RFC-0001,
  backlog du Lot 0.

## [DOCUMENTATION — GEOSYLVA-003 V0.9.0] - 2026-08-04

- **Candidate for Review** — 11 corrections structurantes du Fondateur.
- **CORR 1** : hiérarchie territoriale — `⊇` remplacés par relations
  nommées (graphe relationnel N-N, pas arbre rigide). Une forêt peut
  couvrir plusieurs propriétés ; un peuplement peut chevaucher plusieurs
  parcelles.
- **CORR 2** : navigation contextuelle clarifiée comme **vue
  utilisateur**, pas propriété des données. Les entités utilisent des
  relations N-N (forêt dans plusieurs projets, mission sur plusieurs
  forêts, etc.).
- **CORR 3** : surcharge d'onglets réduite — fiche parcelle 13 onglets →
  5 groupes (Aperçu/Terrain/Interventions/Analyse/Plus) avec
  sous-navigation ; fiche placette 11 onglets → 5 groupes.
- **CORR 4** : bottom nav — « Données » → « Explorer » (variante B
  privilégiée) + variantes A/B à tester avec utilisateurs.
- **CORR 5** : Compte — 16 sections regroupées en 4 groupes visuels
  (Identité / Offre Quintessences / Application / Confidentialité).
- **CORR 6** : permissions onboarding — pas toutes dès le départ,
  demandées au premier usage de chaque fonction (localisation → carte,
  caméra → scan, etc.).
- **CORR 7** : fond vidéo connexion — ressource APK légère par défaut +
  pack signé facultatif (avant la première installation de packs).
- **CORR 8** : splash — séparation bloquant (base/migration/intégrité)
  et non-bloquant (sync/packs/session), démarrage rapide.
- **CORR 9** : contradiction roadmap — ancien P7 « Reporté » →
  « Obsolète, refonte UI transversale à tous les lots ».
- **CORR 10** : contradiction 12 métiers — « 12 métiers v1 » →
  « 12 profils cible longue durée, 1 métier v1 (technicien forestier) ».
- **CORR 11** : diagnostics — onglets fixes → **cartes conditionnelles**
  (apparaissent selon protocoles installés, territoire, métier,
  abonnement, mission, données disponibles).
- GeoSylva spec passe en v0.9.0 — Candidate for Review (commit `684f185`
  sur `fix/enterprise-reliability-2026-07-21`, +284/-68 lignes).

## [DOCUMENTATION — GEOSYLVA-003 V0.8.0] - 2026-08-04

- **Section §29 — Architecture des écrans, navigation et refonte UI/UX**
  (+750 lignes, 31 sous-sections).
- **Audit des 27 écrans existants** (5 NavGraphs) classés en 3
  catégories : conservés/enrichis (18), transformés (10), nouveaux (21).
- **Décisions de cadrage UI** :
  - Bottom nav 5 entrées (Accueil, Missions, Carte, Données, Compte)
    remplace le démarrage direct sur Forets.
  - Écran Martelage → **SynthèseMartelage** (s'ouvre auto après martelage,
    plus écran de saisie).
  - Carte : **refonte complète** (3ème entrée bottom nav, carte globale
    workspace ; ancien Map par parcelle conservé depuis les fiches).
  - Settings **supprimé** → tout dans Compte (16 sections).
  - Diagnostics (stationnel/ripisylve/IBP) **déplacés** en onglets fiche
    parcelle + protocoles Mission Engine (plus de NavGraphs séparés).
- **Roadmap §12.4 enrichie** : colonne « Pages UI » par lot + Quality
  Pass final. La refonte UI/UX accompagne chaque lot technique.
- GeoSylva spec passe en v0.8.0 (commit `d23a9d0` sur
  `fix/enterprise-reliability-2026-07-21`, +750/-14 lignes).

## [DOCUMENTATION — GEOSYLVA-003 V0.7.0] - 2026-08-04

- **Cadrage** suite à la revue critique du Fondateur (10 corrections
  critiques, roadmap refondue, structure territoriale, corrections de
  forme).
- **CORR 1** : avertissement monolithique en §3 + §28 Annexe listant 11
  RFC à extraire (RFC-0001 à RFC-0008, RFC-IA-MODEL-SELECTION, RFC-0018,
  RFC-0019).
- **CORR 2** : modèles IA (SmolLM3, Phi-3, Mistral, Phi-4) remplacés par
  profils T1-MICRO/STANDARD/T2-EDGE/T3-SERVER + RFC renouvelable
  `RFC-IA-MODEL-SELECTION-YYYY-MM`. Latences → objectifs à mesurer (P50,
  P95, tokens/s, RAM). Pack 500 Mo corrigé (3B INT4 = ~1,5 GB).
- **CORR 3** : PureForest TFLite reformulé comme modèle à entraîner/adapter
  + étape audit dataset 7 phases (audit licence, nettoyage, découpage,
  benchmark, conversion, validation terrain).
- **CORR 4** : TreeVision §18.10 colonne « Précision » → « Statut initial »
  + seuils de passage (Prototype → expérimental → assistance → mesure
  professionnelle validée).
- **CORR 5** : GNSS exemples ±1,9 m → objectifs pédagogiques + covariance,
  résidus, poids dynamiques (jamais constantes métier).
- **CORR 6** : migration Google→Keycloak 3 cas (sub vérifié / adresse
  vérifiée / identité ambiguë) + UUID Quintessences indépendant (pas
  dérivé de Google).
- **CORR 7** : identifiant appareil = UUID installation + paire clés
  Keystore + clé publique enregistrée (pas Android ID hashé).
- **CORR 8** : jetons = stockage chiffré + clé Keystore non exportable
  (Keystore stocke des clés, pas des jetons).
- **CORR 9** : séparation Entitlement / Feature module signé / Pack QPIS
  (un pack QPIS ne doit jamais injecter du code exécutable non signé).
- **CORR 10** : tableau licences enrichi (8 colonnes) + données
  institutionnelles (IGN, INPN, BRGM, Copernicus, datasets IA).
- **Roadmap refondue** : 11 lots (0-10) remplaçant P0-P7. Fondations
  (audit, contrat données, noyau scientifique, Mission Engine, identité,
  sync, QPIS, Geo Engine) avant TreeVision R&D, IA locale et Meshtastic.
- **Structure territoriale** : 8 entités distinctes (Property, Forest,
  CadastralParcel, ManagementUnit, ForestParcel, Stand, SamplingUnit,
  Plot).
- **Corrections de forme** : typo « contournée », « connaissances
  cachées » → « disponibles localement », `source` → `entry_mode` +
  `transport`, `auteur` → UUID, `session_id` optionnel.
- GeoSylva spec passe en v0.7.0 (commit `99c6a2d` sur
  `fix/enterprise-reliability-2026-07-21`, +321/-99 lignes).

## [DOCUMENTATION — GEOSYLVA-003 V0.6.0] - 2026-08-04

- Intégration complète de la conversation ChatGPT source (155k caractères)
  : 23 recommandations issues de l'analyse comparative conversation vs Dev
  Pack vs spec v0.5.0.
- **§7 enrichi** (7 sous-sections) : système qualité données (6 états, 6
  niveaux, exemples), campagnes multiannuelles (placettes permanentes),
  architecture moteurs spécialisés (9 domaines, 30 composants), règles
  déclaratives (exemple JSON + décision Kotlin dédié), chaîne valorisation
  (exemple chiffré), versionnement méthodes (scénario migration), IA vs
  moteurs déterministes.
- **§10.1** Catégories de consentement (5 catégories).
- **§16.10-16.12** GSIE usine de packs + Pack Store commun + intelligence
  locale de recommandation.
- **§17.10** Exemple de protocole déclaratif ODK YAML.
- **§18.11-18.18** TreeVision (8 sous-sections) : philosophie coopérative,
  méthodes A/B RANSAC, modèle de confiance, contrôles cohérence, GNSS
  immobilisation, constellations, SpatialEvidence, calibration.
- **§19.7-19.11** Services techniques GSIE + 14 technologies open source
  + Meshtastic détaillé + décisions MapLibre/Room.
- **§20.13-20.17** Droits basés sur capacités (10 exemples) + alternatives
  rejetées (Firebase, Auth0, Clerk) + SCIM + 4 phases déploiement +
  architecture finale recommandée.
- **Nouvelles sections §21-§25** : Diagnostic de station, Scénarios
  sylvicoles, Organisation travaux forestiers, Documents de gestion
  durable, Références locales de marché.
- Renumérotation : §21→§26 Références, §22→§27 Historique.
- GeoSylva spec passe en v0.6.0 (commit `a01bdfc` sur
  `fix/enterprise-reliability-2026-07-21`, +857 lignes).

## [DOCUMENTATION — GEOSYLVA-003 V0.5.0] - 2026-08-04

- Vérification section par section de la spec v0.4.0 face aux documents
  sources du Dev Pack. Correction de 9 écarts et 3 tensions logiques.
- **§4.2 amendé** : pointe vers §20 comme architecture cible (transition
  Keycloak), les comptes entreprise ne sont plus « en développement ».
- **§16.9 Droits et abonnements** : chaîne logique Subscription ↔ QPIS via
  EntitlementResolver (comble la tension T3).
- **§17.9 Catalogue de protocoles** : 4 sources (officiels, organisationnels,
  pédagogiques, communautaires) + 11 métadonnées.
- **§18.10 Modes TreeVision** : rapide, précis, calibration, placette
  semi-automatique.
- **§20.2 enrichi + §20.2.1** : justification Keycloak auto-hébergé, méthodes
  connexion Quintessences (passkey principal, TOTP/codes récupération
  secondaire, mot de passe compatibilité).
- **§20.5 enrichi** : interdictions Android (WebView, secret APK, flux
  implicite, flux mot de passe direct, jetons en clair).
- **§20.9 Migration** : procédure de transition Google direct → Keycloak
  (liaison automatique au premier login, période de transition, fallback).
- **§20.10 Connexion entreprise** : petite structure (invitation) vs grande
  structure (détection domaine → SSO entreprise → Keycloak broker).
- **§20.11 Sécurité administrative** : passkey obligatoire, second facteur,
  session réduite, journal, révocation appareils.
- **§20.12 Gestion des jetons** : access 5-10min, refresh rotation, session
  normale vs admin, vérifications API (signature, iss, aud, exp, session,
  rôles, org active).
- GeoSylva spec passe en v0.5.0 (commit `fe9be9d` sur
  `fix/enterprise-reliability-2026-07-21`).

## [DOCUMENTATION — GEOSYLVA-003 DEV PACK] - 2026-08-04

- Enrichissement de la spécification fonctionnelle GeoSylva 3.0 (v0.4.0) :
  intégration du GeoSylva Quintessences Dev Pack (brainstorming ChatGPT,
  `21_EXPERIMENTS/GEOSYLVA_DEV_PACK_2026-08-04/`).
- **§16 QPIS** — Quintessences Pack Intelligence System : 7 types de packs,
  manifestes, états, téléchargement intelligent, Storage Budget Manager,
  mise à jour différentielle. Le §9 existant est un sous-ensemble de QPIS.
- **§17 Mission Engine et Protocol Engine** : 12 métiers, capabilities,
  missions, protocoles déclaratifs versionnés (inspiré ODK/Open Foris),
  formulaires contextuels, workflows de validation, tableaux de bord par
  métier.
- **§18 TreeVision** : mesure multimodale des arbres (caméra, profondeur,
  IMU, GNSS, instruments), hiérarchie des sources, correction humaine,
  position améliorée (Kalman, triangulation), indice de confiance, banc de
  validation, boucle GSIE.
- **§19 Métiers, capabilities et adaptation contextuelle** : 20 objets
  communs Quintessences, unité territoriale partagée (7 modules), deep
  links interapplications, architecture modulaire (platform/forest-core/
  mission-engine/geo-engine/treevision), moteurs locaux/serveur/hybrides
  avec parité, distance de débardage sur graphe.
- **§20 Identité fédérée et organisations** : Keycloak, OIDC PKCE S256,
  passkeys/WebAuthn, UUID Quintessences immuable, modèle
  (QuintessencesUser, ExternalIdentity, Organization, Workspace, etc.),
  flux Android, hors ligne, séparation identité/autorisation métier,
  liaison de comptes.
- **§12.8 Vision long terme (Dev Pack)** : 10 phases (0-9) du Dev Pack
  comme complément de la roadmap P0-P7 existante.
- **Renumérotation** : §16→§21 Références, §17→§22 Historique.
- ROADMAP.md racine : section GeoSylva 3.0 mise à jour (v0.4.0).

## [DOCUMENTATION — GEOSYLVA-003 ROADMAP] - 2026-08-03

- Enrichissement de la spécification fonctionnelle GeoSylva 3.0 (v0.2.0) :
  roadmap structurée §12 consolidant la documentation existante.
- **Architecture cible** : trois axes distincts (cœur offline, canal 1 GSIE
  Serveur, canaux 2-3 terrain) avec schéma et principes non négociables.
- **Cascade LLM multi-tier** : T1 mobile (SmolLM3 3B), T2 edge (Mistral 7B),
  T3 serveur (Phi-4-reasoning 14B). Règle : le LLM appelle les moteurs, ne
  calcule jamais de mémoire (ADR-009).
- **Connexion GSIE Serveur** : tableau des 8 moteurs appelés par GeoSylva
  (Correlation, Reasoning, Diagnostic, Recommendation, Forest Dynamics,
  Simulation, Botanical, Learning) avec rôle, déclencheur et statut.
- **8 phases** (P0 fondations → P7 refonte visuelle) avec livrables,
  dépendances et 6 décisions/RFC requises.
- **Sources consolidées** (§12.7) : VOLUME_CALCULATION_NEXT_GEN §10/§16,
  RESEARCH_OPPORTUNITIES §3, VISION_LLM_SPECIALISES, RFC-0003, RFC-0019,
  RFC-0018, contrats 14 moteurs, GEO-001 à GEO-004, MASTER_PLAN.
- ROADMAP.md racine : section GeoSylva 3.0 mise à jour avec architecture
  cible, cascade LLM, phases et sources consolidées.

## [RFC — GEOSYLVA-003 DÉTAILLÉ] - 2026-08-03

- Spécification GeoSylva 3.0 enrichie (v0.3.0) avec deux sections majeures :
- **§14 Connexion GSIE Serveur détaillée** : enveloppes communes de
  requête/réponse (requete_id, session_id, source_reference,
  evidence_level), tableau des 8 moteurs avec déclencheurs, chaîne
  d'analyse approfondie (Correlation → Reasoning → Diagnostic →
  Recommendation → Simulation), cache local SQLCipher avec badges
  version/obsolescence, pull serveur→mobile, résolution de conflits,
  SDK Kotlin, garde-fous ADR-009/CON-001/CON-004.
- **§15 LLM on-device et multi-tier détaillée** : architecture 3 tiers
  (T1 mobile SmolLM3 3B ONNX, T2 edge Mistral 7B, T3 serveur vLLM),
  règles de cascade, adaptateurs LoRA GeoSylva-Forest, RAG scientifique
  (pgvector + RFC-0019), identification essence on-device (TFLite +
  PureForest), assistant vocal (Vosk FR), distribution via packs de
  données, banc d'évaluation GSIE-Eval-FR, choix de modèles.
- **RFC-0033** créée : contrats d'interface GeoSylva ↔ moteurs GSIE.
  Endpoints par moteur, orchestrateur, SDK Kotlin, cache, pull, conflits.
- **RFC-0034** créée : IA forestière on-device et multi-tier. Choix
  SmolLM3 3B, runtime ONNX, RAG local SQLite-vec, quantification INT4,
  cascade, identification TFLite, assistant vocal, RGPD audio.
- ROADMAP.md : références aux RFC-0033 et RFC-0034 dans les phases P4/P5.

## [DÉCISIONS — DEC-000049, DEC-000050] - 2026-08-03

- **DEC-000049** : contrats d'interface GeoSylva ↔ moteurs GSIE (RFC-0033
  adoptée). Enveloppes communes, 8 endpoints moteurs + 2 orchestration +
  1 pull, SDK Kotlin, cache local, résolution conflits. Phase P4.
- **DEC-000050** : IA forestière on-device et multi-tier (RFC-0034 adoptée).
  T1 SmolLM3 3B ONNX, T2 Mistral 7B edge, T3 serveur vLLM. RAG local
  SQLite-vec, identification TFLite PureForest, assistant vocal Vosk FR,
  banc GSIE-Eval-FR. Phase P5.
- RFC-0033 et RFC-0034 passées en statut `Adopté`.

## [DOCUMENTATION — GEOSYLVA-003] - 2026-08-03

- Création de la spécification fonctionnelle GeoSylva 3.0 : parcours
  Projet→Forêt→Parcelle→Placette→Martelage, onboarding, cartographie, packs,
  échanges terrain et mode développeur.
- Ajout de la doctrine scientifique imposant provenance, unités, incertitudes,
  tests reproductibles et prise en compte explicite de la qualité du bois et des
  observations sanitaires, y compris le contexte des parcelles voisines.

## [SESSION 2026-08-03 — SYNCHRONISATION PARCELLES GEOSYLVA] - 2026-08-03

### DEC-000048 — première donnée métier connectée à GSIE

- API privée `/api/v1/sync/geosylva/parcelles` authentifiée et isolée par
  compte, avec liste paginée, validation stricte et quotas.
- Migration Alembic `20260803_0031` : schéma `gsie_synchronisation`, table de
  répliques, index propriétaire/date, RLS forcée et absence de droit `DELETE`
  pour le rôle applicatif.
- Écritures idempotentes par UUID d’opération, version optimiste et réponse
  HTTP 409 contenant l’instantané courant sans écrasement automatique.
- Suppressions conservées sous forme de tombstones.
- GeoSylva Room v33 : file chiffrée, reprise WorkManager, refresh de session
  sur 401, backoff réseau et états visibles dans les options développeur.
- Réclamations et réponses de file conditionnées par UUID : une réponse réseau
  ancienne ne peut pas écraser une modification locale plus récente ; les
  lots supérieurs à 50 éléments déclenchent une continuation.
- Première transmission soumise à une action explicite ; compte facultatif et
  cœur forestier hors ligne préservés.

### Preuves

- API : 6 tests de service/contrat et 8 tests migration/PostgreSQL ciblés
  passent ; Ruff et mypy strict sont verts.
- Android : compilation debug réussie ; 5/5 tests de projection, politique de
  reprise et migration Room passent, schéma v33 exporté ; campagne complète
  de 518/518 tests et lint sans erreur.

## [SESSION 2026-08-03 — BORDURE CLOUDFLARE ZERO TRUST] - 2026-08-03

### DEC-000047 — protocole réseau GSIE

- Cloudflare Tunnel adopté comme entrée publique optionnelle, sortante
  uniquement, sans exposition directe de l'origine.
- Séparation formelle des flux publics, machine-à-machine, plan de contrôle
  Fondateur et réseau Docker interne.
- Mobile : HTTPS, WAF et JWT GSIE ; aucun secret Cloudflare ou certificat mTLS
  commun dans les APK.
- Services de confiance : Cloudflare Access ou mTLS sur un nom dédié, puis
  identité et rôles GSIE obligatoires.
- Profil Compose `edge`, image `cloudflared` 2026.7.2 verrouillée par digest,
  token monté comme secret et healthcheck natif du tunnel.
- Quotas GSIE compatibles avec `CF-Connecting-IP` uniquement lorsque le mode
  tunnel est explicitement activé.

### Fiabilité outbox

- Remplacement du faux healthcheck HTTP hérité de l'image API par un battement
  écrit après chaque cycle PostgreSQL/Redis réussi.
- Sonde Docker dédiée refusant un battement absent ou vieux de plus de trente
  secondes.

## [SESSION 2026-08-03 — CYCLE COMPLET DU COMPTE LOCAL] - 2026-08-03

### DEC-000046 — profil, vérification et récupération

- API du profil courant avec modification du nom affiché.
- Vérification d'adresse et récupération de mot de passe par codes Argon2id
  à usage unique, valables quinze minutes et jamais persistés en clair.
- Réponses anti-énumération et révocation des anciennes sessions après
  changement du mot de passe.
- SMTP configurable avec chiffrement obligatoire en production ; Mailpit
  captif sur `localhost:8025` pour le développement.
- Migration `20260803_0030` ajoutant la table temporaire des actions
  d'identité et la version de session.
- GeoSylva complète désormais le profil, la vérification, la récupération et
  le diagnostic développeur, sans dépendance du cœur forestier hors ligne.

### Preuves

- Cycle Docker réel validé de bout en bout : inscription, profil,
  vérification, récupération, révocation de l'ancienne session et
  reconnexion.
- Domaine identité Python : 170 tests passés ; modules de cycle, dépôt et
  courrier transactionnel couverts à 100 %, Ruff et mypy strict verts.
- Suite API complète antérieure : 1 936 tests passés, 63 ignorés ; les
  nouveaux tests de fermeture passent, mais la relance globale a dépassé la
  fenêtre locale de dix minutes sans échec observé.
- GeoSylva : 513 tests passés, 0 échec, 0 ignoré ; Lint 0 erreur bloquante ;
  APK debug produit et parcours vérifié sur émulateur Android.

## [SESSION 2026-08-03 — CLIENT IDENTITÉ GEOSYLVA] - 2026-08-03

### DEC-000045 — première interface mobile Quintessences

- Trois écrans Jetpack Compose distincts dans le repo externe GeoSylva :
  connexion/création, gestion du compte et options développeur.
- Client Retrofit du contrat GSIE, fournisseurs publiés dynamiquement,
  connexion locale et Google Credential Manager avec nonce serveur.
- Jetons GSIE conservés dans un coffre Android chiffré, jamais dans DataStore,
  les logs ou l’interface.
- Mode développeur persistant activable après huit pressions sur la version ;
  diagnostic en lecture seule de `/health`, `/ready`, des fournisseurs, de la
  session, du build et de l’appareil.
- Le geste local n’accorde aucun rôle. Toute future commande réservée au
  Fondateur devra être contrôlée côté serveur.
- Cœur forestier hors-ligne préservé et aucune donnée de terrain synchronisée
  par cette tranche.

### Preuves

- `:app:compileDebugKotlin` : succès.
- `:app:assembleDebug` : APK de débogage produit.
- `:app:lintDebug` : succès, 0 erreur (576 avertissements non bloquants).
- 513 tests unitaires : 513 passés, 0 échec.
- Documentation GeoSylva, politique de confidentialité, registre des
  traitements, mémoire, roadmap et spécification d’identité synchronisés.

## [SESSION 2026-08-03 — IDENTITÉ QUINTESSENCES MULTI-FOURNISSEURS] - 2026-08-03

### RFC-0032 / DEC-000044 — socle serveur livré

- Compte Quintessences canonique commun à toutes les applications de
  l’écosystème, séparé des moyens de connexion.
- Inscription et connexion locales avec normalisation d’e-mail, mot de passe
  Argon2id et erreurs anti-énumération.
- Connexion Google OpenID Connect côté serveur : validation par audience,
  émetteur et sujet stable `sub`, e-mail vérifié, nonce à usage unique ; aucun
  rapprochement silencieux par adresse e-mail.
- Rattachement Google explicite à un compte déjà authentifié.
- Jetons GSIE RS256 et refresh rotatif conservés quelle que soit l’origine de
  connexion.
- Découverte des fournisseurs ; connexion professionnelle OIDC/SAML déclarée
  « En développement » sans fausse activation.

### Persistance et sécurité

- Migration réversible `20260803_0029` : `user_account`,
  `identity_provider_link`, `local_credential`, `account_role` dans
  `gsie_rgpd_identites`.
- Le rôle `gsie_application` reçoit seulement `SELECT`, `INSERT` et `UPDATE`
  sur ces quatre tables, sans `DELETE` et sans accès à `data_subject` ou aux
  consentements.
- Configuration documentée pour les client IDs Google et le stockage Redis
  des nonces.

### Preuves exécutées

- Migration base vierge → head → downgrade → head et parité SQLAlchemy :
  **2 tests passés**.
- Isolement RGPD réel sous rôles PostgreSQL : **48 tests passés**.
- Suite unitaire globale : **1 915 tests passés**, 63 ignorés, 0 échec,
  **100 % de couverture** (9 338/9 338 instructions).
- Dépôt d’identité PostgreSQL : **4 tests d’intégration passés**.
- Ruff, formatage, mypy strict et quatre gardes de gouvernance/cohérence verts.

### Suites prévues avant ouverture publique

- vérification de l’adresse e-mail et récupération du mot de passe ;
- configuration et validation de la marque OAuth Google ;
- écrans de compte web et GeoSylva ;
- MFA administrateur puis fédération entreprise OIDC/SAML.

## [SESSION 2026-08-02 (soir) — PHASE DE STABILISATION CLÔTURÉE] - 2026-08-02

### Phase de stabilisation DEC-000043 — 3/3 livrables clôturés

**S1 — Restauration DB prouvée** (`74b1b59`)
- Backup pg_dump → restore sur base vierge → vérification d'intégrité
- 127 tables, 327 FK, 475 index, 6 RLS, 464 fonctions PostGIS
- Parité source/restaurée ✓ (tables, FK, index)
- Scripts : `test_restauration_db.sh` (bash), `test_restauration_db.py` (CI)
- Document : `DR-RESTAURATION.md`

**S2 — Tranche verticale réelle** (`b6b61f6`)
- Chaîne complète : Reasoning → Diagnostic → Recommendation → Validation
- Données réelles : Parelle 2007 (Quercus robur vs petraea), 29 faits vérifiés
- 2 conclusions (acidité + engorgement), diagnostic persisté, 1 recommandation
- Validation : `valide`, aucune cause de blocage
- Temps chaîne : 0.15s
- Script : `tranche_verticale.py`, document : `TRANCHE_VERTICALE.md`

**S3 — Validation scientifique + benchmark** (`56d4ba5`)
- 3 scénarios ground truth, 18/18 checks validés
- Latence moyenne : 32.05ms, p95 : 34.68ms, p99 : 34.68ms
- Throughput : 0.35 req/s (limité par rate limit 20/min)
- Mémoire peak : 0.25 MB
- Script : `validation_benchmark.py`, document : `VALIDATION_SCIENTIFIQUE.md`

### Gates mis à jour

Gates 4 (Science), 5 (Intégration), 6 (Performance) passent de ❌ à ⚠️ :
la preuve de chaîne complète est faite, les restes sont documentés.

---

## [SESSION 2026-08-02 (soir) — CONSOLIDATION + DEC-000043] - 2026-08-02

### Consolidation mémoire

- `PROJECT_MEMORY.md` : en-tête + section « État réel mesuré » avec
  chiffres vérifiés (14 moteurs, 28 migrations, 120 tables, 83 routes,
  1859 tests, 100% couverture, mutation 67/67). Diagnostic Fondateur
  intégré. Phase de stabilisation documentée.
- `ROADMAP.md` : ligne « Couverture 100% » + section « Phase de
  stabilisation » (S1/S2/S3). Gates 4/5/6 → ❌ (bloqués par S2/S3).
- `DEC-000043` : décision formelle de phase de stabilisation.

### État final mesuré

- **1859 tests passed**, 63 skipped, 0 failed
- **100% couverture** (8831/8831 statements)
- **Score mutation 67/67** (100%)
- ruff OK, mypy OK

### Diagnostic Fondateur

> Le code est plus mature que le produit intégré.

Rapidité 9/10, qualité technique 8/10, qualité produit 6,5-7/10.
Phase de stabilisation décidée : S1 restauration DB, S2 tranche verticale
réelle, S3 validation scientifique + performance.

---

## [SESSION 2026-08-02 — RFC-0031 PHASE 1 IMPLÉMENTÉE + PHASE 2 INTÉGRÉE] - 2026-08-02

### RFC-0031 Phase 1 — 3 quick wins restants implémentés

- **uvloop** (action 6) : `pyproject.toml` + `worker.py` — `loop=uvloop`
  dans SecureUvicornWorker (Linux uniquement, 2-4x plus rapide qu'asyncio)
- **Uptime Kuma** (action 7) : `docker-compose.yml` — conteneur de monitoring
  uptime sur port 3001, surveille /health et /ready
- **API PlantNet** (action 8) : `plantnet_client.py` — client ResilientHttpClient
  pour identification de plantes par image (78 810 espèces), POST multipart,
  7 tests unitaires + 5 tests factory de résilience. `http_client.py` étendu
  avec `_post_multipart_json` pour upload + parse JSON.

**Tests** : 1837 passed, 63 skipped, 0 failed (4 workers xdist).

### ROADMAP.md — Phase 2 intégrée

Les 12 actions Phase 2 du RFC-0031 (court terme, 3-6 mois) sont intégrées
dans `ROADMAP.md` : pg_cron/pg_trgm/HypoPG, index partiels/BRIN, cursor
pagination, SSE helper, backpressure middleware, audit logging immutable,
Hypothesis/Schemathesis, Grafana Stack, Polars, GeoPandas/DuckDB Spatial,
BD Forêt v3/Sentinel-2, NeuralProphet.

### Bug fix — tests flaky xdist 8 workers

`PYTEST_XDIST_AUTO_NUM_WORKERS=4` persisté au niveau utilisateur. Les tests
`test_tout_endpoint_limite_declare_response` et `TestConfigApiRootFallback`
échouaient aléatoirement avec 8 workers (saturation page file Windows,
documenté dans `docs/TESTING_XDIST.md`).

---

## [SESSION 2026-08-02 — VEILLE TECHNOLOGIQUE + SOURCING + RFC-0031 ADOPTÉ] - 2026-08-02

### Veille technologique (8 sous-agents en parallèle)

Document de synthèse : `21_EXPERIMENTS/VEILLE_TECHNO_2026-08-02.md`.
Domaines couverts : DB PostgreSQL/PostGIS, Moteurs AI/ML, API FastAPI,
Géospatial, Observabilité/Sécurité, Concurrence forestière, Infrastructure
DevOps, Data pipelines/science.

**Position concurrentielle** : GSIE occupe un positionnement unique
(14 moteurs intégrés, multi-domaines, multi-applications, prescriptif).
19 concurrents directs identifiés. Stratégie recommandée : partenariats
intégratifs (IGN, INRAE, CIRAD, PlantNet, Arboreal, Dryad, CTrees, GFW).

### Correction post-revue dépôt (5 écarts)

1. Security headers — **déjà implémentés** dans `middleware.py:25-33`
2. pg_stat_statements — **déjà activé** (`docker-compose.yml:36`)
3. Apache AGE — **déjà déployé** (`shared_preload_libraries=age`)
4. API versioning `/api/v1/` — **en place depuis l'origine**
5. PgBouncer — config présent mais **service orphelin non déployé**

### Sourcing des chiffres (2 sous-agents recherche web)

31 chiffres vérifiés : 14 vérifiés, 14 partiellement vérifiés (corrigés
avec contexte), 3 reformulés. Sources citées inline + §14 « Sources ».
Niveau de preuve passé de D (quarantaine) à C (sourcé).

Corrections notables : vLLM 793 tok/s (contexte 256 users), NeuralProphet
+55-92% (short/medium-term), OpenObserve 87x (pas 140x, benchmark éditeur),
Polars 3-11x (pas 5-10x, selon opération), PlantNet 78 810 (pas 77k),
CAPSIS 25 package ONF / ~80 total, SILVA TU Munich (pas INRAE), QLoRA 6GB
(pas LoRA), GPTQ/AWQ <4% (pas <1%), k6 30k-40k VU (pas 2000+).

### RFC-0031 — Adopté (DEC-000042)

`02_RFC/RFC-0031-feuille-de-route-post-veille-2026-08-02.md` **Adopté**
par le Fondateur le 2026-08-02 (DEC-000042) :
- **Phase 1** (8 actions, 5 déjà faites : orjson, Trivy, Bandit,
  Dependabot, Tenacity ; 3 à faire : uvloop, Uptime Kuma, PlantNet)
- **Phase 2** (12 actions adoptées en principe)
- **Écartées** (16 actions)
- **Différées Phase 3-4+** (10 actions)

**Intégration ROADMAP suspendue** à la demande du Fondateur — le feu vert
pour l'intégration des actions Phase 2 dans `ROADMAP.md` sera donné
ultérieurement. Les 3 actions Phase 1 restantes peuvent être implémentées
immédiatement.

### Implémentations effectives

- **orjson** : `default_response_class=ORJSONResponse` dans `app.py`
- **Trivy** dans CI : job `security-scan` (`ci.yml`)
- **Bandit** dans CI : job `python-sast` (`ci.yml`)
- **Dependabot** : `.github/dependabot.yml` (pip + docker + github-actions)
- **Tenacity** : `pyproject.toml` (8.5.0)

### Validation

- ruff : OK sur `app.py` (erreurs préexistantes dans test_auth_coverage.py)
- mypy : Success, no issues found (155 fichiers)
- pytest unit : 1294 passed, 2 failed préexistants (Redis + botanical)

---

## [SESSION 2026-08-02 — CORRECTIONS AUDIT PHASE 4 + AUDIT CLAUDE] - 2026-08-02

### Gouvernance — DIR-0005 et DIR-0006 passent en Review

- **GSIE-DIR-0005** (Directive fondatrice Ignis / GCS) : Draft → Review.
  Justification : livrables en pilote actif (Centre de Commandement
  UE5.8 configuré sur `E:\GSIE-Centre-Commandement`, DEC-000010).
- **GSIE-DIR-0006** (Vision du Moteur Cognitif Ignis) : Draft → Review.
  Même justification.
- Décision du Fondateur (Camille Perraudeau), tracée dans
  `PROJECT_MEMORY.md` (section Documents structurants).

### Audit Claude — 6 corrections (P1/P2)

1. **P1 Rate limiting** : `storage_uri="memory://"` dans conftest.py
   (compteur par processus xdist), limiter actif pour tous les tests.
2. **P1 validation_result** : FK vers resource existante (plus de
   resource fantôme), Revision créée (invariant CON-010), persistance
   obligatoire (erreur si pas de session), docstring enrichment.py
   corrigée.
3. **P1 SynopClient** : cache LRU borné (5 entrées, OrderedDict),
   verrou par année (asyncio.Lock), TTL 24h.
4. **P2 _FICHIERS_SERIAL** : groupe xdist renommé `shared_state_serial`.
5. **P2 stdout/stderr.txt** : supprimés + .gitignore.
6. **P2 ClimateEngine** : `logger.warning` sur CSV mal formé (clés
   surnuméraires).

### Audit Phase 4 — 7 P1 restants corrigés

1. **P1-3 HEALTHCHECK Dockerfile** : déjà présent (lignes 94-96).
2. **P1-4 Traçabilité DEC** : DEC-000024/028/034/040 ajoutées à
   `PROJECT_MEMORY.md` (section Décisions actives) et `CHANGELOG.md`.
3. **P1-7 OpenAPI versionnée** : script `scripts/extract_openapi.py`
   + `docs/openapi.json` (73 paths, 142 schemas, version 0.1.0).
4. **P1-8 Skill /gsie-governance** : créée dans
   `.devin/skills/gsie-governance/SKILL.md` (158 lignes).
5. **P1-6 README moteurs** : enrichissement contrats d'interface (14
   moteurs, en cours via sous-agent documentation).

### Validation

- ruff : All checks passed
- mypy : Success, no issues found
- pytest unit : 1453 passed, 62 skipped, 0 failed

---

## [SESSION 2026-08-02 — CORRECTION P1/P2 AUDIT MOTEURS GSIE] - 2026-08-02

Suite de l'audit Phase 4 du 2026-08-01. Correction des P1 et P2
identifiés sur les 14 moteurs GSIE. Tête Alembic `20260801_0028`
(28 révisions, 120 tables dans `Base.metadata`).

### P1a — Tests d'intégration pour 5 moteurs (résolu)

Création de 5 fichiers de tests d'intégration (47 tests au total) pour
combler le manque identifié dans l'audit :

- `tests/integration/test_evidence_engine.py` — persistance des
  `EvidenceStatement`, niveaux de preuve A-F, versionnement CON-010.
- `tests/integration/test_diagnostic_engine.py` — chaîne d'inférence
  complète, persistance du `QualificationConclusion`, plancher de
  preuve.
- `tests/integration/test_validation_engine.py` — persistance des
  résultats bloqués via `ValidationResultModel`, FK vers `resource`.
- `tests/integration/test_climate_engine.py` — observations
  quotidiennes DPClim, conversions d'unités, cache SynopClient.
- `tests/integration/test_learning_engine.py` — détection de patterns
  de blocage récurrents depuis `validation_result`.

Tous suivent le pattern `requires_docker` + `db_session` (pas de
`@pytest.mark.asyncio`, mode `auto`). 3/3 passent avec Docker, 47/47
sautés sans Docker (poste dev actuel).

### P1b — Cache SynopClient (résolu)

- **Problème** : `SynopClient` téléchargeait 18 Mo de CSV à chaque
  appel, même pour la même année.
- **Fix** : cache par instance avec TTL 1h (`_CACHE_TTL_SECONDS = 3600`),
  classe `_CachedFile` avec `__slots__`, cleanup par expiration.
  Aucune fuite mémoire (limité par nombre d'années).
- **Fichier** : `src/gsie_api/engines/climate/synop_client.py`.

### P1c — Migration Alembic pour `validation_result` (résolu, critique)

- **Problème** : le modèle `ValidationResultModel` existait dans
  `enrichment.py` mais **aucune migration Alembic** ne créait la table
  en base. Toute insertion aurait échoué avec
  `relation "validation_result" does not exist`.
- **Fix** : nouvelle migration `20260801_0028_validation_result_table.py`
  (head `20260801_0027` → `20260801_0028`). Crée la table avec FK
  `ON DELETE CASCADE` vers `resource(id)`, 3 index
  (`statut`, `date_validation`, `requete_origine`), commentaires
  `COMMENT ON` pour le data dictionary. Downgrade réversible
  (DROP TABLE + DROP INDEX).
- **Test** : `_HEAD` mis à jour dans `test_migration_contract.py`
  (`20260801_0027` → `20260801_0028`). 120 tables dans
  `Base.metadata` (confirmé).

### P2a — Refactor Knowledge engine.py (résolu)

Extraction des sous-responsabilités du `KnowledgeEngine` en méthodes
privées nommées (single responsibility, complexité cyclomatique ≤ 5).

### P2b — Persistance des résultats bloqués Validation Engine (résolu)

- **Problème** : les résultats `bloque`/`partiellement_valide`
  disparaissaient à la fin de la requête — le Learning Engine ne
  pouvait pas détecter les patterns de blocage récurrents (RFC-0028).
- **Fix** : nouveau modèle `ValidationResultModel` dans
  `enrichment.py` (table `validation_result`). Le `ValidationEngine`
  persiste via `AsyncSession` passée par le router. Seuls les
  résultats `bloque` et `partiellement_valide` sont persistés (les
  `valide` ne portent pas d'information d'apprentissage).
- **Tests** : 4 nouveaux tests dans `test_enrichment_models.py`
  (présence dans metadata, index sur `statut`, FK cascade, champs
  `statut` + `type_sortie`).

### P2c — Commentaire "déterministe" corrigé (résolu)

Le `gsie_id` du `ValidationEngine._persist_result` est dérivé d'un
`uuid4` (aléatoire), pas déterministe. Commentaire corrigé pour
refléter la réalité : « traçable sans être reproductible ».

### Validation

- **Ruff** : `All checks passed!` sur tous les fichiers modifiés.
- **Mypy** : `Success: no issues found` sur les 3 fichiers source clés.
- **Alembic** : head `20260801_0028`, upgrade + downgrade SQL validés.
- **Tests unitaires** : 1444 passés, 62 sautés, 8 échecs **préexistants**
  (7 `test_auth.py` + 1 `test_db_quality_metrics.py` flaky) — tous liés
  à Redis indisponible sur ce poste (`.env` → `redis://localhost:6379/1`),
  aucune régression introduite. Avec `memory://` forcé : 33/33 passés
  sur les tests ciblés (`test_migration_contract` +
  `test_enrichment_models` + `test_validation_engine`).

---

## [SESSION 2026-08-01 — AUDIT PHASE 4 : CORRECTION P0/P1/P2] - 2026-08-01

Audit Phase 4 strict mais juste. 5 dimensions, 22 preuves reproduites.
Score global 86%. Correction de tous les P1 et P2 actionnables.

### P1-1 — 14 tests en échec → 0 (résolu)

- **Cause racine** : pollution d'event loop asyncio + rate limiter partagé
  entre tests dans le même processus. Les 14 tests passaient en isolation
  mais échouaient en suite complète (segfault Pydantic sur Windows après
  ~1600 tests dans le même processus).
- **Fix 1** : activation de `pytest-xdist -n 2 --dist=loadfile` par défaut
  dans `pyproject.toml` → chaque fichier de test s'exécute dans son propre
  processus worker, isolant les fuites d'état.
- **Fix 2** : fixture autouse `_ensure_fresh_event_loop` dans
  `tests/conftest.py` → crée une nouvelle event loop si la courante est
  fermée (fix Windows `RuntimeError: Event loop is closed`).
- **Fix 3** : fixture autouse `_reset_rate_limiter` dans `conftest.py` →
  `limiter.reset()` avant chaque test pour éviter les `429 Too Many
  Requests` fallacieux (compteurs s'accumulant entre tests E2E).
- **Fix 4** : fixture `mock_lifespan` dans `conftest.py` + utilisation
  dans `test_app.py`, `test_auth.py`, `test_coverage.py` → mocke les
  connexions DB/Redis/WebSocket du lifespan pour éviter que des vraies
  connexions async ne polluent l'event loop.
- **Résultat** : `1640 passed, 114 skipped, 0 failed, 0 error`.

### P1-2 — 7 erreurs TypeScript ADMIN_WEB → 0 (résolu)

- `EngineStatusResponse` : ajout de `planned_week?: number` et
  `language?: string` (champs renvoyés par l'API mais absents du type).
- `ResourcesPanel.tsx` : 3 `class=` → `className=` sur SVG React
  (anti-pattern HTML → JSX).
- **Résultat** : `tsc --noEmit` exit 0, `npm run build` 12 pages 0 erreur.

### P2-10 — Warning fallback Rust au démarrage (résolu)

- **Cause racine** : le module Rust `gsie_evidence` (PyO3/maturin) n'était
  construit que dans le Dockerfile (stage builder). En dev local Windows,
  la wheel n'était pas installée → `ImportError` → fallback Python →
  warning `evidence_engine_rust_not_available_fallback_python`.
- **Fix** : build local de la wheel avec `maturin build --release` +
  installation dans le venv via `uv pip install`. Le moteur Rust est
  maintenant chargé en local (`evidence_engine_rust_loaded version=0.1.0`).
- **Documentation** : procédure de build local ajoutée au
  `ENGINES/EVIDENCE_ENGINE/README.md`.

### Documentation

- `docs/TESTING_XDIST.md` : mis à jour pour refléter l'activation par
  défaut de xdist et la résolution des contraintes 2 et 3.

---

## [SESSION 2026-08-01 — AUDIT QUALITÉ BASE + AMÉLIORATIONS PIPELINE TREEKIPEDIA] - 2026-08-01

Audit qualité de la base GSIE (post-ingestion 1000 espèces Treekipedia)
et intégration de toutes les améliorations identifiées, sans casser
l'existant.

### Audit qualité (constats)

- **P1-1 (résolu)** : Seq Scan sur `entity_alias(namespace, external_id)`
  à chaque lookup d'idempotence — coût 48.83, prohibitif à 135k lignes.
- **P1-2 (résolu)** : pas d'index GIN sur `resource.metadata_json`
  (qui stocke taxonomy, images, descriptions).
- **P1-3 (résolu)** : commit par lot de 10 fragile, pas de checkpoint.
- **P2-1 (résolu)** : 11 descriptions Wikipédia < 100 chars (stubs).
- **P2-2 (résolu)** : 1 image sans license.
- **P3-1 (résolu)** : images stockées dans `metadata_json` au lieu d'une
  table dédiée.
- **P3-2 (résolu)** : descriptions monolingues (EN uniquement).
- **P3-3 (résolu)** : pas de data dictionary (COMMENT ON COLUMN).

### Migration Alembic `20260801_0027`

- **Index unique composite** sur `entity_alias(namespace, external_id)` :
  Seq Scan → Index Scan unique (coût 48.83 → 8.30, 6× plus rapide,
  constant à 135k lignes) + contrainte DB d'unicité (aujourd'hui
  uniquement applicative).
- **Index GIN** sur `resource.metadata_json` (`jsonb_path_ops`) :
  recherche par clé JSONB accélérée.
- **Table `entity_image`** : images d'espèces (Wikimedia Commons, etc.)
  avec url, license, photographer, page_url, source, is_primary,
  validated_at, last_checked_at. Index sur `entity_id` + index unique
  partiel sur `is_primary=true`.
- **Table `entity_description`** : descriptions multilingues avec
  language, source, content, quality. Index sur `entity_id` + index
  unique `(entity_id, language, source)`.
- **Table `ingestion_progress`** : checkpoint de progression pour
  reprise automatique après crash. Colonnes : pipeline (unique),
  last_offset, total, status, started_at, metadata_json.
- **COMMENT ON COLUMN** : data dictionary sur 27 colonnes des tables
  centrales (resource, entity_alias, entity) et nouvelles tables.

### Modèles SQLAlchemy (`enrichment.py`)

- `EntityImageModel` : table `entity_image` (FK CASCADE vers resource).
- `EntityDescriptionModel` : table `entity_description` (FK CASCADE).
- `IngestionProgressModel` : table `ingestion_progress` (pipeline unique).
- Enregistrement dans `models/__init__.py` → `Base.metadata.tables`
  passe de 116 à 119 tables.

### Pipeline Treekipedia refactorisé

- **`ingest_treekipedia.py`** :
  - **Parallélisation GBIF** : `asyncio.Semaphore(concurrency)` avec
    `asyncio.gather` (défaut 5, configurable via `--concurrency`).
    Gain estimé : 6 min → ~2 min pour 1000 espèces.
  - **Batch inserts** : commit par lot de 100 (au lieu de 10).
  - **Checkpoint** : table `ingestion_progress` + option `--resume`
    pour reprise automatique après crash.
  - **Option `--offset`** : démarrer à un offset donné dans le CSV.
- **`enrich_treekipedia.py`** :
  - **Tables dédiées** : images → `entity_image`, descriptions →
    `entity_description` (au lieu de `metadata_json`).
  - **Filtrage stubs** : descriptions < 100 chars non stockées (P2-1).
  - **Qualité estimée** : high/medium/low/stub basé sur la longueur.
  - **Option `--migrate-metadata`** : migre les images/descriptions
    existantes de `metadata_json` vers les tables dédiées.
- **`validate_image_urls.py`** (nouveau) : validation des URLs
  d'images en base (HTTP HEAD parallèle), marque `last_checked_at`,
  supprime les liens morts avec `--fix`.

### WikimediaClient étendu

- **`get_species_description(language=...)`** : paramètre `language`
  (défaut "en", "fr" pour Wikipédia FR).
- **`get_species_description_with_fallback()`** : EN → FR si EN
  absent ou trop court (< 100 chars). Retourne `(description, langue)`.
- **Constante `_MIN_DESCRIPTION_LENGTH = 100`** : seuil de qualité
  d'une description (audit P2-1).

### Monitoring Prometheus (`metrics/db_quality.py`)

- **`gsie_entities_total`** : nombre total d'entities.
- **`gsie_aliases_total{namespace}`** : aliases par namespace.
- **`gsie_enrichment_completeness{field}`** : taux de complétude par
  champ (taxonomy, image, description, common_names — metadata et
  tables dédiées).
- **`gsie_descriptions_by_language{language}`** : descriptions par langue.
- **`gsie_descriptions_by_quality{quality}`** : descriptions par qualité.
- **`gsie_images_validated_total` / `gsie_images_unvalidated_total`** :
  images avec/sans validation d'URL.
- **`gsie_ingestion_progress_offset{pipeline,status}`** : progression
  des pipelines d'ingestion.
- **Endpoint `/metrics/db-quality`** (admin-only hors dev) : déclenche
  le calcul des métriques à la demande.

### Tests

- **`test_enrichment_models.py`** (11 tests) : vérifie l'enregistrement
  des 3 nouvelles tables dans `Base.metadata`, leurs index, FK, et
  contraintes.
- **`test_wikimedia_fallback_fr.py`** (8 tests) : vérifie le fallback
  EN → FR, le filtrage des stubs, et le routage par langue.
- **`test_migration_contract.py`** mis à jour : `_HEAD = "20260801_0027"`,
  `len(Base.metadata.tables) == 119`.
- **Total** : 1421 tests passent, 65 skipped, 0 échec (hors test_auth.py
  flaky Redis, non lié).

### Validation

- `ruff check` : 0 erreur sur tous les fichiers nouveaux/modifiés.
- `mypy --strict` : 0 erreur sur 153 fichiers source.
- `EXPLAIN` : Index Scan using `idx_entity_alias_ns_extid` (coût 8.30,
  vs Seq Scan 48.83 avant).

---

## [SESSION 2026-08-01 — TREEKIPEDIA : INGESTION + ENRICHISSEMENT 1000 ESPÈCES] - 2026-08-01

Ingestion et enrichissement d'un lot de 1000 espèces Treekipedia dans la
base GSIE, à partir du snapshot CSV local officiel (l'API distante
Treekipedia reste inaccessible — 404 sur tous les endpoints documentés).

### Pipeline

1. **Ingestion** (`ingest_treekipedia.py --limit 1000`) : lecture du CSV
   simple (67 928 espèces), résolution GBIF de chaque nom scientifique,
   création du taxon GSIE + alias Treekipedia (idempotent).
2. **Enrichissement** (`enrich_treekipedia.py --limit 1000`) : ajout de la
   taxonomie riche (genus, family, class, order) depuis le CSV export
   Treekipedia, des images Wikimedia Commons (pré-résolues JSON puis API
   en fallback) et des descriptions Wikipédia EN.

### Résultats

- **Ingestion** : 1000/1000 succès, 0 échec (~6 min). 655 taxons uniques
  (déduplication GBIF), 1000 aliases Treekipedia, 655 aliases GBIF.
- **Enrichissement** : 1000/1000 succès, 0 échec (~10 min).
  - `taxonomy` : 1000/1000 (CSV riche)
  - `description_wikipedia` : 857/1000 (API Wikipédia EN)
  - `image_api_commons` : 831/1000 (API Wikimedia Commons)
  - `image_pre_resolue` : 112/1000 (JSON images Treekipedia)
- **Tests** : 1403 passent, 65 skipped, 0 échec (aucune régression).

### Échantillon (Abies alba)

- taxonomy : `Pinaceae / Abies / Pinopsida / Pinales`
- 15 noms vernaculaires (EN, DE, NL, FR, DA, RU, JA…)
- image : Wikimedia Commons (CC-BY-SA-3.0)
- description : extrait introductif Wikipédia EN

### Fichiers

- `GSIE/API/ingest_treekipedia.py` — script d'ingestion (existe depuis
  session pilote 100 espèces).
- `GSIE/API/enrich_treekipedia.py` — script d'enrichissement.
- `GSIE/API/src/gsie_api/engines/botanical/treekipedia_client.py` —
  client CSV (simple + riche + images pré-résolues).
- `GSIE/API/src/gsie_api/engines/botanical/wikimedia_client.py` —
  client Wikimedia (Commons + Wikipédia).

### Suite possible

- Ingestion complète 67 927 espèces (~4h20 ingestion + ~16h enrichissement)
  — à déléguer au Devin Cloud ou en arrière-plan non-surveillé.
- Descriptions Wikipédia FR (fallback pour espèces européennes).
- Autécologie structurée (RFC-0016 — curateur humain requis).

---

## [SESSION 2026-08-01 — VISUALISATION DB + SDK PYTHON + TABLEAU DE CONTRÔLE] - 2026-08-01

Déploiement des outils de visualisation DB, création du SDK Python GSIE
et du tableau de contrôle admin web.

### Ajouts

- **Migration Alembic `20260801_0025`** : crée le groupe `gsie_viz_lecture`
  (NOLOGIN, SELECT sur 8 schémas, REVOKE explicite sur `gsie_rgpd` et
  `gsie_rgpd_identites`) + rattache les comptes `gsie_api` et `gsie_viz`
  à leurs groupes respectifs (`gsie_application`, `gsie_viz_lecture`).
- **Comptes de connexion DB** : `gsie_api` (LOGIN, NOSUPERUSER,
  NOBYPASSRLS) pour l'API + `gsie_viz` (LOGIN, NOSUPERUSER) pour les
  outils de visualisation. Créés via `docker/comptes-de-connexion.sql`.
- **`docker-compose.viz.yml`** : stack de visualisation avec profil `viz`
  (Metabase :3030, Superset :8088, Dekart :8089). Réseau `api_default`
  partagé avec la DB. Ports liés à `127.0.0.1`.
- **Metabase** : déployé + **initialisé via API** (compte admin créé
  depuis `GSIE_METABASE_ADMIN_EMAIL`/`GSIE_METABASE_ADMIN_PASSWORD`, DB
  « GSIE PostGIS » connectée, sync complète, PG 16.14 détecté, sample DB
  supprimée, locale fr).
- **Apache Superset** : déployé + initialisé (compte admin créé depuis
  `GSIE_SUPERSET_ADMIN_PASSWORD`, connexion DB « GSIE PostGIS »
  pré-configurée via CLI).
- **Dekart** : déployé avec datasource PostGIS
  (`DEKART_POSTGRES_DATASOURCE_CONNECTION`), stockage SQLite embarqué
  (sans licence), CORS restreint à `localhost:8089`.
- **SDK Python GSIE** (`GSIE/SDK/python/`) : client async `httpx`, auth
  JWT RS256 avec auto-refresh, wrappers moteurs (diagnostic,
  recommendation, validation, simulation), exceptions typées. Tests
  `respx` + `pytest-asyncio`. `ruff` + `mypy --strict` OK.
- **Tableau de contrôle admin** (`GSIE/ADMIN_WEB/`) : Astro 5 + React 19
  Islands + Tailwind CSS 4. Design calqué sur **Tabler** (sidebar
  groupée + topbar sticky avec search/notifications/user menu + cards
  avec header + stat cards avec icône/trend + badges semi-transparents
  + tables borderless). 4 pages (vue d'ensemble, moteurs, utilisateurs,
  données). Client API hybride (mock → API GSIE auto). Build OK, 0
  erreur, 0 warning, 0 hint.
- **Documentation du schéma DB** (`GSIE/DOCUMENTATION/SCHEMA_DB.md`) :
  120 tables, 2122 colonnes, 7 schémas. Générée par script SQL +
  Python (`GSIE/TOOLS/generate_schema_doc.py`), remplace SchemaSpy
  (incompatible PG16) et tbls (incompatible class-table inheritance).
- **Documentation** : `GSIE/DOCUMENTATION/VISUALISATION_DB_ACCES.md`
  (URLs, credentials, commandes Docker, architecture réseau, sécurité).
- **Veille** : `GSIE/RESEARCH/VEILLE_OUTILS_VISUALISATION_DB_2026-07-31.md`.
- **RFC-0030 + DEC-000040** : mapping Treekipedia ↔ métamodèle v6.2
  (Draft, en attente d'ingestion).

### Corrections

- **Audit concurrentielle** : P0-4 « 3 moteurs stubs » et P0-5
  « autécologie absente » invalidés — les moteurs Recommendation,
  Validation, Simulation et l'adapter autecology sont implémentés.
  Document `ANALYSE_CONCURRENTIELLE_2026-07-31.md` mis à jour.
- **Dekart** : variables `DEKART_POSTGRES_*` (backend métadonnées,
  licence requise) remplacées par `DEKART_POSTGRES_DATASOURCE_CONNECTION`
  (datasource, sans licence) + `DEKART_STORAGE=USER`.
- **Healthcheck Dekart** : `curl` absent de l'image → remplacé par test
  TCP via `/dev/tcp` (bash builtin).
- **SchemaSpy → script SQL** : SchemaSpy incompatible PG16
  (`datlastsysoid` supprimé) et tbls incompatible avec l'héritage
  class-table de PostgreSQL → remplacés par un script SQL + Python qui
  génère un markdown complet du schéma.

### Sécurité

- Barrière RGPD en base (pas dans l'outil) : `gsie_viz` n'a aucun USAGE
  sur `gsie_rgpd` ni `gsie_rgpd_identites` — vérifié par test.
- Comptes applicatifs NOSUPERUSER + NOBYPASSRLS.
- Mots de passe distincts de l'administrateur (refus sinon).
- Clés secrètes Metabase + Superset générées (non versionnées).

### P0 restants

| ID | Description | Statut |
|---|---|---|
| P0-1 | Sauvegardes DB (pgBackRest + WAL archiving) | À faire |
| P0-3 (2e moitié) | SDK Kotlin pour GeoSylva | À faire |
| P1-8 | Intégration GeoSylva/QGISIA ↔ GSIE via SDK | À faire |

---

## [DEC-000041 — INGESTION BULK + PGVECTOR + GARDE ANTI-INVENTION] - 2026-07-31

Préparation de l'API à recevoir des données externes massives (Treekipedia,
BD Forêt IGN, etc.) — débit 20x supérieur au mode unitaire.

### Ajouts

- **Pipeline bulk (P3)** : endpoint `POST /api/v1/resources/bulk` acceptant
  jusqu'à 1000 resources par lot en une transaction. Échec partiel (validation
  par item), rapport détaillé. Schémas `BulkIngestRequest/Result/ItemResult`.
- **Migration pgvector (P1)** : `20260731_0024` — extension `vector` + colonne
  `embedding(1536)` sur `entity` + index IVFFlat (cosine, lists=100). Débloque
  la recherche sémantique d'espèces (Treekipedia).
- **Garde anti-invention RFC-0014 automatisée (P2)** : détection automatique
  des sources AI-sourced (Claude, GPT, Treekipedia, etc.) dans
  auteur/référence/version → force `evidence_level=D` + `quarantine`.
  Intégrée au pipeline Evidence → Knowledge.
- **Rate limiting différencié (P4)** : config `rate_limit_bulk` (600/min) vs
  `rate_limit_evaluate` (30/min). L'endpoint bulk utilise la config.
- **Dockerfile.db** : installe `postgresql-16-pgvector` (dépôt PGDG).
- **Script d'init** `03-pgvector.sql` : crée l'extension à l'initialisation.
- **Modèle `EntityModel`** : déclare la colonne `embedding` (Vector(1536),
  nullable) via `pgvector.sqlalchemy`.
- **Dépendance** : `pgvector` (Python) + `psycopg2-binary` (test, pour Alembic).

### Tests

- 37 tests unitaires (anti_invention, bulk_ingest, rate_limit_bulk,
  migration_pgvector, migration_contract).
- 7 tests d'intégration bulk (pipeline bout-en-bout sur PostgreSQL).
- 2 tests d'intégration pgvector (upgrade + downgrade SQL sur vraie DB).
- 2 nouvelles mutations au harnais (garde_anti_invention, rate_limit_bulk).
- Suite unitaire complète : 1346 passed, 0 failed.

### Corrections

- `Dockerfile.db` : ajout de `postgresql-16-pgvector` (l'extension n'était pas
  disponible dans le conteneur — la migration aurait échoué en prod).
- `EntityModel` : ajout de la colonne `embedding` dans le modèle SQLAlchemy
  (la migration l'ajoutait en SQL mais l'ORM ne la connaissait pas).
- `conftest.py` : installation de pgvector à la volée dans le conteneur
  testcontainers + `CREATE EXTENSION vector` avant `create_all`.
- `test_migration_pgvector_integration.py` : test d'intégration qui exécute
  les SQL de la migration sur une vraie DB avec pgvector.

---

## [GSIE-PROMPT-0025 — INVENTAIRE SOURCES ÉLARGI] - 2026-07-30

Extension de l'inventaire des sources de données GSIE à un état viable 5 ans.
9 domaines thématiques traités (A-I) avec vérification URL exhaustive.

### Bilan

- **68 URLs testées** (webfetch), 82% de succès (10 échecs, tous confirmés par recherche)
- **48 entrées vérifiées** (YAML conformes RFC-0029 §11.3)
- **26 nouvelles sources** ajoutées à `SOURCES_DONNEES_EXHAUSTIVES.md` §6.10
- **34 sources à vérifier** identifiées (URL non testée ou statut incertain)
- **17 signalements** (13 critiques, 4 information)
- **5 corrections critiques** : Prométhée→BDIFF, INPN cyberattaque, ERA5T payant, donneespubliques.meteofrance.fr fermeture, CDSE STAC endpoint
- **Nouveau comptage total** : ~205 sources vérifiées + 34 à vérifier = ~239 potentielles (+33%)

### Fichiers

- `_staging_0025/{A-I}_*.md` : 9 fichiers partiels (48 entrées YAML vérifiées)
- `_staging_0025/_SYNTHESE.md` : synthèse consolidée
- `SOURCES_DONNEES_EXHAUSTIVES.md` : §6.10 ajouté (26 nouvelles sources) + §7 comptage mis à jour
- `DATASET_CATALOG.md` : DS-022 Prométhée marqué OBSOLÈTE, DS-022b BDIFF ajouté, historique mis à jour

### Branche

`feat/inventaire-sources-elargi` — 2 commits locaux (non poussés, en attente d'autorisation)

---

## [RFC-0028 — PERSISTANCE DES RÈGLES D'INFÉRENCE] - 2026-07-28

Adoption de `RFC-0028` par `DEC-000038`. Le Reasoning Engine recevait ses règles
dans la requête : GeoSylva devrait donc embarquer la connaissance sylvicole, et
toute révision d'un seuil imposerait une mise à jour de l'application sur chaque
téléphone.

### Décisions

- **Une règle est une Assertion** (`claim_kind` `rule`/`threshold`), sans table
  nouvelle : le métamodèle portait déjà `rule_subtype`, les trois `*_scope_id`
  du domaine de validité, `assertion_qualifier` et `evidence_assessment`.
- **La condition exécutable est dérivée du fait, jamais stockée.** Une chaîne
  persistée peut diverger du seuil qu'elle traduit : on corrigerait le fait sans
  corriger la règle, et le moteur appliquerait l'ancienne valeur en citant la
  source révisée.
- **Un domaine de validité non renseigné vaut « nulle part »**, jamais
  « partout ». Une règle tirée d'un catalogue régional appliquée hors zone
  produirait une conclusion fausse citant une source réelle, avec une chaîne
  d'inférence complète — invisible. Corollaire : territoire obligatoire sur
  `silvicultural_rule` et `autecology_profile`.
- **Aucun plancher de preuve par défaut**, mais `evidence_level_plancher`
  obligatoire dans la réponse : le danger n'est pas la connaissance faible,
  c'est la connaissance faible présentée comme forte.
- **Une source invalidée** sort la règle du service et rend énumérables les
  conclusions passées qui la citaient.

### Périmètre du premier lot

Chêne sessile, réserve utile maximale, un territoire — de bout en bout.

---

## [FIABILITÉ API — AUDIT PAR RÉFUTATION] - 2026-07-28

Audit de fiabilité de l'API GSIE : chaque constat prouvé par exécution réelle
sur PostgreSQL/PostGIS, chaque correctif vérifié de la même façon. Les défauts
ci-dessous traversaient une suite de plus de 1000 tests sans en faire tomber un
seul — la couverture mesurait les lignes exécutées, pas les comportements
vérifiés.

### Défauts P0 corrigés

- **`resources/service.py`** : `revision.author_id` et `resource_diff.id`
  référencent `resource(id)` mais citaient des identifiants sans ligne parente.
  Toute écriture authentifiée échouait en `ForeignKeyViolationError`. L'Agent
  auteur est désormais matérialisé, et le ResourceDiff crée sa ligne racine
  (type 61 du métamodèle, ADR-002).
- **`resources/router.py`** : `GET /resources?type=` (vide) était traité comme
  un filtre et désactivait l'exclusion RGPD — un simple `reader` listait
  `consent`, `data_subject`, `access_policy`, `sensitivity_classification`.
- **`resources/coercion.py`** (nouveau) : aucune coercition JSON → Python.
  Une date ISO partait telle quelle vers un `timestamptz`, rendant 19 des 90
  types incréables (500 opaque). Les conversions impossibles rendent 422.
- **`resources/service.py`** : une géométrie relue (`WKBElement`) n'était pas
  sérialisable — la ressource était écrite puis devenait illisible.

### Défauts P1/P2 corrigés

- **`alembic/versions/20260728_0006`** : `DEFAULT 'now()'` (chaîne) est figé par
  PostgreSQL à la création de la table. `revision.created_at` portait la date de
  migration pour toutes les lignes — l'horodatage d'audit du Temporal Engine
  était faux (CON-010).
- **`websocket/manager.py`** : le subscriber Redis mourait après 5 s de silence
  (`socket_timeout` sur `pubsub.listen()`), tuant le fan-out inter-workers en
  permanence. Passage à `get_message` + reprises bornées.
- **`websocket/router.py`** : nettoyage déplacé dans `finally` — une trame
  binaire faisait fuir le compteur de quota.
- **`core/limiter.py`** : `key_style="endpoint"`. Le quota était compté par URL
  concrète, donc `DELETE 10/minute` ne bornait rien.
- **14 routers moteurs** : bascule sur le limiter partagé (les limiters locaux
  ignoraient `rate_limit_enabled` et n'étaient pas distribués entre workers).
- **`engines/diagnostic/engine.py`** : rejeu idempotent — `date_diagnostic` est
  hors comparaison, un retry après expiration réseau ne rend plus 409.
- **`engines/knowledge/engine.py`** : jointure 1-N sans agrégation — chaque
  révision dupliquait la connaissance et exposait le niveau de preuve périmé.
- **`engines/botanical/engine.py`** : course sur `_get_or_create_taxon`
  rattrapée par SAVEPOINT.
- **`engines/correlation/engine.py`** : une variable constante rendait 500
  (NaN non gardé) au lieu d'une erreur métier.
- **`resources/service.py`** : une référence pendante rend 422 en nommant le
  champ, au lieu d'un 500 opaque.

### Tests — harnais de mutation

- **`tests/mutation/harnais.py`** (nouveau) : casse volontairement chaque garde
  ajoutée et vérifie que la suite proteste. Une mutation qui survit désigne un
  comportement que rien ne surveille. Score actuel : 6/6.
  Le harnais a immédiatement démasqué deux tests qui ne mordaient pas, dont un
  écrit dans cette même session.
- **`tests/integration/test_resources_fiabilite.py`**,
  **`test_moteurs_fiabilite.py`**, **`tests/unit/test_limiter_contrat.py`**,
  **`test_auth_type_jeton.py`** : non-régression sur base réelle.

### Qualité

- `mypy --strict` : vert sur les 137 modules (4 erreurs corrigées dans
  `recommendation/engine.py` — annotation `str` là où le schéma dit `str | None`).
- `ruff check` : 135 erreurs → 6 (les 6 restantes sont dans des fichiers en
  cours de modification par un autre agent, laissés intacts).

---

## [ENRICHISSEMENT V1 — DONNÉES RÉELLES] - 2026-07-27

### Phase 1 — Pipeline cross-moteurs Validation + Learning (commit 4930aa1)

- **`engines/validation_pipeline.py`** : orchestrateur qui câble le
  Validation Engine sur de vrais objets typés (Diagnostic,
  RecommendationSet, Conclusion) au lieu des dicts abstraits v1.
  Trois adaptateurs (diagnostic, recommandation, ensemble complet) +
  branche Learning (ValidationResult bloqué → LearningSignal
  sortie_bloquee). `run_validation_pipeline()` orchestre la chaîne
  complète Validation → Learning.
- **`engines/learning/engine.py`** : gestion du type `sortie_bloquee`
  (non géré en v1) — accumulation par type de cause, proposition de
  calibration au-delà du seuil (5 blocages), une proposition par type
  de cause (pas de re-émission).

### Phase 2 — Autécologie Rameau (2008)

- **`seeds/autecology_rameau_data.py`** : 20 profils autécologiques
  sourcés Rameau (Flore forestière française, IDF) pour 4 essences
  (Fagus sylvatica, Pinus sylvestris, Quercus ilex, Abies alba), 5
  variables par essence. Niveau C (synthèse reconnue). Valeurs
  textuelles uniquement (ADR-009).
- **`engines/autecology_adapter.py`** : adaptateur
  AutecologyProfile → RegleInference pour le Reasoning Engine.
  Mapping grade → confiance explicite et ordonné (A=0.95, B=0.80,
  C=0.60...).
- Corpus combiné : 26 profils (6 Parelle 2007 + 20 Rameau 2008).

### Phase 3 — Simulation calibrée IGN (alternative Python à CAPSIS)

- **`engines/growth_models.py`** : modèles de croissance calibrés sur
  données publiques IGN (Inventaire Forestier National 2023). 6
  essences calibrées avec AMA volume, AMA circonférence, production
  maximale. Projection linéaire plafonnée, facteur de densité.
- **`engines/simulation_backend.py`** : architecture strategy pattern
  avec 3 backends : LinearGrowthBackend (v1, low), CalibratedGrowthBackend
  (v1 calibré IGN, medium), CapsisBackend (futur Java, high —
  NotImplementedError en v1, architecture en place pour v2).

### Tests

- **43 nouveaux tests** : 7 pipeline cross-engine + 3 learning
  sortie_bloquee + 8 rameau + 8 adaptateur + 9 growth_models + 8
  simulation_backend.
- **Total : 1035 tests unitaires passent** (contre 992 avant), 0 échec.

---

## [14/14 MOTEURS GSIE IMPLÉMENTÉS] - 2026-07-27

### Implémentation des 5 moteurs manquants (commit 4c64bcd)

- **Recommendation Engine** (`engines/recommendation/engine.py` +
  `router.py`) : génération de recommandations contournables avec
  alternatives systématiques, mapping objectif forestier → type d'action
  (v1 déclaratif), enregistrement des décisions du forestier
  (accepte/refuse/modifie). Garanties : contournable (GSIE-CON-001),
  justifié (CON-004), alternatives (principe fondateur).
- **Validation Engine** (`engines/validation/`) : contrôle final avant
  présentation à l'utilisateur. 5 contrôles (niveau preuve, source,
  chaîne inference, contournable, explicabilité), 3 statuts (valide,
  bloque, partiellement_valide), 8 causes de blocage tracées
  (CON-001, CON-002, CON-004, CON-005).
- **Learning Engine** (`engines/learning/`) : détection de patterns de
  refus répétés (seuil = 5), traitement des patterns émergents
  (confiance ≥ 0.7). Subordination aux règles expertes : propositions
  jamais validées automatiquement (GSIE-CON-001).
- **Simulation Engine** (`engines/simulation/`) : projection
  déterministe linéaire (v1, `confidence=low`), parsing d'horizon
  (5y/10y/30y), sources et hypothèses explicites (CON-004, CON-005).
  Pistes v2 documentées : CAPSIS, iLand, LANDIS-II, ForeFire, SALib.
- **Evidence Engine** : `wrapper.py` préexistant (Rust+PyO3) reconnu par
  le meta-test de conformité (correction du test).

### Meta-test de conformité des 14 moteurs

- **`tests/unit/test_engines_conformity.py`** : 31 tests vérifient que
  les 14 moteurs documentés sont implémentés, importables, ont un
  endpoint `/status` et un README. `should_have_all_14_engines_implemented`
  PASSE — les 14 moteurs GSIE sont maintenant implémentés (14/14).

### Tests

- **44 nouveaux tests unitaires** : validation (10), learning (9),
  simulation (13), recommendation (12).
- **Total : 992 tests unitaires passent** (contre 917 avant), 0 échec.

---

## [AUDIT + FIABILISATION DB GSIE] - 2026-07-27

### Audit complet base de données (score 43% -> campagne de fiabilisation)

- **Audit DB complet** : schéma, sécurité, PostGIS, sauvegarde, intégrité
  référentielle. Score global ~43%, 5 P0, 10 P1, 15 P2. Rapport dans
  `GSIE/API/docs/AUDIT_BASE_DONNEES_2026-07-27.md`.
- **DEC-000037 (Draft)** : stratégie de fiabilisation et sécurisation DB.
- **Runbook DR** : `23_QUALITY_MANAGEMENT/PROCESSES/DISASTER_RECOVERY_DB.md`.

### Quick wins (vague 1)

- **Script `pg_dump`** : `scripts/backup_pgdump.sh` (backup + rotation 7).
- **Script test restore** : `scripts/test_restore.sh` (vérifie tables,
  PostGIS, AGE).
- **Doc backup/restore** : `docs/BACKUP_RESTORE.md` (pg_dump + pgBackRest +
  PITR + streaming replication).
- **`wal_level=replica`** explicite dans `docker-compose.yml`.
- **Durcissement `db`** : `cap_drop: ALL` + `cap_add` minimal (CHOWN,
  DAC_OVERRIDE, FOWNER, SETGID, SETUID).

### Index FK + CHECK + compare_type (vague 2, migration 20260727_0003)

- **110 index sur FK non indexées** (P0-3) — fin des seq scans sur
  `recommendation`, `correlation`, `assertion`, `flow`.
- **13 CHECK constraints métier** (P1-6) : confidence ∈ [0,1], p_value ∈
  [0,1], dates cohérentes, surfaces/volumes ≥ 0.
- **`compare_type=True` + `compare_server_default=True`** dans
  `alembic/env.py` — détecte la dérive modèles ↔ schéma.
- **`index=True`** ajouté sur les FK dans 11 fichiers de modèles
  SQLAlchemy (cohérence modèles <-> migration).

### Rôles PostgreSQL + RLS + TLS + pgAudit (vague 2, migration 20260727_0004)

- **3 rôles dédiés** (P0-4) : `gsie_migrator` (DDL/Alembic), `gsie_app`
  (DML restreint), `gsie_readonly` (SELECT). Script `docker/init-roles.sql`.
- **RLS sur 6 tables sensibles** (P0-5) : `consent`, `data_subject`,
  `sensitivity_classification`, `access_policy`, `sample`, `observation`.
  Policies basées sur `current_setting('app.current_user_id')` + bypass
  admin/dpo/governance. `FORCE ROW LEVEL SECURITY`.
- **TLS PostgreSQL** : `db_ssl_mode` setting (asyncpg), `require`+
  obligatoire en staging/production (garde-fou dans
  `validate_production_security`).
- **pgAudit** : `postgresql-16-pgaudit` dans `Dockerfile.db`,
  `shared_preload_libraries=age,pg_stat_statements,pgaudit`,
  `pgaudit.log=ddl,write,role` (traçabilité constitutionnelle).

### Pool sizing + PgBouncer + monitoring (vague 2)

- **Pool sizing corrigé** (P0-2) : `db_pool_size=4`, `db_max_overflow=10`,
  `gunicorn_workers=5` (5×14+6=76 ≤ 100). Validation dans
  `validate_production_security`.
- **Gunicorn workers borné** : `GSIE_GUNICORN_WORKERS` env var, fini le
  `cpu_count()*2+1` non borné.
- **`pool_recycle=1800`** dans `database.py` (évite connexions mortes).
- **PgBouncer config** : `docker/pgbouncer.ini` + `pgbouncer-userlist.txt`
  (config orpheline documentée, activation conditionnée au passage en
  staging).
- **Monitoring** : `pg_stat_statements` dans `shared_preload_libraries`,
  `docker/init/01-pg-stat-statements.sql`, `docker/postgres-queries.yaml`
  pour `postgres_exporter`.

### PostGIS validation + geom_4326 (vague 2, migration 20260727_0005)

- **Contrainte `CHECK ST_IsValid`** sur `place.geometry`.
- **Trigger `ST_MakeValid`** (auto-réparation avant persistance) + rejet
  des géométries vides.
- **Colonne `geom_4326`** générée (`ST_Transform(geometry, 4326)` STORED)
  + index GIST pour l'interop GeoJSON/APIs externes. Stockage reste en
  2154 pour les calculs métriques.
- **Validation GeoJSON** dans `engines/gis/engine.py` : `_validate_geometry`
  répare via `buffer(0)` les géométries invalides IGN entrantes.

### pgBackRest + PITR (vague 3)

- **Config pgBackRest** : `docker/pgbackrest.conf` (chiffrement AES-256,
  compression zstd, block incremental, multi-repo local+S3).
- **Doc PITR** : procédure restore par timestamp / restore point nommé.
- **Streaming replication** : doc primary/standby + promotion manuelle
  (principe constitutionnel : failover manuel).

### Validation

- **913 tests unitaires passent**, 60 skipped, 0 échec (97% couverture).
- **5/5 tests de contrat migration** passent (1 tête Alembic
  `20260727_0005`).
- **mypy --strict** : 0 erreur sur config.py, database.py,
  spatial_temporal.py.
- **ruff** : 0 erreur sur tous les fichiers modifiés.
- **4 fixes de Claude approuvés** par audit QA (non-régression
  confirmée, 908 tests OK).

### Chaîne Alembic finale

```
20260726_0001 (baseline, Locked)
  → 20260726_0002 (outbox retry)
  → 20260727_0003 (110 index FK + 13 CHECK)
  → 20260727_0004 (RLS 6 tables sensibles)
  → 20260727_0005 (PostGIS validation + geom_4326) [head]
```

---

## [RELIABILITY API GSIE] - 2026-07-27

### Fiabilité enterprise — API GSIE

- **Coverage 88% -> 99%** (+11 points) sur la base de code `gsie_api`
  (6605 statements, 72 manquants).
- **1053 tests passent** (60 skipped, 3 xfailed, 0 échec) en 506s.
- **+354 tests ajoutés** sur 4 commits :
  - `test_routers_coverage.py` (87 tests) : routers FastAPI (resources,
    climate, botanical, gis, pedology, forest_dynamics, diagnostic,
    knowledge) — couverture routers 54-87% -> 90-100%.
  - `test_infra_coverage.py` (112 tests) : infrastructure (websocket,
    object_storage, auth/refresh, dpclim, seeds, outbox_worker) —
    couverture infra 50-85% -> 93-100%.
  - `test_e2e_cross_engines.py` (26 tests) : chaîne cross-moteurs
    Evidence -> Knowledge (ADR-009, Docker requis) + edge cases API
    (rate limiting, CORS, gzip, Prometheus, health, RBAC, JWT expiré,
    validation stricte, OpenAPI, versions moteurs, trace ID CON-005).
  - 5 fichiers edge cases moteurs (51 tests) : opérateurs AST interdits,
    conditions non parsables, blocs correlation, dépendances transitives,
    contradictions (reasoning) ; revise/evidence/filter (knowledge) ;
    repli doubtful, erreurs loader (botanical) ; pannes réseau AROME
    (climate) ; fallback _classify_strength NaN, erreur défensive
    diagnostic vide (correlation+diagnostic).
- **Fix `test_migration_baseline.py`** : `test_models.py` polluait
  `Base.metadata` avec un `TestModel(Base)` — remplacé par un
  `LocalBase` dédié.
- **Fix pyproject.toml** : enregistrement du mark `xdist_group`
  (suppression warning pytest).

### Moteurs à 100% de coverage

- `engines/botanical/engine.py` : **100%** (était 88%)
- `engines/climate/arome_client.py` : **100%** (était 88%)
- `engines/correlation/engine.py` : **100%** (était 99%)
- `engines/diagnostic/engine.py` : **100%** (était 99%)
- `engines/knowledge/engine.py` : **100%** (était 94%)
- `engines/reasoning/engine.py` : **99%** (était 91%)
- `engines/pipeline.py` : **100%**
- `engines/forest_dynamics/engine.py` : **100%**
- `engines/gis/engine.py` : **100%**
- `engines/pedology/engine.py` : **100%**
- `websocket/manager.py` : **100%**
- `auth/refresh_tokens.py` : **100%**
- `infrastructure/outbox_worker.py` : **99%**
- `resources/router.py` : **99%**
- `resources/service.py` : **99%**

---

## [BASELINE ALEMBIC GSIE V6.2] - 2026-07-26

### Historique propre et immuable

- **DEC-000036 validée** — la lignée locale non publiée `0001` à `0013` est
  remplacée par `20260726_0001`, baseline autonome du schéma GSIE v6.2.
- La baseline contient exactement 116 tables applicatives, sans importer les
  modèles au moment de l'exécution. Les 12 tables legacy v6.1 restent exclues
  grâce à une base déclarative séparée.
- Aucune donnée historique n'étant à préserver, une ancienne base locale
  marquée `0001` à `0013` doit être recréée ; aucune conversion trompeuse
  n'est maintenue.

### Preuves et garde-fous

- Cycle réel vert sur PostgreSQL 16 + PostGIS + Apache AGE : base vierge,
  `upgrade head`, contrôle de dérive Alembic, `downgrade base`, puis second
  `upgrade head`.
- Le test vérifie les tables, les enums, le graphe AGE, les index `source_id`,
  l'absence des tables legacy et la réversibilité globale.
- Validation locale complète : 548 tests unitaires réussis, 63 exclusions
  historiques, 87 % de couverture ; 83 tests d'intégration réussis ; Ruff et
  mypy strict conformes.
- La CI construit désormais l'image de base spécialisée et échoue si le test
  de migration ne peut pas s'exécuter ; il ne peut plus être ignoré faute
  d'image locale.
- Le point d'entrée refuse une lignée Alembic absente ou incompatible avant
  mutation et conserve les migrations automatiques désactivées par défaut.

### Documentation

- `ADR-004` est marqué supersédé sur le plan opérationnel, sans effacer
  l'historique de la stratégie progressive initiale.
- Le contrat de migration future interdit de réécrire la baseline et impose
  une nouvelle révision autonome pour chaque évolution du schéma.

---

## [DEC-000035 — RUST COMME CRITÈRE DE PERTINENCE] - 2026-07-26

### Décision

- **DEC-000035 validée** — le langage d'implémentation d'un moteur n'est plus
  fixé par avance au niveau de la vague. Rust est employé là où il est
  pertinent, sur justification explicite ; Python reste le défaut.
- Les trois moteurs de la vague 3 (Correlation, Reasoning, Diagnostic) restent
  en Python. Aucune réécriture n'est engagée au seul motif du plan initial de
  `DEC-000019`.
- Le critère d'application exige, avant toute réécriture Rust : un besoin
  constaté (pas supposé), une mesure de référence Python, et une frontière
  d'interface stable.
- `DEC-000019` demeure valide pour son découpage en vagues et son calendrier ;
  seule l'attribution *a priori* des langages cesse de s'appliquer.
- L'écart signalé le 2026-07-26 (commit `83e420b`) dans la section
  « Écart connu, non corrigé » de la section REASONING + DIAGNOSTIC est
  désormais tranché par la présente décision.

---

## [VEILLE SOURCE GÉOSPATIALE — GEORCHESTRA] - 2026-07-26

### Source potentielle future, sans adoption

- **geoOrchestra ajouté au catalogue exhaustif des sources GSIE**, dans la
  catégorie backend géospatial/API et en priorité 3 (veille).
- Rôle borné à une source externe fédérée pour le GIS Engine, consommable
  ultérieurement par connecteur OGC API Features, WFS, WMS/WMTS ou catalogue
  de métadonnées.
- Les applications ne devront pas dépendre directement d'une instance
  geoOrchestra et GSIE conservera ses données normalisées dans son propre
  stockage.
- geoOrchestra n'est pas un producteur de datasets : disponibilité,
  provenance, fraîcheur et licence devront être qualifiées séparément pour
  chaque jeu et chaque instance avant ingestion.
- Aucun composant n'est adopté, aucune intégration n'est planifiée et aucune
  décision structurante n'est créée à ce stade.

### Documentation

- Note de veille :
  `GSIE/RESEARCH/VEILLE_GEORCHESTRA_2026-07-26.md`.
- Mémoire et roadmap synchronisées.

---
## [PERSISTANCE DES DIAGNOSTICS] - 2026-07-26

### Un `diagnostic_id` résolvable

- **Nouveau type de resource `diagnostic`** — le registre passe de 89 à 90
  types. Modèle `infrastructure/models/diagnostic.py`, entrée de validateur,
  désormais intégré à la baseline v6.2 `20260726_0001`.
- **Aucun type existant n'a été réutilisé.** `inference` désigne la
  prédiction d'un modèle statistique, `recommendation` une recommandation
  générique portée par un acteur, `diagnostic_protocol` un protocole
  sanitaire (RFC-0016), donc une méthode et non un résultat. Les confondre
  rendrait indistinguables en base une conclusion tracée par règles
  explicites et une prédiction opaque — interdit par `GSIE-CON-004`.
- **`DiagnosticEngine.diagnostiquer` écrit désormais son résultat.** Le
  moteur n'est plus pur : c'est un changement de contrat, documenté dans
  `DIAGNOSTIC_ENGINE.md` et dans la docstring du moteur. Sans écriture, le
  `diagnostic_id` attendu par `RecommendationRequest`
  (`RECOMMENDATION_ENGINE.md` §5) ne résolvait rien et le contrat du
  Recommendation Engine restait inapplicable. Débloque la tranche R2.

### Ce que la persistance rend impossible

- Le contenu stocké est le `Diagnostic` sérialisé intégral et constitue la
  seule source de relecture ; les colonnes scalaires ne sont que des
  projections d'index. Un `diagnostic_id` ne peut donc pas résoudre vers un
  contenu différent de celui rendu à l'appelant.
- Le statut `brouillon` est persisté avec le corps : la garantie
  `GSIE-CON-001` tient dans la base, pas seulement dans la réponse HTTP.
- Le moteur `flush` sans jamais `commit` : un diagnostic ne survit pas à
  l'échec de la réponse qui le porte.
- `diagnostic_id` étant dérivé par `uuid5`, rejouer une requête est
  idempotent ; un même identifiant dérivé pour un contenu différent lève
  `DiagnosticConflitError` au lieu d'écraser un diagnostic déjà émis.

### Énumérations — source unique

- `TypeDiagnostic`, `EtatGlobal` et `StatutValidation` deviennent aussi des
  types PostgreSQL et vivent désormais dans `infrastructure/models/enums.py`
  (réexportées sous leurs noms d'origine). Deux définitions parallèles
  auraient fini par diverger, et un diagnostic relu autrement qu'il n'a été
  écrit est précisément l'erreur que ces schémas existent pour empêcher.

### Portes

- 544 tests unitaires verts (référence : 530), 63 ignorés ; ruff, `ruff
  format --check`, mypy `--strict` et
  `tools/check_governance_consistency.py` verts.
- 8 tests de persistance ajoutés. La réversibilité est désormais couverte au
  niveau de la baseline complète par
  `tests/integration/test_migration_baseline.py`.

### Dérivation de `diagnostic_id` corrigée

- Elle ne couvrait que `requete_id` et les `conclusion_id` : requalifier une
  contrainte en atout produisait un diagnostic différent **sous le même
  identifiant**. Une citation pouvait résoudre vers une analyse que son
  auteur n'avait jamais lue.
- Elle couvre désormais `requete_id`, `station_id`, `type_diagnostic`, les
  `conclusion_id`, les qualifications et l'état global déclaré
  (justification et source comprises).
- **Sérialisation JSON canonique** plutôt que concaténation par séparateur :
  une clé assemblée par séparateur peut être imitée en glissant ce
  séparateur dans une justification. La structure JSON ne se laisse pas
  imiter par son propre contenu.
- 6 tests ajoutés, vérifiés comme régression réelle : avec l'ancienne
  formule, 5 des 6 échouent.
- Reste hors dérivation : les contradictions déclarées. La garde
  `DiagnosticConflitError` continue de couvrir ce cas.

### Défauts de la chaîne de migrations résolus par DEC-000036

Les deux défauts découverts pendant la persistance des diagnostics — DDL sauté
entre révisions et duplication des index `source_id` — ont motivé le
rebaselining documenté en tête de ce changelog. L'ancienne lignée n'est plus
utilisable et aucune base partenaire n'en dépend.

---
## [REASONING + DIAGNOSTIC — EXPOSITION SUR L'API] - 2026-07-26

### Moteurs atteignables depuis l'API

- **Reasoning Engine monté sur `app.py`.** Le moteur (655 lignes), son
  routeur (240 lignes) et ~1 500 lignes de tests verts existaient depuis la
  tranche R4 (`GSIE-PROMPT-0017`), mais `app.py` n'incluait jamais le
  routeur : l'ensemble était inatteignable depuis l'API.
- **Diagnostic Engine — tranche R4 (routeur et intégration)**, reprise en
  interne faute de prompt dédié. Endpoints `/diagnostic/status`,
  `/version` et `/diagnostiquer`, calqués sur le routeur Reasoning validé :
  horloge injectée par la couche API (reproductibilité,
  `CODE_QUALITY_STANDARD` §3.3), `DiagnosticEngineError` converti en 400
  sans divulguer chemin, trace ni structure interne.
- Six routes exposées au total sous `/api/v1`.

### Classe de bug fermée

- `test_tous_les_routeurs_sont_importables` vérifiait qu'un routeur présent
  **se charge**, explicitement pas qu'il soit **monté**. Un routeur pouvait
  donc passer ruff, mypy `--strict` et toute la suite unitaire sans exposer
  aucune route.
- Nouveau test `test_tous_les_routeurs_presents_sont_montes_sur_l_application` :
  chaque routeur présent doit être atteignable sur l'application construite.
  Vérifié comme régression réelle — le montage retiré, le test échoue en
  indiquant le correctif exact. Un moteur sans routeur (tranche R4 non faite)
  reste ignoré : ce n'est pas un défaut.

### Traçabilité scientifique

- L'exemple OpenAPI du Diagnostic prolonge celui du Reasoning (même station,
  même source Rameau et al. 2008) pour illustrer la chaîne Reasoning →
  Diagnostic **sans introduire d'affirmation scientifique nouvelle**
  (`GSIE-CON-002`, `ADR-009`). Sa validité est vérifiée contre
  `DiagnosticRequest` : un exemple faux dans la documentation publique est
  pire qu'un exemple absent.

### Vérifications

- **509 tests unitaires verts**, 63 ignorés, 83 % de couverture.
- ruff, ruff format et mypy `--strict` propres ; vérificateur de gouvernance
  sans incohérence sur les deux commits.

### Écart connu, non corrigé

- Le plan `DEC-000019` prévoit la vague 3 (Correlation, Reasoning,
  Diagnostic) **en Rust** ; les trois moteurs sont implémentés en Python.
  L'écart est signalé plutôt que masqué : le trancher relève d'une décision,
  pas d'une correction de documentation.

---
## [RFC-0023 / RFC-0024 — CORRECTIONS P0 DU CONTRE-AUDIT] - 2026-07-24

- Les corrections des **3 constats P0** du rapport `694d81d` sont appliquées
  aux RFC de cadrage, sans valoir clôture avant nouveau contre-audit.
- **C-01** : `RFC-0025` et `RFC-0026` deviennent les véhicules exclusifs des
  futurs textes constitutionnels complets, de leurs diffs et empreintes.
  Elles sont créées comme enveloppes non adoptables ; aucun texte `Locked`
  n'est modifié.
- **C-02** : Vision et Constitution appartiennent au même bloc fondateur
  d'autorité `100` ; la Constitution prévaut en cas de conflit et la revue
  annuelle de la Vision reste non normative.
- **C-03** : `GSIE-CON-004` est explicitement inclus dans le futur périmètre
  de `RFC-0026`, avec une justification externe reproductible qui préserve
  les cinq questions fondamentales et les métadonnées d'explicabilité.
- Les constats liés **C-04, C-06 et C-07** sont également traités. **7 P1
  restent ouverts** : C-05, C-08, C-09, C-10, C-11, C-12 et C-13.
- Les RFC restent `EN_REVUE`. Cette étape n'autorise ni adoption, ni création
  d'une `VISION.md` canonique, ni licence finale, ni autonomie R3-R5.
- Contrôles réussis : cohérence de gouvernance, registre des sources de
  vérité et vérification du diff. Un nouveau contre-audit indépendant reste
  obligatoire.

## [DEC-000033 — ORIENTATION DE LA REFONDATION CONSTITUTIONNELLE] - 2026-07-24

- Orientation **multi-domaines** confirmée : Quintessences regroupe le
  programme, la marque, la plateforme et les verticales environnementales ;
  GSIE (*General System Intelligence Engine*) est le socle commun ; GeoSylva
  et Ignis restent les verticales prioritaires ; Forge est la fabrique de
  données et le Hub l'interface de simulation et de coordination.
- **Autonomie décisionnelle traitée séparément** et conservée comme
  **programme de recherche encadré**, tant que sa qualité, sa sécurité, sa
  responsabilité et son domaine de validité ne sont pas démontrés. Aucune
  autonomie R3, R4 ou R5 n'est autorisée.
- **Vision et Constitution placées dans le même bloc fondateur**, autorité de
  registre `100`. La Vision exprime la mission et le périmètre durable, la
  Constitution définit les lois et garde-fous.
- **La Constitution prévaut en cas de contradiction**, jusqu'à révision
  formelle et cohérente du bloc fondateur. La revue annuelle de la Vision est
  un contrôle de fraîcheur, sans pouvoir de modification normative. Cette
  règle lève l'ambiguïté entre la hiérarchie documentaire, qui nomme la Vision
  au niveau 0, et `GSIE-CON-000`, qui déclare la Constitution plus haute
  autorité applicable.
- **RFC-0023 et RFC-0024 maintenues `Proposé — EN_REVUE`** après contre-audit
  indépendant (`GSIE-PROMPT-0003`) : 3 constats P0 bloquants, 10 P1, 6 P2 et
  3 observations. Un nouveau contre-audit est obligatoire avant adoption.
- Rapport de contre-audit archivé dans
  `23_QUALITY_MANAGEMENT/AUDITS/2026-07-24_CONTRE_AUDIT_RFC_0023_0024.md`,
  commit `694d81d`.
- Cette décision **n'autorise pas** : l'adoption des RFC-0023/0024, la
  création d'une `VISION.md` canonique, la modification d'un document
  constitutionnel ou `Locked`, une autonomie critique en production, une
  licence finale de composant, ni l'ouverture de Forge aux partenaires.

## [DEC-000034 — RÉASSIGNATION DE L'ORCHESTRATION DES AGENTS IA] - 2026-07-25

- Amende DEC-000032 (orchestration contrôlée des agents IA) — RFC-0022
  Adopté. Décision d'organisation sans effet constitutionnel.
- Codex conserve l'orchestration technique et le contrôle des preuves
  avant acceptation ; le Fondateur conserve l'autorité finale.
- Voir `03_DECISIONS/DEC-000034.md`.

## [GSIE — CONTRE-AUDIT DE FIABILITÉ ET BUILD LINUX] - 2026-07-22

- RBAC explicite sur toutes les opérations des moteurs ; les routes de statut
  et de version restent publiques, les lectures exigent un rôle lecteur et les
  mutations un rôle writer.
- WebSocket fermé aux jetons sans rôle et filtrage des événements RGPD, y
  compris sur le canal global ; payloads outbox réduits aux identifiants,
  versions et noms de champs modifiés.
- Rotation des refresh tokens entièrement atomique (mémoire et Redis/Lua),
  fermeture propre du store et réponses 413 tracées avec en-têtes de sécurité.
- Build Linux réparé : eccodeslib 2.47.3.23 est désormais verrouillé hors
  Windows avec empreintes ; Maturin est aligné à 1.9.6 dans Docker et le
  manifeste Rust. Image non-root vérifiée avec imports API/Rust/ecCodes.
- CI renforcée : lint Markdown réellement bloquant avec baseline de migration,
  profil strict pour tout nouveau document, contrôle automatique des versions
  de build et refus effectif des modifications Locked sans RFC.
- Preuves : **441 tests Python réussis, 63 ignorés, couverture globale 88 %** ;
  barrière unitaire **368/63 et 81,87 %** ; intégration **73/73** ; Rust
  **41/41** ; Ruff, formatage, mypy strict, Compose et image Docker verts.
- Dette visible : 63 exclusions historiques (données v6.1 et cas Rust Windows)
  et règles Markdown de l'ancien corpus placées sous baseline avant
  réactivation progressive.

## [FORGE — UNICITÉ LANCEDB INTER-PROCESSUS] - 2026-07-22

- Le test précédent avec deux stores était séquentiel et ne démontrait pas
  l'absence de course entre l'API et les workers RQ.
- Un test de non-régression lance désormais quatre vrais processus synchronisés
  sur le même fait et le même volume LanceDB.
- Toutes les mutations du corpus sont sérialisées par un verrou de fichier
  interprocessus ; `merge_insert` est exécuté sur l'état le plus récent et son
  `num_inserted_rows` fournit le compteur fiable.
- Preuves : **328 tests réussis**, couverture globale **81 %**, Ruff propre et
  mypy strict propre sur **140 fichiers**.
- Portée : garantie locale sur volume partagé ; le multi-hôtes reste soumis à
  une barrière d'architecture explicite.

## [DEC-000032 — ORCHESTRATION CONTRÔLÉE DES AGENTS IA] - 2026-07-22

- RFC-0022 et DEC-000032 adoptées : le Fondateur conserve l'autorité finale
  et Codex devient l'orchestrateur technique et le contrôleur des preuves.
- Nouveau processus QMS `AI_AGENT_ORCHESTRATION.md` : cycle des tâches,
  RACI, séparation auteur/relecteur, conditions d'arrêt et rapport obligatoire.
- Nouveau registre `GSIE/PROMPTS/`, modèle de tâche et deux premières
  missions préparées pour Claude et GLM 5.2 via Devin.
- Les missions restent `BLOQUÉE` tant que les trois snapshots contenant les
  changements locaux ne sont pas accessibles par des SHA identifiables.
- `CLAUDE.md` corrigé : Phase 4 active, état des moteurs renvoyé vers la
  mémoire canonique et remote Forge actualisé.
- Les instructions opérationnelles des agents sont désormais enregistrées
  dans le registre des sources de vérité et revues trimestriellement.
- Le garde-fou `tools/check_ai_prompts.py`, ses tests et la CI bloquent les
  prompts non enregistrés, incomplets, dupliqués ou dans un état inconnu.
- Manuel qualité porté en version 1.2.0.


## [DEC-000031 — SOCLE DE FIABILITÉ D'ENTREPRISE] - 2026-07-21

### Sécurité, intégrité et exploitation

- **API GSIE** : refresh tokens à usage unique avec rotation atomique Redis/Lua,
  RBAC fermé avant chargement et étendu aux opérations des moteurs,
  authentification WebSocket avec filtrage RGPD du canal global, événements
  outbox sans valeurs métier, filtrage SQL avant pagination, limite ASGI du
  corps avec réponses 413 tracées, stockage local protégé contre la traversée,
  absence de repli local en production et worker outbox au moins une fois.
- Les migrations au démarrage sont désactivées par défaut. Une migration
  destructive exige trois confirmations distinctes, dont la preuve de
  sauvegarde.
- **GeoSylva** : les workers réutilisent la base SQLCipher de l'application ;
  sauvegarde atomique avec portée honnête, synchronisation tarifaire HTTPS
  bornée et validée, résolution DNS publique uniquement, configuration réseau
  claire en production et exceptions locales limitées au build debug.
- Le barème IBP est aligné sur **IBP FR v3.2 du 2 février 2026**, publié par
  le CNPF :
  <https://www.cnpf.fr/sites/socle/files/2026-02/IBP%20FR%20v3.2%20260202.pdf>.
- **Forge** : authentification et rôles cumulatifs, chemins locaux interdits
  via l'API, SSRF contrôlé sur chaque redirection, téléchargements PDF/HTML
  bornés et atomiques, identifiants de faits complets, ingestion idempotente,
  readiness Redis, exécution conteneur non-root et exposition locale.
- **Qualité** : RFC-0021 et DEC-000031, CODEOWNERS, modèle de PR, registre des
  sources de vérité, dates de revue et contrôle CI bloquant. La CI Forge
  impose lockfile, compilation, typage strict et couverture globale de 80 %.

### Vérifications

- API GSIE : **441 tests réussis, 63 ignorés**, couverture globale **88 %**, Ruff et mypy strict verts.
- Forge : **326 tests réussis**, couverture globale **81 %**, Ruff et mypy
  strict verts.
- GeoSylva : **494 tests réussis** sur 30 suites, dont les tests IBP, SSRF et
  validation tarifaire ; Android Lint : **0 erreur** (564 avertissements
  préexistants inventoriés).
- Risques résiduels explicités dans RFC-0021 : migration des anciennes bases
  mobiles en clair, sauvegarde mobile complète, egress réseau, unicité
  LanceDB inter-processus, dette d'avertissements Kotlin et arbitrage de la
  licence GSIE.


## [AUDIT COMPLET DU CODE — 0 P0, 1 BUG CORRIGÉ, MYPY/RUFF CLEAN] - 2026-07-20

### Audit de l'entièreté du code tracké (195 fichiers Python, hors GeoSylva/QGISIA — dépôts externes)

- Périmètre : `GSIE/API` (160 fichiers), `apps/Ignis` (18),
  `21_EXPERIMENTS` (11), `.devin/scripts` (4), `tools` (2). Vérifié via
  `git ls-files` pour exclure les venvs non trackés (`Forge/.venv`,
  repo externe indépendant).
- Bug réel corrigé (`fix(knowledge)`, commit `ce877be`) :
  `KnowledgeEngine._to_knowledge_object` levait une `ValueError`
  Pydantic opaque si `metadata_json` était corrompu/incomplet (clé
  `type`/`domaine_scientifique` absente) — lève désormais une
  `KnowledgeEngineError` explicite. 4 nouveaux tests.
- mypy --strict (`fix(climate,knowledge)`, commit `6575557`) : 13 → 0
  erreur sur les 104 fichiers de `src/gsie_api` (types génériques
  `dict`/`list` sans paramètres, retours `Any` non castés sur les
  clients HTTP climat, réexport implicite `ConflitBibliographique`,
  override mypy pour `scipy.*` ajouté à `pyproject.toml`).
- ruff (même commit + `chore(ignis)` commit `8725184`) : 0 erreur sur
  l'ensemble du périmètre tracké (imports inutilisés, f-strings sans
  placeholder, variable ambiguë `l`, `try/except/pass` →
  `contextlib.suppress`, lignes trop longues).
- Vérifications complémentaires sans finding : aucun secret/clé en
  dur, aucun `eval`/`exec`, aucun SQL formaté par chaîne, aucune
  exception `except: pass`, chaîne de migrations Alembic cohérente
  (une seule tête), les 60 tests « skipped » sont tous des tests
  d'intégration `requires_docker` documentés (rien de caché).
- 351 tests unitaires passent (0 échec, 60 skipped) après chaque
  commit de cette passe.
- GeoSylva et QGISIA (dépôts Git externes indépendants) non audités
  ici — à faire séparément si demandé.

## [AUDIT QUALITÉ RFC-0016 — CORRECTIONS P1/P2] - 2026-07-20

### Audit qualité (3 subagents backend) sur les tranches 1-5 déjà committées

- Résultat : 0 P0 sur l'ensemble du code audité (committé et non
  committé), ADR-009 respecté partout (aucune valeur scientifique non
  sourcée détectée). 9 P1 + 7 P2 identifiés sur RFC-0016 Phase A, 1 P1
  + 7 P2 sur Phase B/C, 0 P1 + 5 P2 sur l'extension Forest Dynamics.
- Corrections P1 appliquées (`fix(forestry)`) : typage enum strict sur
  6 DTO Pydantic (`AutecologyProfileCreate.evidence_level`,
  `SilviculturalSystemCreate.category`,
  `SilviculturalRuleCreate.evidence_level`,
  `ProvenanceMaterialCreate.base_material_category`,
  `HealthRiskCreate.severity`, `EvidenceStatementRecord.status`) ;
  4 règles métier conditionnelles répliquées dans
  `resources/validators.py` (reflètent des `CheckConstraint` SQL déjà
  en place — `autecology_profile`, `station_observation`,
  `silvicultural_rule`, `health_risk`). 10 nouveaux tests.
- Correction P2 appliquée (`perf(forestry)`) : index manquants sur les
  10 FK `source_id` des tables forestières RFC-0016 (aucune n'était
  indexée alors que toutes les autres FK le sont) — migration
  `0012_forestry_source_id_indexes.py`.
- 347 tests unitaires passent (0 échec, 60 skipped). mypy --strict : 0
  issue. ruff : clean sur tous les fichiers touchés.
- Restent non traités (hors scope de cette passe) : 7+7+5 P2 restants
  de l'audit (dette de cohérence mineure, aucun n'est bloquant).

## [DEC-000030 — RFC-0018 ADOPTÉ, TRANCHE 1/N COMPLÈTE] - 2026-07-20

### RFC-0018 adopté (volet en ligne), schéma de données implémenté

- `DEC-000030` valide RFC-0018 et autorise uniquement le volet en
  ligne (§5) par tranches verticales, sur le modèle éprouvé de
  RFC-0016. Le volet modèle embarqué (§6) reste hors périmètre.
- Tranche 1/N (schéma de données) — 3 nouvelles tables :
  `botanical_identification_request`, `botanical_identification_result`,
  `botanical_identification_decision`
  (`GSIE/API/src/gsie_api/infrastructure/models/identification.py`,
  nouveau module). Contrainte SQL empêchant une décision
  `validee_utilisateur`/`rejetee` sans validateur ni date de décision.
- 2 nouveaux enums (`PlantOrgan`, `IdentificationDecisionStatus`,
  `infrastructure/models/enums.py`). Extension de
  `resources/validators.py` (champs obligatoires + enum par type,
  cohérent avec le principe déjà appliqué en RFC-0016 : la validation
  s'applique même via l'API générique de resources, pas seulement les
  schémas Pydantic des engines).
- Registre de types resources 86 → 89. Suite de tests étendue
  (`tests/unit/test_resources.py`) : 339 tests unitaires passent (0
  échec, 60 skipped). `check_governance_consistency.py` OK.
- Note technique : les contraintes SQL `jsonb_array_length` (nombre de
  photos, nombre de candidats) ont été écartées au profit d'une
  validation applicative — cette fonction est spécifique PostgreSQL et
  absente de SQLite, utilisé par la suite de tests unitaires.
- `PROJECT_MEMORY.md` synchronisé.

## [RFC-0018 EN REVIEW — SPÉCIFICATION GEO-004] - 2026-07-20

### RFC-0018 priorisé, spécification fonctionnelle rédigée

- `05_SPECIFICATIONS/GEOSYLVA/GEO_004_IDENTIFICATION_BOTANIQUE_PLANTNET.md`
  (nouveau) — 16 exigences fonctionnelles (GEO-ID-01 à GEO-ID-16),
  6 exigences non fonctionnelles, 1 cas d'usage terrain (avec/sans
  réseau), complète GEO-F-04 (GEO-001) sans le remplacer.
- `RFC-0018` passe de `Draft` à `Review` — reste avant adoption : revue
  fondateur puis décision (`03_DECISIONS/`). Aucune implémentation
  autorisée.
- `PROJECT_MEMORY.md` synchronisé.

## [DEC-000029 — SCISSION RFC-0017 EN RFC-0018 / RFC-0019] - 2026-07-20

### Veille technologique et scission en RFC d'exécution

- `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md` —
  veille externe (Pl@ntNet, NVIDIA NIM/Blueprints/Skills/Brev) versée
  pour traçabilité.
- `RFC-0017` ouvert puis adopté comme cadrage (DEC-000029), aussitôt
  scindé en deux RFC d'exécution indépendants, tous deux en `Draft` —
  aucun code métier autorisé avant leur propre décision :
  - `RFC-0018` — identification botanique assistée Pl@ntNet (cycle
    `SUGGESTION_IA` → `VALIDEE_UTILISATEUR`, extension satellite
    d'`AutecologyProfile`, volet modèle embarqué offline à l'étude).
  - `RFC-0019` — `gsie-ai-gateway`, couche IA serveur transverse
    (périmètre P0 : RAG scientifique, garde-fou, `GSIE-Eval-FR`).
- `PROJECT_MEMORY.md` synchronisé (RFC ouverts, décisions actives).

## [PHASE 4 — RFC-0016 SCHÉMA FORESTIER SPÉCIALISÉ — PHASE B COMPLÈTE] - 2026-07-19

### RFC-0016 Phase B (intégration Botanical/Forest Dynamics Engine) — 3/3 points implémentés

- 3 commits successifs sur la branche `handoff/audit-2026-07-19`,
  faisant suite à la Phase A :
  1. `f0abd6c` — fermeture d'un trou de la Phase A : les 10 types de
     resource forestiers n'avaient aucune entrée dans le validateur
     générique `resources/validators.py` — un appel direct à l'API
     générique `POST /resources` pouvait contourner la règle déjà
     imposée par les schémas Pydantic (champs obligatoires + enums
     ajoutés pour les 10 types). Dans le même commit, démarrage du
     point 6 (passeport de décision) : `DecisionPassportCategory`/
     `DecisionPassportItem`/`DecisionPassport`
     (`shared/schemas.py`, cross-engine, pas spécifique à un moteur),
     5 catégories (observe, calcule, modelise,
     documente_recommande, incertain), chacune avec justification
     obligatoire imposée par `model_post_init`.
  2. `3afd358` — point 5 : extension du Forest Dynamics Engine.
     `DendrometricRequest`/`Result` portent désormais
     `station_observation_id` optionnel (passthrough, pas de
     résolution DB — le moteur reste une fonction pure v1). Ajout de
     `ForestDynamicsEngine.to_decision_passport_items()` construisant
     des `DecisionPassportItem` (catégorie `calcule`) à partir d'un
     résultat dendrométrique — connecte ce moteur au passeport de
     décision.
  3. `948802b` — point 4 : nouveau module
     `gsie_api.engines.botanical.extraction_bridge`
     (`QuarantinedFact`,
     `build_autecology_profile_from_quarantined_fact()`). Fait le pont
     entre le pipeline d'extraction documentaire (RFC-0014 §3.2,
     `KnowledgeExtractor` dans `Forge/`) et la table
     `autecology_profile` (RFC-0016 tranche 1/10). Ne dérive jamais
     `variable`/valeur par heuristique — le curateur humain fournit
     toujours ces champs explicitement ; seul le champ `method`
     (citation + page + référence) est construit automatiquement à
     partir d'un fait déjà vérifié. Refuse tout fait dont
     `statut != "quarantine"`. Testé directement sur les 29 faits réels
     du 3e pilote RFC-0014 §3.6
     (`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`,
     Quercus robur/petraea, waterlogging).
- Bilan : les 3 points de la Phase B (points 4, 5, 6 du RFC-0016 §5)
  sont désormais couverts. 387 tests unitaires (327 passed, 60
  skipped), `tools/check_governance_consistency.py` OK après chaque
  commit.
- Fichiers principaux : `GSIE/API/src/gsie_api/resources/validators.py`,
  `shared/schemas.py`, `engines/forest_dynamics/schemas.py`,
  `engines/forest_dynamics/engine.py`,
  `engines/botanical/extraction_bridge.py` (nouveau),
  `tests/unit/test_decision_passport.py` (nouveau),
  `tests/unit/test_forest_dynamics.py`,
  `tests/unit/test_extraction_bridge.py` (nouveau),
  `tests/unit/test_resources.py`.
- **Reste à faire** : Phase C (pilote Nouvelle-Aquitaine — constitution
  du corpus 12-20 essences, 50 cas « or » validés par un forestier
  référent, premier pack offline signé) — non commencée. Voir
  `02_RFC/RFC-0016-schema-forestier-specialise.md` et
  `03_DECISIONS/DEC-000027.md`.

---

## [PHASE 4 — RFC-0016 SCHÉMA FORESTIER SPÉCIALISÉ — PHASE A COMPLÈTE] - 2026-07-19

### RFC-0016 Phase A (schéma de données) — 10/10 entités implémentées

- 6 tranches successives sur la branche `handoff/audit-2026-07-19` :
  1. `9a87d98` — `AutecologyProfile`, `SiteIndexModel`, `FertilityClass`.
  2. `1807670` — `StationType`, `StationObservation`.
  3. `0995cb5` — `SilviculturalSystem`, `SilviculturalRule`
     (`Intervention` réutilisée, déjà existante).
  4. `0ca7d1a` — `ProvenanceMaterial`.
  5. `635b8af` — `DiagnosticProtocol`, `HealthRisk`.
  6. `f1cb482` — `EvidenceStatement`/`ConflictRecord` : aucune nouvelle
     table, réutilisation documentée de `AssertionModel`/
     `EvidenceAssessmentModel`/`ConflictClusterModel` déjà existants,
     + nouveau schéma Pydantic `EvidenceStatementCreate`/`Record`
     (`evidence/schemas.py`) imposant `page_or_table` obligatoire.
- Bilan : les 10 entités du §3.1 du RFC-0016 sont désormais toutes
  couvertes — 10 nouvelles tables satellite (`autecology_profile`,
  `site_index_model`, `fertility_class`, `station_type`,
  `station_observation`, `silvicultural_system`, `silvicultural_rule`,
  `provenance_material`, `diagnostic_protocol`, `health_risk`) + 3
  entités réutilisées sans duplication (`Intervention`,
  `EvidenceStatement`, `ConflictRecord`).
- Registre de types resources : 76 → 86 types.
- Nouveaux enums : `SilviculturalSystemCategory`,
  `MaterielBaseCategory`, `HealthRiskSeverity`
  (`infrastructure/models/enums.py`).
- 5 migrations Alembic (`0006` à `0010`).
- 364 tests unitaires (304 passed, 60 skipped),
  `tools/check_governance_consistency.py` OK après chaque commit.
- Fichiers principaux : `GSIE/API/src/gsie_api/infrastructure/models/
  forestry.py` (nouveau), `engines/forest_dynamics/schemas.py`,
  `engines/botanical/schemas.py`, `engines/evidence/schemas.py`,
  `tests/unit/test_forestry_schemas.py` (nouveau), `tests/unit/
  test_resources.py`.
- **Reste à faire** : Phase B (intégration Botanical/Forest Dynamics
  Engine, passeport de décision à 5 catégories) et Phase C (pilote
  Nouvelle-Aquitaine) — non commencées. Voir `02_RFC/
  RFC-0016-schema-forestier-specialise.md` et `03_DECISIONS/
  DEC-000027.md`.

---

## [PHASE 4 — RFC-0015 ENVIRONMENTAL MODEL FABRIC + CLIMATE ENGINE ÉTENDU] - 2026-07-18

### DEC-000028 — Incrément démontrable « territoire + capsule + Golden Bench »

- Première tranche verticale hors-ligne de GSIE sous forme de capsule
  territoriale signée (ADR-008, EXP-0001). Renuméroté depuis DEC-000025
  (collision d'ID avec une décision Validated préexistante). Statut
  Review — validation du Fondateur requise.
- Voir `03_DECISIONS/DEC-000028.md`.

### RFC-0015 adoptée (DEC-000026)

- Étend ADR-009/RFC-0014 (garde-fou anti-invention des données) aux
  modèles scientifiques : registre de modèles (`ModelRegistry`/
  `ModelArtifact`/`LicenseRecord`/`ApplicabilityDomain`/
  `ValidationRun`), LLM strictement orchestrateur non autoritaire,
  vocabulaire imposé (observation/estimation/simulation/
  recommandation ; association/hypothèse causale/effet estimé),
  Correlation Engine v2 (pipeline causal 8 étapes, candidats DoWhy/
  Tigramite/PyMC/MAPIE), packs offline signés GeoSylva, progression
  par vertical slices mesurables.
- Issue de l'étude externe versée
  `GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md`.
- Voir `02_RFC/RFC-0015-environmental-model-fabric.md`,
  `03_DECISIONS/DEC-000026.md`.

### Climate Engine — 4 nouvelles sources réelles Météo-France (portail API)

- Météo des forêts (danger feux J+1/J+2), DPClim (climatologie
  quotidienne, flux 3 étapes commande/polling/fichier), Vigilance
  (carte de vigilance J/J+1), Package Observations (24h glissantes) —
  en plus du flux SYNOP déjà en place. 21 tests, formes de réponse
  réelles capturées.

### Forge — audit et corrections réelles

- Identité git configurée (blocage de commit résolu).
- Recherche documentaire (`documents search`) : agrégation réelle
  HAL + OpenAlex + arXiv au lieu d'arXiv seul (bug de pertinence
  corrigé — requêtes françaises renvoyaient des résultats hors sujet).
  Correction du paramètre OpenAlex (`query` retiré par l'API,
  remplacé par `search`).
- Scraping (`scrape`) : branchement des 5 connecteurs jusqu'ici
  inutilisés (Flickr, Wikimedia, Zenodo, Roboflow, images web), en
  plus de Hugging Face.
- 105 tests passent, mypy --strict propre.

---

## [PHASE 4 — BOTANICAL ENGINE + PEDOLOGY ENGINE] - 2026-07-17

### Nouveaux moteurs — Botanical (GBIF) et Pedology (SoilGrids)

- **Botanical Engine** : résolution taxonomique via GBIF Backbone
  Taxonomy (`species/match`, aucune clé API), résolution de synonymes
  vers le taxon accepté (vérifié : *Quercus sessiliflora* → *Quercus
  petraea*), déduplication par clé GBIF (`entity` + `entity_alias`,
  CON-010). Pas d'autécologie en v1 — nécessite des connaissances
  sourcées (Rameau et al.) pas encore ingérées (RFC-0014). 8 tests.
- **Pedology Engine** : pH (H2O) + texture (argile/sable/limon) via
  SoilGrids (ISRIC, aucune clé), valeurs mises à l'échelle par
  `d_factor` (vérifié empiriquement : argile+sable+limon ≈ 100%).
  `evidence_level=B` — source unique peer-reviewed (Poggio et al.,
  2021), jamais A sans convergence multi-sources
  (EVIDENCE_FRAMEWORK.md). Pas de persistance en v1 (estimation
  ponctuelle sans identité stable). 6 tests.
- **Fix checker de gouvernance** : la règle 3 (ADR-009) signalait à
  tort une `SourceReference(...)` contenant "v2.0" dans une URL comme
  valeur non sourcée — une SourceReference EST déjà la citation
  structurée, désormais exclue explicitement.

### Métriques

- 6/14 moteurs GSIE codés (Evidence, Knowledge, Correlation, GIS,
  Botanical, Pedology). 255 tests passent, 0 échec, 60 skipped, 86%
  couverture. ruff + mypy --strict verts.

---

## [PHASE 4 — GARDE-FOU ANTI-INVENTION + GIS ENGINE] - 2026-07-17

### Gouvernance — RFC-0014, ADR-009

- **RFC-0014** (Adopté) : garde-fou anti-invention de données + pipeline
  d'ingestion de littérature scientifique non structurée, en réponse à
  une exigence explicite du Fondateur (aucune fausse donnée, corrélations
  basées uniquement sur des sources scientifiques réelles).
- **ADR-009** (Accepté) : formalise le garde-fou en décision opposable —
  tout moteur de raisonnement doit justifier source, evidence_level et
  chaîne de provenance pour chaque valeur produite.
- **Checker de gouvernance** : règle 3 ajoutée — détection best-effort de
  constantes numériques (seuils, coefficients) sans citation détectable
  dans les moteurs (`engines/*/engine.py`). 7 tests.
- Lien vers `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md` (catalogue de
  ~179 sources avec méthodes d'accès concrètes) depuis RFC-0013/RFC-0014.

### Pipeline d'extraction sourcée (Forge)

- `Forge/src/dataset_forge/documents/extraction.py` — `KnowledgeExtractor` :
  extraction de faits scientifiques via NVIDIA NIM sous contrainte de
  citation exacte, vérifiée automatiquement contre le texte source,
  statut `quarantine`/`rejete` uniquement (jamais `accepte` automatique).
- Pilote réussi sur un document réel (*Lettre du DSF n°61*, sept. 2024,
  agriculture.gouv.fr) : 8 faits extraits, tous vérifiés.
- Corrections apportées en cours de route : fix venv Forge (chemin
  obsolète après renommage), fix TLS (`truststore`, interception réseau
  locale), modèle `deepseek-v4-flash` préféré à un modèle de raisonnement
  qui épuisait son budget de tokens, parsing JSON tolérant.

### Nouveau moteur — GIS Engine (sort du placeholder)

- Cadastre (API Carto IGN) et altitude (API de calcul altimétrique IGN) —
  données réelles vérifiables sans clé API, géométrie persistée en
  Lambert-93 (`place`, PostGIS). 7 tests (respx, réponses réelles).

### Métriques

- 241 tests API GSIE passent, 0 échec, 60 skipped, 85% couverture
- ruff + mypy --strict verts

---

## [PHASE 4 — CORRELATION ENGINE (v1 réduite)] - 2026-07-17

### Nouveau moteur — Correlation Engine

- `GSIE/API/src/gsie_api/engines/correlation/` (schemas.py, engine.py,
  router.py) — 3e moteur codé après Evidence et Knowledge.
- Calcule pearson/spearman/kendall (scipy) + p-valeur, classe la force
  selon l'échelle Evans (1996), persiste comme `resource(type=correlation)`
  + `CorrelationModel` (schéma v6.2 déjà en place, jusque-là orphelin).
- **Périmètre v1 assumé et documenté** (voir docstring `schemas.py`) :
  contrairement à CORRELATION_ENGINE.md §5, les valeurs sont fournies
  directement dans la requête (les moteurs domaine GIS/Climate/Pedology/
  Botanical/Forest Dynamics n'existent pas encore — seul GIS a un
  placeholder), et une seule paire de variables par requête (pas de
  matrice N×N). Le contrat de sortie respecte la forme cible pour une
  extension future sans rupture.
- 4 endpoints : `/correlation/{status,version,compute,stats}`, branchés
  dans `app.py`.
- 10 tests d'intégration (`tests/integration/test_correlation.py`),
  tous verts, contre Postgres réel.
- Dépendance ajoutée : `scipy==1.15.3`.

---

## [PHASE 4 — GOUVERNANCE : ADOPTION RFC-0011 / ADR-001-006 + FIX MIGRATION] - 2026-07-17

### Gouvernance

- **RFC-0011** : Proposé → Adopté (validation Fondateur)
- **ADR-001, ADR-002, ADR-003, ADR-005, ADR-006** : Proposé → Accepté
  (ADR-004 déjà Validated). Les 6 ADR adoptés par DEC-000022 (déjà
  Validated depuis le 2026-07-16) affichaient encore leur statut
  d'origine — décalage détecté par `tools/check_governance_consistency.py`
  (5 findings « implémentation prématurée »), résolu par mise à jour des
  statuts propres des ADR/RFC pour refléter la décision déjà prise.
- Checker de gouvernance : 0 incohérence (5 → 0)

### Migration 0002 — bug de tables manquantes corrigé

- `alembic/versions/0002_metamodel_v6.2_resource_73types.py` n'important
  pas le module `business.py`, les 7 tables métier ONF/CNPF
  (`management_plan`, `intervention`, `economic_scenario`, `regulation`,
  `compliance_check`, `outcome_tracking`, `administrative_unit`)
  n'étaient jamais créées par `alembic upgrade head` sur une vraie base,
  bien qu'exposées via le CRUD générique (`RESOURCE_TYPES`). Corrigé en
  ajoutant l'import `business` dans `upgrade()` et `downgrade()`.
  Vérifié empiriquement (upgrade réel contre Postgres/AGE/PostGIS,
  les 7 tables sont créées).

### Tests E2E API — mismatch de boucle asyncio résolu

- `tests/integration/test_pipeline_api.py` : remplacement de
  `TestClient` (synchrone) par `httpx.AsyncClient(transport=ASGITransport(...))`
  — supprime le mismatch de boucle événementielle qui bloquait les 2
  tests d'écriture réelle en base. Les 3 tests E2E (pipeline complet,
  pipeline avec révision, rejet connaissance refusée) passent désormais
  réellement, plus aucun skip sur ce fichier.

### Métriques

- 224 tests passent, 0 échec, 60 skipped, 85% couverture
- ruff clean

---

## [PHASE 4 — CI 100% VERTE] - 2026-07-16

### CI GitHub Actions — tous jobs passent

- **Governance Guard** — DEC-000019/020/021/023 : ajout champ Décideur manquant
- **Python lint + type + test** — ruff 0.8.4 (pin CI), mypy override gsie_evidence,
  aiosqlite dev dep, skip tests Rust fallback sans wheel, server_default JSONB
  portable (retiré du modèle, gardé dans Alembic)
- **Python integration tests** — drop postgis_tiger_geocoder extension (conflit
  table place avec PlaceModel)
- **Docker build** — rustc 1.80→1.85 (edition2024 dépendances transitives),
  maturin 1.9.6 pin (compatible rustc 1.85)
- **CI Gate** — bloque merge si un job échoue

### Métriques

- 194 tests unitaires passent, 79 skipped, 84% couverture
- 9 tests integration PostGIS/Redis passent (testcontainers)
- ruff + mypy --strict verts
- Docker build reproductible (rustc 1.85 + maturin 1.9.6)

---

## [PHASE 4 — VAGUE 1 : STABILISATION DOCKER + AUTH + TESTS POSTGIS] - 2026-07-16

### Gate 2 — Docker reproductible

- **Fix docker-compose.yml** — context=project root (le Dockerfile COPY depuis
  `GSIE/API/` et `GSIE/ENGINES/EVIDENCE_ENGINE/rust/`, le context doit être la
  racine du projet, pas `GSIE/API/`)
- **.dockerignore racine** — exclut `apps/`, `Forge/`, `.git/`, dossiers
  gouvernance, caches Python/Rust, secrets
- **entrypoint.sh** — lance `alembic upgrade head` avant Gunicorn (fail fast si
  migration échoue)
- **Dockerfile** — copie `alembic/`, `alembic.ini`, `docker/` dans l'image
- **docker-compose.yml** — monte `keys/` en lecture seule pour JWT RS256
- **generate-jwt-keys.sh** — script génération paire RSA 2048 bits (openssl)

### Gate 3 — Auth production

- **Audit trail** — IP + User-Agent tracés sur `login_success` et `login_failed`
  (CON-005, OWASP A09)
- **Refresh token** — `jti` tracé pour corrélation
- **.env.example** — documentation procédure production (4 étapes)
- **README** — démarrage rapide mis à jour (clés JWT, migrations auto, curl login)

### Gate 4 — Tests PostGIS/Redis réels

- **9 tests d'intégration testcontainers** (PostgreSQL/PostGIS + Redis) :
  - Connexion PostgreSQL + PostGIS (extension vérifiée)
  - CRUD resource : insert, read, soft delete (CON-010)
  - JSONB : requête `metadata_json->>'essence' = 'chene_sessile'`
  - PostGIS : Place avec Geometry SRID 2154 (Lambert-93)
  - PostGIS : `ST_DWithin` — places proches de Landiras (zone test Ignis)
  - Redis : set/get + Pub/Sub (WebSocket fan-out)
- **CI** — `python-integration` ajouté au CI gate (bloque merge si échec)

### Qualité

- **app.py** — migration `on_event` (déprécié) → `lifespan` (FastAPI 0.115+)
- **194 tests passent**, 84% couverture, 0 warning deprecation
- **ruff check** : 0 erreur | **mypy --strict** : 0 erreur

---

## [PHASE 4 — VAGUE 1 : QUALITÉ + GOUVERNANCE + INGESTION] - 2026-07-16

### Qualité API

- **22 tests service.py** — mass-assignment, append-only, soft-delete (98% coverage)
- **CI gate** — ruff + mypy --strict + pytest (83% couverture, 194 tests, 0 échec)
- **Fix bugs** — revision_id → to_revision_id (ResourceDiffModel), create() retournait request.data non filtré
- **Typage** — 14 erreurs mypy corrigées, 54 erreurs ruff corrigées

### Gouvernance

- **RFC-0013** — ingestion données forestières ONF/CNPF/IGN (Draft)
- **DEC-000024** — décision ingestion données forestières (Proposé)

### Métamodèle v6.2

- **7 types métier ONF/CNPF** — management_plan, intervention, economic_scenario, regulation, compliance_check, outcome_tracking, administrative_unit (69 → 76 types)
- **RBAC complet** — reader/writer/admin/rgpd_manager par type, 19 tests
- **Migration progressive** — 0002-0005 selon ADR-004 (4 étapes au lieu d'un big bang)

---

## [GOUVERNANCE — VALIDATIONS RÉTROACTIVES] - 2026-07-16

### Gouvernance

- **DEC-000022** (métamodèle v6.2) : Proposé → Validated (validation rétroactive)
- **DEC-000023** (migration API v6.2) : Proposé → Validated (validation rétroactive)
- **ADR-004** (migration progressive) : Proposé → Validated (plan en 4 migrations confirmé)
- **RFC-0012** (migration API v6.2) : Proposé → Validated + amendement cohérence ADR-004
- Note : l'implémentation a précédé la validation formelle — écart assumé, CI à venir

---

## [MIGRATION API V6.2 — RFC-0012 + DEC-000023 + ADR-007] - 2026-07-16

Migration complète de l'API GSIE du schéma v6.1 (12 tables, `KnowledgeObject`)
vers le métamodèle v6.2 (73 types noyau, table racine `resource`).

### Ajouts

- **RFC-0012** — migration API v6.2 (73 types, resource racine, WebSocket, SDK)
- **ADR-007** — architecture API v6.2 (CRUD générique + modules par domaine)
- **DEC-000023** — décision de migration API v6.2
- **Table racine `resource`** (ADR-001) — class-table inheritance, 73 types, soft delete (CON-010)
- **73 modèles SQLAlchemy** groupés par domaine (12 fichiers) :
  - `provenance.py` — types 1-8 (Entity, Concept, Vocabulary, Instance, etc.)
  - `assertion.py` — types 9-13 (Assertion, Predicate, EvidenceAssessment, etc.)
  - `observation.py` — types 14-19 (Observation, Result, Method, Instrument, etc.)
  - `prov.py` — types 20-24 (Activity, ProvEntity, Agent, Source, Citation)
  - `spatial_temporal.py` — types 25-28 (Unit, Place avec PostGIS Geometry, TemporalContext, Media)
  - `temporal_engine.py` — types 29-30, 61 (Revision, Snapshot, ResourceDiff)
  - `models_ai.py` — types 31-36, 41, 50-52 (Model, Dataset, Feature, Inference, etc.)
  - `ecology.py` — types 43-49 (ScaleContext, Phenomenon, EcologicalProcess, etc.)
  - `reasoning.py` — types 53-60 (Question, Decision, Recommendation, Scenario, etc.)
  - `governance.py` — types 37-40, 42 (Rights, Access, Sensitivity, Conflict)
  - `dynamics.py` — types 59, 66-73 (EcosystemService, Flow, Goal, Constraint, etc.)
  - `fair_rgpd.py` — types 62-65 (Sample, Consent, DataSubject, PersistentIdentifier)
- **52 enums PostgreSQL** (§3.3 à §3.22 + enums supplémentaires + 7 enums audit)
- **17 tables de jonction n:m** (`junctions.py`) — ModelRun inputs/outputs, ConflictCluster assertions, Hypothesis supporting/contradicting, Decision recommendations/evidence, Recommendation assertions/scenarios, FeatureSet features, Experiment scenarios/model_runs, EcologicalState basis, Correlation variables, KnowledgeLineage derived, TerrainSession sampling/media
- **Outbox/Inbox pattern** (ADR-005) — `outbox.py` pour la cohérence événementielle
- **Object Storage abstraction** (ADR-006) — `object_storage.py` (S3/MinIO/local)
- **Registry pattern** — `@register_type` pour auto-enregistrement des 69 types resources
- **CRUD générique** — 8 endpoints `/api/v1/resources` pour les 69 types :
  - GET `/resources/types` — liste des types
  - GET `/resources` — liste paginée (filtre par type)
  - POST `/resources` — créer (Revision v1, validation dynamique, gsie_id auto)
  - GET `/resources/{id}` — détail
  - PUT `/resources/{id}` — mettre à jour (Revision + ResourceDiff, CON-010)
  - DELETE `/resources/{id}` — soft delete (Revision finale, CON-010)
  - GET `/resources/{id}/revisions` — historique des révisions (Temporal Engine)
- **Validation dynamique** — `validators.py` valide les champs obligatoires et enums par type
- **WebSocket** — `/api/v1/ws/hub` et `/api/v1/ws/events` pour le Hub (UE5.8) :
  - Auth JWT obligatoire (token en query param)
  - Rate limiting (10 messages/60s par client)
  - Validation des canaux (16 canaux autorisés)
  - Redis Pub/Sub pour fan-out inter-workers
  - Broadcast events sur create/update/delete
- **Migration Alembic 0002** — création des 73 tables + 17 jonctions + Outbox/Inbox + migration des données existantes
- **Tests** — 19 nouveaux tests (resources + WebSocket), 152 tests passent, 79 skipped (legacy v6.1)
- **Config** — paramètres WebSocket (max connections, heartbeat, allowed origins) + Object Storage (local path, S3 endpoint, bucket)

### Corrections (audit post-implémentation)

- **Soft delete au lieu de hard delete** (CON-010 respecté)
- **Revision créée dans update** (CON-010 respecté, avec ResourceDiff)
- **PostGIS Geometry** pour Place (GeoAlchemy2, SRID 2154)
- **Auth WebSocket** (token JWT en query param, close si invalide)
- **Validation dynamique** des `data` par type (champs obligatoires + enums)
- **17 tables de jonction n:m** manquantes ajoutées
- **12 types avec champs manquants** corrigés (ModelRun, DatasetVersion, ModelVersion, DataSubject, ConfidenceGraph, Goal, Constraint, KnowledgeLineage, TerrainSession, EcosystemService, ResourceDiff)
- **7 enums manquants** ajoutés (EcosystemServiceCategory, GoalPriority, ConstraintSeverity, PropagationMethod, ProductionMethod, TerrainSessionType, SyncStatus)
- **Redis Pub/Sub** pour WebSocket fan-out inter-workers
- **Outbox/Inbox** (ADR-005) pour la cohérence événementielle
- **Object Storage** (ADR-006) abstraction S3/local
- **4 fichiers de tests legacy** marqués skip (migration Vague 2)
- **gsie_id auto-généré** quand non fourni (ex. `assertion:2026:a1b2c3d4`)
- **Broadcast WebSocket** sur create/update/delete
- **Endpoint `/resources/{id}/revisions`** implémenté

### Breaking changes

- `KnowledgeObject` → `Assertion` (type 9 du métamodèle v6.2)
- `knowledge_objects` table → supprimée après migration vers `resource` + `assertion`
- Endpoints `/knowledge/*` migrés vers le CRUD générique `/resources` (Vague 2)

### Conservation

- Endpoint `/evidence/evaluate` — conservé (pas de breaking change)
- Auth JWT RS256 — conservée
- Middlewares (TraceId, CORS, rate limiting, Gzip) — conservés
- Pipeline Evidence → Knowledge devient Evidence → Assertion

---

## [MÉTAMODÈLE V6.2 — RFC-0011 + DEC-000022 + 6 ADR] - 2026-07-15

Rédaction complète du métamodèle v6.2 de l'Encyclopédie de l'Écosystème
et soumission à adoption via RFC-0011 + DEC-000022. Le métamodèle
définit un noyau universel de **73 types** en 5 niveaux, avec
PostgreSQL 16 + PostGIS comme vérité canonique. Neo4j, Elasticsearch,
Jena et GraphQL sont différés (projections régénérables, benchmark
Apache AGE en Vague 1).

La v6.2 enrichit la v6.1 (42 types) avec 18 types issus de la passe
écologique du Fondateur :
- ScaleContext (43) — multi-échelle écologique
- Phenomenon (44) + EcologicalProcess (45) — phénomènes et processus
- RelationType (46) — classification des prédicats
- SamplingEvent (47) — hiérarchie d'échantillonnage
- TraitDefinition (48) + TraitValue (49) — traits fonctionnels
- Feature (50) + FeatureSet (51) + Inference (52) — IA/ML
- Question (53) + Hypothesis (54) + Decision (55) + Recommendation (56) + Scenario (57) — raisonnement
- Correlation (58) — objet de connaissance versionné
- EcosystemService (59) — concept différé
- Capability (60) — orchestration moteurs/apps
- ResourceDiff (61) — GSIE Temporal & Provenance Engine (diff explicite entre revisions)
- Sample (62) — échantillon physique, mapping SOSA/SSN `sosa:Sample`
- Consent (63) + DataSubject (64) — conformité RGPD (art. 6 + 9.2.j)
- PersistentIdentifier (65) — FAIR F1 (DOI, PURL, ORCID, GBIF, Wikidata)
- Flow (66) — flux écologiques (carbone, eau, nutriments, énergie, graines, gènes, pathogènes)
- ConfidenceGraph (67) — graphe de confiance, propagation d'incertitude
- Goal (68) + Constraint (69) — objectifs de gestion + contraintes de faisabilité
- KnowledgeLineage (70) — DAG explicite de production de connaissance
- Experiment (71) — série de ModelRuns avec cadre de comparaison
- TerrainSession (72) — mission terrain GeoSylva (météo, GPS, martelage, inventaire)
- EcologicalState (73) — état synthétique de santé/vitalité/risque/résilience
- + 3 champs : Assertion.rule_subtype, Dataset.purpose, Scenario.scenario_subtype
- + document orchestration Knowledge OS §9.4 (à rédiger Vague 0)
- + stratification méta-architecturale (niveau 0 : Universe → MetaOntology → Ontology → MetaModel → Profiles → Applications)
- + section FAIR compliance §15.1 (audit 15 principes : 4/15 OK, cible 10/15 Vague 1, 15/15 Vague 2)
- + section RGPD §15.2 (art. 6, 7, 9.2.j, 15, 16, 17, 20, 30, 32, 35)
- + mapping SOSA/SSN §15.3 (W3C/OGC — 14 concepts mappés)
- + roadmap Vague 2 exhaustive (16 actions P1 + 20 actions P2)

**Documents créés** :
- `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` — livrable 213 v6.1 (654 lignes, 42 types)
- `02_RFC/RFC-0011-metamodele-encyclopedie-v6.1.md` — RFC principale (430 lignes)
- `02_RFC/annexes/annexe-302.md` à `annexe-205.md` — 7 annexes de superseding/amendement
- `03_DECISIONS/DEC-000022.md` — décision d'adoption (Proposé)
- `GSIE/ARCHITECTURE/ADR-001-racine-resource.md` — class-table inheritance, FK fortes
- `GSIE/ARCHITECTURE/ADR-002-pg-temporal.md` — GSIE Temporal & Provenance Engine (Revision + Snapshot + ResourceDiff + PROV-O)
- `GSIE/ARCHITECTURE/ADR-003-age-benchmark.md` — stratégie d'évaluation AGE vs Neo4j
- `GSIE/ARCHITECTURE/ADR-004-migration-schema.md` — migration knowledge_objects → v6.1
- `GSIE/ARCHITECTURE/ADR-005-outbox-inbox.md` — transactional outbox pattern
- `GSIE/ARCHITECTURE/ADR-006-object-storage.md` — interface MinIO/S3 pour DataAsset

**Superseding** (contenu historique conservé intact, CON-010) :
- Livrable 302 (Knowledge Method) — KnowledgeObject 6 types → Assertion + EvidenceAssessment
- Livrable 304 (Knowledge Graph Spec) — topologie Neo4j → tables PG + AGE
- Livrable 309 (Encyclopedia DB Schema) — 4 couches → PG canonique
- Livrable 310 (Engine Data Socle) — contrats moteurs KnowledgeObject → Assertion

**Amendements** :
- GSIE-DIR-0008 §2.1/§2.3/§2.4 — Neo4j/Jena/GraphQL différés
- DEC-000012 — ADR-0008/0009/0010/0011/0012/0013 → ADR-001 à ADR-006
- DEC-000019 — Vague 0 ajoutée, Vague 1 étendue (42 types)
- DEC-000020 — transition in-memory → schéma v6.1

**Annotation** : livrable 205 (Scientific Data Model, Draft) —
evidence_level → EvidenceAssessment, entités → profils v6.1.

**19 corrections intégrées** (5 P0, 8 P1, 6 P2) + 11 arbitrages
Fondateur additionnels. Statut : **Proposé** — en attente de validation
du Fondateur. Gate documentaire Vague 0 avant toute implémentation.

---

## [ARCHIVAGE PROPOSITION MÉTAMODÈLE V5] - 2026-07-15

Archivage de la proposition non adoptée de métamodèle v5 ; préparation
d'une convergence v6.1 avant RFC. Aucun choix d'architecture adopté.
Les deux documents v5 (`03_DECISIONS/DEC-000022.md` et
`GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md`) ont été retirés des
emplacements actifs et archivés intégralement dans
`22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/` comme ressources historiques non
normatives. Le numéro DEC-000022 reste disponible pour une future
décision après RFC.

> **Correction (même jour)** : l'emplacement `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md`
> n'est pas resté vide comme annoncé ci-dessus — un nouveau brouillon de travail (v6.1
> puis v6.2, non commité) y a été redéposé en parallèle pendant la préparation de
> RFC-0011. Ce brouillon porte désormais son propre avertissement de gouvernance en tête
> de fichier. RFC-0011.md et DEC-000022.md restent inexistants à ce jour ; rien n'est
> adopté.

---

## [VEILLE TECHNOLOGIQUE GSIE — 6 DOMAINES] - 2026-07-15

Rapport de veille technologique couvrant les 6 domaines GSIE (forestier,
géospatial, IA environnementale, incendies, Unreal Engine, Python
scientifique). Ajout de `GSIE/RESEARCH/VEILLE_2026-07-15.md`.

Trouvailles principales : ForestFormer3D et SelectAnyTree (segmentation
d'arbres LiDAR, candidats à évaluer pour succéder/compléter
SegmentAnyTreeV2), SAGStree et ForestSplat (Gaussian Splatting
forestier), citation JOSS officielle de ForeFire (DOI 10.21105/joss.08680,
à référencer pour Ignis), PostGIS 3.6.x (`ST_CoverageClean`,
`ST_ReclassExact`), Cesium for Unreal v2.28.0 (support UE 5.8, correctif
`UCesiumGaussianSplatSubsystem`), TorchGeo 0.9.0. Aucune connaissance
ingérée dans `GSIE/KNOWLEDGE/` — document au stade bibliographie brute,
non qualifiée A-F par l'Evidence Engine.

## [PIPELINE INTÉGRÉ EVIDENCE → KNOWLEDGE — SEMAINE 4] - 2026-07-15

### Tranche verticale prioritaire validée (DEC-000021)

Pipeline intégré chainant l'Evidence Engine et le Knowledge Engine de
bout en bout : soumission → qualification A-F → ingestion (si accepte) →
requête → révision (CON-010).

**Module `pipeline.py`** :
- `EvidenceKnowledgePipeline.process()` — traite une soumission de bout
  en bout : qualification Evidence + ingestion Knowledge si statut « accepte »
- `PipelineResult` — contient la connaissance qualifiée ET l'objet ingéré
  (si applicable), avec statut (ingested | quarantined | refused)
- `query()` et `revise()` — délèguent au Knowledge Engine
- Validation humaine (CON-001) : les connaissances quarantined/refused
  sont retournées à l'appelant, non ingérées automatiquement

**Tests d'intégration E2E** (11 tests) :
- 8 tests engine : ingest si accepte, refuse si F, quarantine si D,
  query après ingest, revise après ingest, préservation evidence_level,
  préservation source, type PipelineResult
- 3 tests API : pipeline complet via endpoints (evaluate → ingest →
  query), pipeline avec révision (evaluate → ingest → revise → query v2),
  refus d'ingestion d'une connaissance refusée

**Qualité** : 166 tests au total (155 + 11 nouveaux), Ruff + mypy --strict OK.

**Fichiers créés** :
- `GSIE/API/src/gsie_api/engines/pipeline.py` — module d'intégration
- `GSIE/API/tests/unit/test_pipeline.py` — tests E2E

**Décision** : DEC-000021 — Semaine 4 pipeline intégré.

---

## [KNOWLEDGE ENGINE — SEMAINE 3] - 2026-07-15

### Implémentation du Knowledge Engine (DEC-000020)

Moteur de base de connaissances — source unique de vérité pour tous les
moteurs de raisonnement. Conforme à KNOWLEDGE_ENGINE.md §5 (contrat d'interface)
et KNOWLEDGE_METHOD.md §2 (structure KnowledgeObject).

**Fonctionnalités** :
- **Ingestion** : reçoit les connaissances qualifiées (statut « accepte »
  depuis Evidence Engine), rejette quarantine et refuse (CON-001).
- **Requête** : 5 types (par_concept, par_relation, par_domaine,
  par_essence, par_station) avec filtres clé-valeur, filtre par niveau
  de preuve minimum, pagination.
- **Versionnement** (CON-010) : chaque révision archive l'ancienne version
  dans l'historique (VersionEntry avec justification), incrémente la
  version, aucune connaissance supprimée silencieusement.
- **Révision** : mise à jour du contenu, du niveau de preuve, de la source
  ou des domaines de validité, avec justification obligatoire.
- **Statistiques** : nombre d'objets par type.

**Endpoints API** :
- `GET  /api/v1/knowledge/status` — statut du moteur
- `GET  /api/v1/knowledge/version` — version et backend
- `POST /api/v1/knowledge/ingest` — ingère une connaissance (201)
- `POST /api/v1/knowledge/query` — interroge le graphe (200)
- `POST /api/v1/knowledge/revise` — révise une connaissance (200/404/400)
- `GET  /api/v1/knowledge/stats` — statistiques du graphe

**Qualité** :
- 33 nouveaux tests (19 unitaires + 14 API), 155 tests au total.
- Ruff + mypy --strict : zéro erreur.
- Rate limiting sur ingest (30/min) et query (60/min).
- Auth JWT obligatoire sur tous les endpoints POST/GET sensibles.

**Fichiers créés** :
- `GSIE/API/src/gsie_api/engines/knowledge/schemas.py` — schémas Pydantic
- `GSIE/API/src/gsie_api/engines/knowledge/engine.py` — implémentation
- `GSIE/API/src/gsie_api/engines/knowledge/router.py` — router FastAPI (remplace placeholder)
- `GSIE/API/tests/unit/test_knowledge.py` — tests unitaires engine
- `GSIE/API/tests/unit/test_knowledge_api.py` — tests API endpoints

**Décision** : DEC-000020 — Knowledge Engine Semaine 3.

---

## [STABILISATION QUALITE VAGUE 1] - 2026-07-14

### Passe qualité complète sur `GSIE/API` et `GSIE/ENGINES/EVIDENCE_ENGINE/rust`

- **Lint / type / tests** : Ruff, mypy `--strict` et Clippy `-D warnings` passent à zéro.
- **Tests** : 122 tests Python unitaires, 41 tests Rust et 2 tests d'intégration PostGIS/Redis passent (couverture Python 98 %).
- **CI** : `.github/workflows/ci.yml` étendue avec les jobs `python-quality` (Ruff, mypy, pytest unitaires), `python-integration` (testcontainers PostGIS/Redis), `rust-quality` (clippy, test) et `docker-build`.
- **Auth** : credentials dev (`admin/changeme`) retirés du code ; `auth_dev_username` et `auth_dev_password` sont désormais configurables via variables d'environnement. Dev login désactivé en production.
- **Evidence** : détection de conflits/versionnement protégée par le feature flag `evidence_experimental_conflicts_enabled` (désactivé par défaut, à valider scientifiquement avant activation).
- **Docker** : build multi-stage mis à jour pour compiler le moteur Rust via Maturin et installer le wheel `gsie_evidence` dans l'image API.
- **Dépendances** : suppression de `types-redis` (obsolète et conflictuel avec Redis 5.x+ qui embarque ses propres stubs).
- Fichiers modifiés : `GSIE/API/src/gsie_api/**/*.py`, `GSIE/API/src/gsie_api/engines/evidence/wrapper.py`, `GSIE/API/tests/**/*.py`, `GSIE/API/pyproject.toml`, `GSIE/API/.env.example`, `GSIE/API/Dockerfile`, `GSIE/ENGINES/EVIDENCE_ENGINE/rust/src/engine.rs`, `.github/workflows/ci.yml`.

## [NETTOYAGE GOUVERNANCE DOCUMENTAIRE] - 2026-07-14

### Correction d'incohérences résiduelles entre l'état réel du projet (Phase 4 active) et sa mémoire documentaire

Aucun changement de statut de livrable, de décision ou de phase — correction
de faits obsolètes dans `PROJECT_MEMORY.md` et `ROADMAP.md`, repérés lors
d'une tâche précédente mais non corrigés à l'époque (hors périmètre).

- `PROJECT_MEMORY.md`, section « Prochaine étape » : décrivait encore la
  Phase 3 comme passée en `Review` en attente de validation, alors que la
  Phase 3 est clôturée (DEC-000017) et que la Phase 4 est active depuis le
  2026-07-13 (DEC-000017 / GSIE-DIR-0011). Remplacée par un état factuel de
  la Phase 4 : Vague 1 (Fondations, DEC-000019) — semaines 1 et 2 livrées
  (FastAPI + Docker Compose, Evidence Engine cœur Rust + bindings PyO3,
  couverture de tests 100 %, durcissement sécurité), semaine 3 (Knowledge
  Engine) à venir ; état du chantier Hub (Centre de Commandement GSIE,
  environnement UE 5.8 configuré, projet réel hors dépôt sur
  `E:\GSIE-Centre-Commandement` et dépôt GitHub `NeooeN45/Hub`).
- `ROADMAP.md` : deux faits périmés corrigés — (1) la note d'audit
  2026-07-06 sur « 3 moteurs dédiés / 11 READMEs de cadrage » ne reflétait
  plus la réalité depuis le livrable 207 (Phase 2, les 14 moteurs ont
  chacun un fichier d'architecture dédié) et l'enrichissement du
  2026-07-13 (section « État de l'art » ajoutée aux 14 fichiers) ; note
  annotée « statut dépassé » avec mise à jour, sans supprimer l'historique.
  (2) le livrable 211 référençait encore l'ancien nom de fichier
  `GSIE_IGNIS_GCS_CINEMA_UNREAL.md`, renommé `COMMAND_CENTER_UNREAL.md`
  lors de l'élargissement du livrable au Centre de Commandement GSIE
  (GSIE-DIR-0009). En outre, la note de clôture de la section Phase 3
  (« la Phase 3 peut passer en Review ») était incohérente avec l'en-tête
  de la même section (« clôturée ✅ ») et le reste du document ; corrigée
  pour refléter la clôture effective par DEC-000017.

Mémoire synchronisée : `PROJECT_MEMORY.md`, `ROADMAP.md`.

---

## [CONFIGURATION CENTRE DE COMMANDEMENT UE5.8] - 2026-07-13

### Installation et configuration du poste de pilotage immersif (livrable 211)

Configuration complète de l'environnement Unreal Engine 5.8 pour le Centre
de Commandement GSIE, sur disque `E:\GSIE-Centre-Commandement` (anciennement
`E:\Quintessences unréal ungin`, renommé). Conforme à DEC-000010 (adoption
UE 5.8 + Cesium) et au livrable 211 (`COMMAND_CENTER_UNREAL.md`).

**Composants installés et configurés :**
- Unreal Engine 5.8.0 (changelist 55116800) — moteur
- Cesium for Unreal v2.28.0 (EngineVersion 5.8.0) — globe 3D géoréférencé,
  installé dans `Engine/Plugins/Marketplace/CesiumForUnreal/`
- Unreal MCP v2.2.0 (GenOrca, EngineVersion 5.8.0) — pilotage IA de l'éditeur
  via MCP (Claude Code, Cursor), 253 actions, précompilé UE 5.8
- Twinmotion 2026.1 — installé
- RealityScan 2.2 — photogrammétrie, installé

**Plugins natifs UE5.8 vérifiés présents :**
- GeoReferencing (avec PROJ/vcpkg — projections EPSG)
- Niagara (effets feu/eau/fumée)
- ScriptPlugin/PythonScriptPlugin (requis par Unreal MCP)

**Plugins source clonés (Plugins-Sources/) :**
- UE-GeoViewer (Will747) — overlay maps Google/Bing, import terrain HGT SRTM
- LandscapeGen (TensorWorks) — veille (EngineVersion 4.25, incompatible 5.8 sans refonte)

**Configuration système :**
- Registre Windows : `HKCU\...\Unreal Engine\Builds\UE_5.8` enregistré
- 8 variables d'environnement utilisateur (UE_ENGINE_PATH, GSIE_UE_ROOT, etc.)
- 3 raccourcis bureau (UE5.8 Editor, Twinmotion, RealityScan)
- Scripts utilitaires (Tools/) : verify-install, launch-ue, launch-twinmotion,
  launch-realityscan, clean-cache
- Config Cesium ion template (Tools/cesium-ion-config.json) — coordonnées
  Landiras (zone de test Ignis, 44.4764°N, -0.4236°E)

**Plugins à installer via Fab (marketplace Epic) — manuel :**
- BlueprintWebSocket (Pandoa) — gratuit, WebSocket pour Blueprints
- FluidFlux (ImaginaryBlend) — $349.99, simulation eau shallow-water (app Hydro)

Mémoire synchronisée : `PROJECT_MEMORY.md`.

---

## [ÉTAT DE L'ART SOURCÉ — 14 MOTEURS + CENTRE DE COMMANDEMENT] - 2026-07-13

### Enrichissement documentaire par recherche sourcée multi-agents

Aucun changement de phase, de statut de livrable ou de décision
structurante. Enrichissement de contenu à l'intérieur de documents
existants, tous restés en `Draft` — des pistes de recherche pour la
Phase 4, pas des choix d'implémentation arrêtés. Toutes les sources
vérifiées par recherche web avant intégration (GSIE-CON-002, GSIE-CON-005).

- Les **14 fichiers de moteurs** (`GSIE/ENGINES/*/*_ENGINE.md` —
  EVIDENCE, KNOWLEDGE, CORRELATION, REASONING, DIAGNOSTIC,
  RECOMMENDATION, VALIDATION, GIS, CLIMATE, PEDOLOGY, BOTANICAL,
  FOREST_DYNAMICS, LEARNING, SIMULATION) reçoivent chacun une nouvelle
  section **« État de l'art et pistes de recherche sourcées »** (§8, ou
  avant « Références » pour `SIMULATION_ENGINE.md`) : technologies,
  algorithmes, bibliothèques et bases de données concrets, précédents
  scientifiques (articles peer-reviewed, standards W3C/OGC, plateformes
  open source), tableau de synthèse + sous-section « Sources ». Aucun
  contrat d'interface ni aucune garantie déjà documentée n'est modifié.
- Renvois croisés ajoutés entre moteurs partageant une même piste
  technique : CAPSIS (Forest Dynamics ↔ Simulation), NED-2/EMDS
  (Reasoning ↔ Recommendation), forêts aléatoires/Random Forest
  (Correlation ↔ Diagnostic), PROV-O (Knowledge ↔ Recommendation ↔
  Validation).
- Deux corrections mineures suite à relecture critique croisée : URL
  FAO-56 corrigée (`CLIMATE_ENGINE.md`), mention de LIME complétée
  (`VALIDATION_ENGINE.md`).
- `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211, Centre de
  Commandement GSIE, Unreal Engine 5.8) passe de **v2.1.0 à v2.2.0** :
  nouvelle section 9 « Compléments de recherche (mise à jour) » —
  détail des fonctionnalités UE5.8 (Mesh Terrain, MegaLights, Movie
  Render Graph, Live Link Hub), mises à jour Cesium for Unreal / Cesium
  ion postérieures à avril 2026 (v2.28.0, tilers NetCDF/GeoJSON),
  précédents de convergence multi-domaines hors incendie (NVIDIA
  Omniverse/OpenUSD, ArcGIS Urban, service « Jumeau numérique » de
  l'IGN — précédent institutionnel français, `ign.fr/offre`), mise à
  jour de maturité du plugin **Unreal MCP** (désormais nommé et
  documenté officiellement par Epic, statut expérimental confirmé), et
  deux publications académiques 2026 (jumeau numérique hydraulique en
  Unreal Engine, pertinent pour l'app Hydro ; convergence SIG/moteur de
  jeu urbain).

Mémoire synchronisée : `PROJECT_MEMORY.md`.

## [VALIDATION ARCHITECTURE PHASE 4] - 2026-07-13

### Validation par 3 subagents de recherche (DEC-000019)

Analyse approfondie de l'architecture Phase 4 par 3 subagents en
parallèle (sources web 2025-2026) :

- **Multi-langage validé** : Python + Rust (pyo3) + Go différé
  (MAVSDK-Go est PoC en 2026, MAVSDK-Python est production). PyO3
  mature (Polars, Pydantic v2, Ruff — gains 7.4x). Pièges : GIL
  (`py.allow_threads()`), FFI overhead (profiler avant)
- **Architecture API validée** : FastAPI + asyncpg + PostGIS + Redis
  + OpenTelemetry. 5 ajustements P0/P1 : bypass PgBouncer pour
  LISTEN/NOTIFY, `statement_cache_size=0`, pygeoapi comme lib
  Starlette, modules par moteur (pas DDD pur), fastgeoapi P1
- **Plan refondu** : 8 semaines → 24 semaines (6 vagues). Respect
  strict du graphe de dépendances (livrable 204). Knowledge Engine
  ajouté (dépendance critique sautée). 2 semaines/moteur Rust
  (réaliste solo). ForeFire repositionné après Climate Engine

Livrables produits :
- `GSIE/RESEARCH/PHASE4_ARCHITECTURE_VALIDATION.md` (318 lignes)
- `GSIE/RESEARCH/API_TECHNOLOGY_RESEARCH.md` (1092 lignes, 30 recos)
- `03_DECISIONS/DEC-000019.md` (141 lignes)

## [STRATÉGIE IA IGN + GEOCONTEXT MCP] - 2026-07-13

### Découverte et capitalisation de la stratégie IA IGN (DEC-000018)

Analyse de la feuille de route IA IGN 2022-2024, de la page vigie IA et
du dépôt `ignfab/geocontext`. 4 livrables produits :

- **`GSIE/RESEARCH/IGN_IA_STRATEGY.md`** (292 lignes) : feuille de route
  IA IGN (6 axes, 3 objectifs), produits (CoSIA 20cm, OCS GE, GéoLLM,
  cartes Anthropocène), consortium AI4GEO, IGNfab, 8 recommandations
- **`.devin/config.json`** : MCP geocontext configuré (instance HTTP
  `https://geollm.beta.ign.fr/geocontext/mcp`). 10 outils : geocode,
  altitude, adminexpress, cadastre, urbanisme, assiette_sup,
  gpf_search_types, gpf_describe_type, gpf_count_features,
  gpf_get_features
- **`DATASET_CATALOG.md`** : 3 nouveaux datasets (DS-027 CoSIA, DS-028
  OCS GE, DS-029 Datasets apprentissage LiDAR HD). Total : 29 datasets
- **`HUB_AND_APPS_PLAN.md`** §11 : interopérabilité IGN geocontext MCP
  documentée pour les specs (HUB-001, HUB-003, IGNIS-001, GEO-001,
  GIS Engine)
- **`DEC-000018`** : décision tracée (3 actes, 8 recommandations)

Alignement thématique IGN ↔ GSIE : forêts (Forest Dynamics), érosion
(GIS/Simulation), cours d'eau (Hydro), artificialisation (GIS),
biodiversité (Botanical). geocontext = première brique d'interopérabilité
avec la Géoplateforme.

## [PHASE 3 CLÔTURÉE — PHASE 4 LANCÉE] - 2026-07-13

### Validation des 10 livrables Phase 3 (DEC-000017)

Le Fondateur valide les 10 livrables Phase 3 (`Review` → `Validated`) et
clôture officiellement la Phase 3 — Connaissance.

- 10 livrables (301-310) passés en `Validated`
- `GSIE-DIR-0007` amendé v1.2 (CLOS)
- `GSIE-DIR-0011` créée — lancement Phase 4 Implémentation
- `DEC-000017` tracée
- `ROADMAP.md` : Phase 3 → Clôturée ✅, Phase 4 → Active 🚀
- `PROJECT_MEMORY.md` : Phase courante → 4 — Implémentation

### Fiche recherche LiDAR HD IGN — analyse complète des 4 PDFs officiels

Sources : `DC_LiDAR_HD_1-0.pdf` (46p, descriptif de contenu v1.0 juillet 2026),
`SE_LiDAR_HD.pdf` (suivi des évolutions), `Offre_Produit_LiDAR_2025-08.pdf`
(accès aux produits), `Traitements_Produits_LiDAR_2025-08.pdf` (traitements).

- `GSIE/RESEARCH/LIDAR_HD_SPECIFICATIONS.md` enrichie (236 → 461 lignes) :
  - 11 classes avec codes ASPRS précis (1,2,3,4,5,6,9,17,64,66,67) et définitions IGN complètes
  - 13 attributs standards + 3 Extra Bytes (DTM_Marker, DSM_Marker, Origin)
  - Qualité géométrique : REMQ plani 11,7cm (exigence 50cm), REMQ alti 5,5cm (exigence 10cm)
  - Accès : COPC.LAZ, EPT/VPC (streaming), WMS-Raster (MNT/MNS/MNH + ombrages), API altimétrique
  - Traitements : calendrier diffusion (juin 2026), améliorations version finale
  - Points d'attention : déficit points sur eau, vég < 20cm = sol, vergers inclus, divers bâtis incertain
  - Classe 64 (sursol pérenne) = lignes électriques → détection risque incendie (Ignis)
  - 15 recommandations Phase 4 priorisées (P0/P1/P2)
- `DATASET_CATALOG.md` DS-002 enrichi : codes précis, attributs, accès, qualité

---

## [SPECS HUB + IGNIS + GEOSYLVA COMPLÈTES] - 2026-07-13

### 5 nouvelles spécifications Draft (HUB-003, IGNIS-002, IGNIS-003, GEO-002, GEO-003)

Complétion du plan `HUB_AND_APPS_PLAN.md` : les 9 spécifications P0/P1
sont désormais rédigées.

- **HUB-003** — Fiches détaillées des 25 couches du Hub (22 apps + 3
  globales). 14 champs par fiche (layer_id, geometry_type, canal,
  datasets, moteur, état, priorité P4). Matrice de compatibilité +
  priorités P0/P1/P2.
- **IGNIS-002** — Spec non fonctionnelle Ignis : performance (latence
  par flux, capacité), résilience (T-10), sécurité (JWT, TLS, rôles,
  RGPD), interopérabilité, souveraineté, explicabilité (CON-004),
  garde-fous RFC-0004 §8, scalabilité.
- **IGNIS-003** — Matrice de traçabilité Ignis : F-01→F-26, NF-01→NF-10,
  datasets (DS-001/002/009/010/022/023/024), moteurs (GIS, Climate,
  Simulation, Correlation, Learning), idées registre (P/J/V/G/S/D),
  couches Hub (ignis.*), garde-fous RFC-0004 §8.
- **GEO-002** — Spec non fonctionnelle GeoSylva : performance (mobile +
  Hub + segmentation), offline-first (RFC-0003, cache < 2 GB),
  résilience (ZICAD), sécurité, interopérabilité (app Android Kotlin),
  souveraineté, accessibilité mobile (terrain).
- **GEO-003** — Matrice de traçabilité GeoSylva : F-01→F-23,
  NF-01→NF-12, datasets (DS-001/002/003/025/026), moteurs (GIS, Forest
  Dyn., Botanical, Diagnostic, Recommendation, Simulation), ontologie
  S-6 (DOM-ECO/DEN/SYL/DYN), couches Hub (geosylva.*), précédents
  opérationnels (ONF, SDIS 63, Arbonaut).

Mémoire synchronisée : `PROJECT_MEMORY.md`, `ROADMAP.md`.

---

## [PHASE 3 — LIVRABLES 301-310 EN REVIEW] - 2026-07-13

### Passage des 10 livrables Phase 3 de `Draft` à `Review`

Les 10 livrables de la Phase 3 (301-310) passent en **Review** : contenu
rédigé, en attente de validation du Fondateur.

- Statut mis à jour (en-tête + pied) dans les 10 fichiers :
  `RESEARCH_METHOD`, `KNOWLEDGE_METHOD`, `FOREST_ONTOLOGY`,
  `KNOWLEDGE_GRAPH_SPECIFICATION`, `DATASET_CATALOG`, `EVIDENCE_FRAMEWORK`,
  `SOURCING_PLAN`, `KNOWLEDGE_BASE_SEED`, `ENCYCLOPEDIA_DATABASE_SCHEMA`,
  `ENGINE_DATA_SOCLE`.
- `ROADMAP.md` : table Phase 3 → tous en Review.
- `PROJECT_MEMORY.md` : section « Prochaine étape » actualisée.
- La validation `Review → Validated` relève du Fondateur (CON-001).

---

## [VAULT OBSIDIAN IGNORÉ — NON CANONIQUE] - 2026-07-13

### Vault Obsidian `Quintessences/Quintessences/` exclu du dépôt

Un vault Obsidian personnel (33 fichiers `.md`) dupliquait la gouvernance
dans une arborescence parallèle, avec un contenu **périmé et contradictoire**
(titres d'articles CON-002 à CON-007 erronés, statuts Locked incorrects,
CON-008/009/010 absents).

- Ajout de `/Quintessences/` au `.gitignore` (ancré à la racine).
- Le vault reste un **outil de navigation personnel local**, explicitement
  **non canonique**. La source de vérité de la gouvernance reste les
  dossiers numérotés (`00_CONSTITUTION/`, `03_DECISIONS/`, etc.).
- Aucun contenu constitutionnel faux n'entrera dans le dépôt.

---

## [PHASE 3 ÉTENDUE À 10 LIVRABLES] - 2026-07-13

### Extension du périmètre Phase 3 (8 → 10) — DEC-000016

Les livrables **309** (Schéma DB Encyclopédie) et **310** (Socle données
14 moteurs + liens apps), créés hors périmètre, sont rattachés
formellement à la Phase 3.

- `GSIE-DIR-0007` amendé (v1.0 → v1.1) — section « Amendement 2026-07-13 »
  ajoutée, texte d'origine (8 livrables) conservé (CON-010).
- `ROADMAP.md` : table Phase 3 étendue à 309-310, note de périmètre.
- `PROJECT_MEMORY.md` : périmètre mis à jour (10 livrables), DEC-000016
  ajoutée.
- Conciliation DEC-000012 : 309-310 sont des **spécifications** (aucun
  code) ; l'implémentation de l'Encyclopédie reste en Phase 4.

---

## [RFC-0002 ADOPTÉ — UNIFICATION DES ARTICLES] - 2026-07-13

### Adoption de RFC-0002 (Option A) — DEC-000015

Les fichiers `GSIE-CON-0XX.md` deviennent la **source de vérité unique**
du corpus d'articles constitutionnels.

- Suppression des 100 fichiers vides `ARTICLE_001.md` → `ARTICLE_100.md`
  (0 octet chacun, vérifiés avant suppression).
- Création de `00_CONSTITUTION/ARTICLES_INDEX.md` (index de renvoi).
- `00_CONSTITUTION/README.md` : section « Ce qui peut y être ajouté »
  corrigée (numérotation `GSIE-CON-0XX` non plafonnée à 100).
- `02_RFC/RFC-0002.md` passé en **Adopté** (section 9 ajoutée).
- `ROADMAP.md` : livrable 010 repointé, mention du gabarit `ARTICLE_0xx`
  retirée.
- `GSIE-CON-000.md` (Locked) non modifié.

### Mémoire du fondateur

- `22_PROJECT_MEMORY/FOUNDER_JOURNAL.md` : entrée du 2026-07-13 ajoutée
  (DEC-000011 à DEC-000015).

---

## [SPECS HUB + AUDIT PHASE 3] - 2026-07-13

### Spécifications créées (05_SPECIFICATIONS/)

- **HUB_001_SPECIFICATION.md** créé : spec fonctionnelle du Centre de
  Commandement (26 exigences : HUB-F-01 à HUB-F-26, HUB-NF-01 à
  HUB-NF-13). 3 cas d'usage (surveillance incendie, diagnostic
  sylvicole, exploration recherche). Matrice de traçabilité exigence →
  source. 13 couches Hub définies.
- **HUB_002_INTERFACE_CONTRACT.md** créé : contrat d'interface Hub ↔
  Apps. 22 couches initiales (geosylva.*, ignis.*, hydro.*, flora.*,
  artemis.*). Format payload temps réel (WebSocket/JSON) et volumineux
  (3D Tiles, GeoTIFF). Métadonnées requises (CON-005). Convention état
  réel vs simulé. Cycle de vie d'une couche. Version 1.0.0 du contrat.
- **IGNIS_001_SPECIFICATION.md** créé : spec fonctionnelle Ignis (357
  lignes, 26 exigences IGNIS-F-01 à F-26 en 8 sections : détection,
  combustible, météo, propagation, drones, visualisation Hub, garde-fous,
  données synthétiques. 10 exigences non fonctionnelles. 3 cas d'usage.
  Traçabilité : 7 datasets (DS-001/002/009/010/022/023/024), 30+ idées
  registre (P/J/V/C/G/D/S/M), garde-fous RFC-0004 §8, contrat HUB-002.
- **GEO_001_SPECIFICATION.md** créé : spec fonctionnelle GeoSylva (432
  lignes, 23 exigences GEO-F-01 à F-23 en 7 sections : inventaire,
  peuplements, biomasse, diagnostic, visualisation Hub, app mobile,
  état réel/simulé). 12 exigences non fonctionnelles. 3 cas d'usage.
  Traçabilité : 5 datasets (DS-001/002/003/025/026), ontologie forestière
  (livrable 303), gradient de fidélité (livrable 212 §1), précédents
  ONF/SDIS/Arbonaut (livrable 212 §3.3), contrat HUB-002.

### Audit Phase 3 (livrables 301-308)

- **Résultat : tous les 8 livrables sont complets et non stubs.**
- 301 RESEARCH_METHOD (~261 lignes) — pipeline 10 étapes ✅
- 302 KNOWLEDGE_METHOD (~358 lignes) — cycle de vie complet ✅
- 303 FOREST_ONTOLOGY (~803 lignes) — 10 domaines S-6 ✅
- 304 KNOWLEDGE_GRAPH_SPEC (~917 lignes) — raisonnement multi-échelle ✅
- 305 DATASET_CATALOG (~889 lignes) — 26 datasets (critère: ≥10) ✅
- 306 EVIDENCE_FRAMEWORK (~579 lignes) — 6 niveaux + exemples 10 domaines ✅
- 307 SOURCING_PLAN (~337 lignes) — 6 vagues alignées moteurs ✅
- 308 KNOWLEDGE_BASE_SEED (~668 lignes) — 25 connaissances (critère: ≥20) ✅
- **La Phase 3 peut passer en Review.**

---

## [SOURCES 3D + PLAN HUB] - 2026-07-13

### Enrichissement des sources de données (DATASET_CATALOG, livrable 305)

- **DS-002 (LiDAR HD IGN)** enrichi : MNT/MNS/MNH 50 cm, 84 % publié
  (juillet 2026), 9 cas d'usage IGN, précédents validés (SDIS 63, ONF,
  Arbonaut SaniLidar), webinaire IGN oct. 2025, restriction ZICAD.
- **DS-025 (GEDI L4A/L4B NASA)** créé : biomasse aérienne spatiale,
  footprint 25 m, grille 1 km, v3 publiée juin 2026.
- **DS-026 (ESA Biomass CCI v7)** créé : cartes globales AGB 2005-2024,
  1 ha, v7 publiée mai 2026 (Sentinel-1 + ALOS-2 + ICESat-2 + GEDI).
- Priorité d'ingestion mise à jour (vague 4 — Forest Dynamics).

### Mise à jour des précédents scientifiques (UNREAL_ENGINE_PRECEDENTS)

- **Cesium 3D Gaussian Splats** (avril 2026) : support production-ready
  dans Cesium for Unreal avec LOD hiérarchique, standardisation glTF
  (KHR_gaussian_splatting + SPZ -90 %), pipeline bout-en-bout Cesium ion.
- **SegmentAnyTreeV2** (2026) : foundation model segmentation d'arbres,
  F1 85 %, zero-shot cross-domain, code ouvert (Open Forest Observatory).
- **Crown-BERT** (2026) : classification d'essences par fusion LiDAR +
  hyperspectral drone, 83-91 % OA, 0.9 M params.

### Mise à jour des livrables d'architecture (Phase 2)

- **Livrable 211 (COMMAND_CENTER_UNREAL.md)** v2.1.0 : brique 5 Gaussian
  Splatting passée de « à tester » → « ✅ validé » (pipeline Cesium ion
  confirmé avril 2026). Section §2 enrichie avec la validation.
- **Livrable 212 (GEOSYLVA_UNREAL_ARCHITECTURE.md)** v1.1.0 : ajout de
  SegmentAnyTreeV2 et Crown-BERT au tableau §3.2, nouvelle section §3.3
  « Précédents opérationnels validés » (ONF, SDIS 63, Arbonaut).

### Veille partenariat (20_PARTNERSHIPS)

- **JUNN_VEILLE.md** créé : veille stratégique sur le programme JUNN
  (Jumeau Numérique National, IGN/Cerema/Inria, France 2030, 25 M€,
  14 partenaires). Alignement quasi 1:1 avec l'architecture Quintessences.
  Pas un partenariat actif — veille uniquement.

### Plan Hub + specs apps (05_SPECIFICATIONS)

- **HUB_AND_APPS_PLAN.md** créé : plan de production du Hub (Centre de
  Commandement) puis des spécifications de chaque app. Ordre : Hub (P0,
  bloquant) → Ignis (P1) → GeoSylva (P1) → Hydro/Flora (P2) →
  Artemis/QGISIA (P3). Exigences fonctionnelles et non fonctionnelles
  structurées (HUB-F-01 à HUB-F-10, HUB-NF-01 à HUB-NF-08, IGNIS-F-01 à
  IGNIS-F-10, GEO-F-01 à GEO-F-12). Contrat d'interface Hub ↔ Apps
  défini. Calendrier indicatif Phase 3 → Phase 4.

---

## [INTÉGRATION REPOS EXTERNES] - 2026-07-13

### Déplacement des repos externes dans la structure Quintessences

| Ancien chemin | Nouveau chemin | Repo git |
|---|---|---|
| `A:\GeoSylva\` | `apps/GeoSylva/` | GitHub: NeooeN45/GeoSylva |
| `A:\QGISIA\` | `apps/QGISIA/` | GitHub: NeooeN45/QGISIAPRO |
| `A:\GSIE-Dataset-Forge\` | `Forge/` | Pas de remote |

Ces repos gardent leur propre `.git` — ils sont indépendants du repo
parent Quintessences. Le `.gitignore` du parent les ignore.

### Fichiers de notes rangés

| Ancien chemin | Nouveau chemin |
|---|---|
| `A:\profile-readme.md` | `22_PROJECT_MEMORY/notes/profile-readme.md` |
| `A:\possible changement de noms.txt` | `22_PROJECT_MEMORY/notes/possible_changement_de_noms.txt` |
| `A:\modification a faire Architecture g.txt` | `22_PROJECT_MEMORY/notes/modification_architecture_globale.txt` |

### Nettoyage

- Stubs `apps/GeoSylva/README.md` et `apps/QGISIA/README.md` supprimés
  (remplacés par les vrais repos)
- `tmp_commit_msg.txt` supprimé

### À noter

- `apps/Artemis/` reste un stub (README.md seulement) — le code sera
  créé en Phase 4
- Le disque `A:\` est désormais propre : seulement `$RECYCLE.BIN` et
  `GSIE/` (qui sera renommé en `Quintessences/` par le Fondateur)

---

## [RÉORGANISATION ARBORESCENCE] - 2026-07-13

### Réorganisation du dépôt (DEC-000014, GSIE-DIR-0010)

Le Fondateur acte la réorganisation de l'arborescence du dépôt en trois
niveaux : **racine** (transverse), **GSIE/** (moteur), **apps/**
(applications clientes).

**13 dossiers déplacés vers GSIE/** :
- `04_ARCHITECTURE/` → `GSIE/ARCHITECTURE/`
- `06_RESEARCH/` → `GSIE/RESEARCH/`
- `07_KNOWLEDGE/` → `GSIE/KNOWLEDGE/`
- `08_DATASETS/` → `GSIE/DATASETS/`
- `09_ENGINES/` → `GSIE/ENGINES/`
- `10_ALGORITHMS/` → `GSIE/ALGORITHMS/`
- `11_MODELS/` → `GSIE/MODELS/`
- `12_APPLICATIONS/` → `GSIE/APPLICATIONS/`
- `13_API/` → `GSIE/API/`
- `14_SDK/` → `GSIE/SDK/`
- `15_TESTS/` → `GSIE/TESTS/`
- `16_TOOLS/` → `GSIE/TOOLS/`
- `17_DOCUMENTATION/` → `GSIE/DOCUMENTATION/`

**6 dossiers apps/ créés** :
- `apps/GeoSylva/` (forêt) — README créé
- `apps/Artemis/` (faune) — README créé
- `apps/Ignis/` (incendies) — déménagé depuis `22_PROJECT_MEMORY/Ignis/`
- `apps/Hydro/` (eau) — README créé
- `apps/Flora/` (végétation) — README créé
- `apps/QGISIA/` (plugin QGIS) — README créé

**454 remplacements de chemins** dans 73 fichiers.
**CLAUDE.md** entièrement réécrit avec la nouvelle arborescence.

### Documents créés

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0010.md` — directive réorganisation
- `03_DECISIONS/DEC-000014.md` — décision réorganisation

---

## [RESTRUCTURATION ÉCOSYSTÈME] - 2026-07-13

### Restructuration Quintessences (DEC-000013, GSIE-DIR-0009)

Le Fondateur acte une restructuration majeure de l'écosystème
Quintessences :

**Renommages** :
- Myhunt → **Artemis** (faune — comptages, pièges photo, empreintes,
  observations, populations)
- GSIE-Ignis → **Ignis** (incendies — DFCI, prévention, simulation,
  gestion de crise)

**Nouvelles applications** :
- **Hydro** (eau) — réseau hydrographique, zones humides, régimes
  hydriques. Moteurs : GIS, Climate, Knowledge, Correlation. Datasets :
  BD Carthage, BD TOPAGE, Sandre.
- **Flora** (végétation) — flore, taxonomie, cartographie végétale,
  phénologie. Moteurs : Botanical, Knowledge, GIS, Climate. Datasets :
  GBIF, Tela Botanica, BDNFF, INPN.

**QGISIA** : reste comme plugin QGIS de l'écosystème Quintessences.

**Centre de Commandement GSIE** (Unreal Engine 5.8) : repositionnement
majeur. UE n'est plus une simple visionneuse 3D — c'est un poste de
pilotage immersif où toutes les données convergent (GeoSylva, Artemis,
Ignis, Hydro, Flora). Mélange ArcGIS Pro + QGIS + Cesium + Flight
Simulator + Microsoft Digital Twins + moteur de jeu.

**Architecture cible** :
```
Quintessences → GSIE (moteur) → GeoSylva, Artemis, Ignis, Hydro, Flora, QGISIA
```

**Applications futures réservées** : Terra, Atmos, Atlas, Aether,
Chronos, Nexus…

### Fichiers renommés

| Ancien nom | Nouveau nom |
|---|---|
| `22_PROJECT_MEMORY/GSIE-Ignis/` | `apps/Ignis/` |
| `22_PROJECT_MEMORY/GSIE-Ignis.md` | `apps/Ignis/REGISTRE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` | `GSIE/ARCHITECTURE/IGNIS_ARCHITECTURE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_DATA_PIPELINE.md` | `GSIE/ARCHITECTURE/IGNIS_DATA_PIPELINE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_DRONE_ARCHITECTURE.md` | `GSIE/ARCHITECTURE/IGNIS_DRONE_ARCHITECTURE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` | `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` |

### Documents mis à jour

- 58 fichiers : remplacement Myhunt→Artemis et GSIE-Ignis→Ignis
- `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` : +Hydro, +Flora, matrice 6 apps
- `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` : +Centre de Commandement
- `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` : repositionnement GCS→Centre de Commandement
- `README.md` : architecture + Hydro + Flora + Centre de Commandement

### Documents créés

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0009.md` — directive restructuration
- `03_DECISIONS/DEC-000013.md` — décision restructuration

---

## [SCHÉMA DB + SOCLE MOTEURS] - 2026-07-13

### Livrables 309-310 — socle technique de l'Encyclopédie

**Livrable 309 — Encyclopédie Database Schema** (677 lignes) :
- 16 tables PostgreSQL/PostGIS avec DDL complet (sources, datasets,
  connaissances_meta, connaissances_versions, conflits,
  domaines_validite, taxons, types_sol, habitats, pathologies,
  insectes, modeles, moteurs_consommateurs, relations_meta,
  ingestion_logs, utilisateurs)
- Schéma Neo4j (labels, relations, contraintes, exemples Cypher)
- Index Elasticsearch (mapping full-text)
- Schéma RDF/OWL (préfixes, classes, propriétés, alignement LOD)
- Règles de génération d'identifiants uniques stables
- Mapping KnowledgeObject → PostgreSQL/Neo4j/RDF
- Pipeline d'ingestion, sécurité et accès

**Livrable 310 — Engine Data Socle** (768 lignes) :
- Socle de données détaillé pour les 14 moteurs (consomme/produit,
  domaines, datasets, entités, requêtes, dépendances, volumes)
- Liens vers les 4 apps externes (GeoSylva, Ignis, Artemis, QGISIA)
- Matrice moteur × app
- Priorité d'alimentation alignée sur l'ordre de développement (204)

### Documents créés

- `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` — livrable 309
- `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` — livrable 310

---

## [ENCYCLOPÉDIE DE L'ÉCOSYSTÈME] - 2026-07-13

### L'Encyclopédie de l'Écosystème (DEC-000012, GSIE-DIR-0008)

Le Fondateur acte la création de l'**Encyclopédie de l'Écosystème** :
la plus grande base de données structurée, sourcée et traçable sur tout
ce qui touche à l'écosystème. Cette encyclopédie est **le produit
principal** de GSIE, pas un sous-produit des moteurs.

**Échelle visée** : million d'entrées minimum.

**Périmètre** : flore, faune, sols, climat, hydrologie, pathologies,
entomologie, mycologie, interactions trophiques, dynamiques,
sylviculture, biodiversité, incendie.

**Architecture cible** (Phase 4) :
- Base graphe (Neo4j ou équivalent) — 10M+ nœuds
- Identifiants uniques stables et citables (GSIE-K-XXXXXXXXXX)
- Triple store sémantique (RDF/OWL, SPARQL)
- Pipelines d'ingestion automatisés (Airflow + NLP + LLM)
- 10 classificateurs (source, preuve, domaine, type, entités, relations,
  seuils, conflits, doublons, conformité)
- API GraphQL + REST + interface web
- Licence ouverte maximale

**Positionnement unique** : la seule base combinant taxonomie +
autécologie + pédologie + climat + interactions + modèles +
sylviculture, sourcé, versionné et interrogeable.

Le livrable 308 (25 connaissances) devient l'**amorce** de
l'Encyclopédie, pas le produit final.

---

## [PHASE 3 — CONNAISSANCE] - 2026-07-13

### Lancement officiel Phase 3 (DEC-000011, GSIE-DIR-0007)

Le Fondateur acte l'entrée en **Phase 3 — Connaissance**. La Phase 3
transforme les fondations scientifiques (Phase 1) et l'architecture
(Phase 2) en une **base de connaissances structurée, sourcée et
versionnée** — le véritable produit de GSIE (CON-003).

### 8 livrables Phase 3 (301-308)

| # | Livrable | Lignes | Description |
|---|---|---|---|
| 301 | Research Method | 261 | Pipeline 10 étapes avec critères opérationnels, articulation moteurs |
| 302 | Knowledge Method | 358 | Cycle de vie KnowledgeObject, 6 types, versionnement, domaines de validité |
| 303 | Forest Ontology | 803 | 10 domaines S-6, concepts, propriétés, relations, référentiels, échelles |
| 304 | Knowledge Graph Spec | 917 | Nœuds, arêtes, requêtes, versioning, graphe vivant DIR-0006, conflits S-3 |
| 305 | Dataset Catalog | 837 | 24 datasets (IGN, Météo-France, INRAE, GBIF, Copernicus, Prométhée) |
| 306 | Evidence Framework | 579 | Niveaux A-F, matrice de décision, 10 exemples par domaine, upgrade/downgrade |
| 307 | Sourcing Plan | 337 | 7 vagues alignées sur moteurs, 64 sources, critères de complétude |
| 308 | Knowledge Base Seed | 668 | 25 connaissances validées (5 essences + pédologie + croissance + taxonomie) |

### Documents créés

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0007.md` — Directive Phase 3
- `03_DECISIONS/DEC-000011.md` — Décision d'ouverture Phase 3
- `GSIE/RESEARCH/RESEARCH_METHOD.md` — détaillage (stub → 261 lignes)
- `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` — nouveau
- `GSIE/RESEARCH/SOURCING_PLAN.md` — nouveau
- `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` — détaillage (stub → 358 lignes)
- `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` — détaillage (stub → 803 lignes)
- `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` — détaillage (stub → 917 lignes)
- `GSIE/KNOWLEDGE/KNOWLEDGE_BASE_SEED.md` — nouveau
- `GSIE/DATASETS/DATASET_CATALOG.md` — nouveau

### Connaissances initiales (livrable 308)

25 KnowledgeObjects validés :
- Autécologie : chêne sessile (K-001 à K-004), hêtre (K-005 à K-007),
  douglas (K-008 à K-010), sapin pectiné (K-011, K-012), pin sylvestre
  (K-013, K-014)
- Pédologie : classes RUM, classes pH, profondeur, Alocrisol, Brunisol
  (K-015 à K-019)
- Croissance : ONF-FFN douglas, chêne, hêtre (K-020 à K-022)
- Taxonomie : Quercus petraea, Fagus sylvatica, Pseudotsuga menziesii
  (K-023 à K-025)
- 1 conflit bibliographique documenté (S-3) : gel du sapin pectiné
  (-20°C vs -15°C selon provenance)

---

## [UNREAL ENGINE — JUMEAU NUMÉRIQUE 3D] - 2026-07-12

### Adoption Unreal Engine 5.8 + Cesium (DEC-000010)

Le Fondateur acte l'adoption d'**Unreal Engine 5.8 + Cesium for Unreal**
comme moteur 3D du jumeau numérique vivant (DIR-0005). Cette décision
réalise l'ADR-001 du livrable 208 (moteur 3D interchangeable) et ouvre
deux nouveaux livrables Phase 2.

### Nouveaux livrables

- **Livrable 211 — GCS-Cinéma Unreal Engine (Ignis)** : architecture du
  poste de commandement 3D. UE 5.8 + Cesium (terrain géoréférencé, 3D
  Tiles, Gaussian Splats) + WebSockets natifs (ingestion temps réel) +
  Niagara (feu/fumée pilotés par données, façon FIRETWIN). Précédents
  scientifiques : FIRETWIN (NASA/NSF 2025), FIRE-VLM (2026), IVSR (2026).
  Prototype WebSocket en cours.
- **Livrable 212 — GeoSylva-Unreal Architecture** : pipeline LiDAR HD IGN
  → arbres individuels (PyCrown), génération procédurale scientifique
  (PCG + landscape data layers), gradient de fidélité (contexte /
  procédural / haute fidélité), synchronisation réel/simulé (CON-010).
  **En attente volontaire** jusqu'à MVP Ignis (règle S-08).

### Documents créés

- `GSIE/ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` (livrable 211)
- `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212)
- `03_DECISIONS/DEC-000010.md` (adoption UE 5.8 + Cesium)
- `GSIE/RESEARCH/UNREAL_ENGINE_PRECEDENTS.md` (fiches FIRETWIN, FIRE-VLM, IVSR)

### Documents mis à jour

- `GSIE/ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` (208) : ajout référence 211
- `GSIE/ARCHITECTURE/TECHNOLOGY_STACK.md` (202) : ajout ADR-0007 (UE 5.8 +
  Cesium), matrice de compatibilité étendue C++/UE
- `PROJECT_MEMORY.md` : DEC-000010 ajouté, documents d'architecture étendus
- `ROADMAP.md` : livrables 211 et 212 ajoutés

### Architecture partagée Ignis ↔ GeoSylva-Unreal

| Partagé (plugin commun) | Séparé (logique propre) |
|---|---|
| Cesium (terrain géoréférencé) | Niagara feu/fumée (Ignis) |
| WebSockets + JSON natif | PCG végétation (GeoSylva) |
| Conventions de données | Mode d'usage (temps réel vs planification) |

Recommandation : un seul projet Unreal en plugins internes (CON-007).

---

## [PHASE 2 — QUICK WINS] - 2026-07-12

### Audit global des 10 livrables Phase 2

Audit parallèle des 10 livrables (201-210) + 14 moteurs contre les critères
de complétude Phase 2. Scores : 201 (8→9), 202 (7), 203 (6), 204 (8.5→9),
205 (8→9), 206 (5 — point faible), 207 (97/100→100), 208 (6), 209 (6.5),
210 (5.5).

### Corrections apportées (4 quick wins initiaux)

- **Livrable 201 — Master Architecture** (524→717 lignes) : ajout des
  références sources scientifiques (mapping domaine → `GSIE/RESEARCH/` /
  `GSIE/DATASETS/`), liaison explicite des principes constitutionnels
  (CON-001 à CON-010), section modes dégradés (hors-ligne vs en ligne par
  moteur), esquisse des contrats d'interface (table inputs/outputs).
- **Livrable 204 — Development Order** (365→416 lignes) : en-tête complété
  (CON-004, CON-005, T-7), incohérence graphe Climate↔GIS corrigée, note
  de cohérence avec livrable 206, positionnement explicite des moteurs
  transverses (Forest Dynamics, Simulation, Learning), colonne Catégorie
  dans le tableau synthétique.
- **Livrable 205 — Scientific Data Model** (797→1179 lignes) : entité
  Peuplement (Stand) ajoutée, entités Forest Dynamics (GrowthModel,
  ForestProjection) ajoutées, entités de sortie spécifiées
  (DiagnosticReport, RecommendationSet, SimulationResult), section
  contraintes d'intégrité (règles de validation par domaine), diagramme
  et cardinalités mis à jour.
- **Livrable 207 — Simulation Engine** : format dépendances harmonisé
  (Type | Cible | Nature), contrat d'interface harmonisé (notation
  `champ : type`), titres cas d'usage standardisés (« Cas 1 — », « Cas 2 — »).

### Corrections apportées (vague 2 — complétion)

- **Livrable 202 — Technology Stack** : audit confirmé — ADR-0002/0003/0004
  déjà complets (Python, Rust, Go, TypeScript). Aucune modification nécessaire.
- **Livrable 203 — Communication Protocol** (6→8/10) : ajout §6.5
  priorisation des messages (critique/important/normal), §6.6 limites et
  mode dégradé (taille de file, comportement sur dépassement), §6.7 codes
  d'erreur offline, lien CON-003.
- **Livrable 206 — Interface Contracts** (5→9/10, 140→1223 lignes) :
  en-tête complété, types communs (SourceReference, EvidenceLevel,
  ConfidenceLevel, EmpriseGeographique, PeriodeTemporelle, IntervalleConfiance,
  IntervalleValeur), schémas formels des 14 moteurs (entrée + sortie +
  messages transverses), garanties de service par interaction (mode, latence,
  retry, timeout, idempotence), codes d'erreur par moteur, versioning SemVer
  des contrats, tests d'interface (conformité schéma, contrat comportemental,
  intégration inter-moteurs).
- **Livrable 208 — Ignis Architecture** (6→9/10, 549→847 lignes) :
  alignement DIR-0005 (§2bis — jumeau numérique vivant : terrain comme
  interface, zoom progressif, ADR-001 moteur 3D interchangeable, trois
  usages d'un socle, immersion), alignement DIR-0006 (§2ter — moteur
  cognitif : assimilation probabiliste, observateurs, graphe vivant,
  raisonnement multi-échelle/temporel/probabiliste, intelligence distribuée,
  IA collaborative, mémoire, explicabilité, auto-évaluation, curiosité
  artificielle sous supervision humaine, anticipation « signale et propose »,
  moteur scientifique), garde-fous RFC-0004 §8 référencés (non dupliqués).
- **Livrable 209 — Ignis Data Pipeline** (6.5→9/10, 569→829 lignes) :
  alignement DIR-0006 (§10 assimilation probabiliste multi-observateurs avec
  tableau de 16 observateurs, §11 raisonnement multi-échelle pixel→pays,
  §12 auto-évaluation + curiosité artificielle sous supervision humaine),
  alignement DIR-0005 (§13 présentation immersive du jumeau numérique,
  terrain comme interface, moteur 3D interchangeable, zoom progressif,
  interactions contextuelles), références DIR-0005/0006 ajoutées.
- **Livrable 210 — Drone Architecture** (5.5→8.5/10, 506→642 lignes) :
  alignement DIR-0006 (§11.1 drone comme observateur avec tableau capteurs,
  §11.2 intelligence distribuée, §11.3 curiosité artificielle sous supervision
  humaine), alignement DIR-0005 (§11.5 alimentation du jumeau numérique vivant,
  interactions au clic drone), sources externes (IGN, Météo-France, Copernicus),
  garde-fous RFC-0004 §8 référencés via §5.2 et §7.5 existants.

### Bilan Phase 2

Tous les livrables Phase 2 (201-210) sont maintenant Draft avec un niveau
de complétude suffisant pour passage en Review. Les 10 livrables respectent
les directives fondatrices DIR-0005/0006 et les garde-fous RFC-0004 §8.

---

## [GSIE-IGNIS — VISION MOTEUR COGNITIF] - 2026-07-12

### DEC-000009 — GSIE-DIR-0006 : le moteur cognitif Ignis

- **GSIE-DIR-0006** — Directive fondatrice compagnon de DIR-0005. Fixe la
  vision du **moteur cognitif** Ignis (le cerveau serveur).
- **Articulation** : DIR-0005 = « Le moteur graphique montre le monde. » ;
  DIR-0006 = « Le moteur cognitif le comprend. »
- **Principes** : le serveur n'est pas un backend mais un système
  d'intelligence (scientifique : collecte, compare, doute, vérifie, corrige,
  prédit, explique, apprend) ; assimilation permanente par fusion
  probabiliste multi-source ; monde comme graphe vivant de relations ;
  raisonnement multi-échelle, temporel et probabiliste ; simulation
  permanente même sans utilisateur ; intelligence distribuée (agents
  spécialisés) et IA collaborative (orchestration de modèles) ; mémoire
  versionnée ; explicabilité, auto-évaluation, curiosité artificielle,
  anticipation ; moteur scientifique (test de théories/IA/simulations).
- **Vision à long terme** : le feu n'est que le premier domaine ; architecture
  conçue pour s'étendre (santé des forêts, biodiversité, tempêtes, sécheresses,
  risques naturels, logistique de crise, gestion des territoires). Rejoint la
  vocation du moteur GSIE et de l'écosystème Quintessences.
- **Cadrage explicite** : curiosité artificielle et anticipation produisent
  des **propositions** sous supervision humaine — jamais de déclenchement
  automatique de mission, d'alerte ou d'intervention (RFC-0004 §8.3/§8.4,
  GSIE-CON-001). Agents = responsabilité unique, fusion explicable
  (GSIE-CON-007, GSIE-CON-004). Apprentissage versionné (GSIE-CON-010).
- **Statut** : `Draft` (en attente de validation du Fondateur).
- **Traçabilité** : `DEC-000009` acte l'adoption ; `PROJECT_MEMORY.md`,
  `ROADMAP.md` synchronisés.
- **Impact** : oriente les livrables Phase 2 n°208-210 (architecture
  Ignis) et les moteurs Reasoning / Correlation / Learning / Simulation.

---

## [GSIE-IGNIS — DIRECTIVE FONDATRICE GCS] - 2026-07-12

### DEC-000008 — GSIE-DIR-0005 : jumeau numérique vivant

- **GSIE-DIR-0005** — Directive fondatrice Ignis (GCS / Ground Control
  System). Fixe la vision produit : Ignis est un **jumeau numérique
  vivant** des opérations de lutte contre les incendies, pas un logiciel de
  cartographie, de drones ou de simulation.
- **Principes** : le terrain devient l'interface unique ; le moteur 3D
  (Unreal Engine ou successeur) est **interchangeable** et ne contient
  **aucune logique métier** (l'intelligence reste dans GSIE) ; un seul socle,
  trois usages (Opération, Formation, Recherche).
- **Cadrage explicite de l'autonomie** : la section « Autonomie » (intention
  vs commande) est cadrée par référence prioritaire à RFC-0004 §8.3/§8.4 —
  l'autonomie d'intention porte sur la sélection des moyens d'observation et
  la navigation ; la décision d'alerte, l'intervention et le commandement
  restent humains (COS / CODIS) ; reprise manuelle toujours possible ;
  aucune alerte directe à la population (FR-Alert).
- **Statut** : `Draft` (en attente de validation du Fondateur).
- **Traçabilité** : `DEC-000008` acte l'adoption ; `PROJECT_MEMORY.md`,
  `ROADMAP.md` synchronisés.
- **Impact** : oriente les livrables Phase 2 n°208-210 (architecture
  Ignis) et les futures spécifications.

---

## [GSIE-IGNIS — BANC DE SIMULATION] - 2026-07-12

### Premier vol drone réussi + 4 tests de vol avancés

- **PX4 SITL v1.18.0-beta1 + Gazebo Harmonic 8.14.0** opérationnels en
  headless sur WSL2
- **Diagnostic et résolution** du blocage au décollage (modèle x500_base
  sans plugins moteurs + setpoint de position insuffisant → setpoint de
  vélocité)
- **Test 1 — Premier vol** : décollage → 34 m → stabilisation → atterrissage ✓
- **Test 2 — Vol waypoint** : navigation 5 waypoints GPS (carré 100 m) ✓
- **Test 3 — Pattern carré** : surveillance 200 m × 200 m à 8 m/s ✓
- **Test 4 — Return-to-Home** : décollage + 150 m Nord + RTL (partiel :
  RTL activé mais atterrissage non complété en 60 s)
- **Test 5 — Surveillance incendie** : pattern lawnmower 4 lignes × 200 m
  avec capture de positions GPS (simulation observation front de feu)
- Scripts : `premier_vol.py`, `vol_waypoint.py`, `vol_pattern_carre.py`,
  `vol_rth.py`, `vol_surveillance_incendie.py`, `run_test.sh`
- ForeFire : compilation + démo propagation.png (Étape 2 validée)

---

## [PHASE 2 — DÉMARRAGE EFFECTIF] - 2026-07-12

### Production de l'architecture (10 livrables)

Démarrage effectif de la Phase 2 (Architecture) avec 3 axes en parallèle :

1. **Architecture des 14 moteurs** — contrats d'interface, entrées/sorties,
   dépendances, garanties, cas d'usage pour chaque moteur + matrice
   d'interactions croisée.
2. **Architecture technique globale** — stack technologique (ADR), protocole
   de communication offline-first, ordre de développement, modèle de données
   scientifique, architecture globale enrichie.
3. **Architecture Ignis** — pipeline de données (ForeFire, drone, GCS),
   architecture drone (PX4, MAVSDK, YOLO), intégration avec les 14 moteurs,
   garde-fous DEC-000003.

ROADMAP.md enrichi avec 10 livrables Phase 2 (201-210) et critères de
complétude.

README réécrit au niveau enterprise : badges, problem statement, tableau
comparatif avec la concurrence, architecture visuelle, gouvernance
constitutionnelle, roadmap, contributing.

---

## [RESTRUCTURATION IDENTITÉ] - 2026-07-12

### DEC-000006 — Quintessences, GSIE, GeoSylva

- **Quintessences** devient l'**écosystème** (marque umbrella) regroupant
  toutes les spécialisations environnementales.
- **GSIE** est redéfini : **General System Intelligence Engine** (avant :
  GeoSylva Intelligence Engine). C'est le **moteur** spécialisable par
  domaine, au cœur de Quintessences.
- **GeoSylva** est repositionné comme **app forestière** (première
  spécialisation de GSIE), au même titre que Ignis (spécialisation
  incendie). GeoSylva garde son nom historique.
- Architecture : `Quintessences > GSIE > GeoSylva / Ignis / futures`.
- README, PROJECT_MEMORY, ROADMAP, CHANGELOG, LICENSE mis à jour.
- La Constitution, les 14 moteurs, la gouvernance et la traçabilité
  restent valables — GSIE est généralisé, pas remplacé.

---

## [PHASE 2 — Architecture] - 2026-07-12

### DEC-000005 — Amendement : archivage du code du banc Ignis

- Le Fondateur **amende** DEC-000003 et DEC-000004 pour autoriser
  l'archivage du code du banc de simulation (Jalon 0) dans
  `apps/Ignis/`.
- Périmètre : `premier_vol.py`, `plot_front.py`, scripts `*.sh` du banc.
- Statut : **artefacts d'archive**, pas du code métier des 14 moteurs.
- Le banc opérationnel reste dans `~/Ignis/` (WSL2) ; le dépôt n'en
  conserve qu'une archive versionnée pour reproductibilité et traçabilité.
- L'interdiction de code métier GSIE dans le dépôt (Phase 4) reste entière.

### DEC-000004 — Entrée en Phase 2

- **Phase 1 clôturée** — tous les livrables Validated (9/12) ou Locked
  (3/12).
- **Phase 2 (Architecture) activée** par le Fondateur.
- Autorise : architecture détaillée des moteurs, spécifications
  techniques, RFC d'architecture, banc de simulation Ignis.
- N'autorise pas encore : code métier dans le dépôt GSIE (Phase 4).

### Banc de simulation Ignis — démarrage

- `.wslconfig` créé (20GB RAM, 6 CPU, 8GB swap).
- État WSL constaté : Ubuntu 24.04.3 LTS, Python 3.12.3, 8 threads,
  948 Go dispo sur E:.
- Installation du socle logiciel en cours (cmake, build-essential,
  libnetcdf-dev).
- Prochaines étapes : ForeFire (compilation + démo Aullène), PX4 SITL
  + Gazebo, structure projet `~/Ignis/`.

---

## [PHASE 1 CLÔTURÉE] - 2026-07-12

### Tous les livrables Validated ou Locked

La Phase 1 (Foundation) est **clôturée**. Les 12 livrables sont
dans un statut terminal :

| Statut | Count | Livrables |
|---|---|---|
| Validated | 9 / 12 | 001, 005, 006, 007, 008, 009, 010, 011, 012 |
| Locked | 3 / 12 | 002, 003, 004 |

### Livrable 011 — Documentation (Validated)

- `CODING_STANDARDS.md` : enrichi (11 → 82 lignes) — conventions nommage,
  structure fonctions, gestion d'erreurs, tests, typage, imports.
- `DEVELOPMENT_PLAYBOOK.md` : enrichi (17 → 68 lignes) — cycle de vie
  Spec→Impl→Tests→Review→Merge, commits conventionnels, ADR.
- `MASTER_ROADMAP.md` : enrichi (20 → 55 lignes) — aligné sur ROADMAP.md
  racine, 5 phases avec jalons et critères de succès.
- `PROJECT_EXECUTION_PLAN.md` : enrichi (16 → 64 lignes) — 9 étapes,
  6 jalons (M1-M6), dépendances entre livrables.
- `CONTRIBUTING_GUIDE.md`, `DOCUMENTATION_SYSTEM.md`,
  `WRITING_GUIDELINES.md` : statuts normalisés → Validated.
- `ENGINEERING_HANDBOOK_TOME_I_CHAPTER_1.md` : en-tête de statut ajouté.
- `MASTER_IMPLEMENTATION_GUIDE.md` : `Statut : Validated` ajouté
  (contenu non touché, v0.6.1 préservée).
- `ENGINEERING_HANDBOOK_TOME_I_CHAPTER_1.docx` : **supprimé** (le .md est
  la source de vérité, pas de binaire dans le dépôt).

### Livrable 010 — Articles CON-001 à CON-010 (Validated)

Les 10 articles constitutionnels ont été mis en conformité avec le
template RFC-0001 (ADOPTÉ) et validés :

- `GSIE-CON-001.md` à `GSIE-CON-010.md` : enrichis avec sections
  Exemple, Contre-exemple, Références, Historique, Statut.
- CON-008 (20 → 74 lignes) et CON-009 (21 → 70 lignes) : enrichis
  avec Conséquences, Exemple, Contre-exemple, Références.
- Tous passent de `Draft (À valider)` à `Validated`.

### Livrable 012 — Mémoire (Validated)

- `FOUNDER_JOURNAL.md` : enrichi (23 → 112 lignes) — 6 entrées datées
  (2026-07-01 à 2026-07-12) au format Décisions/Motivations/Impact.
- `CONTEXT_SNAPSHOT_001.md` : statut clarifié → `Draft — en attente du
  10e Directive`.
- `README.md` (`22_PROJECT_MEMORY/`) : `Ignis.md` et sous-dossier
  `Ignis/` ajoutés à la liste des fichiers autorisés.

### Prochaine étape

Le projet peut entrer en **Phase 2 (Architecture)** après décision du
Fondateur. Le banc de simulation Ignis (`~/Ignis/` WSL2) peut
démarrer indépendamment — il vit hors du dépôt GSIE.

---

## [Livrable 012 Validated] - 2026-07-12

### Mémoire du projet — livrable 012 passé en Validated

Le livrable 012 (Mémoire du projet et snapshots) passe de `Draft` à
`Validated` après audit et enrichissement :

- **`FOUNDER_JOURNAL.md`** : enrichi avec les entrées manquantes
  (2026-07-01 à 2026-07-12). Six entrées datées au format
  Décisions / Motivations / Impact, retraçant la fondation, l'outillage
  Claude Code, l'audit de conformité, l'ouverture des RFC-0002/0003/0004,
  la validation des livrables 005-009 et des articles CON-001 à 010.
- **`CONTEXT_SNAPSHOT_001.md`** : statut « Réservé » remplacé par
  « Draft — en attente du 10e Directive (non atteint) ». Note explicite
  ajoutée : le snapshot sera déclenché à la 10e Directive.
- **`README.md`** (`22_PROJECT_MEMORY/`) : `Ignis.md` et le sous-dossier
  `Ignis/` ajoutés à la liste des fichiers autorisés.

### Avancement Phase 1

- **Validated** : 8 / 12 (001, 005, 006, 007, 008, 009, 010, 012)
- **Locked** : 3 / 12 (002, 003, 004)
- **Draft** : 1 / 12 (011)

### Mémoire synchronisée

- `ROADMAP.md` : livrable 012 → Validated, avancement global mis à jour.
- `PROJECT_MEMORY.md` (racine) : avancement et prochaine étape mis à jour.

---

## [RFC-0004 Ignis — Registre d'idées] - 2026-07-11

### Registre d'idées opérationnelles

- Création de `apps/Ignis/REGISTRE.md` : registre vivant des idées
  Ignis structuré en 8 domaines (Perception, Jumeau numérique, Vol,
  Communications, GCS, Données, Stratégie) + feuille de route + backlog
  de questions ouvertes. Chaque idée est classée par maturité
  (💡/🔍/✅/⏸️/❌), priorité et notes opérationnelles.

### Mémoire synchronisée

- `PROJECT_MEMORY.md` : RFC-0004 référence désormais le registre
  `apps/Ignis/REGISTRE.md`.
- `02_RFC/RFC-0004.md` : étape 3 des prochaines étapes actionnables
  marquée comme réalisée (registre d'idées ouvert).

---

## [RFC-0004 Ignis] - 2026-07-11

### RFC ouvert

- **RFC-0004** — Ignis : Système autonome de surveillance et d'analyse des
  incendies. Proposition d'une nouvelle branche fonctionnelle dédiée au risque
  incendie, positionnée comme application cliente des 14 moteurs GSIE.
  (`02_RFC/RFC-0004.md`)

### Contenu du RFC

- Vision : détection précoce par drones, caractérisation de l'événement, jumeau
  numérique opérationnel du feu, analyse d'enjeux pour le COS / CODIS, autonomie
  drone sous supervision humaine.
- Exigences : sourçage scientifique, métriques domaine (rappel, faux positifs,
  latence, XAI), cadre réglementaire (EASA, SORA, BVLOS, DGAC, RGPD), injection
  de la connaissance métier forestière / DFCI.
- Écosystème : Pyronear, ForeFire, SDIS / CODIS, Prométhée ; datasets Pyro-SDIS,
  FLAME, D-Fire, FASDD, FIgLib, WildfireSpreadTS ; financements ANR, Horizon
  Europe, DGSCGC, CIFRE.
- Jalon : démonstrateur sans drone sur l'incendie de Landiras (Gironde, 2022).
- Points de vigilance : flou organisationnel (entreprise vs fondation), danger
  de la sortie « cause probable », limite du terme « autonome », interdiction
  d'alerte directe à la population, contrainte Phase 1 (pas de code métier).
- Recommandation : approche hybride — Ignis comme application, extensions
  ciblées des moteurs existants, moteur dédié éventuel réservé à un second RFC.

### Mémoire synchronisée

- `PROJECT_MEMORY.md` : date, RFC-0004 tracé.
- `ROADMAP.md` : RFC-0004 ajouté aux RFC ouverts.

---

## [Ignis gouvernance] - 2026-07-12

### Livrables 005-009 validés (Phase 1)

Les 5 livrables passent de `Review` à `Validated` après audit et
enrichissement par le Fondateur :

- **Livrable 005** — `PACT_FOR_AI_AGENTS.md` : enrichi (18 → 113 lignes).
  Ajout : Objectif, distinction des rôles (dev vs production), cas concrets,
  procédure de violation, anti-patterns, conséquences, historique,
  validation. Conformité template RFC-0001.
- **Livrable 006** — `GSIE-DESIGN-PHILOSOPHY.md` : enrichi (29 → 137
  lignes). Ajout : Objectif, principes numérotés et justifiés, exemples de
  décisions guidées par la philosophie (ForeFire GPL, 14 moteurs, Phase 1),
  cas limites, anti-patterns, conséquences, historique, validation.
- **Livrable 007** — `SCIENTIFIC_CONSTITUTION.md` : sections Historique +
  Validation ajoutées. Contenu inchangé (déjà solide, 168 → 184 lignes).
- **Livrable 008** — `TECHNICAL_CONSTITUTION.md` : sections Historique +
  Validation ajoutées. Contenu inchangé (173 → 190 lignes).
- **Livrable 009** — `AI_CONSTITUTION.md` : sections Historique +
  Validation ajoutées. Contenu inchangé (168 → 184 lignes).

### Avancement Phase 1

- **Validated** : 6 / 12 (001, 005, 006, 007, 008, 009)
- **Locked** : 3 / 12 (002, 003, 004)
- **Draft** : 3 / 12 (010, 011, 012)

### Reste à traiter pour clôturer Phase 1

- **Livrable 010** : articles CON-001 à CON-010 — aucun ne suit le template
  RFC-0001 (manquent Références + Historique). CON-008 et CON-009 (20-21
  lignes) sont très incomplets. À enrichir.
- **Livrable 011** : documentation et guides contributeurs — à évaluer.
- **Livrable 012** : mémoire complète — à évaluer.

### RFC-0004 ADOPTÉ

- **DEC-000003** tracée : adoption du RFC-0004 par le Fondateur. Ignis
  devient officiellement une branche fonctionnelle de GSIE, positionnée comme
  application cliente. Approche hybride retenue (Option C).
- RFC-0004 passe au statut **ADOPTÉ**.

### Registre d'idées Ignis

- `apps/Ignis/REGISTRE.md` : registre vivant créé par le Fondateur
  (version 0.7.x, 60+ idées en 9 sections : perception, jumeau numérique, vol
  drone, communications, GCS, données, stratégie, modèles IA, veille
  concurrentielle).
- `apps/Ignis/` : sous-dossier de livrables du Jalon 0
  (comparatif moteurs de simulation, contexte agent, guide d'installation banc).

### Pack contexte agent archivé

- `Ignis_pack_contexte_agent.zip` : lu et extrait. Contenu :
  `AGENTS.md` (contexte maître session), `LISEZMOI.md`, `Ignis_registre_idees.md`
  (v0.7.2), `Ignis_Phase0_comparatif_moteurs_simulation.md`,
  `Ignis_guide_installation_banc.md`.
- `AGENTS_contexte_session.md` et `guide_installation_banc.md` archivés dans
  `apps/Ignis/` avec note de gouvernance (le code du banc vit
  hors dépôt GSIE, dans `~/Ignis/` WSL2).
- Le zip reste ignoré par git (`.gitignore : *.zip`).

### Corrections de gouvernance appliquées

- **Statut ✅** : redéfini de « validée (intégrée à l'architecture) » en
  « principe accepté (intégration prévue en Phase 2+) » — aucune architecture
  n'est finalisée en Phase 1.
- **Phases renommées** : « Phase 0-6 » → « Ignis Jalon 0-6 » pour éviter la
  collision avec les phases GSIE globales (Phase 1-4). Note de rappel ajoutée.
- **RFC-0004** : §12 « Documents liés » ajouté (référence au registre et au
  sous-dossier Jalon 0).
- `PROJECT_MEMORY.md` : section « Branche Ignis (RFC-0004) » + DEC-000003.
- `ROADMAP.md` : RFC-0004 marqué ADOPTÉ.
- `.gitignore` : `*.zip` ajouté (le pack contexte agent binaire n'est pas
  versionné).

---

## [RFC-0003 + Review 005-009] - 2026-07-07

### RFC ouvert

- **RFC-0003** — Architecture distribuée GSIE-Net : capture la vision du
  Fondateur sur l'architecture offline-first, multi-couches, distribuée et
  orientée données. Activé en Phase 2. (`02_RFC/RFC-0003.md`)

### Livrables passés en Review

Cinq livrables passent du statut `Draft` au statut `Review` — soumis à la
validation du Fondateur :

- Livrable 005 — `PACT_FOR_AI_AGENTS.md`
- Livrable 006 — `GSIE-DESIGN-PHILOSOPHY.md`
- Livrable 007 — `SCIENTIFIC_CONSTITUTION.md`
- Livrable 008 — `TECHNICAL_CONSTITUTION.md`
- Livrable 009 — `AI_CONSTITUTION.md`

### Mémoire synchronisée

- `PROJECT_MEMORY.md` mis à jour : avancement Review 5/12, RFC-0003 tracé.
- `ROADMAP.md` mis à jour : statuts livrables + RFC-0003 + prochaine étape.

---

## [Conformité] - 2026-07-06

### Audit de l'état réel

- Cartographie complète du dépôt (277 fichiers `.md`) confrontée au ROADMAP et
  à la mémoire. Écarts de traçabilité et de conformité identifiés.

### Conformité des statuts (livrables 005, 006, 010)

- Ajout des champs `Statut : À valider` et `Classification : Loi Fondamentale
  (Immuable)` aux articles `GSIE-CON-005` à `GSIE-CON-010` (en-têtes non
  conformes au cycle de vie).
- Ajout d'en-têtes (édition, version, statut) à `PACT_FOR_AI_AGENTS.md` (005)
  et `GSIE-DESIGN-PHILOSOPHY.md` (006).
- Aucun document `Locked` modifié.

### Traçabilité

- `GSIE-DIR-0004` (GSIE Genesis Directive, ACTIVE) désormais tracée dans
  `PROJECT_MEMORY.md` (racine et `22_`). Elle en était absente.

### RFC

- **RFC-0002** ouvert : « Unification du système d'articles constitutionnels »
  (double système `ARTICLE_0xx` vides / `GSIE-CON-0xx` rédigés). Statut
  *Proposé*, en attente de validation du Fondateur. Aucune suppression exécutée.
- `RFC-0003` à `RFC-0010` : coquilles vides remplacées par des en-têtes
  « Réservé — non ouvert » (traçabilité conservée, aucun RFC supprimé).

### Livrables 011 et 012

- Rédaction des fichiers vides de `GSIE/DOCUMENTATION/` : `WRITING_GUIDELINES.md`,
  `DOCUMENTATION_SYSTEM.md`, `CONTRIBUTING_GUIDE.md`, `ADR_TEMPLATE.md` (Draft).
- `CONTEXT_SNAPSHOT_001.md` : en-tête de réservation ajouté (déclenchement prévu
  à la 10ᵉ Directive — non atteint, snapshot volontairement en attente).

### ROADMAP

- Livrable 010 repointé vers la source réelle (`GSIE-CON-0xx`) avec renvoi au
  RFC-0002.
- Requalification honnête des 14 moteurs (3 fichiers dédiés, 11 README de
  cadrage ; documentation complète = Phase 2).
- Mention des dossiers hors 12 livrables (`18_FINANCING`, `23_QUALITY_MANAGEMENT`)
  et de leur statut de gouvernance à statuer.

### Reste à la main du Fondateur

- Choix d'une option pour RFC-0002 (A / B / C).
- Levée ou confirmation de la réserve sur le `Locked` de `GSIE-CON-000`
  (« LOCKED sous réserve de validation du Fondateur »).
- Rattachement de `18_FINANCING` et `23_QUALITY_MANAGEMENT` aux livrables.

---

## [Outillage] - 2026-07-03

### Configuration Claude Code

- Initialisation du dépôt git + `.gitignore`
- `CLAUDE.md` racine (gouvernance opérationnelle pour les agents IA)
- `.claude/` : `settings.json`, hook `guard-locked` (protection des `Locked`),
  6 commandes métier, 3 sous-agents, skill projet `gsie-governance`
- Skills : installation vendorisée et épinglée de `mermaid` (MIT, commit
  `8ab1815`, provenance tracée) ; création de la skill `skill-management`
- `.claude/SKILLS_GSIE.md` : sélection des meilleures skills (internes,
  officielles et communautaires) par phase

---

## [0.0.1] - 2026-07-01

### Fondation

- Création de l'arborescence officielle (22 dossiers numérotés)
- Création de la Constitution : 6 documents transverses + 100 articles
  vides
- Création des RFC-0001 à RFC-0010 (RFC-0001 rédigée)
- Création des décisions DEC-000001 et DEC-000002
- Création de la Directive fondatrice GSIE-DIR-0001
- Création de la mémoire du projet (6 fichiers dans 22_PROJECT_MEMORY)
- Création des README de chaque dossier
- Création des fichiers racine : README, PROJECT_MEMORY, CHANGELOG,
  ROADMAP

### Décisions

- DEC-000001 : GSIE est une Fondation scientifique
- DEC-000002 : Phase 1 — Fondation, aucun développement métier

## [0.0.2] - 2026-07-01

### Documents fondateurs de la Constitution

- Création de `CONSTITUTIONAL_PREAMBLE.md` — autorité, portée,
  classification des lois (Immuables / Évolutives) et hiérarchie
  documentaire
- Création de `PHILOSOPHICAL_PREAMBLE.md` — vision, valeurs et
  convictions fondatrices
- Création de `ARTICLE_000.md` — Primauté de la Constitution (Loi
  Immutable, ADOPTÉ)

### Évolutions de RFC

- RFC-0001 : passage de BROUILLON à ADOPTÉ
- RFC-0001 : ajout des 4 décisions fondatrices
  - D1 : distinction Préambule constitutionnel / Préambule philosophique
  - D2 : introduction de l'Article 000 « Primauté de la Constitution »
  - D3 : classification des lois (Immuables et Évolutives)
  - D4 : hiérarchie documentaire officielle (Vision → Code)

### Mémoire du projet

- Mise à jour de `PROJECT_MEMORY.md` et `DECISION_HISTORY.md` avec les
  décisions fondatrices de RFC-0001

## [0.0.3] - 2026-07-01

### Lancement officiel Phase 1 Foundation (GSIE-DIR-0003)

- Création de la Directive `GSIE-DIR-0003` (ACTIVE)
- Définition des **12 livrables obligatoires** de la Phase 1
- La **documentation devient le produit principal** de la phase
- Aucun développement métier avant validation des 12 livrables

### Fichiers créés

- `GSIE/DOCUMENTATION/CONTRIBUTING_GUIDE.md` (vide — livrable 011)
- `GSIE/DOCUMENTATION/DOCUMENTATION_SYSTEM.md` (vide — livrable 011)
- `GSIE/DOCUMENTATION/ADR_TEMPLATE.md` (vide — livrable 011)
- `GSIE/DOCUMENTATION/WRITING_GUIDELINES.md` (vide — livrable 011)
- `22_PROJECT_MEMORY/CONTEXT_SNAPSHOT_001.md` (vide — livrable 012)

### Fichiers mis à jour

- `ROADMAP.md` — ajout de la Foundation Roadmap (12 livrables + statuts)
- `PROJECT_MEMORY.md` — entrée sur la documentation comme produit principal
- `22_PROJECT_MEMORY/PROJECT_MEMORY.md` — avancement des 12 livrables
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 3 nouvelles décisions DIR-0003
- `22_PROJECT_MEMORY/VISION_HISTORY.md` — Vision V1.1
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée Phase 1 Foundation

### Décisions

- DIR-0003-D1 : La documentation devient le cœur du projet
- DIR-0003-D2 : 12 livrables obligatoires, produits dans l'ordre
- DIR-0003-D3 : Aucun développement métier avant validation des 12 livrables

## [0.0.4] - 2026-07-01

### Verrouillage officiel des préambules fondateurs

- Rangement de `GSIE-FND-001.md` (Préambule Philosophique) dans
  `00_CONSTITUTION/` — LOCKED, v1.0, Première Édition
- Rangement de `GSIE-FND-002.md` (Préambule Constitutionnel) dans
  `00_CONSTITUTION/` — LOCKED, v1.0, Première Édition
- Suppression des drafts `PHILOSOPHICAL_PREAMBLE.md` et
  `CONSTITUTIONAL_PREAMBLE.md` (remplacés par les éditions officielles)
- Suppression de `PREAMBLE.md` (vide, hérité de l'ancienne structure)

### Avancement des livrables

- Livrable 002 (Préambule Constitutionnel) : Draft → **Locked**
- Livrable 003 (Préambule Philosophique) : Draft → **Locked**
- Total : 2 Validated, 2 Locked, 8 Draft

### Fichiers mis à jour

- `ROADMAP.md` — statuts 002 et 003 → Locked, avancement global
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — références et
  avancement
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — entrées FND-001, FND-002
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée verrouillage
- `02_RFC/RFC-0001.md` — références aux nouveaux noms de fichiers

## [0.0.5] - 2026-07-01

### Articles constitutionnels officiels

- Rangement de `GSIE-CON-000.md` dans `00_CONSTITUTION/` — La Primauté
  de la Constitution (LOCKED, Loi Fondamentale Immuable, v1.0)
- Rangement de `GSIE-CON-003.md` — La Connaissance avant le Code
  (Draft, à valider)
- Rangement de `GSIE-CON-004.md` — Toute décision doit être explicable
  (Draft, à valider)
- Rangement de `GSIE-CON-005.md` — Toute connaissance doit être
  traçable (Draft, à valider)
- Suppression du draft `ARTICLE_000.md` (remplacé par l'édition
  officielle `GSIE-CON-000.md`)

### Avancement des livrables

- Livrable 004 (Article 000) : Validated → **Locked** (édition officielle)
- Livrable 010 (Articles 001-100) : 3 articles rédigés (003, 004, 005)
  en attente de validation
- Total : 1 Validated, 3 Locked, 8 Draft

### Fichiers mis à jour

- `ROADMAP.md` — livrable 004 → Locked, tableau des articles rédigés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — références et
  avancement
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — entrées CON-000, 003, 004, 005
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée articles officiels

## [0.0.6] - 2026-07-01

### Articles constitutionnels supplémentaires

- Rangement de `GSIE-CON-006.md` — La Documentation fait partie du
  Produit (Draft)
- Rangement de `GSIE-CON-007.md` — La Modularité est obligatoire (Draft)
- Rangement de `GSIE-CON-008.md` — Le Projet appartient à sa Vision
  (Draft)
- Rangement de `GSIE-CON-009.md` — GSIE est un patrimoine scientifique
  vivant (Draft)
- Rangement de `GSIE-CON-010.md` — Toute connaissance doit pouvoir
  évoluer sans perdre son historique (Draft)

### Documents transverses (livrables 005 et 006)

- Rangement de `PACT_FOR_AI_AGENTS.md` dans `00_CONSTITUTION/` — Pacte
  des Agents IA (a remplacé le fichier vide — livrable 005)
- Rangement de `GSIE-DESIGN-PHILOSOPHY.md` dans `00_CONSTITUTION/` —
  Design Philosophy (a remplacé le `DESIGN_PHILOSOPHY.md` vide —
  livrable 006)

### Documents méthodologiques

- Rangement de `ARCHITECTURE_PRINCIPLES.md` dans `GSIE/ARCHITECTURE/`
- Rangement de `RESEARCH_METHOD.md` dans `GSIE/RESEARCH/`
- Rangement de `KNOWLEDGE_METHOD.md` dans `GSIE/KNOWLEDGE/`

### Avancement des livrables

- Livrable 005 (Pacte IA) : rédigé, à valider
- Livrable 006 (Design Philosophy) : rédigé, à valider
- Livrable 010 (Articles) : 9 articles rédigés (000, 003 à 010)
- Total : 1 Validated, 3 Locked, 8 Draft (dont 2 rédigés à valider)

### Fichiers mis à jour

- `ROADMAP.md` — statuts 005/006, tableau des articles (9 rédigés),
  documents transverses et méthodologiques
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — articles, documents,
  avancement, prochaine étape
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 11 nouvelles entrées
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée second lot

## [0.0.7] - 2026-07-01

### Documents d'architecture

- Rangement de `GSIE_MASTER_ARCHITECTURE.md` dans `GSIE/ARCHITECTURE/` —
  architecture globale en couches
- Rangement de `GSIE_CORE_BLUEPRINT.md` dans `GSIE/ARCHITECTURE/` —
  blueprint du cœur système (chaîne de moteurs)
- Rangement de `GSIE_DATA_FLOW.md` dans `GSIE/ARCHITECTURE/` — flux
  officiel des données

### Moteurs documentés

- Recréation de `GSIE/ENGINES/KNOWLEDGE_ENGINE/` — README + définition
  (`KNOWLEDGE_ENGINE.md`)
- Recréation de `GSIE/ENGINES/CORRELATION_ENGINE/` — README + définition
  (`CORRELATION_ENGINE.md`)
- Création de `GSIE/ENGINES/EVIDENCE_ENGINE/` — nouveau moteur, README +
  définition (`EVIDENCE_ENGINE.md`)

### Fichiers mis à jour

- `ROADMAP.md` — documents d'architecture et moteurs documentés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — nouvelles sections
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée architecture et moteurs

## [0.0.8] - 2026-07-02

### Genesis Directive (GSIE-DIR-0004)

- Création de la Directive `GSIE-DIR-0004` (ACTIVE, Priorité ABSOLUE,
  Classification FONDATION) dans `01_DIRECTIVES/ACTIVE/`
- Formalisation de l'identité, du rôle de l'agent, de la méthode de
  travail, des qualités prioritaires, des interdictions et de la
  philosophie modulaire
- Liste officielle des **14 moteurs GSIE**
- Liste officielle des **9 bases spécialisées**
- Décision : conservation de l'arborescence existante (22 dossiers),
  la directive s'intègre sans restructurer

### Articles constitutionnels manquants

- Création de `GSIE-CON-001.md` — Le forestier reste le décideur
  (Draft, Loi Fondamentale Immuable). Toute sortie est contournable,
  explicable, non-contraignante. Interdiction de décision automatique.
- Création de `GSIE-CON-002.md` — La science avant tout (Draft, Loi
  Fondamentale Immuable). Aucune connaissance sans source, niveau de
  preuve, traçabilité et révisabilité.

La Constitution compte désormais **11 articles** (CON-000 à CON-010),
tous rédigés.

### Nouveaux moteurs documentés

- Création de `GSIE/ENGINES/FOREST_DYNAMICS_ENGINE/` — dynamique des
  peuplements (nouveau, DIR-0004)
- Création de `GSIE/ENGINES/LEARNING_ENGINE/` — apprentissage (nouveau,
  DIR-0004, subordonné à CON-001 et CON-004)
- Création de `GSIE/ENGINES/SIMULATION_ENGINE/` — simulation de
  scénarios (nouveau, DIR-0004)

`GSIE/ENGINES/` contient désormais **6 moteurs documentés** sur 14.

### Analyse d'architecture

- 7 points de friction identifiés (contradiction Evidence Engine,
  pipeline linéaire, constitutions vides, absence de contrat
  d'interface, stratégie hors-ligne, README racine non aligné)
- Recommandation : ne pas verrouiller les documents d'architecture
  tant que les contradictions ne sont pas résolues

### Fichiers mis à jour

- `ROADMAP.md` — articles 001 et 002, 3 nouveaux moteurs
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — articles et
  moteurs
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — section 2026-07-02,
  6 nouvelles décisions
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée Genesis Directive

### Décisions

- DIR-0004-D1 : Genesis Directive officielle
- DIR-0004-D2 : Liste officielle des 14 moteurs GSIE
- DIR-0004-D3 : Liste officielle des 9 bases spécialisées
- DIR-0004-D4 : Conservation de l'arborescence existante
- CON-001 : Le forestier reste le décideur
- CON-002 : La science avant tout

## [0.0.9] - 2026-07-02

### Constitutions sectorielles (livrables 007, 008, 009)

- Rédaction de `SCIENTIFIC_CONSTITUTION.md` — 7 articles : sources
  acceptées (5 catégories), 6 niveaux de preuve (A-F), conflits
  bibliographiques, révision par RFC, incertitude explicite, 10
  domaines, patrimoine versionné
- Rédaction de `TECHNICAL_CONSTITUTION.md` — 10 articles : modularité,
  couplage faible, subordination code→connaissance, anti-duplication,
  tests obligatoires, versionnement, gestion d'erreurs, **hors-ligne
  (T-8)**, sécurité, dépendances
- Rédaction de `AI_CONSTITUTION.md` — 8 articles : rôle assistant,
  explicabilité, anti-boîte noire, apprentissage encadré, désaccord
  humain, biais affichés, agents IA soumis aux règles, pas de décision
  automatique

### Résolution de la contradiction Evidence Engine (ARCH-D1)

- `GSIE_DATA_FLOW.md` corrigé : Evidence Engine repositionné **avant**
  Knowledge Graph
- `GSIE_CORE_BLUEPRINT.md` corrigé : Evidence Engine repositionné
  **avant** Knowledge Engine
- Cohérence rétablie entre les 3 documents (Data Flow, Core Blueprint,
  README Evidence Engine)

### 14/14 moteurs documentés (ARCH-D2)

Création des 8 moteurs restants avec README (périmètre, principe,
frontières, position) :
- `REASONING_ENGINE/` — raisonnement sur connaissances
- `DIAGNOSTIC_ENGINE/` — diagnostics stationnels
- `RECOMMENDATION_ENGINE/` — recommandations contournables
- `VALIDATION_ENGINE/` — validation des sorties
- `GIS_ENGINE/` — données géospatiales
- `CLIMATE_ENGINE/` — données climatiques
- `PEDOLOGY_ENGINE/` — données pédologiques
- `BOTANICAL_ENGINE/` — flore et taxonomie

### README racine mis à jour

- Section « État du projet » reflète l'état réel (11 articles, 3
  constitutions sectorielles, 14 moteurs)
- Ajout section « Moteurs GSIE » : tableau des 14 moteurs + chaîne
  principale
- Ajout section « Bases spécialisées » : tableau des 9 bases

### Fichiers mis à jour

- `README.md` — sections moteurs et bases, état du projet
- `ROADMAP.md` — 14 moteurs, livrables 007-009 rédigés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — constitutions,
  14 moteurs, architecture corrigée
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 5 nouvelles décisions
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée constitutions +
  résolution Evidence Engine + 14 moteurs

### Décisions

- SCI-CON : Constitution Scientifique (livrable 007)
- TECH-CON : Constitution Technique (livrable 008)
- AI-CON : Constitution IA (livrable 009)
- ARCH-D1 : Evidence Engine repositionné en amont de Knowledge Engine
- ARCH-D2 : 14/14 moteurs officiels documentés
