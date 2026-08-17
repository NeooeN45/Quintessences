# Registre des opportunités — GSIE Serveur

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-REG-SERVEUR |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Dernier reclassement** | 2026-08-16 |
| **Cible** | API GSIE, RAG scientifique, orchestration d'agents, moteurs mutualisés, calcul asynchrone lourd |
| **Contraintes de la cible** | GPU mutualisé ou absent · base canonique PostgreSQL/PostGIS/AGE · traçabilité obligatoire · pas de verrouillage fournisseur |
| **Registres frères** | Applications mobiles · GSIE PC · Hub Unreal Engine · Applications clientes |

---

## 1. Comment lire ce registre

Identifiants `OPP-xxx` stables et uniques dans tous les registres. Une
opportunité entre une fois et n'en sort jamais : elle change de rang, de statut,
et son verrou se lève ou se déplace.

**Le classement se fait sur le seul intérêt pour cette cible**, de 1 à 5. La note
est un point de départ discutable, pas un verdict.

**Le verrou n'est pas une pénalité** : ce qui manque devient une tâche. Seules
les opportunités du §6 sont écartées, et pour des motifs durs uniquement —
licence incompatible, contradiction constitutionnelle, ou remise en cause de la
base canonique.

**Statuts** : INTÉGRER · BENCHMARKER · SURVEILLER · ÉCARTER.

---

## 2. Ce que la cible serveur impose, quel que soit l'intérêt

Quatre règles à appliquer avant toute notation. Elles ont déjà coûté des
arbitrages ; les rouvrir demanderait un RFC.

1. **La vérité canonique est PostgreSQL / PostGIS / Apache AGE.** Tout index
   vectoriel, tout store spécialisé, tout cache est une **projection
   reconstruisible** — jamais autoritaire. Un moteur de recherche qui devient la
   source de vérité est une régression, pas une optimisation.
2. **Le LLM orchestre et explique ; il ne calcule jamais.** Une valeur numérique
   vient d'un moteur déterministe ou d'une source citée. Le modèle transforme un
   résultat structuré en explication, sans en changer les nombres.
3. **Toute réponse conserve sa provenance** : `model_id`, version, `evidence_ids`,
   paramètres, incertitude, domaine de validité, état de validation humaine. Une
   réponse non traçable n'est pas une réponse.
4. **Aucun verrouillage fournisseur.** La passerelle `gsie-ai-gateway` expose des
   points d'entrée neutres (`/ai/chat`, `/ai/embed`, `/ai/rerank`,
   `/ai/research`, `/ai/transcribe`, `/ai/vision`) et journalise modèle, version,
   coût, durée et citations — précisément pour pouvoir changer de fournisseur.
   Les clés restent exclusivement côté serveur.

---

## 3. Classement au 2026-08-16

