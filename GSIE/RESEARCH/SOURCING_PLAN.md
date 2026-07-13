# GSIE Sourcing Plan — Plan d'ingestion des sources scientifiques

| Champ | Valeur |
|---|---|
| **Livrable** | 307 — Sourcing Plan |
| **Phase** | 3 — Connaissance |
| **Statut** | Validated |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-005 |
| **Constitutions liées** | Scientifique (S-1, S-6) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |
| **Documents connexes** | 301 (Research Method), 305 (Dataset Catalog), 306 (Evidence Framework), 204 (Engine Development Order) |

---

## 1. Objet

Définir le plan priorisé d'ingestion des sources scientifiques pour
construire la base de connaissances de GSIE. Ce plan aligne l'acquisition
des sources sur l'ordre de développement des moteurs (livrable 204) afin
que chaque moteur dispose des connaissances nécessaires au moment de son
implémentation (Phase 4).

---

## 2. Principes de priorisation

### 2.1 Alignement sur l'ordre des moteurs

Les sources sont ingérées par vagues correspondant aux dépendances des
moteurs (livrable 204) :

```
Vague 0 : Evidence + Knowledge (backbone)
Vague 1 : GIS, Botanical, Pedology, Climate (domaine)
Vague 2 : Correlation, Reasoning (raisonnement)
Vague 3 : Diagnostic, Forest Dynamics (synthèse)
Vague 4 : Simulation, Recommendation, Validation (sortie)
Vague 5 : Learning (transverse)
Vague I : Ignis (incendie — parallèle)
```

### 2.2 Critères de priorisation au sein d'une vague

| Critère | Poids | Description |
|---|---|---|
| Criticité moteur | Élevé | La connaissance est-elle bloquante pour le moteur ? |
| Disponibilité source | Moyen | La source est-elle accessible immédiatement ? |
| Niveau de preuve attendu | Moyen | Priorité aux sources de niveau A-B (S-2) |
| Couverture de domaines | Faible | La source couvre-t-elle plusieurs domaines (S-6) ? |
| Licence | Faible | Licence ouverte préférée (voir 19_LEGAL) |

### 2.3 Règle de non-blocage

Aucune vague n'attend l'ingestion complète de la précédente. Les vagues
se chevauchent : dès qu'une source de la vague N+1 est disponible et que
la vague N est à 70% complétée, l'ingestion N+1 peut commencer.

---

## 3. Vague 0 — Backbone (Evidence + Knowledge)

### 3.1 Objectif

Établir le framework méthodologique : comment évaluer, qualifier et
stocker les connaissances. Aucune connaissance forestière n'est ingérée
dans cette vague — seulement les méta-connaissances.

### 3.2 Sources à ingérer

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| Sacks et al. (2023) — Frameworks d'évidence en écologie | Peer-reviewed | B | Méthodologie | CC-BY |
| Pullin et al. (2018) — Collaboration for Environmental Evidence | Peer-reviewed | B | Méthodologie | CC-BY |
| GRADE — Grading of Recommendations Assessment (santé, adapté) | Référentiel | B | Méthodologie | Domaine public |
| Standards ontologiques OWL/RDF (W3C) | Référentiel | A | Informatique | Domaine public |
| Baize & Jabiol (2008) — RPF INRAE | Référentiel | B | Pédologie | Accord INRAE |
| Rameau et al. (2008) — Flore forestière française | Ouvrage | B | Écologie | IDF |

### 3.3 Critère de complétude

- Framework d'évidence défini (livrable 306).
- Structure KnowledgeObject validée (livrable 302).
- Ontologie forestière initialisée (livrable 303).
- Graphe de connaissances spécifié (livrable 304).

---

## 4. Vague 1 — Moteurs domaine fondamentaux

### 4.1 Botanical Engine

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| Rameau et al. (2008) — Flore forestière française (3 tomes) | Ouvrage | B | Botanique, Écologie | IDF |
| GBIF — Backbone Taxonomic | Référentiel | A | Taxonomie | CC-BY |
| BDNFF — Base Nomenclaturale Flore de France | Référentiel | A | Taxonomie | CC-BY |
| Tela Botanica — eFlore | Référentiel | B | Botanique | CC-BY-SA |
| APG IV (2016) — classification phylogénétique | Peer-reviewed | A | Taxonomie | CC-BY |
| Tutin et al. — Flora Europaea | Ouvrage | A | Taxonomie | Domaine public |
| Boullet et al. — Référentiel des habitats forestiers | Référentiel | B | Écologie | Accord |

### 4.2 Pedology Engine

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| Baize & Jabiol (2008) — RPF INRAE | Référentiel | B | Pédologie | Accord INRAE |
| IUSS WRB (2015) — Base de référence mondiale des sols | Référentiel | A | Pédologie | Domaine public |
| INRAE — BDAT | Dataset | B | Pédologie | Licence Ouverte |
| BRGM — Cartographie géologique 1/50000 | Référentiel | B | Géologie | Licence Ouverte |
| Gobin et al. — Pédologie forestière française | Peer-reviewed | B | Pédologie | CC-BY |
| Legros — Les sols acides | Ouvrage | B | Pédologie | — |

