# Domaine C — Sols, géologie, hydrologie

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 4 testées, 0 échec.

---

## Entrées vérifiées

### C-001 — Hub'Eau (APIs REST données eau)

```yaml
- nom: Hub'Eau — APIs REST sur les données de l'eau
  producteur: OFB + BRGM (France, pôle INSIDE)
  url: https://hubeau.eaufrance.fr/
  access_method: api_rest
  licence: Licence Ouverte 2.0 (données publiques eau)
  ai_training_allowed: false
  grain_m2: inconnu — données ponctuelles (stations, points prélèvement)
  emprise: France entière (métropole + DOM)
  etendue_temporelle: variable par API (depuis ~1970 pour hydrométrie)
  frequence_mise_a_jour: continue (temps réel pour certaines APIs)
  format: CSV, JSON, GeoJSON
  volume_estime: inconnu — 13 APIs, milliards d'observations cumulées
  type_source: referentiel_officiel
  moteur_destinataire: Hydro, GIS, Diagnostic, Knowledge, Correlation
  regime: referencee
```

**Note** : 13 APIs REST — Vente/achat PPP (BNV-D), Écoulement cours d'eau (350k obs), Qualité eau potable (120M analyses), Surveillance eaux littorales (600k contaminants), Hydrobiologie (11M obs), Prélèvements eau (1.1M volumes), Hydrométrie, Température cours d'eau, Qualité cours d'eau, Qualité nappes, Piézométrie, Indicateurs services (décommissionnement 10/09/2026), Poisson. URL testée : portail répond, liste APIs et actualités confirmées.

---

### C-002 — HydroPortail (hydrométrie quantitative)

```yaml
- nom: HydroPortail — données hydrométriques publiques
  producteur: MTE / OFB / partenaires bassins (France)
  url: https://www.hydro.eaufrance.fr/
  access_method: file_download
  licence: Licence Ouverte 2.0
  ai_training_allowed: false
  grain_m2: inconnu — stations hydrométriques ponctuelles
  emprise: France entière (7 bassins métropole + 5 DOM)
  etendue_temporelle: ~1850 — continu (selon station)
  frequence_mise_a_jour: continue (temps réel Vigicrues) + archives
  format: CSV, XML (exports séries mesures)
  volume_estime: inconnu — ~3500 stations, séries pluridécennales
  type_source: capteur_instrumente
  moteur_destinataire: Hydro, GIS, Simulation, Forest Dynamics
  regime: referencee
```

**Note** : HydroPortail v3.5.4 (19 mai 2026). Accès gratuit aux données quantitatives écoulement cours d'eau. Fonctionnalités : référentiel (zones hydro, entités), cartes hydrologiques (toutes/basses/hautes eaux), comparateur, exports séries hydrométriques + météo. Liens : Vigicrues, Sandre, Hub'Eau, Groupe Doppler Hydrométrie. type_source = `capteur_instrumente` (proposé RFC-0029 §11.3) : stations calibrées, chaîne de mesure connue. URL testée : portail répond, version et fonctionnalités confirmées.

---

### C-003 — GIS Sol (système d'information sur les sols de France)

```yaml
- nom: GIS Sol — Groupement d'Intérêt Scientifique Sol
  producteur: INRAE / ADEME / MTE / MAA (France, consortium GIS Sol)
  url: https://www.gissol.fr/
  access_method: ogc_wms
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: variable (canton pour BDAT ; placette pour RMQS ; 1/100000 pour cartes)
  emprise: France métropolitaine (+ DOM partiels)
  etendue_temporelle: 1990 — continu (selon base)
  frequence_mise_a_jour: variable (BDAT décennale, RMQS annuelle)
  format: Shapefile, GeoJSON, WMS/WFS (webservices)
  volume_estime: inconnu — BDAT + RMQS + Geosol + Refersols
  type_source: referentiel_officiel
  moteur_destinataire: Pedology, Diagnostic, Correlation, Knowledge
  regime: referencee
```

