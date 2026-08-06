# GSIE Server Meshing — Architecture cible

| Champ | Valeur |
|---|---|
| **Chantier** | GSIE Server Meshing — Vague 2 (architecture) |
| **Phase** | 4 — Implémentation (anticipation Phase 5-7) |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **Auteur** | Camille Perraudeau (Fondateur) — instruit par agent architecte |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-003 (connaissance avant code), GSIE-CON-007 (modularité), GSIE-CON-010 (évolution sans perte d'historique) |
| **RFC liée** | RFC-0035 (vision et principes), RFC-0003 (GSIE-Net), RFC-0011 (métamodèle v6.2) |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents apparentés** | `SERVER_MESHING_PROTOTYPE_V0.md`, `SERVER_MESHING_ROADMAP.md`, `COMMAND_CENTER_UNREAL.md` (livrable 211), `ADR-007-api-v6.2.md`, livrable 203 (communication moteurs) |

---

## 1. Mission du document

Décrire l'architecture cible long terme du GSIE Server Meshing telle
que cadrée par RFC-0035 et GSIE-DIR-0012. Ce document ne préjuge pas
du calendrier de mise en œuvre (voir `SERVER_MESHING_ROADMAP.md`) ni
du périmètre du premier prototype (voir `SERVER_MESHING_PROTOTYPE_V0.md`).
Il fixe la structure que ces deux documents doivent respecter.

Il est **Draft** : il oriente les choix d'implémentation Phase 4
(interfaces abstraites, persistance externe) sans imposer de livraison
immédiate d'un mesh opérationnel.

---

## 2. Vue d'architecture cible

```
                          ┌───────────────────────────────────────────┐
                          │         ORCHESTRATEUR DE MESH              │
                          │  - Découpage spatial adaptatif             │
                          │  - Allocation de ressources                │
                          │  - Supervision des transferts d'autorité   │
                          │  - Registre de service discovery           │
                          └───────────────┬─────────────────────────────┘
                                          │ (contrôle, pas de données métier)
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼────────┐               ┌────────▼───────┐               ┌────────▼───────┐
│ SERVEUR DE ZONE │               │ SERVEUR DE ZONE│               │ SERVEUR DE ZONE│
│  Aquitaine       │◄──handoff──►│  Corse          │◄──handoff──►│  PACA           │
│  (IMeshNode,     │               │  (priorité feu) │               │                 │
│   IZoneServer)   │               │                 │               │                 │
└───────┬──────────┘               └───────┬─────────┘               └───────┬─────────┘
        │                                  │                                 │
        └──────────────────┬───────────────┴────────────────┬────────────────┘
                            │                                │
                   ┌────────▼────────┐               ┌───────▼─────────┐
                   │ SERVEURS         │               │ GRAPHE D'AUTORITÉ│
                   │ SPÉCIALISÉS      │◄──consulte───►│ (IAuthorityGraph)│
                   │ Simulation       │               │ zone × type      │
                   │ Learning         │               │ résolution de    │
                   │ Knowledge        │               │ conflits          │
                   │ Drones           │               └───────┬─────────┘
                   └────────┬─────────┘                       │
                            │                                 │
                            └───────────────┬─────────────────┘
                                            │
                          ┌─────────────────▼─────────────────────┐
                          │        COUCHE DE PERSISTANCE            │
                          │  PostgreSQL/PostGIS — source de vérité  │
                          │  Métamodèle v6.2 (bitemporel, RFC-0011) │
                          │  Journal d'audit du mesh (immuable)     │
                          │  (IPersistenceLayer)                    │
                          └─────────────────┬────────────────────────┘
                                            │ (flux de réplication par pertinence)
                          ┌─────────────────▼─────────────────────┐
                          │            CLIENTS DE RENDU             │
                          │  Hub UE5.8 (salle de commandement)      │
                          │  Futur : Hub UE6 (interfaces stables)   │
                          │  CesiumJS web (léger, distant)          │
                          │  Apps mobiles / GCS-Lite (offline-first)│
                          │  (IRenderClient)                        │
                          └───────────────────────────────────────┘
```

Note de lecture : les flèches « handoff » entre serveurs de zone
représentent le transfert d'autorité (§6), pas un flux de données
permanent. Les serveurs de zone ne communiquent jamais directement
d'état métier entre eux hors persistance — voir §11 (relation avec
GSIE-Net).

