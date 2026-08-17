# Priorisation des besoins d'intégration des sources GSIE — 2026-08-13

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-PRIORISATION-001 |
| **Statut** | Draft — validation du Fondateur requise |
| **Version** | 1.0.0 |
| **Principe** | Intégrer selon la valeur métier et la maturité juridique, pas selon la quantité disponible |
| **Ressources locales** | `E:\Documents` volontairement reportées en dernier |

## 1. Niveaux de besoin d'intégration

| Niveau | Besoin | Critère d'entrée | Action autorisée |
|---|---|---|---|
| **I0 — Socle Registry** | Référencer immédiatement les sources déjà nécessaires au fonctionnement | Source déjà appelée par un adapter ou indispensable à l'identité d'une donnée | Fiche Registry complète, santé, version, droits ; FETCH reste fermé par défaut |
| **I1 — Intégration métier prioritaire** | Alimenter les moteurs sans attendre un enrichissement IA | Source officielle, cas d'usage clair, valeur pour GeoSylva/GSIE | Qualification juridique/technique puis adapter borné |
| **I2 — Intégration scientifique contrôlée** | Améliorer les diagnostics et corrélations | Référentiel ou dataset utile, mais qualité, granularité ou droits à confirmer | Research + fiche Registry ; tests et validation experte avant données dérivées |
| **I3 — Partenaire / recherche / benchmark** | Comparer, enrichir ou préparer des partenariats | Source prometteuse mais accès propriétaire, sensible, mondial ou non stabilisé | Metadata-only, citation, benchmark fermé ou accord partenaire |
| **I4 — Local différé** | Exploiter les productions et données locales | Donnée privée, personnelle, de stage ou géospatiale locale | Dernière tranche uniquement, quarantaine et consentement explicite |
| **X — Exclue ou obsolète** | Ne pas intégrer | URL morte, doublon technique, source remplacée ou usage hors périmètre | Conserver la trace historique, aucune ingestion |

## 2. Ordre global recommandé

```text
I0 — Registry des sources déjà consommées
        ↓
I1 — Socle forestier, climat, sols, eau et taxonomie
        ↓
I2 — Dendrométrie, santé, biodiversité, télédétection et hydrographie avancée
        ↓
I3 — Partenaires, sources mondiales, IA, données incendie et Treekipedia
        ↓
I4 — Ressources locales de E:\Documents
```

Chaque niveau comprend d'abord la fiche Registry et la qualification juridique,
ensuite seulement la conception de l'adapter. Aucun niveau n'ouvre FETCH à lui
seul : l'ouverture reste source par source, bornée, checksumée et autorisée.

## 3. Classement des familles canoniques

### I0 — Socle Registry

| ID | Source | Rôle |
|---|---|---|
| DS-013 | SoilGrids | Sols ; micro-extrait déjà autorisé, FETCH canonique fermé |
| DS-014 | GBIF | Occurrences et validation taxonomique |
| DS-007/009/010 | Météo-France (Safran, AROME, observations) | Météo, contrôle terrain et risque |
| — | IGN API Carto / Géoplateforme | Parcelles, limites, WFS/WMTS et recherche spatiale |
| DS-003 | DataIFN / Inventaire Forestier National | Placettes et calibration dendrométrique |

### I1 — Intégration métier prioritaire

| ID | Source | Moteurs concernés |
|---|---|---|
| DS-001 | BD Forêt v2 | GIS, Diagnostic, Forest Dynamics |
| DS-002 | LiDAR HD | GIS, Forest Dynamics, Ignis, Simulation |
| DS-004 | BD Ortho | GIS, Diagnostic, validation visuelle |
| DS-008 | DRIAS | Climate, Simulation, adaptation |
| DS-011 | BDAT | Pedology, Diagnostic, Correlation |
| DS-017 | INPN/TAXREF/SINP | Botanical, biodiversité, Diagnostic |
| DS-018 | Sentinel-2 | GIS, stress, Diagnostic, Ignis |
| DS-022b | BDIFF | Ignis, historique feux, Validation |
| D5-01 à D5-05 | Hub'Eau | Hydro, Climate, Diagnostic |
| D5-06 à D5-16 | Vigicrues, SANDRE, ADES, BD Topage, BDLISA, RPDZH | Hydro et risques |

### I2 — Intégration scientifique contrôlée

