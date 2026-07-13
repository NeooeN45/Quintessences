# Pedology Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Pedology Engine |
| **Catégorie** | Moteur domaine (pédologie) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | 8 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer les données de sol, classer les sols selon les référentiels
pédologiques officiels et fournir les caractéristiques stationnelles
pédologiques (texture, pH, profondeur, drainage, réserve utile en eau)
sans jamais inventer de seuil.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Scientific Database | Base de données | Données pédologiques stockées |
| Station Repository | Base de données | Données de station (relevés, profils) |
| Base de Données des Sols | Source externe | BD sols nationale, équivalents régionaux |
| Référentiel Pédologique Français | Référentiel | RPF (INRAE) — classifications et seuils |
| WRB | Référentiel | World Reference Base (FAO) — classification internationale |
| Observations terrain | Données utilisateur | Profils de sol, mesures pH, textures relevées |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Caractéristiques pédologiques | Texture, pH, profondeur, drainage, RUM, classification |
| `CORRELATION_ENGINE` | Données pédologiques | Données pour croisement statistique |
| `REASONING_ENGINE` | Caractéristiques pédologiques | Données pour l'inférence d'adaptation |
| `FOREST_DYNAMICS_ENGINE` | Caractéristiques sol | RUM et contraintes pour les modèles de croissance |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Scientific Database, Station Repository | Stockage des données pédologiques |
| Référentiel | Référentiel Pédologique Français (INRAE) | Classifications et seuils officiels |
| Référentiel | WRB (FAO) | Classification internationale |
| Aucun moteur | — | Le Pedology Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `PedologyQuery`

```
PedologyQuery = {
  requete_id : UUID
  station_id : UUID (optionnel)
  emprise    : EmpriseGeographique (optionnel)
  parametres : liste de enum {
    ph, texture, profondeur, drainage, reserve_utile_eau,
    matiere_organique, cailloux, compaction, classification
  }
  referentiel_classification : enum { RPF, WRB } (optionnel)
}
```

### Sortie — `PedologyData`

```
PedologyData = {
  requete_id : UUID
  station_id : UUID (optionnel)
  profil     : ProfilSol (optionnel)
  caracteristiques : liste de SolCaracteristique
  classification : ClassificationSol (optionnel)
  source     : SourceReference
  date_donnees : ISO 8601
}

ProfilSol = {
  horizons   : liste de HorizonSol
  profondeur_totale_cm : décimal
}

HorizonSol = {
  profondeur_min_cm : décimal
  profondeur_max_cm : décimal
  texture     : enum { sableux, sable_limoneux, limoneux, limono_argileux, argileux }
  ph          : décimal
  matiere_organique_pct : décimal (optionnel)
  cailloux_pct : décimal (optionnel)
}

SolCaracteristique = {
  nom         : texte (ex. « reserve_utile_eau »)
  valeur      : décimal
  unite       : texte (ex. « mm », « pH », « % »)
  source      : SourceReference
  evidence_level : enum { A, B, C, D, E, F }
}

ClassificationSol = {
  referentiel : enum { RPF, WRB }
  type_sol    : texte (ex. « Alocrisol », « Luvisol »)
  source      : SourceReference
}
```

## 6. Garanties

- **Toute classification pédologique est sourcée** — aucune
  classification n'est produite sans référence au référentiel cité
  (principe fondateur).
- **Aucun seuil (pH, texture, drainage) n'est inventé** — tout provient
  du référentiel cité (`GSIE-CON-002`).
- Les conflits entre référentiels (RPF vs WRB) sont signalés, jamais
  résolus arbitrairement.
- Le moteur ne produit **pas de diagnostic** — il fournit des données et
  des classifications (séparation des responsabilités).
- Fonctionnement hors-ligne sur données en cache local (article T-8).

## 7. Cas d'usage

### Cas 1 — Classification d'un sol pour choix d'essence

