# VEILLE — Modèles IA et pistes R&D pour GSIE v0.1.0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-VEILLE-LLM-RD-2026-08-12 |
| **Statut** | Draft |
| **Version** | 0.1.0 |
| **Date** | 2026-08-12 |
| **Auteur** | Codex, sous autorité du Fondateur |
| **Périmètre** | Normalisation Data Registry, IA spécialisée et R&D Quintessences |

## 1. Objet et niveau de confiance

Cette veille consolide des informations issues d'échanges de recherche et de
vérifications ciblées. Elle ne transforme aucune affirmation de modèle, de
licence, de quota, de financement ou de performance en vérité de production.

Les éléments sont classés ainsi :

- **Vérifié** : fiche officielle ou documentation primaire consultée ;
- **Candidat** : piste techniquement intéressante, à mesurer dans GSIE-Bench ;
- **À revalider** : nom, licence, disponibilité, quota, performance ou éligibilité
  insuffisamment établis ;
- **R&D** : idée de recherche sans autorisation d'implémentation ou d'ingestion.

Aucune donnée confidentielle, donnée client, source `citation_only` ou document
sous droits non qualifiés ne doit être envoyé à une API externe ou utilisé pour
un entraînement.

## 2. Architecture cible pour la normalisation GSIE

Le modèle ne doit pas remplacer les transformations déterministes :

```text
Profilage déterministe
    ↓
Extraction spécialisée
    ↓
Recherche sémantique de candidats
    ↓
Reranking
    ↓
LLM uniquement pour les ambiguïtés
    ↓
Validation GSIE
    ↓
Proposition de normalisation avec provenance
```

Les conversions de CRS, coordonnées, dates, unités, géométries, types
numériques, bornes physiques et checksums restent exécutées et vérifiées par du
code déterministe. Le modèle produit une proposition, jamais une écriture
immédiate dans PostgreSQL/PostGIS.

La sortie minimale proposée est :

```json
{
  "raw_value": "t2m",
  "normalized_value": "air_temperature_2m",
  "canonical_id": "gsie:meteorology.air_temperature_2m",
  "mapping_type": "semantic_match",
  "confidence": 0.94,
  "evidence": "Documentation source, section 3",
  "transform_id": "convert_kelvin_to_celsius",
  "source_dataset_id": "dataset_001",
  "model_id": "model-candidate",
  "model_version": "0.1.0",
  "prompt_version": "gsie-normalizer-v1",
  "review_status": "pending_validation"
}
```

Un modèle doit pouvoir refuser : colonne inconnue, unité ambiguë, CRS absent,
donnée contradictoire ou information insuffisante.

## 3. Candidats pour la normalisation et l'extraction

| Modèle ou famille | Usage GSIE | État | Réserve |
|---|---|---|---|
| **GLiNER2 Multi** | Entités, classification, extraction structurée et relations | Vérifié comme candidat | Valider le français et les vocabulaires forestiers sur GSIE-Norm-Bench |
| **Qwen3-Embedding-0.6B** | Recherche sémantique de colonnes, unités, taxons et concepts | Vérifié comme candidat | Les scores éditeur ne remplacent pas le benchmark GSIE |
| **Qwen3-Reranker-0.6B** | Reclassement des correspondances candidates | Vérifié comme candidat | Mesurer le gain réel par rapport à une recherche vectorielle seule |
| **Table Transformer** | Détection de tableaux, lignes, colonnes et cellules PDF | Candidat | Ne comprend pas seul la sémantique scientifique des colonnes |
| **Qwen3-0.6B** | Génération courte de JSON pour cas ambigus | Candidat à tester | Validation stricte JSON Schema et refus des inventions |
| **NuExtract3** | Extraction structurée de documents, images et tableaux | Vérifié comme candidat documentaire | Trop lourd pour un fine-tuning confortable sur la machine locale ; droits des documents à contrôler |
| **mDeBERTa / XLM-R** | Classification de colonnes, unités, dates, entités et taxonomies | Candidats | Comparer à GLiNER2 sur des annotations GSIE |
| **Gemma 4 E2B/E4B** | Documents multimodaux et génération structurée | Vérifié comme famille existante ; candidat | Conditions de licence Google à qualifier avant usage commercial |

GLiNER2 est particulièrement intéressant pour un premier prototype local : sa
fiche officielle le décrit comme un modèle multi-tâche d'environ 205 M de
paramètres, orienté extraction structurée et exécution CPU.

Qwen3-Embedding-0.6B et Qwen3-Reranker-0.6B sont documentés par Qwen comme des
modèles de recherche et de classement multilingues. Ils devront néanmoins être
évalués avec des données françaises, forestières, pédologiques et climatiques
réelles mais juridiquement utilisables.

## 4. Modèles pour d'autres tâches — à ne pas confondre avec la normalisation

