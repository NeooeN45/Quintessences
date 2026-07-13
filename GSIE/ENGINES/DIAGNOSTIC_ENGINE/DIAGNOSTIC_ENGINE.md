# Diagnostic Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Diagnostic Engine |
| **Catégorie** | Chaîne d'intelligence (analyse stationnelle) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-001, GSIE-CON-004 |
| **Ordre de développement** | 11 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Synthétiser les conclusions du Reasoning Engine et les données
multi-domaines en un diagnostic cohérent de l'état d'une station ou
d'un peuplement, identifiant les contraintes, atouts et risques — sans
prescrire d'action.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `REASONING_ENGINE` | Conclusions inférées | Déductions logiques avec chaîne d'inférence |
| `GIS_ENGINE` | Données géospatiales | Pente, exposition, altitude, hydrographie |
| `CLIMATE_ENGINE` | Données climatiques | Variables bioclimatiques, projections |
| `PEDOLOGY_ENGINE` | Données pédologiques | Caractéristiques et classifications du sol |
| `BOTANICAL_ENGINE` | Données botaniques | Végétation présente, autécologie |
| `FOREST_DYNAMICS_ENGINE` | Données de peuplement | Croissance, régénération, perturbations |
| `KNOWLEDGE_ENGINE` | Référentiels | Référentiels stationnels et sylvicoles |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `RECOMMENDATION_ENGINE` | Diagnostic | État de la station, contraintes, atouts, risques, confiance |
| `VALIDATION_ENGINE` | Diagnostic | Pour contrôle de cohérence avant présentation |
| `SIMULATION_ENGINE` | Diagnostic | État initial pour les projections de scénarios |
| Utilisateur (via interface) | Rapport de diagnostic | Présentation de l'analyse au forestier |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `REASONING_ENGINE` | Conclusions inférées (obligatoire) |
| Moteur | `GIS_ENGINE` | Données géospatiales stationnelles |
| Moteur | `CLIMATE_ENGINE` | Données bioclimatiques |
| Moteur | `PEDOLOGY_ENGINE` | Données pédologiques |
| Moteur | `BOTANICAL_ENGINE` | Données botaniques |
| Moteur | `FOREST_DYNAMICS_ENGINE` | Données de peuplement |
| Moteur | `KNOWLEDGE_ENGINE` | Référentiels stationnels |

## 5. Contrat d'interface

### Entrée — `DiagnosticRequest`

```
DiagnosticRequest = {
  requete_id  : UUID
  station_id  : UUID
  peuplement_id : UUID (optionnel)
  conclusions : liste de Conclusion (issues du Reasoning Engine)
  contexte    : StationContexte (voir REASONING_ENGINE.md §5)
  type_diagnostic : enum { stationnel, sylvicole, sanitaire, global }
}
```

### Sortie — `Diagnostic`

```
Diagnostic = {
  diagnostic_id   : UUID
  requete_origine : UUID
  station_id      : UUID
  type_diagnostic : enum { stationnel, sylvicole, sanitaire, global }
  etat_global     : enum { sain, vigueur_reduite, depérissement, critique }
  contraintes     : liste de ElementDiagnostic
  atouts          : liste de ElementDiagnostic
  risques         : liste de RisqueDiagnostic
  confiance       : décimal (0,0 à 1,0)
  incertitudes    : liste de texte
  conclusions_source : liste de UUID (Conclusion du Reasoning Engine)
  date_diagnostic : ISO 8601
}

ElementDiagnostic = {
  description    : texte (ex. « sol acide, pH 5,2 »)
  domaine        : enum { pedologique, climatique, topographique, botanique, sylvicole }
  evidence_level : enum { A, B, C, D, E, F }
  source         : SourceReference
}

RisqueDiagnostic = {
  description    : texte (ex. « risque de dépérissement lié au déficit hydrique »)
  probabilite    : enum { faible, modere, eleve, tres_eleve }
  horizon        : texte (ex. « 5 ans », « 20 ans »)
  domaine        : enum { climatique, sanitaire, sylvicole }
  evidence_level : enum { A, B, C, D, E, F }
  source         : SourceReference
}
```

## 6. Garanties

- **Un diagnostic est une analyse, pas une décision** — il décrit l'état
  et les risques, il ne prescrit pas l'action (principe fondateur).
- Toute contrainte, atout ou risque est sourcé avec son niveau de
  preuve (`GSIE-CON-002`, `GSIE-CON-005`).
- La confiance et les incertitudes du diagnostic sont explicitement
  documentées (`GSIE-CON-004`).
- Le forestier reste le décideur — le diagnostic est contournable
  (`GSIE-CON-001`).
