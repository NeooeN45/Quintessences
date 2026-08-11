# Departmental Operational Domain — Architecture du domaine opérationnel départemental

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 (GSIE Territorial Mesh) |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **Dépend de** | ADR-005 (Outbox/Inbox), ADR-008 (capsule territoriale signée), ADR-011 (PostgreSQL/PostGIS), ADR-013 (Redis Pub/Sub), ADR-017 (mTLS) |
| **Voir aussi** | `TERRITORIAL_MESH_REGIONAL_HUB.md`, `TERRITORIAL_MESH_DYNAMIC_CELLS.md` |

---

## 1. Rôle

Le **Departmental Operational Domain** (DOD) est le troisième niveau
du GSIE Territorial Mesh (RFC-0036 §1). C'est le premier niveau qui
porte une **autorité métier directe** sur le jumeau numérique
environnemental : contrairement au NCP (plan de contrôle pur) et au
RCH (coordination et pool de calcul), le DOD est responsable de
l'état chaud réel des territoires opérationnels et des cellules
spatiales de son département.

---

## 2. Responsabilités

### 2.1 Autorité métier sur le périmètre départemental

Le DOD est l'**autorité métier unique** sur son périmètre
départemental. Il n'existe jamais deux DOD concurrents sur le même
département : le registre des autorités du NCP (§2.5 du document NCP)
garantit cette unicité. Toute action métier (observation, simulation,
recommandation issue des moteurs GSIE) sur le territoire départemental
transite par le DOD responsable.

### 2.2 Cellules spatiales actives sur le département

Le DOD pilote l'**allumage et l'extinction** des cellules spatiales
(RFC-0035, `TERRITORIAL_MESH_DYNAMIC_CELLS.md`) qui couvrent son
territoire : territoires opérationnels (massifs, DFCI, bassins
versants) et leurs sous-cellules de simulation.

### 2.3 State Fabric départemental

Le DOD maintient un **State Fabric départemental** : l'état chaud du
jumeau numérique pour son périmètre, persisté en PostgreSQL local et
répliqué vers le RCH (logical replication, voir
`TERRITORIAL_MESH_REGIONAL_HUB.md` §5).

### 2.4 Edge nodes départementaux

Le DOD est le point d'entrée pour les **edge nodes** opérant sur son
territoire : drones, capteurs, stations GCS-Lite, terminaux terrain.
Ces edge nodes communiquent avec le DOD via des **capsules signées**
(ADR-008), y compris en mode déconnecté (synchronisation différée).

### 2.5 Bus d'événements départemental

Le DOD héberge un **bus d'événements départemental local** (Redis
Pub/Sub, ADR-013), fédéré au bus régional du RCH (§2.5 de
`TERRITORIAL_MESH_REGIONAL_HUB.md`).

### 2.6 Applications terrain

Les applications clientes terrain (GeoSylva, Ignis, Artemis) se
connectent au DOD de leur périmètre pour consommer et alimenter le
jumeau numérique départemental — jamais directement au RCH ou au NCP.

---

## 3. Interfaces

```
IDepartmentalAuthority
  claimAuthority(scope, expectedEpoch) -> AuthorityRecord
  releaseAuthority(scope, reason, epoch) -> void
  resolveConflict(scope, authorityDecision, expectedEpoch) -> AuthorityRecord
  getAuthorityStatus(scope) -> AuthorityRecord

ICellLifecycle
  activateCell(cellId, trigger) -> CellState
  deactivateCell(cellId, reason) -> CellState
  listActiveCells() -> CellDescriptor[]
  getCellLoad(cellId) -> CellLoadSnapshot

IDepartmentalStateFabric
  getState(entityId) -> EntityState
  applyChange(change: StateChange) -> void
  getReplicationStatus() -> ReplicationStatus
  getLocalCache() -> CacheSnapshot

IEdgeNodeRegistry
  registerNode(node: EdgeNodeDescriptor) -> void
  ingestCapsule(capsule: SignedCapsule) -> IngestResult
  getNodeStatus(nodeId) -> EdgeNodeStatus
  listOfflineNodes() -> EdgeNodeDescriptor[]

IDepartmentalBus
  publish(topic, event) -> void
  subscribe(topic, handler) -> Subscription
  federateToRegional(event) -> void
```

---

## 4. Autorité métier

Le DOD détient l'autorité métier exclusive sur son périmètre
départemental. En cas de territoire opérationnel transfrontalier
(ex. massif partagé entre deux départements), l'autorité est répartie
par sous-zone via le mécanisme de **transfert d'autorité** (handoff)
défini dans RFC-0035 §3 (ADR-010), arbitré si nécessaire par le RCH
commun (§2.2 de `TERRITORIAL_MESH_REGIONAL_HUB.md`).

La résolution de conflit d'autorité (deux DOD candidats sur une même
zone frontalière) repose sur une décision explicite du RCH compétent ou
du NCP selon la portée, avec conservation de l'historique bitemporel et
incrément d'un epoch de fencing. Elle n'est pas résolue par convergence
automatique, CRDT ou last-write-wins.

---

## 5. Edge nodes

| Type d'edge node | Protocole | Sécurité |
|---|---|---|
| Drone (PX4) | Capsule signée + télémétrie | Ed25519 (ADR-008), mTLS quand connecté |
| Capteur IoT | Capsule signée périodique | Ed25519 (ADR-008) |
| GCS-Lite | Session mTLS + capsules | mTLS (ADR-017) + Ed25519 |
| Terminal terrain (app) | API DOD authentifiée | mTLS + JWT court |

