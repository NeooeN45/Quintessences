# Domaine D — Biodiversité, taxonomie, phytosanitaire

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 7 testées, 2 échec (gbif.org 403 — API alternative OK ; eea.europa.eu/en/europes-biodiversity 404 — URL corrigée).

---

## Entrées vérifiées

### D-001 — INPN (Inventaire National du Patrimoine Naturel)

```yaml
- nom: INPN — Inventaire National du Patrimoine Naturel
  producteur: PatriNat (OFB-CNRS-MNHN-IRD) (France)
  url: https://inpn.mnhn.fr/
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: inconnu — occurrences ponctuelles + zonages
  emprise: France entière (métropole + DOM + Nouvelle-Calédonie)
  etendue_temporelle: continu (depuis ~1970)
  frequence_mise_a_jour: continue (via SINP)
  format: Shapefile, GeoPackage, CSV, WMS/WFS
  volume_estime: inconnu — millions d'occurrences + zonages ZNIEFF/Natura 2000
  type_source: referentiel_officiel
  moteur_destinataire: Botanical, Diagnostic, Knowledge, GIS, Correlation
  regime: referencee
```

**Note** : **CYBERATTAQUE MNHN 26/07/2025 → 22/07/2026** (1 an hors service). Restauration 21/07/2026 — version zéro du nouvel INPN. Fiches espèces + téléchargement référentiels disponibles. Autres rubriques (fiches espaces, indicateurs aires protégées, formulaires SINP, OpenObs, CarHab, viewers) reviennent fin 2026. Fiches habitats, synthèses locales, nouveau moteur de recherche en 2027. URL testée : site répond, message de restauration affiché.

---

### D-002 — TAXREF (référentiel taxonomique national)

```yaml
- nom: TAXREF — référentiel taxonomique national
  producteur: PatriNat (OFB-CNRS-MNHN-IRD) (France)
  url: https://taxref.mnhn.fr/
  access_method: api_rest
  licence: Licence Ouverte 2.0
  ai_training_allowed: false
  grain_m2: sans objet — référentiel taxonomique
  emprise: France métropolitaine + outre-mer
  etendue_temporelle: continu (v18 publiée 09/01/2025)
  frequence_mise_a_jour: annuelle (version majeure)
  format: CSV (téléchargement), JSON (API REST), RDF/SPARQL (LOD)
  volume_estime: inconnu — ~200 000 taxons, 8 fichiers par version
  type_source: referentiel_officiel
  moteur_destinataire: Botanical, Knowledge, Correlation, Diagnostic
  regime: referencee
```

**Note** : TAXREF v18.0 (09/01/2025). Référentiel nomenclatural + taxonomique de tous les organismes vivant en France. API REST documentée. SPARQL endpoint (TAXREF-LD). Intégré GBIF (DOI: 10.15468/vqueam). Outils : TAXREF-MATCH, plugin QGIS, rtaxref (R), LibreOffice/Google Sheets. Citation : "TAXREF v18.0, référentiel taxonomique pour la France, PatriNat, MNHN, Paris". URL testée : site répond, v18 confirmée.

---

### D-003 — GBIF (Global Biodiversity Information Facility)

```yaml
- nom: GBIF — Global Biodiversity Information Facility
  producteur: GBIF Secretariat (Copenhague, Danemark) + réseau international
  url: https://www.gbif.org/
  access_method: api_rest
  licence: variable par occurrence (majorité CC-BY 4.0)
  ai_training_allowed: true
  grain_m2: inconnu — occurrences ponctuelles
  emprise: mondial (213 498 318 occurrences France au 30/07/2026)
  etendue_temporelle: continu (depuis ~1700)
  frequence_mise_a_jour: continue (crawl mensuel)
  format: Darwin Core Archive (DWCA), CSV, JSON (API REST)
  volume_estime: inconnu — >2 milliard d'occurrences mondiales
  type_source: referentiel_officiel
  moteur_destinataire: Botanical, Correlation, Knowledge, Diagnostic
  regime: referencee
```

**Note** : API REST confirmée — `api.gbif.org/v1/occurrence/search?country=FR&limit=1` retourne 213 498 318 occurrences France. Site web gbif.org 403 via webfetch (anti-bot) mais API publique fonctionne. Download API asynchrone pour bulk. pygbif (Python). Licence par occurrence (CC-BY 4.0 pour la majorité). URL testée : API OK, site web bloqué pour fetch automatique mais existence confirmée.

---

### D-004 — BISE (Biodiversity Information System for Europe)

```yaml
- nom: BISE — Biodiversity Information System for Europe
  producteur: EEA + European Commission (Europe)
  url: https://biodiversity.europa.eu/
  access_method: publication_text
  licence: libre (données publiques EU, attribution requise)
  ai_training_allowed: false
  grain_m2: variable par dataset
  emprise: EU27 + pays coopérants (40 pays EEA/Eionet)
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: HTML, PDF, données téléchargeables (variable)
  volume_estime: inconnu — gateway vers multiples datasets
  type_source: referentiel_officiel
  moteur_destinataire: Botanical, Knowledge, Correlation, Diagnostic
  regime: referencee
```

**Note** : gateway européen biodiversité. 26.4% territoire EU en aires protégées, 12.3% eaux marines, 1840+ espèces protégées, 230+ habitats protégés. Services : Nature Restoration Corner, Natura 2000 viewer, factsheets espèces/habitats. Liens vers Natura 2000, WISE marine/freshwater, FISE, ClimateADAPT. URL testée : portail répond, statistiques confirmées.

