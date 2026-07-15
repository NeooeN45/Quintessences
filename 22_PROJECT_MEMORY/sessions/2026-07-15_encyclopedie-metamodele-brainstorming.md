# Session 2026-07-15 — Encyclopédie et métamodèle environnemental

## Métadonnées

| Champ | Valeur |
|---|---|
| **Date** | 2026-07-15 |
| **Type** | Brainstorming, audit d’architecture et orchestration multi-agents |
| **Statut** | Ressource de réflexion non normative |
| **Phase projet** | Phase 4 — Implémentation |
| **Directive liée** | GSIE-DIR-0008 — Encyclopédie de l’Écosystème |
| **Décisions liées** | DEC-000012, DEC-000019, DEC-000020 ; DEC-000022 en cours de rédaction par un autre agent |
| **Documents en cours externes à cette session** | `03_DECISIONS/DEC-000022.md`, `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` |

> Cette archive conserve le cheminement intellectuel de la session. Elle ne valide aucune proposition et ne remplace ni une RFC, ni une décision, ni un document d’architecture adopté.

## 1. Intention du Fondateur

Construire non pas une simple base de données, mais une mémoire scientifique du fonctionnement des écosystèmes, capable de relier :

- flore, faune, champignons et micro-organismes ;
- sols, géologie, climat et hydrologie ;
- observations de terrain, télédétection et séries temporelles ;
- interactions écologiques et réseaux trophiques ;
- gestion forestière et activités humaines ;
- maladies, ravageurs et perturbations ;
- services écosystémiques ;
- publications et connaissances expertes ;
- modèles scientifiques et modèles IA ;
- corrélations, règles, inférences et simulations ;
- décisions, interventions et conséquences observées ;
- jumeaux numériques territoriaux alimentant le Centre de Commandement Unreal.

Questions cibles : pourquoi une essence pousse à un endroit, quels risques futurs existent, quelle essence est adaptée, quels effets aura le changement climatique, quel sera l’état d’une parcelle dans trente ans, quels services sont rendus, quelles espèces protégées seront affectées et quelle intervention est la moins perturbatrice.

## 2. Choix de cadrage exprimés

- Territoire initial : France métropolitaine et Corse, avec architecture extensible.
- Données : ouvertes, sous accord et privées, avec cloisonnement.
- Première tranche verticale : Fiche Essence 360°.
- Modifications locales Alembic/PostGIS/seeds : à auditer avant intégration.
- Les travaux non committés d’autres agents doivent être préservés.
- La documentation et les décisions doivent être stabilisées avant le démarrage du code correspondant.

## 3. Principe conceptuel retenu pour étude

Formulation corrigée de « tout devient une entité » :

> Tout objet possédant une identité, une histoire ou des relations propres peut devenir une entité. Toute information concernant cet objet devient une observation, une assertion, un événement, un processus, une mesure ou une propriété contextualisée.

Noyau conceptuel proposé pour rationalisation :

- Entity et EntityIdentity ;
- Concept et Instance ;
- Place ou SpatialFeature ;
- Agent ;
- Source, Dataset et Asset ;
- Observation et MeasurementResult ;
- Assertion et RelationAssertion ;
- Event et Process ;
- Activity, Method, Protocol, Instrument et Sensor ;
- EvidenceAssessment et QualityAssessment ;
- Version et ProvenanceRecord ;
- Model, ModelRun et Scenario ;
- Decision et Action/Intervention.

Les profils spécialisés comme `TreeMeasurement`, `FireFront`, `Martelage`, `CameraTrap` ou `STACItem` ne sont pas nécessairement des fondations universelles.

## 4. Séparations jugées indispensables

### 4.1 Nature des informations

- actifs de données physiques ou numériques ;
- observations et mesures ;
- entités et référentiels ;
- assertions scientifiques ;
- événements et processus ;
- produits dérivés, prédictions et simulations.

### 4.2 Graphes logiques

- graphe ontologique ;
- graphe des assertions scientifiques ;
- graphe des observations et états territoriaux ;
- graphe de provenance et de lignage.

### 4.3 Temporalité

- temps de validité dans le monde ;
- temps d’enregistrement dans GSIE ;
- saison, période, évolution et tendances.

### 4.4 Qualification scientifique

Ne pas confondre :

