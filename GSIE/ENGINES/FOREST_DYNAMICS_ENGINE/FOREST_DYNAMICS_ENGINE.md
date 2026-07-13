# Forest Dynamics Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Forest Dynamics Engine |
| **Catégorie** | Moteur domaine (dynamique forestière) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | Non listé (moteur domaine complémentaire) |

---

## 1. Responsabilité

Modéliser la croissance et l'évolution des peuplements forestiers sur
le long terme, en intégrant les modèles de production, de régénération
et les perturbations, pour fournir des projections de dynamique
sourcées et incertaines.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Connaissances normalisées | Modèles de croissance, paramètres de production, règles de régénération |
| `CORRELATION_ENGINE` | Corrélations | Relations entre croissance et facteurs stationnels |
| `CLIMATE_ENGINE` | Variables climatiques | Données climatiques pour les modèles de croissance |
| `PEDOLOGY_ENGINE` | Caractéristiques sol | RUM, profondeur, contraintes hydriques |
| Données d'inventaire | Données utilisateur | Dendrométrie, densité, âge, structure du peuplement |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `SIMULATION_ENGINE` | Projections de dynamique | Trajectoires de croissance et d'évolution pour les scénarios |
| `RECOMMENDATION_ENGINE` | Projections de croissance | Croissance attendue par essence pour la recommandation |
| `DIAGNOSTIC_ENGINE` | État dynamique | Dynamique actuelle du peuplement (croissance, régénération) |
| `CORRELATION_ENGINE` | Données de peuplement | Données de croissance pour croisement |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `KNOWLEDGE_ENGINE` | Modèles et paramètres de croissance sourcés |
| Moteur | `CORRELATION_ENGINE` | Relations croissance/facteurs stationnels |
| Moteur | `CLIMATE_ENGINE` | Variables climatiques pour la croissance |
| Moteur | `PEDOLOGY_ENGINE` | Contraintes hydriques et pédologiques |
| Base | Données d'inventaire | Dendrométrie et structure de peuplement |

## 5. Contrat d'interface

### Entrée — `DynamicsRequest`

```
DynamicsRequest = {
  requete_id    : UUID
  peuplement_id : UUID
  etat_initial  : PeuplementState
  horizon_annees : entier (ex. 10, 30, 50)
  scenario_climat : texte (optionnel — ex. « RCP85 »)
  perturbations : liste de Perturbation (optionnel)
}

PeuplementState = {
  essence_principale : texte
  age_moyen     : décimal (années)
  densite_t_ha  : décimal
  diametre_moyen_cm : décimal
  hauteur_moyenne_m : décimal
  surface_terriere_m2_ha : décimal
  structure     : enum { reguliere, irreguliere, melange, taillis }
  source_inventaire : SourceReference
}

Perturbation = {
  type     : enum { tempete, secheresse, ravageur, incendie, coupe }
  annee    : entier
  intensite : enum { faible, modere, fort, tres_fort }
}
```

### Sortie — `DynamicsProjection`

```
DynamicsProjection = {
  projection_id : UUID
  requete_origine : UUID
  trajectoires : liste de TrajectoireCroissance
  perturbations_modelisees : liste de Perturbation (optionnel)
  source_modele : SourceReference
  date_projection : ISO 8601
}

TrajectoireCroissance = {
  essence    : texte
  points     : liste de PointTrajectoire
  modele     : texte (ex. « ONF-FFN », « INRAE-MARGINAL »)
  source     : SourceReference
  evidence_level : enum { A, B, C, D, E, F }
}

PointTrajectoire = {
  annee      : entier
  diametre_cm : décimal
  hauteur_m  : décimal
  volume_m3_ha : décimal
  accroissement_annuel_m3_ha : décimal
  incertitude : IntervalleConfiance (optionnel)
}
```

## 6. Garanties

- **Les modèles de croissance sont sourcés** — aucun coefficient n'est
  inventé ; tout provient de publications ou de référentiels identifiés
  (`GSIE-CON-002`).
- **Les projections incluent leur incertitude** — les intervalles de
  confiance sont fournis pour chaque point de trajectoire.
- Les perturbations (tempêtes, sécheresses, ravageurs) sont prises en
  compte de manière explicite et sourcée.
- Le moteur ne produit **pas de recommandation** — il fournit des
  projections (séparation des responsabilités).
- Le domaine de validité de chaque modèle est explicite (essence,
  région, conditions stationnelles).

## 7. Cas d'usage

### Cas 1 — Projection de croissance d'un peuplement de douglas

Un peuplement de douglas de 25 ans, densité 800 t/ha, diamètre moyen
18 cm. Le Forest Dynamics Engine projette sur 30 ans avec le modèle ONF
(source : ONF, 2019, evidence B) : à 55 ans, diamètre moyen 42 cm
(intervalle [38 ; 46] à 90 %), volume 480 m³/ha. Cette projection est
transmise au Simulation Engine pour comparer les scénarios d'éclaircie.

### Cas 2 — Effet d'une sécheresse sur la croissance du hêtre

Le Forest Dynamics Engine reçoit une perturbation « sécheresse 2023,
intensité forte ». Il applique un modèle de réduction de croissance
(source : INRAE, 2021, evidence C) : réduction de l'accroissement
annuel de 40 % sur 3 ans. La trajectoire projetée intègre cette
réduction avec son incertitude. Le Diagnostic Engine utilise cette
information pour évaluer le risque de dépérissement.

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de pistes pour la Phase 4
(implémentation future), des plateformes, modèles et méthodes
représentatifs de l'état de l'art en simulation de dynamique
forestière. Elle ne prescrit aucun choix d'implémentation ni de
détail technique : elle vise à documenter, de façon sourcée et
vérifiable, l'éventail des approches disponibles pour couvrir la
responsabilité du moteur — modélisation de la croissance, de la
régénération et des perturbations, avec incertitude explicite.

