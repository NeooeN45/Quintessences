# GSIE Territorial Mesh — Architecture cible

| Champ | Valeur |
|---|---|
| **Livrable** | Architecture cible long terme — GSIE Territorial Mesh |
| **Phase** | 2 — Architecture (production anticipée en Phase 4) |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 |
| **Directive** | GSIE-DIR-0013 |

---

## 1. Mission

Décrire l'architecture cible long terme du GSIE Territorial Mesh :
l'organisation logique, administrative et opérationnelle du territoire
sur laquelle s'appuie le jumeau numérique environnemental fédéré, en
complémentarité stricte avec le GSIE Server Meshing (RFC-0035,
`SERVER_MESHING_TARGET.md`).

Ce document ne redéfinit aucun contrat d'interface du Server Meshing.
Il définit les contrats propres au Territorial Mesh et leurs points de
jonction avec l'existant.

---

## 2. Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                  NATIONAL CONTROL PLANE (NCP)                    │
│   Carte territoriale maîtresse · Politiques de gouvernance       │
│   Fédération des RCH · Supervision globale · Pas de calcul métier│
└───────────────────────────────┬────────────────────────────────┬─┘
                                │                                │
                ┌───────────────▼───────────────┐  ┌─────────────▼──────────────┐
                │  REGIONAL COORDINATION HUB     │  │  REGIONAL COORDINATION HUB  │
                │  Nouvelle-Aquitaine            │  │  (autre région, ultérieur)  │
                │  Pool de calcul régional        │  │                              │
                │  Coordination inter-DOD        │  │                              │
                └──────┬───────────────┬─────────┘  └──────────────────────────────┘
                       │               │
        ┌──────────────▼───┐   ┌───────▼──────────┐
        │  DOD Charente    │   │  DOD Deux-Sèvres │
        │  (16)            │   │  (79)            │
        │  Autorité métier │   │  Autorité métier │
        │  Cellules actives│   │  Cellules actives│
        │  State Fabric dép│   │  State Fabric dép│
        │  Edge nodes      │   │  Edge nodes      │
        └──────┬───────────┘   └──────┬───────────┘
               │                      │
     ┌─────────▼─────────┐  ┌─────────▼─────────┐
     │ Territoire Opér.  │  │ Territoire Opér.  │
     │ (massif, DFCI,    │  │ (bassin versant)  │
     │  bassin versant)  │  │                    │
     └─────────┬─────────┘  └─────────┬─────────┘
               │                      │
     ┌─────────▼─────────┐  ┌─────────▼─────────┐
     │ Cellule Spatiale   │  │ Cellule Spatiale   │
     │ (Server Meshing)   │  │ (Server Meshing)   │
     └─────────┬─────────┘  └─────────┬─────────┘
               │                      │
     ┌─────────▼─────────┐  ┌─────────▼─────────┐
     │ Sous-cellule       │  │ Sous-cellule       │
     │ de Simulation      │  │ de Simulation      │
     └────────────────────┘  └────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│           GSIE STATE FABRIC FÉDÉRÉ (transverse à tous niveaux)   │
│  PostgreSQL/PostGIS (ADR-011) · Réplication logique cross-région │
│  Cache Redis cluster · Capsules territoriales signées (ADR-008)  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│           BUS D'ÉVÉNEMENTS FÉDÉRÉ (transverse à tous niveaux)    │
│  Redis Pub/Sub par niveau · Routage inter-niveaux                │
│  Outbox/Inbox (ADR-005) pour durabilité                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Composants détaillés

### 3.1 National Control Plane (NCP)

**Responsabilités**
- Maintenir la carte territoriale maîtresse (référentiel des régions,
  départements, territoires opérationnels et leur correspondance avec
  les frontières scientifiques, P-TERR-08).
- Définir et diffuser les politiques de gouvernance applicables à
  l'ensemble du territoire (rétention des données, niveaux de
  criticité, seuils d'escalade en crise).
