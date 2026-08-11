# GSIE Environmental Digital Twin Platform — Cas d'usage réels fédérés

| Champ | Valeur |
|---|---|
| **Livrable** | Catalogue de cas d'usage réels pour la plateforme de jumeau numérique fédéré |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation (cadrage) |
| **RFC** | RFC-0037 |
| **Documents liés** | `GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md`, `HUB_001_SPECIFICATION.md`, `SIMULATION_ENGINE.md`, `TERRITORIAL_MESH_PROTOTYPE_V0.md`, `SERVER_MESHING_PROTOTYPE_V0.md` |

---

## 1. Objectif

Ce catalogue recense des cas d'usage réels, documentés et sourçables, que la plateforme de jumeau numérique environnemental fédéré GSIE peut adresser. Chaque cas part d'un événement ou d'une crise constatée, identifie les projections métier concernées, les ressources échangées, les décisions supportées et les moyens de validation.

Les cas ne sont pas des spécifications d'implémentation. Ils servent à :

- valider la pertinence de l'architecture fédérée sur des besoins concrets ;
- prioriser les tranches verticales de la roadmap RFC-0037 ;
- aligner les projections GeoSylva, Ignis, Hydro, Flora, Artemis et QGISIA sur des flux inter-domaines réels ;
- nourrir les scénarios du `Simulation Engine`, du Hub Unreal et des tests d'acceptation.

## 2. Méthodologie

Chaque cas d'usage suit le même schéma :

| Rubrique | Contenu |
|---|---|
| **Événement de référence** | Date, périmètre, ordre de grandeur, source |
| **Projections concernées** | Domaines GSIE impliqués |
| **Ressources échangées** | `Observation`, `Forecast`, `Scenario`, `SimulationRun`, `Mission`, `ActionRequest` |
| **Décisions supportées** | Type de décideur, action possible, contrainte d'autorité |
| **Validation possible** | Données de référence, critère de succès, prototype envisageable |
| **Maturité** | Données accessibles, modèles disponibles, besoin de recherche |

Les cas sont classés par degré de fédération croissant : du cas principalement mono-domaine au cas multi-domaines avec action critique.

## 3. Cas d'usage

### UC-001 — Ruissellement et érosion post-incendie en forêt méditerranéenne

| Rubrique | Détail |
|---|---|
| **Événement de référence** | Incendie des Maures (août 1990, 8 400 ha ; été 2017, 1 800 ha) ; incendies de Landiras et La Teste-de-Buch (juillet-août 2022, > 6 500 ha) ; crues éclair post-incendie dans l'Aude (Monze, 2019) et les Pyrénées-Orientales (Cerbère). |
| **Sources** | BRGM `RP-69494-FR` sur Bormes-les-Mimosas ; Persée — Martin & Chevalier (1993) sur le Real Collobrier ; SMEGREG (2022) ; Copernicus EMSR592 ; MONTCLIMA guide post-fire erosion. |
| **Projections** | **Ignis** (feu) → **Hydro** (ruissellement, érosion, crue) → **GeoSylva** (mortalité, régénération, restauration) → **Flora** (changement de végétation) → **Artemis** (habitats perturbés). |
| **Ressources échangées** | - `Observation` (contours brûlés, sols exposés, perte de couvert végétal) produite par Ignis. <br>- `Forecast` de ruissellement et de transport solide produite par Hydro à partir des surfaces brûlées. <br>- `Scenario` de restauration et de reboisement produit par GeoSylva. <br>- `Recommendation` de placement d'ouvrages de protection. |
| **Décisions supportées** | Placement de barrages à sédiments, restriction d'accès au massif, plan de restauration, choix d'essences de régénération, alerte crue post-incendie. |
| **Validation possible** | Rejeu sur le bassin versant du Real Collobrier (Maures) ou sur un secteur Landiras ; comparaison aux mesures de ruissellement et de transport solide disponibles dans la littérature. |
| **Maturité** | Élevée — modèles de ruissellement post-incendie documentés, données Sentinel-2 et Landsat disponibles, mesures terrain dans les BVRE du Real Collobrier. |

