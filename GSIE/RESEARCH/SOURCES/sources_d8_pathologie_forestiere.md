# Sources — D8 Pathologie forestière

| Champ | Valeur |
|---|---|
| **Domaine** | Pathologie forestière |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## Sommaire

1. [EPPO Global Database — ravageurs et organismes de quarantaine](#1-eppo-global-database--ravageurs-et-organismes-de-quarantaine)
2. [EPPO Data Portal / API REST — accès programmatique aux données EPPO](#2-eppo-data-portal--api-rest--acces-programmatique-aux-donnees-eppo)
3. [EPPO Q-Bank — banque de barcodes ADN pour diagnostic phytosanitaire](#3-eppo-q-bank--banque-de-barcodes-adn-pour-diagnostic-phytosanitaire)
4. [DSF — Département de la Santé des Forêts (France)](#4-dsf--departement-de-la-sante-des-forets-france)
5. [DEPERIS — méthode d'évaluation de l'état sanitaire des houppiers](#5-deperis--methode-devaluation-de-letat-sanitaire-des-houppiers)
6. [Observatoire des forêts françaises — portail IGN](#6-observatoire-des-forets-francaises--portail-ign)
7. [inventIF Santé — IGN / Inventaire forestier national](#7-inventif-sante--ign--inventaire-forestier-national)
8. [RENECOFOR — réseau national de suivi à long terme des écosystèmes forestiers (ONF)](#8-renecofor--reseau-national-de-suivi-a-long-terme-des-ecosystemes-forestiers-onf)
9. [ONF Open Data — données ouvertes de l'Office national des forêts](#9-onf-open-data--donnees-ouvertes-de-loffice-national-des-forets)
10. [Ephytia — encyclopédie des maladies forestières (INRAE)](#10-ephytia--encyclopedie-des-maladies-forestieres-inrae)
11. [ICP Forests — programme international de surveillance des forêts européennes](#11-icp-forests--programme-international-de-surveillance-des-forets-europeennes)
12. [ForDead — détection satellitaire du dépérissement forestier (INRAE)](#12-fordead--detection-satellitaire-du-deperissement-forestier-inrae)
13. [THEIA / Sentinel-2 — données satellitaires pour la santé des forêts](#13-theia--sentinel-2--donnees-satellitaires-pour-la-sante-des-forets)
14. [FCBA — Institut technologique Forêt Cellulose Bois-construction Ameublement](#14-fcba--institut-technologique-foret-cellulose-bois-construction-ameublement)
15. [Atlas of Forest Pests — base de données européenne des ravageurs forestiers](#15-atlas-of-forest-pests--base-de-donnees-europeenne-des-ravageurs-forestiers)
16. [Forest Research UK — ressources maladies et ravageurs des arbres](#16-forest-research-uk--ressources-maladies-et-ravageurs-des-arbres)
17. [EUROPHYT — système européen de notification des interceptions phytosanitaires](#17-europhyt--systeme-europeen-de-notification-des-interceptions-phytosanitaires)
18. [EFSA Pest Survey Cards — fiches de surveillance des organismes de quarantaine](#18-efsa-pest-survey-cards--fiches-de-surveillance-des-organismes-de-quarantaine)
19. [Euphresco — réseau européen de recherche phytosanitaire](#19-euphresco--reseau-europeen-de-recherche-phytosanitaire)
20. [BDIFF — base de données sur les incendies de forêts en France](#20-bdiff--base-de-donnees-sur-les-incendies-de-forets-en-france)
21. [Synthèse — Priorités et lacunes pour GSIE](#21-synthese--priorites-et-lacunes-pour-gsie)

---

## 1. EPPO Global Database — ravageurs et organismes de quarantaine

| Champ | Valeur |
|---|---|
| **Nom officiel** | EPPO Global Database |
| **Organisme** | European and Mediterranean Plant Protection Organization (EPPO) |
| **URL d'accès** | https://gd.eppo.int/ |
| **Type d'accès** | publication_text |
| **Licence** | Open Data Licence (EPPO) — accès gratuit |
| **Volume estimé** | > 90 000 organismes (pestes, plantes hôtes, vecteurs) ; > 16 000 photos ; articles du Reporting Service depuis 1974 |
| **Variables** | Distribution géographique (cartes mondiales), plantes hôtes, statut de quarantaine (A1, A2, Alert List), fiches techniques (datasheets), rapports d'analyse de risque phytosanitaire (PRA), standards EPPO, photos |
| **Fréquence** | Mise à jour continue |
| **Couverture** | Région EPPO (Europe, Méditerranée, Asie centrale) — données sur organismes de quarantaine et émergents |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://gd.eppo.int/ (page d'accueil) ; https://www.eppo.int/RESOURCES/eppo_databases/global_database (page descriptive) ; https://www.eppo.int/ACTIVITIES/plant_quarantine/A1_list (liste A1) ; https://www.eppo.int/ACTIVITIES/plant_quarantine/A2_list (liste A2) ; https://www.eppo.int/ACTIVITIES/plant_quarantine/alert_list (Alert List) ; https://gd.eppo.int/taxon/DENCMI/datasheet (fiche Dendroctonus micans) |

### Notes techniques

- Base de données de référence pour les organismes de quarantaine en Europe. Inclut les listes A1 (absents de la région EPPO), A2 (localement présents) et Alert List (veille).
- Chaque organisme possède une fiche avec : taxonomie, distribution géographique, plantes hôtes, vecteurs, statut réglementaire, photos, liens vers datasheets et PRA.
- Le Reporting Service (articles depuis 1974) documente les signalements d'organismes nuisibles dans la région EPPO.
- Pas d'API REST directe sur le site gd.eppo.int — l'accès programmatique se fait via EPPO Data Portal (voir source n°2).
- Données structurées par codes EPPO (ex. `DENCMI` pour Dendroctonus micans, `HIMEFR` pour Hymenoscyphus fraxineus).
- Inclut des organismes forestiers majeurs : Ips typographus, Dendroctonus micans, Hymenoscyphus fraxineus, Phytophthora ramorum, Dothistroma septosporum, Cryphonectria parasitica, etc.
- Pour GSIE : source de référence pour le référentiel taxonomique des organismes nuisibles forestiers et leur statut réglementaire européen.

---

## 2. EPPO Data Portal / API REST — accès programmatique aux données EPPO

| Champ | Valeur |
|---|---|
| **Nom officiel** | EPPO Data Portal (anciennement EPPO Data Services) |
| **Organisme** | European and Mediterranean Plant Protection Organization (EPPO) |
| **URL d'accès** | https://data.eppo.int/ |
| **Type d'accès** | api_rest |
| **Licence** | Open Data Licence (EPPO) — accès gratuit, inscription requise pour token API |
| **Volume estimé** | API couvrant l'ensemble des données EPPO : codes taxonomiques, distribution, hôtes, catégorisation |
| **Variables** | Codes EPPO, noms taxonomiques, noms préférés, distribution géographique, relations hôte-pest, catégorisation (quarantaine), standards |
| **Fréquence** | Mise à jour continue |
| **Couverture** | Région EPPO (Europe, Méditerranée, Asie centrale) |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://data.eppo.int/ (portail) ; https://data.eppo.int/documentation/ (documentation) ; https://data.eppo.int/apis/ (liste des APIs) |

### Notes techniques

- API REST avec réponses en JSON. Authentification via token personnel (gratuit, inscription sur le portail).
- Endpoints documentés : `/taxons/list`, `/tools/names2codes`, `/tools/codes2prefnames`, et endpoints pour distribution, hôtes, catégorisation.
- Ancienne API (`/api/rest/1.0/`) active jusqu'au 1er septembre 2026 — migration vers le nouveau portail en cours.
- Packages R disponibles : `pestr` (https://github.com/mczyzj/pestr) et `eppoFindeR` (https://github.com/openefsa/eppoFindeR) pour interroger l'API depuis R.
- Formats de téléchargement : XML, SQL, JSON pour les exports complets.
- Pour GSIE : intégration directe possible pour alimenter le moteur Forest/Pathologie en référentiel taxonomique et statut réglementaire des organismes nuisibles.

---

## 3. EPPO Q-Bank — banque de barcodes ADN pour diagnostic phytosanitaire

| Champ | Valeur |
|---|---|
| **Nom officiel** | EPPO-Q-bank Database |
| **Organisme** | European and Mediterranean Plant Protection Organization (EPPO) |
| **URL d'accès** | https://qbank.eppo.int/ |
| **Type d'accès** | publication_text |
| **Licence** | Open Access — accès gratuit, inscription requise pour télécharger les séquences |
| **Volume estimé** | 7 disciplines (arthropodes, bactéries, champignons, nématodes, phytoplasmes, virus & viroïdes, plantes invasives) ; milliers de spécimens/souches/isolats référencés |
| **Variables** | Séquences ADN (barcodes), métadonnées des spécimens (collection, origine, identification), protocoles de barcoding, outils BLAST intégrés |
| **Fréquence** | Mise à jour continue |
| **Couverture** | Organismes de quarantaine EPPO et leurs look-alikes (espèces proches) |
| **Priorité GSIE** | P1 |
| **Exemples d'URL vérifiées** | https://qbank.eppo.int/ (page d'accueil) ; https://qbank.eppo.int/general/page/userguides (guides utilisateur) ; https://qbank.eppo.int/data/files/general/factsheet_EPPO-Q-bank_V2.pdf (fiche descriptive) |

### Notes techniques

- Base de données de séquences ADN de référence pour le diagnostic des organismes de quarantaine. Lancée en 2010 (projet Q-bank néerlandais), transférée à EPPO en 2018.
- Inclut des outils BLAST pour comparer des séquences inconnues contre la base curée.
- Les séquences sont accessibles après connexion (gratuite). Les métadonnées des spécimens sont publiquement visibles.
- Liens vers les collections biologiques où les spécimens peuvent être obtenus pour études ou contrôles.
- Publication scientifique de référence : Bonants et al. (2019), EPPO-Q-bank: a curated database to support plant pest diagnostic activities, EPPO Bulletin, doi:10.1111/epp.13063.
- Pour GSIE : source de référence pour l'identification moléculaire des pathogènes forestiers (champignons, nématodes, bactéries). Utile pour validation de diagnostics.

---

## 4. DSF — Département de la Santé des Forêts (France)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Département de la Santé des Forêts (DSF) |
| **Organisme** | Ministère de l'Agriculture, de l'Agro-alimentaire et de la Souveraineté alimentaire (DGAL) |
| **URL d'accès** | https://agriculture.gouv.fr/la-sante-des-forets |
| **Type d'accès** | publication_text |
| **Licence** | Données publiques (Etalab Licence Ouverte v2.0) pour les publications ; base de données d'observations non libre d'accès direct |
| **Volume estimé** | ~15 000 observations sylvosanitaires par an ; réseau de 270+ correspondants-observateurs ; 1 124 problèmes différents enregistrés ; réseau systématique 16×16 km (~600 placettes en France) |
| **Variables** | Observations sylvosanitaires (agent pathogène, essence, localisation, symptômes, gravité), bilans annuels nationaux et interrégionaux, lettres du DSF (semestrielles), suivi spécifique scolytes, chalarose, encre du châtaignier, etc. |
| **Fréquence** | Observations continues ; bilan annuel national ; bilans interrégionaux annuels ; lettre bisannuelle |
| **Couverture** | France métropolitaine (forêts publiques et privées) |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://agriculture.gouv.fr/la-sante-des-forets (page d'accueil) ; https://agriculture.gouv.fr/le-departement-de-la-sante-des-forets-role-et-missions (missions) ; https://agriculture.gouv.fr/suivi-de-la-sante-des-forets (suivi) ; https://agriculture.gouv.fr/la-chalarose-du-frene-12-ans-apres-la-premiere-detection-en-france (chalarose) ; https://draaf.auvergne-rhone-alpes.agriculture.gouv.fr/suivi-de-l-essaimage-du-scolyte-typographe-en-2026-a6549.html (suivi scolytes 2026) ; https://agriculture.gouv.fr/telecharger/142886 (Plan national d'actions scolytes) |

### Notes techniques

- Acteur central de la surveillance phytosanitaire des forêts françaises. Créé en 1989, organisé en 6 pôles régionaux/interrégionaux hébergés dans les DRAAF.
- Le réseau de correspondants-observateurs (CO) — forestiers de terrain de l'ONF, CNPF et services déconcentrés — collecte les observations. 4 experts nationaux : pathologie forestière, entomologie forestière, problèmes abiotiques, télédétection.
- La base de données d'observations du DSF n'est pas en open data direct. Les données sont diffusées via les bilans (publications PDF), l'Observatoire des forêts françaises (source n°6) et des présentations.
- Suivis spécifiques documentés : scolytes (Ips typographus — réseau de piégeage hebdomadaire en AuRA, Grand Est), chalarose du frêne (depuis 2008), encre du châtaignier (Phytophthora cinnamomi/sweetgum), dépérissement du chêne.
- Le réseau systématique européen « 16×16 km » (Level I d'ICP Forests) compte ~600 placettes en France, avec ~12 000 arbres observés annuellement.
- Pour GSIE : source française primordiale pour l'état sanitaire des forêts. Les données brutes nécessitent un accord avec le DSF/DGAL pour accès. Les bilans publiés sont exploitables directement.

---

## 5. DEPERIS — méthode d'évaluation de l'état sanitaire des houppiers

| Champ | Valeur |
|---|---|
| **Nom officiel** | DEPERIS — méthode d'estimation simplifiée de l'état des houppiers |
| **Organisme** | Département de la Santé des Forêts (DSF) / MASA |
| **URL d'accès** | https://agriculture.gouv.fr/la-methode-deperis-comment-quantifier-et-mesurer-letat-de-sante-dune-foret-et-son-evolution |
| **Type d'accès** | publication_text |
| **Licence** | Données publiques (Etalab Licence Ouverte v2.0) |
| **Volume estimé** | Intégré au réseau 16×16 km (~600 placettes, ~12 000 arbres/an) ; déployé aussi sur placettes ponctuelles par gestionnaires |
| **Variables** | Note DEPERIS par arbre (A à F) : mortalité de branches (MB) + manque de ramification (MR, feuillus) ou manque d'aiguilles (MA, résineux) ; agrégation à l'échelle peuplement (peuplement dégradé si >20% arbres en D/E/F) |
| **Fréquence** | Annuelle (réseau systématique) ; ponctuelle (placettes gestionnaires) |
| **Couverture** | France métropolitaine |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://agriculture.gouv.fr/la-methode-deperis-comment-quantifier-et-mesurer-letat-de-sante-dune-foret-et-son-evolution (description) ; https://agriculture.gouv.fr/la-methode-deperis-pour-quantifier-letat-de-sante-de-la-foret (présentation) ; https://agriculture.gouv.fr/telecharger/149170 (guide de terrain) ; https://agriculture.gouv.fr/telecharger/131828 (bilan réseau 16×16) |

### Notes techniques

- Méthode développée par le DSF pour quantifier objectivement le dépérissement. Deux critères : mortalité de branches (MB) et manque de ramification (MR/MA). Note de A (parfaitement sain) à F (complètement dégradé).
- Intégré au réseau systématique européen 16×16 km depuis 2021. Les notes DEPERIS complètent le déficit foliaire traditionnel (critère ICP Forests).
- Méthode utilisable par tous les acteurs (ONF, CNPF, IGN, gestionnaires privés) — ne nécessite pas d'expertise sanitaire spécialisée.
- Les données DEPERIS sont visualisables via l'application inventIF Santé de l'IGN (source n°7) et l'Observatoire des forêts françaises (source n°6).
- Pour GSIE : protocole de terrain de référence pour l'évaluation de l'état sanitaire. Les notes DEPERIS peuvent servir de variable cible pour des modèles de prédiction du dépérissement.

---

## 6. Observatoire des forêts françaises — portail IGN

| Champ | Valeur |
|---|---|
| **Nom officiel** | Observatoire des forêts françaises |
| **Organisme** | IGN (pilotage) — en coordination avec ONF, CNPF, France Bois Forêt, OFB, MASA, MTE |
| **URL d'accès** | https://observatoire.foret.gouv.fr/ |
| **Type d'accès** | publication_text |
| **Licence** | Données publiques (Etalab Licence Ouverte v2.0) |
| **Volume estimé** | 5 clubs thématiques (santé des forêts, risque incendies, ressources en bois, adaptation climat, atténuation GES) ; indicateurs pour ~270 territoires ; cartes thématiques interactives |
| **Variables** | Surfaces de forêts dépérissantes, mortalité des arbres, indicateurs sanitaires (DEPERIS, déficit foliaire), ressources en bois, carbone, incendies, biodiversité |
| **Fréquence** | Mise à jour annuelle (alignée sur l'inventaire forestier) |
| **Couverture** | France métropolitaine (Corse incluse) — échelles nationale, régionale, départementale, sylvoécorégions |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://observatoire.foret.gouv.fr/ (portail) ; https://observatoire.foret.gouv.fr/catalogue/renecofor-reseau-national-de-suivi-a-long-terme-des-ecosystemes-forestiers (fiche RENECOFOR) ; https://observatoire.foret.gouv.fr/annuaire/DSF (annuaire DSF) ; https://www.ign.fr/institut/espace-presse/pour-la-journee-internationale-des-forets-le-site-de-lobservatoire-des-forets-francaises-senrichit (extension 2024) |

### Notes techniques

- Lancé en juillet 2023, l'Observatoire est le portail de référence unifiant les données forestières françaises. Co-piloté par IGN, ONF, CNPF, FBF, OFB.
- Le club « Santé des forêts » est co-piloté par l'IGN et le DSF, mobilisant l'expertise de l'INRAE, du CNPF et de l'ONF.
- Service « Les forêts de mon territoire » : indicateurs synthétiques (surfaces, mortalité, dépérissement, ressources, carbone) par territoire avec comparaison entre territoires.
- Catalogue de cartes thématiques interactives : forêts dépérissantes, zones touchées par crises sanitaires, incendies, ressources, biodiversité.
- Pour GSIE : portail d'accès principal aux indicateurs sanitaires agrégés à l'échelle française. Les données sous-jacentes proviennent de l'IGN (inventaire), du DSF (observations) et de l'ONF (RENECOFOR).

---

## 7. inventIF Santé — IGN / Inventaire forestier national

| Champ | Valeur |
|---|---|
| **Nom officiel** | inventIF — Santé des forêts |
| **Organisme** | IGN — Institut national de l'information géographique et forestière |
| **URL d'accès** | https://inventif.ign.fr/sante/ |
| **Type d'accès** | publication_text |
| **Licence** | Données publiques (Etalab Licence Ouverte v2.0) |
| **Volume estimé** | Données sur les principales essences forestières françaises ; ~12 000 arbres observés annuellement (réseau 16×16) ; données ARCHI sur >120 000 arbres suivis |
| **Variables** | Taux d'arbres morts sur pied par essence, déficit foliaire moyen, répartition des notes DEPERIS (A-F), cartes de parts d'arbres sains/dégradés par placette, mortalité annuelle, taux de mortalité |
| **Fréquence** | Annuelle (mise à jour avec les dernières campagnes d'inventaire) |
| **Couverture** | France hexagonale et Corse — échelles nationale, régionale, départementale, sylvoécorégions, GRECO |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://inventif.ign.fr/sante/ (application) ; https://inventif.ign.fr/sante/?tab=classement_ess_deperis (onglet DEPERIS par essence) ; https://inventaire-forestier.ign.fr/ (portail inventaire) ; https://inventaire-forestier.ign.fr/IMG/pdf/lif_sante-des-forets_web.pdf (publication n°47, 2021) |

### Notes techniques

- Application web interactive développée par l'IGN pour visualiser les données sanitaires de l'inventaire forestier national. Issue du numéro 47 de L'IF « Santé des forêts » (novembre 2021).
- Figures interactives : l'utilisateur peut sélectionner la région administrative, filtrer par essence, survoler pour voir les valeurs.
- Données issues du réseau systématique 16×16 km (DEPERIS, déficit foliaire) et de l'inventaire forestier permanent (mortalité, arbres morts).
- Méthode ARCHI : évaluation de l'état du houppier déployée sur >120 000 arbres suivis (mortalité des branches, manques, dépérissement).
- Les données de l'inventaire forestier national (IFN) sont téléchargeables via le portail IGN et data.gouv.fr.
- Pour GSIE : source quantitative de référence pour les indicateurs de santé des forêts françaises par essence et par territoire. Données téléchargeables et réutilisables.

---

## 8. RENECOFOR — réseau national de suivi à long terme des écosystèmes forestiers (ONF)

| Champ | Valeur |
|---|---|
| **Nom officiel** | RENECOFOR — Réseau National de suivi à long terme des Ecosystèmes Forestiers |
| **Organisme** | ONF — Office national des forêts |
| **URL d'accès** | https://www.onf.fr/renecofor |
| **Type d'accès** | publication_text |
| **Licence** | Données publiques (accès aux rapports et publications ; données brutes sur demande) |
| **Volume estimé** | 102 placettes permanentes (créées en 1992) ; suivi sur 30+ ans ; mesures dendrométriques, état sanitaire, composition foliaire, dépôts atmosphériques, sols |
| **Variables** | Croissance et production (dendrométrie), état sanitaire des tiges échantillons, composition chimique du feuillage, dépôts atmosphériques, chimie des sols, phénologie, végétation au sol |
| **Fréquence** | Mesures dendrométriques tous les 3-5 ans ; observations sanitaires annuelles ; autres suivis à fréquences variables |
| **Couverture** | France métropolitaine (forêts publiques) — 102 placettes réparties sur les principales essences et stations |
| **Priorité GSIE** | P1 |
| **Exemples d'URL vérifiées** | https://www.onf.fr/renecofor (page d'accueil) ; https://www.onf.fr/onf/+/2ff::renecofor-reseau-national-de-suivi-long-terme-des-ecosystemes-forestiers.html (infographie) ; https://observatoire.foret.gouv.fr/catalogue/renecofor-reseau-national-de-suivi-a-long-terme-des-ecosystemes-forestiers (fiche Observatoire) ; https://las.hautsdefrance.hub.inrae.fr/partenariat/le-reseau-national-de-suivi-a-long-terme-des-ecosysthemes-forestiers (description INRAE) |

### Notes techniques

- Réseau créé en 1992 par l'ONF dans le cadre des engagements français pour le suivi international des impacts des pollutions atmosphériques sur les forêts (convention CLRTAP / ICP Forests).
- Constitue la composante française du Level II d'ICP Forests (suivi intensif). Les placettes RENECOFOR correspondent aux placettes Level II françaises.
- Suivi multidisciplinaire : dendrométrie, état sanitaire, chimie foliaire, dépôts atmosphériques, sols, phénologie, végétation au sol, ozone.
- Données accessibles via les publications ONF et sur demande. Les métadonnées sont disponibles via le portail open data d'ICP Forests (source n°11).
- Pour GSIE : source de données de suivi à long terme sur l'état sanitaire et le fonctionnement des écosystèmes forestiers français. Complémentaire du réseau 16×16 (Level I) pour les relations causes-effets.

---

## 9. ONF Open Data — données ouvertes de l'Office national des forêts

| Champ | Valeur |
|---|---|
| **Nom officiel** | ONF Open Data — catalogue des données |
| **Organisme** | ONF — Office national des forêts |
| **URL d'accès** | https://appliforet.onf.fr/onf/connaitre-lonf/+/35::opendata-onf.html |
| **Type d'accès** | file_download |
| **Licence** | Etalab Licence Ouverte v2.0 (données ouvertes) |
| **Volume estimé** | Catalogue thématique : contours des forêts publiques, parcelles forestières, réserves biologiques, données naturalistes (via INPN), relevés d'incendies (via BDIFF), documents d'aménagement |
| **Variables** | Contours géographiques des forêts domaniales et communales, parcelles, directions territoriales, réserves biologiques, données naturalistes, calendriers de chasse |
| **Fréquence** | Mise à jour variable selon thématique |
| **Couverture** | France métropolitaine et DOM (forêts publiques gérées par l'ONF) |
| **Priorité GSIE** | P1 |
| **Exemples d'URL vérifiées** | https://appliforet.onf.fr/onf/connaitre-lonf/+/35::opendata-onf.html (page Open Data) ; https://www.onf.fr/vivre-la-foret/+/21ce::la-recherche-lonf.html (recherche ONF) |

### Notes techniques

- L'ONF a une politique d'ouverture des données (Open Data) avec un catalogue organisé par thématiques.
- Les données sanitaires spécifiques de l'ONF ne sont pas en téléchargement direct — elles sont diffusées via le DSF (observations des correspondants-observateurs ONF) et l'Observatoire des forêts françaises.
- L'ONF utilise l'outil DEPERIS (source n°5) et la chaîne ForDead (source n°12) pour le suivi sanitaire des forêts publiques.
- Le service RDI (Recherche, Développement, Innovation) de l'ONF compte 75 personnes et gère ~700 dispositifs expérimentaux en forêts publiques, avec mesures dendrométriques et état sanitaire.
- Pour GSIE : source pour les contours géographiques des forêts publiques (couche de référence spatiale) et pour les données de recherche ONF. Les données sanitaires passent par le DSF/Observatoire.

---

## 10. Ephytia — encyclopédie des maladies forestières (INRAE)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Ephytia — Forêts |
| **Organisme** | INRAE — Institut national de recherche pour l'agriculture, l'alimentation et l'environnement |
| **URL d'accès** | https://ephytia.inrae.fr/fr/P/124/Forets |
| **Type d'accès** | knowledge_extraction |
| **Licence** | Accès libre (contenu INRAE) |
| **Volume estimé** | ~200 fiches décrivant les problèmes sanitaires forestiers les plus fréquents et à risque ; > 1 000 photos |
| **Variables** | Fiches par pathologie/ravageur : biologie de l'organisme, symptômes, diagnostic, facteurs de risque, recommandations de gestion, photos, distribution |
| **Fréquence** | Mise à jour régulière (en lien avec le DSF) |
| **Couverture** | France métropolitaine — forêts de métropole |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://ephytia.inrae.fr/fr/P/124/Forets (page Forêts) ; https://ephytia.inrae.fr/fr/Home/index (accueil Ephytia) ; https://ephytia.inrae.fr/fr/Contents/view/20407/Forets-Chalarose-du-frene (fiche chalarose du frêne) ; https://ephytia.inrae.fr/fr/C/24029/Hypp-encyclopedie-en-protection-des-plantes-Les-maladies-et-ravageurs (encyclopédie Hypp) |

### Notes techniques

- Ephytia est la plateforme INRAE de fiches maladies des plantes, avec un espace dédié aux forêts développé en partenariat avec le DSF.
- Les ~200 fiches couvrent les problèmes les plus fréquemment observés par les correspondants-observateurs du DSF et les plus à risque.
- Chaque fiche détaille : biologie de l'organisme nuisible, symptômes et éléments de diagnostic, facteurs de risque, recommandations de gestion, photos illustratives.
- Inclut l'encyclopédie Hypp (protection des plantes) qui couvre aussi des pathogènes forestiers.
- Exemples de fiches forestières : chalarose du frêne (Hymenoscyphus fraxineus), encre du châtaignier, scolytes, rouilles, oïdiums, chancre, etc.
- Pour GSIE : source de connaissances structurées sur les maladies et ravageurs forestiers. Les fiches peuvent alimenter la base de connaissances du moteur Forest/Pathologie (symptômes, diagnostic, recommandations).

---

## 11. ICP Forests — programme international de surveillance des forêts européennes

| Champ | Valeur |
|---|---|
| **Nom officiel** | International Co-operative Programme on Assessment and Monitoring of Air Pollution Effects on Forests (ICP Forests) |
| **Organisme** | UNECE — Convention on Long-range Transboundary Air Pollution (CLRTAP) |
| **URL d'accès** | https://www.icp-forests.net/ |
| **Type d'accès** | file_download |
| **Licence** | Open Data (jeu de données Level II en open data ; Level I sur demande) |
| **Volume estimé** | Level I : ~6 000 placettes (grille systématique 16×16 km) ; Level II : > 600 placettes intensives ; jusqu'à 40 ans de suivi ; 16 enquêtes (crown condition, croissance, sols, dépôts, feuillage, etc.) |
| **Variables** | État du houppier (crown condition, déficit foliaire, causes de dommages), croissance et production, chimie du feuillage, chimie des sols, dépôts atmosphériques, solution du sol, végétation au sol, phénologie, ozone, qualité de l'air, LAI, litière |
| **Fréquence** | Level I : annuel (crown condition) ; Level II : variable selon enquête (annuel à pluriannuel) |
| **Couverture** | Europe et au-delà (42+ pays participants) |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://www.icp-forests.net/ (page d'accueil) ; https://icp-forests.org/open_data/ (open data) ; https://icp-forests.org/open_data/level_ii/index.html (dataset Level II) ; https://www.icp-forests.net/database (base de données) ; https://www.icp-forests.org/documentation/Introduction/index.html (documentation) ; https://www.icp-forests.org/pdf/ICPForests_TR2022.pdf (rapport 2022) |

### Notes techniques

- Programme lancé en 1985 sous la convention CLRTAP de l'UNECE. Pionnier du suivi de la santé des forêts à l'échelle européenne.
- Level I : grille systématique 16×16 km, ~6 000 placettes, suivi annuel de l'état du houppier et des causes de dommages. La France y participe avec ~600 placettes (réseau géré par le DSF).
- Level II : suivi intensif sur > 600 placettes avec 16 enquêtes (crown condition, croissance, sols, dépôts, feuillage, végétation, phénologie, ozone, etc.). Les placettes RENECOFOR (ONF) constituent la composante française du Level II.
- Open data : jeu de données Level II disponible en téléchargement (description générale des placettes + métadonnées). Les données détaillées s'obtiennent sur demande via le data portal.
- Documentation complète en ligne : manuel de suivi, dictionnaires, templates CSV, formulaires.
- Rapports techniques annuels (Technical Reports) avec évaluations européennes de l'état des forêts.
- Pour GSIE : source européenne de référence pour le suivi longitudinal de la santé des forêts. Les données Level I (crown condition) et Level II (multi-paramètres) sont essentielles pour les analyses de tendances et de corrélations à l'échelle européenne.

---

## 12. ForDead — détection satellitaire du dépérissement forestier (INRAE)

| Champ | Valeur |
|---|---|
| **Nom officiel** | ForDead — Python package for vegetation anomalies detection from Sentinel-2 images |
| **Organisme** | INRAE — UMR TETIS (Territoires, Environnement, Télédétection et Information Spatiale) |
| **URL d'accès** | https://fordead.gitlab.io/fordead_package/ |
| **Type d'accès** | file_import |
| **Licence** | GNU GPLv3 (logiciel libre) |
| **Volume estimé** | Traitement de séries temporelles Sentinel-2 complètes depuis 2015 ; détection au niveau pixel (10 m) ; mise à jour à chaque nouvelle acquisition Sentinel-2 |
| **Variables** | Détection d'anomalies de végétation (stress hydrique, dépérissement), date de début d'anomalie, durée, nombre de périodes d'anomalie, indices spectraux (CRSWIR, EWT) |
| **Fréquence** | Continue (mise à jour à chaque acquisition Sentinel-2, ~5 jours) |
| **Couverture** | France (et toute zone couverte par Sentinel-2, soit mondiale) |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://fordead.gitlab.io/fordead_package/ (documentation) ; https://gitlab.com/fordead/fordead_package (dépôt GitLab) ; https://www.theia-land.fr/en/blog/product/fordead-a-python-package-for-vegetation-anomalies-detection-from-sentinel-2-images/ (page THEIA) ; https://geodes.cnes.fr/detection-du-deperissement-forestier-par-intelligence-artificielle-a-partir-de-donnees-sentinel-2/ (article CNES) |

### Notes techniques

- Package Python développé par INRAE (UMR TETIS) en 2021, initialement pour la crise des scolytes sur épicéa. Détecte les anomalies de végétation à partir de séries temporelles Sentinel-2.
- Méthode : utilise les séries complètes Sentinel-2 depuis 2015, détecte les anomalies au niveau pixel (10 m) en analysant l'évolution des indices spectraux (notamment CRSWIR pour la teneur en eau). Mise à jour incrémentale à chaque nouvelle acquisition.
- Workflow en deux phases : « fit » (calibration sur période saine) puis « predict » (détection d'anomalies sur nouvelles acquisitions).
- Outils inclus : pipeline de détection, outils de calibration/validation, extraction de métriques (date de début, durée, nombre de périodes), visualisation, polygonisation pour SIG.
- Intégré dans la chaîne de traitement du DSF pour la cartographie du dépérissement (scolytes, chênes).
- Données d'entrée : images Sentinel-2 Level 2A (corrigées atmosphériquement) disponibles via THEIA (source n°13) ou Copernicus.
- Pour GSIE : outil opérationnel pour la détection précoce du dépérissement forestier par télédétection. Intégration possible comme module du moteur Forest/Pathologie pour le suivi spatial.

---

## 13. THEIA / Sentinel-2 — données satellitaires pour la santé des forêts

| Champ | Valeur |
|---|---|
| **Nom officiel** | THEIA — Pôle thématique Surfaces continentales (Sentinel-2 Surface Reflectance) |
| **Organisme** | THEIA / Data Terra / CNES-CESBIO |
| **URL d'accès** | https://www.theia-land.fr/en/products/ |
| **Type d'accès** | stac_api |
| **Licence** | Etalab Licence Ouverte v2.0 (Sentinel-2 L2A/L3A) ; CC BY-NC 4.0 (Venus) |
| **Volume estimé** | Sentinel-2 L2A : France + zones mondiales, depuis 2016, acquisition tous les 5 jours, 10 bandes spectrales, résolution 10-20 m ; Sentinel-2 L3A : synthèses mensuelles sans nuages depuis 2017 |
| **Variables** | Réflectance de surface (10 bandes spectrales visible + infrarouge), produits Level 2A (corrigés atmosphère) et Level 3A (synthèses mensuelles) |
| **Fréquence** | L2A : tous les 5 jours (Sentinel-2A + 2B) ; L3A : mensuel |
| **Couverture** | France + zones étendues (Europe, Maghreb, Sahel) — couverture mondiale sur demande |
| **Priorité GSIE** | P0 |
| **Exemples d'URL vérifiées** | https://www.theia-land.fr/en/products/ (catalogue produits) ; https://www.theia-land.fr/en/forest/ (thématique forêt) ; https://www.theia-land.fr/en/blog/product/sentinel-2-surface-reflectance/ (Sentinel-2 L2A) ; https://catalogue.theia-land.fr/ (catalogue de téléchargement) ; https://browser-theia.stac.teledetection.fr/ (STAC browser) ; https://catalogue.theia.data-terra.org/collection/forms-t (produit FORMS-T) |

### Notes techniques

- THEIA est le pôle thématique « Surfaces continentales » de la infrastructure de recherche Data Terra. Il produit et distribue des données satellitaires traitées (correction atmosphérique MAJA).
- Sentinel-2 L2A : réflectance de surface corrigée des effets atmosphériques et topographiques. Disponible pour la France depuis 2016, mise à jour en temps quasi-réel.
- Sentinel-2 L3A : synthèses mensuelles sans nuages (moyenne pondérée sur 45 jours). Disponible depuis juillet 2017 pour la France.
- Accès via catalogue THEIA (téléchargement par tuile) ou via STAC API (https://browser-theia.stac.teledetection.fr/) pour intégration programmatique.
- Produits forestiers THEIA : occupation du sol (24 classes, annuel), FORMS-T (hauteur, volume, biomasse forestière 2018-présent, 10-30 m).
- Données d'entrée pour ForDead (source n°12) et pour les études de dépérissement par télédétection.
- Pour GSIE : source de données satellitaires de référence pour le suivi de la santé des forêts par télédétection. Les produits L2A/L3A alimentent les chaînes de détection du dépérissement.

---

## 14. FCBA — Institut technologique Forêt Cellulose Bois-construction Ameublement

| Champ | Valeur |
|---|---|
| **Nom officiel** | FCBA — Institut technologique Forêt Cellulose Bois-construction Ameublement |
| **Organisme** | FCBA (Centre technique industriel des filières forêt-bois et ameublement) |
| **URL d'accès** | https://www.fcba.fr/ |
| **Type d'accès** | knowledge_extraction |
| **Licence** | Accès libre (contenu public) ; prestations et études sur devis |
| **Volume estimé** | 280 personnes ; expertise de l'amont forestier à la fin de vie des produits ; projets de recherche (ex. ScolytesWood) |
| **Variables** | Pathologies du bois (insectes xylophages, champignons lignivores, mérule), impact des ravageurs sur la qualité du bois (scolytes), durabilité et préservation du bois, identification d'essences, analyses ADN |
| **Fréquence** | Projets de recherche pluriannuels ; publications et guides techniques |
| **Couverture** | France (et Europe via partenariats) |
| **Priorité GSIE** | P2 |
| **Exemples d'URL vérifiées** | https://www.fcba.fr/ (site principal) ; https://www.fcba.fr/prestations/essais/ (laboratoires et essais) ; https://www.fcba.fr/travaux/scolyteswood/ (projet ScolytesWood) ; https://www.fcba.fr/qui-sommes-nous/notre-organisation/ (organisation) |

### Notes techniques

- FCBA est le centre technique industriel des filières forêt-bois et ameublement. Né de la fusion AFOCEL + CTBA en 2007.
- Expertise en pathologie du bois : insectes de bois sec, termites, mérule, champignons lignivores. Laboratoires d'essais et d'identification.
- Projet ScolytesWood : étude de l'impact du bois d'épicéa attaqué par les scolytes sur les procédés et produits bois (rendement Kraft, panneaux, absorption d'eau).
- Expertise en sylviculture (amélioration génétique avec INRAE), récolte de bois, approvisionnement.
- Pour GSIE : source d'expertise sur l'impact des ravageurs forestiers sur la qualité du bois et la filière. Pertinent pour le volet « conséquences économiques » des pathologies forestières. Priorité P2 car orienté filière bois plutôt que santé des forêts vivantes.

---

## 15. Atlas of Forest Pests — base de données européenne des ravageurs forestiers

| Champ | Valeur |
|---|---|
| **Nom officiel** | Atlas of Forest Pests |
| **Organisme** | Forest Protection Service (Slovaquie) — LOS |
| **URL d'accès** | https://www.forestpests.eu/ |
| **Type d'accès** | knowledge_extraction |
| **Licence** | Accès libre (contenu public) |
| **Volume estimé** | Base de données d'insectes et maladies affectant les principales essences forestières européennes ; photos ; fiches par organisme |
| **Variables** | Fiches par ravageur/pathogène : identification, symptômes, biologie, essences hôtes, photos, distribution européenne |
| **Fréquence** | Mise à jour régulière (2015-2025) |
| **Couverture** | Europe (focus Europe centrale) |
| **Priorité GSIE** | P2 |
| **Exemples d'URL vérifiées** | https://www.forestpests.eu/ (page d'accueil) ; https://www.forestpests.eu/pest-database (base de données) ; https://www.forestpests.eu/atlas (liste des ravageurs) ; https://www.forestpests.eu/insects (insectes) ; https://www.forestpests.eu/pest/dendroctonus-micans (fiche Dendroctonus micans) |

### Notes techniques

- Atlas en ligne des ravageurs et maladies forestières d'Europe, maintenu par le Forest Protection Service (Slovaquie).
- Outil d'identification : permet de déterminer la cause de dommages sur arbres et arbustes par navigation taxonomique ou par symptômes.
- Couvre les insectes (scolytes, chenilles défoliatrices, etc.) et les maladies (champignons, etc.) des principales essences européennes.
- Inclut des applications mobiles pour l'identification sur le terrain.
- Pour GSIE : source complémentaire d'identification des ravageurs forestiers européens. Moins exhaustive qu'EPPO mais avec une approche pratique d'identification par symptômes.

---

## 16. Forest Research UK — ressources maladies et ravageurs des arbres

| Champ | Valeur |
|---|---|
| **Nom officiel** | Forest Research — Pest and disease resources |
| **Organisme** | Forest Research (agence de recherche forestière du Royaume-Uni, Defra/Forestry Commission) |
| **URL d'accès** | https://www.forestresearch.gov.uk/tools-and-resources/fthr/pest-and-disease-resources/ |
| **Type d'accès** | knowledge_extraction |
| **Licence** | Accès libre (contenu public — Open Government Licence) |
| **Volume estimé** | Fiches sur > 30 maladies et ravageurs majeurs ; outil TreeAlert de signalement ; base de données THDAS (diagnostics depuis les années 1980) |
| **Variables** | Fiches par pathologie/ravageur : symptômes, biologie, distribution, impact, gestion ; cartographie des Phytophthora (> 3 000 enregistrements depuis 1975) ; signalements TreeAlert |
| **Fréquence** | Mise à jour continue |
| **Couverture** | Royaume-Uni (avec pertinence européenne) |
| **Priorité GSIE** | P1 |
| **Exemples d'URL vérifiées** | https://www.forestresearch.gov.uk/tools-and-resources/fthr/pest-and-disease-resources/ (ressources) ; https://www.forestresearch.gov.uk/tools-and-resources/fthr/tree-alert/ (TreeAlert) ; https://www.forestresearch.gov.uk/tools-and-resources/fthr/pest-and-disease-resources/dothistroma-needle-blight-dothistroma-septosporum/ (Dothistroma) ; https://www.forestresearch.gov.uk/tools-and-resources/fthr/pest-and-disease-resources/phytophthora-disease-of-alder-phytophthora-alni/ (Phytophthora alni) ; https://www.forestresearch.gov.uk/research/mapping-the-distribution-of-phytophthoras-in-britain/ (cartographie Phytophthora) ; https://www.forestresearch.gov.uk/research/focus-on-emerging-phytophthoras/ (Phytophthora émergents) |

### Notes techniques

- Forest Research est l'agence de recherche forestière du Royaume-Uni, financée par Defra, Forestry Commission, Scottish Forestry et Welsh Government.
- Fiches détaillées sur les principales maladies et ravageurs : chalarose du frêne, Dothistroma (rouille des aiguilles du pin), graphiose de l'orme, Phytophthora (P. ramorum, P. alni, P. austrocedri, P. lateralis, P. pluvialis, P. kernoviae), chancre du châtaignier (Cryphonectria parasitica), Heterobasidion annosum (pourriture racinaire), oak wilt, etc.
- TreeAlert : outil en ligne de signalement des maladies et ravageurs suspects (citoyen et professionnel).
- Base de données THDAS (Tree Health Diagnostic and Advisory Service) : enregistrements de diagnostics depuis les années 1980 (hôte, pathogène, localisation, type de bois).
- Projet de cartographie des Phytophthora : > 3 000 enregistrements analysés, cartes de distribution pour 10+ espèces de Phytophthora.
- Pour GSIE : source de connaissances de haut niveau sur les pathologies forestières avec une perspective européenne (UK). Les fiches sont très détaillées et utiles pour la base de connaissances GSIE.

---

## 17. EUROPHYT — système européen de notification des interceptions phytosanitaires

| Champ | Valeur |
|---|---|
| **Nom officiel** | EUROPHYT — European Union Notification System for Plant Health Interceptions |
| **Organisme** | Commission européenne — DG Santé et sécurité alimentaire (DG SANTE) |
| **URL d'accès** | https://food.ec.europa.eu/plants/plant-health-and-biosecurity/europhyt_en |
| **Type d'accès** | publication_text |
| **Licence** | Données publiques (tableaux de bord interactifs et rapports annuels) |
| **Volume estimé** | Notifications d'interceptions depuis 2022 (tableau de bord QlikSense) ; rapports mensuels et annuels ; données pré-2022 en archives |
| **Variables** | Interceptions d'organismes nuisibles aux frontières EU : organisme intercepté, pays d'origine, produit, date, type de non-conformité, action prise |
| **Fréquence** | Tableau de bord actualisé deux fois par mois (6 et 21 de chaque mois) ; rapports mensuels et annuels |
| **Couverture** | UE + Suisse (interceptions aux frontières et commerce intra-UE) |
| **Priorité GSIE** | P1 |
| **Exemples d'URL vérifiées** | https://food.ec.europa.eu/plants/plant-health-and-biosecurity/europhyt_en (page principale) ; https://food.ec.europa.eu/plants/plant-health-and-biosecurity/europhyt/interceptions_en (interceptions) ; https://food.ec.europa.eu/plants/plant-health-and-biosecurity/europhyt/notification-procedure_en (procédure) ; https://food.ec.europa.eu/plants/plant-health-and-biosecurity/europhyt/network_en (réseau) |

### Notes techniques

- EUROPHYT est le système européen de notification et d'alerte rapide pour les interceptions phytosanitaires. Géré par la DG SANTE de la Commission européenne.
- Trois types de notifications : (1) interceptions aux importations (organismes réglementés), (2) non-conformités non biologiques (certificats, etc.), (3) interceptions intra-UE.
- Tableau de bord interactif QlikSense : visualisation par origine, organisme nuisible, type de produit. Données depuis 2022, actualisées bimensuellement.
- Rapports annuels et mensuels avec statistiques et analyses des tendances.
- Pour GSIE : source pour la veille phytosanitaire aux frontières européennes. Pertinent pour détecter l'introduction de nouveaux organismes nuisibles forestiers (ex. via bois d'œuvre, plants, emballages bois).

---

## 18. EFSA Pest Survey Cards — fiches de surveillance des organismes de quarantaine

| Champ | Valeur |
|---|---|
| **Nom officiel** | EFSA Pest Survey Cards |
| **Organisme** | EFSA — Autorité européenne de sécurité des aliments |
| **URL d'accès** | https://www.efsa.europa.eu/en/topics/pest-surveillance |
| **Type d'accès** | publication_text |
| **Licence** | Accès libre (publications EFSA — Open Access) |
| **Volume estimé** | Fiches de surveillance pour les principaux organismes de quarantaine de l'UE ; guidelines de surveillance ; outils statistiques (RiPEST) |
| **Variables** | Fiches par organisme : biologie, distribution, hôtes, méthodes de détection, protocoles de surveillance (détection, délimitation, zone tampon), analyse de risque |
| **Fréquence** | Mise à jour continue (nouvelles fiches et révisions) |
| **Couverture** | UE (27 États membres + Islande, Norvège) |
| **Priorité GSIE** | P1 |
| **Exemples d'URL vérifiées** | https://www.efsa.europa.eu/en/topics/pest-surveillance (surveillance) ; https://www.efsa.europa.eu/en/topics/topic/plant-health (santé des plantes) ; https://www.efsa.europa.eu/en/news/protecting-europes-plants-pest-survey-cards-go-digital (digitalisation) ; https://www.efsa.europa.eu/en/supporting/pub/en-9894 (exemple fiche) |

### Notes techniques

- Les Pest Survey Cards sont préparées par l'EFSA dans le cadre de son mandat de surveillance des organismes nuisibles (M-2020-0114), à la demande de la Commission européenne.
- Outil de planification : les fiches guident les États membres dans la conception de surveillances basées sur le risque (risk-based surveys) pour les organismes de quarantaine.
- Inclut des fiches pour des organismes forestiers : Dendroctonus micans, Ips typographus, Phytophthora ramorum, Dothistroma septosporum, Cryphonectria parasitica, etc.
- Boîte à outils complète : fiches par organisme + guidelines générales + outil RiPEST (Risk-based Pest Survey Tool) pour le design statistique des surveillances.
- Réseau EFSA Plant Pest Surveillance : établi en 2022, coordonne les États membres pour harmoniser les méthodologies de surveillance.
- Pour GSIE : source de protocoles standardisés de surveillance phytosanitaire. Les fiches peuvent alimenter les recommandations de surveillance du moteur Forest/Pathologie.

---

## 19. Euphresco — réseau européen de recherche phytosanitaire

| Champ | Valeur |
|---|---|
| **Nom officiel** | Euphresco — Network for Phytosanitary Research Coordination |
| **Organisme** | Euphresco (réseau international de coordination de la recherche phytosanitaire) |
| **URL d'accès** | https://www.euphresco.net/ |
| **Type d'accès** | knowledge_extraction |
| **Licence** | Accès libre (contenu public) ; projets de recherche sur financement |
| **Volume estimé** | Réseau de partenaires de recherche phytosanitaire (organismes nationaux de protection des végétaux, instituts de recherche) ; appels à projets thématiques |
| **Variables** | Projets de recherche collègues en phytosanité (incluant pathologie forestière), rapports, publications, méthodes de diagnostic et de surveillance |
| **Fréquence** | Appels à projets annuels ; publications selon les projets |
| **Couverture** | Europe et international (partenaires mondiaux) |
| **Priorité GSIE** | P2 |
| **Exemples d'URL vérifiées** | https://www.euphresco.net/ (page d'accueil) ; https://www.era-learn.eu/network-information/networks/euphresco-ii (ERA-LEARN) ; https://cordis.europa.eu/project/id/266505/reporting (CORDIS) ; https://www.iamb.ciheam.org/euphresco/ (Euphresco III) |

### Notes techniques

- Euphresco est un réseau de coordination de la recherche phytosanitaire. Son objectif est de soutenir la collaboration entre organismes de recherche et de partager les ressources.
- Finance des projets de recherche collaboratifs sur les organismes nuisibles (diagnostic, surveillance, gestion).
- Inclut des projets sur les pathogènes forestiers (Phytophthora, scolytes, champignons pathogènes).
- Recommandation historique : ne pas créer de groupe permanent foresterie, mais inviter les bailleurs de recherche forestière à rejoindre le réseau.
- Pour GSIE : source pour identifier les projets de recherche en cours et les méthodes émergentes en pathologie forestière. Priorité P2 car principalement réseau de coordination de recherche.

---

## 20. BDIFF — base de données sur les incendies de forêts en France

| Champ | Valeur |
|---|---|
| **Nom officiel** | BDIFF — Base de Données sur les Incendies de Forêts en France |
| **Organisme** | MASA / IGN (hébergement) |
| **URL d'accès** | https://bdiff.agriculture.gouv.fr/ |
| **Type d'accès** | file_download |
| **Licence** | Etalab Licence Ouverte v2.0 (données publiques) |
| **Volume estimé** | Données sur les incendies de forêt depuis 2006 ; localisation, surfaces, causes |
| **Variables** | Localisation des incendies, surfaces brûlées, causes (naturelles, humaines), type de végétation, date, heure |
| **Fréquence** | Mise à jour continue (saisonnalité estivale) |
| **Couverture** | France métropolitaine (et DOM) |
| **Priorité GSIE** | P2 |
| **Exemples d'URL vérifiées** | https://bdiff.agriculture.gouv.fr/ (application) ; https://www.data.gouv.fr/datasets/base-de-donnees-sur-les-incendies-de-forets-en-france-bdiff (data.gouv.fr) ; https://outil2amenagement.cerema.fr/outils/la-base-donnees-sur-les-incendies-forets-en-france-bdiff (description Cerema) |

### Notes techniques

- La BDIFF centralise les données sur les incendies de forêt en France depuis 2006. Hébergée par l'IGN.
- Données téléchargeables via data.gouv.fr. Application web pour consultation et requêtes.
- Pertinence pour la pathologie forestière : les incendies affaiblissent les peuplements et favorisent les infestations secondaires (scolytes sur arbres brûlés, pourritures). Les données BDIFF peuvent croiser avec les données sanitaires du DSF.
- Pour GSIE : source pour les facteurs abiotiques interagissant avec la santé des forêts. Priorité P2 car indirectement lié à la pathologie (facteur prédisposant plutôt que pathogène direct).

---

## 21. Synthèse — Priorités et lacunes pour GSIE

### Sources P0 — indispensables pour le moteur Forest/Pathologie

| Source | Rôle pour GSIE |
|---|---|
| **EPPO Global Database** (n°1) | Référentiel taxonomique et statut réglementaire des organismes nuisibles (quarantaine A1/A2, Alert List) |
| **EPPO Data Portal / API REST** (n°2) | Intégration programmatique du référentiel EPPO (codes, distribution, hôtes) |
| **DSF** (n°4) | Observations sylvosanitaires françaises (15 000/an), bilans annuels, suivi des crises (scolytes, chalarose) |
| **DEPERIS** (n°5) | Protocole de terrain de référence pour l'évaluation du dépérissement (notes A-F) |
| **Observatoire des forêts françaises** (n°6) | Portail unifié des indicateurs sanitaires français (dépérissement, mortalité, surfaces touchées) |
| **inventIF Santé (IGN)** (n°7) | Données quantitatives de santé par essence et territoire (DEPERIS, mortalité, ARCHI) |
| **Ephytia (INRAE)** (n°10) | Base de connaissances structurées : ~200 fiches maladies/ravageurs forestiers (symptômes, diagnostic, gestion) |
| **ICP Forests** (n°11) | Suivi européen long terme (Level I : 6 000 placettes, Level II : 600 placettes, 16 enquêtes) |
| **ForDead (INRAE)** (n°12) | Outil opérationnel de détection satellitaire du dépérissement (Sentinel-2, détection précoce) |
| **THEIA / Sentinel-2** (n°13) | Données satellitaires de référence (L2A/L3A) alimentant les chaînes de télédétection sanitaire |

### Sources P1 — importantes

| Source | Rôle pour GSIE |
|---|---|
| **EPPO Q-Bank** (n°3) | Identification moléculaire des pathogènes (barcodes ADN) pour validation de diagnostics |
| **RENECOFOR (ONF)** (n°8) | Suivi intensif long terme (102 placettes, 30+ ans) — composante française du Level II |
| **ONF Open Data** (n°9) | Contours géographiques des forêts publiques (couche spatiale de référence) |
| **Forest Research UK** (n°16) | Fiches maladies de haut niveau (Dothistroma, Phytophthora, Heterobasidion, chalarose) + TreeAlert |
| **EUROPHYT** (n°17) | Veille phytosanitaire aux frontières UE (interceptions d'organismes nuisibles) |
| **EFSA Pest Survey Cards** (n°18) | Protocoles standardisés de surveillance (risk-based surveys) pour organismes de quarantaine |

### Sources P2 — nice-to-have

| Source | Rôle pour GSIE |
|---|---|
| **FCBA** (n°14) | Impact des ravageurs sur la qualité du bois et la filière (volet économique) |
| **Atlas of Forest Pests** (n°15) | Identification des ravageurs par symptômes (approche pratique, Europe centrale) |
| **Euphresco** (n°19) | Veille sur les projets de recherche phytosanitaire en cours |
| **BDIFF** (n°20) | Facteurs abiotiques (incendies) interagissant avec la santé des forêts |

### Lacunes identifiées

1. **Accès aux données brutes du DSF** : la base de données d'observations sylvosanitaires (~15 000/an) n'est pas en open data direct. Les données sont diffusées via bilans (PDF) et l'Observatoire des forêts françaises (indicateurs agrégés). Un accord avec le DSF/DGAL serait nécessaire pour un accès aux observations ponctuelles géoréférencées.

2. **Données de piégeage scolytes en temps réel** : les réseaux de piégeage d'Ips typographus (DRAAF AuRA, Grand Est) publient des synthèses hebdomadaires en saison (avril-juin), mais les données brutes par piège ne sont pas en téléchargement structuré. Format PDF ou pages web.

3. **Suivi de la chalarose du frêne** : le suivi de l'épidémie (depuis 2008) est documenté dans les publications du DSF et d'INRAE (UMR IAM), mais il n'existe pas de base de données publique géoréférencée de la progression annuelle. Les cartes de progression sont publiées dans les bilans.

4. **Données Phytophthora en France** : contrairement au Royaume-Uni (Forest Research, > 3 000 enregistrements cartographiés), la France ne dispose pas d'une base de données publique de distribution des Phytophthora forestiers. Les signalements sont dans la base DSF (non ouverte).

5. **Interopérabilité ICP Forests / DSF** : les placettes françaises du réseau 16×16 km (Level I) et RENECOFOR (Level II) sont gérées respectivement par le DSF et l'ONF, mais les données françaises ne sont pas directement téléchargeables depuis le portail ICP Forests (accès sur demande). L'open data ICP Forests ne couvre que les métadonnées Level II.

6. **Télédétection opérationnelle du dépérissement** : ForDead (INRAE) est un outil mature et open source, mais les produits cartographiques générés (cartes de dépérissement scolytes, chênes) ne sont pas systématiquement publiés en open data. Le DSF pilote la production mais la diffusion est partielle (via l'Observatoire des forêts françaises en indicateurs agrégés).

7. **Intégration EPPO → pathologies forestières spécifiques** : EPPO couvre tous les organismes de quarantaine (agricoles, forestiers, ornementaux). Un filtrage par hôtes forestiers est nécessaire pour extraire le sous-ensemble pertinent pour GSIE. L'API REST (source n°2) permet ce filtrage via les relations hôte-pest.

### Recommandations pour GSIE

- **Priorité d'intégration** : commencer par l'API EPPO (référentiel taxonomique) + Ephytia (fiches connaissances) + inventIF Santé (données quantitatives françaises) + ICP Forests open data (contexte européen).
- **Chaîne de télédétection** : intégrer ForDead comme module de détection spatiale, alimenté par les données Sentinel-2 THEIA (STAC API).
- **Partenariat DSF** : établir un accord avec le DSF/DGAL pour l'accès aux observations sylvosanitaires géoréférencées (15 000/an). C'est le verrou principal pour une couverture fine de la pathologie forestière française.
- **Veille phytosanitaire** : intégrer EUROPHYT (interceptions aux frontières) et EFSA Pest Survey Cards (protocoles de surveillance) pour le volet veille/réglementaire.
- **Base de connaissances** : structurer les fiches Ephytia + Forest Research UK dans la base de connaissances GSIE (symptômes → diagnostic → recommandations).
