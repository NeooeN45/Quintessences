# GSIE Knowledge Base Seed — Premières connaissances validées

| Champ | Valeur |
|---|---|
| **Livrable** | 308 — Knowledge Base Seed |
| **Phase** | 3 — Connaissance |
| **Statut** | Draft |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1, S-2, S-3, S-5) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |
| **Documents connexes** | 302 (Knowledge Method), 303 (Forest Ontology), 306 (Evidence Framework) |

---

## 1. Objet

Contenir les **premières connaissances concrètes validées** de la base
de connaissances GSIE. Ce livrable amorce la base avec 25 connaissances
couvrant l'autécologie de 5 essences françaises, des seuils
pédologiques, des modèles de croissance et des classifications
taxonomiques.

Chaque connaissance respecte la structure `KnowledgeObject` définie
dans le livrable 302 et porte un niveau de preuve (S-2, livrable 306).

---

## 2. Convention de présentation

Chaque connaissance est présentée sous forme de bloc structuré :

```
### K-XXX : <titre>

| Champ | Valeur |
|---|---|
| connaissance_id | K-XXX |
| type | concept / relation / regle / seuil / modele / classification |
| titre | <titre court> |
| description | <description> |
| evidence_level | A / B / C / D / E / F |
| source | <référence complète> |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | <domaine S-6> |
| domaines_validite | <conditions d'application> |
| moteurs_consommateurs | <moteurs> |
| relations | <liens vers autres K-XXX> |
| mots_cles | <mots-clés> |
```

---

## 3. Autécologie du chêne sessile (Quercus petraea)

### K-001 : Autécologie du chêne sessile — concept général

| Champ | Valeur |
|---|---|
| connaissance_id | K-001 |
| type | concept |
| titre | Autécologie du chêne sessile |
| description | Le chêne sessile (Quercus petraea) est une essence post-pionnière de demi-ombre, adaptée aux sols acides à moyennement acides. Il tolère les sols superficiels et les conditions hydriques contrastées. |
| evidence_level | A |
| source | Rameau et al. (2008), Flore forestière française, guide écologique illustré, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | France métropolitaine, plaine et colline |
| moteurs_consommateurs | Botanical, Diagnostic, Recommendation |
| relations | K-002 (seuil pH), K-003 (seuil précipitations), K-004 (relation sol acide) |
| mots_cles | chêne sessile, Quercus petraea, autécologie |

### K-002 : pH optimal du chêne sessile

| Champ | Valeur |
|---|---|
| connaissance_id | K-002 |
| type | seuil |
| titre | pH optimal du chêne sessile |
| description | Le chêne sessile préfère les sols acides à moyennement acides, pH compris entre 4,5 et 6,5. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | pH ∈ [4,5 ; 6,5], France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic, Recommendation |
| relations | K-001 (concept), K-004 (relation), K-016 (classification pH) |
| mots_cles | chêne sessile, pH, seuil, acidité |

### K-003 : Précipitations minimales du chêne sessile

| Champ | Valeur |
|---|---|
| connaissance_id | K-003 |
| type | seuil |
| titre | Précipitations minimales du chêne sessile |
| description | Le chêne sessile requiert au minimum 700 mm de précipitations annuelles pour un développement optimal. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Climatologie et bioclimatologie |
| domaines_validite | Précipitations ≥ 700 mm/an, France métropolitaine |
| moteurs_consommateurs | Climate, Diagnostic, Recommendation |
| relations | K-001 (concept) |
| mots_cles | chêne sessile, précipitations, climat, seuil |

### K-004 : Chêne sessile adapté aux sols acides

| Champ | Valeur |
|---|---|
| connaissance_id | K-004 |
| type | relation |
| titre | Chêne sessile adapté aux sols acides |
| description | Le chêne sessile est adapté aux sols acides (pH < 6,5). |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | pH < 6,5, France métropolitaine |
| moteurs_consommateurs | Reasoning, Recommendation |
| relations | K-001 (concept), K-002 (seuil pH) |
| mots_cles | chêne sessile, sol acide, adaptation |

---

## 4. Autécologie du hêtre (Fagus sylvatica)

### K-005 : RUM minimale du hêtre

