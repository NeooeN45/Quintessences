# RFC-0035 — GSIE Server Meshing : jumeau numérique environnemental distribué continu

| Champ | Valeur |
|---|---|
| **ID** | RFC-0035 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation (anticipation Phase 5) |
| **Auteur** | Camille Perraudeau (Fondateur) — proposition instruite par Devin (GLM 5.2 High) |
| **Date d'ouverture** | 2026-08-03 |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-003 (connaissance avant code), GSIE-CON-007 (modularité), GSIE-CON-010 (évolution sans perte d'historique) |
| **Constitutions liées** | Technique (T-1 responsabilité unique, T-2 couplage faible, T-8 offline-first, T-10 traçabilité) |
| **RFC de référence** | RFC-0003 (GSIE-Net), RFC-0011 (métamodèle v6.2), RFC-0015 (Environmental Model Fabric) |
| **Décisions liées** | DEC-000010 (UE 5.8 + Cesium), DEC-000013 (Centre de Commandement), DEC-000017 (Phase 4) |
| **Directive liée** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0012 (à ouvrir — voir Vague 1) |
| **Impact** | `GSIE/ARCHITECTURE/`, `05_SPECIFICATIONS/HUB/`, `ROADMAP.md`, `PROJECT_MEMORY.md`, `CHANGELOG.md`, futures apps clientes, futures infrastructures de déploiement |

---

## 1. Objet

Proposer et documenter la vision, les principes et le cadrage d'un
**GSIE Server Meshing** : évolution du Centre de Commandement GSIE et
de l'API GSIE vers une architecture distribuée continue dans laquelle
plusieurs serveurs coopèrent pour héberger un **jumeau numérique
environnemental persistant**, en concentrant dynamiquement les
ressources de calcul sur les zones qui requièrent une précision ou une
réactivité supérieure.

Cette RFC capture la vision fondatrice pour qu'elle oriente les travaux
d'architecture et d'implémentation à venir. Elle ne produit pas de code.
Elle s'inspire des approches de **Server Meshing** popularisées par les
mondes persistants à grande échelle (Star Citizen, MMO modernes),
**adaptées** au contexte d'un jumeau numérique environnemental
scientifique, offline-first et traçable.

---

## 2. Motivation

### 2.1 Constat

Le Centre de Commandement GSIE actuel (livrable 211, HUB-001) est un
**client de visualisation monolithique** : une seule scène Unreal Engine
5.8 consomme un seul flux WebSocket/JSON depuis une seule instance
d'API GSIE. Ce modèle est adapté à un périmètre régional et à un
opérateur unique, mais il présente trois limites structurelles :

1. **Pas de continuité spatiale au-delà d'une région.** Le Hub charge
   un secteur (Landiras pour Ignis, futur massif pour GeoSylva). Il n'y
   a pas de mécanisme pour traverser une frontière de serveur sans
   coupure visible pour l'opérateur.
2. **Pas de concentration dynamique de ressources.** Si un incendie
   éclate en Corse pendant qu'une mission d'inventaire se déroule en
   Aquitaine, le système ne peut pas automatiquement allouer plus de
   capacité de calcul et de rendu à la Corse et moins à l'Aquitaine.
3. **Pas de persistance hors Unreal.** Le Hub est un client léger —
   c'est sain — mais il n'existe pas encore de couche de persistance
   distribuée qui survive à l'arrêt d'un serveur, qui réplique l'état
   entre régions, et qui permette à un autre nœud de prendre le relais.

### 2.2 Vision

Le **GSIE Server Meshing** est l'évolution qui répond à ces trois
limites. Il transforme le jumeau numérique environnemental en un
**monde continu, persistant et distribué** :

- **Continu** : l'opérateur peut naviguer sans coupure d'une région à
  l'autre, comme sur un globe unique, alors que les serveurs sous-jacents
  changent.
- **Persistant** : l'état du jumeau (entités, simulations, observations)
  survive à l'arrêt ou à la panne d'un serveur. Tout état critique est
  répliqué hors Unreal Engine.
- **Distribué** : plusieurs serveurs coopèrent, chacun responsable d'une
  portion d'espace et/ou d'un domaine fonctionnel, en concentrant
  dynamiquement les ressources sur les zones actives (incendie, crise,
  mission terrain).

### 2.3 Principe fondamental — Unreal Engine n'est pas la source de vérité

