# Reasoning Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Reasoning Engine |
| **Catégorie** | Chaîne d'intelligence (inférence) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-004, GSIE-CON-005 |
| **Ordre de développement** | 10 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Appliquer des règles d'inférence explicites et auditées sur les
connaissances et corrélations qualifiées pour produire des conclusions
expliquées et traçables, sans jamais inventer de règle.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Connaissances normalisées | Concepts, relations, règles d'inférence, seuils sourcés |
| `CORRELATION_ENGINE` | Matrice de corrélations | Relations statistiques significatives et sourcées |
| `GIS_ENGINE` | Données géospatiales | Caractéristiques stationnelles (pente, exposition, altitude) |
| `CLIMATE_ENGINE` | Données climatiques | Variables bioclimatiques de la station |
| `PEDOLOGY_ENGINE` | Données pédologiques | Caractéristiques du sol de la station |
| `BOTANICAL_ENGINE` | Données botaniques | Autécologie des essences présentes ou candidates |
| `FOREST_DYNAMICS_ENGINE` | Données de peuplement | État et dynamique du peuplement |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Conclusions inférées | Déductions logiques avec chaîne d'inférence complète |
| `RECOMMENDATION_ENGINE` | Conclusions inférées | Conclusions exploitables pour la recommandation |
| `VALIDATION_ENGINE` | Chaînes d'inférence | Vérification de la cohérence logique des sorties |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `KNOWLEDGE_ENGINE` | Règles et connaissances de référence (obligatoire) |
| Moteur | `CORRELATION_ENGINE` | Corrélations statistiques (obligatoire) |
| Moteur | `GIS_ENGINE` | Données stationnelles géospatiales |
| Moteur | `CLIMATE_ENGINE` | Données bioclimatiques |
| Moteur | `PEDOLOGY_ENGINE` | Données pédologiques |
| Moteur | `BOTANICAL_ENGINE` | Données autécologiques |
| Moteur | `FOREST_DYNAMICS_ENGINE` | Données de peuplement |

## 5. Contrat d'interface

### Entrée — `ReasoningRequest`

```
ReasoningRequest = {
  requete_id     : UUID
  station_id     : UUID (optionnel)
  contexte       : StationContexte
  question       : texte (ex. « quelles essences sont adaptées à cette station ? »)
  profondeur_max : entier (limite de profondeur de la chaîne d'inférence)
}

StationContexte = {
  geographie  : donnees GIS (pente, exposition, altitude, coordonnees)
  climat      : donnees bioclimatiques (temperatures, precipitations, deficit)
  pedologie   : donnees sol (pH, texture, profondeur, drainage, RUM)
  botanique   : essences presentes, vegetation accompagnatrice
  peuplement  : donnees Forest Dynamics (age, densite, croissance)
  correlations: liste de Correlation (issues du Correlation Engine)
}
```

### Sortie — `InferenceResult`

```
InferenceResult = {
  resultat_id    : UUID
  requete_origine: UUID
  conclusions    : liste de Conclusion
  contradictions : liste de ContradictionDetectee (optionnel)
  date_inférence : ISO 8601
}

Conclusion = {
  conclusion_id  : UUID
  enonce         : texte (ex. « le hêtre est adapté à cette station »)
  niveau_confiance : décimal (0,0 à 1,0)
  chaine_inference : liste de EtapeInference
  sources_utilisees : liste de SourceReference
  connaissances_utilisees : liste de UUID (KnowledgeObject)
  moteurs_solicites : liste de texte
}

EtapeInference = {
  ordre        : entier (1, 2, 3…)
  regle_appliquee : texte (description de la règle)
  source_regle : SourceReference
  premisses    : liste de texte (faits ou conclusions antérieurs)
  conclusion_locale : texte
}

ContradictionDetectee = {
  conclusion_a : UUID
  conclusion_b : UUID
  description  : texte
}
```

## 6. Garanties

- **Aucun raisonnement n'est produit sans chaîne d'inférence
  documentée** (principe fondateur).
- Le moteur n'invente **aucune règle** — il applique uniquement les
  règles scientifiquement validées du Knowledge Engine (`GSIE-CON-002`).
- Toute conclusion est explicable : pourquoi, avec quelles données,
  selon quelles règles, avec quel niveau de confiance, quelles limites
  (`GSIE-CON-004`).
- Les contradictions dans le raisonnement sont détectées et signalées,
  jamais résolues arbitrairement.
- Le moteur ne produit **pas de diagnostic ni de recommandation** — il
  fournit des conclusions (séparation des responsabilités).
- Fonctionnement hors-ligne complet (article T-8).

## 7. Cas d'usage

### Cas 1 — Inférence d'adaptation du chêne sessile sur une station

Le Reasoning Engine reçoit le contexte d'une station : pH 5,2, altitude
320 m, précipitations 850 mm/an, sol sablonneux profond. Il applique la
règle « le chêne sessile est adapté aux sols acides à modérément acides
(pH 4,5–6,0) » (source : Rameau et al., 2018, evidence B) et la règle
« le chêne sessile tolère les précipitations > 700 mm/an » (source :
ONF, 2020, evidence B). Conclusion : « le chêne sessile est adapté à
cette station », niveau de confiance 0,82. La chaîne d'inférence
complète (2 étapes, 2 règles, 2 sources) est transmise au Diagnostic
Engine.

### Cas 2 — Détection d'une contradiction sur la vulnérabilité au gel

Le Reasoning Engine applique deux règles sur le sapin pectiné à
altitude 1200 m : règle A « le sapin pectiné tolère les gelées jusqu'à
-20 °C » (source 2015, evidence B) et règle B « les provenances du Sud
sont vulnérables en dessous de -15 °C » (source 2028, evidence C). La
station connaît des gelées à -18 °C. Contradiction détectée : la
conclusion A indique « non vulnérable », la conclusion B indique
« vulnérable ». Les deux conclusions sont transmises au Diagnostic
Engine avec la contradiction signalée.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
