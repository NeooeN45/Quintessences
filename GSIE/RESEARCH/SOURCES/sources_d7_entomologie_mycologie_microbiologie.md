# Sources — D7 Entomologie + Mycologie + Microbiologie

| Champ | Valeur |
|---|---|
| **Domaine** | Entomologie + Mycologie + Microbiologie |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## Sommaire

### Entomologie

1. [INPN — Données d'observation et de suivi sur les espèces (insectes)](#1-inpn--données-dobservation-et-de-suivi-sur-les-espèces-insectes)
2. [GBIF — Occurrences d'arthropodes et d'insectes](#2-gbif--occurrences-darthropodes-et-dinsectes)
3. [BDM — Biodiversity Monitoring Switzerland (référence)](#3-bdm--biodiversity-monitoring-switzerland-référence)
4. [DSF — Département de la Santé des Forêts (insectes ravageurs)](#4-dsf--département-de-la-santé-des-forêts-insectes-ravageurs)
5. [Ephytia — Fiches insectes et champignons forestiers (INRAE/DSF)](#5-ephytia--fiches-insectes-et-champignons-forestiers-inraedsf)
6. [EPPO Global Database — Ravageurs et organismes de quarantaine](#6-eppo-global-database--ravageurs-et-organismes-de-quarantaine)
7. [EPPO Q-Bank — Banque de barcodes ADN d'arthropodes](#7-eppo-q-bank--banque-de-barcodes-adn-darthropodes)

### Mycologie

8. [FongiBase / FongiFrance — Base mycologique nationale française](#8-fongibase--fongifrance--base-mycologique-nationale-française)
9. [MycoDB — Base de données mycologique collaborative](#9-mycodb--base-de-données-mycologique-collaborative)
10. [MycoBank — Nomenclature et taxonomie mycologique mondiale](#10-mycobank--nomenclature-et-taxonomie-mycologique-mondiale)
11. [SwissFungi — Base de données mycologique suisse](#11-swissfungi--base-de-données-mycologique-suisse)
12. [GlobalFungi — Base globale de champignons (metabarcoding HTS)](#12-globalfungi--base-globale-de-champignons-metabarcoding-hts)
13. [FungalTraits — Base de données de traits fonctionnels fongiques](#13-fungaltraits--base-de-données-de-traits-fonctionnels-fongiques)

### Microbiologie

14. [RMQS / GIS Sol — Réseau de Mesures de la Qualité des Sols (microbiome)](#14-rmqs--gis-sol--réseau-de-mesures-de-la-qualité-des-sols-microbiome)
15. [Earth Microbiome Project — Catalogue mondial de diversité microbienne](#15-earth-microbiome-project--catalogue-mondial-de-diversité-microbienne)
16. [Global Soil Biodiversity Atlas (GSBI / JRC) — Atlas mondial de la biodiversité des sols](#16-global-soil-biodiversity-atlas-gsbi--jrc--atlas-mondial-de-la-biodiversité-des-sols)

### Synthèse

17. [Synthèse — Priorités et lacunes pour GSIE](#17-synthèse--priorités-et-lacunes-pour-gsie)

---

## 1. INPN — Données d'observation et de suivi sur les espèces (insectes)

| Champ | Valeur |
|---|---|
| **Nom officiel** | INPN — Données d'observation et de suivi sur les espèces (OpenObs) |
| **Organisme** | UAR PatriNat (OFB-MNHN-CNRS-IRD), dans le cadre du SINP |
| **URL d'accès** | https://inpn.mnhn.fr/ |
| **Type d'accès** | `api_rest` + `file_download` (via OpenObs : https://openobs.mnhn.fr/) |
| **Licence** | Open Data — Licence Ouverte / Open Licence v2.0 (données de référence) ; conditions des producteurs pour les occurrences |
| **Volume estimé** | Des dizaines de millions d'occurrences toutes espèces confondues ; les insectes (Arthropoda: Insecta) représentent une part majeure des observations naturalistes françaises |
| **Variables** | Taxon (espèce, genre, famille), date, localisation, observateur, statut de validation SINP, statuts de protection |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — source nationale de référence pour les occurrences d'insectes en France |
| **Exemples d'URL vérifiées** | Portail INPN : https://inpn.mnhn.fr/ — OpenObs : https://openobs.mnhn.fr/ — Jeu de données data.gouv.fr : https://www.data.gouv.fr/datasets/inpn-donnees-dobservation-et-de-suivi-sur-les-especes — Page temporaire PatriNat (cyber-attaque MNHN 2025) : https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353 |

### Notes techniques

- **Attention :** Le site de l'INPN et ses services sont temporairement indisponibles depuis la cyber-attaque subie par le MNHN en été 2025. Une page de téléchargement temporaire des référentiels est maintenue par PatriNat.
- Les données d'occurrence sont également diffusées vers GBIF.
- Le référentiel taxonomique TAXREF (https://taxref.mnhn.fr/taxref-web/api/doc) couvre l'ensemble des insectes de France.
- Les données sensibles (espèces protégées) sont floutées géographiquement à la diffusion publique.

---

## 2. GBIF — Occurrences d'arthropodes et d'insectes

| Champ | Valeur |
|---|---|
| **Nom officiel** | Global Biodiversity Information Facility — Occurrence API |
| **Organisme** | GBIF Secretariat (Copenhague, Danemark) — réseau international financé par les gouvernements membres |
| **URL d'accès** | https://www.gbif.org/ |
| **Type d'accès** | `api_rest` (Occurrence API, Species API) + `file_download` (archives asynchrones Darwin Core) |
| **Licence** | CC0 (public domain), CC-BY 4.0, ou CC-BY-NC 4.0 selon le jeu de données — > 82 % des enregistrements sous CC0 ou CC-BY |
| **Volume estimé** | > 2,9 milliards d'occurrences toutes espèces (2025) ; les arthropodes représentent plusieurs centaines de millions d'enregistrements |
| **Variables** | Espèce, taxon, coordonnées, date, pays, source, identifiant, licence, statut de géoréférencement |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P0** — source mondiale de référence pour les occurrences d'arthropodes, complémentaire de l'INPN |
| **Exemples d'URL vérifiées** | Portail : https://www.gbif.org/ — Occurrence API : https://techdocs.gbif.org/en/openapi/v1/occurrence — Species API : https://techdocs.gbif.org/en/openapi/v1/species — Formats de téléchargement : https://techdocs.gbif.org/en/data-use/download-formats — API downloads : https://techdocs.gbif.org/en/data-use/api-downloads — Conditions d'utilisation : https://www.gbif.org/terms/data-user |

### Notes techniques

- L'API Occurrence permet la recherche paginée (max 300 enregistrements par page, limite stricte de 100 000 par requête). Au-delà, utiliser le service de téléchargement asynchrone.
- Les téléchargements asynchrones génèrent un DOI citable pour chaque extraction.
- Les filtres taxonomiques supportent les clés de royaume, phylum, classe, ordre, famille, genre, espèce.
- Pour les arthropodes : `taxonKey` du phylum Arthropoda = `367` (GBIF Backbone Taxonomy).
- GBIF héberge également des données d'insectes forestiers via de nombreux jeux de données nationaux et de collections muséales.

---

## 3. BDM — Biodiversity Monitoring Switzerland (référence)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Biodiversity Monitoring Switzerland (BDM) |
| **Organisme** | Federal Office for the Environment (FOEN / BAFU), Suisse |
| **URL d'accès** | https://www.biodiversitymonitoring.ch/ |
| **Type d'accès** | `data_agreement` (accord d'utilisation requis pour les données brutes) + `file_download` (indicateurs et méthodes publics) |
| **Licence** | Méthodes et produits gratuits (sur demande) ; données brutes soumises à accord d'utilisation ; indicateurs disponibles sur le site FOEN |
| **Volume estimé** | ~500 surfaces d'échantillonnage de 1 km² ; ~50 000 observations de plantes vasculaires par an ; papillons et oiseaux nicheurs suivis sur le même réseau ; données depuis 2001 |
| **Variables** | Espèces (plantes vasculaires, papillons, oiseaux nicheurs, mousses, escargots, invertébrés aquatiques), abondance, localisation, date, méthodes standardisées |
| **Couverture** | Suisse (ensemble du territoire, réseau systématique de ~500 sites) |
| **Priorité GSIE** | **P0** — référence méthodologique pour le suivi standardisé de la biodiversité, incluant les papillons (Lepidoptera) comme bioindicateurs |
| **Exemples d'URL vérifiées** | Portail : https://www.biodiversitymonitoring.ch/ — Commande de données : https://www.biodiversitymonitoring.ch/index.php/en/data/data-orders — Flux de données : https://biodiversitymonitoring.ch/index.php/en/data/data-flow — Documents méthodologiques : https://biodiversitymonitoring.ch/index.php/en/methodology/method-documents — Géodonnées FOEN : https://www.bafu.admin.ch/en/geodata |

### Notes techniques

- Le BDM est **la référence internationale** pour le suivi longitudinal standardisé de la biodiversité. Son protocole rigoureux (méthodes de terrain et de laboratoire documentées publiquement) en fait un modèle pour GSIE.
- Les données brutes nécessitent un **accord d'utilisation** (data usage agreement) : nom, organisation, spécification des données souhaitées, description du projet.
- Les données de papillons sont transférées au centre de données info fauna (CSCF).
- Les indicateurs de biodiversité calculés par le BDM sont publiés sur le site du FOEN.
- Réseau d'échantillonnage : ~500 surfaces de 1 km², 20 % échantillonnées chaque année (rotation sur 5 ans).

---

## 4. DSF — Département de la Santé des Forêts (insectes ravageurs)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Département de la Santé des Forêts (DSF) |
| **Organisme** | Ministère de l'Agriculture et de la Souveraineté alimentaire (DGAL) — France |
| **URL d'accès** | https://agriculture.gouv.fr/la-sante-des-forets |
| **Type d'accès** | `web_portal` (rapports, bilans, fiches) + `file_download` (PDF, données synthétiques) |
| **Licence** | Open Data (données publiques de l'État) — bilans et fiches librement accessibles |
| **Volume estimé** | ~15 000 observations sylvosanitaires par an ; 270 correspondants-observateurs ; 300 problèmes sanitaires différents diagnostiqués chaque année ; 1 000 échantillons analysés en laboratoire par an ; données depuis 1989 |
| **Variables** | Insectes ravageurs (processionnaire du pin, processionnaire du chêne, défoliateurs du chêne, bombyx disparate, typographe de l'épicéa, hylobe), champignons pathogènes (rouilles des peupliers, oïdium du chêne, sphaeropsis du pin, maladie des bandes rouges), problèmes abiotiques, essence, localisation, année, intensité des dégâts |
| **Couverture** | France métropolitaine (17 millions d'hectares de forêts surveillés) |
| **Priorité GSIE** | **P0** — source nationale de référence pour les insectes forestiers ravageurs en France |
| **Exemples d'URL vérifiées** | Page principale : https://agriculture.gouv.fr/la-sante-des-forets — Rôle et missions : https://agriculture.gouv.fr/le-departement-de-la-sante-des-forets-role-et-missions — Bilans annuels : https://agriculture.gouv.fr/bilans-annuels-en-sante-des-forets — Thermomètre DSF : https://agriculture.gouv.fr/le-thermometre-du-dsf-donne-les-tendances-des-principaux-problemes-sanitaires-et-estime-levolution — Ressources et publications : https://agriculture.gouv.fr/sante-des-forets-ressources-et-publications-0 |

### Notes techniques

- Le DSF suit 6 insectes indicateurs et 4 champignons indicateurs en priorité, ainsi que l'état sanitaire de 10 essences principales (5 feuillus, 5 résineux).
- Les données sont organisées en 6 pôles régionaux/interrégionaux (Nord-Ouest, Nord-Est, Nouvelle-Aquitaine, Bourgogne-Franche-Comté, Auvergne-Rhône-Alpes, Sud-Est).
- Les fiches techniques détaillées sont publiées sur le portail Ephytia (voir source 5).
- Les bilans annuels (nationaux et interrégionaux) sont publiés sous forme de PDF téléchargeables.
- Le « thermomètre du DSF » fournit des indicateurs synthétiques sur l'évolution temporelle des principaux problèmes sanitaires.

---

## 5. Ephytia — Fiches insectes et champignons forestiers (INRAE/DSF)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Ephytia — Espace Forêt |
| **Organisme** | INRAE (en partenariat avec le DSF) |
| **URL d'accès** | https://ephytia.inrae.fr/fr/P/124/Forets |
| **Type d'accès** | `web_portal` (fiches consultables en ligne) |
| **Licence** | Accès libre (contenu INRAE public) |
| **Volume estimé** | Centaines de fiches techniques couvrant les principaux problèmes sanitaires forestiers (insectes, champignons, problèmes abiotiques) |
| **Variables** | Biologie des agents pathogènes, symptômes, dégâts, photos, cartes de répartition, méthodes de lutte, identification |
| **Couverture** | France métropolitaine (forêts françaises) |
| **Priorité GSIE** | **P1** — base de connaissances descriptive sur les insectes ravageurs et champignons pathogènes forestiers |
| **Exemples d'URL vérifiées** | Espace Forêt : https://ephytia.inrae.fr/fr/P/124/Forets — Fiche Typographe : https://ephytia.inrae.fr/fr/C/20324/Forets-Typographe — Fiche Insectes de l'écorce : https://ephytia.inrae.fr/fr/C/18689/Forets-Insectes-de-l-ecorce — Fiche Phytophthora ramorum : https://ephytia.inrae.fr/fr/C/24935/Forets-Phytophthora-ramorum |

### Notes techniques

- Ephytia est le portail de référence pour les fiches techniques phytosanitaires en France.
- L'espace Forêt couvre les principaux problèmes observés par les correspondants-observateurs du DSF.
- Les fiches sont régulièrement mises à jour avec les connaissances de la recherche (partenariat INRAE-DSF).
- Contient à la fois des fiches sur les insectes ravageurs (typographe, processionnaires, scolytes, défoliateurs) et les champignons pathogènes ( Phytophthora, rouilles, oïdium, sphaeropsis).
- Ne fournit pas de données d'occurrence brutes mais des descriptions structurées des bioagresseurs.

---

## 6. EPPO Global Database — Ravageurs et organismes de quarantaine

| Champ | Valeur |
|---|---|
| **Nom officiel** | EPPO Global Database (GD) |
| **Organisme** | European and Mediterranean Plant Protection Organization (EPPO) |
| **URL d'accès** | https://gd.eppo.int/ |
| **Type d'accès** | `web_portal` + `api_rest` (requêtes) + `desktop_app` (EPPO GD Desktop hors ligne) |
| **Licence** | Accès libre et gratuit |
| **Volume estimé** | > 98 700 espèces d'intérêt (plantes cultivées et sauvages, ravageurs, organismes de quarantaine) ; > 1 900 espèces de ravageurs d'intérêt réglementaire avec informations détaillées |
| **Variables** | Noms scientifiques et synonymes, noms communs multilingues, position taxonomique, codes EPPO, distribution géographique (cartes mondiales), plantes hôtes, statut de quarantaine (listes EPPO A1/A2, réglementation UE), vecteurs, agents de lutte biologique |
| **Couverture** | Europe et région méditerranéenne (étendu aux ravageurs réglementés dans le monde) |
| **Priorité GSIE** | **P1** — référence pour les insectes ravageurs forestiers de quarantaine et organismes exotiques invasifs |
| **Exemples d'URL vérifiées** | Portail : https://gd.eppo.int/ — Datasheet Choristoneura fumiferana : https://gd.eppo.int/taxon/CHONFU/datasheet — Guide utilisateur (PDF) : https://gd.eppo.int/media/files/general_user-guide.pdf?202410= — EPPO GD Desktop : https://gd.eppo.int/gddesktop/ |

### Notes techniques

- La base EPPO est la référence pour les organismes de quarantaine en Europe.
- Chaque espèce possède un code EPPO unique (ex. `CHONFU` pour Choristoneura fumiferana).
- Les fiches détaillées incluent distribution géographique mondiale, plantes hôtes, et statut réglementaire (EPPO A1/A2, annexes UE).
- La version Desktop permet une consultation hors ligne (remplace l'ancien système PQR).
- Le Reporting Service EPPO publie des alertes sur les nouveaux ravageurs détectés.

---

## 7. EPPO Q-Bank — Banque de barcodes ADN d'arthropodes

| Champ | Valeur |
|---|---|
| **Nom officiel** | EPPO-Q-bank Arthropod database |
| **Organisme** | EPPO (développée par INRAE-CBGP, France ; NVWA, Pays-Bas) |
| **URL d'accès** | https://qbank.eppo.int/arthropods/ |
| **Type d'accès** | `web_portal` + `database_query` (BLAST) |
| **Licence** | Accès libre (outil d'identification EPPO) |
| **Volume estimé** | Séquences ADN (barcodes COI et ITS2) d'arthropodes de quarantaine pour l'Europe et espèces apparentées (~100 espèces proches séquencées) |
| **Variables** | Séquences mitochondriales COI (barcode standard, 658 bp), séquences nucléaires ITS2, identification taxonomique, protocoles EPPO associés |
| **Couverture** | Europe (arthropodes de quarantaine EPPO et espèces congénères) |
| **Priorité GSIE** | **P2** — outil d'identification moléculaire spécialisé, utile pour la détection d'espèces exotiques invasives |
| **Exemples d'URL vérifiées** | Portail arthropodes : https://qbank.eppo.int/arthropods/ — EPPO Global Database (distribution et protocoles) : https://gd.eppo.int/ |

### Notes techniques

- Conçue pour l'identification fiable de tous les stades de développement des arthropodes de quarantaine.
- Le fragment COI (cytochrome c oxydase 1) est le barcode standard ; ITS2 est utilisé en complément pour certains genres.
- Certaines espèces ne peuvent pas être identifiées de manière fiable par COI seul (groupes taxonomiques à vérifier).
- La base ne prétend pas être exhaustive : consulter la liste des taxons inclus pour vérifier la couverture.
- Développée dans le cadre du projet QBOL (2011-2015), maintenue par EPPO.

---

## 8. FongiBase / FongiFrance — Base mycologique nationale française

| Champ | Valeur |
|---|---|
| **Nom officiel** | FongiBase — Inventaire mycologique national (plateforme FongiFrance) |
| **Organisme** | Association FongiFrance (anciennement AdoniF, fondée 2015) — en partenariat avec SMF, SMNF, MNHN, SINP |
| **URL d'accès** | https://fongibase.fongifrance.fr/ |
| **Type d'accès** | `web_portal` (consultation cartographique et recherche) + `api_rest` (connexion requise pour saisie) |
| **Licence** | Open Data — données publiques librement consultables (sauf espèces sensibles) ; données transmises au SINP |
| **Volume estimé** | > 1 771 312 observations (juillet 2026) ; 11 556 taxons fongiques recensés en France métropolitaine ; données depuis 1708 |
| **Variables** | Espèce (taxon fongique), localisation géographique, date d'observation, observateur, organisme contributeur, écologie (guildes : mycorrhizien 44,6 %, saprotrophe litière 31,6 %, saprotrophe du bois 18,1 %) |
| **Couverture** | France métropolitaine (outre-mer en extension) |
| **Priorité GSIE** | **P0** — source nationale de référence pour les occurrences de champignons en France |
| **Exemples d'URL vérifiées** | FongiBase : https://fongibase.fongifrance.fr/ — FongiFrance (association) : https://fongi.fongifrance.fr/ — Recherche cartographique : https://fongibase.fongifrance.fr/recherchecarto/ — Fiches SMNF : https://fongibase.fongifrance.fr/fiches-smnf/ — Article scientifique (MDPI) : https://www.mdpi.com/2309-608X/8/9/926 |

### Notes techniques

- FongiFrance est constituée de trois bases interconnectées :
  - **FongiBase** : données d'occurrence (répartition géographique et temporelle)
  - **FongiRef** : base nomenclaturale (référentiel des noms d'espèces et synonymies)
  - **FongiDoc** : base documentaire (références bibliographiques associées)
- Les données sont publiées en Open Data et communiquées au SINP au fur et à mesure de leur intégration.
- Les espèces sensibles ne sont pas diffusées publiquement en localisation précise.
- De nombreuses sociétés mycologiques régionales et nationales contribuent (SMF, SMNF, CBN, ONF, RNF, etc.).
- L'analyse publiée (MDPI 2022) révèle une géographie inégale de l'échantillonnage : 4 clusters de forte intensité contrastent avec des zones mal documentées (notamment méditerranéennes).
- Les Basidiomycota et Agaricales dominent (88,8 % et 50,4 % des enregistrements respectivement).

---

## 9. MycoDB — Base de données mycologique collaborative

| Champ | Valeur |
|---|---|
| **Nom officiel** | MycoDB — Base de données de champignons |
| **Organisme** | Projet collaboratif indépendant (contributeurs multiples) |
| **URL d'accès** | https://mycodb.fr/ |
| **Type d'accès** | `web_portal` (consultation, fiches descriptives, photos, cartographie) |
| **Licence** | Accès libre (projet collaboratif en ligne) |
| **Volume estimé** | Centaines à milliers de fiches descriptives avec photos (volume exact non publié publiquement) |
| **Variables** | Descriptions morphologiques, photos, classification du règne fongique, cartographie des récoltes, clés de détermination macroscopique par famille |
| **Couverture** | France (principalement) avec extension aux espèces européennes |
| **Priorité GSIE** | **P2** — base descriptive et pédagogique, complémentaire de FongiBase pour l'identification |
| **Exemples d'URL vérifiées** | Portail : https://mycodb.fr/ — Aide en ligne : https://www.mycodb.fr/help.php?id=1 |

### Notes techniques

- MycoDB est un projet de compilation de données mycologiques sur internet, centralisant descriptions et photos.
- Outil collaboratif permettant à de multiples contributeurs de participer.
- Inclut des clés de détermination macroscopique des familles et des clés informatiques par famille.
- Liée à trois autres bases de données (mentionné dans l'aide en ligne).
- Moins structurée pour l'extraction de données que FongiBase, mais utile pour l'identification visuelle.

---

## 10. MycoBank — Nomenclature et taxonomie mycologique mondiale

| Champ | Valeur |
|---|---|
| **Nom officiel** | MycoBank — Fungal Databases, Nomenclature & Species Banks |
| **Organisme** | Westerdijk Fungal Biodiversity Institute (Utrecht, Pays-Bas) |
| **URL d'accès** | https://www.mycobank.org/ |
| **Type d'accès** | `web_portal` (recherche simple, avancée, type specimens) + `database_query` |
| **Licence** | Accès libre (service à la communauté mycologique) |
| **Volume estimé** | > 500 000 noms fongiques documentés (nomenclature et taxonomie mondiale) ; ~97,7 % des nouveaux taxa décrits enregistrés (2018-2020) |
| **Variables** | Noms scientifiques, nomenclature (nouveautés, combinaisons), descriptions, illustrations, numéros MycoBank, alignements de séquences, identifications polyphasiques, liens vers cultures vivantes, données ADN, spécimens de référence |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P1** — référentiel nomenclatural mondial pour la taxonomie des champignons (symbiotiques, pathogènes, saprophytes) |
| **Exemples d'URL vérifiées** | Portail : https://www.mycobank.org/ — Recherche simple : https://www.mycobank.org/Simple%20names%20search — Recherche avancée : https://www.mycobank.org/Advanced%20names%20search — Recherche type specimens : https://www.mycobank.org/Type%20specimens%20search — Fiche re3data : https://www.re3data.org/repository/r3d100011222 |

### Notes techniques

- MycoBank est l'un des trois dépôts nomenclaturaux reconnus par le Nomenclature Committee for Fungi (avec Index Fungorum et Fungal Names).
- Chaque nouveauté nomenclaturale reçoit un numéro MycoBank unique avant publication valide (requis par l'ICN depuis 2013).
- Les données sont liées à Index Fungorum, GBIF et autres initiatives de biodiversité.
- Inclut des alignements de séquences par paires et des identifications polyphasiques contre des bases de références curatorielles.
- Les noms déposés peuvent rester confidentiels jusqu'à publication, puis deviennent publics.

---

## 11. SwissFungi — Base de données mycologique suisse

| Champ | Valeur |
|---|---|
| **Nom officiel** | SwissFungi — Records Database for the Fungi of Switzerland |
| **Organisme** | WSL (Swiss Federal Institute for Forest, Snow and Landscape Research) — partenaire d'InfoSpecies |
| **URL d'accès** | https://swissfungi.wsl.ch/en/ |
| **Type d'accès** | `web_portal` (atlas de distribution public, précision 5×5 km) + `data_request` (données précises sur demande via InfoSpecies) + `gbif` (jeu de données publié sur GBIF) |
| **Licence** | Licence InfoSpecies — données gratuites pour la recherche, disponibles sur demande ; atlas public à précision 5×5 km |
| **Volume estimé** | > 670 000 observations géoréférencées ; 8 996 taxons connus pour la Suisse ; observations depuis 1770 |
| **Variables** | Espèce (taxon fongique), localisation (précision variable selon niveau de confidentialité), date, observateur, source (inventaires nationaux, projets de recherche, observations bénévoles, herbiers, littérature) |
| **Couverture** | Suisse (ensemble du territoire) |
| **Priorité GSIE** | **P1** — référence pour la mycologie suisse, complémentaire du BDM et de FongiBase pour les comparaisons transfrontalières |
| **Exemples d'URL vérifiées** | Portail : https://swissfungi.wsl.ch/en/ — Données de distribution : https://swissfungi.wsl.ch/en/distribution-data/ — Confidentialité : https://swissfungi.wsl.ch/en/participate/confidentiality-of-data/ — Jeu GBIF : https://www.gbif.org/dataset/c0633ec5-19cd-4a58-b84c-ca55c2e7ae64 — EnviDat : https://www.envidat.ch/dataset/swissfungi-distribution-of-fungi-in-switzerland — opendata.swiss : https://opendata.swiss/en/dataset/swissfungi-records-database-for-the-fungi-of-switzerland — DOI : https://doi.org/10.16904/envidat.136 |

### Notes techniques

- SwissFungi est le Centre national de données et d'information pour les champignons en Suisse, partenaire du réseau InfoSpecies.
- Niveaux de confidentialité (5 niveaux) : sans restriction (standard), restriction 1×1 km, restriction 5×5 km, données verrouillées.
- Les données précises sont disponibles pour les autorités publiques (nationales, cantonales, municipales) et sur demande formelle pour les autres utilisateurs (ONG, éco-bureaux, universités).
- Les données sont transférées vers GBIF (jeu de données Darwin Core).
- La checklist suisse compte 8 996 taxons (état 2018), en constante évolution avec la taxonomie moléculaire.

---

## 12. GlobalFungi — Base globale de champignons (metabarcoding HTS)

| Champ | Valeur |
|---|---|
| **Nom officiel** | GlobalFungi — A global database of fungal occurrences from high-throughput-sequencing metabarcoding studies |
| **Organisme** | Institute of Microbiology, Czech Academy of Sciences (République tchèque) |
| **URL d'accès** | https://globalfungi.com |
| **Type d'accès** | `web_portal` (interface utilisateur) + `file_download` (téléchargement manuel des tables d'abondance) |
| **Licence** | CC-BY-NC 4.0 (Creative Commons Attribution-NonCommercial) — données ouvertes pour usage non commercial avec attribution |
| **Volume estimé** | > 600 millions d'observations de séquences fongiques ; > 17 000 échantillons géolocalisés ; 178 études originales ; millions de variants de séquences uniques (ITS1 et ITS2) |
| **Variables** | Abondance des séquences par taxon fongique, localisation géographique, métadonnées environnementales (habitat, pH, température, précipitations, type de végétation), région ITS (ITS1, ITS2), guildes écologiques (symbiotrophes, pathotrophes, saprotrophes) |
| **Couverture** | Mondiale (tous biomes terrestres : sols et habitats associés aux plantes) |
| **Priorité GSIE** | **P0** — atlas le plus complet de la distribution globale des champignons du sol (symbiotiques, pathogènes, saprophytes) |
| **Exemples d'URL vérifiées** | Interface : https://globalfungi.com — Article Scientific Data : https://www.nature.com/articles/s41597-020-0567-7 — Article Science Advances (diversité multidimensionnelle) : https://www.science.org/doi/10.1126/sciadv.adj8016 — GitHub (copies de données pour GloBI) : https://github.com/globalbioticinteractions/globalfungi — Database Commons : https://ngdc.cncb.ac.cn/databasecommons/database/id/7337 |

### Notes techniques

- GlobalFungi est la base de données la plus complète sur la distribution globale des champignons, basée sur le metabarcoding HTS (séquençage à haut débit).
- Les données couvrent les trois grandes guildes fongiques : **symbiotrophes** (mycorhiziens), **pathotrophes** (pathogènes), **saprotrophes** (décomposeurs).
- Release 5 (2025) disponible : tables d'abondance au niveau espèce pour ITS1, ITS2, et combiné ITS1+ITS2.
- Le site ne propose pas d'accès automatisé (API) — téléchargement manuel uniquement. Des copies sont disponibles sur GitHub pour les workflows automatisés (projet GloBI).
- Les métadonnées incluent : localisation GPS, habitat, type de sol, paramètres édaphiques, productivité de l'écosystème, disponibilité en eau, température.
- Les champignons mycorrhiziens arbusculaires (AM) et ectomycorrhiziens (EcM) montrent des distributions quasi opposées (AM en tropical/subtropical, EcM en tempéré/boréal).

---

## 13. FungalTraits — Base de données de traits fonctionnels fongiques

| Champ | Valeur |
|---|---|
| **Nom officiel** | FungalTraits — A user-friendly traits database of fungi and fungus-like stramenopiles |
| **Organisme** | Université d'Helsinki (Finlande) — publié dans Fungal Diversity (Springer) |
| **URL d'accès** | https://github.com/traitecoevo/fungaltraits |
| **Type d'accès** | `git_repository` (GitHub) + `file_download` (CSV/TXT) |
| **Licence** | Accès libre (données de recherche ouvertes) |
| **Volume estimé** | Traits fonctionnels pour > 10 000 espèces fongiques (champignons et organismes apparentés stramenopiles) |
| **Variables** | Guildes écologiques (symbiotrophes, saprotrophes, pathotrophes, endophytes), traits de cycle de vie, mode de nutrition, préférences d'habitat, taille des fructifications, type de mycorrhize, pathogénicité (animale, végétale, humaine) |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P1** — référentiel des traits fonctionnels fongiques pour catégoriser les champignons en symbiotiques / pathogènes / saprophytes |
| **Exemples d'URL vérifiées** | GitHub : https://github.com/traitecoevo/fungaltraits — Article Springer : https://link.springer.com/article/10.1007/s13225-020-00466-2 — Comparaison FungalTraits vs FUNGuild : https://pmc.ncbi.nlm.nih.gov/articles/PMC9958157/ |

### Notes techniques

- FungalTraits est la base de traits fonctionnels fongiques la plus complète et la plus conviviale.
- Permet de catégoriser les champignons en guildes écologiques : mycorrhiziens (AM, EcM), saprotrophes (sol, bois, litière, fumier), pathotrophes (plantes, animaux, humains), endophytes, lichens.
- Supérieure à FUNGuild pour la couverture des saprotrophes, pathogènes végétaux et endophytes.
- Les données sont téléchargeables depuis GitHub au format tabulaire.
- Essentiel pour croiser les données d'occurrence (GlobalFungi, FongiBase) avec les fonctions écologiques.

---

## 14. RMQS / GIS Sol — Réseau de Mesures de la Qualité des Sols (microbiome)

| Champ | Valeur |
|---|---|
| **Nom officiel** | RMQS — Réseau de Mesures de la Qualité des Sols (programme GIS Sol) |
| **Organisme** | GIS Sol (Groupement d'Intérêt Scientifique Sol) — coordonné par INRAE Info&Sols (Val-de-Loire) |
| **URL d'accès** | https://www.gissol.fr/le-gis/programmes/rmqs-34 |
| **Type d'accès** | `web_portal` + `data_request` (données sur demande) + `file_download` (rapports publics) |
| **Licence** | Open Data (données publiques GIS Sol) — accès aux données détaillées sur demande |
| **Volume estimé** | ~2 200 sites en France métropolitaine (maille systématique 16 km) + 70 sites outre-mer (Antilles, Réunion, Mayotte, Guyane) ; suivi depuis 2000 ; échantillonnage par rotation (20 % des sites chaque année sur 5 ans) |
| **Variables** | Propriétés physiques (texture, structure), chimiques (pH, C, N, P, métaux), biologiques (biomasse microbienne, diversité bactérienne et fongique par metabarcoding ADN), contaminants, occupation des sols, pratiques agricoles |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — source nationale de référence pour le microbiome du sol en France |
| **Exemples d'URL vérifiées** | GIS Sol RMQS : https://www.gissol.fr/le-gis/programmes/rmqs-34 — INRAE Info&Sols : https://info-et-sols.val-de-loire.hub.inrae.fr/projets/programmes-du-gis-sol/rmqs — Article HAL (biodiversité des sols) : https://hal.inrae.fr/hal-03484172v1 — Encyclopédie de l'environnement : https://www.encyclopedie-environnement.org/en/zoom/rmqs-network-soil-quality/ — INRAE InfoSol : https://www.inrae.fr/en/news/infosol |

### Notes techniques

- Le RMQS est le programme national français de surveillance à long terme de la qualité des sols, démarré en 2000.
- Une phase « RMQS-biodiversité » est en développement pour le suivi de la biodiversité des sols (bactéries, champignons, mésofaune) par metabarcoding ADN.
- La biodiversité du sol représenterait environ un quart des espèces de la planète.
- Un gramme de sol contient ~1 milliard de bactéries et 100 000 à 1 million d'espèces différentes (INRAE).
- Les données microbiologiques s'affranchissent des identifications morphologiques au profit du polymorphisme de l'ADN extrait directement du sol.
- Le programme REVA (sciences participatives, créé en 2016) complète le RMQS pour le suivi de la qualité biologique des sols agricoles.

---

## 15. Earth Microbiome Project — Catalogue mondial de diversité microbienne

| Champ | Valeur |
|---|---|
| **Nom officiel** | Earth Microbiome Project (EMP) |
| **Organisme** | EMP Consortium (fondé en 2010, coordonné depuis UCSD / Knight Lab) |
| **URL d'accès** | https://earthmicrobiome.org/ |
| **Type d'accès** | `file_download` (FTP, Zenodo) + `web_portal` (Qiita EMP Portal) + `git_repository` (GitHub) |
| **Licence** | CC-BY 4.0 (données et résultats publiés sur Zenodo) — données ouvertes |
| **Volume estimé** | ~25 000 échantillons dans 97 études (EMP Release 1) ; ~100 études au total ; archive Zenodo de 47,3 Go ; EMP500 (extension à 500 échantillons) |
| **Variables** | Tables d'observation BIOM (abondance OTU/ASV), métadonnées d'échantillons (type d'environnement, pH, température, salinité, oxygène), taxonomies (Greengenes, SILVA), arbres phylogénétiques, diversité alpha et beta, ontologie EMPO (EMP Sample Type Ontology) |
| **Couverture** | Mondiale (tous types d'environnements : sols, eau, sédiments, hot springs, animaux, plantes) |
| **Priorité GSIE** | **P0** — catalogue mondial de référence pour la diversité microbienne, incluant les microbiomes du sol |
| **Exemples d'URL vérifiées** | Portail : https://earthmicrobiome.org/ — Données et code : https://earthmicrobiome.org/data-and-code/ — Archive Zenodo (Release 1) : https://zenodo.org/records/890000 — GitHub (code et méthodes) : https://github.com/biocore/emp — Article Nature : https://www.nature.com/articles/nature24621 — Qiita EMP Portal : https://qiita.ucsd.edu/emp/ |

### Notes techniques

- L'EMP est le plus grand effort collaboratif de catalogage des communautés microbiennes à l'échelle planétaire.
- EMP Release 1 (16S) : ~25 000 échantillons, 97 études, tables BIOM déblur (90bp, 100bp, 150bp) et closed-reference (Greengenes 13.8, SILVA 123).
- Les données sont accessibles via :
  - **FTP** : `ftp://ftp.microbio.me/emp/release1` (tables BIOM, métadonnées, arbres, résultats de diversité)
  - **Zenodo** : archive complète avec DOI (47,3 Go)
  - **Qiita** : portail pour rechercher et télécharger des études individuelles (requiert Google Chrome)
  - **Redbiom** : recherche par données d'observation et métadonnées d'échantillons
- L'ontologie EMPO (EMP Sample Type Ontology) classifie les types d'environnements de manière standardisée.
- Les « EMP Trading Cards » mettent en évidence les patterns de distribution de séquences prévalentes.

---

## 16. Global Soil Biodiversity Atlas (GSBI / JRC) — Atlas mondial de la biodiversité des sols

| Champ | Valeur |
|---|---|
| **Nom officiel** | Global Soil Biodiversity Atlas |
| **Organisme** | Global Soil Biodiversity Initiative (GSBI) + European Commission Joint Research Centre (JRC) |
| **URL d'accès** | https://www.globalsoilbiodiversity.org/ |
| **Type d'accès** | `web_portal` + `file_download` (atlas PDF, cartes, données) |
| **Licence** | Accès libre (publication conjointe GSBI/JRC) — données européennes via ESDAC (JRC) |
| **Volume estimé** | Atlas synthétisant la recherche mondiale sur la biodiversité des sols ; cartes globales de distribution des organismes du sol (bactéries, champignons, nématodes, coléoptères, vers de terre, acariens, etc.) |
| **Variables** | Distribution des groupes d'organismes du sol, menaces (pollution, changement climatique, usage intensif, espèces invasives), services écosystémiques, richesse spécifique estimée, biomasse microbienne |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P1** — référence synthétique pour la biodiversité des sols au niveau global, complémentaire du RMQS (France) et de l'EMP (microbiome) |
| **Exemples d'URL vérifiées** | GSBI : https://www.globalsoilbiodiversity.org/ — Introduction atlas : https://www.globalsoilbiodiversity.org/atlas-introduction — ESDAC JRC : https://esdac.jrc.ec.europa.eu/content/global-soil-biodiversity-atlas |

### Notes techniques

- Le Global Soil Biodiversity Atlas est la première synthèse mondiale de la recherche sur la biodiversité des sols.
- Publication conjointe GSBI (Colorado State University) et JRC (Commission européenne).
- L'atlas décrit le sol comme habitat pour la diversité des organismes, attire l'attention sur les menaces (espèces invasives, pollution, usage intensif, changement climatique) et propose des solutions.
- Les données sous-jacentes sont accessibles via ESDAC (European Soil Data Centre) du JRC.
- Une traduction de l'atlas est en cours d'extension.
- Complémentaire du RMQS pour la dimension globale et de l'EMP pour la dimension moléculaire.

---

## 17. Synthèse — Priorités et lacunes pour GSIE

### Récapitulatif des priorités

| Priorité | Sources | Rôle dans GSIE |
|---|---|---|
| **P0** | INPN (insectes), GBIF (arthropodes), BDM (référence méthodologique), DSF (insectes forestiers), FongiBase (champignons France), GlobalFungi (champignons mondiaux), RMQS (microbiome sol France), EMP (microbiome mondial) | Sources de données primaires — occurrences, suivis, metabarcoding |
| **P1** | Ephytia (fiches forestières), EPPO Global Database (quarantaine), MycoBank (nomenclature fongique), SwissFungi (mycologie suisse), FungalTraits (traits fonctionnels), Global Soil Biodiversity Atlas (synthèse sols) | Sources de référence et complémentaires — taxonomie, traits, réglementation, comparaisons transfrontalières |
| **P2** | EPPO Q-Bank (barcodes quarantaine), MycoDB (base descriptive) | Outils spécialisés — identification moléculaire, pédagogie |

### Couverture par sous-domaine

| Sous-domaine | Sources principales | Sources complémentaires | Lacunes identifiées |
|---|---|---|---|
| **Insectes (occurrences)** | INPN, GBIF | BDM (papillons) | Données d'insectes décomposeurs et auxiliaires sous-représentées dans les bases naturalistes vs. ravageurs |
| **Insectes forestiers ravageurs** | DSF, Ephytia, EPPO | EPPO Q-Bank | Données brutes d'occurrence du DSF non accessibles en téléchargement direct (synthèses publiques uniquement) |
| **Insectes auxiliaires / décomposeurs** | INPN, GBIF | — | Pas de base dédiée aux insectes auxiliaires ou décomposeurs forestiers ; à reconstituer par filtrage taxonomique |
| **Champignons symbiotiques** | GlobalFungi, FongiBase, FungalTraits | SwissFungi, MycoBank | Couverture mondiale bonne (GlobalFungi) ; données françaises en progression (FongiBase) |
| **Champignons pathogènes** | DSF, Ephytia, EPPO, GlobalFungi | FungalTraits, MycoBank | Bonne couverture pour les pathogènes forestiers (DSF/Ephytia) ; pathogènes non forestiers à compléter via EPPO |
| **Champignons saprophytes** | GlobalFungi, FongiBase | FungalTraits, SwissFungi | Couverture adéquate via GlobalFungi (metabarcoding) et FongiBase (occurrences) |
| **Microbiome du sol** | RMQS, EMP | Global Soil Biodiversity Atlas | RMQS-biodiversité encore en phase pilote ; données microbiennes à long terme à consolider |
| **Taxonomie fongique** | MycoBank, FongiRef | TAXREF (INPN) | Taxonomie fongique en constante évolution (moléculaire) — synchronisation nécessaire |

### Recommandations pour GSIE

1. **Entomologie :** Croiser INPN (occurrences France) + GBIF (occurrences mondiales) + DSF (ravageurs forestiers) pour une vue intégrée. Le BDM sert de **référence méthodologique** pour le suivi standardisé des papillons (bioindicateurs).
2. **Mycologie :** Combiner FongiBase (occurrences France) + GlobalFungi (metabarcoding mondial) + FungalTraits (guildes fonctionnelles) pour modéliser les rôles écologiques (symbiotique / pathogène / saprophyte).
3. **Microbiologie :** Articuler RMQS (France, long terme) + EMP (mondial, diversité) + Global Soil Biodiversity Atlas (synthèse) pour le moteur Pedology et les services écosystémiques du sol.
4. **Interopérabilité taxonomique :** MycoBank et TAXREF (INPN) comme référentiels nomenclaturaux ; FongiRef pour la fonge française.
5. **Ravageurs forestiers :** DSF + EPPO + Ephyta forment un triptyque complet (données de terrain + réglementation + connaissances descriptives).
6. **Attention INPN :** Le site INPN est temporairement indisponible (cyber-attaque MNHN été 2025). Utiliser la page PatriNat de téléchargement temporaire en attendant la restauration.

---

## Références bibliographiques clés

- Větrovský et al. (2020). GlobalFungi, a global database of fungal occurrences from high-throughput-sequencing metabarcoding studies. *Scientific Data* 7, 228. https://doi.org/10.1038/s41597-020-0567-7
- Thompson et al. (2017). A communal catalogue reveals Earth's multiscale microbial diversity. *Nature* 551, 457–463. https://doi.org/10.1038/nature24621
- Põlme et al. (2020). FungalTraits: a user-friendly traits database of fungi and fungus-like stramenopiles. *Fungal Diversity* 105, 1–16. https://doi.org/10.1007/s13225-020-00466-2
- Andrew et al. (2017). French National Fungal Database (FongiFrance) — *Journal of Fungi* 8(9), 926. https://www.mdpi.com/2309-608X/8/9/926
- Egli et al. (2020). SwissFungi — Records Database for the Fungi of Switzerland. EnviDat. https://doi.org/10.16904/envidat.136
