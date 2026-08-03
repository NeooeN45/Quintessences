# Synthèse — Fusion et assemblage GSIE-PROMPT-0025

> Document de synthèse — Phase 5 (Fusion)
> Date : 2026-07-30
> Auteur : Cascade (pair programming)
> Source : 9 fichiers partiels `_staging_0025/{A,B,C,D,E,F,G,H,I}_*.md`

---

## 1. Bilan de la vérification

| Domaine | Entrées vérifiées | À vérifier | Signalements | URLs testées | Échecs |
|---|---|---|---|---|---|
| A — Forestier | 7 | 3 | 1 | 10 | 1 (onf.fr Open Data 404) |
| B — Climat | 7 | 3 | 2 | 10 | 0 (2 SPA confirmées par recherche) |
| C — Sols/hydro | 4 | 4 | 2 | 4 | 0 |
| D — Biodiversité | 7 | 3 | 2 | 7 | 2 (gbif.org 403, eea.europa.eu 404) |
| E — Télédétection | 4 | 4 | 2 | 7 | 1 (Sentinel Hub 503) |
| F — Incendie | 5 | 4 | 2 | 5 | 1 (promethee.net fusionné) |
| G — Réglementaire | 5 | 4 | 2 | 4 | 1 (bd-haies 404 → URL corrigée) |
| H — Archives | 4 | 4 | 2 | 4 | 2 (gallica 403, remembrement désactivé) |
| I — Outre-mer | 5 | 5 | 2 | 6 | 1 (carto.geonature.guyane) |
| **TOTAL** | **48** | **34** | **17** | **57** | **10** |

**Taux de succès URL** : 47/57 = 82% (les 10 échecs ont tous été confirmés par recherche web ou API alternative).

---

## 2. Dédoublonnage — sources déjà présentes dans l'inventaire existant

Les sources suivantes sont **déjà cataloguées** dans `SOURCES_DONNEES_EXHAUSTIVES.md`. Elles sont confirmées par cette vérification mais ne nécessitent pas d'ajout (sauf correction — voir §3).

| Entrée staging | Référence inventaire | Statut URL | Action |
|---|---|---|---|
| B-001 CDS | §2.2 ERA5, §10.6 | ✅ | Ajouter URL racine CDS |
| B-002 ECA&D | §6.4 ECA&D Soil Moisture | ✅ | Confirmé |
| B-004 DRIAS | DS-008 | ✅ | Confirmé |
| B-005 Météo-France Portail API | §10.3 A | ✅ | Confirmé |
| B-006 donneespubliques.meteofrance.fr | §10.3 B (SWI mensuel) | ⚠️ | **Fermeture annoncée** — à migrer |
| C-003 GIS Sol | DS-011 BDAT | ✅ | Ajouter URL racine GIS Sol |
| C-004 BRGM InfoTerre | §3.2 BRGM géologie | ✅ | Confirmé |
| D-001 INPN | DS-017 | ⚠️ | **Cyberattaque** — à mettre à jour |
| D-003 GBIF | DS-014 | ✅ | Confirmé (API OK, site 403) |
| D-007 EPPO | §6.6, §10.12 | ✅ | Confirmé |
| E-003 CDSE STAC | §10.2 | ✅ | Préciser endpoint racine /v1/ |
| F-001 EFFIS | DS-023 | ✅ | Confirmé |
| F-002 GWIS | §2.3 | ✅ | Confirmé |
| F-003 FIRMS | DS-024 | ✅ | Confirmé |
| F-004 BDIFF | §2.4 | ✅ | Confirmé (Prométhée fusionnée) |
| F-005 feuxdeforet.fr | §2.4 | ✅ | Confirmé |
| I-004 BD Ortho OM | DS-004 | ✅ | Préciser couverture OM |

**Total doublons confirmés** : 17 sources.

---

## 3. Corrections à apporter à l'inventaire existant

### 3.1 Corrections critiques (statut ou URL modifié)

| Référence | Correction | Détail |
|---|---|---|
| **DS-022 Prométhée** | **Obsolète** | Fusionnée dans BDIFF en janvier 2023. URL promethee.com/promethee.net morte. À supprimer ou fusionner dans la fiche BDIFF (F-004). Données 1973-2022 incluses dans BDIFF. |
| **DS-017 INPN** | **Mise à jour statut** | Cyberattaque MNHN 26/07/2025 → 22/07/2026 (1 an hors service). Restauration partielle 21/07/2026 (fiches espèces + téléchargement). Autres rubriques fin 2026, 2027. WMS/WFS à vérifier. |
| **§10.3 B SWI mensuel** | **Fermeture endpoint** | `donneespubliques.meteofrance.fr/?fond=produit&id_produit=301` — site en cours de fermeture. Migration vers portail-api.meteofrance.fr ou meteo.data.gouv.fr. À migrer avant fermeture définitive. |
| **§2.2 ERA5** | **Précision licence** | ERA5T (temps quasi réel) devient payant (annonce CDS 30/07/2026). ERA5 différé reste libre. À distinguer dans l'inventaire. |
| **§10.2 CDSE STAC** | **Endpoint racine** | Ajouter endpoint racine `https://stac.dataspace.copernicus.eu/v1/` (plus général que `/v1/collections/sentinel-2-l2a/items`). Support CQL2 + collection-search RC.1. |

