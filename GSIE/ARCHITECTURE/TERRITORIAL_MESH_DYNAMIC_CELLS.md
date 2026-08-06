# Dynamic Spatial Cells — Architecture des cellules spatiales dynamiques

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_DYNAMIC_CELLS |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 (GSIE Territorial Mesh), RFC-0035 (GSIE Server Meshing) |
| **Dépend de** | ADR-010 (autorité hybride zone + type), ADR-012 (Replication Graph), ADR-011 (PostgreSQL/PostGIS), ADR-013 (Redis Pub/Sub), ADR-017 (mTLS) |
| **Voir aussi** | `TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md` |

---

## 1. Rôle

Les **Dynamic Spatial Cells** constituent le dernier niveau structurel
du GSIE Territorial Mesh (RFC-0036 §1), avant les sous-cellules de
simulation. Elles sont le cœur du **GSIE Server Meshing** (RFC-0035) :
c'est à ce niveau que se concentrent le calcul, la simulation active et
la réplication d'entités du jumeau numérique environnemental.

Une cellule spatiale est allumée ou éteinte dynamiquement selon la
charge et le besoin opérationnel — elle n'a pas d'existence permanente
comme le NCP, le RCH ou le DOD, qui sont des structures administratives
stables.

---

## 2. Responsabilités

### 2.1 Allumage/extinction selon la charge

Une cellule spatiale transite entre les états
`Froid → Chaud → Opérationnel → Crise` selon des déclencheurs définis
en §4. Le DOD responsable du territoire opérationnel couvert par la
cellule décide de l'allumage/extinction, dans les limites du pool de
calcul alloué par le RCH.

### 2.2 Transfert d'autorité inter-cellules

Lorsqu'une entité (drone, zone de simulation, observation en cours)
franchit la frontière entre deux cellules, un **handoff** transfère
l'autorité d'exécution de la cellule source vers la cellule destination.
La continuité sans interruption visible est un objectif mesuré, pas une
garantie avant validation du prototype (RFC-0035 §3, ADR-010).

### 2.3 Réplication par pertinence

Chaque cellule ne réplique et ne reçoit que les entités **pertinentes**
pour son périmètre — visibles, interagissantes, ou nécessaires à la
continuité d'une simulation en cours — selon le **Replication Graph**
défini par ADR-012, et non l'état complet du jumeau numérique.

### 2.4 Simulation active

La cellule héberge l'exécution effective des moteurs GSIE de
simulation (ex. moteur Simulation, moteur ForestDynamics) et des
scènes Unreal Engine associées (IGNIS, GeoSylva) pour les
sous-cellules de simulation qui lui sont attachées.

### 2.5 Streaming vers le Hub

La cellule expose un flux de streaming vers le Centre de Commandement
(Hub) via WebSocket, conforme au contrat **HUB-002**, pour la
visualisation temps réel des entités et simulations qu'elle porte.

---

## 3. Types de cellules

| Type | Description | Exemple |
|---|---|---|
| **Cellule administrative** | Alignée strictement sur les limites d'un département | Cellule Charente (16) |
| **Cellule scientifique** | Alignée sur un territoire opérationnel scientifique, potentiellement transfrontalière | Massif forestier, périmètre DFCI, bassin versant |
| **Cellule de crise** | Allumée temporairement pour un événement critique, hors périmètre administratif figé | Incendie, inondation |

Un territoire opérationnel scientifique peut recouvrir plusieurs
DOD, mais une cellule d'exécution ne possède qu'un seul détenteur
d'autorité à un instant donné. Le territoire partagé est donc découpé
en cellules d'exécution par périmètre d'autorité, avec coordination
inter-DOD et handoff via le RCH commun si nécessaire (voir
`TERRITORIAL_MESH_REGIONAL_HUB.md` §2.2).

---

## 4. Allumage/extinction

| Déclencheur | Type de cellule concerné | Procédure |
|---|---|---|
| Demande opérateur (mission planifiée) | Administrative, scientifique | Activation par le DOD, dans le pool alloué |
| Détection automatique de charge | Administrative, scientifique | Activation automatique si seuil de charge dépassé sur un territoire opérationnel |
| Alerte incident (incendie, inondation) | Crise | Préactivation technique possible et demande de priorité au RCH ; la déclaration métier Crise reste attribuée au DOD (§2.6 de `TERRITORIAL_MESH_REGIONAL_HUB.md`) |
| Fin de mission / retour sous seuil | Tous | Extinction, retour à l'état Froid ou Chaud selon politique |

L'état d'une cellule est **persisté** (PostgreSQL, ADR-011) avant toute
transition, afin que l'extinction ne fasse jamais perdre l'état
métier : seule la capacité de calcul est libérée, l'état survit.

---

## 5. Handoff inter-cellules

Le handoff suit le protocole de transfert d'autorité défini par
RFC-0035 §3 et ADR-010 :

1. Détection du franchissement de frontière par l'entité et lecture
   de l'epoch d'autorité courant.