| Rang | ID | Opportunité | Intérêt | Verrou actuel | Pour le lever | Statut |
|---:|---|---|:-:|---|---|---|
| 1 | OPP-032 | **GSIE-Bench / GSIE-Eval-FR** — banc d'évaluation propriétaire | 5 | Aucun banc équivalent n'existe ; tout est à construire | Écrire 100 à 500 cas forestiers validés par des professionnels, jamais versés à l'entraînement | INTÉGRER |
| 2 | OPP-007 | **Qwen3-Embedding + Qwen3-Reranker 0.6B** | 5 | Scores éditeur non rejoués sur données françaises | Mesurer sur corpus FR forestier/pédologique juridiquement utilisable | BENCHMARKER |
| 3 | OPP-002 | **GLiNER2 Multi** — extraction structurée, 205 M, CPU | 5 | Français et vocabulaires forestiers non validés | Annotations GSIE + `GSIE-Norm-Bench` | BENCHMARKER |
| 4 | OPP-004 | **DoWhy + Tigramite** — causalité et inférence | 5 | Aucun — briques matures | Intégration sous contraintes métier du Correlation Engine | INTÉGRER |
| 5 | OPP-005 | **PyMC + MAPIE** — quantification d'incertitude | 5 | Aucun | Rendre l'intervalle obligatoire dans le contrat de sortie des moteurs | INTÉGRER |
| 6 | OPP-010 | **LLM multilingue ouvert 8B** — Apertus, Ministral 3, Qwen3 | 5 | Choix non tranché ; benchmark français absent | OPP-032 d'abord : on ne choisit pas un modèle sans banc | BENCHMARKER |
| 7 | OPP-033 | **Benchmarks externes réutilisables** — GEO-Bench, PANGAEA, REOBench, 3D3, FLAIR, Synthetic Forest | 4 | Aucun ; code reproductible et baselines publiées | Adosser GSIE-Bench à leurs protocoles plutôt que réinventer | INTÉGRER |
| 8 | OPP-013 | **NOOA** — agents objets typés, Apache-2.0 | 4 | Statut alpha ; Python ≥3.12 | POC sur un agent GSIE existant avant tout engagement d'architecture | SURVEILLER |
| 9 | OPP-020 | **NeMo Evaluator + Guardrails** | 4 | Dépendance NVIDIA ; conditions de production à qualifier | Usage en intégration continue sur GSIE-Eval-FR, sans dépendance dure | BENCHMARKER |
| 10 | OPP-011 | **Prithvi-EO-2.0 + AnySat** — observation de la Terre | 4 | Calcul GPU ; validation territoriale française absente | Limiter le premier benchmark à deux modèles, sur zone pilote | BENCHMARKER |
| 11 | OPP-012 | **BioCLIP 2 / SpeciesNet** — biodiversité visuelle | 4 | Validation humaine obligatoire en aval | Chaîne pré-identification probabiliste → confirmation | BENCHMARKER |
| 12 | OPP-034 | **AI-Q Blueprint** — agent de recherche avec citations | 3 | Architecture de référence lourde | Récupérer le patron, pas le déploiement | SURVEILLER |
| 13 | OPP-019 | **NeMo Retriever / Embed / Rerank** (NIM) | 3 | Config de référence ≥ 3 GPU H100 ; licence de production | Prototyper sur endpoints hébergés, jamais en dépendance dure | BENCHMARKER |
| 14 | OPP-023 | **NuExtract3 / Table Transformer / mDeBERTa** | 3 | Droits des documents à contrôler ; NuExtract3 lourd à affiner localement | Comparateurs de GLiNER2 sur le même banc | BENCHMARKER |
| 15 | OPP-024 | **Chronos-Bolt / TimesFM** — séries temporelles | 3 | Sous-benchmark séries temporelles inexistant | Définir les tâches météo/capteurs/hydrologie avant de comparer | SURVEILLER |
| 16 | OPP-106 | **Voxtral-Mini-4B-Realtime / cohere-transcribe** — ASR serveur | 3 | Gabarit GPU ; besoin serveur non encore formulé | Qualifier le besoin de transcription temps réel côté API | SURVEILLER |
| 17 | OPP-016 | **nvmath-python** — CUDA-X math sous Python | 3 | Aucun goulot d'étranglement mesuré ne le justifie | Profiler d'abord le Correlation Engine ; fallback scipy conservé | SURVEILLER |
| 18 | OPP-036 | **P** — vérification formelle de protocoles distribués | 3 | Le protocole Server Meshing n'est pas encore spécifié | Modéliser le transfert d'autorité en P **avant** de l'implémenter | SURVEILLER |
| 19 | OPP-028 | **Adaptateurs LoRA GSIE spécialisés** | 3 | GSIE-Eval-FR absent ; matériel local insuffisant | OPP-032, puis test court sur GPU loué (~4 à 8 $) | SURVEILLER |
| 20 | OPP-037 | **Patron OTP « supervision tree »** | 3 | Aucun — c'est un patron, pas une dépendance | Transposable en Python/Rust/Go sans adopter Elixir | SURVEILLER |
| 21 | OPP-025 | **Gemma 4 E2B/E4B** — multimodal compact | 2 | **Licence Google non qualifiée pour usage commercial** | Analyse juridique avant tout prototype | SURVEILLER |
| 22 | OPP-026 | **Nemotron 3.5 Lightning** — MoE 30 B / 3 B actifs | 2 | Déploiement de classe A100/H100 ; hors de portée du matériel actuel | Réévaluer si l'infrastructure change | SURVEILLER |
| 23 | OPP-038 | **Dafny** — preuve de propriétés | 2 | Déclencheur non atteint | Activer seulement si des bugs logiques récurrents résistent aux tests | SURVEILLER |

