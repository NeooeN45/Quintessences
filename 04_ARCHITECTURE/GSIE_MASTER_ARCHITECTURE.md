# GSIE Master Architecture

| Champ | Valeur |
|---|---|
| **Livrable** | 201 — Architecture globale GSIE |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-003, GSIE-CON-007, GSIE-CON-010 |
| **Constitutions liées** | Technique (T-1 à T-10), Scientifique (S-1 à S-7) |
| **RFC de référence** | RFC-0003 (GSIE-Net) |
| **Décision d'ouverture** | DEC-000004 |

---

## 1. Mission

Décrire l'architecture technique globale de GSIE (General System
Intelligence Engine) : organisation en couches, flux de données,
principes directeurs et relation avec l'architecture distribuée
GSIE-Net (RFC-0003).

Ce document est le point d'entrée de l'architecture système. Il ne
décrit pas le détail interne de chaque moteur (voir
`09_ENGINES/*/`) ni les contrats d'interface (voir livrable 206,
`ENGINE_INTERFACE_CONTRACTS.md`). Il définit la structure qui les
contient et les contraint.

---

## 2. Vue d'ensemble du système

GSIE est un **moteur d'intelligence environnementale** modulaire,
traçable et explicable. Il n'est pas une application : les applications
(GeoSylva, GSIE-FEU, futures spécialisations) sont des **clients** du
moteur.

Le système se décompose en trois axes :

