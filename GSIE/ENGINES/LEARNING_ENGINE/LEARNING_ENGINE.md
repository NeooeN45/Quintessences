# Learning Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Learning Engine |
| **Catégorie** | Moteur transverse (apprentissage) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-001, GSIE-CON-004, GSIE-CON-005 |
| **Ordre de développement** | Non listé (moteur transverse) |

---

## 1. Responsabilité

Améliorer continuellement les modèles et calibrations de GSIE à partir
des données terrain validées et des retours d'expérience du forestier,
en restant subordonné aux règles expertes et en garantissant
l'explicabilité de toute sortie.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `VALIDATION_ENGINE` | Sorties bloquées | Échecs de validation pour apprentissage et correction |
| `RECOMMENDATION_ENGINE` | Retours forestier | Décisions du forestier (acceptation, refus, modification) |
| `CORRELATION_ENGINE` | Patterns émergents | Corrélations nouvelles détectées, à valider |
| `KNOWLEDGE_ENGINE` | Connaissances actuelles | Référence pour détecter les écarts et proposer des révisions |
| Observations terrain validées | Données utilisateur | Relevés, inventaires, suivis temporels validés |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Propositions de révision | Connaissances dont le niveau de preuve ou le contenu évolue (sous réserve de validation) |
| `CORRELATION_ENGINE` | Patterns détectés | Nouvelles corrélations candidates pour le croisement |
| Journal d'apprentissage | Trace | Modèles ajustés, calibrations, patterns, avec justification |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `VALIDATION_ENGINE` | Signaux d'échec pour correction |
| Moteur | `RECOMMENDATION_ENGINE` | Retours d'expérience du forestier |
| Moteur | `CORRELATION_ENGINE` | Patterns émergents |
| Moteur | `KNOWLEDGE_ENGINE` | Référence des connaissances actuelles |
| Base | Observations terrain | Données d'apprentissage |

## 5. Contrat d'interface

### Entrée — `LearningSignal`

```
LearningSignal = {
  signal_id  : UUID
  type       : enum { retour_forestier, sortie_bloquee, pattern_emergent, observation_terrain }
  contenu    : structure selon type
  date_signal: ISO 8601
}

RetourForestier = {
  recommandation_id : UUID
  decision     : enum { accepte, refuse, modifie, demande_alternative }
  justification_forestier : texte (optionnel)
  contexte_station : UUID
}

PatternEmergent = {
  description  : texte
  correlations : liste de Correlation
  confiance    : décimal (0,0 à 1,0)
}
```

### Sortie — `LearningOutput`

```
LearningOutput = {
  output_id   : UUID
  type        : enum { proposition_revision, calibration_modele, pattern_confirme }
  description : texte
  justification : liste de texte (chaîne d'apprentissage)
  donnees_source : liste de SourceReference
  confidence  : décimal (0,0 à 1,0)
  connaissances_concernees : liste de UUID (KnowledgeObject)
  date_output : ISO 8601
  statut      : enum { propose, en_validation, valide, rejete }
}
```

## 6. Garanties

- **Toute sortie est explicable et traçable** — le moteur documente la
  chaîne d'apprentissage qui mène à chaque proposition (`GSIE-CON-004`,
  `GSIE-CON-005`).
- **Subordonné aux règles expertes** — l'apprentissage ne remplace
  jamais les règles validées du Knowledge Engine ; il propose des
  révisions qui doivent être validées (`GSIE-CON-004`).
- **L'IA assiste, elle ne décide pas** — le Learning Engine propose,
  le Knowledge Engine (et le processus de validation) décide
  (`GSIE-CON-001`).
- Aucune proposition de révision n'est appliquée automatiquement —
  toute révision passe par un processus documenté.
- Le moteur ne remplace jamais le `KNOWLEDGE_ENGINE` ni le
  `REASONING_ENGINE` (séparation des responsabilités).
- Les propositions rejetées sont archivées pour audit.

## 7. Cas d'usage

### Cas 1 — Apprentissage à partir des refus de recommandation

Sur 50 recommandations de plantation de hêtre en plaine, 35 forestiers
ont refusé au profit du chêne sessile, invoquant le risque de
dépérissement. Le Learning Engine détecte ce pattern : « le hêtre est
sous-estimé en risque de dépérissement en plaine (< 300 m) sur la
période 2020–2025 ». Il propose une révision du niveau de confiance du
hêtre en plaine (baisse de 0,75 à 0,55) avec justification
statistique. La proposition est transmise au Knowledge Engine pour
validation.

### Cas 2 — Calibration d'un modèle de croissance à partir d'observations

Des inventaires répétés sur 20 ans montrent que le modèle de croissance
du chêne sessile surestime l'accroissement de 12 % sur sols acides
superficiels. Le Learning Engine propose une calibration du coefficient
de croissance (réduction de 12 %) pour ce domaine de validité, avec
justification (30 placettes observées, intervalle de confiance 95 %).
La proposition est transmise au Knowledge Engine. L'ancien coefficient
est archivé (`GSIE-CON-010`).

## 8. État de l'art et pistes de recherche sourcées

Cette section recense des méthodes et outils actuels pertinents pour la
responsabilité du Learning Engine — améliorer les modèles et
calibrations de GSIE à partir de données terrain validées et de
retours d'expérience du forestier, sous subordination aux règles
expertes et avec explicabilité garantie. Ces pistes sont documentées
en vue d'une **évaluation en Phase 4** (implémentation) ; aucune n'est
prescrite ni figée à ce stade.