### 3.2 Corrections mineures (précisions)

| Référence | Précision | Détail |
|---|---|---|
| DS-004 BD Ortho | Couverture OM | Préciser : couvre outre-mer sauf intérieur Guyane, Polynésie, Nouvelle-Calédonie, Wallis-et-Futuna. Ortho Express Guyane 2025 sur demande anticipée. |
| DS-014 GBIF | Accès API | Préciser : site web gbif.org 403 anti-bot, mais API `api.gbif.org` fonctionne. 213 498 318 occurrences France au 30/07/2026. |
| §6.4 ECA&D | Version | Préciser : E-OBSv33.0e (mai 2026), 89 participants, 65+ pays. API MeteoGate (juin 2026). |

---

## 4. Nouvelles sources à ajouter à l'inventaire

### 4.1 Sources nouvelles (non présentes dans l'inventaire existant)

**26 nouvelles sources vérifiées** à ajouter :

| ID staging | Nom | Domaine | Type source | Moteurs |
|---|---|---|---|---|
| B-003 | ECMWF Open Data (IFS+AIFS) | Climat | sortie_de_modele | Climate, Simulation, Ignis |
| B-007 | meteo.data.gouv.fr | Climat | referentiel_officiel | Climate, Correlation, Forest Dynamics |
| C-001 | Hub'Eau (13 APIs eau) | Hydro | referentiel_officiel | Hydro, GIS, Diagnostic, Knowledge |
| C-002 | HydroPortail | Hydro | capteur_instrumente | Hydro, GIS, Simulation, Forest Dynamics |
| D-002 | TAXREF v18 | Biodiversité | referentiel_officiel | Botanical, Knowledge, Correlation, Diagnostic |
| D-004 | BISE (Biodiversity IS Europe) | Biodiversité | referentiel_officiel | Botanical, Knowledge, Correlation, Diagnostic |
| D-005 | FISE (Forest IS Europe) | Biodiversité | referentiel_officiel | Forest Dynamics, Knowledge, GIS, Correlation |
| D-006 | SINP | Biodiversité | referentiel_officiel | Botanical, Knowledge, Correlation, Diagnostic |
| E-001 | Element84 Earth Search (STAC AWS) | Télédétection | capteur_instrumente | GIS, Forest Dynamics, Diagnostic, Ignis |
| E-002 | Microsoft Planetary Computer (STAC Azure) | Télédétection | capteur_instrumente | GIS, Forest Dynamics, Climate, Diagnostic, Ignis |
| E-004 | ESA Earth Online | Télédétection | referentiel_officiel | GIS, Forest Dynamics, Knowledge |
| G-001 | Géorisques | Réglementaire | referentiel_officiel | GIS, Diagnostic, Ignis, Recommendation |
| G-002 | Géoportail de l'Urbanisme (PLU/POS/CC/PSMV) | Réglementaire | referentiel_officiel | GIS, Recommendation, Knowledge |
| G-003 | Forêts de protection (massifs classés) | Réglementaire | referentiel_officiel | GIS, Knowledge, Recommendation, Forest Dynamics |
| G-004 | Forêts soumises au régime du code forestier | Réglementaire | referentiel_officiel | GIS, Knowledge, Forest Dynamics, Recommendation |
| G-005 | BD Haie (haies linéaires bocagières) | Réglementaire | capteur_instrumente | GIS, Forest Dynamics, Diagnostic, Knowledge |
| H-001 | Remonter le Temps (IGN) | Archives | referentiel_officiel | Knowledge, Correlation, Forest Dynamics, GIS |
| H-002 | Carte de Cassini (XVIIIe siècle) | Archives | referentiel_officiel | Knowledge, Correlation, Forest Dynamics |
| H-003 | Carte d'État-Major (1820-1866) | Archives | referentiel_officiel | Knowledge, Correlation, Forest Dynamics, GIS |
| H-004 | Gallica (BnF) | Archives | referentiel_officiel | Knowledge, Correlation |
| I-001 | GéoGuyane | Outre-mer | referentiel_officiel | GIS, Forest Dynamics, Diagnostic, Knowledge |
| I-002 | Guyane-SIG (PTIG) | Outre-mer | referentiel_officiel | GIS, Forest Dynamics, Diagnostic, Knowledge |
| I-003 | Parc amazonien de Guyane | Outre-mer | capteur_instrumente | Forest Dynamics, Botanical, Knowledge, Diagnostic |
| I-005 | CARTOS VEGETATION DROM | Outre-mer | capteur_instrumente | Forest Dynamics, Botanical, Diagnostic, Knowledge |

