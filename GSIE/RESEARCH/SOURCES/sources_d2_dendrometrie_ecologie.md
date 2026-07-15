# Sources — D2 Dendrométrie + Écologie forestière

| Champ | Valeur |
|---|---|
| **Domaine** | Dendrométrie + Écologie forestière |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## Sommaire

1. [BD Forêt v2 (IGN)](#1-bd-forêt-v2-ign)
2. [Données brutes de l'Inventaire Forestier National — DataIFN (IGN)](#2-données-brutes-de-linventaire-forestier-national--dataifn-ign)
3. [Indices écologiques de l'inventaire forestier (IGN)](#3-indices-écologiques-de-linventaire-forestier-ign)
4. [Clés de détermination des habitats forestiers par GRECO (IGN)](#4-clés-de-détermination-des-habitats-forestiers-par-greco-ign)
5. [ICP Forests — Level I (surveillance systématique européenne)](#5-icp-forests--level-i-surveillance-systématique-européenne)
6. [ICP Forests — Level II (monitoring intensif)](#6-icp-forests--level-ii-monitoring-intensif)
7. [RENECOFOR — Réseau National de suivi à long terme des Écosystèmes Forestiers (ONF)](#7-renecofor--réseau-national-de-suivi-à-long-terme-des-écosystèmes-forestiers-onf)
8. [Guides et catalogues des stations forestières (CNPF / CRPF)](#8-guides-et-catalogues-des-stations-forestières-cnpf--crpf)
9. [Flore forestière française — Rameau et al. (IDF)](#9-flore-forestière-française--rameau-et-al-idf)
10. [Portail cartographique IGN — couches forestières (IGN)](#10-portail-cartographique-ign--couches-forestières-ign)
11. [Outil inventIF — visualisation des résultats IFN (IGN)](#11-outil-inventif--visualisation-des-résultats-ifn-ign)

---

## 1. BD Forêt v2 (IGN)

| Champ | Valeur |
|---|---|
| **Nom officiel** | BD Forêt® version 2.0 |
| **Organisme producteur** | Institut national de l'information géographique et forestière (IGN-F) |
| **URL d'accès** | https://geoservices.ign.fr/bdforet |
| **Type d'accès** | `file_download`, `ogc_wms`, `ogc_wfs`, `ogc_wmts` |
| **Licence et conditions** | Licence Ouverte / Open Licence Etalab v2.0 (depuis le 01/01/2021). Mention obligatoire : « Source IGN – BD Forêt version 2 » |
| **Volume estimé** | Couverture nationale par emprises départementales (96 départements métropolitains). Nomenclature nationale en 32 postes. Éléments > 5 000 m² (0,5 ha) |
| **Variables disponibles** | Type de formation végétale (32 postes), densité de couvert, composition, essence dominante, superposable avec BD TOPO® couche « Végétation » |
| **Fréquence de mise à jour** | Production 2007–2018 (assemblage de millésimes départementaux). Pas de cycle de révision systématique annuel ; mises à jour par département selon disponibilité des orthophotos |
| **Qualité et couverture** | France métropolitaine (96 départements). Corse incluse. Précision : photo-interprétation d'images infrarouge couleur de la BD ORTHO® |
| **Priorité GSIE** | **P0** — référentiel géographique forestier national de base |
| **Exemples concrets d'URL** | WMS : `https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities` ; WFS : `https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities` ; WMTS : `https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities` ; Téléchargement : `https://data.geopf.fr/telechargement/resource/BDFORET` ; Documentation : `https://data.geopf.fr/annexes/ressources/documentation/DC_BDForet_2-0.pdf` ; data.gouv.fr : `https://www.data.gouv.fr/datasets/bd-foret-version-2` |

---

## 2. Données brutes de l'Inventaire Forestier National — DataIFN (IGN)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Données brutes de l'inventaire forestier (DataIFN) |
| **Organisme producteur** | IGN — Département Inventaire Forestier |
| **URL d'accès** | https://inventaire-forestier.ign.fr/dataifn/ |
| **Type d'accès** | `file_download` (CSV/ZIP), visualisation interactive via requêteur |
| **Licence et conditions** | Licence Ouverte / Open Licence Etalab v2.0. Citation obligatoire : « IGN – Inventaire forestier national français, Données brutes, Campagnes annuelles 2005 et suivantes, https://inventaire-forestier.ign.fr/dataIFN/ » |
| **Volume estimé** | ~6 000 placettes/an, ~60 000 arbres mesurés/an. Données disponibles depuis 2005 (campagnes annuelles). Coordonnées fournies au kilomètre près (centre de maille) |
| **Variables disponibles** | Caractéristiques des placettes (exposition, pente, topographie), mesures dendrométriques (diamètre, hauteur, accroissement), données éco-floristiques (relevé floristique sur 700 m²), description du sol, habitat potentiel, taux de couvert libre (TCL), mortalité, prélèvements de bois |
| **Fréquence de mise à jour** | Annuelle (campagne annuelle). Dernière mise à jour : 14/10/2025 (campagne 2024). Placettes semi-permanentes : revisitées à 5 ans |
| **Qualité et couverture** | France métropolitaine (Corse incluse). Protocole stable depuis 1994 pour l'écologie, échantillonnage statistique systématique. Coordonnées anonymisées au km près |
| **Priorité GSIE** | **P0** — source dendrométrique et écologique principale pour la France |
| **Exemples concrets d'URL** | Portail DataIFN : `https://inventaire-forestier.ign.fr/dataIFN/index.php` ; data.gouv.fr : `https://www.data.gouv.fr/datasets/donnees-brutes-de-l-inventaire-forestier` ; Manuel utilisateur : `https://inventaire-forestier.ign.fr/IMG/pdf/Manuel_Utilisateur_VDB.pdf` |

---

## 3. Indices écologiques de l'inventaire forestier (IGN)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Indices écologiques de l'inventaire forestier |
| **Organisme producteur** | IGN (avec INRAE, ONF, ADEME — projet INSENSE) |
| **URL d'accès** | https://www.data.gouv.fr/datasets/indices-ecologiques-de-linventaire-forestier |
| **Type d'accès** | `file_download` (CSV/ZIP) |
| **Licence et conditions** | Licence Ouverte / Open Licence v2.0 |
| **Volume estimé** | Indices calculés pour tous les points d'inventaire en forêt depuis 2005. Fichier ZIP « Données brutes et indices écologiques – campagnes 2005 à 2018 » (et extensions ultérieures) |
| **Variables disponibles** | Indices écologiques calculés (alimentation en eau, alimentation minérale, pH, richesse chimique, texture), indicateurs de sensibilité des sols (Ca, Mg, K, P — projet INSENSE), groupes écologiques |
| **Fréquence de mise à jour** | Ponctuelle (liée aux campagnes et projets de recherche). Fichier de référence 2005–2018, extensions par campagne |
| **Qualité et couverture** | France métropolitaine. Calculés à partir des données brutes IGN, protocole stable |
| **Priorité GSIE** | **P1** — complément écologique calculé à partir des données brutes |
| **Exemples concrets d'URL** | data.gouv.fr : `https://www.data.gouv.fr/datasets/indices-ecologiques-de-linventaire-forestier` ; Page écologie forestière IGN : `https://inventaire-forestier.ign.fr/spip.php?rubrique240=` |

---

## 4. Clés de détermination des habitats forestiers par GRECO (IGN)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Clés de détermination des habitats forestiers naturels (par Grande Région Écologique — GRECO) |
| **Organisme producteur** | IGN — Département Écosystèmes forestiers |
| **URL d'accès** | https://inventaire-forestier.ign.fr/?lang=fr |
| **Type d'accès** | `knowledge_extraction`, `file_download` (PDF) |
| **Licence et conditions** | Licence Ouverte / Open Licence v2.0 (documents IGN) |
| **Volume estimé** | Une clé par GRECO (13 GRECO en France métropolitaine). Production depuis 2011. Clé GRECO Alpes disponible récemment |
| **Variables disponibles** | Type d'habitat élémentaire (niveau association végétale phytosociologique), critères floristiques et écologiques, correspondance avec les cahiers d'habitats (directive 92/43/CEE) |
| **Fréquence de mise à jour** | Production progressive par GRECO depuis 2011. Pas de cycle fixe |
| **Qualité et couverture** | France métropolitaine par GRECO. Caractérisation sur le terrain par les équipes IGN sur tous les points d'inventaire en forêt |
| **Priorité GSIE** | **P1** — référentiel d'habitats pour l'écologie stationnelle |
| **Exemples concrets d'URL** | Article habitats : `https://inventaire-forestier.ign.fr/IMG/pdf/rff-68_409-425_benest.pdf` ; Note méthodologique : `https://inventaire-forestier.ign.fr/IMG/pdf/note_methodologique.pdf` |

---

## 5. ICP Forests — Level I (surveillance systématique européenne)

| Champ | Valeur |
|---|---|
| **Nom officiel** | ICP Forests Level I — European forest condition monitoring |
| **Organisme producteur** | International Cooperative Programme on Assessment and Monitoring of Air Pollution Effects on Forests (ICP Forests), sous la Convention CLRTAP (UNECE) |
| **URL d'accès** | https://icp-forests.org/open_data/ |
| **Type d'accès** | `file_download` (open data : GPD/DAR metadata), `publication_text` (rapports annuels). Données détaillées : sur demande via data request |
| **Licence et conditions** | Open data (metadata GPD/DAR). Données complètes : accès sur demande (data request) — approbation par les National Focal Centres (NFC) et PCC, délai 2–4 semaines |
| **Volume estimé** | ~6 000 placettes Level I sur grille systématique 16 × 16 km à l'échelle européenne. France : ~540 placettes (partie française du réseau) |
| **Variables disponibles** | État des cimes (crown condition : défoliation, coloration), espèces arborées, phénologie, croissance (DBH, hauteur sur sous-ensemble), lichens épiphytes (survey LQA) |
| **Fréquence de mise à jour** | Annuelle (campagne estivale). Rapport annuel « Forest Condition in Europe » (édition 2025 disponible) |
| **Qualité et couverture** | Europe entière + pays au-delà. Grille systématique transnationale harmonisée. Protocole standardisé (ICP Forests Manual) |
| **Priorité GSIE** | **P1** — référence européenne pour la santé des forêts et la dendrométrie harmonisée |
| **Exemples concrets d'URL** | Open data : `https://icp-forests.org/open_data/` ; Documentation : `https://icp-forests.org/documentation/` ; Data requests : `https://www.icp-forests.net/data-maps/data-requests` ; Rapport 2025 : `https://www.icp-forests.net/fileadmin/icp_forests/Dateien/TR/ICPForests_TR2025.pdf` ; Plots & data : `http://icp-forests.net/page/plots-data` |

---

## 6. ICP Forests — Level II (monitoring intensif)

| Champ | Valeur |
|---|---|
| **Nom officiel** | ICP Forests Level II — Intensive monitoring plots |
| **Organisme producteur** | ICP Forests (UNECE CLRTAP) — Programme Coordinating Centre (PCC) |
| **URL d'accès** | https://icp-forests.org/open_data/level_ii/index.html |
| **Type d'accès** | `file_download` (open data : GPD/DAR, tree species distribution), `knowledge_extraction` (documentation en ligne). Données détaillées : sur demande (data request) |
| **Licence et conditions** | Open data (metadata et description générale). Données complètes : accès sur demande — approbation NFC + PCC (2–4 semaines). Base de données sols : accès sur demande spécifique |
| **Volume estimé** | ~800 placettes Level II en Europe. France : ~102 placettes (correspondant au réseau RENECOFOR). Surveys : sol (SO), eau du sol (SW), feuillage (FO), croissance (TR), couronnes (CR), litière (LI), météo (ME), biodiversité (BD) |
| **Variables disponibles** | Croissance dendrométrique (DBH, hauteur, accroissement), état des cimes, chimie du feuillage, chimie et physique des sols, eau du sol, dépôts atmosphériques, litière, phénologie, météorologie, biodiversité (flore, lichens, coléoptères) |
| **Fréquence de mise à jour** | Variable selon survey : cimes/croissance annuel, sols tous ~10 ans, feuillage tous 2 ans, eau du sol continu |
| **Qualité et couverture** | Europe (286 placettes avec données sols consolidées). France : ~102 placettes. Protocole ICP Forests Manual strict, assurance qualité centralisée |
| **Priorité GSIE** | **P0** — source la plus riche en données écologiques forestières intensives multi-paramètres |
| **Exemples concrets d'URL** | Open data Level II : `https://icp-forests.org/open_data/level_ii/index.html` ; Documentation surveys : `https://icp-forests.org/documentation/` ; Data requests : `https://www.icp-forests.net/data-maps/data-requests` ; User guide data portal : `https://www.icp-forests.net/fileadmin/icp_forests/Dateien/icpf_data_portal_user_guide.pdf` ; Database report 2023 : `https://www.icp-forests.net/fileadmin/icp_forests/Dateien/Database_Reports/ICP_Forests_Database_Report_2023.pdf` |

---

## 7. RENECOFOR — Réseau National de suivi à long terme des Écosystèmes Forestiers (ONF)

| Champ | Valeur |
|---|---|
| **Nom officiel** | RENECOFOR — Réseau National de suivi à long terme des Écosystèmes Forestiers |
| **Organisme producteur** | Office National des Forêts (ONF) — créé en 1992 |
| **URL d'accès** | https://www.onf.fr/renecofor |
| **Type d'accès** | `publication_text`, `knowledge_extraction` (rapports, fiches). Données brutes : sur demande à l'ONF |
| **Licence et conditions** | Données non libre-accès par défaut. Rapports et infographies publiquement disponibles. Accès aux données : demande auprès de l'ONF / GIP Ecofor |
| **Volume estimé** | ~102 placettes permanentes en France métropolitaine (correspond aux placettes ICP Forests Level II françaises). Suivi depuis 1992 (30+ ans de séries temporelles) |
| **Variables disponibles** | Croissance dendrométrique, état sanitaire (cimes), chimie du feuillage, chimie des sols, dépôts atmosphériques, eau du sol, litière, flore, phénologie. Cycle des éléments nutritifs |
| **Fréquence de mise à jour** | Annuelle (cimes, croissance). Décennale (sols). Continue (météo, dépôts) |
| **Qualité et couverture** | France métropolitaine (102 placettes). Séries temporelles longues (depuis 1992). Partie française d'ICP Forests Level II |
| **Priorité GSIE** | **P1** — séries longues françaises, complémentaire d'ICP Forests Level II |
| **Exemples concrets d'URL** | ONF RENECOFOR : `https://www.onf.fr/renecofor` ; Infographie : `https://www.onf.fr/onf/+/2ff::renecofor-reseau-national-de-suivi-long-terme-des-ecosystemes-forestiers.html` ; GIP Ecofor : `http://www.gip-ecofor.org/f-ore-t/renecofor.php` ; Observatoire des forêts : `https://observatoire.foret.gouv.fr/catalogue/renecofor-reseau-national-de-suivi-a-long-terme-des-ecosystemes-forestiers` |

---

## 8. Guides et catalogues des stations forestières (CNPF / CRPF)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Catalogues et guides des stations forestières (par région naturelle) |
| **Organisme producteur** | Centre National de la Propriété Forestière (CNPF) et CRPF régionaux |
| **URL d'accès** | https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/les-stations-forestieres |
| **Type d'accès** | `file_download` (PDF), `knowledge_extraction` |
| **Licence et conditions** | Libre téléchargement sur site CNPF et IGN. Diffusion papier via délégations régionales CNPF |
| **Volume estimé** | Des dizaines de guides par région naturelle. Chaque document : ~2–3 ans de travail. Couverture partielle du territoire (régions investies différemment) |
| **Variables disponibles** | Types de stations forestières, clés de détermination, groupes écologiques d'espèces, potentialités de production par essence, conseils de gestion sylvicole, variantes d'habitat, facteurs pédo-climatiques |
| **Fréquence de mise à jour** | Ponctuelle par région. Pas de cycle fixe. Rééditions occasionnelles (ex. Guide des Habitats Centre, 2e édition 2025) |
| **Qualité et couverture** | France métropolitaine (couverture hétérogène par région). Guides par région forestière / administrative. Ex. : Grand Est, Hauts-de-France-Normandie, Centre, Champagne-Ardenne |
| **Priorité GSIE** | **P1** — référentiel stationnel régional pour le choix des essences et la gestion |
| **Exemples concrets d'URL** | CNPF stations : `https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/les-stations-forestieres` ; Guide Habitats Centre : `https://ifc.cnpf.fr/sites/ifc/files/2025-04/Guide-Habitat-VF-CNPF-IFC-1-112.pdf` ; Grand Est : `https://grandest.cnpf.fr/se-former-s-informer/stations-forestieres/les-guides-simplifies-pour-le-choix-des-essences-en-grand` ; Hauts-de-France-Normandie : `https://hautsdefrance-normandie.cnpf.fr/sols-forestiers-et-guides-des-stations` ; IGN (téléchargement) : `https://inventaire-forestier.ign.fr/spip.php?rubrique255=` |

---

## 9. Flore forestière française — Rameau et al. (IDF)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Flore forestière française : guide écologique illustré (3 tomes) |
| **Organisme producteur** | Institut pour le Développement Forestier (IDF) — auteurs : J.-C. Rameau, D. Mansion, G. Dumé, et al. |
| **URL d'accès** | https://biblio.cbnpmp.fr/index.php?id=5249&lvl=publisher_see |
| **Type d'accès** | `publication_text` (ouvrages imprimés), `knowledge_extraction` (écogrammes, groupes écologiques) |
| **Licence et conditions** | Ouvrage commercial (IDF). Consultable en bibliothèque (CNPF). Pas de téléchargement libre |
| **Volume estimé** | 3 tomes : Tome 1 « Plaines et collines » (1989, 1785 p.), Tome 2 « Montagnes » (1993), Tome 3 (2009). Référence taxonomique et écologique pour la France |
| **Variables disponibles** | Détermination des espèces (herbacées et ligneuses), écogrammes (alimentation en eau × alimentation minérale), groupes écologiques, caractères indicateurs stationnels, autécologie des essences |
| **Fréquence de mise à jour** | Statique (éditions 1989, 1993, 2009). Pas de mise à jour régulière |
| **Qualité et couverture** | France métropolitaine (Plaines/Collines, Montagnes). Référence nationale pour la phytosociologie et l'écologie forestière |
| **Priorité GSIE** | **P2** — référence de connaissance (non numérique), à intégrer comme base taxonomique/écologique |
| **Exemples concrets d'URL** | Catalogue IDF : `https://biblio.cbnpmp.fr/index.php?id=5249&lvl=publisher_see` ; Notice Tome 1 : `https://biblio.cbnpmp.fr/index.php?lvl=notice_display&id=76576` |

---

## 10. Portail cartographique IGN — couches forestières (IGN)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Portail cartographique de l'Inventaire Forestier — couches d'information géographique |
| **Organisme producteur** | IGN — Inventaire Forestier |
| **URL d'accès** | https://inventaire-forestier.ign.fr/spip.php?rubrique227= |
| **Type d'accès** | `ogc_wms`, `file_download` (visualisation + téléchargement via outil carto) |
| **Licence et conditions** | Licence Ouverte / Open Licence Etalab v2.0 |
| **Volume estimé** | Couches : BD Forêt V2, BD Forêt V1, cartographie dégâts tempête Klaus (2009), zonages biogéographiques (régions forestières, GRECO, sylvoécorégions) |
| **Variables disponibles** | Formations végétales forestières, types de peuplements, dégâts tempête, régions forestières, grandes régions écologiques, sylvoécorégions |
| **Fréquence de mise à jour** | Variable selon couche. BD Forêt : voir §1. Zonages : stables |
| **Qualité et couverture** | France métropolitaine. Corse incluse pour BD Forêt |
| **Priorité GSIE** | **P1** — couches de zonage écologique indispensables (GRECO, sylvoécorégions) |
| **Exemples concrets d'URL** | Portail carto : `https://inventaire-forestier.ign.fr/spip.php?rubrique227=` ; Catalogue IGN : `https://geoservices.ign.fr/bdforet` ; cartes.gouv.fr : `https://cartes.gouv.fr/aide/fr/partenaires/ign/referentiels-description-territoire/foret/` |

---

## 11. Outil inventIF — visualisation des résultats IFN (IGN)

| Champ | Valeur |
|---|---|
| **Nom officiel** | inventIF — Outil de visualisation des résultats issus de l'Inventaire Forestier National |
| **Organisme producteur** | IGN — Inventaire Forestier |
| **URL d'accès** | https://inventif.ign.fr/ |
| **Type d'accès** | `publication_text` (visualisation interactive, tableaux de résultats) |
| **Licence et conditions** | Libre accès (visualisation). Données sous-jacentes : Licence Ouverte v2.0 |
| **Volume estimé** | 6 thématiques : anomalies de croissance, biodiversité, santé des forêts, flux de bois, (et extensions). Tableaux standards de résultats chiffrés |
| **Variables disponibles** | Résultats agrégés : croissance (anomalies), biodiversité, santé, flux de bois (production biologique, prélèvement, mortalité). Figures interactives avec filtres |
| **Fréquence de mise à jour** | Annuelle (liée aux campagnes IFN) |
| **Qualité et couverture** | France métropolitaine. Données agrégées statistiquement |
| **Priorité GSIE** | **P2** — visualisation de résultats agrégés, utile pour validation et communication |
| **Exemples concrets d'URL** | inventIF : `https://inventif.ign.fr/` |

---

## Synthèse des priorités GSIE

| Priorité | Sources | Rôle dans GSIE |
|---|---|---|
| **P0** | BD Forêt v2, DataIFN (données brutes IFN), ICP Forests Level II | Référentiel géographique + dendrométrie nationale + monitoring écologique intensif |
| **P1** | Indices écologiques IGN, Clés habitats GRECO, ICP Forests Level I, RENECOFOR, Guides stations CNPF, Portail carto IGN | Compléments écologiques, stationnels, séries longues, zonages |
| **P2** | Flore forestière Rameau, inventIF | Référence de connaissance taxonomique, visualisation agrégée |

---

## Notes méthodologiques

- **Aucune URL inventée** — toutes les URLs ci-dessus ont été vérifiées via recherche web (juillet 2026).
- **ICP Forests Level I/II** : distinction claire — Level I = grille systématique 16×16 km (~6 000 placettes, crown condition), Level II = monitoring intensif (~800 placettes, multi-paramètres). La France contribue au Level II via le réseau RENECOFOR (ONF, ~102 placettes).
- **DataIFN vs BD Forêt** : DataIFN = données terrain (dendrométrie, écologie, placettes statistiques) ; BD Forêt v2 = cartographie par photo-interprétation (formations végétales). Sources complémentaires, non redondantes.
- **Accès ICP Forests** : open data limité aux metadata (GPD/DAR). Données détaillées sur demande (data request) avec approbation des NFC — prévoir un délai de 2–4 semaines pour le projet GSIE.
- **Corse** : couverte par BD Forêt v2 et DataIFN. RENECOFOR : présence de placettes en Corse à vérifier auprès de l'ONF.
