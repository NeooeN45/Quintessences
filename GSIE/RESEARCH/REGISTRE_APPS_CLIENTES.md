# Registre des opportunités — Applications clientes

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-REG-APPS |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Dernier reclassement** | 2026-08-16 |
| **Cible** | Ignis (incendies) · Hydro (eau) · Flora (végétation) · Terra (sols) · Aeris (atmosphère) · Atlas (cartographie) · Artemis (faune) |
| **Contraintes de la cible** | Domaines scientifiques distincts · calibration territoriale obligatoire · responsabilité opérationnelle · licences hétérogènes |
| **Registres frères** | GSIE Serveur · GSIE PC · Applications mobiles · Hub Unreal Engine |

---

## 1. Comment lire ce registre

Identifiants `OPP-xxx` stables et uniques dans tous les registres. Classement sur
le seul **intérêt**, de 1 à 5, toutes applications confondues — une seule liste,
de la plus intéressante à la moins intéressante, avec la colonne « App » pour
retrouver son domaine. Le **verrou** décrit ce qui bloque et ce qu'il faudrait
pour le lever ; ce n'est pas une pénalité de rang.

**Statuts** : INTÉGRER · BENCHMARKER · SURVEILLER · ÉCARTER.

---

## 2. Quatre règles qui priment sur tout classement

Une par domaine, toutes issues de l'étude du 18 juillet. Elles ne se négocient
pas au cas par cas.

**Ignis — la ligne rouge.** Tant que les validations terrain, la responsabilité,
les seuils de sécurité, la disponibilité opérationnelle et la gouvernance humaine
ne sont pas établis, Ignis se présente comme *simulateur de scénarios*, *outil de
préparation et de retour d'expérience*, *visualisateur de données et
d'incertitude* — **jamais** système autonome de commandement ni prédicteur
garanti.

**Hydro — la validité ne se transfère pas.** Un modèle hydrologique appris sur de
grands bassins américains ou mondiaux ne devient pas valide sur un petit bassin
forestier français karstique, méditerranéen ou fortement anthropisé. La
calibration par bassin est un préalable, pas un réglage fin.

**Aeris — la donnée opérationnelle avant le modèle expérimental.** Météo-France,
ECMWF et Copernicus restent prioritaires. Un modèle appris peut servir d'ensemble,
de descente d'échelle ou d'expérimentation — jamais remplacer silencieusement une
source opérationnelle sans validation ni avertissement.

**Flora et Artemis — l'observation incertaine se conserve.** Le modèle ne
supprime jamais une observation douteuse et ne fusionne jamais deux taxons
proches. Toute détection affiche espèces candidates, score calibré, zone et
saison utilisées, qualité du média, modèle et version, avec bouton de
confirmation ou de correction. Une espèce rare, protégée ou à fort enjeu exige
une validation renforcée et la conservation du média source.

---

## 3. Classement au 2026-08-16

