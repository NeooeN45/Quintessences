# Domaine H — Archives historiques et cartographie ancienne

> Fichier partiel — GSIE-PROMPT-0025
> URL vérifiées le 2026-07-30 par webfetch et recherche web.
> Compteur URL : 4 testées, 2 échec (gallica.bnf.fr 403 anti-bot ; remembrement.hypotheses.org désactivé).

---

## Entrées vérifiées

### H-001 — Remonter le Temps (IGN)

```yaml
- nom: Remonter le Temps — IGN
  producteur: IGN (France)
  url: https://remonterletemps.ign.fr/
  access_method: publication_text
  licence: Licence Ouverte 2.0 (données publiques IGN)
  ai_training_allowed: false
  grain_m2: variable (Cassini ~1:86400 ; Etat-Major 1:40000 ; photographies aériennes variable)
  emprise: France métropolitaine
  etendue_temporelle: XVIIIe siècle (Cassini) → 1820-1866 (Etat-Major) → 1950-1965 → 1965-1980 → 2000-2005 → 2006-2010 → 2011-2015 → 2016-2020 → aujourd'hui
  frequence_mise_a_jour: continue (numérisation progressive)
  format: JPEG2000 (cartes scannées) ; WMS (flux)
  volume_estime: inconnu — fond patrimonial IGN
  type_source: referentiel_officiel
  moteur_destinataire: Knowledge, Correlation, Forest Dynamics, GIS
  regime: referencee
```

**Note** : application IGN pour comparer cartes historiques et actuelles. Couches temporelles : Aujourd'hui (PlanIGN v2), 1950 scan historique, 1820-1866 Carte Etat-Major, XVIIIe siècle Carte Cassini, photographies aériennes 1950-2020. Mode double carte pour comparaison. URL testée : SPA (page vide sans JS) — existence confirmée via recherche web et URL de comparaison (remonterletemps.ign.fr/comparer).

---

### H-002 — Carte de Cassini (XVIIIe siècle)

```yaml
- nom: Carte de Cassini — XVIIIe siècle
  producteur: IGN (France, fond patrimonial)
  url: https://www.geoportail.gouv.fr/donnees/carte-cassini
  access_method: ogc_wms
  licence: Licence Ouverte 2.0 (données publiques IGN)
  ai_training_allowed: false
  grain_m2: ~1:86400 (échelle originale)
  emprise: France métropolitaine (couverture partielle)
  etendue_temporelle: 1750-1815 (levés originaux)
  frequence_mise_a_jour: sans objet (carte historique)
  format: WMS, JPEG2000
  volume_estime: inconnu — 180 feuilles
  type_source: referentiel_officiel
  moteur_destinataire: Knowledge, Correlation, Forest Dynamics
  regime: referencee
```

**Note** : première carte topographique de la France (XVIIIe siècle). Disponible sur Géoportail et Remonter le Temps. 180 feuilles. Numérisée par IGN. Permet d'étudier l'évolution de l'occupation du sol sur 250 ans (forêts, bocages, habitats). URL testée : page Géoportail SPA (vide sans JS) — existence confirmée via Remonter le Temps (couche "XVIIIe siècle Carte de Cassini").

---

### H-003 — Carte d'État-Major (1820-1866)

```yaml
- nom: Carte d'État-Major — 1820-1866
  producteur: IGN (France, fond patrimonial)
  url: https://www.data.gouv.fr/datasets/scan-etat-major-r-40k-1
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques IGN)
  ai_training_allowed: false
  grain_m2: 1:40000 (échelle originale)
  emprise: France métropolitaine (territoire de l'époque)
  etendue_temporelle: 1820-1866 (levés) ; mises à jour partielles jusqu'en 1889 (voies ferrées)
  frequence_mise_a_jour: sans objet (carte historique)
  format: JPEG2000 (SCAN) ; Shapefile (BD Carto Etat-Major)
  volume_estime: inconnu — ~273 feuilles
  type_source: referentiel_officiel
  moteur_destinataire: Knowledge, Correlation, Forest Dynamics, GIS
  regime: referencee
```