---

## 3. Composants

### 3.1 Orchestrateur de mesh

Responsabilité unique : décider **qui possède quoi** (autorité) et
**avec quels moyens** (allocation), sans jamais porter lui-même de
données métier. Il consomme des métriques (charge, alertes, nombre
d'opérateurs connectés) et produit des décisions de redécoupage et de
transfert, chacune journalisée (§10).

L'orchestrateur ne remplace pas le graphe d'autorité : il le pilote.
Le graphe d'autorité est la structure de données persistée ; l'orchestrateur
est le processus qui la fait évoluer.

### 3.2 Serveurs de zone

Un serveur de zone porte l'autorité spatiale primaire (P-MESH-03) sur
une portion géographique définie dynamiquement par l'orchestrateur. Il
expose l'interface `IZoneServer` (extension de `IMeshNode`). Il ne
persiste rien en mémoire durable — toute écriture transite par
`IPersistenceLayer` avant d'être considérée comme valide (P-MESH-02).

### 3.3 Serveurs spécialisés

Un serveur spécialisé porte l'autorité fonctionnelle secondaire
(P-MESH-03) sur un type d'entité, indépendamment de la zone
(Simulation, Learning, Knowledge, Drones — RFC-0035 §4.1). Il expose
`ISpecializedServer`. Sa relation avec les 14 moteurs GSIE est directe :
un serveur spécialisé encapsule un ou plusieurs moteurs (par exemple,
le serveur Simulation encapsule le moteur Simulation Engine et consulte
le moteur Reasoning Engine).

### 3.4 Couche de persistance

PostgreSQL/PostGIS reste l'unique source de vérité (CON-003, CON-007,
P-MESH-02). Le métamodèle v6.2 bitemporel (RFC-0011) porte l'historique
des entités. Le graphe d'autorité et le journal d'audit du mesh sont
des extensions de schéma de cette même couche — ils ne créent pas de
seconde source de vérité. Interface : `IPersistenceLayer`.

### 3.5 Graphe d'autorité

Structure bidimensionnelle (zone × type) répondant à la question :
*quel serveur est responsable de cette entité, à cet instant ?*
Persisté, répliqué en lecture aux serveurs du mesh, consultable par les
clients de rendu pour savoir quel flux écouter. Interface :
`IAuthorityGraph`. Détail du protocole de résolution : §7.

### 3.6 Clients de rendu

Le Hub UE5.8 (livrable 211) et ses évolutions futures (UE6, CesiumJS
web, apps mobiles offline-first) sont des consommateurs du mesh,
jamais des porteurs d'autorité ou de source de vérité (principe
fondateur RFC-0035 §2.3). Interface : `IRenderClient`. Détail de la
neutralité UE6 : §13.

---

## 4. Interfaces contractuelles du mesh

Toute évolution d'une de ces interfaces requiert une RFC (P-MESH-07,
règle constitutionnelle CON-007). Les signatures ci-dessous sont
conceptuelles — la spécification technique détaillée (types, schémas)
relève d'un livrable de spécification distinct, non de ce document
d'architecture.

### 4.1 `IMeshNode` — contrat commun à tout nœud du mesh

```
IMeshNode
├── node_id: identifiant unique et stable du nœud
├── node_kind: ZONE | SPECIALIZED | ORCHESTRATOR
├── register()      : s'annonce au service discovery
├── deregister()    : se retire proprement
├── heartbeat()     : signal de vie périodique
├── health_status() : état de santé exposé à l'orchestrateur
└── audit_log()     : accès en écriture au journal d'audit (append-only)
```

### 4.2 `IZoneServer` (étend `IMeshNode`)