| Rang | ID | App | Opportunité | Intérêt | Verrou actuel | Pour le lever | Statut |
|---:|---|---|---|:-:|---|---|---|
| 1 | OPP-009 | Hydro | **airGR** — modèles pluie-débit GR, neige CemaNeige | 5 | R/GPL-2 ; calibration par bassin indispensable | Commencer sur un ou deux bassins bien documentés | INTÉGRER |
| 2 | OPP-015 | Ignis | **ForeFire** — propagation, couplages atmosphériques | 5 | GPL-3.0 ; validation française à établir | Banc Ignis simulé ; relation CNRS/Université de Corse déjà amorcée | INTÉGRER |
| 3 | OPP-085 | Ignis | **Pyretechnics** — comportement du feu, modulaire et explicable | 5 | EPL-2.0 ; à confronter à ForeFire | Intégrer au benchmark comme outil de comparaison de formules | INTÉGRER |
| 4 | OPP-133 | Aeris | **Météo-France · ECMWF · Copernicus** — sources opérationnelles | 5 | Conditions de réutilisation à qualifier par produit | Contractualiser l'accès avant tout modèle appris | INTÉGRER |
| 5 | OPP-087 | Ignis | **xclim** — indices climatiques, briques du Fire Weather Index | 4 | Calibration française nécessaire | Fournisseur d'indicateurs de danger, calibré sur données FR | INTÉGRER |
| 6 | OPP-128 | Terra | **RothC_R** — carbone organique des sols | 4 | Mesures initiales nécessaires ; hypothèses à déclarer | Scénarios calibrés sur parcelles instrumentées | INTÉGRER |
| 7 | OPP-127 | Terra | **SoilGrids** — propriétés des sols mondiales avec incertitudes | 4 | Résolution et biais globaux ; l'ISRIC recommande la comparaison aux cartes nationales | Usage strict en **a priori** et covariable — jamais vérité de parcelle | INTÉGRER |
| 8 | OPP-090 | Hydro | **NeuralHydrology** — cadre ML pluie-débit | 4 | Pas un modèle prêt à l'emploi ; entraînement par cas | Comparer à airGR **sans supposer sa supériorité** | BENCHMARKER |
| 9 | OPP-098 | Flora / Artemis | **PyTorch-Wildlife** — détecteurs et classifieurs faune | 4 | **Licence différente pour chaque checkpoint** ; certaines variantes MegaDetector sont AGPL | Adopter la plateforme avec une **liste blanche de modèles** explicite | INTÉGRER |
| 10 | OPP-100 | Flora | **biomod2** — ensembles de modèles de distribution d'espèces | 3 | Très dépendant des absences/pseudo-absences et des biais d'échantillonnage | Usage côté analyse, avec expertise écologique | INTÉGRER |
| 11 | OPP-091 | Hydro | **SWAT+** — bassin, qualité, érosion, usage des terres | 3 | Paramétrage lourd, incertitude structurale, expertise requise | Activer seulement quand les données nécessaires existent | SURVEILLER |
| 12 | OPP-092 | Hydro | **LISFLOOD** (JRC, EUPL-1.2) — hydrologie distribuée et crues | 3 | Résolution et usage local à valider | Benchmark territorial sur bassin pilote | BENCHMARKER |
| 13 | OPP-086 | Ignis | **ELMFIRE** — propagation, probabilité de brûlage, sévérité | 3 | EPL-2.0 ; Fortran/Python | Banc de comparaison face à ForeFire et Pyretechnics | BENCHMARKER |
| 14 | OPP-035 | Ignis | **cuOpt** — affectation de moyens et itinéraires | 3 | Dépendance NVIDIA ; scénario non formalisé | Scénario Ignis d'affectation, sur endpoints hébergés | BENCHMARKER |
| 15 | OPP-093 | Hydro | **HydroMT + Wflow** (Deltares) | 3 | Courbe d'apprentissage et dépendances de données | Après le premier bassin airGR | SURVEILLER |
| 16 | OPP-099 | Flora / Artemis | **Perch** — embeddings audio multi-taxa, Apache-2.0 | 3 | Logits non calibrés ; espèces rares difficiles selon la *model card* | Benchmark face à BirdNET sur enregistrements français | BENCHMARKER |
| 17 | OPP-134 | Aeris | **Aurora** — modèle de fondation du système Terre, MIT | 3 | **Le projet avertit lui-même de ne pas l'utiliser seul pour des décisions opérationnelles** | Scénarios expérimentaux et ensembles, en P2 | BENCHMARKER |
| 18 | OPP-135 | Aeris | **NeuralGCM** — hybride dynamique + ML | 3 | Code Apache-2.0 mais **checkpoints sous conditions CC BY-SA** | Vérifier la compatibilité des poids avant tout usage | BENCHMARKER |
| 19 | OPP-130 | Terra | **OpenFLUID** — flux dans les paysages, plateforme française | 2 | Intégration et modèles à étudier au cas par cas | Piste pour le continuum eau/sol/paysage | SURVEILLER |
| 20 | OPP-094 | Hydro | **TELEMAC-MASCARET** (EDF, GPL) — hydraulique 1D/2D/3D | 2 | Maillage, calcul et expertise importants | Réserver aux études exigeant réellement cette finesse | SURVEILLER |
| 21 | OPP-095 | Hydro | **MODFLOW 6** (USGS) — eaux souterraines | 2 | Modèle conceptuel et paramètres hydrogéologiques nécessaires | P2 souterrain | SURVEILLER |
| 22 | OPP-137 | Aeris | **WRF** — modélisation atmosphérique régionale | 2 | HPC ; très lourd | Études régionales avancées, couplage feu | SURVEILLER |
| 23 | OPP-088 | Ignis | **WRF-Fire** — couplage météo-feu haute fidélité | 2 | Très lourd ; recherche/HPC | Pas pour le MVP Ignis | SURVEILLER |
| 24 | OPP-136 | Aeris | **Prithvi-WxC · ClimaX · FourCastNet** | 2 | Calcul et données lourds | Baselines scientifiques de comparaison | SURVEILLER |
| 25 | OPP-089 | Ignis | **Jeux de données ML de propagation** — Next Day Wildfire Spread, WildFireSpreadTS, Mesogeos | 2 | **Ne constituent pas une validation opérationnelle française** — combustibles, résolution, biais et politiques d'extinction diffèrent | Usage recherche uniquement, jamais comme preuve | SURVEILLER |
| 26 | OPP-126 | Flora | **elapid · maxnet** — modèles de niche type Maxent | 2 | Corrélation environnement-présence — ni causalité, ni abondance | Benchmark face à biomod2 | BENCHMARKER |
| 27 | OPP-129 | Terra | **SoilR** — décomposition de la matière organique | 2 | Bibliothèque scientifique, pas résultat prêt à l'emploi | Outil de recherche et de validation | SURVEILLER |
| 28 | OPP-096 | Hydro | **ParFlow** — surface/sous-sol intégré | 1 | Très lourd pour un premier produit | Réévaluer après le vertical slice hydrologique | SURVEILLER |
| 29 | OPP-097 | Hydro | **EPA SWMM · WNTR** — réseaux urbains et résilience | 1 | Hors cœur forestier initial | Module urbain futur | SURVEILLER |
| 30 | OPP-131 | Terra | **DayCent** — cycle carbone/azote/eau | 1 | **Accès et licence de la version exacte à confirmer** | Revue juridique avant toute intégration | SURVEILLER |
| 31 | OPP-132 | Terra | **PCSE / WOFOST · AquaCrop-OSPy** | 1 | Paramètres culturaux régionaux indispensables ; AquaCrop-OSPy n'est pas l'implémentation FAO officielle | Module agriculture futur | SURVEILLER |
| 32 | OPP-138 | Aeris | **CMAQ** — qualité de l'air et chimie atmosphérique | 1 | Projet lourd | Module atmosphère futur | SURVEILLER |

