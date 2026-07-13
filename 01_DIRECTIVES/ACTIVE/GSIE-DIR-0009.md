# ============================================================================
# GSIE ECOSYSTEM RESTRUCTURING DIRECTIVE
# Directive ID : GSIE-DIR-0009
# Version : 1.0
# Statut : ACTIVE
# Priorité : CRITIQUE
# Classification : FONDATION
# Auteur : Camille Perraudeau
# Date : 2026-07-13
# ============================================================================

# Titre : Restructuration de l'écosystème Quintessences — apps,
# Centre de Commandement et organisation

## Résumé exécutif

Le Fondateur acte une restructuration majeure de l'écosystème
Quintessences :

1. **Renommage des applications** : Myhunt devient **Artemis** (faune),
   GSIE-Ignis devient **Ignis** (incendies).
2. **Nouvelles applications** : **Hydro** (eau) et **Flora** (végétation)
   rejoignent l'écosystème.
3. **Applications futures** : Terra, Atmos, Atlas, Aether, Chronos, Nexus…
4. **QGISIA** reste comme plugin QGIS de l'écosystème Quintessences.
5. **Unreal Engine** est repositionné comme **Centre de Commandement
   GSIE** — pas une simple visionneuse 3D, mais un poste de pilotage
   immersif où toutes les données convergent.
6. **Réorganisation des dossiers** : sous-dossiers par application pour
   un meilleur rangement et une meilleure interconnexion.

---

## 1. Architecture cible

```
                    Quintessences
                    Ecosystème logiciel complet
                                  │
                                  ▼
             GSIE (General System Intelligence Engine)
      Moteur central de données, IA, simulations et interopérabilité
────────────────────────────────────────────────────────────────────
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
   GeoSylva     Artemis      Ignis      Hydro      Flora
   Forêt         Faune      Incendies     Eau     Végétation
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
                         Partage des données
```

### 1.1 GSIE — le système nerveux

GSIE n'est pas une application. C'est le cœur. Il est responsable de :

