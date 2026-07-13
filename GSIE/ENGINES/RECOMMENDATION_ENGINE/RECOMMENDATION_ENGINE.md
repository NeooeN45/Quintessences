# Recommendation Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Recommendation Engine |
| **Catégorie** | Chaîne d'intelligence (proposition d'action) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-001, GSIE-CON-004 |
| **Ordre de développement** | 12 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Produire des recommandations sylvicoles contournables à partir des
diagnostics et des simulations, en proposant systématiquement des
alternatives justifiées et en documentant les refus du forestier.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Diagnostic | État de la station, contraintes, atouts, risques |
| `SIMULATION_ENGINE` | Scénarios projetés | Effets attendus des interventions sur le long terme |
| `BOTANICAL_ENGINE` | Données botaniques | Autécologie des essences candidates |
| `KNOWLEDGE_ENGINE` | Règles sylvicoles | Guides sylvicoles, itinéraires techniques, règles de gestion |
| `FOREST_DYNAMICS_ENGINE` | Modèles de croissance | Projections de croissance par essence |
| Retours forestier | Décisions utilisateur | Refus, modifications, écarts enregistrés |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `VALIDATION_ENGINE` | Recommandations | Propositions validées avant présentation |
| `SIMULATION_ENGINE` | Scénarios à simuler | Demandes de projection pour comparaison d'alternatives |
| `LEARNING_ENGINE` | Retours d'expérience | Écarts entre recommandations et décisions du forestier |
| Utilisateur (via interface) | Recommandations présentées | Propositions avec alternatives, justifications et confiance |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `DIAGNOSTIC_ENGINE` | Diagnostic de la station (obligatoire) |
| Moteur | `SIMULATION_ENGINE` | Projections pour comparer les alternatives |
| Moteur | `BOTANICAL_ENGINE` | Autécologie des essences candidates |
| Moteur | `KNOWLEDGE_ENGINE` | Règles et itinéraires sylvicoles |
| Moteur | `FOREST_DYNAMICS_ENGINE` | Modèles de croissance |

## 5. Contrat d'interface

### Entrée — `RecommendationRequest`

```
RecommendationRequest = {
  requete_id     : UUID
  diagnostic_id  : UUID
  objectif_forestier : enum { production, protection, biodiversite, mixte, reboisement }
  contraintes_forestier : liste de texte (préférences du forestier, optionnel)
  alternatives_demandees : booléen (défaut : vrai)
}
```

### Sortie — `RecommendationSet`

```
RecommendationSet = {
  ensemble_id    : UUID
  requete_origine: UUID
  diagnostic_source : UUID
  recommandations : liste de Recommendation
  date_generation: ISO 8601
}

Recommendation = {
  recommandation_id : UUID
  type_action   : enum { plantation, eclaircie, coupe_rase, regeneration, protection, intervention_sanitaire, attente_surveillance }
  description   : texte (ex. « planter du chêne sessile, densité 1100 t/ha »)
  essence_concernee : texte (optionnel)
  parametres    : map (clé-valeur : densité, période, surface, etc.)
  justification : JustificationRecommandation
  alternatives  : liste de Recommendation (optionnel — alternatives de rang inférieur)
  niveau_confiance : décimal (0,0 à 1,0)
  scenario_projection : UUID (référence vers Simulation Engine, optionnel)
  contournable  : booléen (toujours vrai — GSIE-CON-001)
}

JustificationRecommandation = {
  diagnostic_ref : UUID
  connaissances_utilisees : liste de UUID (KnowledgeObject)
  regles_appliquees : liste de texte
  sources : liste de SourceReference
  facteurs_limitants : liste de texte
  moteurs_solicites : liste de texte
}
```

### Retour forestier — `ForestierDecision`

```
ForestierDecision = {
  recommandation_id : UUID
  decision      : enum { accepte, refuse, modifie, demande_alternative }
  justification_forestier : texte (optionnel)
  modifications : map (optionnel — paramètres modifiés)
  date_decision : ISO 8601
}
```

## 6. Garanties

- **Toute recommandation est contournable** — le forestier peut refuser,
  modifier ou demander une alternative (`GSIE-CON-001`).
- **Plusieurs alternatives** sont systématiquement proposées, pas une
  seule option (principe fondateur).
- Chaque recommandation est justifiée par le diagnostic, les
  connaissances et les règles sous-jacentes (`GSIE-CON-004`).
- Aucune recommandation n'est étiquetée comme « décision » — GSIE
  recommande, le forestier décide (`GSIE-CON-001`).
- Les refus et écarts du forestier sont documentés pour traçabilité et
  apprentissage (`GSIE-CON-005`).
- Le niveau de confiance et les facteurs limitants sont affichés pour
  chaque recommandation.

## 7. Cas d'usage

### Cas 1 — Recommandation de reboisement après coupe rase

Sur une station à pH 5,8, altitude 400 m, sol profond, le Diagnostic
Engine indique un état sain avec risque d'érosion modéré. Le
Recommendation Engine propose :
- **Recommandation principale** : planter du chêne sessile, densité
  1100 t/ha, confiance 0,82. Justification : pH et profondeur favorables
  (Rameau et al., 2018), précipitations adéquates (ONF, 2020).
- **Alternative 1** : planter du hêtre, densité 1200 t/ha, confiance
  0,68. Justification : pH favorable mais risque de déficit hydrique à
  long terme.
- **Alternative 2** : mélange chêne sessile + hêtre (50/50), confiance
  0,75. Justification : diversification du risque.

Le forestier choisit l'alternative 2. La décision est enregistrée avec
l'écart par rapport à la recommandation principale.

### Cas 2 — Recommandation d'éclaircie sur un peuplement dense

Un peuplement de douglas de 35 ans présente une densité excessive
(densité relative 1,3). Le Recommendation Engine propose une éclaircie
modérée (prélèvement 25 %), confiance 0,78, justifiée par le guide
sylvicole du douglas (ONF, 2019). Alternative : éclaircie forte
(35 %), confiance 0,65, avec risque de destabilisation. Le forestier
peut refuser, modifier le pourcentage ou demander une simulation
comparative via le Simulation Engine.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