| Famille | Domaine | Position GSIE |
|---|---|---|
| **Prithvi-EO** | Télédétection et enrichissement géospatial | Sous-benchmark GeoAI, pas normaliseur de colonnes |
| **Chronos-Bolt / TimesFM** | Séries temporelles météo, capteurs et hydrologie | Sous-benchmark séries temporelles |
| **Nemotron multimodal / OCR** | Documents, images, audio et vidéo | R&D documentaire ou multimodale sur infrastructure adaptée |
| **Qwen3-14B/30B, Ministral, Granite** | Raisonnement ou normalisation complexe | Candidats partenaires, à comparer après benchmark |

Ces familles peuvent enrichir GSIE, mais elles ne doivent pas être intégrées au
normaliseur sans contrat de tâche séparé.

## 5. Nemotron et NVIDIA NIM

### 5.1 Nemotron 3.5 Lightning

La fiche officielle consultée décrit Nemotron 3.5 Lightning comme un modèle MoE
de 30 B de paramètres totaux et environ 3 B actifs par token. Cette propriété
réduit le coût de calcul par token, mais ne signifie pas que les poids tiennent
dans la mémoire d'un modèle 3 B.

La fiche de référence BF16 indique un déploiement de classe A100/H100. Une version
GGUF ou quantifiée peut être expérimentée avec Ollama, mais une RTX 3050 avec
environ 4 Gio de VRAM et 32 Gio de RAM ne constitue pas une cible confortable ou
validée. Le test local devra mesurer mémoire, vitesse, contexte et stabilité ;
il ne doit pas être présenté comme une capacité garantie.

**Position :** expérimentation locale possible, modèle principal GSIE non retenu
à ce stade, fine-tuning local non recommandé.

### 5.2 NVIDIA NIM

NIM est une couche de déploiement et de service, pas un modèle. Les endpoints
hébergés gratuits du programme développeur sont destinés au prototypage, à la
recherche, au développement et aux tests. Les conditions de production, de
rétention, de quotas, de sécurité et de licence doivent être vérifiées pour
chaque offre.

NIM peut servir à :

- comparer des modèles ;
- prototyper un AI Gateway ;
- tester un modèle sur des données publiques ;
- évaluer une future infrastructure partenaire.

NIM gratuit ne doit pas devenir le moteur de production de GSIE ni recevoir des
données sensibles sans qualification contractuelle et juridique.

### 5.3 Embeddings NIM

Les variantes Nemotron d'embedding ou de reranking citées dans la veille sont
conservées comme candidats à vérifier dans le catalogue officiel. Aucun nom de
modèle, quota, licence ou latence n'est considéré comme acquis sans fiche
primaire et mesure GSIE.

## 6. Faisabilité selon le matériel

### Machine locale actuelle — RTX 3050 Laptop, environ 4 Gio VRAM, 32 Gio RAM

Priorité recommandée :

```text
GLiNER2 Multi
    ↓
Qwen3-Embedding-0.6B
    ↓
Qwen3-Reranker-0.6B
    ↓
Règles déterministes GSIE
```

Un petit modèle génératif quantifié peut être ajouté pour les ambiguïtés. Le
fine-tuning QLoRA de modèles de plusieurs milliards de paramètres est considéré
comme très contraint sur cette machine : les estimations minimales publiées ne
comprennent pas toujours les activations, le contexte, l'optimiseur, Windows et
la marge mémoire.

### Infrastructure partenaire — 8 à 16 Gio VRAM

Candidats à comparer sur le même benchmark :

- Qwen3-4B ;
- Ministral 3B ;
- Granite 3B/4.1 3B ;
- Gemma 4 E2B/E4B ;
- NuExtract3 pour les documents.

Les noms, licences et versions exacts devront être revérifiés au moment de
l'achat ou du partenariat.

### Infrastructure 24 Gio et plus

Peuvent devenir réalistes :

- Qwen3-8B/14B ;
- modèles documentaires 4B et plus ;
- Prithvi de taille supérieure ;
- fine-tuning QLoRA avec marge opérationnelle ;
- serveur d'embeddings et de reranking dédié.

### Infrastructure 48 Gio et plus

Peuvent être étudiés :

- modèles 14B et 30B ;
- multimodalité plus lourde ;
- NIM auto-hébergé ;
- batch de normalisation important ;
- fine-tuning et distillation avec jeux GSIE qualifiés.

Aucun palier matériel ne constitue une promesse de performance : chaque choix
sera mesuré dans GSIE-Bench.

## 7. GSIE-Norm-Bench

GSIE-Bench évalue les diagnostics et recommandations. La normalisation doit
posséder un sous-benchmark ou une suite complémentaire dédiée :

```text
GSIE-Norm-Bench v0.1
```

Le contrat devra mesurer :

- validité du JSON et du schéma ;
- exactitude du mapping de colonnes ;
- rappel Top-k des candidats ;
- exactitude des unités ;
- exactitude des CRS et dates ;
- complétude de provenance ;
- abstention correcte ;
- taux d'invention ;
- robustesse aux valeurs manquantes et contradictoires ;
- latence, mémoire et coût ;
- reproductibilité.

La première suite doit utiliser des données publiques ou produites
artificiellement avec des droits clairs. Les articles `citation_only`, les PDF
sous copyright et les données clientes ne doivent pas servir de corpus
d'entraînement ou d'évaluation redistribuable.