Quatre axes structurent cet état de l'art : (1) les plateformes de
simulation de croissance forestière existantes, qui illustrent des
architectures modulaires transposables ; (2) l'opposition entre
modèles à l'arbre individuel et modèles de peuplement, qui informe le
niveau de granularité de `PeuplementState`/`TrajectoireCroissance` ;
(3) les modèles de succession et de perturbation (tempête, sécheresse,
ravageurs), directement liés au type `Perturbation` du contrat
d'interface ; (4) les méthodes de quantification de l'incertitude, qui
répondent à la garantie « les projections incluent leur incertitude ».

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **CAPSIS** — plateforme ouverte de modélisation de la croissance forestière (INRAE et communauté scientifique associée) | Architecture de référence pour un moteur modulaire capable d'héberger plusieurs familles de modèles au sein d'un même cadre logiciel | CAPSIS a été conçu précisément pour permettre l'implémentation hétérogène de modèles de croissance, compétition, mortalité et régénération et la comparaison de scénarios sylvicoles — une organisation directement transposable à la séparation « modèles de production / régénération / perturbations » que ce moteur doit intégrer (Dufour-Kowalski et al., 2012). CAPSIS est également cité dans la section équivalente du `SIMULATION_ENGINE`, dont ce moteur est la dépendance principale (§4) : les deux moteurs devraient partager la même bibliothèque de modèles plutôt que de dupliquer l'intégration. |
| **iLand** — modèle paysager individu-centré de dynamique et de perturbation forestière (Université technique de Munich et collaborateurs) | Précédent pour le couplage explicite entre croissance à l'arbre individuel, régénération et perturbations discontinues sous scénario climatique | iLand intègre nativement les processus continus (croissance, mortalité, régénération) et discontinus (perturbations) dans un même cadre hiérarchique multi-échelle — une correspondance directe avec le champ `perturbations` de `DynamicsRequest` (Rammer et al., 2024) |
| **SILVA** — simulateur de peuplement à l'arbre individuel, dépendant de la position spatiale (TU Munich, H. Pretzsch et al.) | Piste pour approfondir la modélisation de la croissance à l'arbre individuel en peuplements mélangés et irréguliers | SILVA évalue la structure tridimensionnelle du peuplement pour déterminer la compétition inter-arbres — pertinent pour les structures `melange` et `irreguliere` déjà prévues dans `PeuplementState.structure` (Pretzsch, Biber & Ďurský, 2002) |
| **ForCEEPS / ForClim** — modèle de succession forestière de type « gap model », multi-essences, sous contrainte climatique | Piste pour le volet régénération/succession à long terme, en particulier la coexistence d'essences et la réponse au changement climatique | Ce type de modèle simule explicitement l'établissement, la croissance et la survie des essences sous contraintes abiotiques et biotiques (Morin et al., 2021) |
| **Couplage sécheresse × scolytes dans un modèle de perturbation forestier** (étude appliquée au modèle iLand sur un paysage d'Europe centrale) | Précédent scientifique pour le sous-module de perturbations biotiques (`type: ravageur`) | Cette étude formalise la sécheresse comme facteur déclencheur de pullulations de scolytes — un exemple directement transposable au type `Perturbation { type: ravageur }` du contrat d'interface (Das et al., 2025) |
| **Cadre bayésien de quantification d'incertitude pour les projections de croissance et de production** (démonstration sur douglas en plantation, Pacifique Nord-Ouest des États-Unis) | Piste méthodologique pour construire l'`IntervalleConfiance` associé à chaque `PointTrajectoire` | Le cadre bayésien génère une distribution prédictive des états futurs du peuplement à partir de l'incertitude sur les paramètres (Wilson, Monleon & Weiskittel, 2019) |

Ces pistes restent, à ce stade, des orientations de recherche pour la
Phase 4 : aucune n'est retenue comme choix d'implémentation, aucun
algorithme n'est prescrit, et le moteur devra dans tous les cas
documenter précisément le domaine de validité et le niveau de preuve
(`evidence_level`) de tout modèle finalement intégré.

### Sources

- Dufour-Kowalski, S., Courbaud, B., Dreyfus, P., Meredieu, C., de Coligny, F. (2012). *Capsis: an open software framework and community for forest growth modelling.* Annals of Forest Science, 69(2), 221–233. https://doi.org/10.1007/s13595-011-0140-9
- Rammer, W. et al. (2024). *The individual-based forest landscape and disturbance model iLand: Overview, progress, and outlook.* Ecological Modelling, 495, 110785. https://doi.org/10.1016/j.ecolmodel.2024.110785 — https://iland-model.org/
- Pretzsch, H., Biber, P., Ďurský, J. (2002). *The single tree-based stand simulator SILVA.* Forest Ecology and Management, 162(1), 3–21. https://doi.org/10.1016/S0378-1127(02)00047-6
- Morin, X. et al. (2021). *Beyond forest succession: a gap model to study ecosystem functioning and tree community composition under climate change.* Functional Ecology. https://doi.org/10.1111/1365-2435.13760
- Das, A. K., Baldo, M., Dobor, L. et al. (2025). *The increasing role of drought as an inciting factor of bark beetle outbreaks can cause large-scale transformation of Central European forests.* Landscape Ecology, 40. https://doi.org/10.1007/s10980-025-02125-w
- Wilson, D., Monleon, V., Weiskittel, A. (2019). *Quantification and Incorporation of Uncertainty in Forest Growth and Yield Projections Using A Bayesian Probabilistic Framework.* Mathematical and Computational Forestry & Natural-Resource Sciences, 11(2), 264–285. https://mcfns.com/index.php/Journal/article/view/11.3

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
