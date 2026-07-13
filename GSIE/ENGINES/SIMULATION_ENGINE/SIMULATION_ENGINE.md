# Simulation Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Simulation Engine |
| **Catégorie** | Moteur transverse (simulation de scénarios) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-004, GSIE-CON-005, GSIE-CON-007 |
| **Ordre de développement** | Non listé (moteur transverse) |

---

## 1. Responsabilité

Simuler des scénarios d'évolution et d'intervention à partir de l'état
courant du système (forêt, feu, climat) pour projeter les conséquences
des décisions avant qu'elles ne soient prises.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Diagnostic | État courant diagnostiqué (station, peuplement, risque) |
| `RECOMMENDATION_ENGINE` | Recommandation | Scénarios d'intervention à simuler |
| `GIS_ENGINE` | Données spatiales | MNT, parcelles, infrastructures |
| `CLIMATE_ENGINE` | Données climatiques | Scénarios climatiques futurs (AROME, ERA5) |
| `FOREST_DYNAMICS_ENGINE` | Modèle de croissance | Paramètres de croissance et mortalité |
| `PEDOLOGY_ENGINE` | Données sol | Propriétés pédologiques (drainage, texture) |
| `BOTANICAL_ENGINE` | Données flore | Composition floristique, autécologie |
| `LEARNING_ENGINE` | Paramètres calibrés | Paramètres de simulation ajustés par apprentissage |
| Utilisateur | Scénario | Hypothèses d'intervention saisies par le forestier/COS |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `VALIDATION_ENGINE` | Résultats de simulation | Projections temporelles (état à +5, +10, +30 ans) |
| `RECOMMENDATION_ENGINE` | Comparatif de scénarios | Sorties comparées de plusieurs scénarios |
| `LEARNING_ENGINE` | Écarts simulation/réalité | Écarts entre projections et observations terrain |
| Utilisateur | Visualisation | Rendus cartographiques et temporels des scénarios |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `FOREST_DYNAMICS_ENGINE` | Modèles de dynamique forestière (obligatoire) |
| Moteur | `CLIMATE_ENGINE` | Scénarios climatiques comme conditions aux limites |
| Moteur | `GIS_ENGINE` | Données spatiales pour la projection cartographique |
| Moteur | `LEARNING_ENGINE` | Calibration des paramètres de simulation |
| Externe | ForeFire (Ignis) | Moteur de propagation de feu pour les scénarios incendie |

## 5. Contrat d'interface

### Entrée — `ScenarioSimulation`

```
ScenarioSimulation = {
  scenario_id       : UUID
  source_diagnostic : DiagnosticRef
  intervention      : InterventionSpec
  horizon           : Duration
  climate_scenario  : ClimateScenarioRef
  parameters        : Map<String, Value>
}
```

### Sortie — `SimulationResult`

```
SimulationResult = {
  scenario_id   : UUID
  projections   : List<TimedProjection>
  confidence    : ConfidenceLevel
  sources       : List<SourceRef>
  assumptions   : List<String>
  alternatives  : List<SimulationResult>
}

TimedProjection = {
  timestamp     : DateTime
  state         : SystemState
  key_indicators: Map<String, Value>
}
```

## 6. Garanties

- **Toute simulation cite ses sources** — les modèles utilisés sont
  référencés et traçables (GSIE-CON-005).
- **Toute projection est explicable** — les hypothèses simplificatrices
  sont explicites (GSIE-CON-004).
- **Les scénarios sont comparatifs** — plusieurs alternatives sont
  présentées, pas une seule projection (GSIE-CON-001).
- **La simulation ne décide pas** — elle projette des conséquences, le
  forestier/COS choisit (GSIE-CON-001).
- **Les paramètres sont ajustables** — l'utilisateur peut modifier les
  hypothèses et relancer la simulation.

## 7. Cas d'usage

### Cas 1 — Forestier (sylviculture)