---

## 3 bis. Plateforme de données — sous-ensemble classé à part

Ces opportunités partagent la même cible mais forment un bloc cohérent : elles se
décident ensemble, par phases, et non ligne par ligne. Elles proviennent de
`ETUDE_DATA_PLATFORM_EMERGENTE_2026-08-09`, qui les avait déjà réparties par
niveau d'adoption — répartition conservée ici.

| Rang | ID | Opportunité | Intérêt | Verrou actuel | Pour le lever | Statut |
|---:|---|---|:-:|---|---|---|
| 1 | OPP-060 | **STAC** — standard de découverte géospatiale | 5 | Aucun ; standard établi | Adoption immédiate comme catalogue des jeux spatiaux | INTÉGRER |
| 2 | OPP-061 | **COG · GeoParquet · COPC** — formats cloud-native | 5 | Conversion des jeux existants à outiller | Adoption immédiate sur les nouveaux jeux, migration progressive | INTÉGRER |
| 3 | OPP-062 | **Object storage** — MinIO, SeaweedFS ou Ceph | 5 | Choix non tranché entre les trois | Phase 1 du plan d'implémentation : fiabiliser le stockage avant tout le reste | INTÉGRER |
| 4 | OPP-063 | **DuckDB** — analytique locale et lecture S3 | 4 | Aucun ; complète la base, ne la remplace pas | Adoption immédiate en exploration. *Renvoi croisé : registre GSIE PC.* | INTÉGRER |
| 5 | OPP-064 | **Apache Iceberg** — tables analytiques versionnées | 4 | Justifié seulement au-delà d'un certain volume | Après le premier pilote, si le volume le justifie | SURVEILLER |
| 6 | OPP-065 | **Pangeo · Xarray · Zarr · Kerchunk** | 4 | Chaîne à monter ; pertinence liée aux cubes climatiques | Après le premier pilote climat | SURVEILLER |
| 7 | OPP-066 | **Apache DataFusion** — moteur analytique Rust | 3 | Aucun goulot mesuré ne le justifie aujourd'hui | POC conditionnel, sur hot path analytique identifié | SURVEILLER |
| 8 | OPP-067 | **SedonaDB / Apache Sedona** | 3 | Recouvre partiellement PostGIS et DuckDB Spatial | POC conditionnel, si un besoin distribué apparaît | SURVEILLER |
| 9 | OPP-068 | **TileDB** — cubes et nuages de points | 2 | Candidat spécialisé ; recouvrement avec COPC/Zarr | Ne pas adopter maintenant | SURVEILLER |

**Le plan d'implémentation de l'étude reste valable et n'est pas à refaire** :
stockage objet fiable → publication Forge vers GSIE → formats et catalogue
spatial → premier dataset réel → benchmark CPU/GPU → accélération spécialisée.
L'ordre compte : le benchmark n'a de sens qu'une fois un dataset réel en place.

### 3ter. Enrichissement — recherche web du 2026-08-16

