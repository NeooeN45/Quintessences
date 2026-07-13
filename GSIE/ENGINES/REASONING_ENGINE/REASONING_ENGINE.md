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

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de pistes pour la Phase 4
(implémentation), des technologies et méthodes actuelles pertinentes
pour la responsabilité exacte du Reasoning Engine : appliquer des
règles d'inférence **explicites et auditées** sur des connaissances et
corrélations qualifiées, sans jamais inventer de règle, en produisant
des conclusions expliquées et traçables. Aucune de ces pistes ne
constitue un choix d'implémentation arrêté — un tel choix relèvera
d'une décision tracée (`03_DECISIONS/`) au moment de la Phase 4.

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **Drools** (moteur de règles métier, KIE Community / Apache Incubator depuis janvier 2023, algorithme Rete, chaînage avant et arrière) | Exécution des règles d'inférence déclarées (`EtapeInference`) avec traçabilité native de la chaîne de déclenchement | Drools sépare strictement les règles (déclarées, versionnables) du moteur d'exécution, ce qui correspond directement à la garantie « le moteur n'invente aucune règle » : chaque `regle_appliquee` peut être retracée jusqu'à sa définition source. La version 10.x (10.0.0, décembre 2024 ; 10.1.0, juillet 2025) confirme un développement actif. |
| **CLIPS** (C Language Integrated Production System, développé par la Software Technology Branch du NASA Johnson Space Center) | Alternative légère de système de production à chaînage avant, pour un moteur embarqué et fonctionnant hors-ligne | CLIPS est considéré comme le standard de facto des systèmes experts à base de règles en chaînage avant dans le domaine public ; sa simplicité et sa faible empreinte en font un candidat cohérent avec la garantie de fonctionnement hors-ligne complet (article T-8). |
| **Réseaux bayésiens / modèles graphiques probabilistes** (ex. bibliothèque `pgmpy`, Ankan & Panda) | Calcul et propagation du `niveau_confiance` (0,0–1,0) attaché à chaque `Conclusion`, en complément — jamais en remplacement — de la chaîne d'inférence | Les réseaux bayésiens formalisent l'incertitude sur des relations autécologiques et sont déjà utilisés pour actualiser des modèles de distribution d'espèces et d'adéquation d'habitat en écologie. Ils offrent un cadre pour quantifier une confiance sans dispenser de la justification par règle exigée par `GSIE-CON-002`. |
| **Approches neuro-symboliques hybrides** (Probabilistic Soft Logic / NeuPSL, réseaux logiques de Markov) | Pondération probabiliste de règles symboliques lorsqu'elles doivent intégrer des corrélations statistiques qualifiées issues du `CORRELATION_ENGINE` | Ces approches combinent logique formelle (premier ordre) et poids probabilistes appris, ce qui permettrait d'articuler règles auditées et corrélations statistiques sans perdre l'auditabilité symbolique. Une revue systématique récente note toutefois que l'explicabilité reste le point le moins mature de ces architectures (28 % des travaux recensés) — un signal de prudence pour toute adoption. |
| **Answer Set Programming** (ex. solveur `clingo`, extension explicative `xclingo`) | Raisonnement non-monotone et détection formelle de règles contradictoires | L'ASP gère nativement le raisonnement par défaut et l'identification de conflits entre règles concurrentes, ce qui correspond directement à la structure `ContradictionDetectee` du contrat de sortie. L'outil `xclingo` génère des arbres de dérivation textuels, un mécanisme directement transposable à l'exigence de chaîne d'inférence documentée. |
| **Précédent opérationnel — NED-2** (décision assistée par ordinateur pour la gestion des écosystèmes forestiers, USDA Forest Service, architecture tableau noir / agents en Prolog) | Référence de conception pour l'articulation de règles à travers plusieurs échelles (arbre → peuplement → paysage) | NED-2 démontre, à l'échelle opérationnelle nord-américaine, la faisabilité d'un moteur de règles logiques (Prolog) couplé à des modèles de croissance et des données SIG pour produire des prescriptions sylvicoles justifiées — un précédent directement transposable au raisonnement multi-échelle (spatial et temporel) requis par ce moteur. |

Ces six pistes ne s'excluent pas mutuellement : un moteur de règles de
type production (Drools ou CLIPS) reste le candidat le plus direct
pour satisfaire la garantie « aucune règle inventée » et la structure
`EtapeInference`, tandis que les réseaux bayésiens ou les approches
neuro-symboliques n'interviendraient qu'en complément, pour qualifier
le `niveau_confiance` sans se substituer à la règle auditée elle-même.
L'Answer Set Programming apparaît en outre comme une piste
spécifiquement adaptée à la détection de contradictions déjà prévue
dans le contrat de sortie. Le raisonnement multi-échelle (spatial et
temporel), quatrième axe demandé, ne dispose pas d'un outil unique
dédié dans l'état de l'art actuel : il s'agit davantage d'un principe
d'architecture (hiérarchisation des règles par échelle, à l'image de
NED-2) que d'une bibliothèque à adopter telle quelle. Le choix final
entre ces pistes, ainsi que toute combinaison retenue, devra faire
l'objet d'une décision tracée avant le début de l'implémentation en
Phase 4.

À noter : NED-2 et **EMDS** (cité dans la même section du
`RECOMMENDATION_ENGINE`) proviennent tous deux de l'écosystème
USDA Forest Service et occupent des positions adjacentes dans la
chaîne Reasoning → Recommendation ; une évaluation conjointe des deux
précédents en Phase 4 est plus pertinente qu'une évaluation isolée.

### Sources

- Drools — KIE Community / Apache Software Foundation. https://docs.drools.org/latest/drools-docs/drools/rule-engine/index.html ; https://en.wikipedia.org/wiki/Drools
- CLIPS — Software Technology Branch, NASA Johnson Space Center. https://en.wikipedia.org/wiki/CLIPS ; rapport technique originel, NASA Technical Reports Server, 1991 : https://ntrs.nasa.gov/citations/19910014730
- pgmpy — Ankan A., Panda A. et contributeurs, *pgmpy: Probabilistic Graphical Models using Python*. https://github.com/pgmpy/pgmpy et https://pgmpy.org
- « Bayesian networks facilitate updating of species distribution and habitat suitability models », ScienceDirect, 2024. https://www.sciencedirect.com/science/article/abs/pii/S0304380024003703
- « Neuro-Symbolic AI in 2024: A Systematic Review », arXiv:2501.05435. https://arxiv.org/html/2501.05435v1
- « NeuPSL: Neural Probabilistic Soft Logic », arXiv:2205.14268. https://arxiv.org/pdf/2205.14268
- Cabalar P. et al., « A System for Explainable Answer Set Programming » (xclingo). https://www.dc.fi.udc.es/~cabalar/xclingo.pdf
- Twery M.J. et al., « NED-2: A decision support system for integrated forest ecosystem management », Computers and Electronics in Agriculture. https://www.sciencedirect.com/science/article/abs/pii/S0168169905000487 (version accessible : USDA Forest Service Treesearch, https://research.fs.usda.gov/download/treesearch/15882.pdf)

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
