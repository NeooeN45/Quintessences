# VEILLE — Reconnaissance vocale embarquée et modèles VLA pour l'acquisition drone

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-VEILLE-STT-VLA-2026-08-16 |
| **Statut** | Draft |
| **Version** | 0.1.0 |
| **Date** | 2026-08-16 |
| **Auteur** | Claude, sous autorité du Fondateur |
| **Périmètre** | Axe A — reconnaissance vocale embarquée GeoSylva ; Axe B — perception et VLA pour l'acquisition drone |
| **Documents liés** | `ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md`, `VEILLE_LLM_ET_RD_GSIE_2026-08-12.md`, `apps/GeoSylva/RESEARCH_OPPORTUNITIES.md` |

---

## 1. Objet et niveau de confiance

Cette veille recense les modèles ouverts publiés ou consolidés entre janvier et
août 2026 qui répondent à deux besoins identifiés de Quintessences : la saisie
vocale hors-ligne en français sur terrain forestier (GeoSylva) et la perception
aérienne pour l'acquisition drone (GeoSylva, Ignis).

Elle **ne remplace aucune décision** et ne qualifie aucun modèle pour la
production. Chaque affirmation porte son niveau de confiance :

- **Vérifié** — fiche officielle du modèle consultée le 2026-08-16 (métadonnées
  Hugging Face : licence, langues, nombre de paramètres, format de poids).
- **Rapporté** — issu d'une publication scientifique ou d'un article de presse
  technique non rejoué par nous ; les chiffres de performance sont ceux des
  auteurs.
- **Hypothèse** — raisonnement d'ingénierie de notre part, à confirmer par
  mesure.

Aucune performance annoncée ci-dessous n'a été reproduite sur nos données. Le
protocole de vérification est décrit en §2.5 et §3.5.

---

## 2. Axe A — Reconnaissance vocale embarquée pour GeoSylva

### 2.1 Point de départ réel

**Vérifié.** GeoSylva utilise aujourd'hui la reconnaissance vocale **native
Android**, via `RecognizerIntent.ACTION_RECOGNIZE_SPEECH`
(`apps/GeoSylva/.../settings/SettingsHomeScreen.kt:289`), avec dégradation
silencieuse quand aucun moteur n'est installé sur l'appareil.

**Vérifié.** `apps/GeoSylva/RESEARCH_OPPORTUNITIES.md` (§3.4) identifie déjà
Vosk Android (Apache-2.0) comme piste hors-ligne française, et
`GEOSYLVA_3_SPECIFICATION_FONCTIONNELLE.md` (§3.3, §209) pose l'offline-first
comme principe fondateur et prévoit un mode vocal pour le martelage.

**Constat.** L'implémentation actuelle contredit partiellement le principe
offline-first : le moteur natif dépend de l'appareil, de la présence des
services Google et, selon la configuration, d'une connexion réseau. Sa qualité,
son vocabulaire et son comportement hors-ligne ne sont ni maîtrisés ni
reproductibles d'un terminal à l'autre. C'est ce trou que les modèles ci-dessous
peuvent combler.

### 2.2 Contraintes de sélection

| Contrainte | Exigence |
|---|---|
| Langue | Français obligatoire (le français est la locale par défaut de GeoSylva) |
| Connectivité | Fonctionnement intégral hors réseau |
| Cible matérielle | Smartphone Android ARM64, sans GPU dédié, autonomie terrain |
| Licence | Permissive et compatible avec une distribution applicative — **NC exclu** |
| Format | Poids quantifiables (GGUF, ONNX int8) et exécutables via un runtime embarquable |
| Vocabulaire | Doit tolérer le lexique forestier (essences, qualités, codes de martelage) |

### 2.3 Candidats retenus

**Vérifié** pour la licence, les langues, la taille et le format ; les colonnes
« Intérêt » et « Réserve » sont de l'**Hypothèse** d'ingénierie.