**Intérêt pour GSIE.** Ce cas est la figure même de la fédération : un événement Ignis génère des conséquences Hydro, GeoSylva et Flora. Il pousse le modèle de ressource fédérée (`state_kind`, `scenario_id`, `provenance`) et le Hub multi-domaines (superposition forêt, feu, eau).

---

### UC-002 — Crise scolytes du sapin pectiné et dépérissement forestier

| Rubrique | Détail |
|---|---|
| **Événement de référence** | Épidémie d'*Ips typographus* et dépérissement du sapin pectiné en Grand-Est, Bourgogne-Franche-Comté, Vosges et Ardenne (2018-2023), après les sécheresses 2018-2020 et 2022. |
| **Sources** | DRAAF BFC info technique mars 2023 ; Nardi et al. (2023) ; `fordead` package INRAE/INRIA ; Orbi ULiège — évaluation de la fin de l'épidémie dans le nord-est de la France. |
| **Projections** | **Climate** (stress hydrique, sécheresse) → **GeoSylva** (inventaire, essences, peuplements) → **Flora** (végétation, santé du couvert) → **Forest Dynamics** (mortalité, croissance) → **Artemis** (habitats faune). |
| **Ressources échangées** | - `Observation` de dépérissement par série temporelle Sentinel-2 (Flora/GeoSylva). <br>- `Forecast` de stress hydrique (Climate). <br>- `Scenario` de coupe sanitaire et de conversion d'essences (GeoSylva + Simulation). <br>- `Recommendation` de priorité de surveillance. |
| **Décisions supportées** | Coupe sanitaire, choix d'essences de remplacement, plan de surveillance, adaptation des plans d'aménagement forestier. |
| **Validation possible** | Détection précoce sur parcelles d'essai dans les Vosges ; comparaison aux cartes de santé du sapin produites par `fordead`. |
| **Maturité** | Élevée — séries Sentinel-2, modèles de stress hydrique, références ONF et INRAE. |

**Intérêt pour GSIE.** Ce cas pousse la fédération GeoSylva ↔ Flora ↔ Climate et la capacité du jumeau à détecter un dépérissement avant sa généralisation. Il nécessite des séries temporelles bitemporelles et un modèle de perturbation forestière (`type: ravageur`).

---

### UC-003 — Pilotage opérationnel d'incendie avec SITAC multi-moyens

| Rubrique | Détail |
|---|---|
| **Événement de référence** | Gestion des feux de forêt en Haute-Corse (SDIS 2B, ~1 750 ha/an) ; projet ADAGES (Lot) avec Crimson Tactic ; système Asphodèle (SDIS 06) ; programme NexSIS 18-112 (ANSC). |
| **Sources** | Eurisy — SDIS 2B satellite information for realtime tactic management ; ANSC NexSIS 18-112 ; ANSC moteur de mobilisation ; Pompiers du Lot — Crimson Tactic. |
| **Projections** | **Ignis** (front, propagation, enjeux) + **Hub Unreal** (visualisation immersive) + **Territorial Mesh** (DOD/RCH, autorité) + **GeoSylva** (combustible, pistes). |
| **Ressources échangées** | - `Observation` temps réel (position des moyens, drones, Canadair, hotspots). <br>- `Forecast` de propagation (ForeFire). <br>- `Scenario` de positionnement des moyens. <br>- `ActionRequest` pour demander un largage, une trajectoire ou une mission drone. <br>- `Decision` validée par le COS. |
| **Décisions supportées** | Positionnement des moyens terrestres, coordination aéronefs/drones, évacuation d'enjeux, choix de ligne de défense. |
| **Validation possible** | Replay d'un feu historique en Corse ou en Lot-et-Garonne ; scénario avec un opérateur unique, puis plusieurs opérateurs via Server Meshing. |
| **Maturité** | Moyenne à élevée — besoin d'intégrer les protocoles opérationnels (NexSIS, SITAC) sans les remplacer ; fédération Territorial Mesh nécessaire. |

