# RFC-0036 — GSIE Territorial Mesh : organisation logique, administrative et opérationnelle du territoire

| Champ | Valeur |
|---|---|
| **ID** | RFC-0036 |
| **Livrable** | Vision et cadrage architectural — chantier GSIE Territorial Mesh |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation (anticipation Phase 5) |
| **Auteur** | Camille Perraudeau (Fondateur) — proposition instruite par l'Architecte GSIE |
| **Date d'ouverture** | 2026-08-06 |
| **Lois fondatrices** | GSIE-CON-001 (le forestier décide), GSIE-CON-002 (IA assiste, ne décide pas), GSIE-CON-003 (connaissance avant code), GSIE-CON-004 (décisions explicables), GSIE-CON-005 (connaissance traçable), GSIE-CON-007 (modularité), GSIE-CON-010 (évolution sans perte d'historique) |
| **Constitutions liées** | Technique (T-1 responsabilité unique, T-2 couplage faible, T-3 interfaces contractuelles, T-4 pas d'autorité concurrente, T-5 persistance externe, T-6 configuration sans redéploiement, T-7 observabilité, T-8 offline-first, T-9 sécurité par conception, T-10 traçabilité) ; Scientifique (S-1 sourçabilité, S-2 niveaux de preuve, S-3 reproductibilité, S-4 provenance, S-5 incertitude explicite, S-6 frontières scientifiques vs administratives, S-7 primauté de la connaissance) |
| **RFC de référence** | RFC-0003 (GSIE-Net, offline-first), RFC-0029 (organisation physique des données), RFC-0035 (GSIE Server Meshing) |
| **Directive liée** | GSIE-DIR-0013 (à activer) — supplée GSIE-DIR-0012 sans l'invalider |
| **Décision d'ouverture** | DEC-000054 |
| **Impact** | `GSIE/ARCHITECTURE/`, `05_SPECIFICATIONS/`, `ROADMAP.md`, `PROJECT_MEMORY.md`, `CHANGELOG.md`, futures infrastructures de déploiement, futures applications clientes |

---

## 1. Problème

Le chantier **GSIE Server Meshing** (RFC-0035, GSIE-DIR-0012, DEC-000053)
répond à une question précise : *comment répartir dynamiquement les
ressources de calcul et de rendu d'un jumeau numérique environnemental
distribué ?* Il introduit une autorité hybride zone + type, une
réplication par pertinence, un orchestrateur de mesh et des interfaces
abstraites compatibles UE6.

Ce cadre est nécessaire mais **insuffisant** pour organiser
l'exploitation réelle du système à l'échelle d'un territoire national.
Quatre lacunes structurelles apparaissent dès que l'on projette le
Server Meshing sur un déploiement multi-régional et multi-départemental :

1. **Pas de hiérarchie administrative et opérationnelle.** Le Server
   Meshing raisonne en « serveurs de zone » sans les inscrire dans une
   structure de gouvernance correspondant aux échelons de décision
   réels (région, département, territoire opérationnel). Il n'existe
   pas de notion de qui a autorité **administrative** sur quel
   périmètre, indépendamment de qui exécute le calcul.
2. **Pas d'états opérationnels du territoire.** Le Server Meshing gère
   l'allocation de ressources par charge instantanée, mais ne modélise
   pas des états métiers explicites (un département en veille
   hivernale, un massif en alerte DFCI, une région en gestion de
   crise) qui doivent piloter *à la fois* la gouvernance et
   l'allocation.
3. **Pas de pool de calcul régional intermédiaire.** L'architecture
   actuelle oppose des « serveurs de zone » à une couche de
   persistance globale, sans échelon intermédiaire capable de
   fédérer et d'arbitrer entre plusieurs départements d'une même
   région avant de solliciter le niveau national.
4. **Pas de fédération inter-niveaux du bus d'événements et de l'état.**
   Le Server Meshing spécifie un bus Redis Pub/Sub pour la
   communication inter-nœuds (ADR-013, `SERVER_MESHING_ADR.md`) à
   l'échelle d'un mesh unique, mais ne définit pas comment ce bus se
   fédère entre échelons administratifs distincts (départemental,
   régional, national) ni comment la réplication logique PostgreSQL
   franchit ces frontières.

Le **GSIE Territorial Mesh** comble ces lacunes en ajoutant une couche
**orthogonale** : elle définit *qui a autorité sur quel territoire, à
quel niveau administratif, dans quel état opérationnel* — indépendamment
de *quel serveur exécute quel calcul à cet instant* (Server Meshing).

## 2. Vision

Le GSIE Territorial Mesh organise le jumeau numérique environnemental
comme un système **fédéré, persistant et distribué**, structuré selon
la géographie administrative et opérationnelle réelle du territoire
français, sans jamais figer une association rigide entre un échelon
administratif et une machine physique.

Un département n'est pas un serveur. Une région n'est pas un cluster.
Le Territorial Mesh décrit une **hiérarchie logique de gouvernance et
d'autorité**, dont l'exécution physique est déléguée au Server Meshing
(RFC-0035). Les deux chantiers sont complémentaires et ne se
substituent pas l'un à l'autre (voir §6).

## 3. Principes fondateurs

### P-TERR-01 — Hiérarchie configurable

Le territoire est organisé selon une hiérarchie à six niveaux :
national, régional, départemental, territoire opérationnel, cellule
spatiale, sous-cellule de simulation (voir §4). Cette hiérarchie est
**configurable** : elle n'est pas figée dans le code, elle est décrite
par des données de configuration territoriale versionnées, afin de
pouvoir évoluer (nouvelle région pilote, fusion de départements,
nouveau découpage DFCI) sans RFC pour chaque changement de périmètre.

### P-TERR-02 — Orthogonalité au Server Meshing

Le Territorial Mesh répond à *qui a autorité et sous quel état*
(gouvernance). Le Server Meshing répond à *quel serveur exécute quel
calcul à cet instant* (exécution). Ces deux préoccupations sont
séparées par conception (T-1, T-2). Un même Regional Coordination Hub
peut voir ses cellules spatiales sous-jacentes migrer d'un serveur
physique à un autre sans que l'autorité territoriale ne change.

### P-TERR-03 — Concentration dynamique par la demande, pas par la structure

Les ressources de calcul suivent les besoins opérationnels ; la
structure territoriale ne les précède pas. Un territoire opérationnel
en état de crise reçoit des ressources sans qu'il soit nécessaire de
redessiner la hiérarchie administrative. La hiérarchie territoriale
reste stable ; c'est l'état opérationnel (P-TERR-04) qui varie et qui
pilote l'allocation via le Server Meshing.

### P-TERR-04 — États opérationnels explicites

Chaque composant du Territorial Mesh (RCH, DOD, cellule) possède un
état opérationnel explicite parmi : **froid**, **chaud**,
**opérationnel**, **crise** (voir §4 de `TERRITORIAL_MESH_TARGET.md`
pour la matrice complète). L'état est une donnée de gouvernance
tracée, distincte de la charge technique mesurée par le Server
Meshing.

### P-TERR-05 — Persistance fédérée

PostgreSQL/PostGIS reste la source de vérité (ADR-011,
`SERVER_MESHING_ADR.md`), à chaque niveau où une autorité départementale
ou régionale existe. La fédération se fait par **réplication logique
cross-région** et non par une base de données monolithique nationale
(contrainte anti-paternelle : pas de serveur national centralisant
toutes les données).

### P-TERR-06 — Offline-first territorial

Le principe offline-first (T-8, RFC-0003) s'applique à chaque niveau
territorial. Les capsules territoriales signées (ADR-008,
`ADR-008-capsule-territoriale-signee.md`) permettent à un Departmental
Operational Domain ou à un edge node de fonctionner en autonomie en cas
de perte de connectivité avec le Regional Coordination Hub ou le
National Control Plane.

### P-TERR-07 — Autorité unique par périmètre

Aucun périmètre territorial ne connaît deux autorités concurrentes
(contrainte anti-paternelle). Le Departmental Operational Domain est
l'autorité métier unique sur son périmètre ; le Regional Coordination
Hub coordonne sans se substituer à cette autorité ; le National
Control Plane fédère sans exercer d'autorité métier directe.

### P-TERR-08 — Frontières scientifiques possibles

Le Territoire Opérationnel n'est pas nécessairement une frontière
administrative. Il peut correspondre à un massif forestier, une zone
DFCI ou un bassin versant (S-6). La hiérarchie territoriale
administrative (région, département) porte la gouvernance ; le
Territoire Opérationnel porte la pertinence scientifique et
opérationnelle. Les deux découpages coexistent et sont réconciliés
par une table de correspondance, jamais par une fusion forcée.

### P-TERR-09 — Subordination à la connaissance

Conformément à CON-003, CON-007 et au principe déjà acté par le Server Meshing
(P-MESH-08), Unreal Engine et tout client de rendu reflètent l'état du
Territorial Mesh, ils ne le calculent pas. Les services scientifiques
(moteurs GSIE) ne dépendent jamais d'Unreal pour fonctionner.

### P-TERR-10 — Traçabilité et gouvernance multi-niveaux

Toute décision d'activation, de désactivation ou de changement d'état
d'un composant territorial est journalisée et attribuable à un niveau
de gouvernance précis (CON-005, CON-010). L'audit est possible par
territoire, à tout niveau de la hiérarchie.

## 4. Hiérarchie territoriale

```
France (National Control Plane)
│  Carte territoriale maîtresse, politiques de gouvernance,
│  fédération des RCH, supervision globale. Aucun calcul métier.
│
└── Région (Regional Coordination Hub)               ex : Nouvelle-Aquitaine
    │  Pool de calcul régional, coordination inter-départementale,
    │  réplication régionale des données chaudes.
    │
    └── Département (Departmental Operational Domain) ex : Charente (16)
        │                                              ex : Deux-Sèvres (79)
        │  Autorité métier départementale, cellules actives,
        │  State Fabric départemental, edge nodes.
        │
        └── Territoire Opérationnel      ex : massif forestier, zone DFCI,
            │                                bassin versant
            │  Frontière scientifique ou administrative de pertinence
            │  opérationnelle (P-TERR-08).
            │
            └── Cellule Spatiale (Server Meshing, RFC-0035)
                │  Unité d'exécution du Server Meshing : allumage/
                │  extinction dynamique, réplication par pertinence.
                │
                └── Sous-cellule de Simulation
                     Granularité fine de calcul pour la simulation
                     active (incendie, propagation, croissance).
```

La frontière entre les deux chantiers se situe entre le **Territoire
Opérationnel** (gouvernance et pertinence scientifique — Territorial
Mesh) et la **Cellule Spatiale** (exécution — Server Meshing, voir §6).

## 5. Composants

### 5.1 National Control Plane (NCP)

Détient la carte territoriale maîtresse (référentiel des régions,
départements et territoires opérationnels), les politiques de
gouvernance applicables à l'ensemble du territoire, et fédère les
Regional Coordination Hub. Ne réalise aucun calcul métier : il n'est
pas un point de passage obligatoire des données, uniquement un plan de
contrôle (contrainte anti-paternelle : pas de serveur national
monolithique, pas d'envoi de toutes les données au niveau national).

### 5.2 Regional Coordination Hub (RCH)

Dispose d'un pool de calcul régional mutualisé entre ses départements,
coordonne les Departmental Operational Domain de sa région, réplique
les données chaudes à l'échelle régionale, et décide de
l'activation/désactivation des DOD selon leur état opérationnel
(P-TERR-04).

### 5.3 Departmental Operational Domain (DOD)

Porte l'autorité métier départementale — autorité unique sur son
périmètre (P-TERR-07). Héberge les cellules actives de son territoire,
un State Fabric départemental (extrait du State Fabric fédéré), et des
edge nodes pour le fonctionnement offline (P-TERR-06).

### 5.4 Dynamic Spatial Cells

Correspondent au cœur du Server Meshing (RFC-0035) : allumage/extinction
selon charge, handoff d'entités à la frontière, réplication par
pertinence. Le Territorial Mesh les rattache à un Territoire
Opérationnel et donc, transitivement, à un DOD et un RCH.

### 5.5 GSIE State Fabric fédéré

PostgreSQL/PostGIS reste la source de vérité (ADR-011). Le State Fabric
se fédère par réplication logique cross-région, s'appuie sur un cache
Redis cluster pour les lectures chaudes, et sur des capsules
territoriales signées (ADR-008) pour l'usage en edge et hors-ligne.

### 5.6 Bus d'événements fédéré

Un bus Redis Pub/Sub existe à chaque niveau (national, régional,
départemental). La fédération entre niveaux se fait par routage
inter-niveaux explicite, avec un mécanisme outbox/inbox (ADR-005,
`ADR-005-outbox-inbox.md`) garantissant la durabilité logique et le rejeu idempotent des événements
lors des changements d'état ou des ruptures de connectivité.

## 6. Relation avec le Server Meshing

| Dimension | GSIE Server Meshing (RFC-0035) | GSIE Territorial Mesh (RFC-0036) |
|---|---|---|
| Question posée | Quel serveur exécute quel calcul, à cet instant ? | Qui a autorité sur quel territoire, dans quel état ? |
| Unité de base | Cellule spatiale, sous-cellule de simulation | Région, Département, Territoire Opérationnel |
| Nature | Exécution, allocation de ressources | Gouvernance, administration, état opérationnel |
| Autorité | Hybride zone + type (P-MESH-03) | Autorité unique par périmètre (P-TERR-07) |
| Persistance | PostgreSQL source de vérité (ADR-011) | Même socle, fédéré cross-région (P-TERR-05) |
| Bus | Redis Pub/Sub inter-nœuds (ADR-013) | Redis Pub/Sub fédéré inter-niveaux (§5.6) |
| Offline | Nœuds terminaux (ADR-019) | Capsules territoriales par DOD/edge (P-TERR-06) |
| Dépendance | S'appuie sur une topologie de cellules | Fournit le cadre administratif dans lequel les cellules s'inscrivent |

Les deux chantiers sont **complémentaires et non substituables**. Le
Territorial Mesh ne redéfinit aucun contrat d'interface du Server
Meshing (ADR-010 à ADR-019) ; il les consomme.

## 7. Relation avec l'existant

- **RFC-0003 (GSIE-Net)** : le principe offline-first (T-8) et le
  modèle de synchronisation par retour de connectivité s'appliquent
  sans modification à chaque niveau territorial (P-TERR-06).
- **RFC-0029 (organisation physique des données)** : la fédération du
  State Fabric (§5.5) prolonge les règles d'organisation physique déjà
  établies, sans les contredire.
- **ADR-001 à ADR-009** (`GSIE/ARCHITECTURE/`) : la persistance
  PostgreSQL comme source de vérité (ADR-001, ADR-002), l'outbox/inbox
  (ADR-005) et les capsules territoriales signées (ADR-008) sont
  réutilisés tels quels et étendus à la fédération multi-niveaux.
- **Modèle administratif existant** (`GSIE/API/src/gsie_api/infrastructure/models/business.py`) :
  `AdministrativeUnitModel` porte actuellement une sémantique
  forestière/juridique et cadastrale (forêt domaniale, triage, parcelle).
  Il ne doit pas être étendu implicitement pour représenter France →
  Région → Département. Une spécification dédiée doit décider entre une
  entité `TerritorialAdministrativeUnit` distincte et une relation de
  correspondance explicite avec le modèle existant, conformément à
  P-TERR-08 et ADR-028, avant toute implémentation.

## 8. Périmètre du prototype v0

Le prototype v0 est circonscrit à la région **Nouvelle-Aquitaine**,
avec deux Departmental Operational Domain actifs : **Charente (16)**
et **Deux-Sèvres (79)**. Ce périmètre permet de valider la coordination
inter-départementale au sein d'un même Regional Coordination Hub sans
exposer immédiatement la fédération inter-régionale complète. Le choix
est cohérent avec le prototype mono-région du Server Meshing (Landiras,
Gironde, DEC-000053), auquel il s'ajoute sans le remplacer.

## 9. Risques principaux

Les risques structurants (complexité distribuée non justifiée, dérive
vers un serveur national monolithique, sous-estimation de la
fédération multi-niveaux, cas offline mal couverts, coûts et sécurité
par niveau) sont recensés et détaillés dans le registre dédié
`GSIE/ARCHITECTURE/TERRITORIAL_MESH_RISKS.md` (produit en statut Draft — voir
GSIE-DIR-0013 §5).

## 10. Glossaire

| Terme | Définition |
|---|---|
| **NCP** | National Control Plane — plan de contrôle national, sans calcul métier |
| **RCH** | Regional Coordination Hub — pool de calcul et coordination régionale |
| **DOD** | Departmental Operational Domain — autorité métier départementale |
| **Territoire Opérationnel** | Périmètre de pertinence scientifique ou opérationnelle, administratif ou non (massif, DFCI, bassin versant) |
| **Cellule Spatiale** | Unité d'exécution du Server Meshing (RFC-0035) |
| **État opérationnel** | Froid / chaud / opérationnel / crise — état de gouvernance d'un composant |
| **State Fabric** | Couche de persistance fédérée PostgreSQL/PostGIS + cache + capsules |
| **Capsule territoriale** | Paquet de données signé permettant le fonctionnement offline (ADR-008) |
