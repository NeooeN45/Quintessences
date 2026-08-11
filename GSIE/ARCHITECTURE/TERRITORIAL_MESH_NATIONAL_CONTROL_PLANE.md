# National Control Plane — Architecture du plan de contrôle territorial national

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_NATIONAL_CONTROL_PLANE |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 (GSIE Territorial Mesh) |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **Dépend de** | ADR-011 (PostgreSQL/PostGIS source de vérité), ADR-013 (Redis Pub/Sub), ADR-017 (mTLS) |

---

## 1. Rôle

Le **National Control Plane** (NCP) est le sommet de la hiérarchie du
GSIE Territorial Mesh (voir RFC-0036 §1, structure
`France → Région → Département → Territoire opérationnel → Cellule
spatiale → Sous-cellule de simulation`). Le NCP est un **plan de
contrôle**, non un plan d'exécution : il ne réalise **aucun calcul
métier**, ne porte **aucune simulation**, et n'héberge **aucune donnée
opérationnelle chaude**.

Sa responsabilité est de garantir la cohérence, la gouvernance et la
supervision de l'ensemble du mesh territorial français, en fédérant
les Regional Coordination Hubs (RCH) sans jamais se substituer à eux
dans l'exécution.

Ce principe reprend directement la logique de séparation
plan-de-contrôle/plan-d'exécution déjà actée dans RFC-0035 §2.3 :
« Unreal Engine n'est pas la source de vérité ». Ici : « le NCP n'est
pas un moteur de calcul ».

---

## 2. Responsabilités

### 2.1 Carte territoriale maîtresse

Le NCP maintient la **carte territoriale maîtresse** : la
représentation de référence de la hiérarchie complète, du national à
la sous-cellule de simulation.

```
France (NCP)
└── Région (RCH) — ex: Nouvelle-Aquitaine
    └── Département (DOD) — ex: Charente (16)
        └── Territoire opérationnel — ex: massif, DFCI, bassin versant
            └── Cellule spatiale (Server Meshing, RFC-0035)
                └── Sous-cellule de simulation
```

Cette carte est la **source de vérité de la topologie**, distincte de
l'état opérationnel (froid/chaud/opérationnel/crise) qui est porté par
chaque niveau lui-même. Toute création, fusion ou suppression d'un
nœud territorial (nouvelle région, redécoupage départemental, création
d'un territoire opérationnel transfrontalier) transite par le NCP et
est tracée.

### 2.2 Politiques de gouvernance

Le NCP porte les **politiques de gouvernance** qui répondent à la
question : *qui peut activer quoi, à quel niveau ?*

| Action | Autorité minimale requise |
|---|---|
| Activation d'un RCH (froid→chaud) | Admin national (NCP) |
| Activation d'un DOD (froid→chaud) | Admin régional (RCH), validé par politique NCP |
| Activation d'une cellule spatiale | Admin départemental (DOD), dans les limites allouées par le RCH |
| Déclaration d'une Crise locale | Admin départemental (DOD), notification au RCH |
| Bascule en Crise multi-régionale | Admin national (NCP) |
| Modification de la carte territoriale | Admin national (NCP) exclusivement |

Ces politiques sont des données de gouvernance (schéma
`gsie_gouvernance`, §6), pas du code : elles sont modifiables sans
déploiement, sous contrôle RBAC (§7).

### 2.3 Fédération des Regional Coordination Hubs

Le NCP fédère l'ensemble des RCH actifs sur le territoire national. Il
maintient un **registre des RCH** (identité, périmètre régional, état
courant, capacité déclarée, dernière heartbeat) et arbitre les
situations qui dépassent le périmètre d'un seul RCH :

- coordination d'une crise inter-régionale (ex. feu de forêt à cheval
  sur deux régions) ;
- répartition de charge exceptionnelle entre RCH voisins ;
- cohérence de la carte territoriale entre régions limitrophes.

Le NCP **ne remplace jamais** un RCH dans ses responsabilités
opérationnelles régionales (voir `TERRITORIAL_MESH_REGIONAL_HUB.md`
§1) : il fédère, il n'exécute pas.

### 2.4 Supervision globale

Le NCP agrège la **métrologie**, l'**audit** et la **santé** de
l'ensemble du mesh :

- état de santé de chaque RCH (heartbeat, latence, charge agrégée) ;
- journal d'audit consolidé des changements de gouvernance et
  d'autorité territoriale ;