**Intérêt pour GSIE.** Ce cas pousse le Hub Ignis, le contrat `ActionRequest` et la séparation entre intention opérateur et commande physique. Il illustre la règle : le Hub ne commande pas directement les aéronefs ou les drones, il prépare une demande validée par l'autorité compétente.

---

### UC-004 — Prévision des crues éclair et hydrologie karstique

| Rubrique | Détail |
|---|---|
| **Événement de référence** | Crue du Gard et du Vidourle des 8-9 septembre 2002 (24 décès, 1,2 Md€ de dégâts) ; épisodes cévenols récurrents ; hydrologie du karst du Larzac et de la source du Durzon. |
| **Sources** | OHM-CV — Cévennes-Vivarais Mediterranean Hydrometeorological Observatory ; SHF LHB 2004/6 ; Parc national des Cévennes ; OREME — Observatoire du Larzac / Durzon ; SCHAPI — Vigicrues Flash. |
| **Projections** | **Hydro** (bassins versants, crues, karst) + **Climate** (pluies, vigilance) + **Ignis** (si crue post-incendie) + **GeoSylva** (couvert forestier, infiltration). |
| **Ressources échangées** | - `Observation` (pluie, débit, niveau de nappe). <br>- `Forecast` de crue éclair (Hydro + Climate). <br>- `Scenario` d'épisode pluvieux et d'impact sur les infrastructures. <br>- `Mission` de surveillance des ouvrages et des exutoires. |
| **Décisions supportées** | Alerte des communes, fermeture de routes, gestion des retenues, planification des secours, restriction d'accès aux massifs brûlés. |
| **Validation possible** | Replay de la crue du 8-9 septembre 2002 sur le Gard ; calage sur la source du Durzon (Larzac) avec mesures OREME. |
| **Maturité** | Élevée — modèles AIGA/SMASH (Vigicrues Flash), données hydrométriques et radar Météo-France, observatoires karstiques. |

**Intérêt pour GSIE.** Ce cas pousse Hydro comme projection autonome et en tant que consommateur des sorties Ignis. Il nécessite des modèles hydrologiques distribués, de l'assimilation de pluie et une gestion des zones humides / karstiques.

---

### UC-005 — Gestion de la biodiversité forestière et des corridors écologiques

| Rubrique | Détail |
|---|---|
| **Événement de référence** | Suivi des habitats forestiers d'intérêt communautaire (Annexe I Habitats Directive) ; projets BioDT Forest Biodiversity Dynamics, Forest DTC (ESA), SenseForest (Biodiversa+), FORWARDS ForestWard Observatory. |
| **Sources** | BioDT Forest Biodiversity Dynamics ; Forest DTC use cases (Finland, Catalonia, Czechia) ; SenseForest pilot Biodiversa+ ; FORWARDS — ForestWard Observatory. |
| **Projections** | **GeoSylva** (forêt, structure, gestion) + **Flora** (taxonomie, habitats végétaux) + **Artemis** (faune, corridors, observations) + **Climate** (scénarios climatiques). |
| **Ressources échangées** | - `Observation` d'habitats et d'espèces (Flora, Artemis). <br>- `SimulationRun` de dynamique forestière et de succession (LANDIS-II / BioDT). <br>- `Scenario` de gestion (coupe, non-intervention, restauration). <br>- `Recommendation` de gestion adaptative. |
| **Décisions supportées** | Plan de gestion Natura 2000, maintien des vieilles forêts, création de corridors, choix de régénération naturelle vs intervention. |
| **Validation possible** | Site pilote en forêt de Finlande (Forest DTC) ou en forêt catalane ; comparaison aux suivis nationaux d'habitats. |
| **Maturité** | Moyenne — modèles et plateformes existants, mais le couplage opérationnel avec GeoSylva et Artemis reste à démontrer. |