Les edge nodes fonctionnent selon un principe **offline-first** : en
absence de connectivité, les observations sont persistées dans un
journal local durable, signées par l'identité de l'appareil et mises en
file pour synchronisation vers le DOD dès rétablissement du lien. Le
mécanisme Outbox/Inbox (ADR-005) assure le rejeu idempotent et la
traçabilité ; l'absence de perte est une propriété à démontrer avec un
budget de stockage et des tests de saturation, pas une garantie de la
seule capsule.

---

## 6. State Fabric départemental

- **PostgreSQL local** : source de vérité de l'état chaud
  départemental (ADR-011), hébergée au plus près du territoire pour
  minimiser la latence des cellules spatiales actives.
- **Réplication vers le RCH** : logical replication continue des
  changements d'état chaud (voir §5 de
  `TERRITORIAL_MESH_REGIONAL_HUB.md`).
- **Cache Redis local** : cache de lecture pour les accès à haute
  fréquence (état des cellules actives, positions edge nodes en
  temps réel), invalidé après chaque écriture confirmée en PostgreSQL
  et reconstructible depuis la base en cas d'événement manqué.

---

## 7. États opérationnels

| État | Signification pour le DOD |
|---|---|
| **Froid** | DOD hors service. Aucune cellule active. Edge nodes en mode offline pur. |
| **Chaud** | DOD activé, State Fabric disponible, aucune cellule spatiale active par défaut. |
| **Opérationnel** | Charge normale : cellules spatiales actives selon la demande, applications terrain connectées. |
| **Crise** | Priorité maximale : allumage de cellules de crise (voir `TERRITORIAL_MESH_DYNAMIC_CELLS.md` §3), remontée immédiate au RCH. |

---

## 8. Flux de données

- **DOD ↔ RCH** : réplication logique de l'état chaud, remontée de
  charge, demandes d'allocation de pool, handoffs cross-département.
- **DOD ↔ cellules** : ordres d'activation/extinction, streaming
  d'état pour simulation (voir
  `TERRITORIAL_MESH_DYNAMIC_CELLS.md` §8).
- **DOD ↔ edge** : ingestion de capsules signées, ordres de mission,
  synchronisation offline différée.
- **DOD ↔ apps** : API départementale consommée par GeoSylva, Ignis,
  Artemis.

```
[RCH] <--- réplication logique / métriques ---> [DOD]
                                                    |
                +-----------------------------------+-----------------------------------+
                |                        |                          |
        [Cellules spatiales]        [Edge nodes]              [Apps terrain]
        (RFC-0035)                  (drones, capteurs,        (GeoSylva, Ignis,
                                      GCS-Lite)                 Artemis)
```

---

## 9. Sécurité

- **mTLS** (ADR-017) sur tous les canaux DOD↔RCH, DOD↔apps et
  DOD↔GCS-Lite connectés.
- **Capsules signées Ed25519** (ADR-008) pour le contexte de mission,
  et signatures d'appareil pour les observations produites offline,
  connecté ou non.
- **RBAC admin départemental** : rôle distinct des rôles national et
  régional, habilité à activer/désactiver les cellules de son
  périmètre, sans autorité sur le pool de calcul régional (réservé au
  RCH).
- **Audit territorial** : chaque changement d'autorité, chaque
  activation de cellule de crise, chaque ingestion de capsule à
  signature invalide est journalisé et remonté au registre d'audit
  (consolidé au niveau NCP, §2.4 du document NCP).

---

## 10. Mode dégradé

En cas d'indisponibilité du DOD :

1. Les **edge nodes basculent en autonomie offline** : ils continuent
   d'enregistrer dans un journal local durable et signé, sans pouvoir
   synchroniser tant que le DOD n'est pas rétabli.
2. Les **cellules spatiales déjà actives continuent leur exécution**
   de manière autonome le temps nécessaire (voir
   `TERRITORIAL_MESH_DYNAMIC_CELLS.md` §10). Le RCH peut maintenir une
   supervision technique des heartbeats sans prendre l'autorité métier.
3. Le **RCH coordonne uniquement la capacité technique minimale**
   (heartbeat des cellules, réallocation de pool si nécessaire), sans
   se substituer à l'autorité métier départementale, qui reste suspendue
   jusqu'au retour du DOD.
4. À la reprise, réconciliation via Outbox/Inbox (ADR-005) : rejeu des
   capsules edge en attente, réconciliation de l'état chaud avec la
   réplique régionale.

---

## 11. Diagramme ASCII

```
                          +-------------------+
                          |        RCH        |
                          +-------------------+
                                    ^
                                    | réplication logique / métriques
                                    v
                +-----------------------------------------+
                |     DEPARTMENTAL OPERATIONAL DOMAIN       |
                |                 (DOD)                     |
                |  - Autorité métier départementale          |
                |  - State Fabric local (PostgreSQL + Redis) |
                |  - Registre des edge nodes                  |
                |  - Bus d'événements départemental            |
                +-----------------------------------------+
                 /              |                \
                /               |                 \
       +---------------+  +--------------+  +----------------+
       |   Cellules     |  |  Edge nodes  |  |  Apps terrain   |
       |   spatiales     |  |  (drones,    |  |  (GeoSylva,     |
       |   (territoires  |  |   capteurs,  |  |   Ignis,        |
       |    opérationnels)|  |   GCS-Lite)  |  |   Artemis)      |
       +---------------+  +--------------+  +----------------+
```