### 4.3 Climate Engine

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| Météo-France — Safran (précipitations, température) | Dataset | B | Climatologie | Accord |
| Météo-France — DRIAS (projections RCP/SSP) | Dataset | B | Climatologie | Licence Ouverte |
| Météo-France — ARPEGE/AROME | Dataset | B | Climatologie | Accord |
| Ozenda (1982/2002) — Végétation de la chaîne alpine | Ouvrage | B | Bioclimatologie | — |
| Badeau et al. (2004) — Changement climatique et forêts | Peer-reviewed | B | Climatologie | CC-BY |
| Chebbi et al. — DRIAS scenarios | Peer-reviewed | B | Climatologie | CC-BY |

### 4.4 GIS Engine

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| IGN — BD Forêt v2 | Dataset | B | Sylviculture | Licence Ouverte |
| IGN — LiDAR HD | Dataset | B | Dendrométrie | Licence Ouverte |
| IGN — BD Ortho | Dataset | B | Télédétection | Licence Ouverte |
| IGN — BD ALTI | Dataset | B | Topographie | Licence Ouverte |
| Copernicus — Sentinel-2 | Dataset | B | Télédétection | CC-BY |
| USGS/NASA — Landsat 8/9 | Dataset | B | Télédétection | Domaine public |

### 4.5 Critère de complétude

- Autécologie de 5 essences ingérée (chêne sessile, hêtre, douglas, sapin pectiné, pin sylvestre).
- Classification pédologique RPF ingérée (au moins 10 types de sol).
- Données climatiques Safran + DRIAS accessibles.
- BD Forêt v2 et LiDAR HD accessibles.

---

## 5. Vague 2 — Raisonnement (Correlation + Reasoning)

### 5.1 Sources à ingérer

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| Rameau et al. (2008) — autécologie détaillée | Ouvrage | B | Écologie | IDF |
| ONF — Guides sylvicoles par région | Document technique | B | Sylviculture | ONF |
| CRPF — Fiches techniques de choix d'essences | Document technique | B | Sylviculture | Licence Ouverte |
| Gégout et al. — EcoPlant (écologie des plantes forestières) | Dataset | B | Écologie | Accord INRAE |
| Piedallu et al. — Distribution des essences et climat | Peer-reviewed | B | Écologie, Climat | CC-BY |
| Nageleisen — Santé des forêts (DSF) | Document technique | B | Pathologie | ONF |

### 5.2 Critère de complétude

- Règles d'adaptation essence-station pour 10 essences.
- Corrélations pH-essence ingérées.
- Corrélations climat-essence ingérées.

---

## 6. Vague 3 — Synthèse (Diagnostic + Forest Dynamics)

### 6.1 Sources à ingérer

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| ONF-FFN — Modèles de croissance (2019) | Référentiel | B | Dendrométrie | ONF |
| INRAE — capsis (modèles de dynamique) | Logiciel scientifique | B | Dynamique | INRAE |
| Deleuze et al. — Modèle de croissance hêtre/douglas | Peer-reviewed | B | Dendrométrie | CC-BY |
| Dhôte — Modèles de croissance futaies régulières | Peer-reviewed | B | Dendrométrie | CC-BY |
| Bouchon — Structure et dynamique des peuplements | Ouvrage | B | Dynamique | — |
| DSF — Bilan annuel santé des forêts | Référentiel | B | Pathologie | ONF |
| INRAE — Chalarose du frêne | Peer-reviewed | C | Pathologie | CC-BY |

### 6.2 Critère de complétude

- Modèles de croissance pour 5 essences.
- Modèles de dynamique de peuplement (capsis).
- Diagnostics pathologiques principaux (chalarose, scolytes, graphiose).

---

## 7. Vague 4 — Sortie (Simulation + Recommendation + Validation)

### 7.1 Sources à ingérer

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| ONF — Guides de sylviculture (régions forestières) | Document technique | B | Sylviculture | ONF |
| CRPF — Recommandations de choix d'essences | Document technique | B | Sylviculture | Licence Ouverte |
| IDF — Fiches de sylviculture par essence | Document technique | B | Sylviculture | IDF |
| Météo-France — DRIAS (scenarios climatiques) | Dataset | B | Climatologie | Licence Ouverte |
| INRAE — Projections d'aire de distribution | Peer-reviewed | C | Écologie, Climat | CC-BY |
| Seidl et al. — Disturbances in forest ecosystems | Peer-reviewed | B | Dynamique | CC-BY |

### 7.2 Critère de complétude

- Recommandations sylvicoles pour 10 essences.
- Projections climatiques intégrées.
- Règles de validation (cohérence, domaine de validité).

---

## 8. Vague 5 — Learning (transverse)