**NOOA confirmé en détail.** Version 0.0.8 publiée le 30 juillet 2026, Apache
2.0, Python 3.12-3.13 exigé. Deux stratégies d'exécution : `PredictStrategy`
(appel LLM typé unique avec retry local) et `CodeActStrategy` (REPL Python que le
modèle pilote jusqu'à un résultat validé). Performance mesurée : 82,2 % sur
SWE-bench Verified avec GPT-5.5, pour environ 1,1 M tokens et 28 appels modèle
par tâche — contre 2,2 M tokens et 66 appels chez les concurrents à 78,2 %. Ces
chiffres confortent le statut BENCHMARKER de OPP-013 ; le POC reste la bonne
prochaine étape, pas un engagement d'architecture immédiat.

**Le paysage des benchmarks LLM confirme la stratégie GSIE-Bench.** Les
benchmarks généralistes (MMLU, GLUE) sont saturés au-delà de 88 % de score, et le
terrain s'est fragmenté vers des évaluations verticales par domaine — médecine,
droit, science, cybersécurité. Le précédent le plus proche de notre cas :
HealthBench utilise 48 562 critères de rubrique rédigés par 262 médecins de 26
spécialités et 60 pays ; LegalBench-RAG évalue spécifiquement la moitié
« récupération » d'un pipeline RAG juridique, là où la plupart des échecs de
production trouvent leur origine. **Ce constat valide directement l'approche
GSIE-Bench (OPP-032)** : un banc vertical, construit par des professionnels du
domaine, est la norme du secteur en 2026 — pas une réinvention.

**DoWhy — écosystème 2026 confirmé, une clarification de plus sur CausalNex.**
La pile causale 2026 associe des bibliothèques dédiées (DoWhy, EconML,
CausalNex, Tetrad, CausalML) à une évaluation LLM pour les tâches explicatives
connexes. Cette source cite encore CausalNex activement — **à ne pas suivre** :
la fin de vie de CausalNex en juin 2026 reste actée (§6, OPP-143). Une mention
générique dans une veille externe ne rouvre pas une décision déjà tracée.

---

## 4. Fiches — les six premiers

### OPP-032 · GSIE-Bench et GSIE-Eval-FR — la brique qui conditionne toutes les autres
Six opportunités de ce registre attendent ce banc. Sans lui, choisir un LLM,
qualifier un LoRA ou mesurer un gain de RAG relève de l'opinion.

Deux constats de la veille du 11 août structurent sa conception :
- **Aucun benchmark équivalent n'existe.** Les briques INRAE les plus proches
  (OBUP, FOR-EVAL/INSENSÉ, EcoPlant/Sophy, lidaRtRee) couvrent des tâches
  partielles, pas un diagnostic stationnel complet.
- **La méthode, elle, existe.** Deux divisions — *GSIE Closed* (mêmes données,
  mêmes droits, même protocole, pour comparer deux versions à armes égales) et
  *GSIE Open* (nouvelles données autorisées, différences déclarées). Trois
  niveaux de scénarios, dont *Gold* : diagnostic publié ou consensus d'au moins
  deux experts, désaccords arbitrés.

Règle non négociable : les cas de test ne sont **jamais** versés à
l'entraînement, et la séparation se fait par documents, régions et périodes pour
éviter les fuites.

### OPP-007 · Qwen3-Embedding + Reranker 0.6B
Recherche et reclassement multilingues, 0,6 Md chacun. Le couple embedding +
reranker est le cœur du RAG scientifique. **Le gain du reranker par rapport à une
recherche vectorielle seule doit être mesuré**, pas supposé — c'est la réserve
explicite de la veille du 12 août.

### OPP-002 · GLiNER2 Multi
205 M paramètres, extraction structurée, exécution CPU — donc déployable sans
GPU. *Renvoi croisé : registre Applications mobiles, où elle sert au rattrapage
de la dictée de martelage.*

### OPP-004 · DoWhy + Tigramite
Socle du Correlation Engine. Ce que ces bibliothèques apportent n'est pas de la
performance mais de l'**honnêteté méthodologique** : elles rendent explicites les
hypothèses causales qu'une corrélation brute laisse implicites. EconML en
alternative.

### OPP-005 · PyMC + MAPIE
Toute prédiction GSIE doit exposer un intervalle et un domaine de validité.
Bootstrap métier en repli quand le modèle ne s'y prête pas.

### OPP-010 · Le LLM d'orchestration
Apertus 8B Instruct en premier choix à évaluer, Ministral 3 8B et Qwen3 8B en
alternatives. **Aucun fine-tuning factuel initial** : le modèle apprend à appeler
des outils, pas à mémoriser de la science. Le choix attend OPP-032.

---

## 5. Deux dépendances à surveiller de près

**NVIDIA NIM.** Quatre opportunités de ce registre en dépendent (OPP-019,
OPP-020, OPP-034, et indirectement OPP-026). Les endpoints gratuits du programme
développeur couvrent le prototypage, la recherche et les tests — **servir de
vrais utilisateurs est un usage de production** nécessitant une licence AI
Enterprise ou un endpoint partenaire. Tarifs relevés : 4 500 $/GPU/an plein
tarif, 1 125 $ en tarif Inception, ~1 $/GPU/heure en cloud. La passerelle
neutre (§2.4) existe précisément pour que ces quatre opportunités restent
remplaçables.

**Le matériel.** Le poste de référence actuel (RTX 3050 Laptop, ~4 Gio VRAM,
Windows 11) ne permet ni l'auto-hébergement NIM — documenté sous Linux, non
testé sous Windows/WSL — ni le fine-tuning confortable. Plusieurs verrous de ce
registre sont matériels, pas techniques : ils se lèveront par la location
ponctuelle de GPU, pas par un meilleur choix de modèle.

---

## 6. Écartées — motifs durs uniquement

| ID | Opportunité | Motif |
|---|---|---|
| OPP-107 | LLM entraîné depuis zéro | Trop coûteux, difficile à évaluer, probablement moins performant qu'un modèle existant. Rejet explicite de l'étude du 18 juillet. |
| OPP-108 | Auto-hébergement du Blueprint RAG NVIDIA complet | Configuration de référence ≥ 3 GPU H100/B200/RTX Pro 6000. Récupérer l'architecture, pas le déploiement. |
| OPP-111 | Milvus ou Elasticsearch en remplacement de PostgreSQL/PostGIS/AGE | Contredit la règle §2.1 : la base canonique n'est pas négociable. Un index reste une projection. |
| OPP-109 | LLM pour les calculs dendrométriques | Contredit la règle §2.2. Définitif. |
| OPP-112 | Blueprints NVIDIA dépréciés (Flood Intelligence, CorrDiff) | Dépréciés par l'éditeur. |
| OPP-113 | Licence NIM de production anticipée | Aucun client, aucune charge mesurée. À rouvrir quand l'un des deux existe. |
| OPP-114 | Gleam, Mojo, Pony, Unison, MoonBit, Koka, Chapel | Écosystèmes immatures ou à continuité incertaine pour un projet en Phase 4. |
| OPP-115 | Elixir comme langage de la pile | La stack Python + Rust + Go + TypeScript est actée (DEC-000019). **Le patron OTP est retenu séparément** (OPP-037) : c'est l'idée qui vaut, pas le langage. |

---

## 7. Sources absorbées

| Document d'origine | Apport |
|---|---|
| `ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18` | Principe directeur, sélection prioritaire, registre de modèles, répartition par niveau de calcul |
| `VEILLE_LLM_ET_RD_GSIE_2026-08-12` | GLiNER2, Qwen3-Embedding/Reranker, NuExtract3, Nemotron 3.5, faisabilité matérielle |
| `VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20` | Priorisation NIM P0-P3, points de vigilance, architecture `gsie-ai-gateway`, conditions commerciales |
| `VEILLE_NVIDIA_DEV_BLOG_2026-08-08` | NOOA, nvmath-python |
| `ETUDE_NOOA_ORCHESTRATION_AGENTS_2026-08-08` | Identification du dépôt, licence, statut alpha, comparaison à l'orchestration GSIE actuelle |
| `VEILLE_2026-08-11_BENCHMARKS_GSIE` | Verdict sur l'existant, benchmarks externes réutilisables, architecture GSIE-Bench |
| `VEILLE_BEAM_OTP_SERVER_MESHING_2026-08-07` | Patron OTP, P et Dafny, verdict sur les langages émergents |
| `VISION_LLM_SPECIALISES_GSIE_CORE_2026-07-20` | Adaptateurs LoRA, danger du multi-agents non protocolé, stratégie d'entraînement |

---

## 8. Journal des reclassements

| Date | Mouvement | Motif |
|---|---|---|
| 2026-08-16 | Création — 23 opportunités actives, 8 écartées | Consolidation par cible d'exécution |
| 2026-08-16 | OPP-032 (GSIE-Bench) placée au rang 1 | Six opportunités du registre en dépendent ; sans banc, tout choix de modèle est une opinion |
| 2026-08-16 | OPP-106 (Voxtral, cohere) versée depuis le registre mobile | Écartée du terrain pour gabarit, elle a sa place ici |
| 2026-08-16 | OPP-037 (patron OTP) séparée de OPP-115 (Elixir) | Le patron est transposable ; le langage est écarté par DEC-000019 |

---

## 9. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 1.0.0 | 2026-08-16 | Claude | Création — registre par cible d'exécution |
