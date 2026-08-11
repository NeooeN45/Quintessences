# Regional Coordination Hub — Architecture du hub de coordination régionale

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_REGIONAL_HUB |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 (GSIE Territorial Mesh) |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **Dépend de** | ADR-011 (PostgreSQL/PostGIS), ADR-013 (Redis Pub/Sub), ADR-017 (mTLS) |
| **Voir aussi** | `TERRITORIAL_MESH_NATIONAL_CONTROL_PLANE.md`, `TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md` |

---

## 1. Rôle

Le **Regional Coordination Hub** (RCH) est le second niveau du GSIE
Territorial Mesh (RFC-0036 §1). Contrairement au NCP, le RCH n'est pas
un pur plan de contrôle : il porte un **pool de calcul régional**
réel et coordonne l'exécution opérationnelle sur son périmètre —
une région administrative (ex. Nouvelle-Aquitaine).

Le RCH est l'échelon où la gouvernance nationale (NCP) devient
capacité de calcul concrète, allouée dynamiquement aux Departmental
Operational Domains (DOD) de la région.

---

## 2. Responsabilités

### 2.1 Pool de calcul régional

Le RCH gère un **pool de calcul régional** : une capacité de calcul
dédiée (datacenter régional ou infrastructure cloud régionalisée)
partagée entre tous les DOD de la région. Ce pool héberge les cellules
spatiales actives lorsque leur charge dépasse la capacité locale d'un
DOD, ou lors d'une montée en charge de crise (§2.6).

### 2.2 Coordination inter-départementale

Le RCH coordonne les **handoffs cross-département** : lorsqu'une
entité, une cellule spatiale ou un territoire opérationnel
(ex. massif forestier à cheval sur deux départements) nécessite un
transfert d'autorité entre deux DOD de la même région, le RCH arbitre
et enregistre ce transfert (aligné sur le mécanisme de transfert
d'autorité de RFC-0035 §3, ADR-010).

### 2.3 Réplication régionale des données chaudes

Le RCH maintient une **réplication régionale** des données chaudes
issues des DOD, via **PostgreSQL logical replication** : chaque DOD
réplique en continu son état chaud vers le RCH, qui en conserve une
vue consolidée à l'échelle régionale (voir §5).

### 2.4 Activation/désactivation des DOD

Le RCH pilote le cycle de vie opérationnel des DOD de sa région :

```
Froid → Chaud → Opérationnel → Crise
```

Une activation de disponibilité d'un DOD (froid→chaud) est orchestrée
par le RCH selon la politique de gouvernance applicable (voir
`TERRITORIAL_MESH_NATIONAL_CONTROL_PLANE.md` §2.2), soit sur demande
départementale, soit automatiquement (planification saisonnière,
alerte météo, seuil de charge). Cette action administrative ne remplace
pas la déclaration métier d'une crise, qui relève du DOD.

### 2.5 Bus d'événements régional

Le RCH héberge un **bus d'événements régional** (Redis Pub/Sub,
ADR-013) qui fédère les bus départementaux (§2.5 de
`TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md`) et relaie vers le NCP les
événements de portée nationale.

### 2.6 Montée en charge crise

En situation de crise (incendie majeur, inondation), le RCH :

- coordonne les DOD concernés après déclaration d'un état **Crise**
  par l'autorité métier DOD ;
- alloue en priorité le pool de calcul régional aux cellules spatiales
  du DOD en crise, au détriment des DOD en charge normale (dégradation
  contrôlée, jamais totale) ;
- notifie le NCP si la crise dépasse le périmètre régional (§2.3 du
  document NCP).

---

## 3. Interfaces

```
IRegionalPool
  getCapacity() -> RegionalCapacitySnapshot
  allocate(request: AllocationRequest) -> AllocationResult
  release(allocationId) -> void
  reprioritize(criteria: PriorityCriteria) -> void

IDepartmentalLifecycle
  activateDOD(dodId, reason) -> DODState
  deactivateDOD(dodId, reason) -> DODState
  requestCrisisEscalation(dodId, incident) -> EscalationRequest
  getDODState(dodId) -> DODState

IRegionalReplication
  getReplicationStatus(dodId) -> ReplicationStatus
  getRegionalSnapshot(scope?) -> RegionalDataSnapshot
  resolveConflict(conflictId, authorityDecision, expectedEpoch) -> ConflictResolution

IRegionalBus
  publish(topic, event) -> void
  subscribe(topic, handler) -> Subscription
  federateToNational(event) -> void
```

Toute évolution de ces contrats suit la règle générale : pas de
modification sans RFC.

---

## 4. Pool de calcul

Le pool de calcul régional est décrit par une capacité déclarée
(nœuds de calcul, mémoire, capacité de simulation concurrente) et une
allocation dynamique par priorité :