- niveau de preuve ;
- qualité des données ;
- probabilité du phénomène ;
- confiance calibrée du modèle ;
- incertitude ;
- applicabilité au contexte ;
- concordance des sources ;
- fraîcheur.

Aucun score global unique ne doit masquer ces dimensions sans méthode et usage explicités.

### 4.5 Corrélation et causalité

Distinguer :

- association statistique ;
- corrélation spatiale ou temporelle ;
- causalité démontrée ;
- mécanisme plausible ;
- règle experte ;
- relation ontologique ;
- observation ;
- prédiction ;
- hypothèse.

## 5. Architecture technique provisoire étudiée

- stockage objet immuable pour données brutes et volumineuses ;
- PostgreSQL/PostGIS comme vérité transactionnelle canonique ;
- Apache AGE, recherche, embeddings et RDF comme projections reconstructibles ;
- formats envisagés selon le type : COG, GeoParquet, Parquet, NetCDF-CF, Zarr, COPC/LAZ ;
- standards à évaluer : PROV-O, DCAT/GeoDCAT-AP, ISO 19115, STAC, OGC O&M/SensorThings, Darwin Core, SKOS/OWL, GeoSPARQL, UCUM/QUDT et OGC API.

Aucun choix supplémentaire de moteur de stockage n’est considéré adopté par cette archive.

## 6. Résultat du brainstorming agent v5

L’agent a proposé un « Environmental Knowledge Operating System » d’environ 110 classes, organisé en huit couches : fondation, connaissances, acquisition, analyse, simulation, décision, applications, Event Bus/Scheduler, avec six registres transverses : Connector, Model, Capability, Ontology, Workflow et Plugin.

Idées jugées intéressantes :

- provenance et data lineage ;
- cycle de vie des connaissances ;
- qualité contextualisée ;
- couche sémantique ;
- OGC et STAC ;
- inventaires forestiers ;
- modèles et simulations ;
- catalogue de connecteurs et de modèles ;
- mécanisme événementiel ;
- extensibilité progressive.

## 7. Réserves majeures formulées sur la v5

1. Les 110 classes mélangent métamodèle, profils métier, standards externes, stockage et infrastructure.
2. La Registry Architecture est utile, mais ne constitue pas encore une différenciation démontrée.
3. `LISTEN/NOTIFY` seul n’est pas un bus durable : un transactional outbox est requis.
4. `DataQuality` ne doit pas être une série de scores universels avec moyenne globale canonique.
5. Le lignage doit rester aligné sur Entity/Activity/Agent de PROV.
6. Audit, historique scientifique, provenance, événements métier et logs techniques doivent rester distincts.
7. Les tableaux de clés étrangères doivent être remplacés par des entités d’association.
8. L’EAV généralisé est rejeté ; privilégier colonnes typées, Observation/Result et JSONB limité.
9. STAC et OGC sont des standards/projections, pas des classes fondamentales du domaine.
10. Une ligne PostgreSQL par tuile raster est probablement inadaptée à l’échelle nationale ; privilégier COG, overviews, stockage objet et STAC.
11. DuckDB est un moteur analytique, pas une source de vérité.
12. PostgreSQL 17 n’est pas acté ; l’environnement actuel est PostgreSQL 16.
13. TimescaleDB, Elasticsearch, Jena et Neo4j doivent être conditionnés à des besoins mesurés.
14. L’auto-apprentissage E/F sans validation humaine est rejeté : les résultats deviennent des connaissances candidates en quarantaine.
15. Le Feature Store complet est différé jusqu’à l’existence de consommateurs réels communs.
16. Les plugins dynamiques exigeraient allowlist, signature, permissions, isolation, compatibilité et audit.
17. La future RFC doit couvrir les impacts sur les livrables 205, 304, 309 et 310, ainsi que les décisions 012, 019 et 020.
18. Les propositions issues du brainstorming ne doivent pas être nommées « décisions validées » avant arbitrage du Fondateur.

## 8. Rationalisation v6 demandée à l’agent

Une passe de convergence a été validée par le Fondateur et transmise à l’agent. Elle doit :

- séparer métamodèle universel, profils métier, projections, infrastructure et vision long terme ;
- limiter le noyau universel à 20–30 types ;
- produire un registre des décisions candidates ;
- qualifier chaque élément comme proposé, retenu pour RFC, différé ou rejeté ;
- corriger Event Bus, qualité, provenance, temporalité, relations et apprentissage ;
- produire des vagues avec critères de sortie mesurables ;
- préparer le plan d’une RFC transverse sans encore rédiger ni adopter la RFC.

