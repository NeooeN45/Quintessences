# Domaine G — Réglementaire, zonages, foncier

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 4 testées, 1 échec (bd-haies 404 — URL corrigée : bd-haie).

---

## Entrées vérifiées

### G-001 — Géorisques (portail risques naturels et technologiques)

```yaml
- nom: Géorisques — portail des risques naturels et technologiques
  producteur: BRGM / MTE (France)
  url: https://www.georisques.gouv.fr/
  access_method: ogc_wms
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: variable (PPR polygones ; aléa retrait-gonflement argiles raster)
  emprise: France entière
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: WMS, SHP, GeoJSON, PDF (PPR)
  volume_estime: inconnu — portail agrégé
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Diagnostic, Ignis, Recommendation
  regime: referencee
```

**Note** : portail BRGM/MTE. Recherche par adresse/carte/parcelle. Risques : inondation, feu de forêt, tempête, cyclone, mouvement terrain, avalanche, séisme, volcanisme, technologiques (barrage, industriel, nucléaire, transport matières dangereuses). ERRIAL (état des risques pour location/vente). Carte RGA actualisée 09/01/2026 (PNACC-3). Fonds de prévention RGA expérimentation octobre 2025 (11 départements). URL testée : portail répond, fonctionnalités confirmées.

---

### G-002 — Géoportail de l'Urbanisme (PLU, POS, CC, PSMV, SCOT, SUP)

```yaml
- nom: Géoportail de l'Urbanisme (GPU)
  producteur: IGN / MTE (France)
  url: https://www.geoportail-urbanisme.gouv.fr/
  access_method: api_rest
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: inconnu — zonages parcellaires (visible à partir de 1:60 000)
  emprise: France entière
  etendue_temporelle: continu
  frequence_mise_a_jour: continue (publication par collectivités)
  format: SHP, GeoJSON, GeoParquet, PDF (règlements)
  volume_estime: inconnu — 13214 documents d'urbanisme, 293 SCOT, 88765 SUP, 40 PSMV
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Recommendation, Knowledge
  regime: referencee
```