Le pipeline comparera au minimum :

```text
Règles déterministes
    vs GLiNER2
    vs Embedding seul
    vs Embedding + Reranker
    vs petit LLM structuré
```

Aucune intégration IA ne doit être lancée avant l'adoption de RFC-0039 /
DEC-000067 et la définition du contrat de cette suite.

## 8. Pistes de R&D environnementale

Les propositions suivantes sont conservées comme pistes, sans validation ni
implémentation :

| Piste | Domaine | Intérêt | État |
|---|---|---|---|
| Reconstruction thermique sous couvert | IGNIS | Détection de points chauds masqués par la végétation, fusion drone/IA/simulation | À sourcer et reproduire |
| HYDRA2DGPU | Hydro | Solveur hydraulique GPU potentiel dans l'écosystème QGIS | À tester sur un petit MNT ; ne pas créer de dépendance |
| Plugins IGN QGIS récents | GeoSylva / Atlas | Inspiration UX pour profil altimétrique et couches favorites | Veille fonctionnelle |
| Meshtastic Build-Off | Mesh / capteurs | Répéteurs solaires, gateways, autonomie et boîtiers | Analyser les projets publics après la période d'évaluation |
| GeoAI local/on-premise | GIS / multi-moteurs | Segmentation, super-résolution, occupation du sol et espèces invasives | Piste stratégique à benchmarker |

Les chiffres de performance, dates de publication et disponibilités ne seront
retenus comme faits qu'après vérification des publications, dépôts ou pages
officielles correspondantes.

## 9. Opportunités de financement — pistes non qualifiées

Les éléments suivants sont enregistrés comme pistes de recherche, pas comme
éligibilités acquises :

| Opportunité | Usage envisagé | État |
|---|---|---|
| Trophées Innovation Design — jumeaux numériques / IA | Démonstrateur GSIE/IGNIS | Date et éligibilité à confirmer officiellement |
| R&D Start-up Nouvelle-Aquitaine | Programme R&D GSIE, GeoSylva, IA et capteurs | À qualifier selon statut juridique |
| PIIEC Intelligence artificielle — France 2030 | IA industrielle, edge/cloud et souveraineté | Consortium et critères à vérifier |
| ADEME « Mandat + Durable » | Pilote territorial avec un EPCI partenaire | Candidature directe de Quintessences non présumée |
| Horizon Europe — société résiliente | IGNIS, risques naturels, drones et jumeau numérique | Consortium européen à identifier |

Aucune candidature, dépense, partenariat ou annonce publique ne découle de cette
section. Les dates limites et conditions devront être relues sur les pages
institutionnelles au moment de l'action.

## 10. Règles de gouvernance R&D

- Une piste de veille ne devient pas une ressource validée sans ingestion et
  qualification prévues par la gouvernance.
- Une licence de modèle doit être vérifiée séparément de la licence des données
  d'entraînement et des données GSIE.
- Un modèle ne contacte jamais directement les fournisseurs ; il consomme les
  sorties versionnées du Data Registry.
- Un modèle ne modifie jamais directement PostgreSQL/PostGIS et ne déclenche
  aucune promotion.
- Toute sortie IA porte modèle, version, schéma de features, datasets, confiance,
  incertitude, preuves et `trace_id`.
- Le benchmark, la baseline, les seuils, le jeu d'évaluation et le rollback
  doivent précéder toute intégration de production.
- Les APIs gratuites sont des outils d'essai : données envoyées, quotas,
  rétention et conditions de production doivent être documentés.

## 11. Sources principales

- NVIDIA Nemotron 3.5 Lightning :
  <https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16>
- NVIDIA NIM et programme développeur :
  <https://docs.api.nvidia.com/nim/docs/product>
- NVIDIA NIM Anywhere :
  <https://docs.api.nvidia.com/nim/docs/run-anywhere>
- Ollama — catalogue Nemotron : <https://ollama.com/library>
- Qwen3 Embedding 0.6B :
  <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>
- Qwen3 Reranker 0.6B :
  <https://huggingface.co/Qwen/Qwen3-Reranker-0.6B>
- GLiNER2 Multi : <https://huggingface.co/fastino/gliner2-multi-v1>
- NuExtract3 : <https://huggingface.co/numind/NuExtract3>
- Gemma 4 E4B-it : <https://huggingface.co/google/gemma-4-E4B-it>
- RFC-0039 — GSIE-Bench v0.1 ;
- `GSIE/ARCHITECTURE/GSIE_EVOLUTION_AND_AI_INTEGRATION.md` ;
- `GSIE/API/docs/data/GSIE_DATA_QUALITY_FETCH_PHASE_2026-08-10.md`.

Les pistes forestières, géospatiales, mesh et financières mentionnées dans la
source de cette veille restent à qualifier à partir de leurs publications ou
pages institutionnelles primaires avant toute action.

## 12. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 0.1.0 | 2026-08-12 | Consolidation critique des candidats LLM et des pistes R&D futures. |