| Champ | Valeur |
|---|---|
| connaissance_id | K-005 |
| type | seuil |
| titre | RUM minimale du hêtre |
| description | Le hêtre requiert une réserve utile en eau (RUM) minimale de 80 mm pour un développement optimal. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | RUM ≥ 80 mm, France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic, Recommendation |
| relations | K-001 (concept hêtre), K-015 (classes RUM) |
| mots_cles | hêtre, Fagus sylvatica, RUM, eau, seuil |

### K-006 : Vulnérabilité du hêtre au déficit hydrique

| Champ | Valeur |
|---|---|
| connaissance_id | K-006 |
| type | seuil |
| titre | Vulnérabilité du hêtre au déficit hydrique en plaine |
| description | Le hêtre est vulnérable au déficit hydrique en dessous de 800 m d'altitude en zone atlantique. |
| evidence_level | C |
| source | INRAE — Badeau et al. (2004), Changement climatique et forêts françaises |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Climatologie et bioclimatologie |
| domaines_validite | Altitude < 800 m, France atlantique |
| moteurs_consommateurs | Climate, Diagnostic, Simulation |
| relations | K-005 (RUM), K-007 (relation climat atlantique) |
| mots_cles | hêtre, déficit hydrique, climat, vulnérabilité |

### K-007 : Hêtre dépendant du climat atlantique

| Champ | Valeur |
|---|---|
| connaissance_id | K-007 |
| type | relation |
| titre | Hêtre dépendant du climat atlantique |
| description | Le hêtre est dépendant d'un climat atlantique tempéré avec humidité atmosphérique élevée. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Climatologie et bioclimatologie |
| domaines_validite | France atlantique, climat tempéré |
| moteurs_consommateurs | Climate, Recommendation |
| relations | K-005 (RUM), K-006 (vulnérabilité) |
| mots_cles | hêtre, climat atlantique, dépendance |

---

## 5. Autécologie du douglas (Pseudotsuga menziesii)

### K-008 : pH optimal du douglas

| Champ | Valeur |
|---|---|
| connaissance_id | K-008 |
| type | seuil |
| titre | pH optimal du douglas |
| description | Le douglas préfère les sols acides à moyennement acides, pH compris entre 4,5 et 6,5. |
| evidence_level | B |
| source | ONF — Guide de sylviculture du douglas (2019) |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | pH ∈ [4,5 ; 6,5], France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic, Recommendation |
| relations | K-009 (modèle croissance), K-010 (relation sol profond) |
| mots_cles | douglas, Pseudotsuga menziesii, pH, seuil |

### K-009 : Modèle de croissance du douglas

| Champ | Valeur |
|---|---|
| connaissance_id | K-009 |
| type | modele |
| titre | Croissance du douglas (ONF-FFN) |
| description | Modèle de croissance ONF-FFN pour le douglas : production moyenne de 12 m³/ha/an sur sol profond et bien alimenté en eau. |
| evidence_level | B |
| source | ONF-FFN (2019), Modèles de croissance forestière française |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Dendrométrie et croissance |
| domaines_validite | Sols profonds, pH 4,5-6,5, précipitations > 800 mm, France métropolitaine |
| moteurs_consommateurs | Forest Dynamics, Simulation |
| relations | K-008 (pH), K-010 (sol profond) |
| mots_cles | douglas, croissance, ONF-FFN, modèle |

### K-010 : Douglas croît mieux sur sol profond

| Champ | Valeur |
|---|---|
| connaissance_id | K-010 |
| type | relation |
| titre | Douglas croît mieux sur sol profond |
| description | Le douglas présente une croissance optimale sur sols profonds (> 60 cm) bien drainés. |
| evidence_level | B |
| source | ONF — Guide de sylviculture du douglas (2019) |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | Profondeur > 60 cm, France métropolitaine |
| moteurs_consommateurs | Pedology, Recommendation |
| relations | K-008 (pH), K-009 (modèle croissance) |
| mots_cles | douglas, sol profond, croissance |

---

## 6. Autécologie du sapin pectiné (Abies alba)

### K-011 : Précipitations minimales du sapin pectiné