- Les contradictions entre domaines (ex. sol favorable mais climat
  défavorable) sont mises en évidence, jamais masquées.
- Fonctionnement hors-ligne complet (article T-8).

## 7. Cas d'usage

### Cas 1 — Diagnostic de dépérissement d'une hêtraie de plaine

Une hêtraie à 250 m d'altitude présente 30 % de mortalité. Le
Diagnostic Engine synthétise : contrainte climatique (déficit hydrique
estival croissant, evidence B), contrainte stationnelle (sol superficiel,
RUM faible, evidence B), atout (pH favorable 6,2, evidence B). État
global : « dépérissement ». Risque : « aggravation du dépérissement à
horizon 10 ans, probabilité élevée ». Confiance : 0,75. Le diagnostic
est transmis au Recommendation Engine sans prescrire d'action.

### Cas 2 — Diagnostic de station pour choix d'essence après coupe rase

Après une coupe rase sur une station à pente 15 %, altitude 400 m, sol
limoneux profond, pH 5,8, précipitations 900 mm. Le Diagnostic Engine
produit : atouts (sol profond, RUM élevée, pH modérément acide),
contraintes (pente, exposition nord), risques (érosion post-coupe,
probabilité modérée). État global : « sain ». Le diagnostic est transmis
au Recommendation Engine qui proposera des essences adaptées.

## 8. État de l'art et pistes de recherche sourcées

> Piste de recherche pour la Phase 4 (implémentation future). Ce qui
> suit ne prescrit aucun choix technique définitif ni détail
> d'implémentation — il documente des technologies, algorithmes et
> précédents scientifiques vérifiables, pertinents pour la
> responsabilité exacte du Diagnostic Engine : synthétiser des
> conclusions et des données multi-domaines en un diagnostic
> stationnel cohérent (contraintes, atouts, risques), sans prescrire
> d'action.

### 8.1 Panorama

Le Diagnostic Engine se situe au croisement de deux traditions de
recherche bien documentées : (1) les **systèmes experts de diagnostic
sylvicole**, qui formalisent depuis les années 1980 la synthèse de
symptômes et de facteurs stationnels en un état de santé explicable
et contournable par le forestier ; et (2) la **télédétection de la
santé forestière**, qui fournit aujourd'hui des indicateurs
quantitatifs, sourcés et répétables (indices spectraux, imagerie
hyperspectrale) pouvant alimenter les `ElementDiagnostic` et
`RisqueDiagnostic` du contrat d'interface. La classification
supervisée (forêts aléatoires, gradient boosting) constitue le pont
technique entre ces deux traditions : elle permet de synthétiser des
variables multi-domaines (GIS, climat, pédologie, botanique) en une
classe d'état sanitaire, avec une traçabilité de l'importance de
chaque variable — donc compatible avec l'exigence de sourçage
(`GSIE-CON-002`, `GSIE-CON-005`) et de diagnostic non prescriptif
(garanties §6).

