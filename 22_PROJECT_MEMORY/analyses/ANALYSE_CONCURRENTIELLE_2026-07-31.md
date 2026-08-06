# Analyse concurrentielle approfondie — Écosystème GSIE

**Date** : 2026-07-31
**Auteur** : GLM 5.2 High (méthode unbridled, validée par le Fondateur)
**Portée** : État de l'art courant de GSIE + comparaison avec la concurrence mondiale + veille forums/sources

---

## 1. Vue d'ensemble de l'écosystème

### 1.1 Ce qui existe aujourd'hui

| Composant | État | Volume |
|---|---|---|
| **Gouvernance** | 39 décisions (DEC-000001→039), 29 RFC, Constitution (10+7+10 articles) | Mature |
| **14 moteurs GSIE** | 14 livrés (Recommendation 535 LOC, Validation 288 LOC, Simulation 164 LOC — vérifié 2026-07-31) | ~7 000 LOC Python + ~800 LOC Rust |
| **API GSIE** | FastAPI 0.115.6, JWT RS256, RBAC, WebSocket, 14 endpoints moteurs | Opérationnelle |
| **Base de données** | PostgreSQL 16 + PostGIS 3.4 + Apache AGE, 116 tables, 21 migrations | Score audit ~43% 🔴 |
| **Forge** | Usine de données Python/uv, 8 connecteurs vision, 4 documentaires | Alpha |
| **GeoSylva** | App Android Kotlin/Compose, 27 écrans, 339 fichiers | ~170k LOC, mature |
| **QGISIA** | Plugin QGIS React/Python, 7 agents, LiteLLM | ~180k LOC, mature |
| **Ignis** | Banc simulation PX4+Gazebo+ForeFire, 5/5 tests vol | ~15k LOC, prototype |
| **Hub UE5.8** | Projet créé, compilation validée | Cesium à configurer |
| **Artemis/Hydro/Flora** | Stubs (README uniquement) | 0 LOC |
| **Tests** | 1225 tests (1073 unitaires + 152 intégration) + harnais mutation | Couverture 80% |
| **CI/CD** | GitHub Actions : 6 jobs (markdown, consistency, python, rust, docker) | Opérationnelle |
| **Recherche** | 8 domaines sourcés, 29 datasets catalogués, 25 connaissances validées | Solide |

### 1.2 La chaîne des 14 moteurs

```
Sources externes → Evidence (Rust) → Knowledge (PostgreSQL)
→ Correlation (scipy) → Reasoning (AST déterministe + autécologie Rameau)
→ Diagnostic → Recommendation (535 LOC) → Validation (288 LOC) → Utilisateur

Moteurs domaine : GIS (IGN) | Climate (Météo-France ×7) | Pedology (SoilGrids)
                  Botanical (GBIF+TAXREF+Bellifa + autécologie) | ForestDynamics (géométrique)

Transverses : Learning (stateless) | Simulation (164 LOC — modèle linéaire v1)
```

### 1.3 Le plan de construction (24 semaines)

| Vague | Semaines | Contenu | Statut |
|---|---|---|---|
| 1 | 1-4 | FastAPI + Evidence + Knowledge + pipeline intégré | ✅ Clôturée |
| 2 | 5-15 | 14 moteurs + API Resources + outbox + enrichissement v1 | 🔄 En cours |
| 3 | 16-24 | Intégration apps + Hub UE5.8 + pilote Nouvelle-Aquitaine | ⬜ À venir |

---

## 2. Comparaison avec la concurrence

### 2.1 Concurrents directs — DSS forestiers

