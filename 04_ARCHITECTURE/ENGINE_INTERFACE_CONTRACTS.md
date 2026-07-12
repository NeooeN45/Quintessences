# Contrats d'interface des 14 moteurs — Matrice d'interactions

| Champ | Valeur |
|---|---|
| **Document** | ENGINE_INTERFACE_CONTRACTS |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-004, GSIE-CON-005, GSIE-CON-007 |

---

## Matrice d'interactions

Lecture : la ligne **émet** vers la colonne **récepteur**. Une case vide
signifie aucune interaction directe.

| Émetteur \ Récepteur | Evid. | Know. | Correl. | Reas. | Diag. | Recom. | Valid. | GIS | Clim. | Pedol. | Botan. | ForestDyn. | Learn. | Simul. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Evidence** | — | ✅ | | | | | | | | | | | ✅ | |
| **Knowledge** | | — | ✅ | ✅ | | | | | | | | | | |
| **Correlation** | | | — | ✅ | | | | | | | | | ✅ | |
| **Reasoning** | | ✅ | | — | ✅ | | | | | | | | | |
| **Diagnostic** | | | | | — | ✅ | | | | | | | | ✅ |
| **Recommendation** | | | | | | — | ✅ | | | | | | | ✅ |
| **Validation** | | | | | | | — | | | | | | ✅ | |
| **GIS** | | | | | ✅ | | | — | | | | | | ✅ |
| **Climate** | | | | | ✅ | | | | — | | | | | ✅ |
| **Pedology** | | | | | ✅ | | | | | — | | | | ✅ |
| **Botanical** | | | | | ✅ | | | | | | — | | | ✅ |
| **ForestDyn** | | | | | ✅ | | | | | | | — | | ✅ |
| **Learning** | ✅ | ✅ | | | | | | | | | | | — | |
| **Simulation** | | | | | | | ✅ | | | | | | ✅ | — |

Légende : ✅ = flux de données direct entre les deux moteurs.

---

## Détail des flux par moteur

### Evidence Engine (filtre amont)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Connaissance qualifiée | Knowledge Engine | `QualifiedKnowledge` | Connaissance + niveau de preuve + source + version |
| Signaux de réévaluation | Learning Engine | `ReassessmentSignal` | Connaissances dont le niveau de preuve peut évoluer |

### Knowledge Engine (centralisation)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Base de connaissances | Correlation Engine | `KnowledgeQuery` | Réponses aux requêtes de corrélation |
| Base de connaissances | Reasoning Engine | `KnowledgeQuery` | Réponses aux requêtes de raisonnement |

### Correlation Engine (corrélations)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Corrélations détectées | Reasoning Engine | `CorrelationSet` | Ensemble de corrélations multiparamètres |
| Corrélations | Learning Engine | `CorrelationFeedback` | Corrélations à valider/ajuster par apprentissage |

### Reasoning Engine (raisonnement)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Requête de connaissance | Knowledge Engine | `KnowledgeQuery` | Demande de connaissances contextuelles |
| Conclusions raisonnées | Diagnostic Engine | `ReasoningOutput` | Inférences prêtes pour le diagnostic |

### Diagnostic Engine (diagnostic)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Diagnostic | Recommendation Engine | `DiagnosticReport` | État diagnostiqué + problèmes identifiés |
| État courant | Simulation Engine | `SystemState` | État du système pour simulation |

### Recommendation Engine (recommandations)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Recommandations | Validation Engine | `RecommendationSet` | Recommandations contournables + alternatives |
| Scénarios d'intervention | Simulation Engine | `InterventionSpec` | Actions à simuler |

### Validation Engine (validation)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Sorties validées | Utilisateur | `ValidatedOutput` | Recommandations validées + sources + niveau de confiance |
| Écarts détectés | Learning Engine | `ValidationGap` | Écarts entre attendu et observé |

### Moteurs domaine (GIS, Climate, Pedology, Botanical, Forest Dynamics)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Données domaine | Diagnostic Engine | `DomainData` | Données spatiales, climatiques, pédologiques, floristiques, dynamique |
| Données domaine | Simulation Engine | `DomainData` | Conditions aux limites pour les scénarios |

### Learning Engine (apprentissage)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Réévaluation de preuve | Evidence Engine | `ReassessmentRequest` | Mise à jour du niveau de preuve d'une connaissance |
| Mises à jour de connaissances | Knowledge Engine | `KnowledgeUpdate` | Connaissances ajustées par apprentissage |

### Simulation Engine (simulation)

| Sortie | Destinataire | Format | Description |
|---|---|---|---|
| Résultats de simulation | Validation Engine | `SimulationResult` | Projections temporelles + confiance + sources |
| Comparatif de scénarios | Recommendation Engine | `ScenarioComparison` | Scénarios alternatifs comparés |
| Écarts simulation/réalité | Learning Engine | `SimulationGap` | Écarts pour calibration des modèles |

---

## Principes d'interface

1. **Aucun moteur ne connaît les détails internes d'un autre** (GSIE-CON-007).
   Chaque échange passe par un contrat de données explicite.

2. **Tous les flux sont tracés** (GSIE-CON-005). Chaque message porte
   un identifiant de source et un horodatage.

3. **Toutes les sorties sont explicables** (GSIE-CON-004). Chaque
   recommandation ou diagnostic cite les moteurs et sources qui l'ont
   produite.

4. **Communication asynchrone par défaut**. Les moteurs domaine
   répondent en temps différé. La chaîne d'intelligence (Evidence →
   Validation) peut être synchrone pour les flux temps réel (GSIE-Ignis).

5. **Offline-first**. Les moteurs communiquent par messages persistés.
   En cas de coupure réseau, les messages sont mis en file et traités
   à la reconnexion.

---

## Références

- `09_ENGINES/*/` — documentation détaillée de chaque moteur
- `04_ARCHITECTURE/ENGINE_COMMUNICATION_PROTOCOL.md` — protocole d'échange
- `04_ARCHITECTURE/GSIE_DATA_FLOW.md` — flux de données global
- `04_ARCHITECTURE/ENGINE_DEVELOPMENT_ORDER.md` — ordre de développement