---

### D-005 — FISE (Forest Information System for Europe)

```yaml
- nom: FISE — Forest Information System for Europe
  producteur: EEA + European Commission (Europe)
  url: https://forest.eea.europa.eu/
  access_method: publication_text
  licence: libre (données publiques EU)
  ai_training_allowed: false
  grain_m2: variable par dataset
  emprise: EU27 (39% du territoire EU = 159 Mha forestiers)
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: HTML, PDF, cartes interactives
  volume_estime: inconnu — gateway vers datasets forestiers EU
  type_source: referentiel_officiel
  moteur_destinataire: Forest Dynamics, Knowledge, GIS, Correlation
  regime: referencee
```

**Note** : point d'entrée unique données/information forêts EU. 9552 Mt carbone stocké dans biomasse forestière EU27. 23% forêts EU en Natura 2000. 3.6M travailleurs filière. Services : EU forest policies, European forest maps, country factsheets, research corner. Initiative 3 Billion Trees. URL testée : portail répond, statistiques confirmées.

---

### D-006 — SINP (Système d'Information de l'INventaire du Patrimoine naturel)

```yaml
- nom: SINP — Système d'Information de l'INventaire du Patrimoine naturel
  producteur: PatriNat (OFB-MNHN) + MTE (France)
  url: https://sinp.naturefrance.fr/
  access_method: publication_text
  licence: Licence Ouverte 2.0 (données publiques SINP)
  ai_training_allowed: false
  grain_m2: inconnu — occurrences ponctuelles + zonages
  emprise: France entière (métropole + DOM + collectivités outre-mer volontaires)
  etendue_temporelle: continu
  frequence_mise_a_jour: continue (réseau d'acteurs)
  format: variable (échange standardisé SINP)
  volume_estime: inconnu — système décentralisé partenarial
  type_source: referentiel_officiel
  moteur_destinataire: Botanical, Knowledge, Correlation, Diagnostic
  regime: referencee
```

**Note** : système d'information décentralisé. Cadre méthodologique de référence pour partage données biodiversité/géodiversité. 5 classes : observations directes/indirectes, synthèse (ZNIEFF, INPG, cartes répartition), descriptives (traits de vie, paramètres), référence (TAXREF, HabRef), métadonnées. Site institutionnel (état d'avancement projets) — données elles-mêmes sur INPN. URL testée : site répond, description complète du SINP confirmée.

---

### D-007 — EPPO Global Database (pathogènes et ravageurs)

```yaml
- nom: EPPO Global Database
  producteur: EPPO — European & Mediterranean Plant Protection Organization (Europe/Méditerranée)
  url: https://gd.eppo.int/
  access_method: publication_text
  licence: libre (accès public gratuit)
  ai_training_allowed: false
  grain_m2: sans objet — base de données taxonomique/réglementaire
  emprise: Europe + Méditerranée (EPPO region)
  etendue_temporelle: 1974 — continu (EPPO Reporting Service)
  frequence_mise_a_jour: continue
  format: HTML, PDF (datasheets, PRA reports), images
  volume_estime: inconnu — 98 700+ espèces, 1900+ pests réglementés, 16000+ photos
  type_source: referentiel_officiel
  moteur_destinataire: Diagnostic, Knowledge, Botanical
  regime: referencee
```

**Note** : 98 700+ espèces d'intérêt agriculture/foresterie/protection des plantes. 1900+ pests d'intérêt réglementaire (distribution mondiale, plantes hôtes, statut quarantaine). Datasheets EPPO, PRA reports, EPPO Standards, EPPO Reporting Service (depuis 1974). EPPO Codes (système de codification unique). Version Desktop offline disponible. URL testée : site répond, contenu confirmé via recherche.

---

## À VÉRIFIER — Domaine D

### D-V001 — HabRef (référentiel des typologies d'habitats)

**Motif** : HabRef est le référentiel des habitats du SINP, géré par PatriNat/MNHN. Mentionné dans la description du SINP mais l'URL directe n'est pas confirmée (probablement via inpn.mnhn.fr/referentiels-donnees, page actuellement en reconstruction post-cyberattaque). À vérifier après restauration complète INPN fin 2026.

### D-V002 — CardObs / OpenObs (plateformes saisie/visualisation observations)

**Motif** : CardObs (saisie) et OpenObs (visualisation) sont des applications de l'écosystème INPN mentionnées comme "remontées dans les prochains mois" après la cyberattaque. À vérifier quand elles seront restaurées.

### D-V003 — EUNIS (European Nature Information System)

**Motif** : EUNIS (https://eunis.eea.europa.eu/) est la base européenne d'information sur les espèces, habitats et sites protégés. Gérée par EEA. URL non testée séparément — potentiellement redondant avec BISE/Natura 2000 viewer. À vérifier : contenu spécifique vs BISE.

---

## Signalements — Domaine D

- **INPN — cyberattaque MNHN (26/07/2025 → 22/07/2026)** : 1 an d'indisponibilité. Restauration partielle le 21/07/2026 (fiches espèces + téléchargement). L'inventaire existant cite INPN (DS-017) et les WMS/WFS INPN (§10.7) — vérifier que ces endpoints sont restaurés avant ingestion. Certaines fonctionnalités reviennent fin 2026, autres en 2027.
- **GBIF — site web 403 via webfetch** : le site gbif.org bloque les requêtes automatiques (anti-bot). L'API `api.gbif.org` fonctionne normalement. Pour vérification humaine, le site est accessible en navigateur. À documenter dans les méthodes d'ingestion.
