# Validation Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Validation Engine |
| **Catégorie** | Chaîne d'intelligence (contrôle final) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-001, GSIE-CON-004, GSIE-CON-005 |
| **Ordre de développement** | 13 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Vérifier la cohérence, la conformité constitutionnelle et la complétude
des diagnostics et recommandations avant leur présentation à
l'utilisateur, en bloquant toute sortie non conforme.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `RECOMMENDATION_ENGINE` | Recommandations | Ensemble de recommandations à valider |
| `DIAGNOSTIC_ENGINE` | Diagnostic | Diagnostic à valider |
| `REASONING_ENGINE` | Chaînes d'inférence | Vérification de la cohérence logique |
| `KNOWLEDGE_ENGINE` | Vérification de validité | Contrôle que les connaissances utilisées sont à jour et valides |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| Utilisateur (via interface) | Sortie validée | Diagnostic et/ou recommandations conformes, prêts pour présentation |
| Journal d'audit | Sorties bloquées | Sorties non conformes avec cause de blocage |
| `LEARNING_ENGINE` | Signaux d'échec | Sorties bloquées pour apprentissage et amélioration |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `RECOMMENDATION_ENGINE` | Sorties à valider |
| Moteur | `DIAGNOSTIC_ENGINE` | Diagnostics à valider |
| Moteur | `REASONING_ENGINE` | Chaînes d'inférence à vérifier |
| Moteur | `KNOWLEDGE_ENGINE` | Contrôle de validité des connaissances utilisées |

## 5. Contrat d'interface

### Entrée — `ValidationRequest`

```
ValidationRequest = {
  requete_id    : UUID
  type_sortie   : enum { diagnostic, recommandation, ensemble_complet }
  contenu       : Diagnostic ou RecommendationSet
  chaines_inference : liste de Conclusion (optionnel)
  connaissances_utilisees : liste de UUID (KnowledgeObject)
}
```

### Sortie — `ValidationResult`

```
ValidationResult = {
  validation_id : UUID
  requete_origine : UUID
  statut        : enum { valide, bloque, partiellement_valide }
  controles     : liste de ControleResultat
  causes_blocage : liste de CauseBlocage (si statut = bloque)
  date_validation : ISO 8601
}

ControleResultat = {
  nom_controle  : texte
  resultat      : enum { conforme, non_conforme, non_applicable }
  details       : texte
}

CauseBlocage = {
  type_cause    : enum {
    sans_niveau_preuve,
    sans_source,
    sans_chaine_inference,
    hors_domaine_validite,
    connaissance_obsolete,
    contradiction_non_signalee,
    recommandation_non_contournable,
    explicabilite_insuffisante
  }
  element_concerne : UUID
  description   : texte
}
```

## 6. Garanties

- **Aucune sortie n'atteint l'utilisateur sans validation** — la
  validation est le dernier rempart (principe fondateur).
- Toute sortie validée respecte la Constitution : explicabilité
  (`GSIE-CON-004`), traçabilité (`GSIE-CON-005`), niveaux de preuve
  affichés (`GSIE-CON-002`), recommandations contournables
  (`GSIE-CON-001`).
- Toute sortie bloquée est journalisée avec la cause précise de
  blocage.
- Le moteur ne produit **pas de contenu** — il valide et filtre
  (séparation des responsabilités).
- Les connaissances obsolètes ou invalidées sont détectées et signalées.
- Les sorties hors domaine de validité sont bloquées avec justification.

## 7. Cas d'usage

### Cas 1 — Blocage d'une recommandation sans niveau de preuve

Le Recommendation Engine produit une recommandation de plantation
d'eucalyptus. Le Validation Engine détecte qu'aucune source
scientifique ne justifie l'adaptation de l'eucalyptus à la station
(règle non sourcée). Cause de blocage : `sans_niveau_preuve` et
`sans_source`. La recommandation est bloquée et journalisée. L'erreur
est transmise au Learning Engine pour amélioration.

### Cas 2 — Validation d'un diagnostic complet

Un diagnostic de dépérissement de hêtraie est soumis. Le Validation
Engine vérifie : (1) toutes les contraintes ont un niveau de preuve →
conforme, (2) toutes les sources sont identifiées → conforme, (3) les
chaînes d'inférence sont complètes → conforme, (4) les connaissances
utilisées sont à jour (version courante du Knowledge Engine) →
conforme, (5) le diagnostic est étiqueté « diagnostic » et non
« décision » → conforme. Statut : `valide`. Le diagnostic est présenté
au forestier.

## 8. État de l'art et pistes de recherche sourcées

Cette section recense des technologies, méthodes et standards existants
et vérifiables, pertinents pour la responsabilité exacte du Validation
Engine (cohérence, conformité constitutionnelle, complétude, blocage
des sorties non conformes). Il s'agit de **pistes de recherche pour la
Phase 4** (implémentation future) — aucune n'est prescrite comme choix
définitif, et aucun détail de code ou d'intégration n'est fixé ici.