---

## 3bis. Enrichissement — recherche web du 2026-08-16

**airGR — la famille de modèles confirmée en détail.** Développé par l'unité
HYCAR de l'INRAE-Antony, le paquet couvre GR4H, GR5H (horaires), GR4J, GR5J,
GR6J (journaliers), GR2M (mensuel) et GR1A (annuel), avec le modèle de neige
CemaNeige associé. Le cœur de chaque modèle est codé en Fortran pour la
vitesse de calcul, la calibration et les critères d'efficacité restant en R —
conçu explicitement pour rester accessible à des utilisateurs non experts. Ce
niveau de détail conforte le rang 1 de OPP-009 : c'est un outil mûr et
activement maintenu, pas une bibliothèque de recherche isolée.

**ForeFire — la validation opérationnelle est plus riche que prévu, et le
partenaire n'est pas seulement académique.** Le système couplé
**MesoNH-ForeFire** associe l'Université de Corse, le CNRS **et Météo-France**
— la source opérationnelle française elle-même est déjà partie prenante du
développement du modèle. ForeFire a été validé par confrontation à des feux
réels majeurs : Aullène 2009 (Corse), Pedrógão Grande 2017 (Portugal, 66
morts), Vésuve 2017 (Italie). Une publication de 2026 dans le *Quarterly
Journal of the Royal Meteorological Society* analyse la dynamique d'un
méga-feu au Portugal avec ce système couplé à interaction bidirectionnelle
(la chaleur et la vapeur du feu modifient l'atmosphère, le vent de surface
pilote la propagation).