### 8.1 Panorama

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **Apprentissage actif** (active learning), ex. bibliothèque open source **modAL** (Danka & Horváth, 2018) | Sélectionner et prioriser les observations terrain (`LearningSignal` de type `observation_terrain`) à demander au forestier pour réduire au minimum l'incertitude des modèles avec le moins de relevés possible | Les données écologiques de terrain sont rares et coûteuses à collecter ; l'apprentissage actif choisit les échantillons les plus informatifs plutôt que d'exiger une collecte exhaustive — un précédent académique direct est l'estimation active de l'aire de répartition d'espèces (Lange et al., NeurIPS 2023) |
| **Apprentissage continu** (continual learning) par consolidation élastique des poids (*Elastic Weight Consolidation*, EWC — Kirkpatrick et al., PNAS 2017), ou par rejeu d'expérience (ER-PASS, *Remote Sensing*, MDPI, 2025) | Permettre la recalibration d'un modèle sur un nouveau domaine de validité (essence, sol, région) sans dégrader les calibrations déjà validées sur d'autres domaines | Une mise à jour incrémentale « naïve » d'un modèle peut faire régresser des connaissances déjà validées par le Knowledge Engine (oubli catastrophique) ; les méthodes de type EWC ou rejeu d'expérience contraignent la mise à jour pour préserver les paramètres critiques déjà appris |
| **Apprentissage fédéré** (federated learning), ex. cadriciel open source **Flower** (Beutel et al., 2020) | Agréger des signaux d'apprentissage provenant de plusieurs forestiers ou exploitations sans centraliser les données brutes de chaque parcelle | Les données terrain de GSIE sont par nature distribuées entre forestiers et stations ; la littérature sur l'agriculture de précision documente cette approche pour mutualiser l'apprentissage tout en respectant la confidentialité des données (revue *Computers and Electronics in Agriculture*, 2025) |
| **Apprentissage par préférences à partir de retours humains** (principe de la RLHF, Christiano et al., NeurIPS 2017), adapté au retour du forestier (`RetourForestier`) | Transformer les décisions du forestier en signal structuré ajustant le niveau de confiance des recommandations, sans automatiser la décision elle-même | Le principe fondateur « l'IA assiste, ne décide jamais » (`GSIE-CON-001`) impose que le retour humain modifie des paramètres de confiance soumis à validation, jamais une action directe ; précédent proche du domaine : Farmer.Chat (Digital Green) |
| **Modèles de récompense interprétables** pour l'apprentissage par préférences, ex. arbres de décision différentiables appliqués à la RLHF (arXiv:2306.13004) | Garantir que l'ajustement des modèles à partir des retours humains reste documentable étape par étape | La RLHF standard produit typiquement un modèle de récompense peu interprétable ; des architectures de récompense interprétables permettent de documenter la « chaîne d'apprentissage » exigée par les garanties du moteur (`GSIE-CON-004`, `GSIE-CON-005`) |

### 8.2 Lecture transversale

- Les quatre axes demandés (apprentissage actif, apprentissage continu,
  apprentissage fédéré, retour d'expert humain) correspondent à des
  sous-problèmes distincts et peuvent être adoptés indépendamment.
- Dans tous les cas, la contrainte constitutionnelle d'explicabilité
  (`GSIE-CON-004`, `GSIE-CON-005`) reste première : toute méthode
  retenue en Phase 4 devra produire une sortie conforme au contrat
  `LearningOutput` (avec `justification` et `donnees_source`), quelle
  que soit sa sophistication interne.
- Ces pistes ne présument pas d'un choix de bibliothèque ni
  d'architecture définitive ; elles indiquent des familles de méthodes
  dont la maturité est suffisante pour être évaluées lors de la
  spécification détaillée en Phase 4.

### Sources

- Lange, C., Cole, E., Van Horn, G., Mac Aodha, O. (2023). « Active Learning-Based Species Range Estimation ». NeurIPS 2023. arXiv:2311.02061. https://arxiv.org/abs/2311.02061
- Danka, T., Horváth, P. (2018). « modAL: A modular active learning framework for Python ». arXiv:1805.00979. https://arxiv.org/abs/1805.00979 (projet : https://github.com/modAL-python/modAL)
- Kirkpatrick, J. et al. (2017). « Overcoming catastrophic forgetting in neural networks ». Proceedings of the National Academy of Sciences, 114(13), 3521–3526. https://www.pnas.org/doi/10.1073/pnas.1611835114
- « ER-PASS: Experience Replay with Performance-Aware Submodular Sampling for Domain-Incremental Learning in Remote Sensing » (2025). Remote Sensing (MDPI), 17(18), 3233. https://www.mdpi.com/2072-4292/17/18/3233
- Beutel, D. J., Topal, T., Mathur, A. et al. (2020). « Flower: A Friendly Federated Learning Research Framework ». arXiv:2007.14390. https://arxiv.org/abs/2007.14390 (projet : https://flower.ai)
- « Agricultural data privacy and federated learning: A review of challenges and opportunities » (2025). Computers and Electronics in Agriculture, 232. https://www.sciencedirect.com/science/article/pii/S0168169925001541
- Christiano, P. F., Leike, J., Brown, T. et al. (2017). « Deep Reinforcement Learning from Human Preferences ». NeurIPS 2017. arXiv:1706.03741. https://arxiv.org/abs/1706.03741
- « Can Differentiable Decision Trees Enable Interpretable Reward Learning from Human Feedback? » (2023). arXiv:2306.13004. https://arxiv.org/abs/2306.13004
- « Application of reinforcement learning from human feedback for localizing quality agricultural advice using generative AI » (Digital Green, Farmer.Chat). Advancements in Agricultural Development. https://agdevresearch.org/index.php/aad/article/view/625

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