```
IZoneServer
├── zone_boundary: géométrie de la zone d'autorité courante
├── accept_authority(entity_ref, from_node)   : accepte le transfert entrant
├── release_authority(entity_ref, to_node)    : cède le transfert sortant
├── query_entities_in_view(frustum)           : réplication par pertinence
└── report_load()                             : métrique consommée par l'orchestrateur
```

### 4.3 `ISpecializedServer` (étend `IMeshNode`)

```
ISpecializedServer
├── entity_types: liste des types d'entités sous autorité
├── accept_authority(entity_ref, from_node)
├── release_authority(entity_ref, to_node)
└── invoke_engine(engine_name, payload)   : délégation à un moteur GSIE (livrable 203)
```

### 4.4 `IAuthorityGraph`

```
IAuthorityGraph
├── resolve(entity_ref) → (zone_authority, type_authority)
├── resolve_conflict(zone_authority, type_authority) → autorité effective
├── register_transfer(entity_ref, from_node, to_node, reason)
└── history(entity_ref) → journal bitemporel des autorités passées
```

Règle de résolution de conflit (P-MESH-03) : l'autorité **zone** est
primaire pour toute décision de rendu spatial et de continuité de
navigation ; l'autorité **type** est primaire pour toute décision
relevant du domaine fonctionnel du serveur spécialisé (simulation,
apprentissage). En cas de désaccord non couvert par cette règle, la
priorité documentée par défaut est **zone > type**, et tout écart doit
être tracé (DEC-xxxxxx) car il constitue une exception structurante.

### 4.5 `IPersistenceLayer`

```
IPersistenceLayer
├── commit(entity_state)          : écriture validée bitemporelle
├── read(entity_ref, as_of)       : lecture à un instant donné
├── subscribe(zone_or_type)       : flux de changement (base du Replication Graph)
└── audit_append(mesh_event)      : journal d'audit immuable du mesh
```

### 4.6 `IRenderClient`

```
IRenderClient
├── connect_to_mesh(authority_graph_endpoint)
├── receive_stream(zone_or_type, relevance_filter)
├── request_handoff_notice()      : reçoit les transferts en cours pour lissage visuel
└── report_viewport(frustum, operator_position)  : entrée du Replication Graph
```

`IRenderClient` est délibérément pauvre en dépendances Unreal : aucune
classe UE5.8/UE6 n'apparaît dans le contrat. L'implémentation actuelle
(Hub UE5.8) satisfait ce contrat via un adaptateur, cf. §13.

---

## 5. Relation avec les 14 moteurs GSIE

Le Server Meshing ne remplace aucun moteur et ne modifie aucun contrat
d'interface de moteur existant (`GSIE/ENGINES/<NOM>_ENGINE/README.md`).
Les serveurs spécialisés sont des **hôtes d'exécution** pour les
moteurs, pas une nouvelle couche de raisonnement. La communication
inter-moteurs continue de suivre le livrable 203. Un serveur
spécialisé Simulation, par exemple, héberge le Simulation Engine et
consulte le Reasoning Engine via les contrats déjà documentés — le
mesh ajoute une couche de distribution physique, pas une nouvelle
sémantique de communication.

---

## 6. Protocole de transfert d'autorité (handoff)

Séquence nominale de transfert d'une entité du serveur de zone A vers
le serveur de zone B (franchissement de frontière spatiale) :

1. **Détection** — le serveur A détecte qu'une entité approche ou
   franchit sa frontière de zone (position, ou décision de
   l'orchestrateur suite à redécoupage §8).
2. **Pré-annonce** — A notifie l'orchestrateur et B (`IZoneServer.accept_authority`
   en mode « proposé ») avant tout transfert effectif.
3. **Réplication de l'état** — A écrit l'état courant de l'entité dans
   `IPersistenceLayer.commit()`. Aucun transfert n'a lieu tant que
   cette écriture n'est pas confirmée (P-MESH-02).
4. **Confirmation de B** — B lit l'état via `IPersistenceLayer.read()`,
   confirme sa capacité à assumer l'autorité (`accept_authority`
   validé).
5. **Bascule du graphe d'autorité** — `IAuthorityGraph.register_transfer()`
   enregistre le nouveau propriétaire avec horodatage bitemporel et
   motif du transfert.
