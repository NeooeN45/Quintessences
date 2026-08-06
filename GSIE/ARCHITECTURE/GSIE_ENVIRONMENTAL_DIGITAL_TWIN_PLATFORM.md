# GSIE Environmental Digital Twin Platform — Architecture cible

| Champ | Valeur |
|---|---|
| **Livrable** | Architecture cible de la plateforme de jumeau numérique environnemental fédéré |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation (cadrage) |
| **RFC** | RFC-0037 |
| **Dépend de** | RFC-0011, RFC-0029, RFC-0035, RFC-0036, HUB-002 |
| **Applications** | GeoSylva, Ignis, Hydro, Flora, Artemis, QGISIA |
| **Hub** | Unreal Engine 5.8 + Cesium for Unreal |

---

## 1. Positionnement

GSIE est un **jumeau numérique environnemental fédéré**. Il ne s'agit
pas d'une seule application ni d'une scène Unreal centralisant toutes
les données.

Le système est une plateforme qui conserve un état environnemental
spatio-temporel commun et fournit plusieurs projections métier :

```text
                    JUMEAU NUMÉRIQUE GSIE
             état territorial + connaissances + historique
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    Projection            Projection            Projection
     GeoSylva               Ignis                  Hydro
       forêt                feu                    eau
        │                     │                     │
        └──────────────┬──────┴──────┬─────────────┘
                       │             │
                 Flora / Artemis / QGISIA
                       │             │
                Hubs Unreal spécialisés
```

Les projections partagent les contrats GSIE mais conservent leurs
responsabilités scientifiques et opérationnelles propres.

## 2. Règles d'architecture

1. **Un socle, plusieurs projections** : aucune application ne devient la
   base des autres applications.
2. **Une source d'autorité par ressource** : une projection ne modifie
   pas directement les données internes d'une autre.
3. **Observation ≠ calcul ≠ prévision ≠ scénario ≠ décision** : ces états
   sont séparés dans le modèle et dans l'interface.
4. **Toute sortie est traçable** : source, méthode, version, incertitude,
   validité et chaîne de production sont conservées.
5. **Le Hub visualise et coordonne** : il ne remplace pas les moteurs
   scientifiques ni les systèmes opérationnels autorisés.
6. **Le scénario est une branche** : une simulation ne modifie pas l'état
   réel canonique.
7. **Le temps réel est sélectif** : seuls les flux opérationnels urgents
   utilisent la haute fréquence ; les rasters et scènes 3D sont streamés
   par tuiles.
8. **Offline-first** : chaque client conserve le dernier état cohérent
   connu et synchronise les observations à la reconnexion.

## 3. Couches de la plateforme

### 3.1 Couche de connaissance

- Evidence Engine ;
- Knowledge Engine ;
- sources scientifiques ;
- datasets qualifiés ;
- provenance et niveaux de preuve ;
- règles, modèles et hypothèses versionnés.

### 3.2 Couche de données environnementales

- ressources territoriales ;
- observations terrain ;
- états environnementaux ;
- géométries et rasters ;
- séries temporelles ;
- capteurs et missions ;
- historiques bitemporels.

### 3.3 Couche des moteurs

- GIS ;
- Climate ;
- Pedology ;
- Botanical ;
- Forest Dynamics ;
- Simulation ;
- Correlation ;
- Reasoning ;
- Diagnostic ;
- Recommendation ;
- Validation ;
- Learning.

### 3.4 Couche des projections métier

Chaque projection possède :

- un modèle de domaine ;
- des vues spécialisées ;
- des scénarios propres ;
- des workflows ;
- des droits d'action ;
- des adaptateurs d'entrée/sortie ;
- une politique de qualité et de fraîcheur.

### 3.5 Couche d'expérience

- application terrain GeoSylva ;
- GCS-Lite Ignis ;
- Hub Unreal Ignis ;
- Hub Unreal GeoSylva ;
- Hub Unreal Hydro ;
- consoles web et QGISIA ;
- exports scientifiques et opérationnels.

## 4. Modèle de ressource fédéré

### 4.1 Enveloppe commune

```json
{
  "resource_id": "uuid-v7",
  "resource_type": "observation|forecast|scenario|simulation_run|mission|action_request",
  "schema_version": "1.0.0",
  "source_domain": "geosylva|ignis|hydro|flora|artemis|qgisia",
  "producer_engine": "string",
  "geometry": {},
  "srs": "EPSG:2154",
  "valid_time": {
    "start": "2026-08-06T10:00:00Z",
    "end": null
  },
  "transaction_time": "2026-08-06T10:01:00Z",
  "state_kind": "real|derived|forecast|simulated|proposed|decided",
  "confidence": 0.0,
  "provenance": [],
  "scenario_id": null,
  "trace_id": "uuid-v7"
}
```

### 4.2 Ressources partagées

| Ressource | Producteurs | Consommateurs possibles |
|---|---|---|
| `Observation` | GeoSylva, Ignis, Hydro, Flora, Artemis, capteurs | Tous domaines concernés |
| `EnvironmentalState` | Moteurs GSIE | Projections et Hub |
| `Forecast` | Climate, Simulation, Ignis, Hydro, Forest Dynamics | Projections spécialisées |
| `Scenario` | Toute projection | Toute projection autorisée |
| `SimulationRun` | Simulation, Ignis, Hydro, Forest Dynamics | Hub, applications et validation |
| `Mission` | GeoSylva, Ignis, Hydro | Terrain, drones, opérateurs |
| `ActionRequest` | Hub ou application habilitée | Adaptateur opérationnel |
| `Recommendation` | Recommendation Engine | Utilisateur autorisé |
| `Decision` | Opérateur humain habilité | Audit, State Fabric, projections |