| Famille | Sources |
|---|---|
| Stations et écologie | DS-005 RPF, DS-006 F-ORE-T, DS-012 RPFR, DS-034a à f, ICP Forests, RENECOFOR |
| Botanique | DS-015 Tela Botanica, DS-016 BDNFF, IPNI, WCVP, WFO, Catalogue of Life, ITIS, WoRMS |
| Sols et géologie | WRB, WoSIS, InfoTerre BRGM, ESDAC, GIS Sol/IGCS, LUCAS Soil, GéoNormandie |
| Climat avancé | CDS, CMIP6/ESGF, DRIAS-Eau, ClimEssences, BioClimSol/FORECCAsT, Climadiag |
| Télédétection | DS-019 Sentinel-1, DS-020 Landsat, DS-021 MODIS, DS-025 GEDI, DS-026 Biomass CCI, DS-027 CoSIA, DS-028 OCS GE |
| Santé forestière | DSF, DEPERIS, inventIF Santé, ForDead, Ephytia, ICP Forests, FCBA |
| Faune et biodiversité | OpenObs, BDC-Statuts, LPO, SHF, SFEPM, UICN/PatriNat, STOC |
| Pathologie et microbiologie | EPPO, Q-Bank, FongiBase, MycoBank, GlobalFungi, FungalTraits, RMQS, EMP, GSBI |

### I3 — Partenaires, recherche et benchmark

| Ressource | Motif |
|---|---|
| Treekipedia/Silvi | Grande valeur taxonomique et écologique ; accès API et droits des données agrégées à qualifier |
| DS-018/019/020 hors France | Comparaison internationale et séries longues, pas socle GeoSylva |
| GEDI, Biomass CCI, Global Forest Watch, HydroSHEDS | Contexte mondial ou benchmark, grain souvent trop grossier pour une décision locale |
| AIFS, GenCast, Aurora, CorrDiff, FourCastNet | Modèles météo de recherche ; benchmark avant dépendance opérationnelle |
| Pyro-SDIS, FLAME, D-Fire, FASDD, FireBench | Jeux d'apprentissage incendie ; droits et vérité terrain à vérifier |
| Meshtastic, sensor.community, Météorage, Blitzortung | Capteurs/partenariats, qualification technique et contractuelle nécessaire |
| ForeFire, FARSITE, Rothermel, Balbi, Dupuy | Modèles de simulation ; intégration après baselines déterministes Ignis |

### I4 — Ressources locales différées

Toutes les ressources inventoriées dans `E:\Documents` : fiches BTS, relevés,
GeoPackages, shapefiles, rasters, rapports de stage, images, données PSG et
productions personnelles. Elles ne sont pas intégrées dans cette tranche.

### X — Excluses ou historiques

| ID/ressource | Décision |
|---|---|
| DS-022 Prométhée | Obsolète, remplacé par DS-022b BDIFF |
| Fonds de carte uniquement | Proxy QGISIA ; jamais preuve versionnée sans archivage |
| Doublons de catalogue | Réconcilier par checksum/provenance, ne pas créer un Dataset distinct |
| URL/API mortes ou non vérifiées | Conserver en historique, statut `blocked` |

## 4. Règle de fiche Registry

Chaque source retenue reçoit une fiche comportant au minimum :

```text
source_registry_id
title / description
producteur (Agent)
type (dataset, API, service, publication, modèle, référentiel)
domaines GSIE et moteurs consommateurs
URL officielle, documentation, date de consultation
version/millésime et couverture temporelle
territoire, emprise et grain natif si spatial
format et méthode d'accès
licence et droits d'utilisation
attribution, indexation, dérivés, redistribution offline, entraînement IA
qualité, Evidence Level, santé et limites connues
statut Registry, routage et niveau I0–I4/X
preuves manquantes, décision et historique
```

Les valeurs inconnues sont écrites `à_qualifier` ; elles ne sont jamais
remplacées par une supposition. Une fiche `à_qualifier` reste
`metadata_only`, sans FETCH, sans ingestion et sans promotion.

## 5. Tranches d'exécution

1. **Tranche A** : fiches complètes I0 et rapprochement avec
   `SCIENTIFIC_SOURCES` et `REGISTRY_MANIFEST.json`.
2. **Tranche B** : fiches I1, contrôle des quotas/allowlists et adapters
   bornés sans activation globale.
3. **Tranche C** : fiches I2, relecture scientifique et tests de provenance.
4. **Tranche D** : fiches I3, accords partenaires et benchmarks fermés.
5. **Tranche E** : ressources locales I4 de `E:\Documents`, dernière étape.

## 6. Références

- `GSIE/DATASETS/NOMENCLATURE_SOURCES.md`
- `GSIE/DATASETS/REGISTRY_MANIFEST.json`
- `GSIE/DATASETS/FETCH_QUALIFICATION.json`
- `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md`
- `GSIE/DATASETS/CATALOGUE_RESSOURCES_EXHAUSTIF_2026-08-13.md`
- `GSIE/RESEARCH/SOURCES/sources_d1_taxonomie_botanique.md` à
  `sources_d8_pathologie_forestiere.md`
- `GSIE/API/src/gsie_api/governance/source_registry.py`

## 7. Historique

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-13 | Classement des sources par besoin d'intégration ; ressources locales explicitement reportées en dernier. |
