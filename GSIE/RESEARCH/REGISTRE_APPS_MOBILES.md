# Registre des opportunités — Applications mobiles

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-REG-MOBILE |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Dernier reclassement** | 2026-08-16 |
| **Cible** | GeoSylva (Android, terrain), Artemis (Phase 4), tout futur client mobile |
| **Contraintes de la cible** | Hors-ligne intégral · CPU/NPU sans GPU dédié · énergie limitée · français par défaut · licence compatible distribution applicative |
| **Registres frères** | GSIE Serveur · GSIE PC · Hub Unreal Engine · Applications clientes |

---

## 1. Comment lire ce registre

Chaque opportunité porte un identifiant stable `OPP-xxx`, unique dans **tous** les
registres. Elle entre une fois et n'en sort jamais : elle change de rang, de
statut, et son verrou se lève ou se déplace.

**Le classement se fait sur le seul intérêt pour cette cible** — de 1 à 5, où 5
signifie « débloque un besoin identifié et daté » et 1 « curiosité sans besoin
rattaché ». La note est un point de départ discutable, pas un verdict : elle se
révise à chaque analyse.

**Le verrou n'est pas une pénalité.** Une opportunité bloquée par un corpus
manquant garde son rang : ce qui manque devient une tâche, pas une raison de
descendre. La colonne « Pour le lever » dit ce qu'il faudrait faire. Seules les
opportunités du §5 sont réellement écartées, et uniquement pour des motifs durs :
licence contaminante ou incompatible, ou contradiction avec la Constitution.