6. **Notification aux clients de rendu** — les clients abonnés à
   l'entité (`IRenderClient.request_handoff_notice`) reçoivent un
   signal de transfert pour lisser l'affichage (aucune coupure
   visible, P-MESH-01).
7. **Libération de A** — A appelle `release_authority()`, cesse d'être
   source pour cette entité.
8. **Journalisation** — l'ensemble de la séquence est écrit dans le
   journal d'audit du mesh (`audit_append`), avec identifiant
   traçable unique (P-MESH-06).

En cas d'échec à toute étape 2 à 6, le transfert est annulé et A
conserve l'autorité (règle de sécurité : l'autorité ne change jamais
tant que la persistance n'a pas confirmé le nouvel état).

---

## 7. Réplication par pertinence (Replication Graph adapté)

Chaque client de rendu déclare son point de vue (`report_viewport`) :
position opérateur, direction, distance de rendu. Le serveur de zone
ne réplique que les entités visibles ou interagissantes dans ce
périmètre, avec une marge de préchargement. Contrairement à Star
Citizen, la pertinence n'est pas seulement géométrique : une entité
peut être répliquée parce qu'elle est **scientifiquement pertinente**
pour l'opérateur (front de feu actif, alerte en cours) même hors
frustum strict — ceci découle de P-MESH-08 (subordination à la
connaissance).

---

## 8. Partitionnement spatial dynamique

La grille de zones n'est pas figée. L'orchestrateur redécoupe les
zones selon des métriques de charge (activité de simulation, nombre
d'opérateurs, alertes actives — P-MESH-04). Un redécoupage :

- ne peut jamais interrompre une entité en cours de handoff ;
- est toujours précédé d'une pré-annonce aux serveurs concernés ;
- est toujours journalisé (§10) avec la métrique déclenchante ;
- respecte une granularité minimale documentée pour éviter les
  oscillations (anti-flapping), dont le seuil est un paramètre
  opérationnel, pas architectural.

---

## 9. Service discovery des nœuds

Chaque nœud (`IMeshNode`) s'annonce à un registre tenu par
l'orchestrateur au démarrage (`register()`) et émet un battement de
vie périodique (`heartbeat()`). L'absence de battement au-delà d'un
délai configuré déclenche une procédure de reprise (§10.2). Le
registre lui-même est persisté (extension de `IPersistenceLayer`) pour
survivre au redémarrage de l'orchestrateur — l'orchestrateur n'est pas
davantage une source de vérité que les serveurs de zone.

---

## 10. Gestion des partitions réseau et mode dégradé

### 10.1 Position CAP

Le mesh privilégie **cohérence** sur disponibilité pour toute écriture
d'autorité (le graphe d'autorité ne doit jamais avoir deux propriétaires
simultanés confirmés pour une même entité). Il privilégie
**disponibilité** pour la lecture par les clients de rendu, avec
indication explicite de fraîcheur (dernière confirmation connue) en
cas de partition.

### 10.2 Mode dégradé

Si un serveur de zone perd la connectivité à la couche de persistance,
il :

- cesse d'accepter de nouveaux transferts d'autorité entrants ;
- continue de servir en lecture les données déjà répliquées, marquées
  comme potentiellement obsolètes ;
- tente une reconnexion périodique ;
- à la reconnexion, réconcilie son état local avec la couche de
  persistance avant de redevenir éligible à l'autorité (cohérence
  avant disponibilité).

Si l'orchestrateur perd un serveur de zone (heartbeat expiré), il
déclenche une reprise d'autorité par un autre serveur disponible pour
la zone concernée, selon le protocole de handoff (§6), initié non par
le serveur défaillant mais par l'orchestrateur lui-même à partir du
dernier état confirmé en persistance.

---

## 11. Sécurité

- **mTLS inter-nœuds** : toute communication entre nœuds du mesh
  (serveurs de zone, serveurs spécialisés, orchestrateur, couche de
  persistance) est authentifiée mutuellement par certificat. Un nœud
  sans certificat valide n'est pas accepté par le service discovery.
