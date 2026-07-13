# Correlation Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Correlation Engine |
| **Catégorie** | Chaîne d'intelligence (détection de relations) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | 5 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Détecter et quantifier les corrélations statistiques significatives
entre données issues de sources hétérogènes (géospatiales, climatiques,
pédologiques, botaniques, terrain) pour alimenter le raisonnement.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Connaissances normalisées | Règles, seuils et relations connues servant de référence |
| `GIS_ENGINE` | Données géospatiales | MNT, pente, exposition, hydrographie, limites parcellaires |
| `CLIMATE_ENGINE` | Données climatiques | Températures, précipitations, déficit hydrique, bioclimat |
| `PEDOLOGY_ENGINE` | Données pédologiques | Texture, pH, profondeur, drainage, réserve utile |
| `BOTANICAL_ENGINE` | Données botaniques | Présence/absence d'essences, autécologie |
| `FOREST_DYNAMICS_ENGINE` | Données de peuplement | Croissance, régénération, perturbations |
| Observations terrain | Données utilisateur | Relevés, inventaires, diagnostics terrain |
| `GSIE/DATASETS/` | Jeux de données | Séries temporelles et spatiales référencées |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `REASONING_ENGINE` | Matrice de corrélations | Relations statistiques justifiées et sourcées |
| `DIAGNOSTIC_ENGINE` | Matrice de corrélations | Relations utiles au diagnostic stationnel |
| `FOREST_DYNAMICS_ENGINE` | Corrélations | Relations alimentant les modèles de dynamique |
| `LEARNING_ENGINE` | Patterns émergents | Corrélations nouvelles détectées, à valider |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `KNOWLEDGE_ENGINE` | Référentiel de règles et relations connues |
| Moteur | `GIS_ENGINE` | Données géospatiales |
| Moteur | `CLIMATE_ENGINE` | Données climatiques |
| Moteur | `PEDOLOGY_ENGINE` | Données pédologiques |
| Moteur | `BOTANICAL_ENGINE` | Données botaniques |
| Moteur | `FOREST_DYNAMICS_ENGINE` | Données de peuplement |
| Base | `GSIE/DATASETS/` | Jeux de données référencés |

## 5. Contrat d'interface

### Entrée — `CorrelationRequest`

```
CorrelationRequest = {
  requete_id    : UUID
  domaine       : enum { stationnel, climatique, sylvicole, sanitaire, global }
  parametres    : liste de ParametreCorrelation
  zone_etude    : EmpriseGeographique (optionnel)
  periode       : PeriodeTemporelle (optionnel)
  seuil_significativite : décimal (optionnel, défaut 0,05)
}

ParametreCorrelation = {
  source_moteur : enum { GIS, CLIMATE, PEDOLOGY, BOTANICAL, FOREST_DYNAMICS, TERRAIN }
  variable      : texte (ex. « pH », « precipitations_estivales », « altitude » )
  unite         : texte
}

EmpriseGeographique = {
  type     : enum { point, polygone, parcelle }
  geometrie : structure GeoJSON (optionnel)
  parcelle_id : texte (optionnel)
}
```

### Sortie — `CorrelationMatrix`

```
CorrelationMatrix = {
  matrice_id    : UUID
  requete_origine : UUID
  correlations  : liste de Correlation
  date_calcul   : ISO 8601
  sources_utilisees : liste de SourceReference
}

Correlation = {
  variable_a    : ParametreCorrelation
  variable_b    : ParametreCorrelation
  coefficient   : décimal (-1,0 à 1,0)
  p_valeur      : décimal
  type_relation : enum { positive, negative, non_significative }
  n_observations: entier
  domaine_validite : texte (ex. « France méditerranéenne, sols acides »)
  source        : SourceReference
  evidence_level: enum { A, B, C, D, E, F }
  confidence    : décimal (0,0 à 1,0)
}
```

## 6. Garanties

- Toute corrélation produite est **sourcée** et **statistiquement
  justifiée** (coefficient, p-valeur, taille d'échantillon) (`GSIE-CON-002`).
- Aucune corrélation n'est présentée comme relation de causalité sans
  justification scientifique explicite.
- Le domaine de validité de chaque corrélation est explicité (zone,
  période, conditions).
- Le moteur ne produit **pas de recommandation** — il alimente le
  raisonnement (séparation des responsabilités).
- Les corrélations non significatives sont conservées dans la matrice
  pour éviter les inférences abusives.
- Fonctionnement hors-ligne sur données en cache local (article T-8).

## 7. Cas d'usage

### Cas 1 — Corrélation entre déficit hydrique estival et dépérissement du hêtre

Le Correlation Engine croise les données climatiques du Climate Engine
(déficit hydrique estival 2003–2023) avec les observations de
dépérissement du hêtre issues du terrain. Il détecte une corrélation
négative significative (r = -0,72, p < 0,01) entre les précipitations
estivales et la vitalité du hêtre en dessous de 800 m. Cette corrélation
est transmise au Reasoning Engine et au Diagnostic Engine avec son
domaine de validité (« France atlantique, altitude < 800 m, période
2003–2023 »).

### Cas 2 — Corrélation entre pH sol et présence du chêne sessile

Croisement des données pédologiques (pH mesuré sur 150 stations) et des
relevés botaniques (présence/absence du chêne sessile). Corrélation
positive significative (r = 0,58, p < 0,05) entre pH 4,5–6,0 et la
présence de l'essence. La corrélation est sourcée (observations terrain
+ référentiel Rameau et al., 2018) et transmise au Reasoning Engine.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