Les axes couverts correspondent aux garanties déjà documentées en §6 :
explicabilité (`GSIE-CON-004`), contournabilité des recommandations
(`GSIE-CON-001`), traçabilité (`GSIE-CON-005`) et détection des sorties
non conformes ou incomplètes.

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **SHAP** (SHapley Additive exPlanations) — ou **LIME** (Local Interpretable Model-agnostic Explanations) comme alternative plus légère | Quantifier la contribution des connaissances et critères mobilisés par le Reasoning/Diagnostic Engine à une conclusion, pour objectiver le contrôle `explicabilite_insuffisante` | SHAP (valeurs de Shapley, théorie des jeux) et LIME (approximation locale par modèle interprétable) sont toutes deux model-agnostic et devenues des références en IA explicable post-hoc ; SHAP offre une cohérence théorique plus forte, LIME un coût de calcul plus faible — le choix entre les deux (ou leur combinaison) reste à arbitrer en Phase 4 (Lundberg & Lee, 2017 ; Ribeiro, Singh & Guestrin, 2016) |
| **Explications contrefactuelles** (cadre de Wachter et al. ; bibliothèque DiCE) | Générer l'ensemble minimal de changements qui inverserait une conclusion, pour vérifier qu'une recommandation reste « contournable » au sens de `GSIE-CON-001` | Le cadre contrefactuel a été formalisé pour répondre à l'exigence de contestabilité des décisions automatisées (RGPD) ; DiCE (Microsoft Research) outille la génération de contrefactuels divers et actionnables, un principe transposable au contrôle de contournabilité déjà listé comme cause de blocage (`recommandation_non_contournable`) (Wachter, Mittelstadt & Russell, 2017 ; Mothilal, Sharma & Tan, 2020) |
| **Validation humaine dans la boucle** (human-in-the-loop) | Formaliser, en amont ou en aval du Validation Engine, le point de contrôle où le forestier confirme, rejette ou surcharge une sortie déjà validée automatiquement | Les revues récentes sur l'IA en agriculture et foresterie de précision indiquent que les architectures human-in-the-loop améliorent la robustesse et la confiance perçue par rapport à des pipelines pleinement automatisés, tout en restant compatibles avec le principe « l'IA assiste, ne décide jamais » (`GSIE-CON-001`) |
| **PROV-O** (W3C PROV Ontology) | Modéliser formellement la provenance des `connaissances_utilisees`, des `chaines_inference` et des décisions de blocage consignées dans le journal d'audit | Recommandation W3C définissant un modèle générique entité/activité/agent pour représenter la provenance de données et de décisions ; aligné sur l'exigence de traçabilité (`GSIE-CON-005`). Également cité dans les sections équivalentes du `KNOWLEDGE_ENGINE` et du `RECOMMENDATION_ENGINE` — une seule modélisation centralisée du vocabulaire de provenance, réutilisée par les trois moteurs, éviterait une triple redondance d'implémentation. |
| **SHACL** (Shapes Constraint Language) | Vérifier déclarativement la complétude structurelle des objets `ValidationRequest`/`ValidationResult` (présence obligatoire d'une source, d'un niveau de preuve, d'une chaîne d'inférence) | Standard W3C de validation de graphes par « shapes », permettant d'exprimer des contraintes de cardinalité, de type et de présence sans coder de logique ad hoc ; transposable aux contrôles de complétude déjà listés en §6 comme vérification déclarative plutôt qu'impérative |
| **Open Policy Agent (OPA) / Rego** | Encoder les règles de blocage constitutionnelles (`sans_source`, `hors_domaine_validite`, `connaissance_obsolete`, etc.) comme politiques déclaratives versionnées, distinctes du code applicatif | Moteur de politique-as-code largement adopté qui découple la décision de politique de son application ; illustre une architecture où les règles de blocage pourraient être révisées via un processus de gouvernance (RFC) sans modifier l'implémentation |

Ces pistes ne s'excluent pas mutuellement : une architecture de
Validation Engine pourrait, par exemple, combiner un moteur de
contraintes déclaratif (SHACL ou OPA) pour la complétude structurelle,
une couche d'attribution (SHAP/LIME) et de contrefactuels (DiCE) pour
les contrôles d'explicabilité et de contournabilité, un modèle de
provenance (PROV-O) pour le journal d'audit, et un point de validation
humaine en périphérie du moteur. Le choix précis, l'articulation entre
ces briques et leur éventuelle implémentation relèvent de la Phase 4 et
devront faire l'objet d'une spécification dédiée.

### Sources

- Lundberg, S. M. & Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions* (SHAP). NeurIPS 2017. https://christophm.github.io/interpretable-ml-book/shap.html
- Ribeiro, M. T., Singh, S. & Guestrin, C. (2016). *"Why Should I Trust You?" Explaining the Predictions of Any Classifier* (LIME). ACM SIGKDD 2016. https://christophm.github.io/interpretable-ml-book/lime.html
- Wachter, S., Mittelstadt, B. & Russell, C. (2017). *Counterfactual Explanations Without Opening the Black Box: Automated Decisions and the GDPR*. Harvard Journal of Law & Technology, 31, 842-887. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3063289
- Mothilal, R. K., Sharma, A. & Tan, C. (2020). *Explaining Machine Learning Classifiers through Diverse Counterfactual Explanations* (DiCE). ACM FAccT 2020. arXiv:1905.07697 — bibliothèque : github.com/interpretml/DiCE
- MDPI *Sensors* (2022). *Digital Transformation in Smart Farm and Forest Operations Needs Human-Centered AI: Challenges and Future Directions*. https://www.mdpi.com/1424-8220/22/8/3043
- W3C (2013). *PROV-O: The PROV Ontology*, W3C Recommendation. https://www.w3.org/TR/prov-o/
- W3C (2017). *Shapes Constraint Language (SHACL)*, W3C Recommendation. https://www.w3.org/TR/shacl/
- Open Policy Agent — documentation officielle du projet (CNCF). https://www.openpolicyagent.org/docs

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