| Concurrent | Origine | Force | Faiblesse vs GSIE |
|---|---|---|---|
| **CAFE** (Espagne) | Académique | Multi-objectif, Pareto, eco-hydro process-based + génétique évolutive | Mono-domaine, pas de graphe de connaissances, pas d'explicabilité constitutionnelle |
| **Future Forest** (Allemagne) | Ministère allemand | Data space IDSA, 100m wall-to-wall, AI upscaling | Pas de chaîne de raisonnement modulaire, pas offline-first terrain |
| **WIS.2** (Suisse) | SmartForest | 20 ans de recul, close-to-nature, simulations long terme | Outil desktop, pas d'API, pas d'IA, pas de jumeau numérique |
| **SYLVECO** (FCBA, France) | Consortium industriel | Simulateur de croissance maritime pine, modules économiques | Mono-essence, pas d'IA, pas de raisonnement, pas de multi-domaine |
| **NEOSILVA** (ANR, France) | Recherche INRAE-Silva | DSS multi-critères petites forêts privées, diagnostic→trajectoire→suivi | Projet de recherche, pas d'implémentation opérationnelle |
| **Sylv'éclair** (Nouvelle-Aquitaine) | OG SPNA | Outil thinning pin maritime, base de données terrain | Mono-essence, mono-opération, pas d'IA |
| **NCX/SilviaTerra** (USA) | Startup Yale | Basemap AI (every acre every year), marketplace carbone, 1.17M acres | Focus carbone uniquement, pas de diagnostic sylvicole, pas multi-domaine |

### 2.2 Concurrents knowledge graph écologique

| Concurrent | Échelle | Force | Faiblesse vs GSIE |
|---|---|---|---|
| **Treekipedia/SilviProtocol** | 67 743 espèces, 5.7M tuiles geohash | SPARQL + GraphDB, ontologie formelle, open source, IPFS | Pas de raisonnement, pas de diagnostic, pas de DSS, focus taxonomique uniquement |
| **FooDS** (Bornéo) | Forest Observatory | Ontologie FOO, capteurs wildlife, raisonnement sur données | Mono-site, pas de sylviculture, pas de DSS |
| **Digital Forest** (UMaine) | Académique | 3 ontologies (STAD, FIO, PrefEnvO), interface sémantique | Pas d'implémentation opérationnelle, pas de moteurs |
| **Ecolink** (2025) | Open source | Schéma LinkML pour knowledge graph environnemental | Schéma uniquement, pas d'implémentation |
| **Forest RAG** (Basque) | Local | RAG + knowledge graph NetworkX, 1250 espèces méditerranéennes | Prototype local, pas d'architecture modulaire, dépend GPT-4o |

### 2.3 Concurrents jumeau numérique incendie

| Concurrent | Stack | Force | Faiblesse vs GSIE |
|---|---|---|---|
| **NVIDIA + Lockheed Martin** | Omniverse + CMM + DGX | Digital twin feu, Rothermel, recommandations suppression | Propriétaire, US-centric, pas multi-domaine |
| **NASA Wildfire Digital Twin** | WRF-SFIRE, 10-30m | API laptop/tablet, ensemble models, FireSense | US-centric, pas de convergence forêt+feu+eau |
| **OroraTech + Earth-2** | Satellites thermiques + Earth-2 | 27 satellites, détection temps réel, edge computing | Détection uniquement, pas de simulation terrain |
| **FIRETWIN** (2025) | Multi-modal sensing | Sensing tactique, analytics interactives | Recherche, pas d'opérationnel |

### 2.4 Patterns d'architecture IA de l'état de l'art