2. Réservation de la cellule destination et émission d'un jeton de
   handoff idempotent.
3. Transfert de l'état de l'entité depuis la source de vérité avec
   incrément d'un epoch de fencing ; l'ancien détenteur est refusé dès
   que le nouvel epoch est actif.
4. Confirmation de prise en charge par la cellule destination et
   vérification du jeton par le DOD/RCH compétent.
5. Libération logique de l'autorité par la cellule source et émission
   de l'événement d'audit. En cas d'échec, le jeton expire et l'ancien
   propriétaire reste le seul détenteur valide.

En cas d'échec ou de désynchronisation du handoff, l'epoch de fencing
le plus récent et valide détermine le détenteur temporaire ; les
écritures de l'ancien epoch sont rejetées. Un conflit non résolu est
escaladé au DOD/RCH compétent avec conservation de l'historique
bitemporel. Aucun last-write-wins ni CRDT n'est utilisé (voir
`GSIE/ARCHITECTURE/SERVER_MESHING_ADR.md`).

---

## 6. Réplication par pertinence

Le **Replication Graph** (ADR-012) détermine, pour chaque cellule,
l'ensemble des entités qu'elle doit recevoir :

- entités physiquement présentes dans son périmètre ;
- entités interagissant avec une entité de son périmètre ;
- entités nécessaires à la continuité d'une simulation en cours
  (ex. front de feu approchant la frontière d'une cellule de crise).

Ce mécanisme évite la réplication totale de l'état du jumeau numérique
à chaque cellule, condition de scalabilité du mesh à l'échelle
nationale.

---

## 7. États opérationnels

Matrice état × type de cellule :

| État | Administrative | Scientifique | Crise |
|---|---|---|---|
| **Froid** | Par défaut hors mission | Par défaut hors mission | N/A — n'existe qu'active |
| **Chaud** | Veille active, faible charge | Veille active, faible charge | N/A |
| **Opérationnel** | Charge normale, missions planifiées | Charge normale, suivi scientifique continu | N/A |
| **Crise** | Bascule possible si incident sur le périmètre | Bascule possible si incident sur le périmètre | État permanent tant qu'active |

---

## 8. Flux de données

- **Cellule ↔ DOD** : ordres d'activation/extinction, remontée de
  charge, persistance de l'état.
- **Cellule ↔ cellule** : handoff inter-cellules, coordination de
  frontière, réplication par pertinence.
- **Cellule ↔ Hub** : streaming WebSocket (HUB-002) pour la
  visualisation temps réel dans le Centre de Commandement.

```
[DOD] <--- activation / extinction / persistance ---> [Cellule A]
                                                             |
                                       handoff / réplication pertinence
                                                             |
                                                       [Cellule B]
                                                             |
                                                 streaming WebSocket (HUB-002)
                                                             |
                                                          [Hub UE5.8]
```

---

## 9. Sécurité

- **mTLS inter-cellules** (ADR-017) pour tout échange de handoff ou de
  réplication entre cellules, y compris transfrontalières entre DOD
  différents.
- **Autorité signée** : chaque transfert d'autorité (§5) est
  accompagné d'une preuve de transfert vérifiable, cohérente avec le
  schéma de capsules signées Ed25519 (ADR-008) lorsque le transfert
  implique un edge node ou une frontière départementale.

---

## 10. Mode dégradé

En cas de panne d'une cellule spatiale :

1. Le DOD responsable **détecte la perte de heartbeat** de la cellule.
2. Le DOD **réalloue** le territoire opérationnel concerné à une
   nouvelle instance de cellule, en restaurant l'état persisté
   (PostgreSQL, ADR-011) — aucune perte de données métier, seule la
   continuité de simulation temps réel est interrompue brièvement.
3. Les entités actives au moment de la panne font l'objet d'un
   **handoff automatique** vers les cellules voisines lorsque cela est
   possible, avec validation d'un nouvel epoch de fencing ; à défaut,
   elles restent en lecture seule jusqu'à la reprise de l'autorité.
4. Le Hub est notifié de l'interruption de streaming et bascule
   automatiquement sur le flux de la cellule de remplacement une fois
   celle-ci opérationnelle.

---

## 11. Diagramme ASCII

```
                    +-------------------------+
                    |           DOD            |
                    | (ex: Charente, 16)        |
                    +-------------------------+
                     /          |          \
                    /           |           \
          +-----------+  +-----------+  +-----------+
          | Cellule A  |  | Cellule B  |  | Cellule C  |
          | (admin.,   |  | (scientif.,|  | (crise,    |
          |  charge    |  |  massif    |  |  incendie) |
          |  normale)  |  |  forestier)|  |            |
          +-----------+  +-----------+  +-----------+
                |  <--- handoff --->  |
                |   (franchissement    |
                |    de frontière)     |
                |                      |
          streaming HUB-002      streaming HUB-002
                |                      |
                v                      v
          +--------------------------------+
          |        Hub (Centre de           |
          |       Commandement UE5.8)       |
          +--------------------------------+
```