**Intérêt pour GSIE.** Ce cas pousse la fédération GeoSylva ↔ Flora ↔ Artemis et la comparaison de scénarios de gestion sur le long terme. Il met en jeu la bitemporalité et la traçabilité des observations scientifiques.

---

### UC-006 — Tempête, dégâts forestiers et plan de récupération

| Rubrique | Détail |
|---|---|
| **Événement de référence** | Tempêtes Lothar (décembre 1999) et Klaus (janvier 2009) en France ; suivis de dégâts de tempête en Finlande par Metsäteho Oy avec DestinE. |
| **Sources** | Météo-France — tempêtes Lothar et Klaus ; DestinE Climate DT — forestry use case (Metsäteho Oy, FMI) ; Forest DTC Finland. |
| **Projections** | **Climate** (vent, tempête) → **GeoSylva** (forêt, peuplements, vulnérabilité) → **Forest Dynamics** (mortalité, chablis) → **Simulation** (scénarios de récupération) → **Flora/Artemis** (impacts écologiques). |
| **Ressources échangées** | - `Observation` de chablis et de dégâts. <br>- `Forecast` de tempête et de zones vulnérables (Climate). <br>- `Scenario` de coupe de récupération et de reconstitution (GeoSylva + Simulation). <br>- `Recommendation` de priorités d'intervention. |
| **Décisions supportées** | Envoi de brigades, coupes de récupération, choix d'essences de remplacement, estimation de la ressource récupérable, protection des habitats. |
| **Validation possible** | Replay de la tempête Klaus sur la forêt landaise ; comparaison aux inventaires de dégâts ONF/FCBA. |
| **Maturité** | Moyenne — données historiques disponibles, modèles de vulnérabilité au vent existants, couplage avec la dynamique forestière à approfondir. |

**Intérêt pour GSIE.** Ce cas pousse la simulation de perturbations abiotiques et la planification de récupération. Il connecte Climate, GeoSylva et Simulation Engine sur un horizon de quelques semaines à quelques années.

## 4. Tableau de synthèse

| ID | Cas | Domaines | Fédération | Maturité | Priorité prototype |
|---|---|---|---|---|---|
| UC-001 | Ruissellement post-incendie | Ignis, Hydro, GeoSylva, Flora, Artemis | Ignis → Hydro → GeoSylva/Flora | Élevée | P1 (tranche verticale Ignis → Hydro) |
| UC-002 | Crise scolytes | Climate, GeoSylva, Flora, Forest Dynamics, Artemis | GeoSylva ↔ Flora ↔ Climate | Élevée | P2 (après GeoSylva ↔ Ignis) |
| UC-003 | SITAC multi-moyens | Ignis, Hub, Territorial Mesh, GeoSylva | Hub → Territorial Mesh → adaptateurs opérationnels | Moyenne | P1 (Hub Ignis) |
| UC-004 | Crues éclair et karst | Hydro, Climate, Ignis, GeoSylva | Hydro autonome + Hydro ↔ Ignis | Élevée | P2-P3 (Hydro) |
| UC-005 | Biodiversité forestière | GeoSylva, Flora, Artemis, Climate | GeoSylva ↔ Flora ↔ Artemis | Moyenne | P4-P5 |
| UC-006 | Tempêtes et récupération | Climate, GeoSylva, Forest Dynamics, Simulation | Climate → GeoSylva → Simulation | Moyenne | P3-P4 |

## 5. Pistes de prototypage

Les cas d'usage ci-dessus peuvent être progressivement intégrés dans la roadmap RFC-0037 :

1. **P1 — Tranche verticale Ignis** : reprendre UC-001 (Landiras ou Maures) en limitant le périmètre à un bassin versant et à quelques jours post-incendie.
2. **P2 — GeoSylva ↔ Ignis** : ajouter la restauration forestière au cas UC-001 ; tester la transmission des contours brûlés et des surfaces exposées.
3. **P3 — Hydro autonome** : déployer UC-004 sur un secteur cévenol ou larzacien avec un modèle hydrologique simplifié et des données Météo-France.
4. **P4 — Biodiversité et corridors** : démarrer UC-005 sur un site Natura 2000 avec GeoSylva, Flora et Artemis.
5. **P5 — Multi-perturbations** : croiser UC-002 (scolytes), UC-006 (tempêtes) et UC-001 (post-incendie) pour valuer la résilience de la forêt sous plusieurs scénarios de perturbations.