Ce principe est déjà acté par la Constitution (CON-003, CON-007) et par
l'architecture existante (livrable 211 §0.2, ADR-001 livrable 208). Le
Server Meshing le **renforce** et le rend opérationnel :

> **Toute donnée critique du jumeau (entités, état, historique,
> simulations en cours) persiste dans une couche de persistance
> externe, indépendante d'Unreal Engine.** Unreal Engine est un
> **client de rendu** parmi d'autres. Il peut planter, être fermé,
> redémarrer — l'état du jumeau est préservé.

La couche de persistance est assurée par PostgreSQL/PostGIS (source de
vérité métier), le métamodèle v6.2 (RFC-0011, bitemporel), et un
**graphe d'autorité** qui détermine, pour chaque entité et chaque
zone, quel serveur est actuellement responsable.

### 2.4 Inspiration Star Citizen — ce que nous gardons et ce que nous adaptons

| Concept Star Citizen | Adaptation GSIE |
|---|---|
| Server Object Authority — chaque serveur possède sa zone | **Autorité hybride zone + type** (zone spatiale primaire, spécialisation par domaine secondaire) |
| Replication Graph — propager seulement le visible | **Réplication par pertinence** : un serveur ne reçoit que les entités visibles ou interagissantes depuis sa zone |
| Server Meshing v2 — handoff d'entités à la frontière | **Transfert d'autorité** : migration d'une entité d'un serveur à un autre lors du franchissement de frontière |
| Spatial partitioning — grille adaptative | **Partitionnement spatial dynamique** : les zones se redécoupent selon la charge (incendie → sous-zone haute précision) |
| Persistence layer — état hors moteur | **Déjà acté** : PostgreSQL + métamodèle bitemporel = source de vérité |
| Entity streaming — chargement/déchargement par distance | **Streaming par pertinence** : le Hub ne charge que ce qui est dans le frustum + marge |

Ce que nous **n'empruntons pas** : le modèle d'authentité par joueur
(GSIE est orienté opérateur, pas joueur), le modèle de physique
temps réel distribué (GSIE fait de la simulation scientifique, pas de
la physique de jeu), et le modèle de monétisation.

---

## 3. Principes fondateurs du GSIE Server Meshing

### 3.1 Continuité spatiale sans coupure (P-MESH-01)

L'opérateur navigue sur un globe apparemment unique. Les frontières
entre serveurs sont invisibles. Le transfert d'autorité d'une entité
d'un serveur à un autre se fait sans interruption visible pour le
client de rendu.

**Conséquence architecturale** : le Hub maintient une scène unique et
reçoit des flux de plusieurs serveurs simultanément. Le graphe
d'autorité est transparent pour l'opérateur.

### 3.2 Persistance externe obligatoire (P-MESH-02)

Aucune donnée critique du jumeau ne vit uniquement en mémoire d'un
serveur Unreal ou d'un worker. Tout état est persisté dans la couche
de persistance externe (PostgreSQL/PostGIS + métamodèle v6.2) avant
d'être considéré comme valide.

**Conséquence architecturale** : un serveur peut être tué à tout
moment. Au redémarrage, il reconstitue son état depuis la couche de
persistance. Le métamodèle bitemporel (RFC-0011) garantit que
l'historique est préservé.

### 3.3 Autorité hybride zone + type (P-MESH-03)

L'autorité sur une entité du jumeau est déterminée par deux axes :

- **Zone spatiale** : chaque serveur possède une zone géographique
  (région, massif, secteur). Une entité spatiale (arbre, front de feu,
  observation) appartient au serveur de sa zone.