| Champ | Valeur |
|---|---|
| connaissance_id | K-011 |
| type | seuil |
| titre | Précipitations minimales du sapin pectiné |
| description | Le sapin pectiné requiert au minimum 1000 mm de précipitations annuelles. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Climatologie et bioclimatologie |
| domaines_validite | Précipitations ≥ 1000 mm/an, France métropolitaine, montagne |
| moteurs_consommateurs | Climate, Diagnostic, Recommendation |
| relations | K-012 (gel) |
| mots_cles | sapin pectiné, Abies alba, précipitations, seuil |

### K-012 : Résistance au gel du sapin pectiné

| Champ | Valeur |
|---|---|
| connaissance_id | K-012 |
| type | seuil |
| titre | Résistance au gel du sapin pectiné |
| description | Le sapin pectiné résiste au gel jusqu'à -20°C selon la provenance. |
| evidence_level | C |
| source | INRAE — Données expérimentales provenances (2015) |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Climatologie et bioclimatologie |
| domaines_validite | France métropolitaine, montagne |
| moteurs_consommateurs | Climate, Diagnostic |
| relations | K-011 (précipitations) |
| mots_cles | sapin pectiné, gel, résistance, seuil, conflit |
| conflits | Voir §8 — Conflit K-012a / K-012b |

---

## 7. Autécologie du pin sylvestre (Pinus sylvestris)

### K-013 : Tolérance pH du pin sylvestre

| Champ | Valeur |
|---|---|
| connaissance_id | K-013 |
| type | seuil |
| titre | Tolérance pH du pin sylvestre |
| description | Le pin sylvestre tolère une large gamme de pH, de 4,0 à 7,0. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | pH ∈ [4,0 ; 7,0], France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic, Recommendation |
| relations | K-014 (relation sol pauvre) |
| mots_cles | pin sylvestre, Pinus sylvestris, pH, tolérance |

### K-014 : Pin sylvestre adapté aux sols pauvres

| Champ | Valeur |
|---|---|
| connaissance_id | K-014 |
| type | relation |
| titre | Pin sylvestre adapté aux sols pauvres |
| description | Le pin sylvestre est adapté aux sols pauvres et superficiels, notamment sur grès et sable. |
| evidence_level | B |
| source | Rameau et al. (2008), Flore forestière française, tome 1, IDF |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Écologie forestière et stationnelle |
| domaines_validite | Sols pauvres, France métropolitaine |
| moteurs_consommateurs | Reasoning, Recommendation |
| relations | K-013 (pH) |
| mots_cles | pin sylvestre, sol pauvre, adaptation |

---

## 8. Conflit bibliographique documenté (S-3)

### Conflit K-012 : Résistance au gel du sapin pectiné

| Source | Valeur | Niveau de preuve | Contexte |
|---|---|---|---|
| INRAE (2015) — provenances du Nord | -20°C | C | Vosges, Jura, Alpes du Nord |
| INRAE (2020) — provenances du Sud | -15°C | C | Pyrénées, Alpes du Sud, Méditerranéen |

**Résolution** : Aucune. Les deux valeurs sont conservées (S-3). Le
contexte (provenance) est documenté. L'utilisateur voit les deux
valeurs avec leur contexte.

**Structure formelle** :

```
ConflitBibliographique = {
  conflit_id       : CBF-001
  connaissance     : K-012
  sources          : [INRAE 2015, INRAE 2020]
  valeurs          : [-20°C, -15°C]
  niveaux_preuve   : [C, C]
  contextes        : [provenances Nord, provenances Sud]
  resolution       : "non résolu — les deux valeurs sont conservées"
  date_detection   : 2026-07-13
}
```

---

## 9. Seuils pédologiques

### K-015 : Classes de réserve utile en eau (RUM)

| Champ | Valeur |
|---|---|
| connaissance_id | K-015 |
| type | classification |
| titre | Classes de réserve utile en eau (RUM) |
| description | Classification de la RUM : faible (< 70 mm), moyen (70-150 mm), fort (> 150 mm). |
| evidence_level | B |
| source | RPF INRAE — Baize & Jabiol (2008), Référentiel Pédologique Forestier |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Pédologie |
| domaines_validite | France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic, Recommendation |
| relations | K-005 (RUM hêtre), K-017 (profondeur sol) |
| mots_cles | RUM, réserve utile, eau, pédologie, classification |

### K-016 : Classes de pH forestier