## 6. Exigences transverses mises en jeu

- **Provenance et fraîcheur** : chaque donnée affiche sa source, son `valid_time`, son `transaction_time` et son niveau de confiance.
- **Séparation réel / simulé / proposé / décidé** : les scénarios de propagation, de crue ou de gestion forestière ne modifient jamais l'état réel sans décision tracée.
- **ActionRequest et autorité** : les commandes physiques (drone, vanne, Canadair) passent par un adaptateur opérationnel après validation humaine.
- **Offline-first** : les agents terrain (GeoSylva, GCS-Lite) conservent le dernier état cohérent et synchronisent à la reconnexion.
- **Scénarios branchés** : chaque cas génère un `scenario_id` distinct, comparable et réplicable.

## 7. Sources et lectures complémentaires

- BRGM, `RP-69494-FR` — *Étude du ruissellement et de l'érosion post-incendie dans la région de Bormes-les-Mimosas* : https://infoterre.brgm.fr/rapports/RP-69494-FR.pdf
- Persée — Martin & Chevalier (1993), *Conséquences de l'incendie de forêt de l'été 1990 sur l'érosion mécanique des sols dans le Massif des Maures* : https://www.persee.fr/doc/bagf_0004-5322_1993_num_70_5_1711
- SMEGREG — *L'eau après le feu : conséquences hydrologiques des incendies de forêt* : https://www.smegreg.org/leau-apres-le-feu-consequences-hydrologiques-des-incendies-de-foret/
- Copernicus EMSR592 — *Forest fires in South West- Gironde and Landes- France* : https://mapping.emergency.copernicus.eu/activations/EMSR592/
- `fordead` package — INRAE/INRIA : https://fordead.gitlab.io/fordead_package/latest/
- DRAAF BFC — *Mortalités de sapins pectinés en région Bourgogne-Franche-Comté* : https://draaf.bourgogne-franche-comte.agriculture.gouv.fr/IMG/pdf/dsf_bfc_info_tech_sapinpectine_mars2023.pdf
- Eurisy — *SDIS 2B satellite information for realtime tactic management* : https://www.eurisy.eu/stories/in-hautecorse-rescue-and-fire-units-use-satellite-information-for-realtime-tactic-situation-management_124/
- ANSC — *NexSIS 18-112* : https://ansc.interieur.gouv.fr/nexsis-18-112/
- OHM-CV — *Cévennes-Vivarais Mediterranean Hydrometeorological Observatory* : https://centaur.reading.ac.uk/36319/1/JHM-400.pdf
- OREME — *Observatoire du Larzac / Durzon* : https://data.oreme.org/observation/gek
- SCHAPI — *Vigicrues Flash* : https://meetingorganizer.copernicus.org/EGU2019/EGU2019-14700.pdf
- BioDT — *Forest Biodiversity Dynamics* : https://biodt.eu/use-cases/forest-biodiversity-dynamics
- Forest DTC — *ESA Digital Twin Earth programme* : https://www.foresttwin.org/
- SenseForest — *Biodiversa+ pilot* : https://www.biodiversa.eu/biodiversity-monitoring/pilots/senseforest/
- FORWARDS — *ForestWard Observatory* : https://forwards-project.eu/the-forestward-observatory/
- DestinE — *Wildfires Evolution use case* : https://destine.ecmwf.int/use-case/destine-use-case-wildfires-evolution/

## 8. Statut

Ce document est un catalogue Draft. Il n'emporte aucune décision d'implémentation, aucune migration de schéma et aucune commande physique. Il doit être mis à jour à mesure que les prototypes valident, invalident ou affinent les cas d'usage recensés.