- la base de connaissances (Encyclopédie de l'Écosystème) ;
- l'IA (14 moteurs) ;
- les corrélations entre les domaines ;
- les simulations ;
- le moteur de règles ;
- la synchronisation des données ;
- les API communes ;
- la gestion des utilisateurs et des droits ;
- l'interopérabilité entre les modules.

### 1.2 Applications — expertes de leur domaine

| Application | Domaine | Statut | Ancien nom |
|---|---|---|---|
| GeoSylva | Forêt (inventaire, martelage, sylviculture, dendrométrie, cartographie) | Active | — |
| Artemis | Faune (comptages, pièges photo, empreintes, observations, populations) | Active | Myhunt |
| Ignis | Incendies (DFCI, prévention, départs de feu, simulation, moyens, gestion de crise, RETEX) | Active | GSIE-Ignis |
| Hydro | Eau (réseau hydrographique, zones humides, régimes hydriques) | Nouvelle | — |
| Flora | Végétation (flore, taxonomie, cartographie végétale) | Nouvelle | — |
| QGISIA | Plugin QGIS (analyses spatiales, couches, IA) | Active (plugin) | — |

### 1.3 Applications futures (réservées)

| Application | Domaine potentiel |
|---|---|
| Terra | Sols / géologie |
| Atmos | Atmosphère / météo |
| Atlas | Cartographie globale |
| Aether | Air / qualité atmosphérique |
| Chronos | Séries temporelles / historique |
| Nexus | Interopérabilité / intégration |

---

## 2. Centre de Commandement GSIE (Unreal Engine)

### 2.1 Repositionnement

Unreal Engine n'est pas une simple visionneuse 3D. C'est le **Centre de
Commandement GSIE** — un poste de pilotage immersif où toutes les
données de l'écosystème convergent.

### 2.2 Vision

Un poste de pilotage où l'utilisateur peut :

- naviguer librement dans un terrain 3D photoréaliste (Cesium, LiDAR HD) ;
- voir les arbres modélisés individuellement (PyCrown + PCG) ;
- localiser les animaux suivis par Artemis ;
- consulter les parcelles et peuplements de GeoSylva ;
- visualiser le réseau hydrographique d'Hydro ;
- afficher les données météo d'Atmos ;
- lancer une simulation d'incendie d'Ignis ;
- visualiser les déplacements d'une harde de cervidés ;
- comparer l'état d'un secteur entre plusieurs dates ;
- voir les flux vidéo de drones ou de caméras ;
- afficher les capteurs IoT ;
- suivre les véhicules et équipes en temps réel.

### 2.3 Comparaison

Le Centre de Commandement est un mélange entre :

- ArcGIS Pro (SIG) ;
- QGIS (analyses) ;
- Cesium (terrain 3D) ;
- Flight Simulator (immersion) ;
- Microsoft Digital Twins (jumeau numérique) ;
- un moteur de jeu (temps réel).

### 2.4 Impact sur les livrables

- Le livrable 211 (GCS-Cinéma) devient le **Centre de Commandement
  GSIE** — pas seulement GCS-Ignis.
- Le livrable 212 (GeoSylva-Unreal) est intégré au Centre de
  Commandement.
- Une nouvelle architecture unifiée remplace les deux documents
  séparés.

---

## 3. Renommages

### 3.1 Myhunt → Artemis

Toutes les références à « Myhunt » dans les documents sont remplacées
par « Artemis ». L'application de suivi de la faune prend le nom
d'Artemis (déesse grecne de la chasse et de la faune sauvage).

### 3.2 GSIE-Ignis → Ignis

L'application « GSIE-Ignis » devient « Ignis ». Le préfixe « GSIE- » est
réservé au moteur central. Les applications sont des clients de GSIE,
pas des sous-modules.

### 3.3 Fichiers et dossiers concernés

| Ancien nom | Nouveau nom | Type |
|---|---|---|
| `22_PROJECT_MEMORY/GSIE-Ignis/` | `22_PROJECT_MEMORY/Ignis/` | Dossier |
| `22_PROJECT_MEMORY/GSIE-Ignis.md` | `22_PROJECT_MEMORY/Ignis.md` | Fichier |
| `04_ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` | `04_ARCHITECTURE/IGNIS_ARCHITECTURE.md` | Fichier |
| `04_ARCHITECTURE/GSIE_IGNIS_DATA_PIPELINE.md` | `04_ARCHITECTURE/IGNIS_DATA_PIPELINE.md` | Fichier |
| `04_ARCHITECTURE/GSIE_IGNIS_DRONE_ARCHITECTURE.md` | `04_ARCHITECTURE/IGNIS_DRONE_ARCHITECTURE.md` | Fichier |
| `04_ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` | `04_ARCHITECTURE/COMMAND_CENTER_UNREAL.md` | Fichier |

### 3.4 Contenu à remplacer

Dans tous les documents :
- « Myhunt » → « Artemis »
- « GSIE-Ignis » → « Ignis » (quand cela désigne l'application)
- « GSIE-Ignis » → « GSIE / Ignis » (quand cela désigne la branche
  projet avec le moteur)

---

## 4. Nouvelles applications

### 4.1 Hydro (eau)

| Champ | Valeur |
|---|---|
| Domaine | Eau |
| Responsabilités | Réseau hydrographique, zones humides, régimes hydriques, qualité de l'eau |
| Moteurs GSIE consommés | GIS, Climate, Knowledge, Correlation |
| Datasets | BD Carthage (IGN), BD TOPAGE, Sandre |
| Statut | Planifiée — pas de développement en Phase 3 |

### 4.2 Flora (végétation)

| Champ | Valeur |
|---|---|
| Domaine | Végétation |
| Responsabilités | Flore, taxonomie, cartographie végétale, phénologie |
| Moteurs GSIE consommés | Botanical, Knowledge, GIS, Climate |
| Datasets | GBIF, Tela Botanica, BDNFF, INPN |
| Statut | Planifiée — pas de développement en Phase 3 |

---

## 5. Réorganisation des dossiers

### 5.1 Principe

Chaque application a un sous-dossier dédié dans `22_PROJECT_MEMORY/`
pour ses livrables, journaux et scripts :

```
22_PROJECT_MEMORY/
├── GeoSylva/          (forêt)
├── Artemis/           (faune — ancien Myhunt)
├── Ignis/             (incendies — ancien GSIE-Ignis)
├── Hydro/             (eau — nouveau)
├── Flora/             (végétation — nouveau)
├── QGISIA/            (plugin QGIS)
└── GSIE-FEU/          (archive historique — conservé)
```

### 5.2 Dataset-Forge

Le dossier `A:\GSIE-Dataset-Forge` est renommé en conséquence des
changements. Il devient un outil de l'écosystème Quintessences.

---

## 6. Décisions validées

1. Myhunt est renommé **Artemis**.
2. GSIE-Ignis (l'application) est renommé **Ignis**.
3. **Hydro** (eau) et **Flora** (végétation) rejoignent l'écosystème.
4. QGISIA reste comme **plugin QGIS** de Quintessences.
5. Unreal Engine devient le **Centre de Commandement GSIE**.
6. Les dossiers de mémoire projet sont réorganisés par application.
7. Les applications futures (Terra, Atmos, Atlas, Aether, Chronos,
   Nexus) sont réservées.
8. GSIE reste le **moteur central** — les applications sont des clients.

---

## 7. Garde-fous

- La Constitution prime sur tout (CON-000).
- GSIE reste le moteur central — les applications ne deviennent pas
  indépendantes (CON-007).
- L'Encyclopédie de l'Écosystème (DIR-0008) reste le produit central.
- Le code métier reste interdit en Phase 3 (DEC-000011).
- Les documents `Locked` ne sont modifiés que par RFC.

---

> Quintessences — la suite logicielle des écosystèmes naturels.
> GSIE — le moteur commun.
> GeoSylva, Artemis, Ignis, Hydro, Flora — les applications spécialisées.