Le forestier envisage une coupe d'éclaircie dans une parcelle de chêne.
Il saisit le scénario (intensité d'éclaircie, horizon 30 ans). Le
Simulation Engine projette l'évolution du peuplement (biomasse,
biodiversité, risque de dépérissement) avec et sans intervention. Le
forestier compare et décide.

### Cas 2 — COS (incendie, Ignis)

Le COS envisage un positionnement de moyens sur un versant. Le
Simulation Engine, couplé à ForeFire, projette la propagation du feu à
+30 min, +1 h, +2 h selon le vent et le terrain. Le COS compare les
scénarios et positionne ses moyens. La simulation ne déclenche rien
d'elle-même.

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de pistes pour une implémentation future
(Phase 4), des technologies, méthodes et précédents scientifiques
pertinents pour la responsabilité du Simulation Engine telle que définie
en §1. Aucun choix d'implémentation n'est arrêté ici : il s'agit de
repères sourcés destinés à alimenter une future spécification technique
et, le cas échéant, un RFC.

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **CAPSIS** (plateforme collaborative INRAE/AMAP/CIRAD) | Bibliothèque de modules de croissance forestière calibrés, réutilisable en amont ou en complément du Forest Dynamics Engine pour alimenter les `TimedProjection` du contrat de sortie | Framework Java open source fédérant, depuis plus de vingt ans, des dizaines de modèles de croissance calibrés sur des essences européennes au sein d'une architecture à modules interchangeables (Dufour-Kowalski et al., 2012). Également cité dans la section équivalente du `FOREST_DYNAMICS_ENGINE`, dont ce moteur dépend directement (§4) : les deux moteurs devraient partager la même bibliothèque de modèles plutôt que de dupliquer l'intégration. |
| **iLand** (individual-based forest Landscape and Disturbance model) | Modèle individu-centré pour projeter des trajectoires de peuplement sous scénarios climatiques et perturbations combinées, à l'échelle du paysage | Conçu explicitement pour coupler dynamique forestière et scénarios climatiques/perturbations sur le temps long ; correspond directement aux champs `climate_scenario` et `horizon` du contrat d'entrée (Seidl et al., 2012 ; Rammer & Seidl, 2024) |
| **LANDIS-II** | Simulateur de paysage multi-perturbations (récolte, feu, agents biotiques) à résolution spatio-temporelle flexible, pour produire plusieurs `alternatives` comparables dans un même `SimulationResult` | Sa conception en modules de perturbation interchangeables illustre concrètement la garantie « les scénarios sont comparatifs, pas une projection unique » (Scheller et al., 2007) |
| **ForeFire** (déjà identifié comme dépendance externe, §4) | Formalisation de l'interface ForeFire ↔ Simulation Engine comme cas particulier du contrat générique `ScenarioSimulation`/`SimulationResult` | Moteur de propagation de feu opérationnel développé au CNRS/Université de Corse, déjà utilisé côté Ignis ; traiter ses sorties comme un type de `SimulationResult` parmi d'autres simplifierait la traçabilité des sources exigée par GSIE-CON-005 (Filippi et al., 2011) |
| **SALib** (bibliothèque Python d'analyse de sensibilité : Sobol, Morris, FAST) | Échantillonnage des `parameters` d'entrée suivi d'une analyse de sensibilité globale, pour documenter le champ `confidence` de `SimulationResult` par une mesure statistique plutôt qu'un niveau qualitatif | Une approche de type Monte Carlo est une pratique courante de quantification d'incertitude en modélisation environnementale ; elle rendrait `confidence` traçable et vérifiable (Herman & Usher, 2017 ; Iwanaga et al., 2022) |
| **Couplage simulation ↔ moteur de rendu temps réel (type Unreal Engine)** | Piste pour la sortie « Visualisation » du Simulation Engine vers le Centre de Commandement GSIE (Unreal Engine 5.8) | Des précédents opérationnels et académiques démontrent la faisabilité d'un flux de données depuis un moteur de simulation externe vers un moteur 3D temps réel assurant un rendu géoréférencé interactif, sans que ce dernier ne recalcule la simulation lui-même — voir `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` pour l'architecture retenue côté rendu (Raha et al., 2025, prépublication non revue par les pairs ; *Computers and Electronics in Agriculture*, 2023, pour un précédent revu par les pairs) |

Ces pistes restent complémentaires entre elles : CAPSIS, iLand et LANDIS-II
relèvent du champ de la dynamique forestière (et donc en premier lieu du
Forest Dynamics Engine, dont le Simulation Engine est dépendant selon
§4), tandis que ForeFire, la quantification d'incertitude et le couplage
au moteur de rendu concernent plus directement la responsabilité propre
du Simulation Engine. Aucune de ces pistes ne modifie les garanties
énoncées en §6.

### Sources

- Dufour-Kowalski, S., Courbaud, B., Dreyfus, P., Meredieu, C., de Coligny, F. (2012). *Capsis: an open software framework and community for forest growth modelling*. Annals of Forest Science, 69(2), 221-233. DOI: 10.1007/s13595-011-0140-9 (voir aussi https://capsis.cirad.fr/capsis/presentation)
- Seidl, R., Rammer, W., Scheller, R.M., Spies, T.A. (2012). *An individual-based process model to simulate landscape-scale forest ecosystem dynamics*. Ecological Modelling, 231, 87-100. https://www.sciencedirect.com/science/article/pii/S0304380012000919
- Rammer, W., Seidl, R. (2024). *The individual-based forest landscape and disturbance model iLand: Overview, progress, and outlook*. Ecological Modelling, 495. https://www.sciencedirect.com/science/article/pii/S030438002400173X (https://iland-model.org/)
- Scheller, R.M., Domingo, J.B., Sturtevant, B.R. et al. (2007). *Design, development, and application of LANDIS-II*. Ecological Modelling, 201, 409-419. DOI: 10.1016/j.ecolmodel.2006.10.009. https://www.landis-ii.org/
- Filippi, J.-B. et al. (2011). *Simulation of Coupled Fire/Atmosphere Interaction with the MesoNH-ForeFire Models*. Journal of Combustion, 2011, article 540390. DOI: 10.1155/2011/540390 — code source : https://github.com/forefireAPI/forefire, documentation https://forefire.readthedocs.io/
- Herman, J., Usher, W. (2017). *SALib: An open-source Python library for Sensitivity Analysis*. The Journal of Open Source Software, 2(9), 97. https://github.com/SALib/SALib
- Iwanaga, T., Usher, W., Herman, J. (2022). *Toward SALib 2.0*. Socio-Environmental Systems Modelling. https://github.com/SALib/SALib
- Raha, M.H., Tavakkoli, A.R., Webb, C. et al. (2025). *FIRETWIN: Digital Twin Advancing Multi-Modal Sensing, Interactive Analytics for Tactical Wildfire Response*. Prépublication arXiv:2510.18879 (non revue par les pairs). https://arxiv.org/abs/2510.18879
- *Forest digital twin: A new tool for forest management practices based on Spatio-Temporal Data, 3D simulation Engine, and intelligent interactive environment*. Computers and Electronics in Agriculture, vol. 215, article 108416, 2023. DOI: 10.1016/j.compag.2023.108416

## Références

- `GSIE/ARCHITECTURE/ENGINE_DEVELOPMENT_ORDER.md` — ordre de développement
- `GSIE/ARCHITECTURE/ENGINE_COMMUNICATION_PROTOCOL.md` — protocole d'échange
- `GSIE/ENGINES/FOREST_DYNAMICS_ENGINE/` — modèles de dynamique (dépendance forte)
- `apps/Ignis/REGISTRE.md` — registre d'idées Ignis (J-01, J-02, J-03)