| Champ | Valeur |
|---|---|
| connaissance_id | K-016 |
| type | classification |
| titre | Classes de pH forestier |
| description | Classification du pH en forêt : très acide (< 4,5), acide (4,5-5,5), moyennement acide (5,5-6,5), neutre (> 6,5). |
| evidence_level | B |
| source | RPF INRAE — Baize & Jabiol (2008), Référentiel Pédologique Forestier |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Pédologie |
| domaines_validite | France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic, Recommendation |
| relations | K-002 (pH chêne), K-008 (pH douglas), K-013 (pH pin) |
| mots_cles | pH, acidité, pédologie, classification |

### K-017 : Profondeur de sol minimale pour enracinement

| Champ | Valeur |
|---|---|
| connaissance_id | K-017 |
| type | seuil |
| titre | Profondeur de sol minimale pour enracinement |
| description | Une profondeur de sol minimale de 40 cm est requise pour un enracinement forestier fonctionnel. |
| evidence_level | B |
| source | RPF INRAE — Baize & Jabiol (2008), Référentiel Pédologique Forestier |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Pédologie |
| domaines_validite | France métropolitaine |
| moteurs_consommateurs | Pedology, Diagnostic |
| relations | K-010 (sol profond douglas), K-015 (RUM) |
| mots_cles | profondeur, sol, enracinement, seuil |

### K-018 : Classification Alocrisol

| Champ | Valeur |
|---|---|
| connaissance_id | K-018 |
| type | classification |
| titre | Alocrisol (RPF) |
| description | L'Alocrisol est un sol forestier acide (pH < 5,5) avec une altération modérée, typique des contextes cristallins ou gréseux. |
| evidence_level | B |
| source | RPF INRAE — Baize & Jabiol (2008), Référentiel Pédologique Forestier |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Pédologie |
| domaines_validite | France métropolitaine, substrats acides |
| moteurs_consommateurs | Pedology, GIS |
| relations | K-016 (classes pH), K-002 (pH chêne), K-013 (pH pin) |
| mots_cles | Alocrisol, RPF, sol acide, pédologie |

### K-019 : Classification Brunisol

| Champ | Valeur |
|---|---|
| connaissance_id | K-019 |
| type | classification |
| titre | Brunisol (RPF) |
| description | Le Brunisol est un sol forestier à pH modérément acide à neutre (5,5-7,0), bien structuré, typique des contextes calcaires ou limoneux. |
| evidence_level | B |
| source | RPF INRAE — Baize & Jabiol (2008), Référentiel Pédologique Forestier |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Pédologie |
| domaines_validite | France métropolitaine, substrats calcaires ou limoneux |
| moteurs_consommateurs | Pedology, GIS |
| relations | K-016 (classes pH) |
| mots_cles | Brunisol, RPF, sol neutre, pédologie |

---

## 10. Modèles de croissance

### K-020 : Modèle de croissance ONF-FFN — douglas

| Champ | Valeur |
|---|---|
| connaissance_id | K-020 |
| type | modele |
| titre | Modèle ONF-FFN — douglas |
| description | Modèle de croissance ONF-FFN pour le douglas : production 12 m³/ha/an sur sol profond, pH 4,5-6,5, précipitations > 800 mm. |
| evidence_level | B |
| source | ONF-FFN (2019), Modèles de croissance forestière française |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Dendrométrie et croissance |
| domaines_validite | Sols profonds, pH 4,5-6,5, précipitations > 800 mm, France |
| moteurs_consommateurs | Forest Dynamics, Simulation |
| relations | K-008 (pH), K-009 (croissance), K-010 (sol profond) |
| mots_cles | douglas, ONF-FFN, croissance, modèle |

### K-021 : Modèle de croissance ONF-FFN — chêne sessile

| Champ | Valeur |
|---|---|
| connaissance_id | K-021 |
| type | modele |
| titre | Modèle ONF-FFN — chêne sessile |
| description | Modèle de croissance ONF-FFN pour le chêne sessile : production 6 m³/ha/an en futaie régulière. |
| evidence_level | B |
| source | ONF-FFN (2019), Modèles de croissance forestière française |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Dendrométrie et croissance |
| domaines_validite | pH 4,5-6,5, France métropolitaine, futaie régulière |
| moteurs_consommateurs | Forest Dynamics, Simulation |
| relations | K-001 (concept), K-002 (pH), K-003 (précipitations) |
| mots_cles | chêne sessile, ONF-FFN, croissance, modèle |