### 8.1 Sources à ingérer

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| Breiman (2001) — Random Forests | Peer-reviewed | A | ML | CC-BY |
| Cutler et al. — Random Forests for classification | Peer-reviewed | A | ML | CC-BY |
| Chen & Guestrin (2016) — XGBoost | Peer-reviewed | A | ML | CC-BY |
| Lundberg & Lee (2017) — SHAP values | Peer-reviewed | A | ML | CC-BY |
| Reichstein et al. (2019) — Deep learning in ecology | Peer-reviewed | B | ML, Écologie | CC-BY |

### 8.2 Critère de complétude

- Méthodes ML pour foresterie documentées.
- Patterns émergents détectables.

---

## 9. Vague I — Ignis (incendie)

### 9.1 Sources à ingérer

| Source | Type | Niveau attendu | Domaine | Licence |
|---|---|---|---|---|
| FIRETWIN (NASA/NSF 2025) — jumeau numérique incendie | Peer-reviewed | B | Incendie | CC-BY |
| FIRE-VLM (2026) — vision-language modeling incendie | Peer-reviewed | C | Incendie, IA | CC-BY |
| IVSR (2026) — immersive visual situational awareness | Peer-reviewed | C | Incendie, UI | CC-BY |
| Prométhée — Base de données incendies France méditerranéenne | Dataset | B | Incendie | Accord |
| EFFIS — European Forest Fire Information System | Dataset | B | Incendie | CC-BY |
| MODIS/FIRMS — Active fire detection | Dataset | B | Incendie | Domaine public |
| Rothermel (1972) — Modèle de propagation du feu | Référentiel | A | Incendie | Domaine public |
| FARSITE — Fire Area Simulator | Logiciel scientifique | B | Incendie | Domaine public |
| Dupuy (2000) — Comportement du feu en France | Peer-reviewed | B | Incendie | — |

### 9.2 Critère de complétude

- Modèle de propagation du feu (Rothermel) ingéré.
- Données Prométhée accessibles.
- Publications FIRETWIN/FIRE-VLM/IVSR ingérées.

---

## 10. Tableau récapitulatif des priorités

| Vague | Moteurs | Domaines prioritaires | Nb sources | Niveau moyen | Période |
|---|---|---|---|---|---|
| 0 | Evidence, Knowledge | Méthodologie | 6 | B | Semaine 1-2 |
| 1 | GIS, Botanical, Pedology, Climate | Botanique, Pédologie, Climat, GIS | 25 | B | Semaine 3-6 |
| 2 | Correlation, Reasoning | Écologie, Sylviculture | 6 | B | Semaine 7-9 |
| 3 | Diagnostic, Forest Dynamics | Dendrométrie, Dynamique, Pathologie | 7 | B | Semaine 10-12 |
| 4 | Simulation, Recommendation, Validation | Sylviculture, Climat | 6 | B | Semaine 13-15 |
| 5 | Learning | ML, Écologie | 5 | A | Semaine 16-17 |
| I | Ignis | Incendie | 9 | B | Parallèle (Semaine 3-12) |

**Total** : 64 sources à ingérer sur 17 semaines (estimation indicative,
non contractuelle — la Phase 3 est de la documentation, pas de
l'implémentation).

---

## 11. Critères de complétude par vague

### 11.1 Vague 0

- Framework d'évidence opérationnel (livrable 306).
- Structure KnowledgeObject validée (livrable 302).
- Ontologie initialisée (livrable 303).
- Graphe spécifié (livrable 304).

### 11.2 Vague 1

- Autécologie de 5 essences (chêne sessile, hêtre, douglas, sapin pectiné, pin sylvestre).
- Classification RPF (10 types de sol).
- Safran + DRIAS accessibles.
- BD Forêt v2 + LiDAR HD accessibles.

### 11.3 Vague 2

- Règles d'adaptation essence-station (10 essences).
- Corrélations pH-essence et climat-essence.

### 11.4 Vague 3

- Modèles de croissance (5 essences).
- Modèles de dynamique (capsis).
- Diagnostics pathologiques (chalarose, scolytes, graphiose).

### 11.5 Vague 4

- Recommandations sylvicoles (10 essences).
- Projections climatiques DRIAS.
- Règles de validation.

### 11.6 Vague 5

- Méthodes ML documentées.
- Patterns émergents détectables.

### 11.7 Vague I

- Modèle Rothermel ingéré.
- Données Prométhée accessibles.
- FIRETWIN/FIRE-VLM/IVSR ingérés.

---

## 12. Risques et mitigations

| Risque | Mitigation |
|---|---|
| Source sous accord (ONF, INRAE, Safran) | Mise en quarantaine (CON-005), négociation licence |
| Source contradictoire (S-3) | Conflit documenté, jamais résolu arbitrairement |
| Source ancienne (< 10 ans) | Conservée mais niveau de preuve plafonné à C |
| Source en anglais | Acceptée, traduction française de la fiche |
| Source inaccessible | Report à la vague suivante, signalement |

---

## 13. Historique

| Date | Événement |
|---|---|
| 2026-07-13 | Création — Phase 3, 7 vagues, 64 sources, alignement moteurs (livrable 204) |

---

> Statut : *Validated — Phase 3 (Connaissance). Documentation uniquement,
> aucune implémentation (Phase 4).*