**Statuts** (repris de l'étude du 18 juillet, §1.2) : INTÉGRER · BENCHMARKER ·
SURVEILLER · ÉCARTER.

---

## 2. Ce que la cible mobile interdit, quel que soit l'intérêt

Trois règles issues de l'architecture GeoSylva, à appliquer avant toute notation :

1. **Le réseau n'est jamais une condition de fonctionnement.** Saisie,
   modification, contrôles qualité, formules dendrométriques approuvées, cartes
   de mission, historique et export de secours restent locaux. Un modèle en
   ligne est un confort, jamais un prérequis.
2. **Aucune sortie de modèle n'est une donnée tant qu'un humain ne l'a pas
   validée.** Statut `SUGGESTION_IA` → `VALIDEE_UTILISATEUR`. Tant que non
   validée : aucune valeur déclenchante — ni cubage, ni conseil sylvicole, ni
   conclusion écologique.
3. **Les modèles se distribuent en packs de mission signés**, versionnés,
   vérifiés par SHA-256, avec licence et attribution consultables hors ligne —
   jamais en téléchargement libre depuis l'interface.

---

## 3. Classement au 2026-08-16

| Rang | ID | Opportunité | Intérêt | Verrou actuel | Pour le lever | Statut |
|---:|---|---|:-:|---|---|---|
| 1 | OPP-001 | **Qwen3-ASR-0.6B** — ASR biaisable par lexique métier | 5 | Pas de build embarqué officiel ; portage Android à qualifier | Banc EXP-0002 + portage ONNX/GGUF à évaluer | BENCHMARKER |
| 2 | OPP-002 | **GLiNER2 Multi** — extraction structurée, 205 M, CPU | 5 | Français et vocabulaire forestier non validés | Annoter 200 énoncés de dictée et mesurer | BENCHMARKER |
| 3 | OPP-006 | **VibeVoice-ASR-BitNet** — 323 M, MIT, inférence CPU | 4 | Capacité de biasing non qualifiée | Test de biasing dans le banc EXP-0002 | BENCHMARKER |
| 4 | OPP-018 | **Pack embarqué essences françaises** — vision légère INT8 | 4 | **Corpus forestier français absent.** Pl@ntNet-300K seul ne suffit pas | Constituer un corpus saisons/organes/espèces proches ; contacter CIRAD/Pl@ntNet pour licence du modèle embarqué | SURVEILLER |
| 5 | OPP-008 | **BirdNET** — bioacoustique hors ligne | 4 | Aucun — candidat de pack local direct | Packaging en pack de mission signé | INTÉGRER |
| 6 | OPP-017 | **Pl@ntNet API** — identification botanique assistée | 4 | Réseau requis ; conditions commerciales à confirmer par écrit | File d'attente offline + confirmation écrite des tarifs | BENCHMARKER |
| 7 | OPP-014 | **Nemotron-3.5-ASR-streaming 0.6B** | 3 | Écosystème NeMo lourd ; portage Android à qualifier | Banc EXP-0002 ; avantage streaming neutralisé par la dictée courte | BENCHMARKER |
| 8 | OPP-029 | **Grammaire déterministe de dictée** — parseur piloté par unités | 5 | Aucun — à écrire, pas à trouver | Rédaction dans EXP-0002 | INTÉGRER |
| 9 | OPP-030 | **Petit LLM quantifié embarqué** — assistant terrain hors ligne | 3 | Valeur d'usage non démontrée ; coût énergétique | Établir d'abord le besoin réel côté forestier | SURVEILLER |
| 10 | OPP-031 | **Classifieurs ONNX/TFLite légers** — défauts, qualités, dégâts | 3 | Corpus photo terrain absent | Même effort de données que OPP-018 | SURVEILLER |

> **Note de classement.** OPP-029 est notée 5 mais placée au rang 8 : elle est
> indissociable de OPP-001 et OPP-002, dont elle constitue l'aval. Elle n'a pas
> de valeur seule, et n'a pas de verrou — il n'y a rien à trouver, seulement à
> écrire.

---

## 3bis. Enrichissement — recherche web du 2026-08-16

**Le biasing contextuel est un axe de recherche actif et récent, pas une
fonctionnalité de niche.** Plusieurs publications 2024-2026 couvrent le
biasing par vocabulaire dynamique, la fusion superficielle par trie et
l'intégration LLM pour la ASR contextuelle. L'IEEE ICASSP 2026 (Barcelone,
4-8 mai) présente plusieurs papiers sur ce thème précis, dont un sur
l'apprentissage par renforcement pour les modèles de langage vocaux
contextuels. **Ce constat renforce le choix de OPP-001 (Qwen3-ASR) en rang 1** :
le biasing par prompt n'est pas une curiosité mais une piste que le secteur
prend au sérieux au moment même où nous l'évaluons.

**Absence documentée de recherche spécifiquement française.** La recherche n'a
trouvé aucun résultat sur le biasing contextuel appliqué au français en
particulier — les publications identifiées portent sur l'anglais ou sont
génériques multilingues. **C'est une lacune réelle, pas un artefact de
recherche** : elle confirme que le banc EXP-0002, avec son corpus de dictées
françaises et ses paires phonétiquement ambiguës (2/12, 6/16, 60/70), n'a pas
de précédent publié à réutiliser. Le travail de validation empirique reste
entièrement à notre charge.

---

## 4. Fiches

### OPP-001 · Qwen3-ASR-0.6B — le favori du banc
782 M paramètres réels malgré le nom, Apache-2.0, français parmi 30 langues.
**Ce qui le place premier :** il accepte un contexte libre en `prompt` pour
biaiser la transcription — vérifié sur la fiche officielle. « Chêne rouvre » et
« dégât d'exploitation » sont hors-distribution dans tout modèle généraliste ;
c'est là que la transcription casse, et c'est exactement ce que le biasing
corrige.

### OPP-002 · GLiNER2 Multi — la brique à double emploi
205 M paramètres, extraction structurée, exécution CPU. Identifiée pour la
normalisation du Data Registry côté serveur, **elle sert aussi à l'extraction des
champs de la dictée** côté mobile. Deux besoins, une brique.
*Renvoi croisé : registre GSIE Serveur.*

### OPP-029 · La grammaire de dictée — ce qu'aucun modèle ne doit faire
Les deux exemples de dictée fournis par le Fondateur — « chêne rouvre 50 cm
hauteur 20 m » et « douglas 25 m diamètre 60 cm dégât d'exploitation » — n'ont
pas le même ordre de champs. Ce sont les **unités** qui portent le sens, y
compris quand le mot « diamètre » ou « hauteur » est omis.
Un parseur positionnel est donc exclu, et un LLM n'a pas sa place ici : une
grammaire déterministe est auditable, gratuite en calcul, et ne peut pas
halluciner un diamètre. GLiNER2 n'intervient qu'en rattrapage sur ce que la
grammaire ne couvre pas.

### OPP-018 · Le pack essences — bloqué par la donnée, pas par la technique
Le mode hors ligne de Pl@ntNet est réservé à son application ; l'API n'en donne
pas le modèle. Pl@ntNet-300K (CC BY 4.0, ~306 000 images, 1 081 espèces) est une
base insuffisante seule. Le modèle devra savoir répondre « espèce inconnue »
plutôt que de forcer un taxon du catalogue.
**Ce verrou est le même que celui de la perception drone** : dans les deux cas il
manque un corpus, pas un modèle.

---

## 5. Écartées — motifs durs uniquement

| ID | Opportunité | Motif |
|---|---|---|
| OPP-101 | Audio8-ASR-0.1B ONNX | CC-BY-NC-4.0. Techniquement le meilleur profil embarqué du lot — 100 M, français, int8/int4. **À rouvrir immédiatement si la licence change.** |
| OPP-102 | CrisperWhisper 2.0 | Poids sous licence de recherche non commerciale ; la mention « MIT » ne couvre que le code d'inférence. |
| OPP-106 | Voxtral-Mini-4B, cohere-transcribe | Gabarit serveur. Non écartées du projet — **déplacées** vers le registre GSIE Serveur. |
| OPP-109 | LLM pour les calculs dendrométriques | Contredit le principe : le modèle explique, les moteurs calculent. Définitif. |

---

## 6. État de l'existant

| Brique | État | Commentaire |
|---|---|---|
| `RecognizerIntent` Android | En production | Moteur natif : qualité, vocabulaire et comportement hors réseau non maîtrisés. C'est le témoin à battre. |
| Vosk FR | Identifié, non intégré | Apache-2.0, portage Android natif, qualité dépassée. Sert de plancher au banc. |
| Banc `EXP-0002` | Ouvert le 2026-08-16 | Protocole, corpus et critère de bascule écrits. |

---

## 7. Sources absorbées

| Document d'origine | Apport |
|---|---|
| `VEILLE_STT_EMBARQUE_ET_VLA_DRONE_2026-08-16` | Candidats ASR, pièges de licence, spécification de dictée |
| `VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20` | Pl@ntNet, pack embarqué, offline-first, conditions commerciales |
| `ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18` (§2.1, §13) | Répartition par niveau de calcul, packs de mission signés, ce qui doit rester local |
| `apps/GeoSylva/RESEARCH_OPPORTUNITIES.md` | Vosk, état de la saisie vocale, contraintes terrain |

---

## 8. Journal des reclassements

| Date | Mouvement | Motif |
|---|---|---|
| 2026-08-16 | Création — 10 opportunités actives, 4 écartées | Consolidation par cible d'exécution |
| 2026-08-16 | OPP-001 passe devant OPP-006 et OPP-014 | Biasing par contexte libre vérifié ; dictée cadrée comme énoncé court |
| 2026-08-16 | OPP-018 conserve son rang malgré son verrou | Changement de méthode : un corpus manquant est une tâche, pas une pénalité |

---

## 9. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 1.0.0 | 2026-08-16 | Claude | Création — registre par cible d'exécution |