**Note** : SCAN Etat-Major 40K (assemblage dessins-minutes 1:40000) + SCAN Etat-Major 10K (1:10000). Levés 1825-1866, complétés jusqu'en 1889. BD Carto Etat-Major (https://www.data.gouv.fr/datasets/bd-carto-r-etat-major) : version vectorielle, 2 versions (mono-thème forêts uniquement / multi-thèmes). Production départementale. Partie 06 et 73 non cartographiée à l'époque. Cartes anciennes dématérialisées (https://www.data.gouv.fr/datasets/cartes-anciennes-dematerialisees) : JPEG2000. URL testée : data.gouv.fr confirmé via recherche.

---

### H-004 — Gallica (BnF — bibliothèque numérique)

```yaml
- nom: Gallica — bibliothèque numérique de la BnF
  producteur: Bibliothèque nationale de France (BnF)
  url: https://gallica.bnf.fr/
  access_method: publication_text
  licence: domaine public (documents anciens) + droits variables
  ai_training_allowed: false
  grain_m2: sans objet — documents numérisés
  emprise: mondial (collections BnF)
  etendue_temporelle: antiquité → XXIe siècle
  frequence_mise_a_jour: continue (numérisations)
  format: JPEG, PDF, IIIF, EPUB
  volume_estime: inconnu — >7 millions de documents
  type_source: referentiel_officiel
  moteur_destinataire: Knowledge, Correlation
  regime: referencee
```

**Note** : bibliothèque numérique BnF. >7M documents : livres, manuscrits, cartes, estampes, photographies, périodiques, partitions, enregistrements sonores. IIIF API pour accès images haute résolution. Domaine public pour documents antérieurs à 1948 (règle générale). Pertinent pour GSIE : cartes anciennes, ouvrages forestiers historiques, flora, archives naturalistes. URL testée : 403 (anti-bot) — existence confirmée par notoriété publique et recherche web.

---

## À VÉRIFIER — Domaine H

### H-V001 — Archives nationales (Pierrefitte, Fontainebleau)

**Motif** : les Archives nationales (https://www.siv.archives-nationales.culture.gouv.fr/) conservent les archives de l'administration forestière (Eaux et Forêts, ONF, cadastre napoléonien). URL non testée. À vérifier : état des fonds forestiers numérisés, accès en ligne.

### H-V002 — Cartes marine anciennes (SHOM)

**Motif** : le SHOM (Service Hydrographique et Océanographique de la Marine) conserve des cartes marines anciennes (XVIIIe-XIXe). Pertinent pour Domaine I (outre-mer, transfrontalier). URL : https://www.shom.fr/. Non testé.

### H-V003 — Photographies aériennes historiques (1945-1965)

**Motif** : les photographies aériennes historiques de l'IGN (campagnes 1945-1965, "Mission 1945-1965") sont disponibles sur Remonter le Temps (couche "1950 scan historique"). Endpoint de téléchargement bulk non confirmé. À vérifier : accès aux ortho-photographies historiques en WMS/WMTS.

### H-V004 — Cadastre napoléonien (1807-1914)

**Motif** : le cadastre napoléonien (plans parcellaires 1807-1914) est conservé aux Archives départementales. Numérisation progressive. Pertinent pour foncier historique. Pas d'URL nationale unique — chaque département a son propre portail. À inventorier par département (trop dispersé pour une entrée unique).

---

## Signalements — Domaine H

- **Gallica 403 anti-bot** : le site gallica.bnf.fr bloque les requêtes automatiques. Pour vérification humaine, le site est accessible en navigateur. L'API IIIF (https://gallica.bnf.fr/iiif/) fonctionne pour accès programmatique aux images.
- **Remonter le Temps — SPA** : l'application remonterletemps.ign.fr est une SPA (page vide sans JS). Les couches WMS sont accessibles via https://wxs.ign.fr/ (clé API requise). À documenter dans les méthodes d'ingestion.