**Note** : portail des données sur les sols de France. Applications : Donesolweb, Geosol (BDAT), Refersols (inventaire études sols), Applicasol, Répédo. Webservices OGC. **Alerte** : arrêt temporaire bases de données 18/02/2026 (changement serveur) — Donesolweb, DonesolNomade, Geosol, Refersols, Applicasol, Répédo inaccessibles pendant migration. Données geodata.inrae.fr également coupées. RMQS (Réseau de Mesure de la Qualité des Sols, ~2200 sites maille 16 km) est géré par GIS Sol. URL testée : site répond, alerte migration affichée.

---

### C-004 — BRGM InfoTerre (données géoscientifiques)

```yaml
- nom: BRGM InfoTerre — portail des données géoscientifiques
  producteur: BRGM (France)
  url: https://infoterre.brgm.fr/
  access_method: ogc_wms
  licence: Licence Ouverte 2.0 (données publiques BRGM)
  ai_training_allowed: false
  grain_m2: variable (1/1 000 000 à 1/50 000 pour cartes géo ; ponctuel pour BSS)
  emprise: France métropolitaine + DOM
  etendue_temporelle: continu (cartes) ; depuis ~1800 (BSS forages)
  frequence_mise_a_jour: continue
  format: WMS, WFS, WCS, Shapefile, PDF (notices)
  volume_estime: inconnu — cartes + BSS + BSSEAU + risques
  type_source: referentiel_officiel
  moteur_destinataire: Pedology, GIS, Diagnostic, Knowledge, Hydro
  regime: referencee
```

**Note** : portail principal BRGM. Couches : cartes géologiques (1/1M à 1/50k + Quaternaire), Banque du Sous-Sol (BSS, forages + logs), eaux souterraines (BSSEAU), CASIAS (anciens sites industriels), mouvements de terrain, cavités souterraines, aléa retrait-gonflement argiles, registres géologiques, points observations, carte lithostratigraphique. Géoservices OGC (INSPIRE). Visualiseur standard + simplifié. URL testée : portail répond, catalogue complet confirmé.

---

## À VÉRIFIER — Domaine C

### C-V001 — ADES (Accès aux Données sur les Eaux Souterraines)

**Motif** : ADES (https://ades.eaufrance.fr/) est le portail national d'accès aux données sur les eaux souterraines. Mentionné indirectement via Hub'Eau (piézométrie, qualité nappes) mais le portail ADES lui-même n'a pas été testé. À vérifier : endpoint exact, contenu (piézométrie, qualité, référentiel nappes).

### C-V002 — GlobalSoilMap

**Motif** : GlobalSoilMap (https://www.globalsoilmap.net/) vise à produire une carte numérique mondiale des sols à 90 m. Le consortium international (INRAE pour France) publie des produits nationaux. L'URL du portail et la disponibilité du produit France ne sont pas confirmées. À vérifier : statut du produit France, accès téléchargement.

### C-V003 — RMQS — endpoint exact

**Motif** : le RMQS (Réseau de Mesure de la Qualité des Sols, ~2200 sites maille 16 km) est géré par GIS Sol mais son endpoint de téléchargement direct n'est pas clair (peut-être via geodata.inrae.fr, actuellement coupé pendant migration GIS Sol). À établir après restauration des bases GIS Sol.

### C-V004 — Cartes pédologiques départementales (1/25000)

**Motif** : les cartes pédologiques historiques à l'échelle départementale (1/25000) existent mais leur numérisation et disponibilité en open data est hétérogène. Certaines sont sur infoterre.brgm.fr, d'autres sur gissol.fr, d'autres uniquement en papier. À inventorier cas par cas — trop dispersé pour une entrée unique.

---

## Signalements — Domaine C

- **GIS Sol — arrêt temporaire bases 18/02/2026** : les applications Donesolweb, Geosol, Refersols, Applicasol, Répédo sont inaccessibles pendant migration serveur. L'inventaire existant cite BDAT (DS-011) — vérifier que l'accès est restauré avant ingestion.
- **Hub'Eau — API Indicateurs des services décommissionnée 10/09/2026** : ne pas intégrer cette API spécifique.
