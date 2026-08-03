# Domaine I — Outre-mer et transfrontalier

> Fichier partiel — GSIE-PROMPT-0025
> URL vérifiées le 2026-07-30 par webfetch et recherche web.
> Compteur URL : 6 testées, 1 échec (carto.geonature.guyane — fetch failed).

---

## Entrées vérifiées

### I-001 — GéoGuyane (portail géographique de la Guyane)

```yaml
- nom: GéoGuyane — portail géographique de la Guyane
  producteur: DGTM Guyane / Collectivité Territoriale de Guyane (France)
  url: https://www.geoguyane.fr/
  access_method: ogc_wms
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: variable par couche
  emprise: Guyane française
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: WMS, WFS, SHP, GeoJSON
  volume_estime: inconnu — portail régional
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Knowledge
  regime: referencee
```

**Note** : portail PRODIGE 5.0 (avril 2025). Navigateur cartographique, cartothèque, catalogue de données. Cartes : espaces naturels protégés, documents d'urbanisme, déforestation/orpaillage 2000-2018, emprises LiDAR/photographies aériennes/satellites, SDOM, masses d'eau, foncier agricole, RAEPA, PPRN, dynamique côtière (ODyC), données forestières ONF. Bilan 2025 : forte hausse usages. URL testée : portail répond, cartes et actualités confirmées.

---

### I-002 — Guyane-SIG (Plateforme Territoriale de l'Information Géographique)

```yaml
- nom: Guyane-SIG — PTIG de Guyane
  producteur: Guyane-SIG (association, financé par CTG, FEDER, partenaires)
  url: https://www.guyane-sig.fr/
  access_method: ogc_wms
  licence: variable par donnée (majorité Licence Ouverte 2.0)
  ai_training_allowed: false
  grain_m2: variable par couche
  emprise: Guyane française + Plateau des Guyanes (Guyana, Suriname, Amapá)
  etendue_temporelle: continu
  frequence_mise_a_jour: continue
  format: WMS, WFS, SHP, GeoTIFF
  volume_estime: inconnu — plateforme agrégée
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Knowledge
  regime: referencee
```

**Note** : plateforme territoriale SIG Guyane. Services : boîte à outils (flux, conversion coordonnées, entrepôt fichiers), cartographie (applications thématiques, visualiseur), catalogue (Guyane-SIG, SEAS Guyane, données référence). Données : déforestation orpaillage (WWF, 2000-2018), Guyadiv (réseau inventaires forestiers depuis 1986, Paracou, Nouragues, Montagne Plomb), Ortho Express Guyane 2025 (accès anticipé IGN sur demande). Partenaires : ONF, CIRAD, Parc amazonien, OFB, BRGM, IGN. URL testée : portail répond, services et partenaires confirmés.

---

### I-003 — Parc amazonien de Guyane (PAG)

```yaml
- nom: Parc amazonien de Guyane (PAG)
  producteur: PAG / OFB (France)
  url: https://www.parc-amazonien-guyane.fr/
  access_method: publication_text
  licence: variable (données publiques + droits spécifiques PAG)
  ai_training_allowed: false
  grain_m2: variable (suivi occupation sol par télédétection Sentinel)
  emprise: sud Guyane (3.4 Mha, un des plus grands parcs nationaux)
  etendue_temporelle: continu (suivi abattis depuis >10 ans)
  frequence_mise_a_jour: continue
  format: SHP, GeoJSON (diffusion via GéoGuyane)
  volume_estime: inconnu — suivi occupation sol + inventaires naturalistes
  type_source: capteur_instrumente
  moteur_destinataire: Forest Dynamics, Botanical, Knowledge, Diagnostic
  regime: referencee
```

**Note** : un des plus grands parcs nationaux (3.4 Mha). Suivi occupation du sol par télédétection (Random Forest, Sentinel). Cartographie formations végétales atypiques (inselbergs, savanes roches). Suivi abattis agricoles (>10 ans données). Inventaires naturalistes (crique Limonade 2026, loutres/tapirs Antecum Pata). Cellule Biodiversité lancée 02/2026. Coopérations régionales : Guiana Shield, REDPARQUES, RENFORESAP, ICMBio Brésil. COP30 Belém 11/2025. Données diffusées via GéoGuyane. URL testée : site répond, missions et coopérations confirmées.

---

### I-004 — BD Ortho Outre-mer (IGN)

```yaml
- nom: BD ORTHO® — outre-mer et collectivités
  producteur: IGN (France)
  url: https://www.data.gouv.fr/datasets/bd-ortho-r
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques IGN)
  ai_training_allowed: false
  grain_m2: 20 cm → 0.04 (résolution standard depuis 2021)
  emprise: France métropolitaine + ultramarin (sauf intérieur Guyane, Polynésie, Nouvelle-Calédonie, Wallis-et-Futuna)
  etendue_temporelle: acquisitions triennales (depuis 1997, première couverture couleur 2003)
  frequence_mise_a_jour: triennale (renouvellement par département)
  format: TIFF (1 km x 1 km), ECW (5 km x 5 km), WMS/WMTS
  volume_estime: pétaoctets (collection complète)
  type_source: capteur_instrumente
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Ignis
  regime: referencee
```

