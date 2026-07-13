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

## Références

- `04_ARCHITECTURE/ENGINE_DEVELOPMENT_ORDER.md` — ordre de développement
- `04_ARCHITECTURE/ENGINE_COMMUNICATION_PROTOCOL.md` — protocole d'échange
- `09_ENGINES/FOREST_DYNAMICS_ENGINE/` — modèles de dynamique (dépendance forte)
- `22_PROJECT_MEMORY/Ignis.md` — registre d'idées Ignis (J-01, J-02, J-03)