### K-022 : Modèle de croissance ONF-FFN — hêtre

| Champ | Valeur |
|---|---|
| connaissance_id | K-022 |
| type | modele |
| titre | Modèle ONF-FFN — hêtre |
| description | Modèle de croissance ONF-FFN pour le hêtre : production 7 m³/ha/an en futaie régulière, RUM ≥ 80 mm. |
| evidence_level | B |
| source | ONF-FFN (2019), Modèles de croissance forestière française |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Dendrométrie et croissance |
| domaines_validite | RUM ≥ 80 mm, climat atlantique, France métropolitaine |
| moteurs_consommateurs | Forest Dynamics, Simulation |
| relations | K-005 (RUM), K-006 (vulnérabilité), K-007 (climat atlantique) |
| mots_cles | hêtre, ONF-FFN, croissance, modèle |

---

## 11. Classifications taxonomiques

### K-023 : Classification Quercus petraea

| Champ | Valeur |
|---|---|
| connaissance_id | K-023 |
| type | classification |
| titre | Quercus petraea (chêne sessile) |
| description | Classification taxonomique du chêne sessile : Fagaceae, Quercus, petraea. |
| evidence_level | A |
| source | GBIF — Backbone Taxonomy (2024) + BDNFF (2023) |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Botanique et taxonomie |
| domaines_validite | Monde (taxonomie globale) |
| moteurs_consommateurs | Botanical, GIS |
| relations | K-001 (concept), K-002 (pH), K-003 (précipitations) |
| mots_cles | Quercus petraea, chêne sessile, taxonomie, GBIF |

### K-024 : Classification Fagus sylvatica

| Champ | Valeur |
|---|---|
| connaissance_id | K-024 |
| type | classification |
| titre | Fagus sylvatica (hêtre) |
| description | Classification taxonomique du hêtre : Fagaceae, Fagus, sylvatica. |
| evidence_level | A |
| source | GBIF — Backbone Taxonomy (2024) + BDNFF (2023) |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Botanique et taxonomie |
| domaines_validite | Monde (taxonomie globale) |
| moteurs_consommateurs | Botanical, GIS |
| relations | K-005 (RUM), K-006 (vulnérabilité), K-007 (climat) |
| mots_cles | Fagus sylvatica, hêtre, taxonomie, GBIF |

### K-025 : Classification Pseudotsuga menziesii

| Champ | Valeur |
|---|---|
| connaissance_id | K-025 |
| type | classification |
| titre | Pseudotsuga menziesii (douglas) |
| description | Classification taxonomique du douglas : Pinaceae, Pseudotsuga, menziesii. Espèce introduite d'Amérique du Nord. |
| evidence_level | A |
| source | GBIF — Backbone Taxonomy (2024) + BDNFF (2023) |
| version | 1 |
| date_integration | 2026-07-13 |
| domaine_scientifique | Botanique et taxonomie |
| domaines_validite | Monde (taxonomie globale) |
| moteurs_consommateurs | Botanical, GIS |
| relations | K-008 (pH), K-009 (croissance), K-010 (sol profond) |
| mots_cles | Pseudotsuga menziesii, douglas, taxonomie, GBIF |

---

## 12. Tableau récapitulatif