- **Type d'entité** : certains types d'entités sont gérés par des
  serveurs spécialisés (un serveur Simulation pour les projections
  long terme, un serveur Learning pour l'amélioration des modèles),
  indépendamment de la zone.

**Conséquence architecturale** : le graphe d'autorité est un graphe
bidimensionnel. Une entité peut être sous l'autorité spatiale d'un
serveur régional ET sous l'autorité fonctionnelle d'un serveur
spécialisé. Les conflits sont résolus par priorité documentée.

### 3.4 Concentration dynamique des ressources (P-MESH-04)

Le mesh adapte sa topologie à la charge. Une zone qui devient active
(incendie déclenché, mission terrain en cours, alerte) reçoit
dynamiquement plus de ressources de calcul et de rendu. Une zone
inactive libère ses ressources.

**Conséquence architecturale** : le partitionnement spatial n'est pas
statique. Un orchestrateur de mesh décide du découpage et de
l'allocation des serveurs en fonction de métriques temps réel (charge,
nombre d'opérateurs connectés, activité de simulation, alertes).

### 3.5 Offline-first préservé (P-MESH-05)

Le Server Meshing ne contredit pas le principe offline-first (T-8,
RFC-0003). Un nœud terminal (téléphone, tablette terrain, GCS-Lite)
continue de fonctionner hors-ligne. Le mesh est une évolution de
l'**infrastructure serveur**, pas des nœuds terminaux.

**Conséquence architecturale** : le mesh doit tolérer qu'un nœud
terminal soit déconnecté. La synchronisation se fait au retour de
connectivité, comme aujourd'hui (RFC-0003 §4, modèle Git).

### 3.6 Traçabilité complète (P-MESH-06)

Toute décision du mesh — transfert d'autorité, redécoupage spatial,
allocation de ressources, création/destruction de serveur — est
journalisée et traçable (CON-005, CON-010). L'historique du mesh
fait partie du jumeau numérique.

**Conséquence architecturale** : l'orchestrateur de mesh produit un
journal d'audit immuable. Chaque transfert d'autorité porte un
identifiant traçable.

### 3.7 Modularité et interchangeabilité (P-MESH-07)

Le Server Meshing est construit sur des **interfaces contractuelles**
(T-2, CON-007). Le client de rendu (UE5.8 aujourd'hui, UE6 demain,
CesiumJS web à terme) est interchangeable. Les serveurs de zone sont
interchangeables. La couche de persistance est interchangeable.
Aucun composant n'est un point de blocage unique.

**Conséquence architecturale** : le mesh est défini par ses interfaces,
pas par ses implémentations. Une RFC est requise pour changer une
interface de mesh.

### 3.8 Subordination à la connaissance (P-MESH-08)

Le Server Meshing est un **moyen**, pas une fin. La connaissance est
le véritable produit (CON-003). Aucune optimisation de mesh ne peut
dégrader la traçabilité, l'explicabilité ou la qualité scientifique
des sorties. En cas de conflit, la connaissance prime.

**Conséquence architecturale** : le mesh ne peut pas sacrifier la
journalisation pour la performance. Le mesh ne peut pas agréger des
données au point de perdre la provenance.

---

## 4. Architecture conceptuelle (cadrage — le détail est dans l'architecture cible)

```
                    ┌─────────────────────────────────────────┐
                    │       ORCHESTRATEUR DE MESH              │
                    │  Découpage spatial, allocation,          │
                    │  transferts d'autorité, supervision      │
                    └──────────────┬──────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────▼─────────┐  ┌───────▼────────┐  ┌───────▼────────┐
     │  SERVEUR DE ZONE  │  │  SERVEUR DE    │  │  SERVEUR DE    │
     │  Aquitaine        │  │  ZONE Corse    │  │  ZONE PACA     │
     │  (forêt, feu,     │  │  (feu priorité)│  │  (faune, eau)  │
     │   faune, eau)     │  │                │  │                │
     └────────┬──────────┘  └───────┬────────┘  └───────┬────────┘
              │                     │                    │
              └─────────────────────┼────────────────────┘
                                    │
                    ┌───────────────▼────────────────────┐
                    │     COUCHE DE PERSISTANCE           │
                    │  PostgreSQL/PostGIS (source vérité) │
                    │  Métamodèle v6.2 (bitemporel)       │
                    │  Graphe d'autorité (qui possède quoi)│
                    └───────────────┬────────────────────┘
                                    │
                    ┌───────────────▼────────────────────┐
                    │     CLIENTS DE RENDU                │
                    │  Hub UE5.8 (lourd, salle commandement)│
                    │  CesiumJS web (léger, distant)       │
                    │  Apps mobiles (terrain, offline)     │
                    └─────────────────────────────────────┘
```

### 4.1 Serveurs spécialisés (transverses aux zones)

En plus des serveurs de zone, des **serveurs spécialisés** gèrent les
entités non spatiales ou transverses :

| Serveur spécialisé | Responsabilité | Exemples d'entités |
|---|---|---|
| Serveur Simulation | Projections long terme, scénarios | Scénarios sylvicoles, propagation feu prédite |
| Serveur Learning | Amélioration continue des modèles | Modèles entraînés, retours terrain |
| Serveur Knowledge | Graphe de connaissances central | Assertions, sources, niveaux de preuve |
| Serveur Drones | Orchestration multi-drones | Flotte, missions, télémétrie |

### 4.2 Graphe d'autorité

Le **graphe d'autorité** est la structure qui répond, pour toute
entité du jumeau et tout instant t, à la question : *quel serveur est
actuellement responsable de cette entité ?*

Il est persisté dans la couche de persistance (PostgreSQL) et répliqué
aux serveurs du mesh. Il est consultable par les clients de rendu pour
savoir quel flux écouter.

---

## 5. Options envisagées

### 5.1 Stratégie d'autorité

| Option | Description | Avantages | Risques |
|---|---|---|---|
| **A** | Autorité par zone spatiale uniquement | Simple à raisonner | Sous-optimal pour entités transverses (drones, simulations) |
| **B** | Autorité par type d'entité uniquement | Spécialisation efficace | Pas de continuité spatiale |
| **C** | **Autorité hybride zone + type** (recommandée) | Flexible, cible long terme | Complexité de résolution des conflits |

**Recommandation** : Option C, conformément à la décision du Fondateur.
L'autorité spatiale est primaire, l'autorité par type est secondaire.
Les conflits sont résolus par priorité documentée (voir architecture
cible).

### 5.2 Périmètre du prototype

| Option | Description | Avantages | Risques |
|---|---|---|---|
| **A** | Mono-région (Landiras) | Valide le pattern, risque minimal | Ne valide pas le handoff inter-serveur |
| **B** | Multi-régions France | Valide le handoff | Effort moyen |
| **C** | France entière | Valide le partitionnement adaptatif | Effort élevé |

**Recommandation** : Option A pour le prototype v0 (décision Fondateur),
puis extension à 2 régions pour valider le handoff (prototype v1).

### 5.3 Dépendance UE6

| Option | Description | Avantages | Risques |
|---|---|---|---|
| **A** | UE5.8 uniquement | Pas d'incertitude | Migration future coûteuse |
| **B** | **Compatibilité UE6 anticipée** (recommandée) | Interfaces abstraites, migration facilitée | Légère surcharge d'abstraction |
| **C** | UE6 comme cible explicite | Bénéficie des primitives UE6 si elles existent | Dépendance à un produit non publié |

**Recommandation** : Option B. Le mesh est défini par des interfaces
abstraites (transport, réplication, autorité) qui ne dépendent pas
d'Unreal Engine. UE5.8 est l'implémentation actuelle du client de
rendu. UE6 sera une implémentation future. Voir stratégie de migration
UE6.

---

## 6. Impact et dépendances

### 6.1 Documents impactés

| Document | Impact | Nature |
|---|---|---|
| `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211) | Évolution | Ajout section "Mesh client" — le Hub devient un client du mesh |
| `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` (livrable 201) | Évolution | Ajout couche "Mesh" dans l'architecture en couches |
| `05_SPECIFICATIONS/HUB/HUB_001_SPECIFICATION.md` | Évolution | Nouvelles exigences HUB-F-27+ (mesh, multi-serveurs, handoff) |
| `05_SPECIFICATIONS/HUB/HUB_002_INTERFACE_CONTRACT.md` | Évolution | Contrat étendu : couches dynamiques par zone d'autorité |
| `ROADMAP.md` | Évolution | Nouvelle section "GSIE Server Meshing" |
| `PROJECT_MEMORY.md` | Évolution | Directive + décision + RFC tracées |

### 6.2 Nouveaux documents à produire

| Document | Chemin | Vague |
|---|---|---|
| Architecture cible Server Meshing | `GSIE/ARCHITECTURE/SERVER_MESHING_TARGET.md` | 2 |
| Architecture prototype v0 | `GSIE/ARCHITECTURE/SERVER_MESHING_PROTOTYPE_V0.md` | 2 |
| Roadmap dédiée Server Meshing | `GSIE/ARCHITECTURE/SERVER_MESHING_ROADMAP.md` | 2 |
| Registre ADR Server Meshing | `GSIE/ARCHITECTURE/ADR-01x-*.md` | 2 |
| Registre de risques | `GSIE/ARCHITECTURE/SERVER_MESHING_RISKS.md` | 2 |
| Diagrammes | `GSIE/ARCHITECTURE/SERVER_MESHING_DIAGRAMS.md` | 2 |
| Backlog phasé | `GSIE/ARCHITECTURE/SERVER_MESHING_BACKLOG.md` | 3 |
| Critères d'acceptation | `GSIE/ARCHITECTURE/SERVER_MESHING_ACCEPTANCE.md` | 3 |
| Stratégie de test | `GSIE/ARCHITECTURE/SERVER_MESHING_TEST_STRATEGY.md` | 3 |
| Stratégie migration UE6 | `GSIE/ARCHITECTURE/SERVER_MESHING_UE6_MIGRATION.md` | 3 |
| Features expérimentales | `GSIE/ARCHITECTURE/SERVER_MESHING_EXPERIMENTS.md` | 3 |
| Estimation complexité | `GSIE/ARCHITECTURE/SERVER_MESHING_COMPLEXITY.md` | 3 |

### 6.3 Dépendances techniques

| Dépendance | Statut | Note |
|---|---|---|
| API GSIE (WebSocket + Redis Pub/Sub) | Existant | Base du mesh — à étendre |
| Métamodèle v6.2 (RFC-0011) | Adopté | Bitemporalité = clé pour réplication |
| GSIE-Net (RFC-0003) | Proposé | Couche réseau distribuée — à étendre au mesh de serveurs |
| PostgreSQL/PostGIS | En production | Source de vérité — à étendre (réplication logique, partitionnement) |
| Cesium for Unreal | Configuré | Client de rendu — à étendre (multi-serveurs, streaming dynamique) |
| Redis Pub/Sub | Configuré | Bus de messages — à étendre (cross-région) |

---

## 7. Ce que cette RFC ne fait PAS

- Elle n'implémente aucun code.
- Elle ne définit pas le détail des protocoles de mesh (transfert
  d'autorité, réplication, service discovery) — c'est le rôle de
  l'architecture cible (Vague 2).
- Elle ne choisit pas de technologie de service mesh (Consul, etcd,
  custom) — c'est un ADR à produire.
- Elle ne contredit aucun article constitutionnel.
- Elle ne modifie pas directement les documents Locked — elle ouvre
  une direction qui pourra, le cas échéant, justifier des RFC
  ultérieures pour faire évoluer des Locked.

---

## 8. Risques identifiés (registre détaillé dans Vague 2)

| Risque | Sévérité | Mitigation |
|---|---|---|
| Complexité du handoff d'autorité | Élevée | Prototype mono-région d'abord, extension progressive |
| Conflits de réplication multi-masters | Élevée | Bitemporalité + résolution par domaine documentée |
| Partition réseau (CAP theorem) | Moyenne | Offline-first préservé — mode dégradé documenté |
| Sur-ingénierie avant besoin réel | Moyenne | Phasage strict — pas de mesh avant qu'une seule région ne soit saturée |
| Dépendance UE6 non livrée | Faible | Compatibilité anticipée, pas de dépendance hard |
| Coût d'infrastructure | Moyen | Concentration dynamique = optimisation des coûts |

---

## 9. Critères d'acceptation de cette RFC

La RFC-0035 est considérée **complète** quand :

- [x] La vision et les 8 principes sont énoncés.
- [x] Les options sont documentées avec recommandation.
- [x] L'impact sur les documents existants est listé.
- [x] Les nouveaux documents à produire sont listés.
- [x] Les risques sont identifiés.
- [ ] La directive fondatrice (GSIE-DIR-0012) est rédigée.
- [ ] La décision d'ouverture (DEC-000053) est rédigée.

---

## 10. Statut de validation

| Étape | Statut |
|---|---|
| Proposé par le Fondateur | Oui — 2026-08-03 |
| Débat ouvert | En attente |
| Adopté / Rejeté | En attente |
| Décision produite | En attente (DEC-000053) |

---

## 11. Note de gouvernance

Cette RFC est ouverte en **Phase 4** pour cadrer une évolution
structurante qui s'étendra sur plusieurs phases. Elle ne sera **activée**
(traduite en travaux d'architecture et d'implémentation) qu'après
validation du Fondateur et production de la directive fondatrice
(GSIE-DIR-0012) et de la décision d'ouverture (DEC-000053).

Le Server Meshing est un **chantier long** qui ne remplace pas les
priorités courantes de la Phase 4 (14 moteurs, API GSIE, Hub UE5.8,
GeoSylva, Ignis). Il s'ajoute comme une **direction architecturale
long terme** qui oriente les choix d'implémentation dès maintenant
(interfaces abstraites, persistance externe, traçabilité) sans
requérir de livrer un mesh opérationnel immédiatement.

> « Le jumeau numérique environnemental doit être aussi continu et
> persistant que le monde qu'il représente. Aucune frontière de
> serveur ne doit être visible pour l'opérateur. Aucune panne ne doit
> perdre la connaissance. »
