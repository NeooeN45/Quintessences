# Sources — D6 Faune (vertébrés)

| Champ | Valeur |
|---|---|
| **Domaine** | Faune (vertébrés) |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## Sommaire

1. [INPN — Données d'observation et de suivi sur les espèces (OpenObs)](#1-inpn--données-dobservation-et-de-suivi-sur-les-espèces-openobs)
2. [INPN — Base de Connaissance sur les Statuts des espèces (BDC-Statuts)](#2-inpn--base-de-connaissance-sur-les-statuts-des-espèces-bdc-statuts)
3. [INPN — Espèces protégées et réglementées](#3-inpn--espèces-protégées-et-réglementées)
4. [TAXREF — Référentiel taxonomique national](#4-taxref--référentiel-taxonomique-national)
5. [GBIF — Occurrences (API internationale)](#5-gbif--occurrences-api-internationale)
6. [GBIF France — Portail national et IPT](#6-gbif-france--portail-national-et-ipt)
7. [LPO — Faune-France](#7-lpo--faune-france)
8. [LPO — Atlas des Oiseaux de France (Oiseaux de France)](#8-lpo--atlas-des-oiseaux-de-france-oiseaux-de-france)
9. [SHF — Atlas des reptiles et amphibiens de France](#9-shf--atlas-des-reptiles-et-amphibiens-de-france)
10. [SHF — POPAmphibiens / POPReptile (suivis temporels)](#10-shf--popamphibiens--popreptile-suivis-temporels)
11. [SFEPM — Observatoire National des Mammifères (ONM)](#11-sfepm--observatoire-national-des-mammifères-onm)
12. [SFEPM — Atlas des Mammifères sauvages de France](#12-sfepm--atlas-des-mammifères-sauvages-de-france)
13. [UICN France / PatriNat — Liste rouge des espèces menacées en France](#13-uicn-france--patrinat--liste-rouge-des-espèces-menacées-en-france)
14. [CRBPO / MNHN — STOC (Suivi Temporel des Oiseaux Communs)](#14-crbpo--mnhn--stoc-suivi-temporel-des-oiseaux-communs)
15. [INPN / SINP — Guide technique sensibilité des données à la diffusion](#15-inpn--sinp--guide-technique-sensibilité-des-données-à-la-diffusion)
16. [Synthèse — Enjeux de confidentialité pour GSIE](#16-synthèse--enjeux-de-confidentialité-pour-gsie)

---

## 1. INPN — Données d'observation et de suivi sur les espèces (OpenObs)

| Champ | Valeur |
|---|---|
| **Nom officiel** | INPN — Données d'observation et de suivi sur les espèces (OpenObs) |
| **Organisme** | UAR PatriNat (OFB-MNHN-CNRS-IRD), dans le cadre du SINP |
| **URL d'accès** | https://openobs.mnhn.fr/ |
| **Type d'accès** | `api_rest` + `file_download` |
| **Licence** | Ouverte / Open Data (respect des conditions des producteurs ; voir métadonnées par jeu de données) |
| **Volume estimé** | Des dizaines de millions d'occurrences (toutes espèces confondues) ; les données d'observation alimentent également GBIF |
| **Variables** | Espèces, occurrences (taxon, date, lieu, observateur), statuts de validation SINP |
| **Données sensibles** | **Oui.** Les données sensibles à la diffusion sont consultables sur OpenObs après application d'un **floutage géographique** défini par le référentiel national de sensibilité. Les données non floutées (précision exacte) nécessitent une demande d'extraction SINP : https://inpn.mnhn.fr/espece/extraction-sinp/preambule |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — source nationale de référence pour les occurrences d'espèces |
| **Exemples d'URL vérifiées** | Portail : https://openobs.mnhn.fr/ — API développeur : https://openobs.mnhn.fr/developer — FAQ (sensibilité) : https://openobs.mnhn.fr/faq — Demande extraction (données sensibles) : https://inpn.mnhn.fr/espece/extraction-sinp/preambule — Jeu de données sur data.gouv.fr : https://www.data.gouv.fr/datasets/inpn-donnees-dobservation-et-de-suivi-sur-les-especes |

### Notes techniques

- L'API RESTful d'OpenObs permet de filtrer par date et lieu d'observation.
- Les données sont également diffusées sur GBIF (https://www.gbif.org).
- La page de téléchargement temporaire des référentiels INPN est accessible via PatriNat : https://www.patrinat.fr/fr/referentiels-et-standards-6041
- L'accès aux données sensibles (localisation précise d'espèces protégées) passe par une procédure d'extraction SINP, soumise à autorisation.

---

## 2. INPN — Base de Connaissance sur les Statuts des espèces (BDC-Statuts)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Base de connaissance sur les statuts des espèces (BDC-Statuts) |
| **Organisme** | UAR PatriNat (OFB-MNHN-CNRS-IRD) — INPN |
| **URL d'accès** | https://inpn.mnhn.fr/telechargement/referentielEspece/bdc-statuts-especes |
| **Type d'accès** | `file_download` + `api_rest` (via API TAXREF : https://taxref.mnhn.fr/taxref-web/api/doc) |
| **Licence** | Ouverte (référentiel public INPN) |
| **Volume estimé** | > 60 000 taxons à statut, issus de 142 textes juridiques recensés (toutes espèces : faune + flore + fonge) |
| **Variables** | Statuts de protection (arrêtés nationaux, directives européennes, conventions internationales), réglementations (introduction, commerce, chasse, nuisance), listes rouges UICN France, statuts de conservation |
| **Données sensibles** | **Non directement** — la BDC-Statuts ne contient pas de localisations. Elle indique quelles espèces sont protégées/sensibles, ce qui est **essentiel pour GSIE** afin de croiser avec les occurrences et déterminer quelles données d'occurrence doivent être floutées |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — référentiel national des statuts juridiques et de conservation |
| **Exemples d'URL vérifiées** | Téléchargement BDC-Statuts : https://inpn.mnhn.fr/telechargement/referentielEspece/bdc-statuts-especes — Documentation API TAXREF : https://taxref.mnhn.fr/taxref-web/api/doc — Miroir GeoNature (versions archivées) : https://geonature.fr/data/inpn/taxonomie/ (ex. `BDC-STATUTS-v18.zip`, 32 Mo, février 2025) |

### Notes techniques

- La méthodologie d'élaboration est décrite par Gargominy & Demonet (2013).
- La BDC-Statuts est mise à jour annuellement, en synchronisation avec les versions de TAXREF.
- Version la plus récente identifiée : v18 (février 2025), ~32 Mo compressé.

---

## 3. INPN — Espèces protégées et réglementées

| Champ | Valeur |
|---|---|
| **Nom officiel** | INPN — Espèces protégées et réglementées |
| **Organisme** | UAR PatriNat (OFB-MNHN-CNRS-IRD) — MNHN |
| **URL d'accès** | https://inpn.mnhn.fr/telechargement/referentielEspece/reglementation |
| **Type d'accès** | `file_download` |
| **Licence** | Ouverte (Open Data — data.gouv.fr) |
| **Volume estimé** | 142 textes juridiques → > 60 000 taxons à statut (toutes espèces) ; pour les vertébrés : mammifères, oiseaux, reptiles, amphibiens, poissons concernés par les arrêtés de protection |
| **Variables** | Espèces protégées (arrêtés nationaux), espèces chassables, espèces nuisibles, espèces domestiques, annexes directives européennes (Oiseaux, Habitats), conventions internationales (CITES, Berne, Bonn) |
| **Données sensibles** | **Non** — référentiel de statuts juridiques, sans localisation. Indique quelles espèces sont protégées, donc indirectement quelles occurrences sont sensibles |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — référentiel juridique indispensable pour le moteur de confidentialité GSIE |
| **Exemples d'URL vérifiées** | Page INPN : https://inpn.mnhn.fr/telechargement/referentielEspece/reglementation — data.gouv.fr : https://www.data.gouv.fr/datasets/inpn-especes-protegees-et-reglementees — OpenDataSoft : https://public.opendatasoft.com/explore/dataset/especes-protegees-et-reglementees-referentiel/api/ |

### Notes techniques

- Les textes principaux pour les vertébrés : arrêté du 23/04/2007 (mammifères protégés), arrêté du 29/10/2009 (oiseaux protégés), arrêtés sur les reptiles/amphibiens, arrêté du 08/12/1988 (poissons protégés).
- Arrêté du 06/01/2020 : liste des espèces à la protection desquelles il ne peut être dérogé qu'après avis du CNPN.
- Base complémentaire « Taxa Fauna Flora » (TFF) : http://droitnature.free.fr/Bdd/AccueilTFF.shtml — base associative recensant les statuts juridiques des espèces en France.

---

## 4. TAXREF — Référentiel taxonomique national

| Champ | Valeur |
|---|---|
| **Nom officiel** | TAXREF — Référentiel nomenclatural et taxonomique national |
| **Organisme** | UAR PatriNat (OFB-MNHN-CNRS-IRD) — MNHN / INPN |
| **URL d'accès** | https://taxref.mnhn.fr/taxref-web/accueil |
| **Type d'accès** | `api_rest` + `file_download` |
| **Licence** | Ouverte (référentiel public INPN) |
| **Volume estimé** | ~190 000 espèces (tous taxons confondus : faune, flore, fonge) ; version v18 (2025), ~56 Mo compressé |
| **Variables** | Noms scientifiques, noms vernaculaires, synonymes, classification taxonomique, statuts (endémisme, introduction), codes TAXREF (cd_nom, cd_ref, cd_taxsup) |
| **Données sensibles** | **Non** — référentiel taxonomique, sans occurrences |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — référentiel taxonomique de base pour tous les moteurs GSIE traitant des espèces |
| **Exemples d'URL vérifiées** | Portail TAXREF : https://taxref.mnhn.fr/taxref-web/accueil — Documentation API : https://taxref.mnhn.fr/taxref-web/api/doc — IPT GBIF France : https://ipt.gbif.fr/resource?r=taxref — data.gouv.fr : https://www.data.gouv.fr/datasets/referentiel-taxonomique-taxref — Miroir GeoNature : https://geonature.fr/data/inpn/taxonomie/ (ex. `TAXREF_v18_2025.zip`, 56 Mo) |

### Notes techniques

- TAXREF est le référentiel unique pour la France ; il liste et organise les noms scientifiques de l'ensemble des êtres vivants recensés sur le territoire.
- Les codes TAXREF (cd_nom, cd_ref) sont la clé de jointure universelle entre toutes les bases de données naturalistes françaises (INPN, GBIF France, Faune-France, SHF, SFEPM).
- Version la plus récente identifiée : v18 (janvier 2025).

---

## 5. GBIF — Occurrences (API internationale)

| Champ | Valeur |
|---|---|
| **Nom officiel** | GBIF — Global Biodiversity Information Facility (Occurrence API) |
| **Organisme** | GBIF Secretariat (Copenhague, Danemark) — réseau international |
| **URL d'accès** | https://www.gbif.org/ — API : https://api.gbif.org/v1/ |
| **Type d'accès** | `api_rest` + `file_download` (téléchargement asynchrone de gros volumes) |
| **Licence** | Variable selon les jeux de données (majorité en CC-BY 4.0 ou CC0) ; les données INPN sur GBIF respectent les licences des producteurs |
| **Volume estimé** | > 2,6 milliards d'occurrences mondiales (toutes espèces) ; pour la France : des dizaines de millions d'occurrences, dont une part majeure provient de l'INPN/SINP |
| **Variables** | Espèces, occurrences (taxon, date, coordonnées, lieu), identifiants Darwin Core, provenance du jeu de données |
| **Données sensibles** | **Oui, partiellement.** GBIF applique un floutage automatique des coordonnées pour les occurrences d'espèces sensibles (selon les règles du pays producteur). Les données françaises sensibles héritent du floutage SINP/INPN. Les coordonnées exactes ne sont pas accessibles publiquement |
| **Couverture** | Mondiale (France incluse via GBIF France) |
| **Priorité GSIE** | **P1** — source complémentaire à l'INPN pour les occurrences ; utile pour les espèces migratrices et la connectivité internationale |
| **Exemples d'URL vérifiées** | Portail : https://www.gbif.org/ — API Occurrence : https://www.gbif.org/fr/developer/occurrence — Documentation OpenAPI : https://techdocs.gbif.org/en/openapi/ — API Occurrence v1 : https://techdocs.gbif.org/en/openapi/v1/occurrence — Débogueur cartes : https://api.gbif.org/v2/map/debug/ol/ |

### Notes techniques

- L'API occurrence permet la recherche paginée (max 300 enregistrements par page).
- Le téléchargement asynchrone permet d'extraire de gros volumes filtrés (par pays, taxon, date).
- Les données françaises sur GBIF proviennent majoritairement de l'INPN via le SINP et GBIF France.

---

## 6. GBIF France — Portail national et IPT

| Champ | Valeur |
|---|---|
| **Nom officiel** | GBIF France — Portail national français |
| **Organisme** | GBIF France (porté par le MNHN / PatriNat, en lien avec le SINP) |
| **URL d'accès** | https://www.gbif.fr/ |
| **Type d'accès** | `file_download` (IPT) + `api_rest` (via API GBIF internationale) |
| **Licence** | Variable selon les jeux de données (majorité CC-BY 4.0) |
| **Volume estimé** | Jeux de données français publiés sur GBIF : atlas, inventaires, suivis ; inclut l'Atlas des oiseaux nicheurs, l'Atlas des ongulés/lagomorphes, TAXREF, etc. |
| **Variables** | Occurrences (Darwin Core), métadonnées EML, ressources taxonomiques |
| **Données sensibles** | **Oui** — hérite du référentiel de sensibilité SINP pour les données françaises |
| **Couverture** | France (métropole + outre-mer) + données françaises collectées hors territoire |
| **Priorité GSIE** | **P1** — portail de publication des jeux de données français au format Darwin Core |
| **Exemples d'URL vérifiées** | Portail GBIF France : https://www.gbif.fr/ — IPT GBIF France : https://ipt-pndb.gbif.fr/ — IPT TAXREF : https://ipt.gbif.fr/resource?r=taxref — Atlas oiseaux nicheurs (GBIF) : https://www.gbif.org/dataset/93773ae8-f7c4-44b3-8793-761bb0561050 — Atlas ongulés/lagomorphes (DOI) : https://doi.org/10.15468/dwnptk |

### Notes techniques

- GBIF France s'appuie sur le SINP pour la collecte et la standardisation des données françaises.
- L'IPT (Integrated Publishing Toolkit) est l'outil de publication des jeux de données au format Darwin Core Archive (DwC-A).

---

## 7. LPO — Faune-France

| Champ | Valeur |
|---|---|
| **Nom officiel** | Faune-France — Portail naturaliste national |
| **Organisme** | LPO France (Ligue pour la Protection des Oiseaux), en collaboration avec un réseau d'associations partenaires |
| **URL d'accès** | https://www.faune-france.org/ |
| **Type d'accès** | `file_download` (export via interface) + `api_rest` (API Biolovision, accès restreint) |
| **Licence** | Données soumises aux conditions d'utilisation de la plateforme ; diffusion publique limitée. Accès aux données brutes sur demande / convention |
| **Volume estimé** | > 150 millions de données (toutes espèces : oiseaux, mammifères, amphibiens, reptiles) — source : LPO, 2025 |
| **Variables** | Espèces, occurrences (taxon, date, lieu, observateur), listes complètes, protocoles (STOC, SHOC, EPOC, LIMAT, Wetlands, Rapaces), photos, sons |
| **Données sensibles** | **Oui.** Les espèces protégées/sensibles sont floutées publiquement. L'accès aux données précises nécessite une convention avec la LPO ou les associations partenaires régionales. Les données remontent au SINP/INPN selon les flux conventionnés |
| **Couverture** | France (métropole + outre-mer via Faune-Guyane, etc.) |
| **Priorité GSIE** | **P0** — plus grande base de données naturalistes participative de France |
| **Exemples d'URL vérifiées** | Portail : https://www.faune-france.org/ — Page LPO Faune-France : https://www.lpo.fr/la-lpo-en-actions/connaissance-des-especes-sauvages/faune-france — Article 150M données (2025) : https://www.lpo.fr/qui-sommes-nous/toutes-nos-actualites/articles/actus-2025/faune-france-plus-de-150-millions-de-donnees-collectees — Application NaturaList : https://www.faune-france.org/index.php?m_id=20015 |

### Notes techniques

- Faune-France utilise le logiciel Biolovision (VisioNature) ; l'API Biolovision permet un accès programmatique aux données (accès restreint, conventionné).
- Les déclinaisons régionales existent (Faune-IDF, Faune-AuRA, Faune-Guyane, etc.) avec leurs propres portails.
- Les données saisies via NaturaList (application mobile) alimentent Faune-France en temps réel.
- Les données Faune-France alimentent l'Atlas des Oiseaux de France et remontent au SINP.

---

## 8. LPO — Atlas des Oiseaux de France (Oiseaux de France)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Oiseaux de France (ODF) — Atlas des oiseaux nicheurs et hivernants de France métropolitaine et d'Outre-mer |
| **Organisme** | LPO France, en collaboration avec SEOF (Société d'Études Ornithologiques de France) et MNHN |
| **URL d'accès** | https://www.oiseauxdefrance.org/ |
| **Type d'accès** | `publication_text` (atlas digital, fiches espèces) + `file_download` (jeux de données sous-jents sur GBIF) |
| **Licence** | Atlas digital : accès gratuit public. Jeux de données sous-jacents : licences variables (voir GBIF) |
| **Volume estimé** | 359 espèces (atlas 2009-2012) ; actualisation 2021-2024 en cours ; maillage 10×10 km ; données issues de Faune-France (~50M+ données) et des protocoles STOC, SHOC, EPOC, LIMAT, Wetlands, Observatoire Rapaces |
| **Variables** | Répartition par maille, indices de nidification, abondance, tailles de populations, tendances démographiques, phénologie (reproduction, migration, hivernage) |
| **Données sensibles** | **Oui.** Les espèces sensibles (rapaces nicheurs rares, etc.) sont affichées à maille floutée. Les données brutes précises ne sont pas accessibles publiquement |
| **Couverture** | France métropolitaine + outre-mer |
| **Priorité GSIE** | **P1** — source de référence pour la répartition et les tendances de l'avifaune française |
| **Exemples d'URL vérifiées** | Plateforme ODF : https://www.oiseauxdefrance.org/ — Page LPO Atlas : https://www.lpo.fr/la-lpo-en-actions/connaissance-des-especes-sauvages/atlas-des-oiseaux-de-france — GitHub (code open source, AGPL v3) : https://github.com/lpoaura/BirdAtlasOfFrance — Atlas 2009-2012 sur GBIF : https://www.gbif.org/dataset/93773ae8-f7c4-44b3-8793-761bb0561050 — Ouvrage de référence (2015) : https://www.delachauxetniestle.com/livre/atlas-des-oiseaux-de-france-metropolitaine/9782603018781 |

### Notes techniques

- L'atlas 2009-2012 a été publié en 2015 (LPO / SEOF / MNHN, Delachaux & Niestlé, 1408 p., 2 volumes).
- L'actualisation 2021-2024 produit un atlas digital permanent, mis à jour en temps réel.
- Le code de la plateforme est open source (AGPL v3), développé par LPO AuRA.
- Les données sous-jacentes (inventaire 2009-2012) sont publiées sur GBIF avec DOI.

---

## 9. SHF — Atlas des reptiles et amphibiens de France

| Champ | Valeur |
|---|---|
| **Nom officiel** | Atlas des reptiles et amphibiens de France |
| **Organisme** | Société Herpétologique de France (SHF), avec le soutien du ministère de l'Environnement et du MNHN |
| **URL d'accès** | https://atlas.lashf.org/ |
| **Type d'accès** | `publication_text` (atlas en ligne, fiches espèces) + `file_download` (données via SINP/INPN) |
| **Licence** | Atlas en ligne : accès public. Données sous-jacentes : soumises aux conditions SINP/INPN |
| **Volume estimé** | 73 espèces autochtones (34 amphibiens + 39 reptiles) + 8 espèces introduites ; 179 426 données d'observation (atlas 2012), dont 135 226 depuis 1990 ; > 6 000 observateurs |
| **Variables** | Répartition par espèce (cartes de mailles), distribution spatiale et altitudinale, état de conservation, liste rouge amphibiens/reptiles |
| **Données sensibles** | **Oui.** Plusieurs espèces d'amphibiens et reptiles sont protégées (arrêtés nationaux). Les localisations précises sont floutées. La SHF est depuis 2024 en charge de la **validation nationale des données herpétologiques du SINP** avec l'UMS PatriNat |
| **Couverture** | France métropolitaine (Corse comprise) |
| **Priorité GSIE** | **P1** — source de référence pour l'herpétofaune française |
| **Exemples d'URL vérifiées** | Atlas en ligne : https://atlas.lashf.org/ — Page Reptiles : https://atlas.lashf.org/groupe/Reptiles — Page Amphibiens : https://atlas.lashf.org/groupe/Amphibiens — Page données SHF : https://lashf.org/donnees/ — Ouvrage (2012, MNHN) : https://sciencepress.mnhn.fr/fr/collections/inventaires-biodiversite/atlas-des-amphibiens-et-reptiles-de-france |

### Notes techniques

- Trois atlas publiés : 1978, 1989, 2012 (le plus récent).
- La SHF est gestionnaire de la base de données herpétologiques la plus complète de France.
- Depuis 2024, la SHF est validatrice nationale des données herpétologiques du SINP (avec PatriNat).
- Les données opportunistes sont saisies via GeoNature (plateformes régionales).

---

## 10. SHF — POPAmphibiens / POPReptile (suivis temporels)

| Champ | Valeur |
|---|---|
| **Nom officiel** | POPAmphibiens / POPReptile — Observatoire de l'herpétofaune (suivis standardisés) |
| **Organisme** | Société Herpétologique de France (SHF), dans le cadre du programme national de surveillance de la biodiversité terrestre (PatriNat / OFB) |
| **URL d'accès** | https://lashf.org/pop-amphibien/ — https://lashf.org/pop-reptile/ |
| **Type d'accès** | `file_download` (saisie via GeoNature régional) + `publication_text` (bilans d'analyse publiés tous les 2 ans) |
| **Licence** | Données SINP / conditions SHF ; bilans d'analyse en accès libre |
| **Volume estimé** | Données protocolées (3 passages/an pour POPAmphibiens ; suivis standardisés pour POPReptile) ; volume exact non publié publiquement, en croissance continue |
| **Variables** | Espèces, abondance, tendances temporelles des populations, stades de développement (amphibiens : pontes, larves, adultes) |
| **Données sensibles** | **Oui** — les sites de suivi d'espèces protégées (tortues, salamandres rares, etc.) ne sont pas diffusés publiquement |
| **Couverture** | France métropolitaine (réseau de sites suivis par des bénévoles) |
| **Priorité GSIE** | **P2** — suivi temporel spécialisé herpétofaune ; utile pour les tendances de populations |
| **Exemples d'URL vérifiées** | POPAmphibien : https://lashf.org/pop-amphibien/ — POPReptile : https://lashf.org/pop-reptile/ — Bilan national POPAmphibien 2021 : https://www.biodiversite-centrevaldeloire.fr/ressources/base-documentaire/bilan-de-l-analyse-du-suivi-pop-amphibien-l-echelle-nationale-2021 — GeoNature ÎdF (POPAmphibien) : https://geonature.arb-idf.fr/popamphibien |

### Notes techniques

- La saisie des données POPReptile et POPAmphibiens se fait exclusivement via les plateformes GeoNature régionales (plus de saisie Excel acceptée).
- Les analyses sont coordonnées par la SHF tous les 2 ans.
- POPAmphibiens : 3 passages par saison (dont au moins un nocturne) pour observer les différentes espèces et stades de développement.

---

## 11. SFEPM — Observatoire National des Mammifères (ONM)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Observatoire National des Mammifères (ONM) |
| **Organisme** | SFEPM (Société Française pour l'Étude et la Protection des Mammifères) |
| **URL d'accès** | https://observatoire-mammiferes.fr/ |
| **Type d'accès** | `file_download` (visualisation cartographique, exports) + `publication_text` (atlas, rapports) |
| **Licence** | Données SFEPM / conditions d'utilisation de l'ONM ; accès public aux cartes de répartition (maille 10×10 km) |
| **Volume estimé** | Données d'occurrence agrégées à minima à la maille 10×10 km pour l'ensemble des mammifères sauvages de France (métropole + outre-mer) ; volume exact non publié publiquement |
| **Variables** | Espèces, occurrences (maille 10×10 km), statuts, tendances, indicateurs |
| **Données sensibles** | **Oui.** Les mammifères protégés (chiroptères, loutre, certains carnivores) ont des localisations floutées. L'ONM agrège des données à maille 10×10 km pour la diffusion publique |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P1** — source de référence pour les mammifères sauvages de France |
| **Exemples d'URL vérifiées** | Portail ONM : https://observatoire-mammiferes.fr/ — Présentation : https://observatoire-mammiferes.fr/presentation — Plaquette ONM (PDF) : https://www.sfepm.org/sites/default/files/inline-files/ONM_plaquette-de-presentation.pdf — Page SFEPM Atlas : https://www.sfepm.org/atlas |

### Notes techniques

- L'ONM a été développé depuis 2018 par la SFEPM.
- Il mutualise les connaissances issues des associations naturalistes, des réseaux scientifiques et des institutions publiques.
- Les données alimentent le SINP et contribuent aux listes rouges, à la Trame verte et bleue, et aux atlas nationaux.
- La plateforme utilise GeoNature-atlas (développé par le Parc national des Écrins).

---

## 12. SFEPM — Atlas des Mammifères sauvages de France

| Champ | Valeur |
|---|---|
| **Nom officiel** | Atlas des Mammifères sauvages de France (multi-volumes) |
| **Organisme** | SFEPM (Société Française pour l'Étude et la Protection des Mammifères) |
| **URL d'accès** | https://www.sfepm.org/atlas |
| **Type d'accès** | `publication_text` (ouvrages publiés) + `file_download` (jeux de données sur GBIF) |
| **Licence** | Ouvrages : droits d'auteur (éditions SFEPM/MNHN). Jeux de données sur GBIF : licences variables |
| **Volume estimé** | Volume 1 : Mammifères marins (16 carnivores, 53 cétartiodactyles, 2 siréniens) ; Volume 2 : Ongulés et Lagomorphes (20 ongulés + 8 lagomorphes) ; Volume 3 : Carnivores et Primates (33 carnivores + 10 primates) ; Volume en cours : Chiroptères (> 175 espèces, métropole + outre-mer). Données compilées 2000-2018+ |
| **Variables** | Répartition par espèce (cartes de mailles), statut de conservation, évolution des populations |
| **Données sensibles** | **Oui.** Les localisations de chiroptères (gîtes), de carnivores rares (loup, lynx, ours) et de certains mammifères marins sont sensibles et floutées |
| **Couverture** | France (métropole + outre-mer) + eaux françaises (mammifères marins) |
| **Priorité GSIE** | **P1** — source de référence pour la répartition des mammifères |
| **Exemples d'URL vérifiées** | Page Atlas SFEPM : https://www.sfepm.org/atlas — Volume 1 (Mammifères marins) : https://www.sfepm.org/atlas — Volume 2 (Ongulés/Lagomorphes) sur GBIF : https://doi.org/10.15468/dwnptk — Page Atlas des Mammifères de France : https://www.sfepm.org/atlas-des-mammiferes-de-france.html |

### Notes techniques

- Le premier (et unique avant cette série) atlas des mammifères de France datait de 1984 (SFEPM).
- La nouvelle série est publiée en volumes thématiques (marins, ongulés/lagomorphes, carnivores/primates, chiroptères, rongeurs/petits mammifères).
- Les données sous-jacentes (atlas ongulés/lagomorphes 2000-2020) sont publiées sur GBIF avec DOI.
- Les données remontent via l'ONM au SINP.

---

## 13. UICN France / PatriNat — Liste rouge des espèces menacées en France

| Champ | Valeur |
|---|---|
| **Nom officiel** | Liste rouge des espèces menacées en France |
| **Organisme** | Comité français de l'UICN + UAR PatriNat (OFB-MNHN-CNRS-IRD) |
| **URL d'accès** | https://uicn.fr/especes/liste-rouge-france/ — résultats détaillés sur INPN |
| **Type d'accès** | `publication_text` (rapports, fiches, PDF) + `file_download` (résultats synthétiques, tableaux) |
| **Licence** | Ouverte (résultats publics) ; citation requise : « UICN Comité français, OFB & MNHN » |
| **Volume estimé** | 17 367 espèces évaluées (toutes espèces : faune + flore) ; 2 903 espèces menacées ; 189 espèces disparues. Pour les vertébrés : Mammifères (2017), Oiseaux (2016), Reptiles/Amphibiens (2015), Poissons d'eau douce (2019), Requins/raies/chimères (2013) — métropole. Évaluations outre-mer également disponibles |
| **Variables** | Catégorie UICN (EX, RE, CR, EN, VU, NT, LC, DD), critères d'évaluation, tendances, statut de menace |
| **Données sensibles** | **Non** — la liste rouge est un statut de conservation, pas une localisation. Elle indique quelles espèces sont menacées, ce qui croisé avec les occurrences permet d'identifier les données sensibles |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — référentiel national du statut de conservation des espèces |
| **Exemples d'URL vérifiées** | Page UICN France : https://uicn.fr/especes/liste-rouge-france/ — Page résultats détaillés : https://uicnfrance.fr/liste-rouge-france/ — Bilan 16 ans (MNHN) : https://www.mnhn.fr/fr/16-ans-liste-rouge-des-especes-menacees-en-france — Résultats synthétiques (PDF) : https://uicn.fr/wp-content/uploads/2024/08/resultats-synthetiques-liste-rouge-france.pdf — Bilan 16 ans (PDF) : https://uicn.fr/bilan-16-ans-liste-rouge-france/ |

### Notes techniques

- La liste rouge nationale est établie selon les critères internationaux de l'UICN (catégories et critères 3.1).
- Élaboration depuis 2008 ; 32 partenaires et > 500 experts mobilisés.
- Les résultats sont consultables sur le site de l'INPN en complément du site UICN.
- La liste rouge est intégrée dans la BDC-Statuts (source n°2 ci-dessus).

---

## 14. CRBPO / MNHN — STOC (Suivi Temporel des Oiseaux Communs)

| Champ | Valeur |
|---|---|
| **Nom officiel** | STOC — Suivi Temporel des Oiseaux Communs (STOC-EPS et STOC-Capture) |
| **Organisme** | CRBPO (Centre de Recherches sur la Biologie des Populations d'Oiseaux) — MNHN, dans le cadre du programme Vigie-Nature |
| **URL d'accès** | https://www.vigienature.fr/fr/suivi-temporel-des-oiseaux-communs-stoc |
| **Type d'accès** | `file_download` (données sur GBIF) + `publication_text` (rapports, indicateurs) |
| **Licence** | Données publiques depuis le 01/03/2009 (données brutes d'observation) ; disponibles sur GBIF |
| **Volume estimé** | Suivi depuis 1989 (STOC-Capture) / 2001 (STOC-EPS) ; centaines d'observateurs ; points d'écoute annuels sur des carrés tirés au sort (rayon 10 km autour du point de l'observateur) |
| **Variables** | Espèces, abondance, tendances temporelles d'effectifs, variations interannuelles, indicateurs par cortèges d'espèces (généralistes, spécialistes des milieux agricoles, forestiers, bâtis) |
| **Données sensibles** | **Partiellement.** Les données STOC sont des données publiques depuis 2009. Les carrés de suivi sont tirés au sort et leur localisation précise peut être sensible pour certaines espèces rares |
| **Couverture** | France métropolitaine (réseau de carrés permanents) |
| **Priorité GSIE** | **P1** — source de référence pour les tendances temporelles de l'avifaune commune |
| **Exemples d'URL vérifiées** | Vigie-Nature : https://www.vigienature.fr/fr/suivi-temporel-des-oiseaux-communs-stoc — INPN (jeu de données) : https://inpn.mnhn.fr/espece/jeudonnees/1987 — GBIF (données brutes) : https://www.gbif.org/dataset/77c3a178-a140-4a5d-87af-1f29e29f8330 — Fiche observatoire : https://www.open-sciences-participatives.org/fiche-observatoire/144 — Wikipédia : https://fr.wikipedia.org/wiki/Suivi_temporel_des_oiseaux_communs |

### Notes techniques

- STOC-EPS (Échantillonnages Ponctuels Simples) : points d'écoute sur des carrés permanents, 2 passages/an au printemps.
- STOC-Capture : baguage et suivi des populations d'oiseaux communs (depuis 1923 pour le baguage au MNHN).
- Les données STOC alimentent les indicateurs de biodiversité nationale et européenne (indicateur « oiseaux communs » pour la SNB).
- Les données sont diffusées via le SINP et GBIF.

---

## 15. INPN / SINP — Guide technique sensibilité des données à la diffusion

| Champ | Valeur |
|---|---|
| **Nom officiel** | Sensibilité des données à la diffusion — Guide technique du SINP (v2.0) |
| **Organisme** | SINP / UAR PatriNat (OFB-MNHN-CNRS-IRD) — INPN |
| **URL d'accès** | https://inpn.mnhn.fr/actualites/lire/13942/ |
| **Type d'accès** | `publication_text` (guide méthodologique PDF) + `knowledge_extraction` (référentiel de sensibilité) |
| **Licence** | Ouverte (document public SINP) |
| **Volume estimé** | Guide technique de 24 pages (v2.0, 2022) ; référentiel national de sensibilité consolidant les référentiels régionaux |
| **Variables** | Niveaux de floutage géographique (de précis à 5 000 km² / départemental), listes d'espèces sensibles, conditions de diffusion, règles d'application |
| **Données sensibles** | **Oui — c'est le référentiel lui-même.** Définit les règles de floutage pour toutes les données d'occurrence diffusées via le SINP/OpenObs. Niveau 3 = floutage départemental (5 000 km²) pour les cas les plus sensibles. L'absence de diffusion est une option pour les cas exceptionnels |
| **Couverture** | France (métropole + outre-mer) |
| **Priorité GSIE** | **P0** — référentiel méthodologique obligatoire pour le moteur de confidentialité GSIE |
| **Exemples d'URL vérifiées** | Actualité INPN : https://inpn.mnhn.fr/actualites/lire/13942/ — Téléchargement guide (PDF) : https://inpn.mnhn.fr/docs-web/docs/download/404525 — Guide PDF (miroir OBV-NA) : https://obv-na.fr/ofsa/images/Actualites/11804/docs/816.pdf — Article méthodologique (Ichter et al. 2024, Naturae) : https://mnhn.hal.science/mnhn-04549849/file/2024-Ichter-Prima-Gigot-LR%20et%20menaces-Naturae.pdf |

### Notes techniques

- Le guide technique v2.0 (2022) remplace la v1.0 ; il définit la démarche étape par étape pour établir les listes d'espèces sensibles et les conditions de floutage.
- Le référentiel national de sensibilité est une consolidation des référentiels de sensibilité établis par les acteurs régionaux du SINP.
- Les niveaux de floutage vont de la précision exacte (non sensible) à 5 000 km² (très sensible), avec possibilité de non-diffusion.
- **Pour GSIE** : ce référentiel doit être intégré au moteur de confidentialité pour déterminer automatiquement le niveau de floutage à appliquer aux occurrences d'espèces protégées.

---

## 16. Synthèse — Enjeux de confidentialité pour GSIE

### 16.1 Le cadre réglementaire français

La diffusion des données d'occurrence d'espèces en France est encadrée par le **Système d'Information de l'Inventaire du Patrimoine Naturel (SINP)**, qui définit un référentiel national de sensibilité. Les espèces protégées (arrêtés nationaux) font l'objet d'un **floutage géographique** systématique lors de la diffusion publique.

### 16.2 Niveaux de floutage (guide technique SINP v2.0)

| Niveau | Précision | Cas d'usage |
|---|---|---|
| 0 | Coordonnées exactes | Espèces non sensibles |
| 1 | ~1 km² | Sensibilité faible |
| 2 | ~100 km² | Sensibilité modérée |
| 3 | ~5 000 km² (départemental) | Sensibilité élevée (cas les plus sensibles) |
| Non-diffusion | Aucune donnée diffusée | Cas exceptionnels |

### 16.3 Sources de données sensibles identifiées

| Source | Données sensibles ? | Mécanisme de protection |
|---|---|---|
| INPN / OpenObs | **Oui** | Floutage SINP ; accès aux données précises via extraction conventionnée |
| GBIF | **Oui** (hérite du floutage SINP pour les données françaises) | Coordonnées floutées automatiquement |
| LPO / Faune-France | **Oui** | Floutage public ; accès aux données brutes via convention |
| SHF (Atlas + POP) | **Oui** | Floutage des espèces protégées ; validation nationale SINP depuis 2024 |
| SFEPM / ONM | **Oui** | Diffusion à maille 10×10 km minimum ; chiroptères et grands carnivores particulièrement sensibles |
| STOC / CRBPO | **Partiellement** | Données publiques depuis 2009 ; localisation des carrés potentiellement sensible |
| BDC-Statuts / Liste rouge | **Non** (statuts, pas de localisations) | N/A — mais indique quelles espèces sont protégées/sensibles |
| TAXREF | **Non** | N/A — référentiel taxonomique |

### 16.4 Recommandations pour GSIE

1. **Intégrer la BDC-Statuts** (source n°2) comme référentiel de statuts juridiques pour croiser avec les occurrences et déterminer la sensibilité.
2. **Intégrer le référentiel national de sensibilité SINP** (source n°15) dans le moteur de confidentialité GSIE pour appliquer automatiquement le floutage.
3. **Pour les données publiques** (OpenObs, GBIF) : utiliser l'API REST pour récupérer les occurrences floutées — acceptable pour les cartes de répartition mais insuffisant pour les analyses fines.
4. **Pour les données précises** : établir une **convention SINP** (extraction INPN) ou des conventions avec les producteurs (LPO, SHF, SFEPM) pour accéder aux coordonnées exactes des espèces protégées, dans le cadre d'un usage scientifique/conservation.
5. **TAXREF** (source n°4) doit être la **source de vérité taxonomique** unique pour tous les moteurs GSIE — les codes `cd_nom` / `cd_ref` sont la clé de jointure universelle.
6. **La liste rouge UICN** (source n°13) doit être intégrée comme attribut de conservation dans le moteur de connaissances GSIE.

### 16.5 Matrice de priorité GSIE

| Source | Priorité | Rôle dans GSIE |
|---|---|---|
| INPN / OpenObs (occurrences) | **P0** | Source principale d'occurrences nationales |
| BDC-Statuts (statuts juridiques) | **P0** | Référentiel des statuts de protection |
| INPN / Espèces protégées et réglementées | **P0** | Référentiel juridique (protection, réglementation) |
| TAXREF (taxonomie) | **P0** | Référentiel taxonomique unique |
| Liste rouge UICN France | **P0** | Statut de conservation des espèces |
| Guide technique sensibilité SINP | **P0** | Méthodologie de floutage / confidentialité |
| LPO / Faune-France | **P0** | Plus grande base naturaliste participative |
| GBIF (occurrences internationales) | **P1** | Complément international / migrateurs |
| GBIF France (IPT) | **P1** | Publication Darwin Core des jeux français |
| Atlas Oiseaux de France (ODF) | **P1** | Répartition + tendances avifaune |
| SHF — Atlas reptiles/amphibiens | **P1** | Répartition herpétofaune |
| SFEPM / ONM (mammifères) | **P1** | Répartition + tendances mammifères |
| SFEPM — Atlas mammifères | **P1** | Répartition mammifères (multi-volumes) |
| STOC (suivi temporel oiseaux) | **P1** | Tendances temporelles avifaune commune |
| SHF — POPAmphibiens / POPReptile | **P2** | Suivis temporels spécialisés herpétofaune |

---

## Sources consultées (recherche web, 2026-07-15)

Toutes les URLs ci-dessus ont été vérifiées via recherches web le 2026-07-15. Aucune URL n'a été inventée. Les sources primaires sont les sites officiels des organismes (INPN/MNHN, GBIF, LPO, SHF, SFEPM, UICN France, PatriNat, Vigie-Nature, data.gouv.fr).
