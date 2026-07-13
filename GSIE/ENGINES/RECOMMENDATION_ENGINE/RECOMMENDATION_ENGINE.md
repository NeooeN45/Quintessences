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

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de pistes pour la Phase 4
(implémentation), des travaux et systèmes existants pertinents pour la
responsabilité exacte du Recommendation Engine : produire des
recommandations sylvicoles contournables, assorties d'alternatives
justifiées, à partir de diagnostics et de simulations, en documentant
les refus du forestier. La recherche a porté sur quatre axes : les
systèmes d'aide à la décision (DSS) forestiers, l'analyse
multicritère appliquée à la sylviculture, les approches de
recommandation adaptées aux décisions rares et à fort enjeu (par
opposition aux recommandeurs de type e-commerce), et la traçabilité
des refus/alternatives.

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **EMDS — Ecosystem Management Decision Support System** (v8.0) | Architecture de référence combinant raisonnement logique (NetWeaver), analyse multicritère et traçabilité native des étapes d'analyse | EMDS est un DSS environnemental opérationnel, développé et maintenu depuis 1997 par le Pacific Northwest Research Station (USDA Forest Service). Sa version 8.0 (Reynolds et al., 2023) expose un mécanisme de suivi de provenance permettant de rejouer chaque étape d'une analyse — un précédent directement transposable à `JustificationRecommandation` et à la documentation des `ForestierDecision`. |
| **Heureka (SLU, Suède)** | Précédent d'architecture pour l'articulation Diagnostic → Simulation → Recommandation dans un DSS forestier opérationnel | Heureka est un DSS forestier utilisé depuis plus de 15 ans en recherche, enseignement et gestion forestière opérationnelle en Suède (Lämås et al., 2023). Il couple simulateur de peuplement, module d'optimisation et analyse régionale — une organisation proche de la dépendance du Recommendation Engine envers `SIMULATION_ENGINE` et `FOREST_DYNAMICS_ENGINE`. |
| **AHP couplé à PROMETHEE (analyse multicritère hybride)** | Pondération des critères de décision (`objectif_forestier`, `contraintes_forestier`) par AHP, puis classement des alternatives sylvicoles par surclassement (outranking) avec PROMETHEE | Lakićević, Reynolds et Gawryszewska (2021) démontrent, sur un cas de gestion paysagère/forestière, l'intégration d'AHP et de PROMETHEE. Cette combinaison correspond structurellement au besoin de produire une recommandation principale et plusieurs alternatives classées, chacune avec un `niveau_confiance` explicite. |
| **Argumentation computationnelle pour la décision explicable et contestable** | Structuration formelle des justifications et des refus : chaque recommandation et chaque alternative devient un argument attaquable/défendable, les refus du forestier deviennent des contestations tracées | Dejl, Williams et Toni (2026, preprint arXiv) proposent un cadre (ArgEval) distinguant la contestation locale (une décision) de la contestation globale (la logique de décision sous-jacente) — une piste pertinente pour transformer `ForestierDecision.decision = refuse` en signal exploitable par `LEARNING_ENGINE`. Sassoon, Kökciyan, Modgil et Parsons (2021) montrent, en aide à la décision clinique, comment des schémas d'argumentation structurent des alternatives concurrentes et leurs justifications. |
| **Raisonnement à partir de cas (Case-Based Reasoning, CBR)** | Réutilisation de diagnostics/recommandations antérieurs similaires comme point de départ argumenté, adapté aux décisions rares et non répétées | Le CBR (Aamodt et Plaza, 1994) est conçu pour des problèmes de décision faiblement structurés où l'expérience passée sert de justification explicite plutôt que de corrélation statistique — mieux adapté qu'un recommandeur classique à des décisions sylvicoles peu fréquentes, à fort enjeu et fortement contextuelles. |
| **W3C PROV-O (PROV Ontology)** | Modèle standard pour tracer la provenance d'une recommandation : quelles données, quelles règles, quelles versions de moteurs ont produit `JustificationRecommandation` | PROV-O est une recommandation W3C (Lebo, Sahoo et McGuinness, éds., 2013) modélisant entités, activités et agents. Également cité dans les sections équivalentes du `KNOWLEDGE_ENGINE` et du `VALIDATION_ENGINE` — une seule modélisation centralisée du vocabulaire de provenance, réutilisée par les trois moteurs, éviterait une triple redondance d'implémentation. |

Ces pistes restent à évaluer et arbitrer en Phase 4 ; aucune ne
constitue un choix d'implémentation arrêté. En particulier, le choix
entre AHP/PROMETHEE, un cadre d'argumentation ou une architecture de
type EMDS n'est pas tranché ici — il dépendra des contraintes
retenues lors de la spécification détaillée (`05_SPECIFICATIONS/`) et
de la disponibilité de règles sylvicoles formalisées dans le
Knowledge Engine.

À noter : EMDS et **NED-2** (cité dans la section équivalente du
`REASONING_ENGINE`) proviennent tous deux de l'écosystème USDA Forest
Service et occupent des positions adjacentes dans la chaîne
Reasoning → Recommendation ; une évaluation conjointe des deux
précédents en Phase 4 est plus pertinente qu'une évaluation isolée.

### Sources

- Reynolds, K. M., Paplanus, S., Murphy, P. J. et al. (2023). *Latest features of the ecosystem management decision support system, version 8.0*. Frontiers in Environmental Science, 11:1231818. https://doi.org/10.3389/fenvs.2023.1231818
- Lämås, T., Sängstuvall, L., Öhman, K. et al. (2023). *The multi-faceted Swedish Heureka forest decision support system*. Frontiers in Forests and Global Change, 6:1163105. https://doi.org/10.3389/ffgc.2023.1163105
- Lakićević, M. D., Reynolds, K. M., & Gawryszewska, B. J. (2021). *An integrated application of AHP and PROMETHEE in decision making for landscape management*. Austrian Journal of Forest Science, 138(3), 167–182. https://research.fs.usda.gov/treesearch/63769
- Dejl, A., Williams, M., & Toni, F. (2026). *Argumentation for Explainable and Globally Contestable Decision Support with LLMs*. arXiv:2603.14643 (preprint). https://arxiv.org/abs/2603.14643
- Sassoon, I., Kökciyan, N., Modgil, S., & Parsons, S. (2021). *Argumentation schemes for clinical decision support*. Argument & Computation, 12(3). https://doi.org/10.3233/AAC-200550
- Aamodt, A., & Plaza, E. (1994). *Case-Based Reasoning: Foundational Issues, Methodological Variations, and System Approaches*. AI Communications, 7(1), 39–59. https://www.iiia.csic.es/~enric/papers/AICom.pdf
- Lebo, T., Sahoo, S., & McGuinness, D. (éds.) (2013). *PROV-O: The PROV Ontology*. W3C Recommendation. https://www.w3.org/TR/2013/REC-prov-o-20130430/
- Yadav, N., Rakholia, S., & Yosef, R. (2024). *Decision Support Systems in Forestry and Tree-Planting Practices and the Prioritization of Ecosystem Services: A Review*. Land, 13(2), 230. https://doi.org/10.3390/land13020230

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