Une station présente un pH 5,2, texture limono-sableuse, profondeur
80 cm, drainage modéré. Le Pedology Engine classe le sol comme
« Alocrisol » (RPF, source : INRAE 2008) / « Acrisol » (WRB, source :
FAO 2014). RUM calculée : 120 mm (source : RPF, formule de calcul de
réserve utile). Ces données sont transmises au Diagnostic Engine pour
évaluer l'adaptation du chêne sessile et du hêtre.

### Cas 2 — Détection d'une contrainte hydrique par RUM faible

Le Pedology Engine fournit une RUM de 60 mm pour une station à sol
superficiel (profondeur 30 cm) sur pente forte. Cette valeur, sourcée
(RPF, INRAE 2008), est transmise au Diagnostic Engine qui l'intègre
comme contrainte pédologique majeure pour le hêtre (RUM minimale
requise : 80 mm selon Rameau et al., 2018).

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de pistes pour la Phase 4 (implémentation),
des outils, méthodes et bases de données existants et vérifiables,
pertinents pour la responsabilité du Pedology Engine (gestion des
données de sol, classification pédologique référencée, caractéristiques
stationnelles sourcées). Aucun de ces éléments ne constitue une
décision d'architecture : ils sont proposés comme points de départ
pour une évaluation ultérieure, dans le respect de `GSIE-CON-002`
(la science avant tout) et `GSIE-CON-005` (traçabilité de la
connaissance).

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **SoilGrids 2.0** (ISRIC) | Source de complément et de contrôle de cohérence pour les caractéristiques pédologiques (texture, pH, carbone organique, densité apparente) hors couverture ou en complément du RRP | Système mondial de cartographie numérique des sols par apprentissage automatique, résolution 250 m, incertitude spatiale quantifiée pour chaque prédiction — directement compatible avec l'exigence de `evidence_level` du contrat `SolCaracteristique` (Poggio et al., 2021) |
| **RRP / DoneSol** (Gis Sol — INRAE) | Référentiel national déjà cité dans les entrées du moteur ; piste : formaliser un connecteur d'ingestion entre les Unités Typologiques de Sol (UTS) du RRP/DoneSol et le contrat `ProfilSol`/`HorizonSol` | Système d'information officiel sur les sols de France, cartographie régionale, structuré en UTS directement mobilisables pour horizons, texture, pH (Gis Sol / INRAE) |
| **Fonctions de pédotransfert françaises pour la réserve utile en eau** (Al Majou, Bruand, Duval, Le Bas & Vautier, 2008 ; Al Majou, Bruand, Duval & Cousin, 2007) | Piste pour **estimer** la RUM (`reserve_utile_eau`) à partir de la texture, de la densité apparente et du type d'horizon quand la mesure directe est absente | Fonctions calibrées et validées sur bases de données pédologiques françaises, comparées aux fonctions internationales de référence (dont le modèle neuronal hiérarchique **ROSETTA**, Schaap et al.) ; la littérature signale des écarts de performance significatifs hors du domaine de calibration, ce qui impose de documenter le domaine de validité de toute fonction retenue |
| **World Reference Base for Soil Resources — 4e édition** (IUSS Working Group WRB, 2022) | Mise à jour du référentiel `WRB` déjà cité dans le contrat d'interface (`referentiel_classification`) | Édition actuellement valide de la classification internationale de référence, publiée par l'IUSS lors du Congrès mondial de science du sol de Glasgow (août 2022) |
| **FOR-EVAL / FOR-EVAL Diagnostics** (INRAE UMR ISPA — ONF) | Précédent opérationnel français directement comparable à la responsabilité du moteur : outil de terrain qui calcule la réserve utile en eau et évalue la sensibilité des sols forestiers à partir de texture, profondeur et éléments grossiers | Application mobile déjà déployée en gestion forestière française, sans analyse de laboratoire, conçue conjointement par un institut de recherche public (INRAE) et le gestionnaire forestier public (ONF) |
| **Catalogues des stations forestières** (Centre National de la Propriété Forestière — CNPF, méthode phytoécologique de la *Flore forestière française*) | Piste pour une base croisée sol-végétation en entrée du moteur ou en interface avec `FOREST_DYNAMICS_ENGINE` | Démarche de référence en foresterie française depuis 1976 (plus de 140 catalogues régionaux), fondée sur les écogrammes de la *Flore forestière française* ; croise systématiquement conditions pédologiques et cortèges floristiques indicateurs — un lien direct à formaliser avec le `BOTANICAL_ENGINE`, qui mobilise les mêmes travaux de Rameau et al. |

