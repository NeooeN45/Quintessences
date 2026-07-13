# Ignis — Registre d'idées

> Document vivant. Chaque idée est capturée, rattachée à un module, évaluée (maturité, priorité), et reliée aux idées connexes.
> Statuts : 💡 idée brute · 🔍 à étudier · ✅ principe accepté (intégration prévue en Phase 2+) · ⏸️ reportée · ❌ écartée (avec raison)
> Version : 0.7.3 — 2026-07-12

---

## 1. Perception & capteurs (embarqué drone)

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| P-01 | Détection fumée/flamme YOLO quantisé (TensorRT/Jetson) | ✅ | Haute | Base : fine-tuning sur Pyro-SDIS, FLAME2, D-Fire |
| P-02 | VLM embarqué/déporté pour description structurée de scène | ✅ | Haute | Réf. papier MDPI Drones 2025 (ForestFireVLM) |
| P-03 | Caméra thermique **radiométrique** : température par pixel → estimation intensité front (kW/m) | ✅ | Haute | Capteur prioritaire n°2 après RGB. Seuil décisionnel COS ~10 000 kW/m |
| P-04 | Interprétation RCCI automatique de la fumée (couleur/densité/comportement → nature du combustible) | 🔍 | Haute | **Différenciant fort, quasi inexistant en recherche.** Attente guide formation RCCI de Camille → taxonomie formelle. Suggestion, jamais attribution de cause |
| P-05 | LiDAR embarqué : structure combustible avant-feu, hauteur panache, scan zones non brûlées sur trajet prédit, cartographie post-feu | 🔍 | Moyenne | Limité en fumée dense. Post-feu = débouché commercial secondaire (RCCI, assurances) |
| P-06 | Multispectral/NIR : état hydrique végétation (combustible disponible), pénétration fumée légère | 🔍 | Moyenne | |
| P-07 | Capteurs atmosphériques in situ : CO/CO₂ (ratio = régime de combustion flamboyante/couvante), particules, T°, hygrométrie | 🔍 | Moyenne | Mesures impossibles par satellite/caméra sol. Prédiction des reprises |
| P-08 | Anémométrie par dérive GPS du drone (vent local mesuré sans capteur dédié) | 💡 | Moyenne | Gratuit en capteur, à valider en précision |
| P-09 | Détection personnes/véhicules en zone (YOLO standard) | ✅ | Haute | Garde-fous RGPD obligatoires |
| P-10 | Payloads modulaires selon mission (chaque capteur coûte de l'autonomie) | 🔍 | Haute | Matrice capteur × apport × coût × poids à produire (Phase 0) |

## 2. Jumeau numérique & propagation

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| J-01 | Moteur de propagation ForeFire (Univ. Corse) + couches open data (MNT/MNH LiDAR HD, BD Forêt, cadastre, AROME, DFCI) | ✅ | Haute | Alternative à comparer : Cell2Fire |
| J-02 | Émulateur neuronal du simulateur → centaines de scénarios probabilistes temps réel | 🔍 | Haute | Tendance recherche : knowledge-guided ML |
| J-03 | Assimilation de données temps réel : boucle prédiction → observation drone → recalage (~5 min) | ✅ | **Cœur du projet** | Filtre de Kalman d'ensemble / particulaire. C'est NOTRE brique |
| J-04 | Vecteur de feu multi-estimateurs : (1) géométrie front thermique entre passages, (2) inclinaison panache + vent, (3) prédiction ForeFire → fusion pondérée par incertitudes | ✅ | Haute | Si divergence → signaler l'incertitude au COS, pas de fausse certitude |
| J-05 | Mise à jour locale de la carte de combustible par LiDAR drone (LiDAR HD IGN parfois daté) | 💡 | Basse | Lié à P-05 |
| J-06 | Analyse d'enjeux : intersection propagation prédite × bâtiments/infra → liste menacée + délais (30 min/1 h/2 h) | ✅ | Haute | GeoPandas/PostGIS |
| J-07 | Rendu 3D du feu simulé en direct sur la carte (position + montée en intensité) | ✅ | Haute | Lié à G-01/G-06 |
| J-08 | Intégration satellites libres : Copernicus EMS (contours validés = vérité terrain de validation), Sentinel-2 (combustible dynamique/stress hydrique), Sentinel-3 + NASA FIRMS (détections thermiques quasi temps réel, API gratuite, latence ~3 h = pré-alerte large échelle + corroboration), ERA5 (entraînement sur feux historiques) | ✅ | Haute | **Idée Camille.** Satellite = large et tard ; drone = fin et vite. Complémentarité affichée dans le GCS |
| J-09 | Carte de risque dynamique pré-feu (heure par heure) : hygrométrie/vent/stress hydrique/combustible → « ce versant est une allumette aujourd'hui ». Déplace la valeur de la détection (réactif) vers la prévention et le pré-positionnement des moyens (proactif = posture préventive SDIS, budgétée) | ✅ | Haute | **Idée Claude validée Camille.** Toutes les couches déjà disponibles. Surveiller l'absence, pas que la présence |
| J-10 | « Boîte noire » du front : flux temporel ultra-compact (position/intensité/vecteur à chaque pas) pour rejouer n'importe quel feu passé dans le simulateur et valider les modèles en continu sur du réel. La base de données devient un banc de test qui grossit seul | ✅ | Haute | **Idée Claude validée Camille.** Chaque intervention rend le système plus crédible |
| J-11 | Modélisation des sautes de feu (spotting) : départs secondaires probables en aval du front, croisés avec vérification drone ciblée des zones à risque. Les sautes tuent les pompiers et déjouent la propagation continue classique | 🔍 | Haute | **Idée Claude validée Camille.** Problème pointu et vital → candidat idéal thèse CIFRE, mal traité par l'existant |
| J-12 | Photogrammétrie 3D du panache (2 drones ou drone + caméras sol) : volume, hauteur d'injection, dynamique de la colonne convective (→ intensité et comportement à venir) | ⏸️ | Basse | **Idée Claude.** Scientifiquement riche mais complexité opérationnelle élevée pour gain marginal au début. Sujet de labo pour phase recherche/CIFRE, pas MVP |

## 3. Vol & autonomie drone

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| V-01 | PX4/ArduPilot + MAVLink, plans de vol auto, décollage/atterrissage auto | ✅ | Haute | Ne jamais réinventer l'autopilote |
| V-02 | Go/no-go météo automatique (station météo locale) | ✅ | Haute | Simple moteur de règles |
| V-03 | Rotation de flotte (relève entre drones pour patrouille continue) | 🔍 | Moyenne | |
| V-04 | Reprise manuelle par télépilote sous supervision humaine | ✅ | Haute | Exigence réglementaire de toute façon |
| V-05 | Modes de mission : patrouille auto / relevé ponctuel sur clic / suivi de front / recherche de personnes dans secteur | ✅ | Haute | Lié à G-02 |
| V-06 | Orchestrateur multi-drones : allocation de tâches autonome (clic zone → choix du drone selon batterie/distance/capteurs, réorganisation des patrouilles) | 🔍 | Haute | Algos type enchères/CBBA. L'interface envoie l'intention, l'orchestrateur décide |
| V-07 | Mission « relais » : un drone se positionne automatiquement pour combler un trou de couverture détecté sur zone d'intervention (nœud Meshtastic volant) | 🔍 | Haute | **Idée Camille.** Nouveau type de mission pour V-06. ⚠️ Relayer LoRa libre = OK ; retransmettre ANTARES pompiers = régalien, interdit — on visualise, on ne relaie pas |
| V-08 | Déconfliction aérienne avec moyens de lutte (Canadair/Dash/HBE) : transpondeur/e-identification, intégration U-space, règle absolue de dégagement automatique à l'arrivée des aéronefs pilotés | ✅ | **Critique** | **Idée Claude.** Un drone non coordonné = arrêt des largages (cas réels). Répond d'avance à LA première objection de tout officier — argument de vente autant qu'obligation |
| V-09 | Stations d'accueil automatiques (drone-in-a-box) : abri + recharge auto + météo locale, déployées sur massif → relève de flotte sans humain = infrastructure de surveillance permanente | 🔍 | Haute | **Idée Claude.** Complète V-01/V-03. Marché mature (DJI Dock et al.) → auditer en Phase 0 : acheter la station, construire le reste |

## 4. Communications

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| C-01 | Architecture hiérarchique par priorité : alertes critiques → LoRa maillé (Meshtastic) ; télémétrie → 4G/5G avec file d'attente ; imagerie → large bande ou stockage à bord | ✅ | Haute | **Idée Camille.** Zones DFCI = zones blanches ; le bas débit passe toujours |
| C-02 | Protocole de messages compacts (~200 octets : détection, lat/lon, intensité, vecteur, horodatage) | 🔍 | Haute | Spécification à écrire. Découle de C-01 |
| C-03 | Chaque nœud (drone, station, véhicule pompier) relaie le mesh → le réseau se renforce en opération | 💡 | Moyenne | Effet réseau vertueux |
| C-04 | Stations capteurs sol fixes = nœuds Meshtastic solaires autonomes (~50 €) → maillage territorial low-cost | 💡 | Moyenne | Complémentaire Pyronear sans le concurrencer |
| C-05 | Comparatif alternatives LoRa (Phase 0) : Wi-Fi HaLow 802.11ah (~Mbps sub-GHz, challenger sérieux), satellite IoT (Kinéis 🇫🇷 = souveraineté, Iridium SBD — filet de sécurité ultime), 4G/5G privée ARCEP (déploiement fixe à terme), MANET tactiques type Silvus (haut débit maillé, très cher, cible « version pro ») | 🔍 | Haute | **Idée Camille** (« trouver équivalents à LoRa si mieux »). C-01 absorbe tout : techno par étage |
| C-06 | Architecture « lourd serveur / léger terrain » : edge = ce qui survit à une coupure (détection, messages compacts, cache tuiles, vol autonome) ; serveur = jumeau numérique, émulateur, scénarios, réentraînement. Règle : le terrain reste opérationnel en mode dégradé, le serveur enrichit mais ne conditionne pas | ✅ | **Structurant** | **Idée Camille.** Argument de vente sécurité civile fort |

## 5. Interface & aide à la décision (GCS métier)

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| G-01 | GCS 3D métier : MapLibre GL 3D + MNT, front de feu vivant, polygones de propagation, enjeux | ✅ | Haute | Compétence GeoSylva réutilisée. Base : QGroundControl/MAVLink |
| G-02 | Clic sur carte → dispatch du drone pour relevé ciblé (façon app DJI) | ✅ | Haute | Testable 100 % en simulation (SITL + ForeFire) |
| G-03 | Affichage explicite de l'incertitude (convergence/divergence des estimateurs) | ✅ | Haute | Critère de confiance opérationnelle SDIS |
| G-04 | Positionnement : outil d'aide à la décision COS/CODIS — jamais d'alerte directe population (FR-Alert = régalien) | ✅ | **Non négociable** | Juridique + acceptabilité SDIS |
| G-05 | GCS-Cinéma : Unreal Engine 5.x + Cesium for Unreal — terrain LiDAR HD/ortho IGN streamé, rendu Lumen/Nanite qualité film | 🔍 | Haute | **Idée Camille.** UE6 annoncé non sorti ; tout migrera |
| G-06 | Feu/fumée Niagara pilotés par les données du jumeau numérique (position, intensité, panache) — visualisation scientifique, pas décorative | 🔍 | Haute | |
| G-07 | Visualisation 3D du vent : particules animées sur champ AROME + mesures locales | 💡 | Moyenne | **Idée Camille** |
| G-08 | Unités terrain en 3D (camions, drones) avec marqueurs cliquables → fiche info (indicatif, moyens, statut) ; intégration géoloc flottes SDIS à étudier | 🔍 | Haute | **Idée Camille** |
| G-09 | Fonds de carte commutables (ortho/plan/thermique/DFCI/combustible) | 🔍 | Moyenne | **Idée Camille** |
| G-10 | Timeline de simulation : propagation minute par minute sur horizon donné (scrubber temporel passé→futur) | ✅ | Haute | **Idée Camille** |
| G-11 | Architecture double client : GCS-Lite (MapLibre, phases 2-3) puis GCS-Cinéma (Unreal, phase 4+), branchés sur la même API temps réel (contrat d'interface WebSocket/gRPC à spécifier tôt) | ✅ | **Structurant** | GCS-Lite convainc techniquement, GCS-Cinéma fait rêver démos/financeurs |
| G-12 | Couche couverture radio/réseau : bulles 3D par technologie (4G/5G cellulaire, radio chiffrée pompiers ANTARES, LoRa) → identifier les trous de maillage avant/pendant intervention | 🔍 | Haute | **Idée Camille — différenciant opérationnel réel.** Prédiction : modèles propagation RF sur MNT (SPLAT!/ITM Longley-Rice) + base ANFR Cartoradio (positions émetteurs, open data). Correction temps réel par mesures RSSI drones/véhicules (encore de l'assimilation !). Déclenche V-07 |
| G-13 | GCS-Cinéma Unreal = aussi simulateur de formation COS/cellules de commandement hors opération. Marché distinct, revenus en période creuse (hiver), amortit l'investissement Unreal sur deux usages. Client potentiel : ENSOSP, écoles sécurité civile | ✅ | Moyenne | **Idée Claude validée Camille.** Un seul actif technique, deux marchés |

## 6. Données & apprentissage

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| D-01 | Base d'entraînement : Pyro-SDIS (data.gouv.fr), FLAME/FLAME2, D-Fire, FASDD, FIgLib, WildfireSpreadTS | ✅ | Haute | |
| D-02 | Partenariats SDIS : rapports d'intervention géolocalisés = étiquettes en or | 🔍 | Haute | Voie d'entrée : Entente Valabre, réseau DFCI Sud-Ouest (contacts ONF) |
| D-03 | Pipeline d'apprentissage continu : faux positifs signalés par pompiers → réentraînement (validation humaine) | ✅ | Moyenne | Le « modèle auto-évolutif » version rigoureuse |
| D-04 | Croisement données terrain drone × base feux historiques × cartes | ✅ | Haute | Fil rouge du jumeau numérique |
| D-05 | Génération de données synthétiques annotées par le simulateur (Unreal/Niagara géoréférencé) : milliers d'images aériennes de feu avec vérité terrain automatique (angles, lumières, végétations, fumées variés). Entraînement mixte synthétique + réel validé par la recherche | ✅ | Haute | **Idée Claude.** Répond au manque d'images aériennes de feux français annotées. GCS-Cinéma = 3e usage : usine à données |
| D-06 | Intégration signalements citoyens : croisement détections × appels 112 géolocalisés × réseaux sociaux pour corroboration | ⏸️ | Basse | **Idée Claude.** Valeur réelle mais dépend d'accès de données obtenables seulement après confiance SDIS établie. Phase 2+ |
| D-07 | Partenariat feuxdeforet.fr : base d'événements feux validés géolocalisés (~935/30 j en saison 2026, horodatés, commune, photos) = flux d'étiquettes françaises + alimentation boîte noire (J-10) ; leur canal signalements citoyens débloque D-06 plus tôt que prévu ; comparaison/complément de leur vigilance journalière par notre carte fine (J-09) ; relais de visibilité communauté feu | 🔍 | Haute | **Idée Camille.** À qualifier avant contact : qui est derrière, modèle éco, provenance des données validées, CGU/réutilisation (accord explicite requis pour entraînement commercial — pas de moisson sauvage). Approche complémentarité, comme Pyronear |
| D-08 | **BDIFF** (bdiff.agriculture.gouv.fr) : base officielle des incendies de forêt en France, données depuis 2006 (saisies remontant à 1973), export CSV, granularité commune, **causes renseignées** (police/gendarmerie contributeurs), collecte par réseau SDIS/DDT/ONF/DRAAF. Prométhée (base méditerranéenne historique) fusionnée dedans en 2023 | ✅ | **Haute** | Colonne vertébrale des feux historiques (J-10, D-04) + causes pour volet RCCI. L'ONF est contributeur — réseau de Camille |
| D-09 | **GIP ATGeRi / PIGMA** : anime la collecte BDIFF en Nouvelle-Aquitaine avec les SDIS des 12 départements, DRAAF et EMIZ Sud-Ouest ; gère les données DFCI Aquitaine (pistes, points d'eau, massifs) | ✅ | **Haute** | **LE partenaire données régional naturel** : un interlocuteur unique déjà connecté aux clients cibles. Camille en Nouvelle-Aquitaine, expérience ONF Charente/Deux-Sèvres |
| D-10 | EFFIS/GWIS (JRC, Commission européenne) : recensement satellitaire temps réel des feux UE, danger prévisionnel, périmètres, API. ⚠️ Stats divergentes de BDIFF (méthode satellite ne distingue pas incendies/brûlages dirigés) → documenter les différences de méthode entre sources | ✅ | Haute | Complément européen de J-08 |
| D-11 | Météosat MTG-FCI (EUMETSAT) : détection feux géostationnaire, rafraîchissement ~10 min sur l'Europe (vs quelques passages/jour pour FIRMS défilant) | ✅ | Haute | Changement de génération pour la pré-alerte satellite (J-08) |
| D-12 | Sentinel-1 SAR : radar → voit à travers fumée et nuages, jour/nuit ; cartographie surfaces brûlées quand l'optique est aveugle | ✅ | Moyenne | Complément direct Sentinel-2 (J-08) |
| D-13 | Foudre : Météorage (payant, réseau FR) ou Blitzortung (communautaire gratuit) — cause majeure en zone inaccessible ; croisé avec J-09 → zones de surveillance prioritaire post-orage | 🔍 | Moyenne | Pyronear a exploré ce croisement (« chasse aux éclairs ») |
| D-14 | CAMS (Copernicus Atmosphère) : modélisation panaches/qualité de l'air — validation observations panache + volet impact sanitaire | 💡 | Basse | |
| D-15 | OSO/CESBIO (Theia) : occupation des sols France entière, MAJ annuelle (plus fraîche que Corine) — complément BD Forêt pour carte de combustible | 🔍 | Moyenne | |
| D-16 | Réseaux RTE/Enedis (open data) : lignes électriques = cause d'ignition connue ET enjeu à protéger — double usage J-06 + J-09 | 🔍 | Moyenne | |
| D-17 | OpenStreetMap + BAN : compléments cadastre pour enjeux (sentiers, campings, réservoirs) + adressage précis des bâtiments menacés | ✅ | Moyenne | |
| D-18 | sensor.community : réseau citoyen mondial capteurs particules/T° open data — stations existantes possibles dans les massifs cibles = préfiguration gratuite du maillage C-04 | 💡 | Basse | |

## 7. Stratégie, réglementaire, financement

| ID | Idée | Statut | Priorité | Notes |
|----|------|--------|----------|-------|
| S-01 | Verrou principal : BVLOS / SORA / DGAC pour patrouilles automatisées | 🔍 | Haute | Démarrer en vol à vue, cadre simple |
| S-02 | RGPD sur détection de personnes | 🔍 | Haute | |
| S-03 | Complémentarité Pyronear (fixe) vs nous (mobile + caractérisation + jumeau numérique). Contribuer à leur open source = carte de visite + réseau SDIS | ✅ | Haute | |
| S-04 | Financements : ANR, Horizon Europe, DGSCGC, thèse CIFRE à terme | 🔍 | Moyenne | Le dossier d'architecture Phase 1 servira de base |
| S-05 | Débouchés secondaires : cartographie post-feu (RCCI, assurances), mise à jour combustible | 💡 | Basse | Ne pas disperser avant le produit principal |
| S-06 | ⚠️ Frontières régaliennes récurrentes : alerte population (FR-Alert), fréquences ANTARES, attribution de cause RCCI → toujours « aider », jamais « se substituer » | ✅ | **Non négociable** | Fil rouge juridique et d'acceptabilité |
| S-07 | RETEX automatique post-incident : rapport comparant prédictions vs réalité + décisions COS + évolution réelle. Nourrit le réentraînement (D-03) ET devient un produit vendable (les SDIS font leurs RETEX réglementaires à la main aujourd'hui) | ✅ | Haute | **Idée Claude validée Camille.** Sous-produit technique → source de revenu |
| S-08 | **Séquençage business (structurant) : le MVP payable n'est PAS le drone.** C'est jumeau numérique + analyse d'enjeux sur données existantes (satellite, stations fixes, saisie manuelle position feu). Un COS qui clique un départ de feu et voit en 10 s la propagation + maisons menacées + délais → se vend SANS drone, finance la suite, et crée la relation SDIS qui fournira les données de la partie drone. Le drone = phase 2 du business | ✅ | **Critique** | **Idée Claude validée Camille.** Antidote n°1 au risque de dispersion. Le drone est phase 2, pas phase 1 |
| S-09 | Largage/action par drone (extinction, marquage) | ❌ reporté | Très basse | Bascule dans une catégorie réglementaire/assurantielle bien plus lourde + concurrence frontale Canadair/doctrine pompier. Rester sur observation + aide à la décision. Rouvrir seulement en très long terme |
| S-10 | Détection acoustique du feu (signature du crépitement) | ⏸️ | Très basse | Scientifiquement réel mais le drone est une source de bruit énorme et le gain sur la thermique est marginal. Joli sujet de recherche, faible valeur produit |
| S-11 | Cybersécurité by design : chiffrement liaisons (MAVLink 2 signé — MAVLink par défaut est peu sécurisé), authentification des nœuds mesh, détection d'anomalies sur messages (fausses détections injectées = panique ou masquage d'un vrai feu), résilience brouillage GPS. Anticiper qualification SecNumCloud/ANSSI pour vendre à la sécurité civile | ✅ | Haute | **Idée Claude.** Le système est une cible. Anticiper coûte 10× moins que rattraper. Rejoint l'intérêt cyber/OSINT de Camille |
| S-12 | Interopérabilité SDIS : exporter dans LEURS formats — symbologie SITAC normalisée, flux vers NexSIS 18-112, compatibilité SGA/SGO. Un système qui s'intègre s'achète ; un système qui veut tout remplacer se refuse | ✅ | Haute | **Idée Claude.** Petit travail de spec, énorme effet d'adoption |
| S-13 | Marché assurantiel comme second client : cartes de risque dynamique (J-09) + cartographie post-feu (S-05) → assureurs, CCR (tarification risque incendie). Paie bien, sans marchés publics | ⏸️ | Basse | **Idée Claude.** Piste réelle mais dispersante. Derrière S-08 : d'abord le MVP SDIS |

## 8. Modèles & plateformes IA (catalogue validé)

### 8a. Embarqué drone (Jetson)

| ID | Élément | Statut | Notes |
|----|---------|--------|-------|
| M-01 | Détecteurs : RT-DETR/RT-DETRv2, D-FINE (Apache 2.0, forts sur petits objets = fumée naissante) vs YOLO11 (⚠️ AGPL Ultralytics → licence commerciale ou éviter). Fine-tunes existants : TommyNgx/YOLOv10-Fire-and-Smoke, kittendev/YOLOv8m-smoke | 🔍 benchmark | **La licence est un critère au même titre que les FPS.** Benchmark : précision fumée fine × FPS Jetson × licence |
| M-02 | VLM edge : SmolVLM2 (256M/500M/2.2B, Apache 2.0, vidéo, GGUF/ONNX — candidat n°1 base RCCI), Qwen2.5-VL-3B (grounding spatial), Moondream2 (~1.9B, pointage par requête), Florence-2 (MIT), Gemma 3 4B-VL. Précédent prouvé : hiko1999/Qwen2-Wildfire-2B (+ GGUF) | 🔍 benchmark | SmolVLM2-500M fine-tuné RCCI = cible P-04 |
| M-03 | Outillage NVIDIA embarqué : TAO Toolkit (fine-tuning + export TensorRT), DeepStream (pipeline vidéo temps réel multi-flux = ossature perception), Metropolis/VSS (recherche vidéo par VLM) | 🔍 | Cohérence totale Jetson → serveur (tout parle TensorRT) |

### 8b. Serveur (analyse lourde)

| ID | Élément | Statut | Notes |
|----|---------|--------|-------|
| M-04 | VLM lourds : Qwen2.5-VL-72B (Apache, quantisé AWQ sur RTX 5090 32 Go), InternVL3-78B, NVIDIA Nemotron (NIM/TensorRT-LLM), famille Qwen3-VL à suivre | 🔍 benchmark | Analyste de scène serveur |
| M-05 | Souveraineté 🇫🇷 : Mistral (Pixtral Large, Mistral Small 3.x vision Apache, Ministral edge, Large via La Plateforme UE, on-premise possible) pour rapports RETEX (S-07) et synthèses COS en français | ✅ | « IA française hébergée UE, RGPD natif » = argument DGSCGC/SDIS que les modèles US ne cochent pas |
| M-06 | Segmentation : SAM 2.1 Large (géométrie fine du front, suivi vidéo), Grounding DINO + SAM2 (« Grounded SAM ») = annotation semi-automatique des datasets RCCI (÷10 le coût d'annotation) | ✅ | |
| M-07 | Backbone vision : DINOv3 (Meta) pour pré-entraîner nos têtes custom sur données propres | 💡 | Phase données propriétaires |
| M-08 | 3D/profondeur : Depth Anything V2 (distance panache monoculaire), VGGT/DUSt3R (reconstruction 3D économique → J-12 sans double drone) | 💡 | |

### 8c. Météo IA (l'étage manquant du jumeau — découverte majeure)

| ID | Élément | Statut | Notes |
|----|---------|--------|-------|
| M-09 | **NVIDIA Earth-2 famille ouverte (jan. 2026)** : CorrDiff (descente d'échelle 25 km → 2 km, 500× plus rapide, ensembles probabilistes), FourCastNet 3 (prévision globale, 60 j en <4 min sur un H100), Nowcasting (satellite+radar génératif), Earth2Studio (pipelines), microservices NIM | ✅ | **Le vent local = paramètre n°1 de la propagation.** CorrDiff fine-tuné France = ensembles de vent hyper-locaux → ensembles ForeFire |
| M-10 | Concurrents au benchmark météo : AIFS (ECMWF — données assimilées européennes), WeatherNext/GraphCast/GenCast (Google DeepMind, GenCast probabiliste natif, utilisé par le National Hurricane Center), Aurora (Microsoft, fondation atmosphérique fine-tunable, Nature) | 🔍 benchmark | Trois fondations météo ouvertes en 18 mois : maturité soudaine |
| M-11 | PhysicsNeMo (ex-Modulus) : framework physique-IA NVIDIA = aussi l'outil naturel de l'émulateur J-02 | 🔍 | |
| M-12 | Piste R&D valorisable : « CorrDiff-France » (vent sur relief français pour le feu) = 2e candidat CIFRE ou partenariat Météo-France | 💡 | Peu d'acteurs feu l'ont vue venir |

### 8d. Géospatial / observation de la Terre

| ID | Élément | Statut | Notes |
|----|---------|--------|-------|
| M-13 | Fondations EO : Prithvi-EO-2.0 (300M/600M, NASA/IBM) — dont **Prithvi-EO-1.0-burn-scar déjà fine-tuné cicatrices de brûlage** (= S-05 quasi gratuit + validation Landiras) ; TerraMind (IBM+ESA Φ-lab, multimodal Sentinel-1+2 radar+optique) ; Clay, SatMAE++ | 🔍 benchmark | |
| M-14 | Plateformes d'analyse : Google Earth Engine (pétaoctets Sentinel/Landsat sans téléchargement, gratuit recherche), Microsoft Planetary Computer (catalogue STAC) | ✅ | Prototypage satellite sans infra |
| M-15 | Datasets HF confirmés : links-ads/wildfires-cems (segmentation surfaces brûlées **Europe**, CC-BY, maintenu), links-ads/effis-wildfire (Sentinel-2 × EFFIS), TheRootOf3/next-day-wildfire-spread (xarray), Wildfire-SearchAndRescue, Pyro-SDIS (hébergé HF) | ✅ | |
| M-16 | Google FireBench : benchmark ML open source pour la recherche incendie | 🔍 à auditer | Pour l'émulateur J-02 |
| M-17 | Optimisation : NVIDIA cuOpt (routage GPU) = candidat orchestrateur multi-drones V-06 ; SimFire/SimHarness (RL sur simulation feu) en veille | 💡 | |
| M-18 | **Neural Operators (FNO/SFNO)** : apprentissage de solveurs physiques entiers (techno sous FourCastNet) = la voie moderne pour l'émulateur J-02, au-dessus de U-Net/ConvLSTM. Disponible dans PhysicsNeMo | 🔍 Haute | Encore un argument PhysicsNeMo (M-11) |
| M-19 | **3D Gaussian Splatting** : reconstruction 3D photoréaliste temps réel depuis simple vidéo drone → jumeau 3D navigable en minutes, plugins Unreal existants (GCS-Cinéma). Applications : post-feu, interface habitat-forêt d'un hameau menacé | 🔍 Haute | Idée à fort effet démo |
| M-20 | Modèles de raisonnement (test-time compute) : DeepSeek-R1 (ouvert, on-premise = souveraineté) pour l'aide à la décision tactique multi-facteurs côté serveur | 💡 | |
| M-21 | GraphRAG : doctrine DFCI + guides op + RETEX historiques en base de connaissance interrogeable par le COS (« feux similaires dans ce massif ? »). Étage au-dessus du RAG ChromaDB existant de SylvIA | 💡 Moyenne | Réutilise l'acquis SylvIA |
| M-22 | Veille long terme : VLA (OpenVLA, GR00T — « drone, va vérifier ce qui fume derrière la crête »), Mamba/SSM (flux vidéo longs à faible mémoire sur Jetson) | 💡 veille | |

## 9. Veille satellite & concurrence

| ID | Élément | Statut | Notes |
|----|---------|--------|-------|
| K-01 | **Google FireSat / Earth Fire Alliance** : constellation dédiée feu (>50 satellites à terme), détection 5×5 m, revisite ≤20 min, IR multispectral perçant la fumée, IA comparative historique. Pilote en orbite + 3 satellites lancés juil. 2026. EFA « accueille de nouveaux partenaires » | 🔍 **prioritaire** | Redéfinit la complémentarité : satellite détecte tôt/partout → notre drone caractérise finement + mesure in situ + alimente le jumeau. Renforce S-08. Contact EFA à envisager (accès données France) |
| K-02 | Pano AI (SF, 89 M$) : caméras 360° + IA + analystes, >50 M acres US/CA/AU, 735 alertes 2025 (>50 % premières détections), brevets imagerie panoramique/géoloc/visu carto, **expansion Europe visée 2026** | 🔍 veille | Le « Pyronear commercial ». Ses brevets sont à examiner avant de breveter nous-mêmes (liberté d'exploitation) |
| K-03 | **Technosylva** : prédiction risque + propagation (utilities, agences US) — concurrent le plus proche de notre jumeau numérique. **Partenariat Technosylva × Pano annoncé fév. 2026** : prédictif + temps réel unifiés en « image décisionnelle partagée » | 🔍 veille | La version US à deux entreprises de ce que Ignis construit intégré. Valide la direction ET presse le tempo |
| K-04 | Dryad Networks (Berlin) : >30 000 capteurs gaz solaires LoRaWAN (H₂/CO/CO₂/COV ppm), détection « par le nez », 10-15 ans d'autonomie sur arbre | 🔍 | **Validation industrielle directe de C-04.** Partenaire potentiel plus que concurrent (capteurs, pas jumeau) |
| K-05 | OroraTech (Munich) : nanosatellites thermiques — le FireSat européen commercial | 🔍 veille | |
| K-06 | Écosystème mondial : ALERTCalifornia (public), Fireball.International, Robotics Cats, exci, Gridware, SenseNet, Insight Robotics, Wildfire Defense Systems (assurance). 72 sociétés, 26 financées, US dominant (20) | ✅ | Détection = marché encombré ; caractérisation drone + assimilation + jumeau + décision COS intégrés = espace encore ouvert |
| K-07 | **Paysage français — MENAPS/Fire Eagle requalifié : source de leçons et d'objectifs, pas menace directe.** Profil : projet porté par MENAPS (conseil digital Toulouse, H. Chaker, Dr informatique), co-développé avec SDIS 11 depuis 2022 (Lézignan), détection fumée 1 m² à 1,5 km validée terrain, vision essaim + recharge auto + centre de contrôle + app d'alerte, focus software sur drone DJI « bon marché ». **Signal clé : levée multi-M€ visée en 2023 → crowdfunding GoFundMe 300 k€ en fév. 2025 (toujours actif) = levée institutionnelle probablement échouée.** Aucun nouveau SDIS ni financement annoncé depuis. Périmètre : détection-alerte seulement (ni propagation, ni assimilation, ni jumeau, ni enjeux, ni SITAC/NexSIS). Autres acteurs FR : TechForFire (IUSTI, académique), Drone Act (SDIS 56), Atraksis, Shark Robotics, fabricants Parrot/Delair/Elistair | ✅ | **3 leçons** : (1) leur mur financier valide S-08 (MVP sans drone) par l'exemple ; (2) marché prouvé, pas saturé — un SDIS co-développe 3 ans, les médias adorent, personne n'a gagné ; (3) scénario partenariat/reprise d'acquis à 12-18 mois plausible (ils cherchent des partenaires, ils ont l'expérience SDIS, nous les couches qu'ils n'ont pas). Veille trimestrielle Pappers/BODACC. Pression concurrentielle réelle = Pano (Europe 2026) + Technosylva×Pano, pas MENAPS |

## 10. Feuille de route (rappel)

> **Les jalons ci-dessous sont internes à Ignis.** Ils ne pas se confondre
> avec les phases de GSIE (Phase 1 Foundation → Phase 4 Implémentation). Ignis
> est une application cliente de GSIE ; ses jalons s'inscrivent *dans* les phases
> GSIE globales. Voir le rappel de gouvernance en fin de section.

- **Ignis Jalon 0** — Cartographie de l'existant : comparatif sourcé des briques + matrice capteurs + comparatif comms (C-05). *(en cours — voir `apps/Ignis/` pour les livrables produits)*
- **Ignis Jalon 1** — Architecture & spécification : vision, modules, ADRs, contrat d'interface API temps réel (G-11), plan de validation.
- **Ignis Jalon 2** — Banc de simulation intégral sur PC : ForeFire + PX4 SITL/Gazebo + détecteur virtuel bruité + boucle d'assimilation + GCS-Lite.
- **Ignis Jalon 3** — Validation sur incendies historiques (Landiras 2022, Copernicus EMS).
- **Ignis Jalon 4** — Hardware in the loop (Jetson réel) + démarrage GCS-Cinéma (Unreal/Cesium).
- **Ignis Jalon 5** — Premier drone réel, vol à vue.
- **Ignis Jalon 6** — Pilote SDIS.

> **Rappel de gouvernance (2026-07-12)** : les jalons 0 et 1 de Ignis
> ci-dessus sont des étapes *documentaires* (comparatifs, specs, ADRs anticipés).
> Aucun code — y compris sur le banc de simulation séparé (`~/Ignis/` WSL2) —
> ne démarre avant la validation complète des 12 livrables de la Phase 1 de
> **GSIE** (le projet-fondation). Voir `02_RFC/RFC-0004.md` §8.5 et §11.

## 11. Idées en attente de capture

*(Section tampon : idées mentionnées mais pas encore développées — à vider ici à chaque session)*

- *(vide — tout est capturé au 2026-07-12)*

---

## Backlog questions ouvertes

1. Quel(s) châssis drone ? (build custom vs plateforme existante — critères : payload, autonomie, IP rating)
2. Liaison vidéo large bande : quelle techno quand 4G absente ? (relais drone ? antenne directionnelle ? → croiser avec C-05)
3. Nuit : thermique seul suffit-il pour patrouille nocturne ? (les feux nocturnes existent)
4. Multi-drones : à partir de quand ? (complexité coordination vs valeur — lié V-06/V-07)
5. Modèle économique : vente matériel, SaaS supervision, service opéré ?
6. Géoloc des flottes SDIS : quels systèmes existants, quelles interfaces possibles ? (G-08)
7. Statut réglementaire d'un drone-relais radio : quelles fréquences a-t-on le droit d'émettre/relayer ? (V-07)
8. Drone-in-a-box : acheter (DJI Dock, alternatives européennes ?) vs construire ? Souveraineté des données avec du matériel chinois pour la sécurité civile ? (V-09, lié S-11)
9. État exact de U-space en France en 2026 et procédures de coordination drone/aéronefs bombardiers d'eau ? (V-08)
10. feuxdeforet.fr : structure juridique, modèle économique, provenance des données validées, existence d'une API, conditions de réutilisation ? (D-07)
11. GIP ATGeRi/PIGMA : quelles données DFCI Aquitaine accessibles, sous quelles conditions, et qui contacter via le réseau ONF ? (D-08)
12. Earth Fire Alliance / FireSat : modalités d'accès aux données pour la France, conditions de partenariat ? (K-01)
13. Brevets Pano AI (imagerie panoramique, géolocalisation, visualisation carto) : analyse de liberté d'exploitation avant nos propres dépôts ? (K-02)
14. Benchmark météo IA sur cas français : CorrDiff vs AIFS vs GenCast vs Aurora — lequel descend le mieux le vent sur relief ? (M-09/M-10)
15. Veille trimestrielle MENAPS (Pappers/BODACC : santé financière, dépôts) + Pano AI Europe + Technosylva — qui fixe le tempo (K-02/K-03/K-07)