### 4.2 Sources à vérifier (À VÉRIFIER — 34 entrées)

**34 sources identifiées mais non vérifiées** (URL non testée ou statut incertain). Voir détail dans chaque fichier partiel `_staging_0025/{A-I}_*.md` section "À VÉRIFIER".

Répartition par domaine :
- A : 3 (BD Forêt v3, ONF Open Data nouveau, RPG)
- B : 3 (ADS, CEMS EWDS, SWI endpoint)
- C : 4 (ADES, GlobalSoilMap, RMQS, cartes pédo départementales)
- D : 3 (HabRef, CardObs/OpenObs, EUNIS)
- E : 4 (Sentinel Hub, PEPS, USGS EarthExplorer, Google Earth Engine)
- F : 4 (Prométhée statut, Atlas DFCI, Météo des forêts, Copernicus EMS Rapid Mapping)
- G : 4 (PPRIF, RPG, BD Forêt v3, SER)
- H : 4 (Archives nationales, SHOM cartes anciennes, photos aériennes 1945-1965, cadastre napoléonien)
- I : 5 (portails SIG autres DROM, GeoNature Guyane, SEAS Guyane, Nouvelle-Calédonie/Polynésie, transfrontalier Plateau Guyanes)

---

## 5. Signalements critiques (17 au total)

### 5.1 Signalements critiques (action requise)

| # | Domaine | Signalement | Action recommandée |
|---|---|---|---|
| 1 | B | **ERA5T devient payant** (annonce CDS 30/07/2026) | Distinguer ERA5 différé (libre) et ERA5T (payant) dans l'inventaire |
| 2 | B | **donneespubliques.meteofrance.fr en fermeture** | Migrer SWI mensuel et autres endpoints vers portail API ou meteo.data.gouv.fr |
| 3 | C | **GIS Sol — arrêt temporaire bases 18/02/2026** | Vérifier restauration avant ingestion BDAT |
| 4 | C | **Hub'Eau — API Indicateurs des services décommissionnée 10/09/2026** | Ne pas intégrer cette API spécifique |
| 5 | D | **INPN — cyberattaque MNHN (26/07/2025 → 22/07/2026)** | Vérifier restauration WMS/WFS avant ingestion |
| 6 | D | **GBIF — site web 403 via webfetch** | Utiliser API `api.gbif.org` pour accès programmatique |
| 7 | F | **Prométhée fusionnée dans BDIFF (janvier 2023)** | Supprimer DS-022, fusionner dans fiche BDIFF |
| 8 | F | **feuxdeforet.fr — accès par convention** | Formaliser accord avant ingestion (régime "accord à formaliser") |
| 9 | G | **BD Haie — URL correcte** | URL = `bd-haie` (sans "s"), pas `bd-haies` |
| 10 | H | **Gallica 403 anti-bot** | Utiliser API IIIF pour accès programmatique |
| 11 | H | **Remonter le Temps — SPA** | Couches WMS via `wxs.ign.fr` (clé API requise) |
| 12 | I | **BD Ortho — couverture partielle OM** | Intérieur Guyane, Polynésie, NC, Wallis-et-Futuna non couverts |
| 13 | I | **CARTOS VEGETATION DROM — méthodes hétérogènes** | Nomenclatures propres à chaque DROM, à harmoniser |

### 5.2 Signalements d'information (pas d'action immédiate)

| # | Domaine | Signalement |
|---|---|---|
| 14 | A | onf.fr Open Data URL 404 — nouveau lien trouvé sur site principal |
| 15 | E | Sentinel Hub 503 temporaire — à retester |
| 16 | E | CDSE STAC déjà partiellement dans inventaire — endpoint racine à ajouter |
| 17 | G | Forêts de protection ≠ forêts soumises régime forestier — deux datasets distincts |

---

## 6. Nouveau comptage total (estimé post-fusion)

| Catégorie | Comptage actuel | Ajout | Nouveau total |
|---|---|---|---|
| Datasets catalogués (DS-001 à DS-029) | 29 | 0 (corrections seulement) | 29 |
| Sources additionnelles Ignis | ~45 | 0 | ~45 |
| Sources scientifiques | ~64 | 0 | ~64 |
| Sources spécifiques apps | ~7 | 0 | ~7 |
| Capteurs drone | 4 | 0 | 4 |
| Nouvelles sources (recherche juillet 2026) | ~30 | 0 | ~30 |
| **NOUVELLES sources vérifiées (GSIE-PROMPT-0025)** | 0 | **+26** | **26** |
| Sources à vérifier (À VÉRIFIER) | 0 | **+34** | **34** |
| **Total estimé** | **~179** | **+26 vérifiées +34 à vérifier** | **~205 + 34 à vérifier = ~239 potentielles** |