- tableau de bord national des états opérationnels
  (froid/chaud/opérationnel/crise) par région et par département.

Cette supervision est en **lecture agrégée** : le NCP consomme des
métriques exportées par les RCH, il ne les recalcule pas.

### 2.5 Registre des autorités

Le NCP tient le **registre des autorités** : pour chaque périmètre
territorial (région, département, territoire opérationnel, cellule),
qui détient l'autorité métier active à un instant donné. Ce registre
est la référence en cas de contestation ou de reprise après panne
(§8), et il est cohérent avec le graphe d'autorité de RFC-0035 §2.3 —
le NCP en porte la vue nationale consolidée, les RCH et DOD en portent
la vue opérationnelle locale.

---

## 3. Interfaces

Conformément à CON-007 (modularité obligatoire), le NCP expose des
interfaces abstraites, indépendantes de toute implémentation
(alignées ADR-015, interfaces abstraites UE6 lorsque pertinent pour le
Hub).

```
ITerritorialMap
  getHierarchy(scope?) -> TerritorialNode[]
  createNode(parentId, node) -> TerritorialNode
  updateNode(nodeId, patch) -> TerritorialNode
  deleteNode(nodeId) -> void
  getNodeHistory(nodeId) -> TerritorialChangeEvent[]

IGovernancePolicy
  getPolicy(action, scope) -> PolicyDecision
  evaluateActivation(request: ActivationRequest) -> PolicyDecision
  registerPolicy(policy: GovernancePolicy) -> void

IRegionalFederation
  registerRCH(rch: RCHDescriptor) -> void
  listRCH(filter?) -> RCHDescriptor[]
  getRCHState(rchId) -> RCHState
  arbitrateCrossRegional(request: CrossRegionalRequest) -> Decision

ISupervision
  getGlobalHealth() -> MeshHealthSnapshot
  getAuditLog(filter?) -> AuditEvent[]
  getOperationalStateMap() -> Map<TerritorialScope, OperationalState>

IAuthorityRegistry
  getAuthority(scope: TerritorialScope) -> AuthorityRecord
  transferAuthority(scope, from, to, reason, expectedEpoch) -> AuthorityRecord
  getAuthorityHistory(scope) -> AuthorityRecord[]
```

Toute modification d'une de ces interfaces est un changement de
contrat et requiert une RFC (voir `AGENTS.md` — « Ne jamais proposer
de modifier un contrat sans RFC »).

---

## 4. État du NCP

Le NCP porte lui-même un état opérationnel, distinct des états portés
par les RCH/DOD/cellules, mais avec une sémantique propre au plan de
contrôle :

| État | Signification pour le NCP |
|---|---|
| **Froid** | NCP hors service. Aucune fédération active. Les RCH fonctionnent en autonomie complète (voir §8). |
| **Chaud** | NCP activé, service minimal : registre des RCH et politiques de gouvernance disponibles en lecture, supervision non garantie. |
| **Opérationnel** | Charge normale : fédération complète, supervision temps réel, arbitrage inter-régional actif. |
| **Crise** | Priorité maximale donnée à l'arbitrage inter-régional et à la supervision des zones en crise ; les fonctions non critiques (rapports, exports) sont dégradées. |

Le NCP n'a **jamais** vocation à être un point de passage obligé du
flux métier temps réel : sa dégradation ou son arrêt ne doit jamais
bloquer l'exécution opérationnelle régionale ou départementale (§8).

---

## 5. Flux de données

### 5.1 NCP ↔ RCH

- **Descendant** : politiques de gouvernance, mises à jour de la carte
  territoriale, décisions d'arbitrage inter-régional.
- **Montant** : heartbeat, métriques agrégées, notifications de
  bascule d'état (chaud/opérationnel/crise), demandes d'arbitrage.

