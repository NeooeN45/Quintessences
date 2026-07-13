# GSIE Master Architecture

| Champ | Valeur |
|---|---|
| **Livrable** | 201 — Architecture globale GSIE |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 (correction audit) |
| **Lois fondatrices** | GSIE-CON-001, GSIE-CON-002, GSIE-CON-003, GSIE-CON-004, GSIE-CON-005, GSIE-CON-007, GSIE-CON-010 |
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
(GeoSylva, GSIE-Ignis, futures spécialisations) sont des **clients** du
moteur.

Le système se décompose en trois axes :

```
┌─────────────────────────────────────────────────────────────────┐
│                        ÉCOSYSTÈME QUINTESSENCES                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  GeoSylva    │  │  GSIE-Ignis    │  │  Futures spécialis.  │   │
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
| Evidence Engine | Évaluer la qualité scientifique (niveau de preuve) de chaque connaissance entrante. *Réf. : `06_RESEARCH/RESEARCH_METHOD.md` (pipeline d'évaluation), `SCIENTIFIC_CONSTITUTION.md` art. S-2 (niveaux A à F)* |
| Knowledge Engine | Centraliser et structurer les connaissances qualifiées (ontologie, graphe). *Réf. : `06_RESEARCH/README.md` (sources scientifiques), `07_KNOWLEDGE/` (base structurée)* |
| Correlation Engine | Croiser automatiquement les données multi-domaines. *Réf. : `06_RESEARCH/RESEARCH_METHOD.md` (modélisation conceptuelle des corrélations)* |
| Reasoning Engine | Produire des conclusions par inférence explicite et auditable. *Réf. : `09_ENGINES/REASONING_ENGINE/REASONING_ENGINE.md`* |
| Diagnostic Engine | Synthétiser un diagnostic stationnel/sylvicole à partir des conclusions. *Réf. : `09_ENGINES/DIAGNOSTIC_ENGINE/DIAGNOSTIC_ENGINE.md`* |
| Recommendation Engine | Proposer des recommandations d'action contournables et justifiées. *Réf. : `09_ENGINES/RECOMMENDATION_ENGINE/RECOMMENDATION_ENGINE.md`* |
| Validation Engine | Valider la conformité de toute sortie avant présentation à l'utilisateur. *Réf. : `09_ENGINES/VALIDATION_ENGINE/VALIDATION_ENGINE.md`* |

**Moteurs domaine (alimentent le raisonnement) :**

| Moteur | Responsabilité |
|---|---|
| GIS Engine | Données géospatiales (parcelles, relief, hydrographie). *Réf. : `08_DATASETS/README.md` (catalogue des datasets géospatiaux), `09_ENGINES/GIS_ENGINE/GIS_ENGINE.md`* |
| Climate Engine | Données climatiques et bioclimatiques (historiques + projections). *Réf. : `08_DATASETS/README.md` (catalogue des datasets climatiques), `09_ENGINES/CLIMATE_ENGINE/CLIMATE_ENGINE.md`* |
| Pedology Engine | Données pédologiques (texture, pH, drainage, réserve utile). *Réf. : `08_DATASETS/README.md` (catalogue des datasets pédologiques), `09_ENGINES/PEDOLOGY_ENGINE/PEDOLOGY_ENGINE.md`* |
| Botanical Engine | Taxonomie, nomenclature et autécologie des essences. *Réf. : `08_DATASETS/README.md` (catalogue des datasets botaniques), `09_ENGINES/BOTANICAL_ENGINE/BOTANICAL_ENGINE.md`* |
| Forest Dynamics Engine | Croissance et dynamique des peuplements forestiers. *Réf. : `06_RESEARCH/README.md` (travaux sur la dendrométrie et croissance), `09_ENGINES/FOREST_DYNAMICS_ENGINE/FOREST_DYNAMICS_ENGINE.md`* |

**Moteurs transverses :**

| Moteur | Responsabilité |
|---|---|
| Learning Engine | Amélioration continue des modèles à partir des retours terrain. *Réf. : `09_ENGINES/LEARNING_ENGINE/LEARNING_ENGINE.md`, `AI_CONSTITUTION.md` art. IA-4 (apprentissage encadré)* |
| Simulation Engine | Projection de scénarios sylvicoles long terme. *Réf. : `09_ENGINES/SIMULATION_ENGINE/SIMULATION_ENGINE.md`* |

### 2.2 Spécialisations (applications clientes)

Les spécialisations sont des **clients** du moteur GSIE, jamais des
forks. Elles consomment les API du moteur et ajoutent une couche
métier propre à leur domaine :

- **GeoSylva** — application forestière (première spécialisation) ;
- **GSIE-Ignis** — surveillance et analyse des incendies (RFC-0004,
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

**Réf. constitutionnelle :** GSIE-CON-007 (modularité obligatoire —
chaque moteur déclare son comportement hors-ligne), GSIE-CON-003
(connaissance avant le code — les connaissances persistent localement,
indépendamment de l'infrastructure).

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

**Réf. constitutionnelle :** GSIE-CON-007 (la modularité est
obligatoire — chaque moteur a une responsabilité unique, une interface
stable et un graphe de dépendances acyclique).

Chaque moteur a **une et une seule** responsabilité. Aucun moteur
n'accède à l'implémentation interne d'un autre. La communication se
fait exclusivement par des interfaces contractuelles versionnées
(T-2). Le graphe de dépendances est acyclique.

**Conséquence architecturale :** un moteur peut être remplacé sans
casser les autres si le contrat d'interface est respecté. Les
moteurs sont testables isolément.

### 3.3 Traçabilité complète (CON-005, CON-010, T-6)

**Réf. constitutionnelle :** GSIE-CON-005 (toute connaissance doit être
traçable — origine, historique, niveau de preuve, version),
GSIE-CON-010 (toute connaissance doit pouvoir évoluer sans perdre son
historique — les versions précédentes sont archivées, jamais supprimées).

Toute connaissance, toute décision, toute modification est tracée et
versionnée. L'historique n'est jamais supprimé — il évolue. Chaque
connaissance a un identifiant stable et citable (S-7).

**Conséquence architecturale :** chaque transformation de donnée
dans le pipeline produit un journal d'audit. Le versioning s'applique
au code (Git), aux connaissances, aux API et aux documents.

### 3.4 Subordination du code à la connaissance (CON-003, T-3)

**Réf. constitutionnelle :** GSIE-CON-003 (la connaissance avant le
code — le code est un moyen, pas une fin ; aucune optimisation ne peut
dégrader la traçabilité ou l'explicabilité).

Le code est un moyen, pas une fin. En cas de conflit entre la qualité
de la connaissance et la performance du code, la connaissance prime.
Aucune optimisation ne peut dégrader la traçabilité ou l'explicabilité.

**Conséquence architecturale :** l'architecture privilégie la
lisibilité et l'auditabilité sur la concision. Les boîtes noires
sont interdites.

### 3.5 Explicabilité native (CON-004, T-3)

**Réf. constitutionnelle :** GSIE-CON-004 (toute décision doit être
explicable — chaîne de raisonnement, sources, niveau de confiance,
limites), GSIE-CON-001 (le forestier reste le décideur — l'explicabilité
est la condition du consentement éclairé).

Toute décision produite par le système doit être explicable. Chaque
recommandation porte sa chaîne d'inférence, ses sources et son
niveau de preuve (S-2).

**Conséquence architecturale :** le pipeline conserve à chaque étape
les métadonnées de provenance. La Validation Engine bloque toute
sortie non expliquée.

### 3.6 Pas de logique métier dupliquée (T-4)

**Réf. constitutionnelle :** GSIE-CON-007 (modularité obligatoire — une
règle métier appartient à un seul moteur, les autres la consomment via
API), GSIE-CON-002 (la science avant tout — toute règle est sourcée et
identifiée à un seul endroit pour garantir la traçabilité).

Toute règle métier (seuil, coefficient, formule) existe à un seul
endroit. La duplication est interdite.

**Conséquence architecturale :** les règles partagées sont extraites
dans des modules partagés ou fournies via l'API d'un moteur
propriétaire.

### 3.7 Couplage faible (T-2)

**Réf. constitutionnelle :** GSIE-CON-007 (modularité obligatoire — les
moteurs communiquent par interfaces contractuelles, jamais par accès
direct à l'implémentation interne d'un autre).

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
│  *Réf. : `08_DATASETS/README.md` (catalogue des datasets   │
│    référencés et sourcés)*                                 │
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
GeoSylva mobile, GSIE-Ignis desktop et une future API publique
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
  sans niveau de preuve (S-2, `GSIE_CORE_BLUEPRINT.md`). Les niveaux
  de preuve (A=Prouvé → F=Observation) sont définis dans la
  Constitution Scientifique article S-2 et le protocole d'évaluation
  est documenté dans `06_RESEARCH/RESEARCH_METHOD.md`.
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

### 5.2 Modes dégradés : fonctionnement hors-ligne vs en ligne

**Réf. constitutionnelle :** GSIE-CON-007 (modularité — chaque moteur
déclare son comportement hors-ligne), Constitution Technique article
T-8 (fonctionnement hors-ligne — données de référence en cache local,
moteurs critiques hors-ligne, mode dégradé documenté pour les moteurs
à données externes).

Le tableau ci-dessous précise, pour chaque moteur, ce qui est
disponible hors-ligne (sur le nœud terminal, sans connexion réseau)
versus en ligne (connexion au serveur GSIE ou Edge Node). Les données
en cache sont préparées par la couche application lors du bundle de
mission (RFC-0003 §7).

#### Cœur de raisonnement

| Moteur | Hors-ligne (cache local) | En ligne (serveur) | Fonctionnalités perdues hors-ligne |
|---|---|---|---|
| Evidence Engine | Évaluation complète des niveaux de preuve (A→F). Base des règles d'évaluation en cache local. | Idem + mise à jour des règles d'évaluation si évolution. | Aucune perte — moteur critique, conçu pour fonctionner hors-ligne. |
| Knowledge Engine | Graphe de connaissances en cache (bundle de mission). Requêtes locales, intégration de nouvelles connaissances terrain. | Graphe complet (source). Synchronisation des connaissances produites hors-ligne, résolution des conflits de fusion. | Pas d'accès aux connaissances ajoutées sur le serveur depuis le bundle. Risque de conflit à la synchronisation (résolu par versioning). |
| Correlation Engine | Croisement multi-domaine sur les données en cache. Pré-filtrage local. | Croisement complet sur l'ensemble des données serveur. | Corrélations limitées au périmètre du bundle de mission. |
| Reasoning Engine | Inférence simple (chaîne courte, règles locales). | Inférence complexe (chaînes longues, règles volumineuses, inférence transverse). | Inférences complexes non disponibles. Le moteur signale la limite. |
| Diagnostic Engine | Synthèse stationnelle/sylvicole complète à partir des données en cache. | Idem + accès aux modèles diagnostiques mis à jour. | Aucune perte — moteur critique. |
| Recommendation Engine | Recommandations contournables et justifiées à partir du diagnostic local. | Idem + accès aux règles de recommandation mises à jour. | Aucune perte — moteur critique. |
| Validation Engine | Conformité constitutionnelle complète (explicabilité, preuve, domaine). | Idem. | Aucune perte — moteur critique, conçu pour fonctionner hors-ligne. |

#### Moteurs domaine

| Moteur | Hors-ligne (cache local) | En ligne (serveur) | Fonctionnalités perdues hors-ligne |
|---|---|---|---|
| GIS Engine | Données géospatiales en cache (parcelles, relief, hydrographie du périmètre de mission). | Source complète (IGN, cadastre, LiDAR). Mise à jour des couches. | Pas d'accès aux couches non incluses dans le bundle. Pas de mise à jour des données IGN. |
| Climate Engine | Données climatiques historiques en cache (normales, bioclimatiques du périmètre). | Projections climatiques complètes, mises à jour Météo-France/DSN. | Pas d'accès aux projections mises à jour. Les projections en cache restent utilisables avec date de validité signalée. |
| Pedology Engine | Données pédologiques en cache (texture, pH, drainage, réserve utile du périmètre). | Source complète (BD Sols, Référentiel Pédologique Français). | Pas d'accès aux données pédologiques hors périmètre de mission. |
| Botanical Engine | Modèle léger en cache (taxonomie, autécologie des essences du périmètre). | Base botanique complète (BDNFF, GBIF). | Pas d'accès aux espèces hors bundle. Autécologie limitée aux essences préchargées. |
| Forest Dynamics Engine | Modèles de croissance partiels en cache (essences principales du périmètre). | Modèles complets (toutes essences, toutes stations). | Modèles de croissance indisponibles pour les essences non préchargées. |

#### Moteurs transverses

| Moteur | Hors-ligne (cache local) | En ligne (serveur) | Fonctionnalités perdues hors-ligne |
|---|---|---|---|
| Learning Engine | Indisponible hors-ligne. Les retours terrain sont stockés localement pour synchronisation différée. | Amélioration continue des modèles à partir des retours validés (serveur). | Pas d'apprentissage en temps réel. Les retours sont différés et traités au serveur. |
| Simulation Engine | Indisponible hors-ligne (calcul lourd). | Projection de scénarios sylvicoles long terme. | Pas de simulation long terme sur le terrain. Le technicien peut demander une simulation qui sera exécutée au prochain passage serveur. |

**Principe de transparence :** le technicien ne voit aucune différence
entre les modes hors-ligne et en ligne — la couche application gère la
transparence (RFC-0003 §6). Les fonctionnalités indisponibles
hors-ligne sont signalées par une mention « nécessite synchronisation »
dans l'interface, sans bloquer le travail en cours.

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

## 10. Esquisse des contrats d'interface

**Réf. constitutionnelle :** GSIE-CON-007 (modularité — communication
par interfaces contractuelles), Constitution Technique article T-2
(couplage faible — un contrat définit les entrées, les sorties, les
erreurs et la version).

Le tableau ci-dessous esquisse les entrées et sorties principales de
chaque moteur. Il s'agit d'une vue d'overview : le détail complet
(format, type, unité, domaine de validité, codes d'erreur, version) est
défini dans le livrable 206 (`ENGINE_INTERFACE_CONTRACTS.md`).

### Cœur de raisonnement

| Moteur | Entrées principales | Sorties principales |
|---|---|---|
| Evidence Engine | Connaissance brute (source, métadonnées, contenu) | Connaissance qualifiée (niveau de preuve A→F, justification) |
| Knowledge Engine | Connaissance qualifiée (Evidence Engine) | Nœud de graphe de connaissances (identifiant stable, ontologie, relations) |
| Correlation Engine | Nœuds de connaissances multi-domaines (Knowledge Engine + moteurs domaine) | Corrélations détectées (paires/triplets, coefficient, niveau de confiance) |
| Reasoning Engine | Corrélations + connaissances (Correlation + Knowledge Engine) | Conclusions inférées (chaîne d'inférence, prémisses, niveau de confiance) |
| Diagnostic Engine | Conclusions inférées + données stationnelles (Reasoning + moteurs domaine) | Diagnostic stationnel/sylvicole (synthèse, facteurs limitants, niveau de confiance) |
| Recommendation Engine | Diagnostic + alternatives (Diagnostic Engine + Simulation Engine optionnel) | Recommandations contournables (action, justification, alternatives, incertitude) |
| Validation Engine | Recommandations + métadonnées de traçabilité (Recommendation Engine) | Sortie validée ou bloquée (conformité constitutionnelle, explication, sources) |

### Moteurs domaine

| Moteur | Entrées principales | Sorties principales |
|---|---|---|
| GIS Engine | Coordonnées géographiques, périmètre de mission | Données géospatiales (parcelles, relief, hydrographie, couches vectorielles/raster) |
| Climate Engine | Localisation, période, scénario climatique | Données climatiques/bioclimatiques (températures, précipitations, indices, projections) |
| Pedology Engine | Localisation, échantillons terrain (optionnel) | Données pédologiques (texture, pH, drainage, réserve utile, type de sol) |
| Botanical Engine | Taxon ou essence, localisation (optionnel) | Données botaniques (taxonomie, nomenclature, autécologie, exigences stationnelles) |
| Forest Dynamics Engine | Peuplement (composition, structure, âge), station, scénario sylvicole | Projections de croissance et dynamique (accroissement, volume, régénération) |

### Moteurs transverses

| Moteur | Entrées principales | Sorties principales |
|---|---|---|
| Learning Engine | Retours terrain validés, écarts recommandation/décision | Ajustements de modèles proposés (justification, source, réversibilité) |
| Simulation Engine | Peuplement initial, scénario sylvicole, horizon temporel | Projections de scénarios (trajectoires, indicateurs, comparaison de scénarios) |

**Note :** chaque contrat d'interface est versionné (T-6). Toute
évolution de contrat est tracée et rétro-compatible ou documentée
comme rupture. Le protocole de communication inter-moteurs est défini
dans le livrable 203 (`ENGINE_COMMUNICATION_PROTOCOL.md`).

---

## 11. Sources et références scientifiques

**Réf. constitutionnelle :** GSIE-CON-002 (la science avant tout —
toute connaissance doit reposer sur une source scientifique
identifiable et vérifiable), GSIE-CON-005 (traçabilité — chaque
connaissance a une origine, un auteur, une date, une version).

Ce document référence des domaines scientifiques couverts par GSIE.
Chaque domaine est sourcé dans `06_RESEARCH/` (travaux scientifiques,
bibliographie) et `08_DATASETS/` (jeux de données référencés). L'état
actuel de ces dossiers est en constitutif — les sources spécifiques
seront cataloguées au fur et à mesure de l'enrichissement de la base
de recherche.

| Domaine scientifique | Moteur(s) concerné(s) | Référence recherche | Référence datasets |
|---|---|---|---|
| Écologie forestière et stationnelle | Diagnostic, Forest Dynamics | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |
| Pédologie | Pedology | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |
| Dendrométrie et croissance | Forest Dynamics | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |
| Climatologie et bioclimatologie | Climate | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |
| Botanique et taxonomie | Botanical | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |
| Géospatial (SIG) | GIS | — | `08_DATASETS/README.md` (à enrichir) |
| Pathologie forestière | (futur moteur domaine) | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |
| Entomologie forestière | (futur moteur domaine) | `06_RESEARCH/README.md` (à enrichir) | `08_DATASETS/README.md` (à enrichir) |

### Documents de référence actuellement disponibles

| Document | Rôle | Chemin |
|---|---|---|
| Research Method | Pipeline officiel d'évaluation scientifique (recherche → collecte → évaluation → niveau de preuve → modélisation → validation → intégration) | `06_RESEARCH/RESEARCH_METHOD.md` |
| Research README | Cadre des travaux scientifiques et bibliographiques | `06_RESEARCH/README.md` |
| Datasets README | Cadre du catalogue des jeux de données référencés | `08_DATASETS/README.md` |
| Constitution Scientifique | Articles S-1 à S-7 (sources acceptées, niveaux de preuve, conflits, révision, incertitude, domaines, patrimoine) | `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md` |
| Constitution Technique | Articles T-1 à T-10 (architecture modulaire, couplage, versionnement, hors-ligne, etc.) | `00_CONSTITUTION/TECHNICAL_CONSTITUTION.md` |

### Sources externes institutionnelles (couche infrastructure)

Les sources externes suivantes sont référencées dans le flux de données
(§5) et la couche infrastructure (§4.3). Leur catalogue détaillé
(métadonnées, licence, couverture, qualité) sera documenté dans
`08_DATASETS/` au fur et à mesure de l'intégration :

- **IGN** — Institut National de l'Information Géographique et Forestière (données géospatiales, forestières) ;
- **Météo-France / DSN** — données climatiques historiques et projections ;
- **INRAE** — Institut National de Recherche pour l'Agriculture, l'Alimentation et l'Environnement (recherche forestière, pédologie) ;
- **GBIF** — Global Biodiversity Information Facility (données de biodiversité) ;
- **BDNFF** — Base de Données Nomenclaturale de la Flore de France (taxonomie botanique) ;
- **BD Sols / Référentiel Pédologique Français** — données et référentiel pédologique ;
- **ONF** — Office National des Forêts (données de gestion forestière) ;
- **LiDAR** — données de relief et de structure de la canopée.

> **Note :** conformément à GSIE-CON-002, aucune donnée de ces sources
> ne sera intégrée sans métadonnées complètes (source, licence, date,
> couverture, qualité). Le respect des contraintes de licence est
> géré en coordination avec `19_LEGAL/`.

---

## 12. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — version squelette (Phase 1) |
| 2026-07-12 | Enrichissement Phase 2 — vue d'ensemble, principes, couches, diagramme de flux, relation RFC-0003 |
| 2026-07-12 | Correction audit — références constitutionnelles explicites (§3), références sources (§2.1, §4.3, §5.1), modes dégradés détaillés (§5.2), esquisse des contrats d'interface (§10), sources et références scientifiques (§11) |

---

## 13. Validation

Document en statut **Draft**. Passage en `Review` soumis à
validation du Fondateur. Aucune modification destructive sans
versionnement préalable (CON-010, T-6).