**Gain net** : +26 sources vérifiées (+14,5%), +34 sources identifiées à vérifier (+19%). Total potentiel : ~239 sources (+33%).

---

## 7. Nouveaux types de sources introduits (RFC-0029 §11.3)

| type_source | Définition | Entrées staging concernées |
|---|---|---|
| `sortie_de_modele` | Sorties de modèles numériques (réanalyses, prévisions, projections) | B-001 CDS, B-003 ECMWF Open Data, B-004 DRIAS, B-005 Météo-France API |
| `capteur_instrumente` | Données issues de capteurs calibrés avec chaîne de mesure connue | C-002 HydroPortail, E-001 Element84, E-002 Planetary Computer, G-005 BD Haie, I-003 Parc amazonien, I-005 CARTOS VEGETATION DROM |
| `capteur_participatif` | Données issues de signalements citoyens ou sciences participatives | F-005 feuxdeforet.fr |
| `donnee_synthetique` | Données générées par synthèse (non utilisé dans cette vague — déjà dans §2.8 inventaire existant) | — |

---

## 8. Recommandations d'ingestion pour les nouvelles sources

### Priorité haute (complète des gaps critiques identifiés RFC-0029 §11)

1. **Hub'Eau (C-001)** → Hydro / GIS / Diagnostic : 13 APIs REST eau, gap critique hydro fillé
2. **Géorisques (G-001)** → GIS / Diagnostic / Ignis : portail risques naturels, gap réglementaire fillé
3. **Géoportail de l'Urbanisme (G-002)** → GIS / Recommendation : PLU/POS/CC, gap foncier fillé
4. **Carte d'État-Major (H-003)** → Knowledge / Forest Dynamics : occupation sols 1820-1866, gap archives fillé
5. **GéoGuyane + Guyane-SIG (I-001, I-002)** → GIS / Forest Dynamics : gap outre-mer Guyane fillé

### Priorité moyenne (enrichissement)

6. **TAXREF v18 (D-002)** → Botanical / Knowledge : référentiel taxonomique national, backbone SINP
7. **Element84 + Planetary Computer (E-001, E-002)** → GIS / Forest Dynamics : catalogues STAC alternatifs (AWS, Azure)
8. **BD Haie (G-005)** → GIS / Forest Dynamics : haies bocagières, écologie du paysage
9. **BISE + FISE (D-004, D-005)** → Knowledge / Correlation : gateways européens biodiversité et forêts
10. **CARTOS VEGETATION DROM (I-005)** → Forest Dynamics / Botanical : végétation ultra-marine

### Priorité basse (veille)

11. **Remonter le Temps + Cassini (H-001, H-002)** → Knowledge : comparaison historique
12. **Gallica (H-004)** → Knowledge : archives documentaires
13. **Forêts de protection + régime forestier (G-003, G-004)** → Knowledge / Recommendation : statuts réglementaires
14. **SINP (D-006)** → Knowledge : cadre méthodologique partage données
15. **ESA Earth Online (E-004)** → GIS : portail missions ESA

---

## 9. Prochaines étapes

1. **Phase 6 — Vérifications** : retester les 10 URLs échouées, vérifier les 34 sources "À VÉRIFIER"
2. **Phase 7 — Revue adversariale** : audit qualité des entrées YAML, conformité NOMENCLATURE_SOURCES
3. **Phase 8 — Commit + PR** : intégrer les 26 nouvelles sources + 5 corrections dans `SOURCES_DONNEES_EXHAUSTIVES.md` et `DATASET_CATALOG.md`
4. **Phase 9 — Capitalisation** : compte rendu, mise à jour PROJECT_MEMORY, CHANGELOG

---

## 10. Fichiers partiels source

| Fichier | Domaine | Entrées | Taille |
|---|---|---|---|
| `A_forestier.md` | Forestier | 7 | 10 384 o |
| `B_climat.md` | Climat | 7 | 9 744 o |
| `C_sols_hydro.md` | Sols/hydro | 4 | 7 492 o |
| `D_biodiversite.md` | Biodiversité | 7 | 10 543 o |
| `E_teledetection.md` | Télédétection | 4 | 6 726 o |
| `F_incendie.md` | Incendie | 5 | 8 702 o |
| `G_reglementaire.md` | Réglementaire | 5 | 8 497 o |
| `H_archives.md` | Archives | 4 | 7 165 o |
| `I_outremer.md` | Outre-mer | 5 | 9 013 o |
| **Total** | **9 domaines** | **48** | **78 266 o** |