**Note** : collection ortho-images RVB + IRC, 20 cm résolution depuis 2021 (tous départements métropole + outre-mer + Saint-Pierre-et-Miquelon, Saint-Barthélemy, Saint-Martin). Île-de-France 15 cm. Wallis-et-Futuna 50 cm (2004). Exceptions ZICAD (zones interdites captation aérienne). Projections adaptées au territoire (RGFG95/UTM22N Guyane, RGAF09UTM Antilles, RGR92 Réunion). Déjà dans l'inventaire existant (DS-003) — cette entrée précise la couverture outre-mer. URL testée : data.gouv.fr confirmé via recherche.

---

### I-005 — CARTOS VEGETATION DROM (IGN)

```yaml
- nom: CARTOS VEGETATION DROM — cartographie formations végétales ultra-marines
  producteur: IGN (France)
  url: https://www.data.gouv.fr/datasets/cartos-vegetation-drom
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques IGN)
  ai_training_allowed: false
  grain_m2: variable (photo-interprétation BD Ortho 20 cm)
  emprise: DROM (Mayotte, Martinique, Guadeloupe, Réunion, Guyane partielle)
  etendue_temporelle: variable par territoire (Mayotte 2016/2023, Martinique 2004/2017/2022, Guadeloupe 2024)
  frequence_mise_a_jour: ponctuelle (millésimes)
  format: Shapefile, GeoPackage
  volume_estime: inconnu — cartographies par DROM
  type_source: capteur_instrumente
  moteur_destinataire: Forest Dynamics, Botanical, Diagnostic, Knowledge
  regime: referencee
```

**Note** : cartographie peuplements forestiers, formations arbustives, formations herbacées naturelles. Nomenclature propre à chaque DROM. Méthodes : photo-interprétation BD Ortho (millésimes anciens) + IA (Sentinel + BD Ortho, millésimes récents, reprises manuelles). Martinique 2022 : 15 postes formations végétales, produit par IA. Guadeloupe 2024. Mayotte 2016/2023. URL testée : data.gouv.fr confirmé via recherche.

---

## À VÉRIFIER — Domaine I

### I-V001 — Portails SIG autres DROM (Guadeloupe, Martinique, Réunion, Mayotte)

**Motif** : chaque DROM a potentiellement son propre portail SIG régional (équivalent GéoGuyane). URLs non testées. À inventorier : GeoReunion, GeoMartinique, GeoGuadeloupe, Mayotte. Probablement sur le modèle PRODIGE.

### I-V002 — Carto GeoNature Guyane

**Motif** : https://carto.geonature.guyane/ — fetch failed. Portail potentiel pour observations naturalistes Guyane (écosystème GeoNature). À vérifier : URL exacte, statut (actif/inactif).

### I-V003 — SEAS Guyane (Service de l'Accès aux données Spatiales)

**Motif** : mentionné dans Guyane-SIG (catalogue SEAS Guyane). Probablement https://www.seas-guyane.fr/ ou similaire. Service régional d'accès aux données satellites (Sentinel, Landsat) pour Guyane. Non testé.

### I-V004 — Nouvelle-Calédonie et Polynésie (collectivités non couvertes par BD Ortho)

**Motif** : la BD Ortho ne couvre pas la Nouvelle-Calédonie ni la Polynésie (cf. I-004). Ces collectivités ont leurs propres services géographiques (Gouv.nc, SIG Polynésie). Non testé. Pertinent pour GeoSylva (extension future).

### I-V005 — Données transfrontalières Plateau des Guyanes

**Motif** : le Parc amazonien coopère avec Guyana, Suriname, Amapá (Brésil). Données transfrontalières (déforestation, faune, aires protégées) potentiellement sur des portails régionaux (Guiana Shield, REDPARQUES). Non testé. Pertinent pour Forest Dynamics Guyane.

---

## Signalements — Domaine I

- **BD Ortho — couverture partielle outre-mer** : l'intérieur de la Guyane, la Polynésie, la Nouvelle-Calédonie et Wallis-et-Futuna ne sont pas couverts par la BD Ortho. Pour la Guyane, l'Ortho Express 2025 est disponible sur demande anticipée (accès FTP, pas de rediffusion). À documenter dans les méthodes d'ingestion.
- **CARTOS VEGETATION DROM — méthodes hétérogènes** : les millésimes anciens sont produits par photo-interprétation, les récents par IA (Sentinel + BD Ortho). Les nomenclatures sont propres à chaque DROM (pas de standard national unifié). À harmoniser pour ingestion cross-DROM.