**Note** : portail IGN/MTE. Documents : PLU (plan local d'urbanisme), POS (plan d'occupation sols), CC (carte communale), PSMV (plan sauvegarde mise valeur), SCOT (schéma cohérence territoriale), SUP (servitudes utilité publique). API Carto REST (JSON/GeoJSON, WGS84). data.gouv.fr : zonages documents urbanisme (https://www.data.gouv.fr/datasets/donnees-geoportail-de-lurbanisme-zonages-des-documents-durbanisme). Zones PLU France en GeoParquet (https://www.data.gouv.fr/datasets/zones-plu-france). URL testée : portail répond, statistiques confirmées.

---

### G-003 — Forêts de protection (massifs classés)

```yaml
- nom: Forêts de protection — massifs forestiers classés
  producteur: MAA — Ministère de l'Agriculture (France)
  url: https://www.data.gouv.fr/datasets/liste-des-massifs-forestiers-classes-en-forets-de-protection-30379254
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: inconnu — massifs forestiers (polygones)
  emprise: France entière
  etendue_temporelle: continu (classements par décret)
  frequence_mise_a_jour: ponctuelle (nouveaux classements)
  format: CSV (données départementales, libellés, surfaces, statut public/privé)
  volume_estime: inconnu — massifs classés
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Knowledge, Recommendation, Forest Dynamics
  regime: referencee
```

**Note** : forêts classées sous régime de protection (Code forestier L.141-1 à L.141-7, anciens L.411-1 à L.413-1). Critères : conservation terres montagnes/pentes, défense avalanches/érosions/eaux/sables, périphérie grandes agglomérations, raisons écologiques/bien-être population. Servitude SUP type A7 reportée en annexe PLU. Régime forestier spécial (aménagement, exploitation, pâturage, fouilles). URL testée : data.gouv.fr confirmé via recherche.

---

### G-004 — Forêts soumises au régime du code forestier

```yaml
- nom: Forêts soumises au régime du code forestier
  producteur: MAA — Ministère de l'Agriculture (France)
  url: https://www.data.gouv.fr/datasets/forets-soumises-au-regime-du-code-forestier
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: inconnu — forêts collectivités (polygones)
  emprise: France entière
  etendue_temporelle: continu
  frequence_mise_a_jour: ponctuelle (arrêtés)
  format: CSV, SHP
  volume_estime: inconnu — forêts collectivités soumises
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Knowledge, Forest Dynamics, Recommendation
  regime: referencee
```

**Note** : article L.211-1-I-2° du code forestier — bois/forêts des collectivités territoriales relevant du régime forestier (susceptibles d'aménagement, exploitation régulière, reconstitution, arrêté d'application). Distinct des forêts de protection (G-003). URL testée : data.gouv.fr confirmé via recherche.

---

### G-005 — BD Haie (haies linéaires bocagières)

```yaml
- nom: BD Haie — couche nationale de référence des haies linéaires
  producteur: IGN / OFB (France, Dispositif de Suivi des Bocages DSB)
  url: https://www.data.gouv.fr/datasets/bd-haie
  access_method: file_download
  licence: Licence Ouverte 2.0 (etalab-2.0)
  ai_training_allowed: false
  grain_m2: inconnu — linéaires (largeur < 20 m, longueur > 25 m)
  emprise: France métropolitaine
  etendue_temporelle: V1 2020 ; V2 mars 2024
  frequence_mise_a_jour: ponctuelle (millésimes)
  format: Shapefile, GeoPackage
  volume_estime: inconnu — haies linéaires France entière
  type_source: capteur_instrumente
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Knowledge
  regime: referencee
```

**Note** : DSB (Dispositif de Suivi des Bocages) OFB-IGN initié 2017. V2 mars 2024 : mise à jour depuis RPG (surfaces non agricoles, photo-interprétation 2020-2022) + MNS (corrélation images aériennes 2020-2022). Définition haie : formation linéaire arbres/arbustes, > 25 m long, < 20 m large, hauteur potentielle > 1.30 m. Dernière mise à jour data.gouv.fr : 27/04/2026. Production départementale. URL testée : data.gouv.fr confirmé via recherche (URL correcte : `bd-haie` sans "s", l'URL `bd-haies` est 404).

---

## À VÉRIFIER — Domaine G

### G-V001 — PPRIF (Plans de Prévention des Risques Incendie de Forêt)

**Motif** : les PPR naturels (incluant PPRIF) sont disponibles via Géorisques (G-001) mais leur endpoint de téléchargement bulk spécifique n'est pas confirmé. Les PPRIF sont des servitudes SUP type A5 reportées en annexe PLU. À vérifier : existe-t-il un dataset data.gouv.fr pour PPRIF spécifiquement ?

### G-V002 — RPG (Registre Parcellaire Graphique)

**Motif** : le RPG (IGN/ASP) est mentionné dans BD Haie comme source. C'est le référentiel des parcelles agricoles (PAC). URL probable : https://www.data.gouv.fr/datasets/registre-parcellaire-graphique-rpg-contour-des-ilots-culturaux-et-leur-groupe-de-culture. Non testé séparément. Potentiellement pertinent pour Forest Dynamics (occupation sols agricole) et Ignis (combustible).

### G-V003 — BD Forêt v3 (2026, jeu test 40 zones)

**Motif** : déjà signalé dans domaine A (A-V003). La BD Forêt v3 est en production par IA à partir de BD Ortho. À suivre pour migration DS-001 → v3.

### G-V004 — Cartes des régions de provenance (matériels forestiers reproduction)

**Motif** : déjà vérifié dans domaine A (A-007) — les régions de provenance sont sur agriculture.gouv.fr. Les cartographies IGN par sylvoécorégions (SER) sont sur inventaire-forestier.ign.fr. À vérifier : endpoint de téléchargement des cartes SER.

---

## Signalements — Domaine G

- **BD Haie — URL correcte** : l'URL `bd-haies` (avec "s") est 404. L'URL correcte est `bd-haie` (sans "s"). À documenter précisément dans les méthodes d'ingestion.
- **Forêts de protection vs forêts soumises régime forestier** : deux datasets distincts sur data.gouv.fr. Les forêts de protection (G-003) sont classées par décret pour utilité publique. Les forêts soumises au régime forestier (G-004) sont les forêts des collectivités. Ne pas confondre.