Le canal est un bus d'événements fédéré (voir §6, technologie Redis
Pub/Sub, ADR-013), complété par un mécanisme Outbox/Inbox (ADR-005)
pour conserver les événements de gouvernance critiques
(transfert d'autorité, changement de politique) en cas
d'indisponibilité temporaire d'un RCH. La livraison est au moins une
fois et le traitement doit être idempotent ; aucune garantie
exactly-once de bout en bout n'est revendiquée.

### 5.2 NCP ↔ supervision

Le NCP expose un flux de métriques et d'audit consolidé vers les
outils de supervision globale (tableau de bord national). Ce flux est
en **lecture seule** depuis la perspective des outils consommateurs :
aucune action de contrôle ne transite par ce canal.

```
[RCH #1] --heartbeat/métriques--> [NCP] --flux consolidé--> [Supervision]
[RCH #2] --heartbeat/métriques--> [NCP]
   ...
[NCP] --politiques/carte--> [RCH #1..N]
```

---

## 6. Persistance

Le NCP persiste exclusivement des **données de gouvernance**, jamais
de données métier opérationnelles (cellules, entités du jumeau,
observations). Schéma dédié :

```
gsie_gouvernance
├── territorial_node          -- carte territoriale maîtresse
├── territorial_change_event  -- historique des modifications de la carte
├── governance_policy         -- politiques d'activation/autorité
├── rch_registry              -- registre des RCH fédérés
├── authority_record          -- registre des autorités par périmètre
└── audit_event                -- journal d'audit consolidé
```

Conformément à ADR-011, PostgreSQL/PostGIS est la source de vérité.
L'usage de PostGIS ici est limité à la représentation géométrique des
périmètres territoriaux (contours régionaux/départementaux), pas au
calcul spatial métier — celui-ci reste porté par les DOD et les
cellules spatiales.

---

## 7. Sécurité

- **mTLS** (ADR-017) obligatoire sur tous les canaux NCP↔RCH et
  NCP↔supervision : aucune communication en clair, aucune
  authentification par simple jeton partagé.
- **RBAC admin national** : un rôle distinct des rôles régionaux et
  départementaux, seul habilité à modifier la carte territoriale
  maîtresse et les politiques de gouvernance de portée nationale (§2.2).
- **Audit exhaustif** : toute action de gouvernance (création de nœud,
  transfert d'autorité, modification de politique) génère un
  `audit_event` immuable, horodaté, signé.
- Les capsules territoriales échangées entre niveaux (RFC-0036, RFC
  parente) suivent le schéma de signature Ed25519 défini par ADR-008
  lorsque des décisions de gouvernance doivent être propagées de
  manière vérifiable jusqu'aux DOD et cellules.

---

## 8. Mode dégradé

Le NCP est conçu pour être **non bloquant** : sa panne ou son
indisponibilité ne doit jamais interrompre l'exploitation
opérationnelle du territoire.

En cas d'indisponibilité du NCP :

1. Chaque RCH continue de fonctionner en **autonomie complète** sur son
   périmètre régional (activation/désactivation des DOD, coordination
   inter-départementale, bus régional) — voir
   `TERRITORIAL_MESH_REGIONAL_HUB.md` §9.
2. Les politiques de gouvernance déjà connues d'un RCH restent
   applicables en cache local ; aucune nouvelle politique nationale ne
   peut être propagée tant que le NCP est indisponible.
3. Les décisions nécessitant strictement un arbitrage national (crise
   inter-régionale, modification de la carte territoriale) sont
   **mises en file d'attente** (Outbox, ADR-005) jusqu'au retour du NCP.
4. À la reprise du NCP, une phase de **réconciliation** rejoue les
   événements en attente et met à jour le registre des autorités si
   des transferts temporaires ont eu lieu localement pendant la panne.
   Chaque transfert est contrôlé par un epoch de fencing afin qu'un
   ancien détenteur ne puisse plus écrire après la reprise.

Ce mode dégradé est cohérent avec le principe offline-first (T-8) déjà
retenu pour les niveaux inférieurs du mesh.

---

## 9. Diagramme ASCII

```
                        +---------------------------+
                        |   NATIONAL CONTROL PLANE   |
                        |            (NCP)           |
                        |  - Carte territoriale      |
                        |  - Politiques gouvernance   |
                        |  - Registre des autorités   |
                        |  - Supervision globale      |
                        +---------------------------+
                         /        |        \        \
                        /         |         \        \
           +-----------+   +-----------+   +-----------+   +-----------+
           |   RCH #1   |   |   RCH #2   |   |   RCH #3   |   |   RCH #N   |
           | Nouvelle-  |   |   Occitanie|   |    PACA    |   |    ...     |
           | Aquitaine  |   |            |   |            |   |            |
           +-----------+   +-----------+   +-----------+   +-----------+
                 |               |               |               |
              (DOD...)        (DOD...)        (DOD...)        (DOD...)

Légende :
  ---- ligne pleine  : canal de fédération mTLS + bus d'événements fédéré
  Le NCP ne porte aucun calcul métier ; il fédère et supervise.
```