**Ce que ça change pour OPP-015 :** le rang 2 déjà attribué à ForeFire est
renforcé, pas remis en cause — mais la mention « validation française à
établir » de la colonne verrou doit être nuancée. La validation existe sur des
feux méditerranéens réels, via un partenariat qui inclut déjà Météo-France.
Ce qui reste à établir est une validation sur *nos* territoires cibles
spécifiquement, pas une validation du modèle en général.

---

## 4. Fiches — les quatre premiers

### OPP-009 · airGR — commencer français
Modèles pluie-débit GR4H à GR1A avec neige CemaNeige, calibration et évaluation,
développés dans l'écosystème INRAE. Sa force n'est pas la sophistication mais
l'**adéquation territoriale** : il a été construit pour les bassins français, ce
qui n'est le cas d'aucun modèle appris disponible.

La stratégie eau qui en découle : un ou deux bassins bien documentés d'abord ;
comparaison à un modèle neuronal ensuite, sans préjuger du résultat ;
enregistrement systématique des périodes de calibration et de validation, des
stations, des données météo, des lacunes, des transformations et des incertitudes.

### OPP-015 · ForeFire — le meilleur candidat français
Propagation, modèles de vitesse, entrées/sorties géospatiales, couplages
atmosphériques. GPL-3.0, développé au CNRS et à l'Université de Corse, publié
dans JOSS. C'est le meilleur candidat pour un Ignis français et méditerranéen
expérimental, et la relation académique est déjà amorcée.

### OPP-085 · Pyretechnics — l'outil qui rend les formules discutables
Bibliothèque transparente de comportement du feu : surface, cime, sautes de feu,
combustibles, humidité. Son intérêt n'est pas de remplacer ForeFire mais de
**rendre les calculs comparables** — approche modulaire, formules explicites.
Dans un domaine où l'on doit pouvoir justifier chaque chiffre devant un
opérationnel, c'est une qualité rare.

### OPP-133 · Les sources opérationnelles avant tout modèle appris
Ce n'est pas un modèle, et c'est précisément pourquoi elle est au rang 4. Aucune
des opportunités Aeris de ce registre — Aurora, NeuralGCM, Prithvi-WxC — ne
remplace Météo-France, ECMWF ou Copernicus pour un usage professionnel français.
Les modèles appris viennent en ensemble, en descente d'échelle ou en
expérimentation, avec avertissement explicite.

---

## 5. Renvois croisés

| ID | Opportunité | Foyer | Ce qu'elle apporte ici |
|---|---|---|---|
| OPP-012 | **BioCLIP 2** — embeddings image-texte taxonomiques, MIT | GSIE Serveur | Shortlist d'espèces pour Flora ; probabilités jamais équivalentes à une identification |
| OPP-008 | **BirdNET** — bioacoustique offline, MIT | Applications mobiles | Reconnaissance terrain pour Artemis ; seuils à calibrer par zone et saison |
| OPP-004 | **DoWhy + Tigramite** | GSIE Serveur | Le moteur de corrélation dessert toutes les applications de ce registre |
| OPP-011 | **Prithvi-EO-2.0 + AnySat** | GSIE Serveur | Socle d'Atlas ; cartographie globale |
| OPP-055 | **CoSIA / OCS GE (IGN)** | GSIE PC | Occupation du sol pour Atlas et Terra |
| OPP-047 | **iLand · LANDIS-II** | GSIE PC → serveur | Dynamique forestière à l'échelle du paysage |