```
┌─────────────────────────────────────────────────────────────────┐
│                        ÉCOSYSTÈME QUINTESSENCES                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  GeoSylva    │  │  GSIE-FEU    │  │  Futures spécialis.  │   │
│  │  (forêt)     │  │  (incendie)  │  │  (eau, biodiv., …)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                     │               │
│         └─────────────────┼─────────────────────┘               │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  INTERFACES  │  Mobile, Web, Desktop, API  │
│                    └──────┬──────┘                              │
│                           │                                     │
│                    ┌──────▼──────────────────────────────┐     │
│                    │           MOTEUR GSIE                │     │
│                    │                                      │     │
│                    │  Cœur de raisonnement (7 moteurs)    │     │
│                    │  Moteurs domaine (5 moteurs)         │     │
│                    │  Moteurs transverses (2 moteurs)     │     │
│                    └──────┬──────────────────────────────┘     │
│                           │                                     │
│                    ┌──────▼──────────────────────┐             │
│                    │     GSIE-NET (RFC-0003)      │             │
│                    │  Synchronisation, routage,   │             │
│                    │  découverte des nœuds        │             │
│                    └──────┬──────────────────────┘             │
│                           │                                     │
│                    ┌──────▼──────────────────────┐             │
│                    │     COUCHE TRANSPORT          │             │
│                    │  LoRa, Wi-Fi, 4G/5G, satellite│             │
│                    └───────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Le moteur GSIE — 14 moteurs

Les 14 moteurs sont organisés en trois familles (voir
`09_ENGINES/README.md`) :

**Cœur de raisonnement (chaîne principale) :**

```
Evidence → Knowledge → Correlation → Reasoning → Diagnostic
→ Recommendation → Validation → Utilisateur
```

| Moteur | Responsabilité |
|---|---|
| Evidence Engine | Évaluer la qualité scientifique (niveau de preuve) de chaque connaissance entrante |
| Knowledge Engine | Centraliser et structurer les connaissances qualifiées (ontologie, graphe) |
| Correlation Engine | Croiser automatiquement les données multi-domaines |
| Reasoning Engine | Produire des conclusions par inférence explicite et auditable |
| Diagnostic Engine | Synthétiser un diagnostic stationnel/sylvicole à partir des conclusions |
| Recommendation Engine | Proposer des recommandations d'action contournables et justifiées |
| Validation Engine | Valider la conformité de toute sortie avant présentation à l'utilisateur |

**Moteurs domaine (alimentent le raisonnement) :**

| Moteur | Responsabilité |
|---|---|
| GIS Engine | Données géospatiales (parcelles, relief, hydrographie) |
| Climate Engine | Données climatiques et bioclimatiques (historiques + projections) |
| Pedology Engine | Données pédologiques (texture, pH, drainage, réserve utile) |
| Botanical Engine | Taxonomie, nomenclature et autécologie des essences |
| Forest Dynamics Engine | Croissance et dynamique des peuplements forestiers |

**Moteurs transverses :**

| Moteur | Responsabilité |
|---|---|
| Learning Engine | Amélioration continue des modèles à partir des retours terrain |
| Simulation Engine | Projection de scénarios sylvicoles long terme |

### 2.2 Spécialisations (applications clientes)

Les spécialisations sont des **clients** du moteur GSIE, jamais des
forks. Elles consomment les API du moteur et ajoutent une couche
métier propre à leur domaine :

- **GeoSylva** — application forestière (première spécialisation) ;
- **GSIE-FEU** — surveillance et analyse des incendies (RFC-0004,
  DEC-000003) ;
- **Futures spécialisations** — eau, biodiversité, etc.

### 2.3 Interfaces

Les interfaces sont les points de contact entre le moteur et les
utilisateurs/applications :

- **Mobile** — application terrain (offline-first, bundle de mission) ;
- **Web** — console de gestion et d'analyse ;
- **Desktop** — poste fixe (bureau d'études) ;
- **API** — accès programmatique pour intégrations tierces.

---

## 3. Principes architecturaux

Les principes suivants découlent directement de la Constitution et
de la Constitution Technique. Aucun ne peut être contourné sans RFC.

### 3.1 Offline-first par nature (T-8, RFC-0003 §1)

Le fonctionnement hors-ligne n'est pas un mode dégradé — c'est
l'état normal d'un technicien de terrain. Chaque nœud terminal
embarque localement les données, les bases de connaissances et les
modèles nécessaires à la mission. La synchronisation se fait lors
d'une fenêtre de connectivité, sans action de l'utilisateur.

**Conséquence architecturale :** aucun moteur critique (Evidence,
Knowledge, Reasoning, Diagnostic) ne dépend d'une connexion réseau
pour fonctionner. Les moteurs nécessitant des données externes
(Climate, GIS) disposent d'un mode dégradé documenté.

### 3.2 Modularité obligatoire (CON-007, T-1)

Chaque moteur a **une et une seule** responsabilité. Aucun moteur
n'accède à l'implémentation interne d'un autre. La communication se
fait exclusivement par des interfaces contractuelles versionnées
(T-2). Le graphe de dépendances est acyclique.

**Conséquence architecturale :** un moteur peut être remplacé sans
casser les autres si le contrat d'interface est respecté. Les
moteurs sont testables isolément.

### 3.3 Traçabilité complète (CON-005, CON-010, T-6)

Toute connaissance, toute décision, toute modification est tracée et
versionnée. L'historique n'est jamais supprimé — il évolue. Chaque
connaissance a un identifiant stable et citable (S-7).

**Conséquence architecturale :** chaque transformation de donnée
dans le pipeline produit un journal d'audit. Le versioning s'applique
au code (Git), aux connaissances, aux API et aux documents.

### 3.4 Subordination du code à la connaissance (CON-003, T-3)

Le code est un moyen, pas une fin. En cas de conflit entre la qualité
de la connaissance et la performance du code, la connaissance prime.
Aucune optimisation ne peut dégrader la traçabilité ou l'explicabilité.

**Conséquence architecturale :** l'architecture privilégie la
lisibilité et l'auditabilité sur la concision. Les boîtes noires
sont interdites.

### 3.5 Explicabilité native (CON-004, T-3)

Toute décision produite par le système doit être explicable. Chaque
recommandation porte sa chaîne d'inférence, ses sources et son
niveau de preuve (S-2).

**Conséquence architecturale :** le pipeline conserve à chaque étape
les métadonnées de provenance. La Validation Engine bloque toute
sortie non expliquée.

### 3.6 Pas de logique métier dupliquée (T-4)

Toute règle métier (seuil, coefficient, formule) existe à un seul
endroit. La duplication est interdite.

**Conséquence architecturale :** les règles partagées sont extraites
dans des modules partagés ou fournies via l'API d'un moteur
propriétaire.

### 3.7 Couplage faible (T-2)

Les moteurs communiquent par interfaces contractuelles, jamais par
accès direct. Un contrat définit les entrées, les sorties, les
erreurs et la version.

**Conséquence architecturale :** l'architecture est distribuée par
construction. Un moteur peut s'exécuter localement (téléphone) ou
distantement (serveur) sans que ses consommateurs le sachent.

---

## 4. Couches architecturales

GSIE suit une architecture en couches séparées (clean architecture).
La dépendance va toujours vers l'intérieur : la couche domaine ne
connaît rien de l'infrastructure ; l'infrastructure connaît le
domaine mais pas l'inverse.

```
┌──────────────────────────────────────────────────────────┐
│  COUCHE PRÉSENTATION                                     │
│  Mobile (TypeScript/React Native) · Web (TypeScript)     │
│  Desktop · API publique                                  │
│  → Affiche, capture, transmet. Aucune logique métier.    │
├──────────────────────────────────────────────────────────┤
│  COUCHE APPLICATION                                      │
│  Orchestration Python · Cas d'usage · Workflows          │
│  → Coordonne les moteurs, gère les transactions,         │
│    les bundles de mission, la synchronisation.           │
├──────────────────────────────────────────────────────────┤
│  COUCHE DOMAINE (cœur IP)                                │
│  14 moteurs (Rust via pyo3 pour le cœur, Python pour     │
│  l'orchestration interne des moteurs)                    │
│  → Raisonnement, diagnostic, recommandation, validation. │
│    Connaissances, preuves, corrélations.                 │
├──────────────────────────────────────────────────────────┤
│  COUCHE INFRASTRUCTURE                                   │
│  Stockage (SQLite local, PostgreSQL serveur)             │
│  Réseau (GSIE-Net) · Transport (LoRa, Wi-Fi, 4G/5G)      │
│  Sources externes (IGN, Météo-France, INRAE, GBIF…)      │
│  → Persistance, communication, accès aux données.        │
└──────────────────────────────────────────────────────────┘
```

### 4.1 Couche domaine

La couche domaine contient le cœur intellectuel de GSIE : les 14
moteurs. C'est la propriété intellectuelle (IP) du système. Elle ne
dépend d'aucune infrastructure — elle définit des interfaces
(repositories) que l'infrastructure implémente.

**Justification du positionnement :** la Constitution (CON-003) pose
que la connaissance prime sur le code. Le domaine est l'expression
de la connaissance en logique. Le placer au centre garantit que
l'infrastructure (changeante) ne pollue pas la connaissance
(pérenne).

### 4.2 Couche application

La couche application orchestre les moteurs pour réaliser des cas
d'usage concrets : préparation d'un bundle de mission, exécution
d'un diagnostic complet, synchronisation différée. Elle ne contient
aucune règle métier — elle coordonne.

**Justification :** séparer l'orchestration du domaine permet de
faire évoluer les workflows sans toucher au cœur de raisonnement.
Cela respecte T-1 (une responsabilité par moteur) et T-4 (pas de
duplication).

### 4.3 Couche infrastructure

La couche infrastructure implémente les interfaces définies par le
domaine : accès aux bases de données, communication réseau
(GSIE-Net), intégration des sources externes (IGN, Météo-France,
INRAE, GBIF, etc.). Elle est remplaçable sans impact sur le domaine.

**Justification :** les technologies de stockage et de transport
évoluent sur des décennies. L'isoler permet de migrer SQLite vers
PostgreSQL, ou LoRa vers une autre radio, sans refonte du domaine
(RFC-0003 §2).

### 4.4 Couche présentation

La couche présentation regroupe les interfaces utilisateur et les
API. Elle ne contient aucune logique métier — elle affiche, capture
et transmet.

**Justification :** les interfaces changent plus vite que le moteur.
GeoSylva mobile, GSIE-FEU desktop et une future API publique
partagent le même moteur mais ont des présentations distinctes.

---

## 5. Diagramme de flux de données

Le flux officiel décrit le parcours d'une donnée depuis son acquisition
jusqu'à sa présentation à l'utilisateur. Chaque étape est journalisée
et produit un artefact traçable.

```
                    SOURCES EXTERNES
                    ┌───────────┬───────────┬───────────┐
                    │ IGN       │ Météo-Fr  │ INRAE     │
                    │ GBIF      │ BDNFF     │ BD Sols   │
                    │ ONF       │ LiDAR     │ Publis    │
                    └─────┬─────┴─────┬─────┴─────┬─────┘
                          │           │           │
                    ┌─────▼───────────▼───────────▼─────┐
                    │         IMPORT / ACQUISITION       │
                    │  (couche infrastructure)           │
                    │  Validation format, parsing,       │
                    │  normalisation des identifiants    │
                    └────────────────┬──────────────────┘
                                     │
                    ┌────────────────▼──────────────────┐
                    │       EVIDENCE ENGINE               │
                    │  Évaluation du niveau de preuve     │
                    │  (A=Prouvé → F=Observation)         │
                    │  Aucune donnée n'entre sans preuve  │
                    └────────────────┬──────────────────┘
                                     │
                    ┌────────────────▼──────────────────┐
                    │       KNOWLEDGE ENGINE              │
                    │  Intégration dans le graphe de      │
                    │  connaissances qualifiées           │
                    │  Ontologie + Knowledge Graph        │
                    └────────────────┬──────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
    ┌─────────▼─────────┐  ┌────────▼────────┐  ┌──────────▼─────────┐
    │  MOTEURS DOMAINE   │  │ CORRELATION ENG.│  │  FOREST DYNAMICS   │
    │  GIS · Climate     │  │  Croisement     │  │  Croissance,       │
    │  Pedology · Botan. │  │  multi-domaine  │  │  régénération      │
    └─────────┬─────────┘  └────────┬────────┘  └──────────┬─────────┘
              │                     │                      │
              └─────────────────────┼──────────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │       REASONING ENGINE             │
                    │  Inférence explicite et auditable  │
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │       DIAGNOSTIC ENGINE            │
                    │  Synthèse stationnelle/sylvicole   │
                    │  (analyse, pas décision)           │
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │    SIMULATION ENGINE (optionnel)   │
                    │  Projection de scénarios long terme│
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │    RECOMMENDATION ENGINE           │
                    │  Recommandations contournables,    │
                    │  justifiées, avec alternatives     │
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │       VALIDATION ENGINE            │
                    │  Conformité constitutionnelle      │
                    │  (explicabilité, preuve, domaine)  │
                    │  Bloque toute sortie non conforme  │
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │         UTILISATEUR                │
                    │  Rapport explicable + niveau de    │
                    │  preuve + incertitude affichée     │
                    └───────────────────────────────────┘

    MOTEURS TRANSVERSES (alimentent l'ensemble du pipeline) :

    ┌──────────────────────────────────────────────────────┐
    │  LEARNING ENGINE                                      │
    │  Amélioration continue à partir des retours terrain   │
    │  → alimente Knowledge, Correlation, Reasoning         │
    ├──────────────────────────────────────────────────────┤
    │  SIMULATION ENGINE                                    │
    │  Projections long terme                               │
    │  → alimente Recommendation                            │
    └──────────────────────────────────────────────────────┘
```

### 5.1 Propriétés du flux

- **Filtre amont obligatoire :** l'Evidence Engine est le premier
  moteur du pipeline. Aucune connaissance n'entre dans le système
  sans niveau de preuve (S-2, `GSIE_CORE_BLUEPRINT.md`).
- **Journalisation à chaque étape :** chaque transformation produit
  un journal d'audit (CON-005, T-6). Le journal est consultable et
  immuable.
- **Sens unique dominant :** le flux principal va de l'acquisition
  vers l'utilisateur. Les moteurs transverses (Learning, Simulation)
  introduisent des boucles de rétroaction, mais jamais de cycles
  (T-1 : graphe de dépendances acyclique).
- **Mode hors-ligne :** l'intégralité du flux s'exécute localement
  sur le nœud terminal. La synchronisation avec le serveur se fait
  en arrière-plan (RFC-0003 §1, §4).

---

## 6. Relation avec RFC-0003 (GSIE-Net)

RFC-0003 propose une architecture distribuée baptisée **GSIE-Net**.
Ce document (Master Architecture) définit l'architecture **logique**
des moteurs ; RFC-0003 définit l'architecture **réseau** qui les
distribue. Les deux sont complémentaires.

### 6.1 Ce que RFC-0003 apporte à cette architecture

| Principe RFC-0003 | Impact sur l'architecture logique |
|---|---|
| Offline-first par nature (§1) | Chaque moteur doit déclarer son comportement hors-ligne et son niveau de distribution |
| Couches séparées GSIE-Net Stack (§2) | La couche infrastructure de GSIE encapsule GSIE-Net comme sous-couche |
| Topologie trois niveaux (§3) | Les moteurs s'exécutent sur le nœud terminal (téléphone), l'Edge Node ou le serveur selon leur capacité |
| Synchronisation orientée données (§4) | Le modèle de données scientifique (livrable 205) doit supporter le versioning de type « commit » |
| Réseau orienté données (§5) | Les moteurs exposent un catalogue de données interrogable, pas seulement des endpoints RPC |
| Intelligence distribuée (§6) | Les 14 moteurs se répartissent selon les capacités du nœud (voir tableau ci-dessous) |
| Bundle de mission (§7) | La couche application prépare un bundle cohérent avant le départ terrain |
| Serveur chef d'orchestre (§8) | La couche application serveur pilote activement la qualité des données |

### 6.2 Distribution des moteurs par niveau de nœud

| Moteur | Téléphone (local) | Edge Node (relais) | Serveur GSIE |
|---|:---:|:---:|:---:|
| Evidence Engine | Oui | — | Oui |
| Knowledge Engine | Oui (cache) | Cache | Oui (source) |
| Correlation Engine | Oui (local) | Pré-filtrage | Oui (complet) |
| Reasoning Engine | Oui (simple) | — | Oui (complexe) |
| Diagnostic Engine | Oui | — | Oui |
| Recommendation Engine | Oui | — | Oui |
| Validation Engine | Oui | — | Oui |
| GIS Engine | Oui (cache) | — | Oui (source) |
| Climate Engine | Oui (cache) | — | Oui (source) |
| Pedology Engine | Oui (cache) | — | Oui (source) |
| Botanical Engine | Oui (modèle léger) | — | Oui (complet) |
| Forest Dynamics Engine | Partiel | — | Oui (complet) |
| Learning Engine | — | — | Oui |
| Simulation Engine | — | — | Oui |

**Lecture :** un technicien en terrain isolé peut exécuter
localement l'intégralité de la chaîne principale (Evidence →
Validation) avec les données en cache. Les moteurs lourds
(Learning, Simulation) nécessitent le serveur. Le technicien ne
voit aucune différence — la couche application gère la
transparence (RFC-0003 §6).

### 6.3 Statut de RFC-0003

RFC-0003 est en statut **Proposé**. Cette architecture logique est
conçue pour être compatible avec GSIE-Net, mais ne présuppose pas
l'adoption définitive du RFC. Si RFC-0003 évolue, les principes
offline-first et modulaires de cette architecture restent valides —
seule la couche infrastructure s'adapte.

---

## 7. Articulation avec les autres documents d'architecture

| Document | Rôle | Relation avec Master Architecture |
|---|---|---|
| `ARCHITECTURE_PRINCIPLES.md` | Principes directeurs | Source des principes (§3) |
| `GSIE_CORE_BLUEPRINT.md` | Blueprint du cœur (chaîne principale) | Détail du pipeline (§5) |
| `GSIE_DATA_FLOW.md` | Flux de données officiel | Version condensée du diagramme (§5) |
| `TECHNOLOGY_STACK.md` (livrable 202) | Stack technologique (ADR) | Implémentation des couches (§4) |
| `ENGINE_COMMUNICATION_PROTOCOL.md` (livrable 203) | Protocole inter-moteurs | Réalise T-2 (couplage faible) |
| `ENGINE_DEVELOPMENT_ORDER.md` (livrable 204) | Ordre de développement | Séquence de mise en œuvre |
| `SCIENTIFIC_DATA_MODEL.md` (livrable 205) | Modèle de données scientifique | Structure des données circulant dans le flux |
| `ENGINE_INTERFACE_CONTRACTS.md` (livrable 206) | Contrats d'interface des 14 moteurs | Réalise T-2 pour chaque moteur |

---

## 8. Objectif de longévité

L'architecture est conçue pour permettre l'évolution de GSIE pendant
plusieurs décennies sans refonte complète. Les garanties sont :

- **Domaine isolé** — le cœur intellectuel ne dépend pas de
  l'infrastructure ; changer SQLite, PostgreSQL, LoRa ou Meshtastic
  n'impacte pas les moteurs.
- **Contrats versionnés** — chaque interface est versionnée (T-6) ;
  un moteur peut évoluer sans casser ses consommateurs.
- **Couches remplaçables** — la couche transport (RFC-0003 §2) est
  isolée ; une technologie radio remplacée dans 10 ans ne change que
  la couche transport.
- **Connaissances indépendantes du code** (CON-003) — les
  connaissances vivent dans le Knowledge Graph, pas dans le code ;
  le code peut être réécrit, les connaissances persistent.

---

## 9. Ce que ce document ne fait PAS

- Il n'implémente aucun code (Phase 2 — interdit, DEC-000004).
- Il ne définit pas les contrats d'interface détaillés (livrable 206).
- Il ne décrit pas le détail interne de chaque moteur (`09_ENGINES/`).
- Il ne choisit pas de technologie radio définitive (RFC-0003).
- Il ne contredit aucun article constitutionnel.

---

## 10. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — version squelette (Phase 1) |
| 2026-07-12 | Enrichissement Phase 2 — vue d'ensemble, principes, couches, diagramme de flux, relation RFC-0003 |

---

## 11. Validation

Document en statut **Draft**. Passage en `Review` soumis à
validation du Fondateur. Aucune modification destructive sans
versionnement préalable (CON-010, T-6).