| Priorité | Contexte | Comportement d'allocation |
|---|---|---|
| P0 — Crise | DOD en état Crise | Allocation garantie, préemption possible sur P2/P3 |
| P1 — Opérationnel critique | Cellules à charge élevée hors crise | Allocation best-effort élevée |
| P2 — Opérationnel normal | Charge normale | Allocation standard |
| P3 — Chaud | DOD activé mais faible charge | Allocation minimale |

L'allocation est réévaluée en continu à partir des métriques de charge
remontées par les DOD (voir §7 de
`TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md`).

---

## 5. Réplication régionale

- **PostgreSQL logical replication** : chaque DOD publie ses
  changements d'état chaud (schéma départemental) vers le RCH, qui les
  consolide en vue régionale (ADR-011 — PostgreSQL/PostGIS reste la
  source de vérité à chaque niveau ; le RCH ne fait que consolider,
  il ne réécrit jamais l'état départemental).
- **Redis cluster régional** : le bus régional (§2.5) s'appuie sur un
  cluster Redis dédié à la région, distinct du cluster national et des
  clusters départementaux, pour isoler les pannes.
- **Stratégie chaud/froid** : seules les données des DOD en état Chaud,
  Opérationnel ou Crise sont répliquées activement vers le RCH ; un DOD
  Froid ne réplique rien (économie de ressources, cohérent avec
  l'esprit d'allumage/extinction dynamique de RFC-0035 §3).

---

## 6. États opérationnels

| État | Signification pour le RCH |
|---|---|
| **Froid** | RCH hors service. Aucune coordination régionale. Les DOD fonctionnent en autonomie (§9). |
| **Chaud** | Pool de calcul en veille active, réplication minimale, aucune allocation de crise possible. |
| **Opérationnel** | Coordination complète, allocation dynamique du pool, réplication régionale à jour. |
| **Crise** | Priorité absolue donnée aux DOD en crise ; préemption de ressources sur les DOD non prioritaires. |

---

## 7. Flux de données

### 7.1 RCH ↔ NCP

Heartbeat, métriques agrégées, demandes d'arbitrage inter-régional
(§5.1 du document NCP).

### 7.2 RCH ↔ DOD

- **Descendant** : décisions d'activation/désactivation, allocation de
  pool, politiques régionales.
- **Montant** : état chaud (réplication logique), métriques de charge,
  demandes de handoff cross-département.

### 7.3 RCH ↔ RCH voisin

Coordination directe entre RCH limitrophes pour préparer les
territoires opérationnels transfrontaliers (ex. massif forestier à
cheval sur deux régions), sans passer nécessairement par le NCP pour la
préparation d'un cas non critique. Elle ne vaut pas transfert définitif
d'autorité : tout transfert utilise un epoch de fencing et est enregistré
au NCP dès que celui-ci est disponible.

```
[NCP]
   ^
   | heartbeat / métriques / arbitrage
   v
[RCH régional] <---- coordination directe ----> [RCH voisin]
   ^
   | activation / allocation / réplication logique
   v
[DOD #1]  [DOD #2]  ...  [DOD #N]
```

---

## 8. Sécurité

- **mTLS** (ADR-017) sur tous les canaux RCH↔NCP, RCH↔DOD et
  RCH↔RCH voisin.
- **RBAC admin régional** : rôle distinct de l'admin national et de
  l'admin départemental, habilité à activer/désactiver les DOD de sa
  région et à allouer le pool de calcul régional, mais **sans**
  autorité sur la carte territoriale maîtresse (réservée au NCP, §2.2
  du document NCP).

---

## 9. Mode dégradé

En cas d'indisponibilité du RCH :

1. Chaque DOD continue de fonctionner en **autonomie complète** sur son
   périmètre départemental (voir
   `TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md` §10).
2. Le NCP, s'il est disponible, conserve une **supervision agrégée
   temporaire** à partir des dernières métriques reçues. Il ne prend pas
   le contrôle direct des DOD et ne se substitue pas à leur autorité
   métier.
3. Les handoffs cross-département sont mis en file d'attente jusqu'au
   retour du RCH ou jusqu'à résolution manuelle par les admins
   départementaux concernés.
4. À la reprise, réconciliation de la réplication logique et rejeu
   idempotent des événements en attente (Outbox/Inbox, ADR-005), avec
   contrôle des epochs d'autorité.

---

## 10. Diagramme ASCII

```
                          +-------------------+
                          |        NCP        |
                          +-------------------+
                                    ^
                                    | heartbeat / arbitrage
                                    v
                    +-------------------------------+
                    |   REGIONAL COORDINATION HUB    |
                    |             (RCH)              |
                    |  - Pool de calcul régional      |
                    |  - Cycle de vie des DOD          |
                    |  - Réplication logique régionale |
                    |  - Bus d'événements régional      |
                    +-------------------------------+
                       /                  \
                      /                    \
              +----------+          +----------+
              |  DOD 16  |          |  DOD 79  |
              | Charente |          | Deux-    |
              |          |          | Sèvres   |
              +----------+          +----------+  +----------+
```
