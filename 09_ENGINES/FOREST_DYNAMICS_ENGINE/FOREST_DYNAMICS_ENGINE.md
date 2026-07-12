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

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