| ID | Type | Titre | Evidence | Source | Domaine |
|---|---|---|---|---|---|
| K-001 | concept | Autécologie du chêne sessile | A | Rameau 2008 | Écologie |
| K-002 | seuil | pH optimal chêne sessile | B | Rameau 2008 | Écologie |
| K-003 | seuil | Précipitations chêne sessile | B | Rameau 2008 | Climat |
| K-004 | relation | Chêne sessile → sol acide | B | Rameau 2008 | Écologie |
| K-005 | seuil | RUM minimale hêtre | B | Rameau 2008 | Écologie |
| K-006 | seuil | Vulnérabilité hêtre déficit hydrique | C | INRAE 2004 | Climat |
| K-007 | relation | Hêtre → climat atlantique | B | Rameau 2008 | Climat |
| K-008 | seuil | pH optimal douglas | B | ONF 2019 | Écologie |
| K-009 | modele | Croissance douglas 12 m³/ha/an | B | ONF-FFN 2019 | Dendrométrie |
| K-010 | relation | Douglas → sol profond | B | ONF 2019 | Écologie |
| K-011 | seuil | Précipitations sapin pectiné | B | Rameau 2008 | Climat |
| K-012 | seuil | Gel sapin pectiné -20°C | C | INRAE 2015 | Climat |
| K-013 | seuil | Tolérance pH pin sylvestre | B | Rameau 2008 | Écologie |
| K-014 | relation | Pin sylvestre → sol pauvre | B | Rameau 2008 | Écologie |
| K-015 | classification | Classes RUM | B | RPF INRAE | Pédologie |
| K-016 | classification | Classes pH forestier | B | RPF INRAE | Pédologie |
| K-017 | seuil | Profondeur sol minimale 40 cm | B | RPF INRAE | Pédologie |
| K-018 | classification | Alocrisol (RPF) | B | RPF INRAE | Pédologie |
| K-019 | classification | Brunisol (RPF) | B | RPF INRAE | Pédologie |
| K-020 | modele | ONF-FFN douglas | B | ONF-FFN 2019 | Dendrométrie |
| K-021 | modele | ONF-FFN chêne sessile | B | ONF-FFN 2019 | Dendrométrie |
| K-022 | modele | ONF-FFN hêtre | B | ONF-FFN 2019 | Dendrométrie |
| K-023 | classification | Quercus petraea | A | GBIF + BDNFF | Botanique |
| K-024 | classification | Fagus sylvatica | A | GBIF + BDNFF | Botanique |
| K-025 | classification | Pseudotsuga menziesii | A | GBIF + BDNFF | Botanique |

**Total** : 25 connaissances validées.

### Répartition par type

| Type | Nombre |
|---|---|
| concept | 1 |
| relation | 4 |
| seuil | 8 |
| modele | 4 |
| classification | 8 |

### Répartition par niveau de preuve

| Niveau | Nombre |
|---|---|
| A (Prouvé) | 4 |
| B (Établi) | 19 |
| C (Probable) | 2 |

### Répartition par domaine scientifique

| Domaine | Nombre |
|---|---|
| Écologie forestière et stationnelle | 11 |
| Climatologie et bioclimatologie | 5 |
| Pédologie | 5 |
| Dendrométrie et croissance | 4 |
| Botanique et taxonomie | 3 |

---

## 13. Sources utilisées

| Source | Type | Niveau moyen | Nb connaissances |
|---|---|---|---|
| Rameau et al. (2008) — Flore forestière française | Ouvrage | B | 10 |
| ONF — Guide de sylviculture du douglas (2019) | Document technique | B | 3 |
| ONF-FFN (2019) — Modèles de croissance | Référentiel | B | 3 |
| RPF INRAE — Baize & Jabiol (2008) | Référentiel | B | 5 |
| GBIF + BDNFF | Référentiel | A | 3 |
| INRAE — Badeau et al. (2004) | Peer-reviewed | C | 1 |
| INRAE — Données provenances (2015) | Peer-reviewed | C | 1 |

---

## 14. Conformité constitutionnelle

| Article | Conformité | Vérification |
|---|---|---|
| S-1 (Sources acceptées) | Oui | Toutes les sources sont peer-reviewed, référentiel officiel ou document technique |
| S-2 (Niveaux de preuve) | Oui | Chaque connaissance porte un `evidence_level` |
| S-3 (Conflits) | Oui | Conflit K-012 documenté (§8) |
| S-5 (Incertitude) | Oui | Domaines de validité explicites pour chaque connaissance |
| S-7 (Patrimoine) | Oui | Toutes les connaissances sont versionnées (version 1) |
| CON-002 (Sourçage) | Oui | Aucune connaissance sans source |
| CON-003 (Connaissance avant code) | Oui | Documentation uniquement, pas de code |
| CON-010 (Historique) | Oui | Version 1, historique initialisé |

---

## 15. Historique

| Date | Événement |
|---|---|
| 2026-07-13 | Création — Phase 3, 25 connaissances initiales (5 essences + pédologie + croissance + taxonomie) |

---

> Statut : *Draft — Phase 3 (Connaissance). Documentation uniquement,
> aucune implémentation (Phase 4).*