- **Authentification opérateurs** : les clients de rendu s'authentifient
  auprès du mesh avec le mécanisme JWT déjà en place (ADR-007, API
  v6.2), sans duplication de schéma d'authentification.
- **Séparation des rôles** : un client de rendu ne peut jamais écrire
  directement dans la couche de persistance ni modifier le graphe
  d'autorité — il consomme des flux et transmet des requêtes via
  l'API GSIE existante, jamais via un canal mesh direct.

---

## 12. Observabilité

- **Métriques mesh** : charge par zone, latence de handoff, nombre de
  redécoupages, taux de rejet de transfert.
- **Traçage distribué** : chaque transfert d'autorité et chaque
  requête inter-nœuds porte un identifiant de corrélation propagé de
  bout en bout, exploitable par les outils d'observabilité déjà en
  place pour l'API GSIE.
- **Journal d'audit** : append-only, persisté (§3.4), couvrant
  transferts d'autorité, redécoupages, création/destruction de nœuds
  (P-MESH-06). Ce journal fait partie du jumeau numérique — il n'est
  pas un simple log opérationnel effaçable.

---

## 13. Relation avec l'existant

| Élément existant | Relation avec le mesh |
|---|---|
| API GSIE (FastAPI, ADR-007) | Reste le point d'entrée métier pour les clients légers et les opérations CRUD. Le mesh consomme la même couche de persistance, sans court-circuiter l'API pour les écritures qui relèvent de son périmètre. |
| GSIE-Net (RFC-0003) | Le mesh est une évolution de l'**infrastructure serveur**. GSIE-Net reste le modèle de référence pour l'offline-first des nœuds terminaux (P-MESH-05) ; le mesh ne le remplace pas. |
| Métamodèle v6.2 (RFC-0011) | Source de vérité inchangée. Le graphe d'autorité et le journal d'audit sont des extensions du même métamodèle bitemporel, pas un second schéma. |
| Les 14 moteurs GSIE | Hébergés par les serveurs spécialisés sans changement de contrat d'interface (§5). |
| Hub UE5.8 (livrable 211) | Devient une implémentation de `IRenderClient` via adaptateur, sans changement de son statut de client de rendu non-source-de-vérité (déjà acté, ADR-001 livrable 208). |

---

## 14. Cible UE6 — neutralité de moteur de rendu

Aucune interface du mesh (§4) ne référence de type ou de dépendance
Unreal Engine. L'implémentation actuelle du client de rendu (Hub
UE5.8) satisfait `IRenderClient` via un adaptateur situé dans la
couche applicative du Hub, pas dans le contrat du mesh. Une future
implémentation UE6 — ou CesiumJS web — satisferait le même contrat
sans modification du mesh. Cette neutralité est une conséquence directe
de P-MESH-07 (modularité) et de la décision Fondateur « compatibilité
UE6 anticipée, pas de dépendance hard » (GSIE-DIR-0012).

---

## 15. Décisions à tracer

Ce document ne crée pas de nouvelle décision structurante au-delà de
DEC-000053 (déjà actée). Les points suivants devront faire l'objet
d'une décision explicite avant implémentation, au moment où ils
deviendront actionnables :

- Choix technologique du transport inter-nœuds (à documenter en ADR
  lors du prototype v1, extension multi-régions).
- Seuil de granularité anti-flapping du partitionnement dynamique
  (paramètre opérationnel, DEC-xxxxxx au moment de sa fixation).
- Règle de résolution de conflit zone/type si un écart au principe
  « zone > type » (§4.4) s'avère nécessaire.

---

## 16. Ce que ce document n'est pas

- Ce n'est pas une spécification technique détaillée (types de
  données, schémas de message) — celle-ci relève d'un livrable de
  spécification distinct, à produire au moment de l'implémentation.
- Ce n'est pas un engagement de calendrier — voir
  `SERVER_MESHING_ROADMAP.md`.
- Ce n'est pas une autorisation de modifier un contrat de moteur
  existant — toute modification de ce type reste soumise à RFC.
