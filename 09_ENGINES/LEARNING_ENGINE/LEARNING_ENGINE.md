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

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