| Modèle | Paramètres | Licence | FR | Format | Intérêt pour GeoSylva | Réserve |
|---|---|---|---|---|---|---|
| [microsoft/VibeVoice-ASR-BitNet](https://hf.co/microsoft/VibeVoice-ASR-BitNet) | 323 M | MIT | oui | GGUF / ggml, inférence CPU | Le meilleur rapport taille/licence du lot. Quantification BitNet pensée pour le CPU, donc pour un téléphone sans NPU exploitable. | Modèle récent (juillet 2026), peu de retours terrain ; qualité FR à mesurer |
| [nvidia/nemotron-3.5-asr-streaming-0.6b](https://hf.co/nvidia/nemotron-3.5-asr-streaming-0.6b) | 638 M | OpenMDW-1.1 (usage commercial permis, **Rapporté**) | oui (35 locales) | GGUF, NeMo | ASR *streaming* « cache-aware » : transcription au fil de la parole, adaptée à une dictée de martelage plutôt qu'à un enregistrement bloc | Écosystème NeMo lourd ; portage Android à qualifier |
| [Qwen/Qwen3-ASR-0.6B-hf](https://hf.co/Qwen/Qwen3-ASR-0.6B-hf) | 782 M | Apache-2.0 | oui (30 langues) | safetensors | Licence la plus confortable, base Qwen3 largement outillée, écosystème de fine-tuning actif (des dérivés métier existent déjà) | Pas de build embarqué officiel ; 782 M réels malgré le nom « 0.6B » |
| [openai/whisper-small](https://hf.co/openai/whisper-small) + [whisper.cpp](https://hf.co/ggerganov/whisper.cpp) | 244 M | MIT / Apache-2.0 | oui | GGUF | **Référence de comparaison**, pas candidat principal : chaîne mature, portage Android documenté depuis des années | Qualité FR inférieure à l'état de l'art 2026 ; pas de streaming natif |

### 2.4 Candidats écartés et motif

**Vérifié.**

| Modèle | Motif d'exclusion |
|---|---|
| [Audio8/Audio8-ASR-0.1B-onnx-runtime](https://hf.co/Audio8/Audio8-ASR-0.1B-onnx-runtime) | Licence **CC-BY-NC-4.0** — usage non commercial. Techniquement le plus séduisant (100 M, ONNX int8/int4, FR) mais juridiquement inutilisable pour une application distribuée. À re-examiner si la licence change. |
| [nyralabs/CrisperWhisper2.0](https://hf.co/nyralabs/CrisperWhisper2.0_large) | **Poids sous « Nyra Health Non-Commercial Research License »** : tout usage commercial exige une licence payante. La licence MIT parfois citée pour ce modèle ne couvre que le code d'inférence, pas les poids. Cas d'école de la confusion « gratuit » / « ouvert ». Les métadonnées du dépôt n'annoncent par ailleurs que l'anglais et l'allemand, alors que la documentation revendique un support multilingue large — contradiction non résolue, sans objet tant que la licence bloque. |
| [mistralai/Voxtral-Mini-4B-Realtime-2602](https://hf.co/mistralai/Voxtral-Mini-4B-Realtime-2602) | 4 Md de paramètres — hors cible smartphone. **Pertinent en revanche côté API GSIE** pour la transcription serveur temps réel, à traiter dans une veille distincte. |
| [CohereLabs/cohere-transcribe-03-2026](https://hf.co/CohereLabs/cohere-transcribe-03-2026) | Même motif : qualité multilingue élevée mais gabarit serveur, pas terrain. |
| Vosk Android | Non écarté, mais **déclassé** : reste le repli le plus sûr en intégration (Apache-2.0, portage Android natif), avec une qualité FR nettement dépassée par les modèles 2026. À conserver comme témoin bas de gamme du benchmark. |

### 2.5 Protocole de vérification proposé

Aucun de ces modèles ne doit entrer dans GeoSylva sans mesure. Le banc minimal :

1. **Corpus** — 30 à 50 dictées de martelage réelles en français, enregistrées
   au micro d'un smartphone en conditions forestières (vent, pluie, distance
   variable), avec transcription de référence produite à la main.
2. **Métriques** — WER global ; **WER restreint au lexique métier** (essences,
   qualités, diamètres) qui est la seule métrique décisionnelle ; latence de
   première transcription ; consommation batterie sur 30 minutes ; taille du
   paquet embarqué.
3. **Terminaux** — au moins un terminal haut de gamme et un terminal d'entrée
   de gamme, l'entrée de gamme étant la vraie contrainte terrain.
4. **Témoins** — `RecognizerIntent` natif (existant) et Vosk FR (bas de gamme).
5. **Critère de bascule** — un modèle ne remplace l'existant que s'il gagne sur
   le WER métier **et** tient la latence **et** fonctionne avion en mode avion.

### 2.6 Recommandation Axe A

**Hypothèse.** Benchmarker trois candidats seulement — VibeVoice-ASR-BitNet,
Nemotron-3.5-ASR-streaming, Qwen3-ASR-0.6B — contre les deux témoins. Le
travail est cadrable en une expérimentation `21_EXPERIMENTS/` sans toucher au
code applicatif : la sortie attendue est un tableau de mesures, pas une
intégration.

Un point mérite d'être tranché en amont par le Fondateur : la dictée de
martelage est un **flux continu**, pas une requête ponctuelle. Si ce cadrage est
retenu, le streaming cache-aware de Nemotron devient un critère structurant et
non un simple bonus.

---

## 3. Axe B — Perception et VLA pour l'acquisition drone

### 3.1 Distinguer trois couches, qui n'ont ni la même maturité ni le même risque

La confusion la plus coûteuse dans ce domaine consiste à traiter « VLA » comme
une brique unique. Il y en a trois :

| Couche | Ce qu'elle fait | Maturité open source | Risque constitutionnel |
|---|---|---|---|
| **C1 — Perception aérienne** | Détecte et segmente sur image drone (arbres, houppiers, trouées, départs de feu) | **Mûre** : modèles prêts à l'emploi, fine-tuning documenté | Faible — production d'évidence, contrôlable par l'opérateur |
| **C2 — VLM aérien** | Décrit une scène aérienne en langage, répond à des questions, produit du texte structuré | **Émergente** : premiers modèles dédiés en 2026 | Modéré — sortie interprétative, doit rester explicable et sourcée |
| **C3 — VLA de navigation** | Traduit une instruction en commandes de vol continues | **Recherche** : publications 2026, pas de produit | **Élevé — voir §3.4** |

### 3.2 Couche C1 — perception aérienne (exploitable dès maintenant)

**Vérifié.** Une série de modèles de segmentation et de détection sur imagerie
drone a été publiée en août 2026 par `dronefreak`, incluant la segmentation
sémantique aérienne ([aeroscapes-yolo26x-sem](https://hf.co/dronefreak/aeroscapes-yolo26x-sem),
[vdd-yolo26x-sem](https://hf.co/dronefreak/vdd-yolo26x-sem)) et la détection
UAV ([seadronessee-rfdetr-small](https://hf.co/dronefreak/seadronessee-rfdetr-small)).

**Point de gouvernance à ne pas manquer.** Ces modèles se répartissent en deux
familles juridiquement opposées :

- les dérivés **Ultralytics (YOLOv8 / YOLO11 / YOLO26) sont en AGPL-3.0** —
  licence contaminante, incompatible avec une distribution non ouverte de
  GeoSylva ou d'Ignis ;
- les dérivés **RF-DETR sont en Apache-2.0** — utilisables sans contrainte de
  réciprocité.

**Hypothèse.** À contrainte de licence égale, la piste RF-DETR est donc la seule
défendable pour du code embarqué dans nos applications, sauf décision explicite
d'ouvrir le composant concerné. Ce constat vaut au-delà de cette veille : il
s'applique à toute réutilisation d'un modèle Ultralytics dans l'écosystème.

**Vérifié.** Pour la donnée satellitaire (et non drone), la famille
[Prithvi-EO-2.0](https://hf.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M) IBM/NASA
reste en Apache-2.0 et déjà couverte par
`ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md` §4. Elle ne répond pas
au besoin drone : résolution et capteurs différents.

### 3.3 Couche C2 — VLM aérien

**Vérifié.** [MirilAI/Miril-DroneVLM-2B-2](https://hf.co/MirilAI/Miril-DroneVLM-2B-2)
(juillet 2026, Apache-2.0, basé sur google/gemma-4-E2B-it) est un VLM
spécifiquement entraîné sur imagerie aérienne : compréhension de scène,
ancrage visuel, sortie structurée, revendiqué « edge-ai ».

**Réserve dirimante : le modèle est annoncé en anglais uniquement.** Pour un
usage GSIE, cela impose soit une couche de traduction — qui dégrade la
traçabilité de l'évidence — soit un fine-tuning français. Aucune des deux
options n'est gratuite.

### 3.4 Couche C3 — VLA de navigation : ligne rouge

**Rapporté.** L'année 2026 a vu apparaître plusieurs VLA aériens :
[AerialVLA](https://github.com/XuPeng23/AerialVLA) (Apache-2.0, poids LoRA
publiés, contrôle continu 3 DoF), [LiteVLA-H](https://arxiv.org/abs/2605.00884)
(256 M de paramètres, 19,7 Hz de commandes sur Jetson AGX Orin selon les
auteurs), AutoFly, SINGER, AIR-VLA. Une revue de 183 contributions
[couvre le domaine](https://www.mdpi.com/2504-446X/10/6/412).

**Position recommandée : ne pas intégrer, surveiller.** Trois raisons, dans cet
ordre :

1. **Constitutionnelle.** `GSIE-CON-001` pose que l'IA assiste et ne décide
   jamais. Un modèle qui produit des commandes de vol continues *décide*, et
   son raisonnement n'est ni explicable ni contournable en vol. Intégrer C3
   sans RFC dédié serait un contournement de la Constitution, pas une avancée
   technique.
2. **Réglementaire.** Le vol autonome de drone en France relève d'un cadre
   (scénarios standards, exigences opérateur) qui ne se traite pas dans une
   veille technique. Aucune ligne de code ne doit précéder cette analyse.
3. **Technique.** Les performances publiées le sont sur benchmarks de
   simulation. Aucune ne concerne le vol sous canopée, qui est notre cas réel
   et le plus difficile.

**Hypothèse.** La valeur exploitable de C3 pour nous à court terme n'est pas le
contrôle : c'est le **mode sémantique** que LiteVLA-H sépare explicitement du
mode guidage — description de scène et narration à destination de l'opérateur.
C'est de la couche C2 déguisée, et elle, elle est intégrable.

### 3.5 Recommandation Axe B

1. **C1 — engager.** Constituer un jeu d'évaluation d'imagerie drone forestière
   annotée, et mesurer un modèle RF-DETR fine-tuné dessus. Sans ce jeu de
   données, aucun modèle de cette couche ne peut être qualifié ; c'est le
   goulot d'étranglement réel, pas le choix du modèle.
2. **C2 — sonder.** Évaluer Miril-DroneVLM sur nos images, en anglais d'abord,
   pour mesurer si la qualité justifie le coût d'une francisation.
3. **C3 — surveiller uniquement.** Réexamen à la prochaine veille. Toute
   évolution vers l'intégration passe par un RFC dans `02_RFC/`, pas par une
   décision technique.

---

## 3 bis. Addendum du 2026-08-16 — arbitrages du Fondateur et vérifications

### 3bis.1 Axe A — la spécification de dictée change le classement

**Vérifié (Fondateur).** La dictée de martelage prend la forme d'énoncés courts
et structurés, un par arbre : « chêne rouvre 50 cm hauteur 20 m », « douglas
25 m diamètre 60 cm dégât d'exploitation ». L'ordre des champs varie d'un
énoncé à l'autre ; ce sont les **unités** qui portent le sens.

Conséquence : **D1 est tranchée dans le sens de l'énoncé court**, pas du flux
continu. Le streaming cesse d'être un critère structurant.

**Vérifié.** Qwen3-ASR accepte un **contexte libre en `prompt`** pour biaiser la
transcription vers un vocabulaire métier. Face à un lexique fermé et
hors-distribution (essences composées, défauts), cette capacité devient le
critère dominant. Qwen3-ASR passe donc **en tête de la liste courte**, devant
VibeVoice-ASR-BitNet et Nemotron.

**Vérifié.** Les modèles ASR spécifiquement français publiés sur le Hub relèvent
tous de la génération wav2vec2 (2022-2024) et sont dépassés. La voie n'est pas
un modèle « français » mais un modèle multilingue 2026 **biaisé par notre
lexique**.

Le banc est ouvert : `21_EXPERIMENTS/EXP-0002_BANC_STT_GEOSYLVA/`.

### 3bis.2 Axe B — le besoin exprimé n'est pas, pour l'essentiel, un problème d'IA

**Besoin exprimé (Fondateur).** Vol autonome dans une zone donnée, évitement
autonome des zones de vol interdit et des obstacles type éoliennes.

**Constat.** Trois des quatre briques nécessaires ne sont pas des modèles :

| Brique | Solution réelle | Nature |
|---|---|---|
| Rester dans une zone donnée | Geofence du contrôleur de vol (PX4, ArduPilot) | Déterministe, auditable |
| Éviter les zones interdites | Données officielles DGAC — Géoportail drones, SUP-AIP — chargées comme polygones d'exclusion | Problème de **donnée**, pas de perception |
| Éviter les éoliennes | Liste des obstacles artificiels publiée par le SIA/DGAC, complétée par un capteur de proximité | Base de données + capteur |
| Comprendre ce qui est survolé | Perception C1 / narration C2 | **Ici seulement l'IA a sa place** |

**Ce constat est une bonne nouvelle pour la gouvernance.** Une geofence
alimentée par des données officielles est explicable, contournable et
vérifiable — elle satisfait `GSIE-CON-001` par construction, là où un VLA de
navigation le viole par construction.

**Verrou réel.** Le vol autonome relève de la catégorie *Spécifique* :
analyse SORA, dossier de sécurité, autorisation DGAC. Le verrou est
réglementaire et opérationnel, pas algorithmique. Aucune ligne de code ne doit
précéder cette analyse.

### 3bis.3 « Prisme » — identification et verdict

Le Fondateur a signalé Prisme comme piste drone, à la suite d'une vidéo de
vulgarisation. Deux clarifications :

1. **Il ne s'agit pas** de *Prism SKR* de Teledyne FLIR, logiciel propriétaire
   d'autonomie et de reconnaissance de cible pour munitions rôdeuses et
   contre-UAS. Sans rapport avec nos besoins, et hors périmètre de
   Quintessences.
2. **Il s'agit** d'un algorithme académique de robotique. La description
   correspond à
   [PRISM — Pointcloud Reintegrated Inference via Segmentation and
   Cross-attention for Manipulation](https://arxiv.org/abs/2507.04633) :
   apprentissage direct depuis nuages de points bruts et état articulaire du
   robot, sans modèle pré-entraîné ni dataset intermédiaire, sortie en actions
   motrices lissées par un module de diffusion. Un homonyme existe
   ([PRISM — Polynomial Representations for Interaction-Structured Motor
   Control](https://arxiv.org/html/2607.23473v1)), également orienté contrôle
   corporel et manipulation riche en contacts.

**Verdict : sans objet pour nos drones.** Ces travaux résolvent la
**manipulation** — préhension, force de contact, friction, angles
d'articulation. Un drone d'acquisition n'a ni bras, ni articulations, ni
contact : son problème est la navigation et la perception. Le rapprochement
avec les drones provient d'une remarque incidente du vulgarisateur, non des
publications.

**Leçon de méthode, plus utile que le modèle lui-même.** Les vidéos de veille
généraliste mélangent trois catégories que nous devons tenir séparées : poids
réellement ouverts, code ouvert sous poids fermés, et produits propriétaires
annoncés « gratuits ». La vérification cas par cas sur la fiche officielle
n'est pas une formalité — sur cette seule séquence, elle a corrigé deux
erreurs de classement.

---

## 4. Ce que cette veille ne couvre pas

Le Fondateur a mentionné deux autres familles, écartées du périmètre de ce
document par cadrage explicite et à traiter séparément :

- **Modèles de raisonnement** pour les moteurs Reasoning / Diagnostic /
  Recommendation — partiellement couverts par
  `VEILLE_LLM_ET_RD_GSIE_2026-08-12.md`.
- **World models** pour le moteur Simulation et le Centre de Commandement
  UE5.8. Signalé au passage : la famille NVIDIA Cosmos / Alpamayo a beaucoup
  bougé en 2026 ([Alpamayo2-Super](https://hf.co/nvidia/Alpamayo2-Super),
  licence OpenMDW-1.1), mais elle est orientée conduite autonome et son
  transfert au domaine forestier est une question ouverte, pas un acquis.

---

## 5. Décisions attendues du Fondateur

| # | Question | Effet si tranchée |
|---|---|---|
| D1 | La dictée de martelage est-elle un flux continu ou une requête ponctuelle ? | Détermine si le streaming est un critère éliminatoire du benchmark STT |
| D2 | Ouvre-t-on une expérimentation `21_EXPERIMENTS/` pour le banc STT ? | Débloque l'Axe A ; coût estimé faible, sans impact sur le code GeoSylva |
| D3 | Accepte-t-on l'AGPL-3.0 pour un composant de vision embarqué ? | Si non — recommandé — la piste Ultralytics est fermée définitivement |
| D4 | Constitue-t-on un jeu d'imagerie drone forestière annotée ? | Prérequis absolu de l'Axe B ; c'est un effort de données, pas de modèle |

---

## 6. Sources

Fiches modèles consultées le 2026-08-16 sur le Hub Hugging Face :

- [microsoft/VibeVoice-ASR-BitNet](https://hf.co/microsoft/VibeVoice-ASR-BitNet)
- [nvidia/nemotron-3.5-asr-streaming-0.6b](https://hf.co/nvidia/nemotron-3.5-asr-streaming-0.6b)
- [Qwen/Qwen3-ASR-0.6B-hf](https://hf.co/Qwen/Qwen3-ASR-0.6B-hf)
- [Audio8/Audio8-ASR-0.1B-onnx-runtime](https://hf.co/Audio8/Audio8-ASR-0.1B-onnx-runtime)
- [mistralai/Voxtral-Mini-4B-Realtime-2602](https://hf.co/mistralai/Voxtral-Mini-4B-Realtime-2602)
- [CohereLabs/cohere-transcribe-03-2026](https://hf.co/CohereLabs/cohere-transcribe-03-2026)
- [nyralabs/CrisperWhisper2.0_large](https://hf.co/nyralabs/CrisperWhisper2.0_large)
- [MirilAI/Miril-DroneVLM-2B-2](https://hf.co/MirilAI/Miril-DroneVLM-2B-2)
- [dronefreak/aeroscapes-yolo26x-sem](https://hf.co/dronefreak/aeroscapes-yolo26x-sem)
- [dronefreak/seadronessee-rfdetr-small](https://hf.co/dronefreak/seadronessee-rfdetr-small)
- [ibm-nasa-geospatial/Prithvi-EO-2.0-300M](https://hf.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M)
- [nvidia/Alpamayo2-Super](https://hf.co/nvidia/Alpamayo2-Super)

Publications et dépôts (non rejoués) :

- [LiteVLA-H — arXiv:2605.00884](https://arxiv.org/abs/2605.00884)
- [AerialVLA — dépôt officiel](https://github.com/XuPeng23/AerialVLA)
- [VLA pour la robotique aérienne — revue MDPI Drones 10(6):412](https://www.mdpi.com/2504-446X/10/6/412)
- [NVIDIA Nemotron 3.5 ASR — annonce presse technique](https://www.marktechpost.com/2026/06/06/nvidia-releases-nemotron-3-5-asr-a-600m-parameter-cache-aware-streaming-model-transcribing-40-language-locales-in-real-time/)

Sources internes :

- `apps/GeoSylva/app/src/main/java/com/forestry/counter/presentation/screens/settings/SettingsHomeScreen.kt`
- `apps/GeoSylva/RESEARCH_OPPORTUNITIES.md`
- `apps/GeoSylva/GEOSYLVA_3_SPECIFICATION_FONCTIONNELLE.md`
- `GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md`
- `GSIE/RESEARCH/VEILLE_LLM_ET_RD_GSIE_2026-08-12.md`

---

## 7. Historique des modifications

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 0.1.0 | 2026-08-16 | Claude | Création — Axes STT embarqué et VLA/perception drone |
