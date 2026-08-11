# GSIE Territorial Mesh — Matrices de responsabilités, autorités et réplication

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_MATRICES |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **Documents liés** | `TERRITORIAL_MESH_STATE_FABRIC.md`, `TERRITORIAL_MESH_EVENT_BUS.md`, `TERRITORIAL_MESH_DIAGRAMS.md` |

---

## 1. Matrice responsabilités × niveaux

| Fonction | NCP | RCH | DOD | Cellule | Edge |
|---|---|---|---|---|---|
| Carte territoriale (référentiel) | Propriétaire | Consommateur | Consommateur | — | Extrait capsule |
| Gouvernance | Propriétaire | Relais | Applique | — | — |
| Pool de calcul | Supervision | Allocation régionale | Allocation locale | Consomme | — |
| Autorité métier | — | Coordination | Propriétaire | Exécution | Acquisition |
| Simulation | — | — | Coordination | Propriétaire | — |
| Edge (offline) | — | — | Distribution capsules | Support | Propriétaire |
| Persistance | Gouvernance (schéma `gsie_gouvernance`) | Réplica logique | Source de vérité | — | SQLite/SQLCipher |
| Bus d'événements | Bus national | Bus régional | Bus départemental | Bus de cellule | Sync différée |
| Supervision | Fédérale | Régionale | Départementale | Locale | — |
| Audit | Fédéré, immuable | Relais audit | Local | Local | Journal de mission |

## 2. Matrice autorités × périmètres

| Niveau | Autorité sur | Ne peut pas |
|---|---|---|
| **NCP** | Gouvernance nationale, référentiel territorial, politique fédérale, audit fédéré | Écrire l'état métier départemental directement |
| **RCH** | Coordination régionale, orchestration de disponibilité des DOD, synthèse régionale | Déclarer ou clôturer seul une crise métier départementale |
| **DOD** | Autorité métier départementale, activation des territoires opérationnels, arbitrage des conflits de synchronisation edge | Modifier la politique de gouvernance nationale |
| **Cellule** | Autorité d'exécution de simulation locale, exécution de mission dans son périmètre | Transférer l'autorité territoriale sans validation DOD/RCH et epoch de fencing |
| **Edge** | Acquisition terrain, exécution offline dans les limites de la capsule signée et du journal local | Valider seul une donnée en conflit (arbitrage réservé au DOD, `TERRITORIAL_MESH_STATE_FABRIC.md` §7) |

## 3. Matrice réplication × niveaux

| Flux | Fréquence | Contenu répliqué | Document de référence |
|---|---|---|---|
| DOD → RCH | Continue (Opérationnel/Crise) | Toutes tables métier départementales publiées | `TERRITORIAL_MESH_STATE_FABRIC.md` §4 |
| RCH → NCP | Synthèse périodique | Agrégats et indicateurs de gouvernance | `TERRITORIAL_MESH_STATE_FABRIC.md` §4 |
| Edge → DOD | Sync de mission (différentielle) | Enregistrements modifiés depuis dernier jeton de sync | `TERRITORIAL_MESH_STATE_FABRIC.md` §7 |
| NCP → RCH → DOD | Sur publication de politique | Référentiel territorial, politiques (`gsie_gouvernance`) | `TERRITORIAL_MESH_STATE_FABRIC.md` §4 |

## 4. Matrice états × composants

| État | NCP | RCH | DOD | Cellule | Edge |
|---|---|---|---|---|---|
| **Froid** | Service de contrôle indisponible, base conservée pour reprise | PostgreSQL seul, réplication différée | PostgreSQL seul, pas de cache | Inactive | Capsule non émise |
| **Chaud** | Synthèse démarrée | Cache activé, réplication démarrée | Cache activé | Standby | Capsule distribuée |
| **Opérationnel** | Supervision active | Réplication continue | Réplication continue, autorité métier active | Active, exécute missions | Sync de mission active |
| **Crise** | Supervision priorisée, audit renforcé | Réplication priorisée sur territoire en crise | Autorité métier priorisée, arbitrage accéléré | Activation maximale, handoff fréquent | Sync accrue, capsules régénérées |

## 5. Matrice sécurité × niveaux

| Niveau | mTLS | RBAC | Audit | Chiffrement |
|---|---|---|---|---|
| **NCP** | Oui, toutes connexions RCH/NCP | Rôles de gouvernance nationale | Journal fédéré immuable | At-rest (volumes PostgreSQL) |
| **RCH** | Oui, DOD/RCH et RCH/NCP | Rôles de coordination régionale | Relais vers audit fédéré | At-rest |
| **DOD** | Oui, cellules/DOD et DOD/RCH | Rôles métier départementaux | Journal local + remontée | At-rest |
| **Cellule** | Oui (RFC-0035 bus inter-nœuds) | Rôles de simulation locale | Journal local | En transit uniquement |
| **Edge** | Non applicable (offline) — mTLS à la sync | RBAC local restreint à la mission | Journal de mission dans la capsule | SQLCipher (at-rest local) |

## 6. Matrice applications × niveaux

| Application | NCP | RCH | DOD | Edge |
|---|---|---|---|---|
| **GeoSylva** | Consultation de synthèse (rare) | Coordination régionale des missions forestières | Connexion primaire (mission départementale) | Capsule territoriale mission (offline-first) |
| **Ignis** | Supervision nationale en crise | Activation régionale en cas d'incendie | Connexion primaire (gestion de crise) | Sync mission terrain (drone, équipe au sol) |
| **Artemis** | — | Coordination régionale (suivi faune) | Connexion primaire | Capsule mission observation |
| **Hydro** | — | Coordination régionale (bassin hydrographique) | Connexion primaire | Capsule mission hydrologique |
| **Flora** | — | Coordination régionale | Connexion primaire | Capsule mission végétation |
| **Hub (Centre de Commandement)** | Vue de synthèse nationale (multi-région) | Vue régionale multi-départementale | Vue départementale opérationnelle | Non applicable (client de rendu, RFC-0035 §3) |

## 7. Matrice modes dégradés × pannes

| Panne | Comportement |
|---|---|
| **Panne NCP** | Aucun impact opérationnel régional/départemental ; gouvernance et synthèse nationale suspendues jusqu'à reprise. |
| **Panne RCH** | Les DOD de la région basculent en autonomie complète (écriture locale poursuivie) ; WAL/publication PostgreSQL et événements Outbox sont conservés jusqu'à la reprise du RCH. |
| **Panne DOD** | Cellules et edge du département basculent en autonomie offline ; reprise par sync différentielle à rétablissement. |
| **Panne Cellule** | Handoff vers une cellule voisine ou reprise directe par le DOD, selon disponibilité (RFC-0035 §3.3, transfert d'autorité). |
| **Panne Edge** | La session terrain est récupérable si le journal local durable et son budget de stockage sont intacts ; reprise à la prochaine synchronisation, avec contrôle d'intégrité et rejeu idempotent (SQLite/SQLCipher persistant). |
| **Panne Bus (Redis)** | Les niveaux inférieurs continuent en autonomie ; événements accumulés en Outbox jusqu'à reprise du bus (`TERRITORIAL_MESH_EVENT_BUS.md` §10). |
| **Panne PostgreSQL (un niveau)** | Aucune écriture possible à ce niveau ; les niveaux enfants basculent en autonomie si le niveau en panne est leur parent direct. |
| **Panne Redis (cache)** | Reconstruction complète du cache depuis PostgreSQL à la reprise ; aucune perte de donnée car le cache n'est jamais source de vérité. |