- Fédérer les Regional Coordination Hub : réconciliation des
  référentiels, supervision de disponibilité, agrégation d'indicateurs
  non sensibles.

**Interfaces**
- `ITerritorialMap` (lecture/écriture du référentiel territorial).
- Interface de supervision en lecture seule vers les RCH (pas
  d'écriture directe dans un DOD).

**État** : le NCP expose lui aussi un état opérationnel, mais avec une
sémantique de disponibilité du plan de contrôle et non de charge métier.
Ses états Froid, Chaud, Opérationnel et Crise sont définis dans le
document NCP. Il agrège les états de ses RCH sans devenir un point de
passage obligatoire du fonctionnement régional (contrainte
anti-paternelle : pas de serveur national monolithique).

### 3.2 Regional Coordination Hub (RCH)

**Responsabilités**
- Coordonner les DOD de sa région : arbitrage de ressources entre
  départements avant sollicitation du NCP.
- Maintenir un pool de calcul régional mutualisé, activable/désactivable
  selon l'état agrégé des DOD.
- Répliquer les données chaudes (State Fabric) à l'échelle régionale.
- Orchestrer le cycle de disponibilité des DOD selon les politiques
  applicables et leur état opérationnel (P-TERR-04). Cette orchestration
  ne modifie pas directement une décision métier du DOD : le RCH demande,
  autorise ou planifie une transition administrative, tandis que le DOD
  reste l'autorité de sa déclaration métier (P-TERR-07).

**Pool de calcul**
Le pool de calcul régional n'est pas une association rigide RCH →
machine. Il s'agit d'une capacité négociée dynamiquement avec le
Server Meshing (RFC-0035) : le RCH exprime des besoins par territoire
opérationnel, l'orchestrateur de mesh (ADR-016) alloue les cellules
spatiales correspondantes.

**Interfaces**
- `IRegionalPool` (négociation de capacité de calcul).
- Interface de coordination vers les DOD (activation, désactivation,
  remontée d'état).

**État** : possède un état opérationnel agrégé (froid, chaud,
opérationnel, crise), reflet pondéré des états de ses DOD, sans
pouvoir en écraser un individuellement.

### 3.3 Departmental Operational Domain (DOD)

**Responsabilités**
- Détenir l'autorité métier unique sur son périmètre départemental ou
  assimilé (P-TERR-07).
- Superviser les cellules actives de son territoire.
- Maintenir un State Fabric départemental (extrait cohérent du State
  Fabric fédéré).
- Héberger des edge nodes pour le fonctionnement offline
  (P-TERR-06).

**Autorité métier**
Le DOD est l'unique périmètre où une décision métier structurante
(déclenchement d'alerte, changement d'état opérationnel local,
validation d'une recommandation issue des moteurs GSIE) peut être
prise à l'échelle départementale. Aucun autre niveau (RCH, NCP) ne
peut se substituer à cette autorité (contrainte anti-paternelle : pas
d'autorités concurrentes sur le même périmètre).

**Edge**
Les edge nodes du DOD embarquent des capsules territoriales signées
(ADR-008) leur permettant de fonctionner en autonomie complète en cas
de perte de connectivité avec le RCH, avec synchronisation différée au
retour de connectivité (modèle Git, RFC-0003 §4).

**Interfaces**
- `IDepartmentalAuthority` (décision métier, changement d'état local).
- Interface d'accès au State Fabric départemental.

**État** : état opérationnel propre (froid, chaud, opérationnel,
crise), déclaré par le DOD ou par un opérateur habilité dans son
périmètre. Une automatisation peut proposer ou déclencher une alerte,
mais toute transition métier structurante reste attribuable et
révocable par l'autorité humaine compétente.

### 3.4 Dynamic Spatial Cells

Cœur du Server Meshing (RFC-0035, ADR-010 à ADR-019). Le Territorial
Mesh les rattache à un Territoire Opérationnel donné (P-TERR-08) :

- **Allumage/extinction** : piloté par la charge (Server Meshing) et
  par l'état opérationnel du Territoire Opérationnel et du DOD parent
  (Territorial Mesh) — les deux signaux sont combinés par
  l'orchestrateur de mesh.
- **Handoff** : transfert d'autorité d'exécution entre cellules,
  transparent pour la hiérarchie territoriale (P-TERR-02).
- **Réplication par pertinence** : inchangée par rapport à RFC-0035 ;
  la pertinence peut être pondérée par l'état de crise du Territoire
  Opérationnel.

### 3.5 GSIE State Fabric fédéré

**PostgreSQL/PostGIS** reste la source de vérité à chaque niveau
disposant d'une autorité (DOD, RCH) — cohérent avec ADR-011. La
fédération repose sur :

- **Réplication logique cross-région** : chaque RCH réplique de
  manière asynchrone les données chaudes de ses DOD ; le NCP ne
  réplique pas l'intégralité des données régionales, uniquement des
  agrégats non sensibles (contrainte anti-paternelle : pas d'envoi de
  toutes les données au niveau national).
- **Cache Redis cluster** : lectures chaudes à chaque niveau,
  invalidé par les événements du bus fédéré (§3.6).
- **Capsules territoriales signées (ADR-008)** : unité de transport
  hors-ligne du State Fabric vers un edge node ou un DOD isolé.

### 3.6 Bus d'événements fédéré

- **Redis Pub/Sub par niveau** : chaque DOD, RCH et le NCP disposent
  de leur propre bus local, cohérent avec ADR-013 (Server Meshing).
- **Fédération par routage inter-niveaux** : un routeur dédié propage
  les événements pertinents d'un niveau à l'autre (DOD → RCH → NCP),
  filtré selon les politiques de gouvernance du NCP (§3.1) — jamais un
  flux brut complet.
- **Outbox/Inbox (ADR-005)** : conserve les événements critiques en
  attente lors d'une partition et permet leur rejeu ordonné et
  idempotent au retour de connectivité. Le contrat vise une livraison
  au moins une fois avec effets métier effectivement uniques, et non une
  garantie exactly-once de bout en bout.

---

## 4. Interfaces

| Interface | Porteur | Rôle |
|---|---|---|
| `ITerritorialMap` | NCP | Lecture/écriture du référentiel territorial (régions, départements, territoires opérationnels, correspondances scientifiques) |
| `IRegionalPool` | RCH | Négociation de capacité de calcul avec le Server Meshing, coordination inter-DOD |
| `IDepartmentalAuthority` | DOD | Décision métier départementale, changement d'état opérationnel local, activation des cellules |
| `IStateFabric` | Tous niveaux | Accès au State Fabric fédéré (lecture, écriture, réplication, capsule) |
| `IFederatedBus` | Tous niveaux | Publication/souscription d'événements, routage inter-niveaux, outbox/inbox |

Toute évolution de ces interfaces requiert une RFC, conformément à
CON-007 et à la règle de modularité déjà appliquée au Server Meshing
(P-MESH-07).

---

## 5. États opérationnels

| État | NCP | RCH | DOD | Cellule Spatiale (Server Meshing) |
|---|---|---|---|---|
| **Froid** | Plan de contrôle indisponible ; les niveaux inférieurs appliquent le mode dégradé | Pool de calcul régional désactivé, aucun DOD sollicité | Composant hors service, aucune cellule active, données persistées uniquement | Éteinte |
| **Chaud** | Registre et politiques disponibles, supervision non garantie | Pool de calcul minimal réservé, DOD en veille surveillée | Activé, calcul minimal, edge nodes synchronisés | Allumée, calcul minimal, prête à monter en charge |
| **Opérationnel** | Fédération et supervision normales | Coordination active des DOD, arbitrage de charge normal | Charge normale, simulation active, autorité métier pleinement exercée | Charge normale, simulation active |
| **Crise** | Arbitrage et supervision inter-régionaux prioritaires, sans calcul métier direct | Priorité aux DOD en crise, réallocation du pool régional | Charge maximale, priorité aux services critiques (incendie, inondation) | Charge maximale, réplication par pertinence renforcée sur la zone de crise |

---

## 6. Contrat des états opérationnels

Les quatre états sont communs aux nœuds territoriaux, mais leur
sémantique dépend du niveau. Les transitions nominales sont
`Froid → Chaud → Opérationnel → Crise`, puis `Crise → Opérationnel →
Chaud → Froid` après résolution et validation. Un passage direct vers
Froid depuis Crise nécessite un arrêt contrôlé et une décision auditée.

- Le NCP exprime la disponibilité de son plan de contrôle ; il ne déduit
  pas l'état métier d'un DOD.
- Le RCH orchestre la disponibilité de ses DOD et la capacité régionale ;
  il ne remplace pas la déclaration métier d'un DOD.
- Le DOD déclare et clôture les crises de son périmètre, sous réserve
  des politiques d'escalade ; une automatisation ne fait que proposer ou
  déclencher une alerte traçable.
- La cellule suit le cycle d'exécution du Server Meshing ; l'autorité
  territoriale reste celle du DOD et les handoffs sont protégés par un
  epoch de fencing.

Toute transition doit contenir l'état précédent, l'état suivant,
l'acteur, le motif, l'epoch d'autorité, l'heure métier et l'heure de
transaction. Une transition invalide est rejetée et auditée.

---

## 7. Relation avec le Server Meshing

| Dimension | Server Meshing (RFC-0035) | Territorial Mesh (présent document) | Point de jonction |
|---|---|---|---|
| Autorité d'exécution | Hybride zone + type (ADR-010) | N/A — non concerné | La zone d'autorité d'exécution est bornée par le Territoire Opérationnel |
| Allocation de ressources | Orchestrateur de mesh (ADR-016), métriques de charge | États opérationnels (P-TERR-04) comme signal d'entrée | `IRegionalPool` transmet l'état territorial à l'orchestrateur |
| Persistance | PostgreSQL source de vérité (ADR-011) | Fédération cross-région du même socle (P-TERR-05) | `IStateFabric` étend ADR-011 sans le modifier |
| Bus | Redis Pub/Sub inter-nœuds (ADR-013) | Redis Pub/Sub fédéré inter-niveaux (§3.6) | `IFederatedBus` route entre le bus de mesh et le bus territorial |
| Offline | Mode dégradé par partition réseau (ADR-019) | Capsules territoriales par DOD/edge (P-TERR-06) | Capsule ADR-008 réutilisée par les deux chantiers |
| Sécurité | mTLS inter-nœuds (ADR-017) | RBAC territorial (§9) au-dessus du même canal mTLS | Le canal mTLS est partagé ; l'autorisation territoriale est une couche supplémentaire |
| Compatibilité UE6 | Interfaces abstraites (ADR-015) | Aucune dépendance directe à un client de rendu | Le Territorial Mesh n'introduit aucune contrainte supplémentaire sur UE6 |

Aucun contrat d'interface du Server Meshing n'est modifié par le
Territorial Mesh. Toute évolution conjointe nécessaire fera l'objet
d'une RFC commune.

---

## 8. Relation avec l'existant

- **RFC-0003 (GSIE-Net)** : le modèle offline-first et de
  synchronisation par retour de connectivité s'applique tel quel à
  chaque niveau territorial (§3.3, §5 « Froid »).
- **RFC-0029 (organisation physique des données)** : les règles
  d'organisation physique des données sont respectées par la
  fédération du State Fabric (§3.5) ; aucune redondance de stockage
  non justifiée n'est introduite.
- **ADR-001 à ADR-009** : ADR-001 (persistance PostgreSQL), ADR-002
  (bitemporalité), ADR-005 (outbox/inbox) et ADR-008 (capsule
  territoriale signée) sont réutilisés tels quels, étendus à la
  fédération multi-niveaux sans modification de leur contrat.
- **Modèle administratif existant** (`GSIE/API/src/gsie_api/infrastructure/models/business.py`) :
  `AdministrativeUnitModel` représente actuellement une hiérarchie
  forestière/juridique et cadastrale. Il n'est pas le modèle direct de la
  hiérarchie France → Région → Département. Une spécification dédiée doit
  décider d'une entité `TerritorialAdministrativeUnit` distincte ou d'une
  correspondance explicite avec ce modèle avant le prototype, sans fusion
  forcée des référentiels (P-TERR-08, ADR-028).
- **GeoSylva** : application cliente consommant le State Fabric
  départemental via `IStateFabric`, sans dépendance à la structure
  interne du Territorial Mesh.
- **Hub (Centre de Commandement UE5.8)** : client de rendu consommant
  l'état territorial agrégé (P-TERR-09) ; ne calcule ni ne décide de
  l'état opérationnel d'un composant.

---

## 9. Sécurité

- **mTLS (ADR-017)** : canal chiffré et authentifié mutuellement entre
  tous les niveaux (DOD ↔ RCH ↔ NCP), réutilisant l'infrastructure de
  certificats déjà cadrée par le Server Meshing.
- **RBAC territorial** : les rôles d'accès sont scopés par périmètre
  territorial (un opérateur habilité pour la Charente n'a pas
  automatiquement accès aux données brutes des Deux-Sèvres), avec des
  rôles transverses explicites pour les fonctions de coordination
  régionale et nationale.
- **Audit** : toute décision de changement d'état, toute activation de
  cellule, tout accès inter-niveaux est journalisé et attribuable à un
  territoire et à un rôle (P-TERR-10), conformément à CON-005 et
  CON-010.

---

## 10. Modes dégradés

- **Offline-first** : un DOD isolé (perte de connectivité avec son
  RCH) continue de fonctionner en autonomie sur son edge node et son
  State Fabric départemental local, avec des capsules territoriales
  signées (ADR-008) comme contexte de mission et un journal local signé
  pour les observations produites en différé.
- **Panne régionale** : si un RCH devient indisponible, ses DOD
  continuent de fonctionner en autorité locale pleine (P-TERR-07) ;
  seule la coordination inter-départementale et l'accès au pool de
  calcul régional mutualisé sont dégradés jusqu'au rétablissement du
  RCH. Une redondance de RCH n'est pas incluse dans le prototype v0 et
  devra faire l'objet d'une décision d'architecture et de tests dédiés
  avant d'être ajoutée à la cible.
- **Crise** : l'état de crise déclenche une priorisation explicite des
  services critiques (incendie, inondation) à tous les niveaux
  concernés, avec réallocation du pool de calcul régional et
  renforcement de la réplication par pertinence sur la zone de crise,
  sans jamais retirer l'autorité métier au DOD concerné.

---

## 11. Glossaire

| Terme | Définition |
|---|---|
| **NCP** | National Control Plane |
| **RCH** | Regional Coordination Hub |
| **DOD** | Departmental Operational Domain |
| **Territoire Opérationnel** | Périmètre de pertinence scientifique ou opérationnelle (massif, DFCI, bassin versant) ou administratif |
| **Cellule Spatiale** | Unité d'exécution du Server Meshing (RFC-0035) |
| **Sous-cellule de Simulation** | Granularité fine de calcul pour la simulation active |
| **État opérationnel** | Froid / chaud / opérationnel / crise |
| **State Fabric** | Couche de persistance fédérée PostgreSQL/PostGIS + cache + capsules |
| **Capsule territoriale** | Paquet de données signé permettant le fonctionnement offline (ADR-008) |
| **Bus fédéré** | Ensemble des bus Redis Pub/Sub par niveau, reliés par routage inter-niveaux |
