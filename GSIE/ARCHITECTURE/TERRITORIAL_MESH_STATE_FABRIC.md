# GSIE Territorial Mesh — State Fabric fédéré

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_STATE_FABRIC |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **ADR liés** | ADR-002 (bitemporalité), ADR-005 (Outbox/Inbox), ADR-006 (object storage), ADR-008 (capsule territoriale signée), ADR-011 (PostgreSQL source de vérité), ADR-013 (Redis Pub/Sub), ADR-015 (interfaces abstraites UE6), ADR-017 (mTLS) |
| **Lois constitutionnelles** | GSIE-CON-007 (modularité), GSIE-CON-010 (évolution sans perte d'historique) |

---

## 1. Rôle

Le **GSIE State Fabric fédéré** est la couche d'état distribuée du
Territorial Mesh (RFC-0036 §5.5). Il constitue au-dessus du Server
Meshing (RFC-0035) une **structuration hiérarchique de la persistance
et du cache** organisée selon la hiérarchie territoriale : France →
Région → Département → Territoire Opérationnel → Cellule Spatiale →
Sous-cellule.

Son rôle est de garantir que, quel que soit le niveau territorial
interrogé (National Control Plane, Regional Coordination Hub,
Departmental Operational Domain, Cellule Dynamique, terminal Edge),
l'état du jumeau numérique environnemental reste **cohérent, traçable
et disponible**, y compris en mode dégradé ou hors-ligne.

Le State Fabric fédéré ne remplace pas la couche de persistance du
Server Meshing (RFC-0035 §3.2, P-MESH-02) — il l'organise
territorialement et l'étend jusqu'au bord du réseau (edge).

## 2. Principes

### 2.1 PostgreSQL/PostGIS reste source de vérité unique (ADR-011)

Aucun mécanisme de consensus distribué de type Raft ou Paxos n'est
introduit par le Territorial Mesh. Chaque niveau territorial disposant
d'une instance PostgreSQL/PostGIS est source de vérité uniquement pour
les données dont il possède l'autorité d'écriture : le NCP pour la
gouvernance nationale, le RCH pour ses projections et décisions de
coordination propres, le DOD pour l'état métier départemental. Il n'y a
jamais de concurrence d'écriture entre niveaux sur les mêmes données.
Le DOD est seul habilité à écrire l'état métier départemental ; le RCH
et le NCP ne font que répliquer ou synthétiser ces données (voir §4).

Cette contrainte évite la classe entière de problèmes de cohérence
forte distribuée (élection de leader, quorum, partition tolérance) au
prix d'une propagation asynchrone entre niveaux, jugée acceptable pour
un jumeau numérique environnemental (RFC-0035 §2.3).

### 2.2 Réplication logique cross-région (chaud → froid)

La réplication logique native de PostgreSQL (`pgoutput`, publication /
souscription) assure la propagation des changements entre niveaux sans
dépendance à un outil tiers. Le sens de propagation suit la charge :
un territoire en état **Chaud** ou **Crise** (§8) publie ses
changements vers le niveau parent en continu ; un territoire en état
**Froid** ne publie qu'en différé ou à la demande.

### 2.3 Cache distribué Redis cluster par niveau

Un cluster Redis distinct est déployé par niveau (national, régional,
départemental), aligné sur la topologie du bus d'événements fédéré
(voir `TERRITORIAL_MESH_EVENT_BUS.md` §3). Le cache ne contient jamais
de donnée non répliquée en base — il est une **projection en lecture**
de PostgreSQL, invalidée par les événements du bus (§5).

### 2.4 Capsules territoriales signées pour l'edge (ADR-008)

Le bord du réseau (terminal terrain, drone, application mobile
offline) ne dispose pas d'accès direct à PostgreSQL. Il emporte des
**capsules `.gsiecap`** signées Ed25519 (ADR-008), construites par le
DOD compétent, contenant l'état territorial nécessaire à une mission
déterminée. Aucune capsule ne s'auto-approuve : la clé publique de
confiance est distribuée hors capsule (ADR-008 « Modèle de
confiance »).

### 2.5 Bitemporalité préservée (ADR-002)

Chaque niveau du State Fabric préserve la double temporalité du
métamodèle v6.2 : `valid_time` (temps métier) et `transaction_time`
(temps d'écriture). La réplication logique et la synchronisation edge
ne réécrivent jamais l'historique — elles ajoutent des révisions
(§2.6).

### 2.6 Append-only (CON-010)

Aucune révision n'est supprimée, à quelque niveau que ce soit. Un
conflit de synchronisation edge → DOD (§7) produit une nouvelle
révision arbitrée, jamais un écrasement silencieux. Cette contrainte
s'applique identiquement aux caches Redis, qui sont reconstructibles
à tout moment depuis PostgreSQL.

## 3. Topologie

```
NCP (National Control Plane)
  └─ PostgreSQL national
       schéma gsie_gouvernance
       carte territoriale (référentiel des territoires)
       audit fédéré
  │
  │  réplication logique (synthèse) ▲
  │
RCH (Regional Coordination Hub)  ×N régions
  └─ PostgreSQL régional
       réplica logique des DOD de la région
       données chaudes régionales (cache tiède)
  │
  │  réplication logique (continue) ▲
  │
DOD (Departmental Operational Domain)  ×N départements
  └─ PostgreSQL départemental
       source de vérité métier départementale
       état chaud (territoires opérationnels actifs)
  │
  │  sync différentielle mission ▲▼
  │
Edge (terminal terrain / drone / mobile)
  └─ SQLite/SQLCipher
       capsule territoriale signée (.gsiecap, ADR-008)
       fonctionnement offline intégral
```

| Niveau | Rôle vis-à-vis du State Fabric | Technologie |
|---|---|---|
| **NCP** | Référentiel territorial national, gouvernance, audit fédéré | PostgreSQL/PostGIS (schéma `gsie_gouvernance`) |
| **RCH** | Réplica logique des DOD de sa région, cache tiède régional | PostgreSQL/PostGIS (réplica logique) |
| **DOD** | Source de vérité métier départementale | PostgreSQL/PostGIS (écriture primaire) |
| **Cellule Spatiale** | Consommateur du DOD, pas de persistance propre | Client (voir RFC-0035 §3) |
| **Edge** | Autonomie offline, sync différée | SQLite/SQLCipher + capsule `.gsiecap` |

## 4. Réplication logique

| Flux | Direction | Fréquence | Contenu |
|---|---|---|---|
| DOD → RCH | Ascendante | Continue (état Opérationnel/Crise) | Toutes les tables métier départementales publiées |
| RCH → NCP | Ascendante | Synthèse périodique | Agrégats territoriaux, indicateurs de gouvernance, jamais le détail métier brut |
| Edge → DOD | Ascendante | Sync de mission (§7) | Différentiel de la capsule depuis dernière synchronisation |
| NCP → RCH → DOD | Descendante | Sur publication de politique | Référentiel territorial, politiques de gouvernance (schéma `gsie_gouvernance` uniquement) |

La réplication logique DOD → RCH utilise une publication PostgreSQL
par territoire opérationnel, ce qui permet de moduler la priorité de
réplication en fonction de l'état opérationnel (§8) sans redéployer de
schéma. Les tables de transport Outbox/Inbox ne sont pas traitées comme
un état métier répliqué : la fédération des événements utilise leur
identifiant d'événement et les tables de relais du bus, afin d'éviter de
republier un même événement à chaque niveau. Le RCH ne réplique jamais directement les données brutes vers
le NCP : une projection de synthèse est d'abord matérialisée dans des
tables dédiées, puis publiée par un export ou un flux d'événements
versionné. Une vue SQL seule n'est pas présentée comme une publication
PostgreSQL native. Cette limite préserve la scalabilité nationale
(RFC-0035 §3.4, concentration dynamique des ressources).

## 5. Cache distribué

Chaque niveau territorial dispose de son propre cluster Redis,
alimenté en lecture par le PostgreSQL du même niveau. L'invalidation
du cache est déclenchée par les événements du bus fédéré
(`TERRITORIAL_MESH_EVENT_BUS.md` §5), avec un mécanisme périodique de
réconciliation depuis PostgreSQL pour récupérer les événements perdus.
Une lecture directe comparant les horodatages n'est pas utilisée comme
mécanisme nominal, afin d'éviter un couplage fort entre cache et base.

| Niveau | Contenu du cache | Invalidation |
|---|---|---|
| National | Carte territoriale, statuts d'activation, indicateurs de gouvernance | `territory.activated`, `territory.deactivated` |
| Régional | État chaud des DOD de la région, disponibilité des cellules | `cell.handoff`, `authority.transferred` |
| Départemental | État chaud des territoires opérationnels actifs, position des cellules | `crisis.declared`, `crisis.resolved`, `edge.synced` |

## 6. Capsules territoriales (ADR-008)

Le DOD compétent produit, avant une mission terrain ou une mission
edge, une capsule territoriale `.gsiecap` contenant :

- `manifest.json` (JSON canonique, liste des fichiers avec SHA-256) ;
- `signature.json` (signature Ed25519 du manifeste, clé de confiance
  externe, jamais auto-approuvée) ;
- `payload/territory.json` (extrait de l'état territorial nécessaire à
  la mission, bitemporel) ;
- `payload/data/...` et `payload/knowledge/...` (référentiels et
  connaissances nécessaires, ADR-008).

La vérification côté edge se fait intégralement hors-ligne : contrôle
d'intégrité (SHA-256), vérification de signature Ed25519 avec la clé
publique installée localement, contrôle de `valid_until` si présent.
Aucune capsule expirée ou invalide n'est chargée dans le SQLite/
SQLCipher local.

## 7. Synchronisation edge → DOD

La synchronisation est **différentielle** : seuls les enregistrements
modifiés depuis la dernière synchronisation réussie (identifiée par un
jeton de synchronisation horodaté, bitemporel) sont transmis.

Résolution de conflits :

1. Toute écriture edge produit une nouvelle révision (append-only,
   §2.6), jamais un écrasement.
2. En cas de modification concurrente de la même entité par deux
   sources (edge et DOD), les deux révisions sont conservées et un
   `conflict.detected` (voir Outbox/Inbox, ADR-005) est émis vers le
   DOD pour arbitrage — jamais résolu automatiquement par la source
   edge elle-même (CON-001, l'IA n'arbitre pas seule une décision
   métier).
3. Aucune fusion automatique n'est appliquée à une décision métier
   conflictuelle. Le DOD compétent arbitre explicitement la révision
   retenue, conserve les révisions concurrentes et enregistre la
   décision, son auteur, sa justification et son epoch dans l'historique
   (CON-001, CON-005, CON-010).

## 8. États opérationnels

| État | Comportement du State Fabric |
|---|---|
| **Froid** | PostgreSQL seul (DOD/RCH), pas de cache actif, pas de réplication continue. Consultation possible mais latence non garantie. |
| **Chaud** | Cache Redis activé au niveau concerné, réplication DOD → RCH démarrée en tâche de fond. |
| **Opérationnel** | Réplication logique active en continu à tous les niveaux concernés, cache tenu à jour par événements. |
| **Crise** | Réplication logique priorisée sur le territoire en crise (bande passante et fenêtres de commit dédiées), cache invalidé en temps réel, capsules edge régénérées à fréquence accrue. |

## 9. Sécurité

- **mTLS (ADR-017)** entre tous les composants du State Fabric (NCP ↔
  RCH ↔ DOD), y compris pour la réplication logique PostgreSQL.
- **Chiffrement at-rest** : chiffrement natif au niveau des volumes
  PostgreSQL (NCP, RCH, DOD).
- **SQLCipher côté edge** : chiffrement de la base locale avec une clé
  issue d'un secret matériel ou d'un keystore sécurisé de l'appareil,
  jamais dérivée de la capsule seule et jamais stockée en clair.
- **Audit fédéré** : toute lecture/écriture structurante au niveau NCP
  (schéma `gsie_gouvernance`) et tout arbitrage de conflit (§7) sont
  journalisés de manière immuable, cohérent avec RFC-0035 §3
  (journal d'audit immuable de l'orchestrateur de mesh).

## 10. Mode dégradé

| Panne | Comportement |
|---|---|
| **Panne RCH** | Les DOD de la région basculent en autonomie : écriture locale poursuivie, WAL/publication PostgreSQL et événements Outbox conservés pour reprise. À la remontée du RCH, la réplication logique reprend depuis la position conservée et les événements sont rejoués idempotemment. |
| **Panne DOD** | Les cellules et terminaux edge du département basculent en autonomie offline complète (capsules déjà distribuées et journal local signé). Reprise par synchronisation différentielle (§7) dès rétablissement du DOD, avec arbitrage des conflits. |
| **Panne NCP** | Aucun impact sur l'exploitation métier régionale/départementale — le NCP n'est pas dans le chemin critique opérationnel, uniquement dans celui de la gouvernance et de la synthèse nationale. |
| **Reprise générale** | À la remontée d'un niveau, rejeu ordonné des files Outbox en attente, puis reprise de la réplication logique standard, jamais de purge de l'historique en attente. |

## 11. Diagramme ASCII — topologie de réplication

```
                     ┌───────────────────────────────┐
                     │              NCP               │
                     │  PostgreSQL national            │
                     │  gsie_gouvernance                │
                     │  carte territoriale · audit      │
                     └───────────────┬─────────────────┘
                                     │ synthèse (agrégats)
                     ┌───────────────▲─────────────────┐
                     │              RCH  (×N régions)   │
                     │  PostgreSQL régional              │
                     │  réplica logique des DOD          │
                     │  cache Redis régional              │
                     └───────────────┬─────────────────┘
                                     │ réplication continue
                     ┌───────────────▲─────────────────┐
                     │              DOD  (×N dépts)     │
                     │  PostgreSQL départemental         │
                     │  source de vérité métier          │
                     │  cache Redis départemental         │
                     └───────────────┬─────────────────┘
                                     │ sync différentielle
                                     │ (capsule .gsiecap)
                     ┌───────────────▲─────────────────┐
                     │             Edge                 │
                     │  SQLite/SQLCipher                 │
                     │  capsule territoriale signée       │
                     │  autonomie offline complète        │
                     └───────────────────────────────────┘
```