## 5. Hubs Unreal spécialisés

### 5.1 Hub Ignis

Le Hub Ignis affiche :

- fronts et périmètres de feu ;
- fumée et intensité ;
- vents et humidité ;
- combustible ;
- bâtiments et infrastructures menacés ;
- drones et moyens terrestres ;
- aéronefs lorsqu'une source autorisée les fournit ;
- scénarios de propagation ;
- zones d'exclusion et trajectoires proposées.

Il peut préparer des demandes d'action, mais une commande critique suit
le contrat `ActionRequest` et exige validation humaine.

### 5.2 Hub GeoSylva

Le Hub GeoSylva permet :

- la visite immersive d'une forêt ;
- l'exploration de son évolution historique ;
- l'affichage des peuplements, arbres, essences et états sanitaires ;
- la comparaison de scénarios sylvicoles ;
- la simulation de changement d'essences ;
- la simulation de rendement et de croissance ;
- la visualisation des impacts d'un incendie ou d'une sécheresse ;
- la consultation des observations collectées par l'application terrain.

Une modification d'essence dans un scénario ne modifie jamais la forêt
réelle sans décision métier explicite et versionnée.

### 5.3 Hub Hydro

Le Hub Hydro permet :

- l'exploration des bassins versants ;
- la visualisation 3D des écoulements ;
- la simulation de crues et ruissellements ;
- l'exploration des réseaux karstiques ;
- la visualisation des nappes, zones humides et réseaux ;
- la simulation des impacts post-incendie sur l'eau et les sols.

### 5.4 Hub scientifique multi-domaines

Un mode transversal permet de superposer :

```text
Forêt + feu + eau + faune + végétation + météo + infrastructures
```

Il est destiné à l'analyse, à la recherche et à la coordination, mais
les droits d'action restent ceux du domaine responsable.

## 6. Flux inter-domaines

```text
Observation GeoSylva
       ↓ provenance + version
State Fabric GSIE
       ↓ projection combustible
Ignis / Simulation
       ↓ résultat feu + impact
State Fabric GSIE
       ├── GeoSylva : mortalité, régénération, restauration
       ├── Hydro : ruissellement, érosion, crue
       ├── Flora : changement de végétation
       └── Artemis : impacts habitats et populations
```

Les applications ne s'appellent pas directement pour synchroniser leurs
bases. Elles publient et consomment des ressources GSIE.

## 7. Scénarios et branches temporelles

Chaque simulation crée un `scenario_id` et une branche indépendante :

```text
État réel R0
  ├── Simulation S1 : vent renforcé
  ├── Simulation S2 : changement d'essences
  ├── Simulation S3 : intervention incendie validée
  └── Simulation S4 : crue post-incendie
```

Les résultats de scénario sont comparables, exportables et auditables.
Ils ne deviennent des données réelles qu'après une décision explicitement
tracée et une opération d'intégration contrôlée.

## 8. Performance et résilience

### 8.1 Classes de flux

| Classe | Exemple | Stratégie |
|---|---|---|
| P0 | Télémétrie, alerte, front actif | Flux temps réel prioritaire, dégradation contrôlée |
| P1 | Recalage feu, météo, trajectoire | Jobs rapides et événements versionnés |
| P2 | LiDAR, 3D Tiles, rasters, splats | Tuiles, cache spatial, chargement progressif |
| P3 | Historique, RETEX, campagnes de simulation | Batch asynchrone, stockage objet |

### 8.2 Règles de performance

- aucun calcul lourd dans le thread de rendu Unreal ;
- aucun chargement massif synchrone dans l'interface ;
- LOD et culling géospatial obligatoires ;
- cache local par territoire et par scénario ;
- backpressure sur les flux temps réel ;
- déduplication des événements ;
- indicateur visible de fraîcheur des données ;
- reprise sur dernier état cohérent connu.

## 9. Sécurité et autorité

- RBAC par domaine et périmètre territorial ;
- mTLS entre services et nœuds ;
- capsules signées pour l'edge ;
- audit de toute action opérateur ;
- validation humaine pour les actions critiques ;
- adaptateurs séparés pour drones, véhicules, aéronefs et systèmes
  réglementaires ;
- aucune commande physique directe depuis un moteur de recommandation ;
- aucune donnée personnelle ou sensible dans les couches publiques du Hub
  sans politique d'accès explicite.

## 10. Relation avec Territorial Mesh et Server Meshing

| Couche | Responsabilité |
|---|---|
| **Environmental Digital Twin Platform** | Fédération des domaines et contrats de ressources |
| **Territorial Mesh** | Autorité, périmètres, états et gouvernance territoriale |
| **Server Meshing** | Cellules d'exécution, charge, réplication et handoff technique |
| **State Fabric** | Persistance, historique, provenance et synchronisation |
| **Hub Unreal** | Visualisation, exploration, scénarios et interaction contrôlée |

## 11. Plan de réalisation

1. Contrat de ressource fédéré et enveloppe d'événement ;
2. Tranche verticale Ignis en replay historique (`GSIE_ENVIRONMENTAL_DIGITAL_TWIN_USE_CASES.md`, UC-001 et UC-003) ;
3. Projection GeoSylva ↔ Ignis ;
4. Projection Hydro et impacts post-incendie (UC-001, UC-004) ;
5. Hub multi-mode et scénarios comparables ;
6. Observations edge et synchronisation offline ;
7. Territorial Mesh et Server Meshing à l'échelle du prototype ;
8. Extension progressive aux domaines Flora, Artemis et QGISIA (UC-002, UC-005, UC-006).

## 12. Statut

Ce document est Draft et dépend de RFC-0037. Il ne remplace pas les
contrats existants ; il les fédère et définit leur trajectoire commune.
