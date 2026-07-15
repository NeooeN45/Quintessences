# Sources — D1 Taxonomie + Botanique

| Champ | Valeur |
|---|---|
| **Domaine** | Taxonomie + Botanique |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## Sommaire

1. [TAXREF — Référentiel taxonomique national](#1-taxref--référentiel-taxonomique-national)
2. [GBIF — Global Biodiversity Information Facility](#2-gbif--global-biodiversity-information-facility)
3. [INPN — Inventaire National du Patrimoine Naturel](#3-inpn--inventaire-national-du-patrimoine-naturel)
4. [Tela Botanica / BDTFX — Base de Données des Trachéophytes de France](#4-tela-botanica--bdtfx--base-de-données-des-trachéophytes-de-france)
5. [BDNFF / ISFF — Base de Données Nomenclaturale de la Flore de France](#5-bdnff--isff--base-de-données-nomenclaturale-de-la-flore-de-france)
6. [Catalogue of Life (COL)](#6-catalogue-of-life-col)
7. [ITIS — Integrated Taxonomic Information System](#7-itis--integrated-taxonomic-information-system)
8. [WoRMS — World Register of Marine Species](#8-worms--world-register-of-marine-species)
9. [BD Forêt (IGN) — Essences forestières](#9-bd-forêt-ign--essences-forestières)
10. [IPNI — International Plant Names Index](#10-ipni--international-plant-names-index)
11. [WCVP — World Checklist of Vascular Plants](#11-wcvp--world-checklist-of-vascular-plants)
12. [WFO — World Flora Online](#12-wfo--world-flora-online)

---

## 1. TAXREF — Référentiel taxonomique national

| Champ | Valeur |
|---|---|
| **Nom officiel** | TAXREF — Référentiel taxonomique national pour la France |
| **Organisme producteur** | PatriNat (OFB–CNRS–MNHN–IRD), Muséum national d'Histoire naturelle (MNHN) |
| **URL d'accès** | Portail : https://taxref.mnhn.fr/taxref-web/ — API : https://taxref.mnhn.fr/taxref-web/api/doc — Téléchargement : https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/18.0/menu |
| **Type d'accès** | `api_rest`, `file_download` |
| **Licence** | CC-BY 4.0 (selon IPT GBIF France). Le paquet R `rtaxref` indique CC BY-SA 3.0 pour les données d'accès. Conditions d'utilisation : citation obligatoire, pas de redistribution à un tiers sans formulaire, pas de mise en ligne sans autorisation préalable. |
| **Volume estimé** | TAXREF v18.0 (publiée le 09/01/2025) : **708 685 enregistrements** au format Darwin Core Archive (DwC-A), 8 fichiers CSV. Couvre l'ensemble des organismes vivants de France métropolitaine et d'outre-mer (faune, flore, fonge). |
| **Variables disponibles** | Nomenclature (noms scientifiques, noms vernaculaires), taxonomie (hiérarchie, rangs, synonymes), répartition biogéographique par territoire, statuts de protection et de menace (Listes rouges, statuts réglementaires), interactions biologiques, références bibliographiques par taxon, codes alternatifs (GBIF, ITIS, WoRMS, etc.). |
| **Fréquence de mise à jour** | Annuelle (version majeure publiée chaque janvier). API en temps réel sur la version courante. |
| **Qualité et couverture** | Référentiel officiel du SINP. Couverture : France métropolitaine + outre-mer. Qualité élevée, validée par des experts taxonomiques. Liens avec référentiels internationaux (GBIF, Catalogue of Life). |
| **Priorité GSIE** | **P0 — critique**. Colonie vertébrale taxonomique pour toutes les espèces françaises. Source primaire pour le moteur Botanical et Forest Dynamics. |
| **Exemples d'URL** | API doc : `https://taxref.mnhn.fr/taxref-web/api/doc` — Recherche taxon : `https://taxref.mnhn.fr/taxref-web/api/taxa/search` — Téléchargement DwC-A : `https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/18.0/menu` — DOI : `https://doi.org/10.15468/vqueam` |

> **Sources** : [TAXREF-Web](https://taxref.mnhn.fr/taxref-web/), [IPT GBIF France](https://ipt.gbif.fr/resource?r=taxref), [PatriNat](https://www.patrinat.fr/fr/referentiel-taxonomique-taxref-6057), [data.gouv.fr](https://www.data.gouv.fr/datasets/referentiel-taxonomique-taxref-1), [GitHub rtaxref](https://github.com/Rekyt/rtaxref/)

> **Note** : Depuis septembre 2025, le MNHN a subi une cyberattaque ; certains services API sont temporairement indisponibles. Une page de téléchargement temporaire est disponible sur [PatriNat](https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353).

---

## 2. GBIF — Global Biodiversity Information Facility

| Champ | Valeur |
|---|---|
| **Nom officiel** | Global Biodiversity Information Facility (GBIF) |
| **Organisme producteur** | Secrétariat GBIF (Copenhague, Danemark), réseau mondial de pays et organisations membres |
| **URL d'accès** | API : https://api.gbif.org/v1/ — Portail : https://www.gbif.org/ — Documentation : https://techdocs.gbif.org/en/openapi/ |
| **Type d'accès** | `api_rest`, `file_download` |
| **Licence** | Données d'occurrence : CC0 1.0, CC-BY 4.0 ou CC-BY-NC 4.0 selon le jeu de données source. L'API GBIF elle-même est en accès libre. Téléchargements asynchrones avec DOI attribué. |
| **Volume estimé** | **> 3,11 milliards d'occurrences** globalement (2025). France : ~212,7 millions d'occurrences (3e pays fournisseur mondial mi-2025). ~185 192 espèces enregistrées pour la France. ~2,6 millions de noms scientifiques indexés (backbone taxonomique). |
| **Variables disponibles** | Occurrences (taxon, coordonnées, date, observateur, baseOfRecord), métadonnées de jeux de données, taxonomie (backbone GBIF basé sur Catalogue of Life + ITIS + autres), métriques (comptes par pays, par taxon, par année), téléchargements asynchrones (filtres prédicats, SQL downloads). |
| **Fréquence de mise à jour** | Continue (indexation quotidienne des nouveaux jeux de données). |
| **Qualité et couverture** | Couverture mondiale. Qualité variable selon les jeux de données sources (de données citoyennes à données muséales expertes). Backbone taxonomique aligné sur Catalogue of Life. |
| **Priorité GSIE** | **P0 — critique**. Source d'occurrences la plus volumineuse au monde. Indispensable pour la corrélation espèces–habitats et la validation de la présence d'essences forestières. |
| **Exemples d'URL** | Recherche d'occurrences : `https://api.gbif.org/v1/occurrence/search?country=FR&taxonKey=6` — Recherche d'espèces : `https://api.gbif.org/v1/species/search?q=Quercus` — Téléchargement asynchrone : `https://api.gbif.org/v1/occurrence/download/request` — SQL downloads : `https://api.gbif.org/v1/occurrence/download/sql` |

> **Sources** : [GBIF API Reference](https://techdocs.gbif.org/en/openapi/), [Occurrence API](https://techdocs.gbif.org/en/openapi/v1/occurrence), [Species API](https://techdocs.gbif.org/en/openapi/v1/species), [API Downloads](https://techdocs.gbif.org/en/data-use/api-downloads), [GBIF France 2025](https://www.odatis-ocean.fr/fileadmin/documents/activites/ateliers/atelier_202506/202506_ODATIS_Atelier_IPT_GBIF.pdf), [CountryLens](https://countrylens.com/index-method/gbif_total_occurrences)

---

## 3. INPN — Inventaire National du Patrimoine Naturel

| Champ | Valeur |
|---|---|
| **Nom officiel** | Inventaire National du Patrimoine Naturel (INPN) |
| **Organisme producteur** | PatriNat (OFB–MNHN–CNRS–IRD), dans le cadre du SINP (Système d'Information de l'inventaire du Patrimoine naturel) |
| **URL d'accès** | Portail : https://inpn.mnhn.fr/ — OpenObs : https://openobs.mnhn.fr/ — API OpenObs : https://openobs.mnhn.fr/developer — API OData SINP : https://odata-sinp.mnhn.fr/ |
| **Type d'accès** | `api_rest`, `file_download` |
| **Licence** | Données ouvertes (Licence Ouverte SINP / Licence Ouverte Etalab 2.0) pour les données non sensibles. Données sensibles : licence spécifique interdisant la rediffusion publique. |
| **Volume estimé** | Données d'observation et de suivi sur les espèces (occurrences non sensibles) accessibles via OpenObs. Exports limités à 1 million de données par téléchargement. Volume total : des dizaines de millions d'occurrences françaises. |
| **Variables disponibles** | Occurrences d'espèces (taxon, coordonnées, date, observateur, stade de vie, statut biologique, comportement), cartes de présence par espèce, référentiels (taxonomiques, géographiques, administratifs), métadonnées de jeux de données, statuts de protection. |
| **Fréquence de mise à jour** | Continue (alimentation par les partenaires du SINP). |
| **Qualité et couverture** | France métropolitaine + outre-mer. Plateforme nationale de référence du SINP. Données validées selon les standards SINP (standard d'échange, contrôles automatiques et experts). |
| **Priorité GSIE** | **P0 — critique**. Source nationale officielle d'occurrences d'espèces en France. Complémentaire de GBIF pour les données françaises avec validation SINP. |
| **Exemples d'URL** | OpenObs : `https://openobs.mnhn.fr/` — API OpenObs : `https://openobs.mnhn.fr/developer` — API OData organismes : `https://odata-sinp.mnhn.fr/organizations?code=UUID` — Extraction SINP (données sensibles) : `https://inpn.mnhn.fr/espece/extraction-sinp/preambule` |

> **Sources** : [INPN](https://inpn.mnhn.fr/), [OpenObs](https://openobs.mnhn.fr/), [data.gouv.fr INPN](https://www.data.gouv.fr/datasets/inpn-donnees-dobservation-et-de-suivi-sur-les-especes), [Accès données INPN PDF](https://www.guadeloupe.developpement-durable.gouv.fr/IMG/pdf/acces_donnees_inpn_v2_2022.pdf), [CADA 20211712](https://cada.data.gouv.fr/20211712/)

---

## 4. Tela Botanica / BDTFX — Base de Données des Trachéophytes de France

| Champ | Valeur |
|---|---|
| **Nom officiel** | BDTFX — Base de Données des Trachéophytes de France métropolitaine et contrées limitrophes |
| **Organisme producteur** | Tela Botanica (réseau des botanistes francophones), compilé par Benoît Bock sur la base de l'ISFF de Michel Kerguelen (1928–1999) |
| **URL d'accès** | Portail : https://www.tela-botanica.org/flore/france-metropolitaine/ — Projet : https://www.tela-botanica.org/projets/referentiel-des-tracheophytes-de-metropole-isff-bdnff-bdtfx-taxref/ — API eFlore : https://api.tela-botanica.org/service:eflore:0.1/ — Téléchargements : https://www.tela-botanica.org/ressources/donnees/telechargements/ |
| **Type d'accès** | `api_rest`, `file_download` |
| **Licence** | CC BY-SA 4.0 (Creative Commons Attribution – Partage dans les Mêmes Conditions). Site Tela Botanica : contenu texte sous licence CC BY-SA 4.0. |
| **Volume estimé** | Version janvier 2024 : **101 476 noms** dont **27 584 taxons** (tous rangs du règne à la forme, y compris hybrides). Index réduit (fleurs de Bonnier, Coste, Fournier, CNRS, Flora Gallica) : 27 677 noms. Extension en cours à tous les taxons européens. |
| **Variables disponibles** | Nomenclature (noms scientifiques, synonymes, noms vernaculaires), taxonomie (hiérarchie, rangs), chorologie départementale, données écologiques (optimums écologiques via baseflor), descriptions, illustrations, ethnobotanique, bibliographie par taxon. |
| **Fréquence de mise à jour** | Mises à jour ponctuelles (dernière version majeure : janvier 2024). Versions successives téléchargeables. |
| **Qualité et couverture** | France métropolitaine + contrées limitrophes (Péninsule ibérique, Italie, Belgique, Luxembourg, Afrique du Nord). Qualité élevée, basée sur Flora Gallica et travaux experts (Rubus de France par David Mercier). A été la source de TAXREF pour les plantes vasculaires de 2010 à 2016. |
| **Priorité GSIE** | **P0 — critique**. Référentiel nomenclatural et taxonomique le plus détaillé pour la flore vasculaire française. Complémentaire de TAXREF avec des données écologiques et chorologiques plus riches pour la botanique. |
| **Exemples d'URL** | Fiche taxon : `https://www.tela-botanica.org/bdtfx-nn-562` — API eFlore métadonnées : `https://api.tela-botanica.org/service:eflore:0.1/` — Documentation API : http://www.tela-botanica.net/doc/services/eflore/ — Téléchargement : `https://www.tela-botanica.org/ressources/donnees/telechargements/` |

> **Sources** : [Tela Botanica — France métropolitaine](https://www.tela-botanica.org/flore/france-metropolitaine/), [Projet BDTFX](https://www.tela-botanica.org/projets/referentiel-des-tracheophytes-de-metropole-isff-bdnff-bdtfx-taxref/), [Téléchargements](https://www.tela-botanica.org/ressources/donnees/telechargements/), [Mentions légales](https://www.tela-botanica.org/mentions-legales/), [Mise à jour 2024](https://www.tela-botanica.org/2019/10/mises-a-jour-des-donnees-deflore-france-metropolitaine/)

---

## 5. BDNFF / ISFF — Base de Données Nomenclaturale de la Flore de France

| Champ | Valeur |
|---|---|
| **Nom officiel** | BDNFF — Base de Données Nomenclaturale de la Flore de France / ISFF — Index Synonymique de la Flore de France |
| **Organisme producteur** | Tela Botanica (Benoît Bock), dans le cadre d'une convention quadripartite MNHN / Tela Botanica / Ministère chargé de l'Écologie / Fédération des conservatoires botaniques nationaux (FCBN) |
| **URL d'accès** | Projet : https://www.tela-botanica.org/projets/referentiel-des-tracheophytes-de-metropole-isff-bdnff-bdtfx-taxref/ — Porte-documents : https://www.tela-botanica.org/projets/referentiel-des-tracheophytes-de-metropole-isff-bdnff-bdtfx-taxref/porte-documents/ |
| **Type d'accès** | `file_download`, `knowledge_extraction` |
| **Licence** | CC BY-SA 4.0 (dans le cadre de Tela Botanica) |
| **Volume estimé** | La BDNFF est la base source de la BDTFX. Recense l'ensemble des noms de plantes vasculaires (Phanérogames et Ptéridophytes) indigènes, naturalisées et adventices de la Flore de France et de Corse mentionnés dans la littérature. Volume similaire à la BDTFX (~100 000 noms). |
| **Variables disponibles** | Nomenclature exhaustive (tous les noms mentionnés dans la littérature, y compris synonymes et noms non retenus), références bibliographiques détaillées, historique nomenclatural. |
| **Fréquence de mise à jour** | Mises à jour ponctuelles, en continu via la liste ISFF et les collaborations expertes. |
| **Qualité et couverture** | France métropolitaine + Corse. Qualité très élevée (travail de synthèse sur la littérature botanique depuis Michel Kerguelen). Couverture nomenclaturale exhaustive. |
| **Priorité GSIE** | **P1 — importante**. Source de référence pour la validation nomenclaturale des taxons botaniques français. La BDNFF est le substrat de la BDTFX ; elle contient l'historique nomenclatural complet. |
| **Exemples d'URL** | Porte-documents : `https://www.tela-botanica.org/projets/referentiel-des-tracheophytes-de-metropole-isff-bdnff-bdtfx-taxref/porte-documents/` — Téléchargements : `https://www.tela-botanica.org/ressources/donnees/telechargements/` |

> **Sources** : [Projet ISFF/BDNFF/BDTFX](https://www.tela-botanica.org/projets/referentiel-des-tracheophytes-de-metropole-isff-bdnff-bdtfx-taxref/), [Téléchargements Tela Botanica](https://www.tela-botanica.org/ressources/donnees/telechargements/)

---

## 6. Catalogue of Life (COL)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Catalogue of Life (COL) |
| **Organisme producteur** | Catalogue of Life (en partenariat avec GBIF), hébergé sur ChecklistBank. Maintenu par des centaines d'experts taxonomiques mondiaux. |
| **URL d'accès** | Portail : https://www.catalogueoflife.org/ — API ChecklistBank : https://api.checklistbank.org/ — API COL : https://api.catalogueoflife.org/ — Documentation API : https://www.catalogueoflife.org/tools/api |
| **Type d'accès** | `api_rest`, `file_download` |
| **Licence** | CC-BY 4.0 (données). Le COL 2025 inclut des données de multiples sources (165+ bases de données taxonomiques peer-reviewed). |
| **Volume estimé** | COL 2025 : **> 2,2 millions d'espèces existantes** décrites (+ ~153 000 espèces éteintes). 48 766 nouveaux noms d'espèces acceptés ajoutés en 2025. 165+ bases de données taxonomiques contributrices. |
| **Variables disponibles** | Nomenclature (noms scientifiques, synonymes), taxonomie (hiérarchie complète, classification), statut des noms (accepté/synonyme), informations bibliographiques, distribution (partielle), identifiants vers autres référentiels. |
| **Fréquence de mise à jour** | Release annuelle (version stable) + working draft continu sur ChecklistBank. |
| **Qualité et couverture** | Couverture mondiale. Qualité élevée (peer-reviewed par experts). Le COL est la base du backbone taxonomique GBIF. |
| **Priorité GSIE** | **P1 — importante**. Référentiel taxonomique mondial de référence. Utile pour aligner les taxons français (TAXREF) avec la taxonomie globale et résoudre les synonymies internationales. |
| **Exemples d'URL** | API ChecklistBank : `https://api.checklistbank.org/` — API COL : `https://api.catalogueoflife.org/` — Release 2025 : `https://www.catalogueoflife.org/2025/07/09/annual-release` |

> **Sources** : [Catalogue of Life](https://www.catalogueoflife.org/), [COL API](https://www.catalogueoflife.org/tools/api), [ChecklistBank API](https://api.checklistbank.org/), [COL 2025 release](https://www.catalogueoflife.org/2025/07/09/annual-release), [Wikipedia COL](https://en.wikipedia.org/wiki/Catalogue_of_Life)

---

## 7. ITIS — Integrated Taxonomic Information System

| Champ | Valeur |
|---|---|
| **Nom officiel** | Integrated Taxonomic Information System (ITIS) |
| **Organisme producteur** | ITIS (partenariat USGS, agences fédérales US, Canada, Mexique, experts mondiaux). Géré par le U.S. Geological Survey. |
| **URL d'accès** | Portail : https://www.itis.gov/ — Web Services : https://www.itis.gov/ws_develop.html — Solr : https://services.itis.gov/ — Description API : https://www.itis.gov/ws_description.html |
| **Type d'accès** | `api_rest` (SOAP/REST + Solr), `file_download` |
| **Licence** | **CC0 1.0 (Public Domain)**. Les données ITIS sont dans le domaine public américain. Citation demandée. DOI : https://doi.org/10.5066/F7KH0KBK |
| **Volume estimé** | Export mensuel juin 2026 : **993 167 noms scientifiques** (tous rangs, tous statuts) et **166 746 noms vernaculaires**. Base de données web service : 483 305 noms scientifiques (380 578 valides/acceptés) et 109 142 noms vernaculaires. |
| **Variables disponibles** | Noms scientifiques (TSN — Taxonomic Serial Number), hiérarchie taxonomique, noms vernaculaires (anglais, espagnol, français), statut (valide/synonyme), rang, royaume, données bibliographiques, crédibilité. |
| **Fréquence de mise à jour** | Export mensuel. Base de données mise à jour en continu. |
| **Qualité et couverture** | Couverture mondiale avec focus Amérique du Nord. Qualité variable selon les groupes (certains très complets, autres en cours de révision). Partenaire du Catalogue of Life et contributeur au backbone GBIF. |
| **Priorité GSIE** | **P2 — utile**. Référentiel international de référence, mais couverture française mieux servie par TAXREF. Utile pour l'alignement taxonomique international et la résolution de noms via TSN. |
| **Exemples d'URL** | API REST/SOAP : `https://www.itis.gov/ITISWebService/services/ITISService/getFullRecordFromTSN?tsn=183833` — Solr JSON : `https://services.itis.gov/?q=tsn:182662&wt=json` — Téléchargement complet : https://www.itis.gov/access.html |

> **Sources** : [ITIS.gov](https://www.itis.gov/), [Web Services](https://www.itis.gov/ws_develop.html), [Solr Web Services](https://www.itis.gov/solr_documentation.html), [Privacy and Legal](https://itis.gov/privacy.html), [Citation](https://www.itis.gov/citation.html), [USGS](https://www.usgs.gov/tools/integrated-taxonomic-information-system-itis)

---

## 8. WoRMS — World Register of Marine Species

| Champ | Valeur |
|---|---|
| **Nom officiel** | WoRMS — World Register of Marine Species |
| **Organisme producteur** | VLIZ (Vlaams Instituut voor de Zee / Flanders Marine Institute), Ostende, Belgique. Édité par des centaines de contributeurs volontaires (WoRMS Editorial Board). |
| **URL d'accès** | Portail : https://marinespecies.org/ — API REST : https://marinespecies.org/rest — Webservice SOAP/WSDL : https://marinespecies.org/aphia.php?p=webservice — Statistiques : https://marinespecies.org/aphia.php?p=stats |
| **Type d'accès** | `api_rest` (REST + SOAP/WSDL), `file_download` (sur demande) |
| **Licence** | **CC-BY 4.0** pour le contenu textuel. Images : CC BY-NC-SA par défaut. Redistribution de la base complète non autorisée sans accord écrit préalable. Téléchargements trimestriels possibles pour instituts (sur demande). |
| **Volume estimé** | **250 290 espèces marines acceptées** (mai 2026, > 98% vérifiées par éditeurs). 523 075 noms d'espèces marines (incluant synonymes). Contient également des espèces non-marines. |
| **Variables disponibles** | Nomenclature (noms scientifiques, synonymes, noms vernaculaires), taxonomie (hiérarchie via AphiaID), distribution, traits, images, statut (accepté/synonyme), identifiants externes (GBIF, ITIS, etc.), informations bibliographiques. |
| **Fréquence de mise à jour** | Continue (mise à jour quotidienne par les éditeurs). Copies trimestrielles disponibles sur demande. |
| **Qualité et couverture** | Couverture mondiale, espèces marines principalement. Qualité très élevée (98% des noms vérifiés par des éditeurs taxonomiques). |
| **Priorité GSIE** | **P2 — utile**. Pertinence limitée pour l'écosystème forestier français (espèces marines). Utile uniquement pour les écosystèmes côtiers/outre-mer ou les espèces halophiles de zones littorales. |
| **Exemples d'URL** | API REST : `https://marinespecies.org/rest` — Recherche par nom : `https://marinespecies.org/rest/AphiaRecordsByName?ScientificName=Solea%20solea` — Détail par AphiaID : `https://marinespecies.org/aphia.php?p=taxdetails&id=127160` — Lien taxon : `https://marinespecies.org/aphia.php?p=taxlist&tName=Solea%20solea` |

> **Sources** : [WoRMS](https://marinespecies.org/), [Webservice](https://marinespecies.org/aphia.php?p=webservice), [About](https://marinespecies.org/about.php), [Stats](https://marinespecies.org/aphia.php?p=stats), [IMIS dataset](https://www.marinespecies.org/imis.php?dasid=8131&module=dataset), [R worrms](https://github.com/ropensci/worrms)

---

## 9. BD Forêt (IGN) — Essences forestières

| Champ | Valeur |
|---|---|
| **Nom officiel** | BD Forêt® (version 2 et version 3 en cours de déploiement) |
| **Organisme producteur** | IGN — Institut national de l'information géographique et forestière (Inventaire Forestier National) |
| **URL d'accès** | Géoplateforme : https://geoservices.ign.fr/ — Téléchargement : https://data.geopf.fr/telechargement/resource/BDFORET — WFS : `https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities` — WMS : `https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities` — WMTS : `https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities` |
| **Type d'accès** | `ogc_wms`, `ogc_wfs`, `ogc_wmts`, `file_download` |
| **Licence** | **Licence Ouverte Etalab 2.0** (depuis le 1er janvier 2021). Diffusion gratuite, réutilisation libre. |
| **Volume estimé** | Couverture nationale métropolitaine (tous départements). Nomenclature nationale de **32 postes** (types de formations végétales). Surface cartographiée : unités ≥ 0,5 ha (5 000 m²). Photo-interprétation d'images infrarouge couleur de la BD ORTHO® (période 2007–2018 pour la V2). |
| **Variables disponibles** | Type de formation végétale (32 postes nomenclature nationale : peuplements purs de principales essences, mélanges, formations préforestières, etc.), géométrie surfacique, superposable avec le Référentiel à Grande Échelle (BD TOPO® couche « Végétation »). |
| **Fréquence de mise à jour** | V2 : photo-interprétation 2007–2018, millésime variable par département. V3 : en cours de déploiement (mise à jour continue prévue). |
| **Qualité et couverture** | France métropolitaine. Référentiel géographique national de description des essences forestières. Précision : échelle 1/25 000 à 1/50 000. |
| **Priorité GSIE** | **P0 — critique**. Référentiel géographique national des essences forestières. Indispensable pour le moteur Forest Dynamics et l'application GeoSylva. Source primaire pour la cartographie des peuplements forestiers français. |
| **Exemples d'URL** | WFS GetCapabilities : `https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities` — WMTS GetCapabilities : `https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities` — Téléchargement : `https://data.geopf.fr/telechargement/resource/BDFORET` — Descriptif de contenu : `https://data.geopf.fr/annexes/ressources/documentation/DC_BDForet_2-0.pdf` |

> **Sources** : [IGN BD Forêt V2](https://inventaire-forestier.ign.fr/spip.php?article646=), [data.gouv.fr](https://www.data.gouv.fr/datasets/bd-foret-r), [INSPIRE Geoportal](https://inspire-geoportal.ec.europa.eu/srv/api/records/IGNF_BD-FORET), [cartes.gouv.fr](https://cartes.gouv.fr/aide/fr/partenaires/ign/referentiels-description-territoire/foret/bd-foret-v2/), [Géoplateforme](https://geoservices.ign.fr/)

---

## 10. IPNI — International Plant Names Index

| Champ | Valeur |
|---|---|
| **Nom officiel** | International Plant Names Index (IPNI) |
| **Organisme producteur** | Collaboration entre Royal Botanic Gardens Kew, Harvard University Herbaria, et Australian National Herbarium |
| **URL d'accès** | Portail : https://www.ipni.org/ — Recherche avancée : https://www.ipni.org/advanced-search — Service de réconciliation : https://data1.kew.org/reconciliation/reconcile/IpniName — Aide réconciliation : https://data1.kew.org/reconciliation/help |
| **Type d'accès** | `api_rest` (API beta en développement), `file_download`, `knowledge_extraction` (RDF via LSID) |
| **Licence** | **CC-BY** (Creative Commons Attribution). Données librement accessibles et réutilisables avec attribution. |
| **Volume estimé** | > 1,4 million de noms de plantes vasculaires (spermatophytes, fougères, lycophytes). Sources : Index Kewensis (> 1 million de records, 1893–2002), Gray Card Index (> 350 000 records), Australian Plant Names Index (> 63 000 records), Index Filicum (ajouté en 2004). ~150 000 records mis à jour annuellement. |
| **Variables disponibles** | Noms scientifiques (famille à infraspecies), auteurs (forme standard Brummitt & Powell), publications (lieu, date, TL-2, BPH-2), type information, statut nomenclatural, LSID (Life Sciences Identifier), données RDF. |
| **Fréquence de mise à jour** | Quotidienne (nouveaux noms ajoutés chaque jour, mise à jour du site vers 4h GMT). |
| **Qualité et couverture** | Couverture mondiale. Nomenclature des plantes vasculaires publiées depuis Linnaeus (1753). Qualité élevée mais standardisation en cours (erreurs résiduelles de l'OCR des années 1980). |
| **Priorité GSIE** | **P1 — importante**. Référentiel nomenclatural mondial pour les plantes vasculaires. Indispensable pour la validation des noms scientifiques botaniques et l'alignement avec les identifiants internationaux (LSID). Source amont de WCVP et WFO. |
| **Exemples d'URL** | Recherche : `https://www.ipni.org/?q=Quercus+robur` — RDF d'un nom : `https://www.ipni.org/n/30117681-2/rdf` — LSID : `https://www.ipni.org/urn:lsid:ipni.org:names:30117681-2` — Réconciliation : `https://data1.kew.org/reconciliation/reconcile/IpniName` |

> **Sources** : [IPNI About](https://www.ipni.org/about), [IPNI Terms](https://www.ipni.org/terms-and-conditions), [Wikidata IPNI](https://www.wikidata.org/wiki/Q922063), [Wikipedia IPNI](https://en.wikipedia.org/wiki/International_Plant_Names_Index), [kewr search_ipni](https://barnabywalker.github.io/kewr/reference/search_ipni.html)

---

## 11. WCVP — World Checklist of Vascular Plants

| Champ | Valeur |
|---|---|
| **Nom officiel** | World Checklist of Vascular Plants (WCVP), anciennement World Checklist of Selected Plant Families (WCSP) |
| **Organisme producteur** | Royal Botanic Gardens, Kew (RBG Kew) — initié par Rafaël Govaerts en 1988 |
| **URL d'accès** | POWO (Plants of the World Online) : https://powo.science.kew.org/ — About WCVP : https://powo.science.kew.org/about-wcvp — Téléchargement (versionné) : https://sftp.kew.org/pub/data-repositories/WCVP/ — GBIF : https://doi.org/10.15468/6h8ucr — Kew repository : https://kew.iro.bl.uk/concern/datasets/042a9f96-41a9-4896-9e80-c89586e68363 |
| **Type d'accès** | `api_rest` (via kewr / POWO), `file_download` |
| **Licence** | **CC-BY 3.0** (selon le dépôt Kew). Sur GBIF : CC-BY 4.0. |
| **Volume estimé** | Avril 2021 : **1 383 297 noms de plantes**, 996 093 au rang espèce, représentant **342 953 espèces vasculaires acceptées**. Version v14 (28 mai 2025) : fichier de ~100 MB. Inclut 400 341 noms acceptés, 744 145 synonymes, 3 610 hybrides artificiels, 42 619 noms non placés. |
| **Variables disponibles** | Nomenclature (noms acceptés, synonymes, hybrides), taxonomie (famille, genre, espèce, infraspecies), bibliographie (auteur, lieu et date de publication), distribution géographique, statut taxonomique (accepté/synonyme/non placé), identifiants IPNI. |
| **Fréquence de mise à jour** | Continue (base mise à jour quotidiennement). Refresh sur POWO chaque lundi. Versions téléchargeables (v1, v2... v14) avec timestamp. |
| **Qualité et couverture** | Couverture mondiale, plantes vasculaires uniquement. Qualité très élevée (expert-reviewed, peer-reviewed). Backbone taxonomique par défaut de World Flora Online (WFO). Source principale du Catalogue of Life pour les plantes. |
| **Priorité GSIE** | **P1 — importante**. Consensus taxonomique mondial pour les plantes vasculaires. Essentiel pour valider les noms acceptés des espèces forestières françaises dans un contexte global. |
| **Exemples d'URL** | POWO : `https://powo.science.kew.org/` — Téléchargement v14 : `https://kew.iro.bl.uk/concern/datasets/042a9f96-41a9-4896-9e80-c89586e68363` — GBIF DwC-A : `https://doi.org/10.15468/6h8ucr` — SFTP : `https://sftp.kew.org/pub/data-repositories/WCVP/` |

> **Sources** : [About WCVP](https://powo.science.kew.org/about-wcvp), [Nature Scientific Data](https://www.nature.com/articles/s41597-021-00997-6), [Kew repository v14](https://kew.iro.bl.uk/concern/datasets/042a9f96-41a9-4896-9e80-c89586e68363), [GBIF WCVP](https://www.gbif.org/dataset/f382f0ce-323a-4091-bb9f-add557f3a9a2), [kewr download_wcvp](https://barnabywalker.github.io/kewr/reference/download_wcvp.html)

---

## 12. WFO — World Flora Online

| Champ | Valeur |
|---|---|
| **Nom officiel** | World Flora Online (WFO) — WFO Plant List |
| **Organisme producteur** | Consortium World Flora Online (RBG Kew, Missouri Botanical Garden, et dizaines de Taxonomic Expert Networks — TENs) |
| **URL d'accès** | WFO Plant List : https://wfoplantlist.org/ — Portail WFO : https://www.worldfloraonline.org/ — Téléchargement : https://www.worldfloraonline.org/downloadData — Zenodo : https://doi.org/10.5281/zenodo.18007552 |
| **Type d'accès** | `file_download` |
| **Licence** | CC-BY (données taxonomiques). |
| **Volume estimé** | Couvre l'ensemble des **~400 000 espèces** de plantes vasculaires et bryophytes du monde. Release 2024-06 disponible sur Zenodo. Versions statiques semestrielles (21 juin et 21 décembre). |
| **Variables disponibles** | Nomenclature (noms acceptés, synonymes), taxonomie (hiérarchie complète : familles, genres, espèces), liens vers IPNI (vasculaires) et Tropicos (bryophytes), identifiants WFO, classification phylogénétique. |
| **Fréquence de mise à jour** | Semestrielle (21 juin et 21 décembre). Working draft continu sur le portail. |
| **Qualité et couverture** | Couverture mondiale. Toutes les plantes : bryophytes, ptéridophytes, gymnospermes, angiospermes. Backbone taxonomique basé sur WCVP pour les plantes vasculaires + Tropicos pour les bryophytes. Maintenu par les TENs (réseaux d'experts taxonomiques). |
| **Priorité GSIE** | **P2 — utile**. Consensus taxonomique mondial pour les plantes. Moins détaillé que WCVP pour les plantes vasculaires, mais couvre également les bryophytes. Utile pour l'alignement global et la résolution de noms. |
| **Exemples d'URL** | WFO Plant List : `https://wfoplantlist.org/` — Téléchargement : `https://www.worldfloraonline.org/downloadData` — Zenodo (latest) : `https://doi.org/10.5281/zenodo.18007552` — Release 2024-06 : `https://zenodo.org/records/12171908` |

> **Sources** : [WFO Plant List](https://wfoplantlist.org/), [WFO Download](https://www.worldfloraonline.org/downloadData), [WFO About](https://about.worldfloraonline.org/faqs), [WFO June 2024](https://about.worldfloraonline.org/june-2024-release), [WFO December 2024](https://about.worldfloraonline.org/december-2024-release), [Zenodo 2024-06](https://zenodo.org/records/12171908)

---

## Synthèse des priorités

| Source | Type d'accès | Licence | Priorité | Rôle dans GSIE |
|---|---|---|---|---|
| **TAXREF** | api_rest, file_download | CC-BY 4.0 | **P0** | Référentiel taxonomique national (France) |
| **GBIF** | api_rest, file_download | CC0 / CC-BY 4.0 | **P0** | Occurrences mondiales + backbone taxonomique |
| **INPN** | api_rest, file_download | Licence Ouverte SINP | **P0** | Occurrences nationales validées (France) |
| **BDTFX (Tela Botanica)** | api_rest, file_download | CC BY-SA 4.0 | **P0** | Référentiel flore vasculaire France (détail botanique) |
| **BD Forêt (IGN)** | ogc_wms, ogc_wfs, ogc_wmts, file_download | Licence Ouverte Etalab 2.0 | **P0** | Cartographie essences forestières (France) |
| **BDNFF / ISFF** | file_download, knowledge_extraction | CC BY-SA 4.0 | **P1** | Nomenclature historique flore France |
| **Catalogue of Life** | api_rest, file_download | CC-BY 4.0 | **P1** | Taxonomie mondiale (alignement international) |
| **IPNI** | api_rest (beta), file_download | CC-BY | **P1** | Nomenclature mondiale plantes vasculaires |
| **WCVP** | api_rest, file_download | CC-BY 3.0/4.0 | **P1** | Consensus taxonomique mondial plantes vasculaires |
| **ITIS** | api_rest, file_download | CC0 1.0 | **P2** | Taxonomie internationale (focus Amérique du Nord) |
| **WoRMS** | api_rest, file_download | CC-BY 4.0 | **P2** | Espèces marines (pertinence limitée forêt) |
| **WFO** | file_download | CC-BY | **P2** | Consensus mondial plantes (vasculaires + bryophytes) |

---

## Recommandations d'intégration GSIE

### Architecture d'intégration proposée

1. **Couche P0 (intégration immédiate)** : TAXREF comme référentiel taxonomique pivot pour toutes les espèces françaises. BDTFX comme couche botanique détaillée pour la flore vasculaire. BD Forêt pour la cartographie des essences. GBIF + INPN pour les occurrences.

2. **Couche P1 (intégration prioritaire)** : IPNI + WCVP pour la validation nomenclaturale mondiale et l'alignement des noms acceptés. Catalogue of Life pour la résolution de synonymies internationales. BDNFF pour l'historique nomenclatural.

3. **Couche P2 (intégration secondaire)** : ITIS, WoRMS, WFO pour des cas d'usage spécifiques (alignement international, espèces marines littorales, bryophytes).

### Flux de données recommandé

```
IPNI (nomenclature mondiale)
  ↓
WCVP (consensus taxonomique vasculaire)
  ↓
BDNFF/BDTFX (spécialisation France)
  ↓
TAXREF (intégration nationale multi-taxons)
  ↓
GBIF + INPN (occurrences)
  ↓
BD Forêt (cartographie essences forestières)
```

### Points d'attention

- **Indisponibilité temporaire MNHN** : Depuis septembre 2025, une cyberattaque a affecté les services du MNHN. Les API TAXREF et INPN peuvent être temporairement indisponibles. Utiliser la [page de téléchargement temporaire PatriNat](https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353).
- **Données sensibles** : Les occurrences d'espèces sensibles (au sens de l'article D411-21-3 du code de l'environnement) ne sont accessibles que via une procédure d'extraction SINP spécifique avec licence restrictive.
- **Limites de téléchargement** : OpenObs limite les exports à 1 million de données par téléchargement. Pour des volumétries supérieures, utiliser le formulaire dédié.
- **Alignement taxonomique** : Les identifiants croisés (TAXREF ↔ GBIF ↔ ITIS ↔ WoRMS) sont disponibles dans TAXREF via les codes alternatifs. WCVP et WFO utilisent les IPNI IDs comme pivot nomenclatural.