| Pattern | Source | GSIE l'applique ? |
|---|---|---|
| **Séparation langage/reasoning** (LLM = sensor, moteur déterministe = reasoning) | MoBayes/BMBE, SymptomWise | ✅ **Oui** — Reasoning Engine est déterministe (AST, pas d'eval), LLM jamais dans la chaîne de décision |
| **Workflow hiérarchique evidence-based** | MedAgent-Pro | ✅ **Oui** — chaîne Evidence→Knowledge→...→Validation |
| **Modularité avec modules remplaçables** | MoDN, MEDDxAgent | ✅ **Oui** — CON-007, interfaces contractuelles, DI |
| **Déterminisme + rejeu** | SymptomWise, Hackernoon | ✅ **Oui** — uuid5, ordre total, rejeu idempotent Diagnostic |
| **Explicabilité par artefacts structurés** | LLM Driven Processes | ✅ **Oui** — DecisionPassport, chaîne d'inférence, trace_id |
| **Garde-fou anti-hallucination** | Avectic deterministic layer | ✅ **Oui** — RFC-0014 §3.2, garde-fou anti-invention, citation mot pour mot |

---

## 3. Ce que GSIE fait mieux que la concurrence

### 3.1 Gouvernance constitutionnelle — **unique au monde**

Aucun concurrent n'a une Constitution (10 articles fondateurs + 7 scientifiques + 10 techniques), un système de statuts (Draft→Review→Validated→Locked), une hiérarchie documentaire stricte, et 39 décisions tracées.

### 3.2 Chaîne de raisonnement modulaire déterministe — **état de l'art**

La séparation stricte entre langage (jamais dans la décision) et raisonnement (déterministe, AST, auditable) est exactement ce que les recherches 2025-2026 (MoBayes, SymptomWise, MedAgent-Pro) identifient comme l'architecture correcte.

### 3.3 Multi-domaine convergent — **pas d'équivalent**

Aucun concurrent ne combine forêt (GeoSylva) + incendie (Ignis) + faune (Artemis) + eau (Hydro) + végétation (Flora) dans un seul écosystème avec un Centre de Commandement immersif (UE5.8 + Cesium).

### 3.4 Niveaux de preuve A-F + garde-fou anti-invention — **plus strict que quiconque**

La matrice Evidence Engine (type_source × type_contenu → A-F) avec plafond par catégorie, upgrade par convergence, downgrade par robustesse, et garde-fou anti-invention (citation mot pour mot, statut quarantine/rejete) est plus rigoureuse que tout ce que les concurrents proposent.

### 3.5 29 datasets catalogués avec licences + 8 domaines sourcés

Le catalogue DATASET_CATALOG.md (DS-001 à DS-029) avec producteur, résolution, licence est plus structuré que ce que proposent les concurrents.

### 3.6 Tests + harnais de mutation — **maturité enterprise**

1225 tests + harnais de mutation (14/14) + CI GitHub Actions 6 jobs + couverture 80% forcée. Aucun concurrent académique ou startup n'a ce niveau de rigueur test.

### 3.7 Résilience clients API — **pattern maison**

La convention `ResilientHttpClient` avec `CLIENT_REGISTRY` + 5 modes de panne testés pour 10 clients API externes est un pattern enterprise.

### 3.8 Offline-first terrain (GeoSylva) — **meilleur du marché français**

GeoSylva (339 fichiers Kotlin, 27 écrans, 7 méthodes de cubage, IBP CNPF, 12 couches carto, clinomètre numérique, exports SIG) est plus complet que Sylv'éclair, SYLVECO, et tout ce qui existe en France.

---

## 4. Ce que GSIE fait moins bien que la concurrence

### 4.1 🔴 Échelle de données — gap majeur vs Treekipedia

**Treekipedia** : 67 743 espèces, 17.6M observations, 5.7M tuiles geohash, 31 796 images.
**GSIE** : 25 connaissances validées, pilotes d'extraction pour ~8 essences.

### 4.2 🔴 Base de données — score 43% (P0 critiques)

5 P0 bloquants : aucune sauvegarde (RPO = ∞), pool non borné, 110 FK sans index, compte unique superuser, service DB non durci.

### 4.3 🟡 Intégration apps ↔ GSIE — **inexistante**

GeoSylva, QGISIA, Ignis : 0 intégration GSIE. Le SDK GSIE est vide (README uniquement).

### 4.4 ✅ 3 moteurs critiques implémentés (vérifié 2026-07-31)

~~Recommendation, Validation, Simulation = 0 LOC.~~ **Corrigé** : les 3 moteurs sont implémentés.
- Recommendation Engine : 535 LOC (`engines/recommendation/engine.py`) — propositions sylvicoles justifiées et contournables, persistance des décisions forestier, alternatives systématiques.
- Validation Engine : 288 LOC (`engines/validation/engine.py`) — 5 contrôles déclaratifs (presence_niveau_preuve, presence_source, presence_chaine_inference, recommandation_contournable, explicabilite), statuts valide/bloque/partiellement_valide.
- Simulation Engine : 164 LOC (`engines/simulation/engine.py`) — projection déterministe linéaire v1, confidence=low explicite, hypothèses simplificatrices documentées (GSIE-CON-004).
- Modules transverses : `growth_models.py` (226 LOC), `simulation_backend.py` (225 LOC), `validation_pipeline.py` (277 LOC).
- Tests : unitaires + intégration pour les 3 moteurs.

### 4.5 ✅ Autécologie ingérée — Reasoning/Diagnostic débloqué (vérifié 2026-07-31)

~~Le contrat Reasoning/Diagnostic exige de raisonner sur l'autécologie des essences. Botanical Engine v1 n'a pas d'autécologie.~~ **Corrigé** : l'autécologie est implémentée.
- `engines/autecology_adapter.py` (110 LOC) — câble le Reasoning Engine sur les profils `AutecologyProfile` (Parelle 2007, Rameau 2008), transforme un corpus autécologique en règles d'inférence génériques.
- Mapping grade de preuve → niveau de confiance explicite (A=0.95, B=0.8, C=0.6...).
- Tests : `test_autecology_adapter.py`, `test_autecology_pilot_data.py`, `test_autecology_rameau_data.py`.
- Limite v1 documentée : conditions sur `essence` uniquement (pas de comparaison pH/altitude), résolution GBIF statique — future version utilisera le Botanical Engine.

### 4.6 🟡 Pas d'ontologie formelle (RDF/OWL/SPARQL)

Tu as Apache AGE (Cypher) mais pas d'ontologie formelle au sens W3C. Treekipedia utilise Darwin Core + ENVO + PATO + PROV.

### 4.7 🟡 Pas de projections climatiques (DRIAS)

Climate Engine v1 : observations uniquement. Pas de projections climatiques (DRIAS/RCP nécessitent clé API Météo-France).

### 4.8 🟡 Forest Dynamics très restreint

Surface terrière uniquement. Pas de volume, pas de trajectoire de croissance, pas de densité, pas de hauteur dominante.

### 4.9 🟡 Pas de marketplace / monétisation

NCX a un marketplace carbone (Microsoft, Shell, South Pole). Pas de modèle de monétisation documenté.

### 4.10 🟡 Pas de déploiement cloud

Tout est Docker local. Pas de Kubernetes, pas de cloud, pas de managed PostgreSQL.

---

## 5. Veille forums/sources

### 5.1 ✅ Ce qui est correct

- Sources institutionnelles françaises (IGN, INRAE, ONF, Météo-France, MNHN, GBIF, ISRIC, Copernicus)
- Niveaux de preuve A-F (inspirés de l'EBM appliqué à la foresterie)
- Garde-fou anti-invention (RFC-0014 §3.2)
- Déterminisme du Reasoning (évaluateur AST)

### 5.2 ⚠️ Ce qui pourrait être mieux

- **Ontologie formelle** : ajouter une couche RDF/OWL exportable depuis AGE
- **SQL/PGQ vs Apache AGE** : PostgreSQL 19 (beta juin 2026) intègre SQL/PGQ natif (ISO/IEC 9075-16:2023). Planifier la migration.
- **PostGIS best practices** : vérifier GEOMETRY(type, SRID), index GiST, GEOGRAPHY vs GEOMETRY
- **FastAPI architecture** : APIRouter par moteur, Depends, pydantic-settings, Annotated
- **LiDAR HD IGN** : intégrer dans Forest Dynamics Engine v2 (ITD — Individual Tree Detection)
- **ForeFire vs Earth-2** : ForeFire reste pertinent pour Ignis, mais envisager Earth-2 pour le Hub UE5.8
- **Treekipedia comme référence** : audit comparatif sur le schéma de connaissance

### 5.3 🔴 Ce qui manque dans la veille

- Pas de veille automatisée (skill `/veille-techno` quota épuisé)
- Pas de benchmark public (Golden Bench DEC-000028 statut Proposé)
- Pas de communauté open source

---

## 6. Synthèse — Score global

| Dimension | Score | vs Concurrence |
|---|---|---|
| **Gouvernance** | 95% | 🟢 Leader — unique au monde |
| **Architecture moteurs** | 85% | 🟢 État de l'art (déterministe, modulaire) |
| **API** | 80% | 🟢 Solide (FastAPI, JWT, RBAC, WebSocket) |
| **Base de données** | 43% | 🔴 Critique (P0 sauvegardes, index, hardening) |
| **Tests** | 85% | 🟢 Enterprise (1225 tests + mutation) |
| **Volume de connaissances** | 15% | 🔴 Très en retard vs Treekipedia (25 vs 67k) |
| **Apps clientes** | 70% | 🟡 Mature mais 0 intégration GSIE |
| **Intégration apps↔GSIE** | 0% | 🔴 Inexistante (SDK vide) |
| **Moteurs complétés** | 100% (14/14) | Tous implémentés (vérifié 2026-07-31) |
| **Déploiement** | 30% | 🔴 Docker local uniquement |
| **Recherche/datasets** | 80% | 🟢 29 datasets, 8 domaines sourcés |
| **CI/CD** | 80% | 🟢 6 jobs GitHub Actions |
| **Veille concurrentielle** | 40% | 🟡 Pas automatisée, pas de benchmark public |

**Score global estimé : ~65%** — architecture excellente, exécution en cours, gaps critiques sur données, intégration et déploiement.

---

## 7. Recommandations priorisées

### P0 — Bloquants (à traiter immédiatement)

1. **Sauvegardes DB** : pgBackRest + WAL archiving → S3/minio
2. **Index sur 110 FK** : migration Alembic dédiée
3. **SDK GSIE** : au moins Python (pour QGISIA) + Kotlin (pour GeoSylva)
4. **Implémenter Recommendation + Validation** : moteurs qui produisent la valeur visible
5. **Ingestion autécologie Rameau** : débloque Reasoning/Diagnostic

### P1 — Élevés (prochaines semaines)

6. **Ingestion mass GBIF/TAXREF** : viser 1000+ essences dans Knowledge Engine
7. **Migration vers SQL/PGQ** (PostgreSQL 19 stable) : planifier le remplacement d'Apache AGE
8. **Intégration GeoSylva ↔ GSIE** : placettes → diagnostic + recommandation
9. **Simulation Engine** : modèles de croissance IGN → projection 20-50 ans
10. **Golden Bench** : 50 cas "or" validés par forestier référent

### P2 — Moyens (prochains mois)

11. **Déploiement cloud** : Kubernetes + managed PostgreSQL
12. **Ontologie RDF/OWL export** : interopérabilité scientifique (Darwin Core, ENVO)
13. **LiDAR HD dans Forest Dynamics** : ITD (Individual Tree Detection)
14. **Earth-2 pour Hub UE5.8** : intégration NVIDIA Earth-2
15. **Veille automatisée** : Forge ingère arXiv/HAL/OpenAlex en continu
16. **Open-source Constitution + Architecture** : construire la communauté

---

## 8. Conclusion

**GSIE est architecturalement supérieur à la concurrence** sur 3 dimensions : gouvernance constitutionnelle, chaîne de raisonnement déterministe modulaire, et multi-domaine convergent. L'architecture est alignée avec l'état de l'art 2025-2026 (MoBayes, SymptomWise, MedAgent-Pro).

**GSIE est opérationnellement en retard** sur 3 dimensions : volume de données (25 vs 67k espèces), intégration apps↔moteurs (0%), et déploiement (Docker local sans sauvegarde).

**La priorité absolue** n'est pas d'ajouter des moteurs ou des fonctionnalités — c'est de **connecter ce qui existe** : SDK → intégration GeoSylva/QGISIA → valeur utilisateur → feedback loop → amélioration.