### 8.2 Technologies, algorithmes et précédents pertinents

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| Indices spectraux dérivés de Sentinel-2 (NDVI, NDMI, indices de la bande *red-edge*), calibrés sur le réseau de placettes **ICP Forests** | Alimenter des `ElementDiagnostic` de domaine botanique/climatique (indicateurs de vigueur, de stress hydrique) avec un niveau de preuve explicite | Le réseau ICP Forests (actif depuis 1985, ~6 000 placettes en Europe) fournit un référentiel de calibration validé pour ces indices ; une étude récente démontre l'usage opérationnel de NDVI standardisé (Z NDVI) pour classer la sévérité des dommages sur des placettes ICP Forests, avec accord entre observations de terrain et imagerie satellite (Molnár et al., 2025) |
| Imagerie hyperspectrale aéroportée ou par drone (UAV) | Détecter des signaux de stress phytosanitaire pré-symptomatiques, avant l'expression visible de dépérissement, pour nourrir des `RisqueDiagnostic` de domaine sanitaire à horizon court | La revue de Marvasti-Zadeh et al. (2024) montre que les approches hyperspectrales et l'apprentissage profond permettent de détecter des signatures spectrales de stress avant l'apparition de symptômes visibles, tout en soulignant des incertitudes encore élevées à corriger — ce qui justifie une évaluation prudente en Phase 4 plutôt qu'un déploiement immédiat |
| Classification supervisée par forêts aléatoires (*Random Forest*, Breiman, 2001) | Synthétiser les variables multi-domaines (topographie, climat, sol, végétation) en une classe `etat_global` (sain / vigueur réduite / dépérissement / critique), avec une hiérarchie d'importance des variables traçable | Méthode robuste au bruit et aux données de haute dimension, largement établie en cartographie et diagnostic par télédétection forestière ; l'importance des variables produite par l'algorithme peut servir de justification explicite à chaque `ElementDiagnostic` |
| Gradient boosting (ex. XGBoost, Chen & Guestrin, 2016) | Alternative ou complément au Random Forest pour l'estimation de la probabilité des `RisqueDiagnostic` (ex. probabilité de dépérissement à horizon donné) | Performances généralement supérieures au Random Forest sur données tabulaires multi-domaines dans des comparaisons publiées en foresterie ; reste interprétable (importance de variables, contributions marginales) |
| Systèmes d'évaluation de prédisposition multi-facteurs (*Predisposition Assessment Systems*, PAS) | Précédent méthodologique direct pour la fusion de facteurs stationnels hétérogènes (sol, climat, peuplement) en une évaluation de risque, sans recommandation d'action | Netherer & Nopp-Mayr (2005) documentent un système opérationnel de notation du risque d'attaque de scolytes intégrant des facteurs de site et de peuplement dans les Hautes Tatras — un précédent vérifié et transposable au principe « diagnostic sans prescription » du moteur |
| Systèmes experts à base de règles d'inférence (ex. PREDICT, pour le diagnostic phytosanitaire du pin rouge) | Précédent pour structurer un diagnostic explicable, combinant une base de règles et des faits observés | Schmoldt & Martin (1986) décrivent un système à ~400 règles d'inférence permettant à un forestier de diagnostiquer une cause probable de symptômes ; illustre la faisabilité, dès les années 1980, d'un diagnostic transparent et contournable par l'utilisateur (`GSIE-CON-001`) |

### 8.3 Points de vigilance pour la Phase 4

- Les indices spectraux et l'imagerie hyperspectrale fournissent des
  **indicateurs**, pas des diagnostics : leur intégration devra rester
  cohérente avec la garantie « diagnostic ≠ décision » (§6) et
  transiter par une estimation de `evidence_level` explicite.
- Les méthodes de classification supervisée (Random Forest, gradient
  boosting) nécessitent des jeux d'entraînement labellisés
  représentatifs des stations françaises/européennes ; leur usage en
  Phase 4 devra être documenté dans `GSIE/DATASETS/` avec la
  provenance et les biais connus des données d'entraînement.
- Les précédents de type PAS et systèmes experts à règles montrent
  qu'une architecture de diagnostic explicable est atteignable sans
  recourir à des modèles boîte noire — un critère à mettre en balance
  avec la performance des méthodes d'apprentissage automatique lors du
  choix d'implémentation en Phase 4.
- Le `CORRELATION_ENGINE` propose également les forêts aléatoires,
  mais pour un rôle distinct (fusion exploratoire multi-sources,
  plutôt que classification supervisée de l'état sanitaire) ; les deux
  usages sont complémentaires et ne doivent pas conduire à deux
  implémentations redondantes en Phase 4.

### Sources

- Molnár, T., Bolla, B., Szabó, O., & Koltay, A. (2025). « Sentinel-2-Based Forest Health Survey of ICP Forests Level I and II Plots in Hungary ». Journal of Imaging, 11(11), 413. https://www.mdpi.com/2313-433X/11/11/413
- Marvasti-Zadeh, S. M., Goodsman, D., Ray, N., & Erbilgin, N. (2024). « Early Detection of Bark Beetle Attack Using Remote Sensing and Machine Learning: A Review ». ACM Computing Surveys, 56(4), article 97 (preprint : https://arxiv.org/abs/2210.03829)
- Netherer, S., & Nopp-Mayr, U. (2005). « Predisposition assessment systems (PAS) as supportive tools in forest management ». Forest Ecology and Management, 207(1-2), 99-107. https://www.sciencedirect.com/science/article/abs/pii/S0378112704007303
- Schmoldt, D. L., & Martin, G. L. (1986). « Expert systems in forestry: Utilizing information and expertise for decision making ». Computers and Electronics in Agriculture, 1, 233-250. https://www.sciencedirect.com/science/article/abs/pii/0168169986900116
- Breiman, L. (2001). « Random Forests ». Machine Learning, 45, 5-32. https://link.springer.com/article/10.1023/A:1010933404324
- Chen, T., & Guestrin, C. (2016). « XGBoost: A Scalable Tree Boosting System ». Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (preprint : https://arxiv.org/abs/1603.02754)
- ICP Forests — International Co-operative Programme on Assessment and Monitoring of Air Pollution Effects on Forests, UNECE. https://www.icp-forests.net/

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