## 9. Tranche verticale retenue

La Fiche Essence 360° doit agréger sans dupliquer la vérité :

- identité et taxonomie ;
- morphologie et traits fonctionnels ;
- distribution ;
- habitats ;
- sols et besoins stationnels ;
- enveloppe climatique ;
- dendrométrie et croissance ;
- régénération ;
- interactions, mycorhizes, pathologies et ravageurs ;
- sensibilité aux perturbations ;
- biodiversité associée ;
- services écosystémiques ;
- sylviculture ;
- conservation et réglementation ;
- scénarios climatiques ;
- preuves, conflits et incertitudes.

Essences pilotes proposées : chêne sessile, hêtre, pin maritime, douglas et sapin pectiné.

## 10. Orchestration multi-agents prévue

- GLM 5.2 : convergence du métamodèle et critique architecturale.
- KIMI 2.7 : standards, référentiels et recherche documentaire massive.
- SWE 1.7 beta : audit puis implémentation guidée, migrations et tests.
- Agent principal : arbitrage, gouvernance, découpage, revue des réponses et gate final.

Aucun agent de code ne doit intervenir avant stabilisation du métamodèle, des décisions et des spécifications.

## 11. Prochaines étapes

1. Recevoir la v6 rationalisée de l’agent.
2. Comparer les propositions aux résultats KIMI et à l’audit SWE.
3. Arbitrer chaque décision candidate avec le Fondateur.
4. Préparer la RFC transverse et la décision d’adoption.
5. Stabiliser l’architecture Phase 4 et les spécifications.
6. Auditer la migration locale existante.
7. Préparer le plan TDD de la Vague 1.
8. Commencer le code seulement après le gate documentaire.

## 12. Fichiers modifiés par cette opération d’archivage

- création de cette archive ;
- création ou mise à jour de `22_PROJECT_MEMORY/sessions/INDEX.md`.

Aucun document d’architecture, décision, code, migration, mémoire racine, roadmap ou changelog n’a été modifié par cette opération.

## 13. Archivage de la proposition v5

Le 2026-07-15, après convergence v6 puis v6.1, le Fondateur a autorisé
l’archivage intégral des deux documents v5 produits pendant le
brainstorming, ainsi que le retrait des affirmations v5 non adoptées de
la mémoire courante du projet.

### Fichiers archivés intégralement

Les deux fichiers v5 ont été copiés byte pour byte (sha256 vérifié)
dans `22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/` avec un en-tête explicite
indiquant leur statut non normatif :

- `22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/ECOSYSTEM_METAMODEL_V5_PROPOSITION_NON_ADOPTEE.md`
  — archive du livrable 213 v5 (`GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md`,
  1142 lignes originales).
- `22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/DEC_000022_V5_PROPOSITION_NON_ADOPTEE.md`
  — archive de la proposition de décision
  (`03_DECISIONS/DEC-000022.md`, 169 lignes originales).

### Statut réel

- **DEC-000022 n’a pas été adopté.** Le fichier portait à tort le
  statut `Validated` ; il s’agissait d’une erreur de gouvernance
  historique. Le numéro `DEC-000022` reste disponible pour une future
  décision après RFC.
- **Le livrable 213 v5 n’est pas l’architecture courante.** Le fichier
  `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` a été retiré de l’espace
  actif. Le futur livrable 213 v6.1 sera créé dans une mission ultérieure
  après la RFC.
- **La convergence v6.1 devient la base de préparation de RFC-0011**,
  sans être elle-même adoptée à ce stade. Aucune architecture issue du
  brainstorming n’est adoptée.
- Les mentions « 25 décisions validées », « PostgreSQL 17 adopté »,
  « auto-apprentissage E-F sans humain » et « Registry Architecture
  actée » ont été retirées de `PROJECT_MEMORY.md` et `CHANGELOG.md` en
  tant qu’affirmations non adoptées.
- RFC-0011 n’existe pas encore et n’a pas été créée par cette opération.
- Aucun commit, aucun push, aucune modification de code, migration,
  Docker, pyproject ou document Locked.