### Points de vigilance scientifique

- Les fonctions de pédotransfert **estiment** des propriétés, elles ne
  les **mesurent** pas : toute valeur qui en serait issue devrait être
  marquée avec un `evidence_level` inférieur à celui d'une mesure de
  terrain ou de laboratoire. La synthèse de Weber et al. (2024,
  *Hydrology and Earth System Sciences*) souligne que la majorité des
  fonctions de pédotransfert hydro-pédologiques ont été calibrées sur
  des sols agricoles tempérés à l'échelle du laboratoire, ce qui limite
  leur transférabilité directe à d'autres contextes sans validation
  locale.
- La coexistence de plusieurs référentiels de classification (RPF,
  WRB, catalogues régionaux de stations) confirme la garantie déjà
  documentée : les conflits entre référentiels doivent être signalés
  et non résolus arbitrairement par le moteur.
- Toute intégration de ces pistes en Phase 4 devrait faire l'objet
  d'une spécification dédiée (`05_SPECIFICATIONS/`) précisant la
  source exacte, la version du référentiel et le domaine de validité
  retenu, avant toute implémentation.

### Sources

- Poggio, L., de Sousa, L. M., Batjes, N. H. et al. (2021). *SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty*. SOIL, 7(1), 217–240. https://soil.copernicus.org/articles/7/217/2021/
- ISRIC — World Soil Information. *SoilGrids*. https://www.isric.org/explore/soilgrids
- Gis Sol (INRAE). *Référentiel Régional Pédologique (RRP)* et base *DoneSol*. https://www.gissol.fr/le-programme/bases-de-donnees/donesol-146 et https://www.gissol.fr/publications/fiche-referentiel-regional-pedologique-rrp-2192
- Al Majou, H., Bruand, A., Duval, O., Le Bas, C., Vautier, A. (2008). *Prediction of soil water retention properties after stratification by combining texture, bulk density and the type of horizon*. Soil Use and Management, 24, 383–391.
- Al Majou, H., Bruand, A., Duval, O., Cousin, I. (2007). *Comparaison de fonctions de pédotransfert nationales et européennes*. Étude et Gestion des Sols, 14(2). https://hal.inrae.fr/hal-02667286
- Schaap, M. G., Leij, F. J., van Genuchten, M. Th. (2001). *Rosetta: a computer program for estimating soil hydraulic parameters*. Journal of Hydrology, 251(3–4), 163–176. https://github.com/usda-ars-ussl/rosetta-soil
- Weber, T. K. D., Weihermüller, L., Nemes, A., Bechtold, M. et al. (2024). *Hydro-pedotransfer functions: a roadmap for future development*. Hydrology and Earth System Sciences, 28(14), 3391–3433. https://hess.copernicus.org/articles/28/3391/2024/
- IUSS Working Group WRB (2022). *World Reference Base for Soil Resources, 4th edition*. https://wrb.isric.org/files/WRB_fourth_edition_2022-12-18.pdf
- INRAE UMR ISPA — ONF. *FOR-EVAL Diagnostics*. https://ispa.hub.inrae.fr/outils/outils-d-aide-a-la-decision/for-eval-une-application-mobile-pour-evaluer-les-sols-forestiers/for-eval-diagnostics
- Centre National de la Propriété Forestière (CNPF). *Les stations forestières*. https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/les-stations-forestieres

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