**Atlas n'a aucune opportunité en propre** dans ce registre. C'est cohérent :
l'application est un consommateur de couches produites ailleurs, pas un domaine
scientifique autonome. Si cela change, elle prendra ses propres lignes.

---

## 6. Écartées — motifs durs uniquement

| ID | App | Opportunité | Motif |
|---|---|---|---|
| OPP-140 | Aeris | **GraphCast / GenCast via WeatherNext** | Code Apache-2.0, mais **certains poids sont CC BY-NC-SA** — incompatible avec un cœur commercial sans accord. |
| OPP-141 | Terra | **APSIM** | Licence communautaire restrictive pour certains usages commerciaux. Écarté du cœur sans accord écrit. |
| OPP-142 | Ignis | **Cell2Fire** | GPL-3.0 mais mentions d'usage recherche, et **combustibles canadiens** — mauvaise base par défaut pour la France. |
| OPP-143 | — | **CausalNex** | Fin de vie en juin 2026. Ne pas créer de nouvelle dépendance. |
| OPP-144 | Ignis | **Ignis en système autonome de commandement** | Contredit la règle §2. Définitif. |

---

## 7. Le motif qui traverse tout ce registre

Sur trente-deux opportunités, la quasi-totalité des verrous relève de la **même
famille** : la calibration territoriale. airGR demande une calibration par
bassin ; xclim une calibration française ; SoilGrids une comparaison aux cartes
nationales ; ForeFire une validation française ; les jeux de données ML de
propagation ne valent pas validation opérationnelle chez nous ; NeuralHydrology
exige un entraînement par cas.

Ce n'est pas une coïncidence, c'est la nature du domaine : **un modèle
environnemental est valide sur son territoire de calibration, pas au-delà**. Le
travail qui débloque ce registre n'est donc pas de trouver de meilleurs modèles,
mais de constituer les jeux de calibration français qui les rendent utilisables.

C'est le pendant, côté science, du constat déjà fait côté IA : le corpus commande
davantage que le modèle.

---

## 8. Sources absorbées

| Document d'origine | Apport |
|---|---|
| `ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18` (§6 à §11) | Eau, feux, climat, biodiversité, sols et carbone, moteur de corrélation |
| `VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20` | cuOpt, Earth2Studio, réserve sur les alertes automatiques |
| `UNREAL_ENGINE_PRECEDENTS` | Précédents Ignis, garde-fous d'autonomie |

**Restent à répartir** dans une passe ultérieure : `VEILLE_AUDIT_CONCURRENTIEL_GEOSYLVA_2026-07-20`
(destination : registre Applications mobiles), `JUNN_VEILLE`,
`VEILLE_INNOVATIONS_QUINTESSENCES_2026-07-20`, `VEILLE_2026-07-15`,
`VEILLE_2026-08-09` et `VEILLE_TECHNO_2026-08-02`.

---

## 9. Journal des reclassements

| Date | Mouvement | Motif |
|---|---|---|
| 2026-08-16 | Création — 32 opportunités actives, 5 écartées, 6 renvois croisés | Consolidation par cible d'exécution |
| 2026-08-16 | OPP-133 (sources opérationnelles) classée devant tous les modèles météo appris | Règle §2 Aeris : la donnée opérationnelle prime sur le modèle expérimental |
| 2026-08-16 | OPP-098 (PyTorch-Wildlife) conservée au rang 9 malgré ses licences hétérogènes | Le verrou se lève par une liste blanche de checkpoints, pas par l'abandon de la plateforme |
| 2026-08-16 | OPP-015 (ForeFire) — verrou nuancé, rang inchangé | Validation confirmée sur feux méditerranéens réels avec Météo-France partenaire ; reste à établir sur nos territoires spécifiques |

---

## 10. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 1.0.0 | 2026-08-16 | Claude | Création — registre par cible d'exécution |
