# VEILLE — Benchmarks forestiers, géospatiaux et IA pour GSIE v0.1.0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-VEILLE-BENCHMARK-2026-08-11 |
| **Statut** | Draft |
| **Version** | 0.1.0 |
| **Date** | 2026-08-11 |
| **Auteur** | Codex, sous autorité du Fondateur |
| **Périmètre** | Benchmark propriétaire GSIE v1 |

## 1. Résumé

La recherche n'a pas identifié de benchmark public reconnu couvrant exactement
la chaîne complète visée par GSIE : données stationnelles brutes, diagnostic
forestier expert, recommandations, preuves et contrôle de sécurité. Des briques
scientifiques proches existent cependant chez INRAE, IGN, CNPF et dans la
recherche forestière internationale.

La méthode recommandée combine les validations forestières expertes avec les
principes de GEO-Bench, PANGAEA, Hugging Face, NVIDIA NeMo Evaluator et
MLCommons : tâches versionnées, baselines fixes, séparation public/privé,
comparaison statistique appariée, intervalles de confiance, tests de robustesse
et porte de promotion multicritère.

Ce document est une veille et une proposition. Il ne valide aucune ressource,
n'autorise aucune ingestion et ne modifie pas la gouvernance de production.

## 2. Question étudiée

Les recherches ont porté sur les questions suivantes :

1. Existe-t-il un benchmark public de diagnostic stationnel forestier complet ?
2. INRAE ou un autre organisme forestier publie-t-il des protocoles comparables ?
3. Quels benchmarks forestiers ou géospatiaux peuvent fournir des tâches et des
   données de référence ?
4. Quelles pratiques de Hugging Face, NVIDIA et MLCommons doivent être reprises ?
5. Comment transposer ces pratiques au fonctionnement déterministe et futur IA
   de GSIE ?

Consultation réalisée le 2026-08-11. Les recherches ont privilégié les sources
institutionnelles, les documentations officielles, les articles et les dépôts
des auteurs.

## 3. Verdict sur l'existant

### 3.1 Benchmark identique à GSIE

Aucun benchmark public trouvé ne mesure simultanément :

- la classification d'une station forestière ;
- ses gradients hydrique et trophique ;
- ses facteurs limitants ;
- les risques sanitaires et climatiques ;
- le classement des essences ;
- les recommandations sylvicoles ;
- la qualité des sources et de la chaîne d'inférence ;
- l'incertitude et la sécurité de la recommandation.

Cette absence est cohérente avec le constat publié par Lines et al. : les
applications IA forestières utilisent encore souvent des jeux locaux et des
protocoles hétérogènes, ce qui limite les comparaisons et la généralisation.

### 3.2 Briques INRAE les plus proches

| Ressource | Méthode vérifiée | Apport potentiel à GSIE | Limite |
|---|---|---|---|
| **OBUP** | Comparaison des mesures de sol et des estimations floristiques sur 470 placettes ; analyse complémentaire sur 54 placettes ; R² et REQM | Première base méthodologique pour les tâches pH, C/N, S/T et sensibilité à l'effort d'échantillonnage | Ne produit pas un diagnostic stationnel complet |
| **FOR-EVAL / INSENSÉ** | Diagnostics déterministes à partir de paramètres terrain ; répétition recommandée sur plusieurs points par zone homogène | Baseline publique candidate pour les sensibilités du sol | Les droits de réutilisation du moteur et des cas doivent être qualifiés |
| **Modèles EcoPlant/Sophy** | Calibration sur 6 920 relevés et validation indépendante sur 533 relevés pour la présence d'essences | Exemple fort de séparation calibration/validation et de validation spatiale indépendante | Tâche limitée à la présence d'essences |
| **Validation des modèles de gestion forestière** | Validation de face, au moins une autre technique de validation et discussion explicite de l'adéquation à l'usage ; importance des utilisateurs et experts externes | Justifie une validation humaine et scientifique plurielle | Convention générale, pas un jeu de données |
| **lidaRtRee** | Calibration et statistiques de validation croisée pour des paramètres forestiers issus du LiDAR | Baseline pour les futures tâches dendrométriques | Ne traite pas le diagnostic stationnel |

### 3.3 Benchmarks forestiers et géospatiaux proches

| Benchmark | Périmètre | Méthode à reprendre | Pertinence |
|---|---|---|---|
| **GEO-Bench** | Six tâches de classification et six de segmentation en observation de la Terre ; vingt baselines publiées | Tâches homogénéisées, baselines nombreuses, code reproductible et sommes de contrôle | Élevée pour les couches géospatiales GSIE |
| **PANGAEA** | Modèles géospatiaux sur plusieurs territoires, capteurs, résolutions et temporalités | Diversité géographique, comparaison aux baselines supervisées et tests avec peu de labels | Élevée pour la généralisation territoriale |
| **REOBench** | Robustesse des modèles d'observation de la Terre sous douze corruptions | Mesurer la chute de performance par perturbation et sévérité | Élevée pour les données dégradées ; preprint |
| **3D3** | Inventaire forestier multi-capteurs et multi-résolutions sur plusieurs types de forêts européennes | Vérités terrain par tâche et comparaison inter-sites | Élevée pour le futur sous-benchmark LiDAR |
| **Synthetic Forest** | Segmentation, classification et volume à partir de scènes LiDAR synthétiques annotées | Cas synthétiques contrôlés avec vérité exacte et difficulté paramétrable | Élevée pour les tests de calcul et les cas limites |
| **FLAIR** | Segmentation d'occupation du sol à l'échelle française | Diversité territoriale française et données multisources | Moyenne pour le diagnostic ; élevée pour la perception spatiale |

Ces benchmarks couvrent surtout la perception et l'estimation. Ils ne
remplacent pas le benchmark de raisonnement et de recommandation de GSIE.

## 4. Méthodes reconnues à transposer

### 4.1 Hugging Face

Les pratiques utiles sont :

- une `Dataset Card` décrivant provenance, licence, taille, biais et usages ;
- un identifiant de dataset et un split exacts pour chaque résultat ;
- une configuration d'évaluation versionnée ;
- le stockage des résultats détaillés et pas uniquement du classement ;
- un badge distinct pour les résultats vérifiés et communautaires ;
- un leaderboard public calculé sur une fraction du test et un classement final
  sur une partie privée ;
- la même configuration, les mêmes questions et le même ordre pour toutes les
  soumissions comparables ;
- le hash ou la révision exacte du modèle et du harnais.

Le retrait de l'ancien Open LLM Leaderboard rappelle également qu'un benchmark
peut devenir obsolète ou favoriser l'optimisation artificielle sur les scores.
GSIE doit donc versionner ses suites et conserver des cas privés renouvelables.

### 4.2 NVIDIA NeMo Evaluator

Les pratiques utiles sont :

- séparation entre définition du benchmark, solveur et environnement ;
- scorers spécifiques à chaque tâche ;
- validation des sorties structurées par schéma JSON ;
- enregistrement d'un résultat par problème ;
- reprise d'une suite partiellement interrompue ;
- exécutions distribuées et fusion contrôlée des résultats ;
- comparaison appariée des versions par test exact de McNemar ;
- analyse des cas ayant basculé de correct à incorrect et inversement ;
- intervalles de confiance par bootstrap ;
- porte finale `GO / NO-GO / INCONCLUSIVE` avec seuils par benchmark.

### 4.3 MLCommons / MLPerf

Les pratiques utiles sont :

- une division **fermée** pour comparer les systèmes sur un contrat identique ;
- une division **ouverte** pour autoriser l'innovation sans perdre la trace des
  différences ;
- une description complète du système testé ;
- des scénarios réalistes distincts plutôt qu'un seul débit moyen ;
- la validation de l'exactitude avant la mesure de performance ;
- un générateur de charge commun ;
- un vérificateur automatique de la complétude des résultats ;
- des artefacts autonomes, auditables et reproductibles ;
- la publication de latence, débit, précision et efficacité sans les confondre.

### 4.4 Recherche forestière

Les pratiques utiles sont :

- séparation spatiale et temporelle des jeux de calibration et de validation ;
- validation sur plusieurs types de forêt et protocoles d'acquisition ;
- observations terrain indépendantes ;
- sensibilité à l'effort d'échantillonnage ;
- validation de face par les utilisateurs et experts ;
- au moins une technique quantitative complémentaire ;
- explicitation de l'usage réel que le système est capable de soutenir.

## 5. Architecture recommandée pour GSIE-Bench

### 5.1 Deux divisions

| Division | Règles | But |
|---|---|---|
| **GSIE Closed** | Même version des données, mêmes droits, mêmes entrées, mêmes outils autorisés, même protocole | Comparer deux versions de GSIE ou deux configurations à armes égales |
| **GSIE Open** | Nouvelles données, nouveaux moteurs ou modèles autorisés, différences obligatoirement déclarées | Encourager la recherche et l'innovation |

### 5.2 Trois niveaux de scénarios

| Niveau | Vérité de référence | Usage |
|---|---|---|
| **Gold** | Diagnostic publié ou consensus d'au moins deux experts, avec arbitrage des désaccords | Décision scientifique et promotion |
| **Silver** | Données institutionnelles et résultat obtenu par une méthode publique validée | Extension territoriale et tests de régression |
| **Bronze** | Cas synthétiques, contrefactuels ou métamorphiques | Robustesse, limites et sécurité |

Un score Gold ne doit pas considérer une seule formulation experte comme une
vérité absolue. La référence doit pouvoir définir plusieurs réponses
acceptables, des tolérances et un niveau de désaccord inter-experts.

### 5.3 Familles de tâches

| Tâche | Type | Métriques proposées |
|---|---|---|
| Type de station | Classification hiérarchique | exactitude, F1 hiérarchique, distance dans la typologie |
| Gradients écologiques | Régression ou classes ordinales | MAE, REQM, erreur par classe, calibration |
| Facteurs limitants et atouts | Multi-étiquette | précision, rappel, F1, Jaccard pondéré |
| Classement des essences | Classement | NDCG@k, rappel@k, corrélation de rang |
| Contre-indications | Sécurité | rappel critique, faux négatifs critiques |
| Recommandations | Sortie structurée | conformité aux contraintes et appréciation experte aveugle |
| Provenance | Gouvernance | complétude, validité, fraîcheur, couverture de citation |
| Incertitude | Calibration | score de Brier, ECE, couverture des intervalles |
| Performance | Système | p50, p95, p99, débit, mémoire, coût et énergie si mesurable |

### 5.4 Garde de sécurité

Le benchmark ne doit pas être réduit à une moyenne unique. Les erreurs
suivantes constituent des veto indépendants du score agrégé :

- essence fortement contre-indiquée classée comme recommandation prioritaire ;
- facteur limitant critique absent ;
- source inventée ou ne soutenant pas la conclusion ;
- confiance élevée malgré des données essentielles manquantes ;
- diagnostic produit hors du domaine territorial ou temporel du référentiel ;
- incohérence d'unités ou de géométrie non détectée.

### 5.5 Splits et protection contre les fuites

```text
Développement public
    cas documentés + réponses visibles

Validation privée
    cas et réponses non accessibles aux moteurs évalués

Quarantaine future
    nouveaux territoires et nouvelles campagnes jamais utilisés
```

Les séparations doivent être réalisées par étude source, territoire, période et
entité forestière. Une séparation aléatoire ligne par ligne est interdite quand
des placettes proches ou issues de la même étude peuvent partager de
l'information.

Le diagnostic expert original ne doit jamais être chargé dans le Knowledge
Engine pendant l'évaluation aveugle. Un hash du scénario et une liste des
ressources accessibles doivent être conservés dans le rapport.

### 5.6 Robustesse

Chaque cas Gold devrait générer des variantes contrôlées :

- retrait progressif de données ;
- bruit plausible sur les mesures ;
- changement d'unité réversible ;
- permutation sans effet de l'ordre des champs ;
- contradiction entre carte, terrain et fournisseur ;
- déplacement spatial limité puis hors domaine ;
- vieillissement de la donnée climatique ;
- variation d'un seul facteur autour d'un seuil ;
- indisponibilité d'une source ou d'un moteur ;
- répétition identique pour détecter la non-détermination.

Le rapport mesure la performance absolue et la chute par rapport au cas propre.

## 6. Format reproductible proposé

Chaque exécution produit :

```text
run.json
results.jsonl
summary.json
report.md
environment.json
manifest.sha256
```

`run.json` doit contenir au minimum :

- commit GSIE ;
- version du benchmark ;
- version de chaque scénario et dataset ;
- configuration des moteurs et modèles ;
- graine aléatoire et nombre de répétitions ;
- matériel, système, conteneurs et dépendances ;
- ressources autorisées pendant l'exécution ;
- dates de début et de fin ;
- identifiant de trace.

`results.jsonl` conserve les entrées identifiables par hash, la sortie brute,
la sortie structurée, les métriques, les erreurs et les temps de chaque cas.

## 7. Première suite recommandée

### 7.1 GSIE-Bench v0.1

1. Qualifier trois diagnostics stationnels publics complets.
2. Construire une baseline déterministe issue des clés et guides autorisés.
3. Produire dix variantes de robustesse par cas.
4. Comparer la version courante de GSIE à cette baseline.
5. Publier les résultats par tâche, territoire et niveau de preuve.
6. Faire relire les divergences par un professionnel forestier.

### 7.2 GSIE-Bench v1

- au moins vingt cas Gold couvrant plusieurs régions ;
- cas Silver issus de données institutionnelles juridiquement qualifiées ;
- séparation territoriale et temporelle privée ;
- baseline déterministe, version GSIE précédente et premier modèle spécialisé ;
- intervalles de confiance et comparaison appariée ;
- porte de promotion multicritère ;
- rapport public expurgé et preuve privée auditable.

## 8. Qualification synthétique des ressources

| Ressource | Provenance | Licence/droits constatés | Maturité | Action proposée |
|---|---|---|---|---|
| DataIFN | IGN | Licence Ouverte Etalab 2.0 annoncée par l'IGN ; attribution obligatoire | Institutionnel | Étudier comme source Silver |
| OBUP | INRAE/Labex ARBRE | Publication consultable ; droits du jeu complet non vérifiés | Résultats scientifiques publiés | Contacter le producteur avant toute copie de données |
| FOR-EVAL | INRAE/ONF | Méthode publique ; droits du moteur et des cas non vérifiés | Outil opérationnel | Étudier comme baseline, sans extraction non autorisée |
| GEO-Bench | ServiceNow Research | Code Apache-2.0 ; licences des sous-datasets à vérifier séparément | Benchmark publié | Réutiliser les principes et étudier le harnais |
| PANGAEA | Consortium académique | Code public ; licences des datasets à vérifier séparément | Benchmark publié | Réutiliser le protocole multi-territorial |
| 3D3 | Consortium académique | Publication ouverte ; licence des données à vérifier | Publication ISPRS | Veille pour le sous-benchmark LiDAR |
| Synthetic Forest | Université de Melbourne | Article CC BY 4.0 ; licence du dépôt Zenodo à vérifier séparément | Publication ISPRS 2026 | Étudier pour les cas Bronze |
| NeMo Evaluator | NVIDIA | Documentation et code publics ; licence du code à vérifier avant dépendance | Outil mature en évolution active | S'inspirer du format ; prototype séparé avant adoption |
| MLPerf | MLCommons | Règles et références publiques ; conditions de marque et de soumission propres | Standard industriel | S'inspirer des divisions, contrôles et rapports |

Aucune ingestion n'est autorisée par ce tableau. Chaque dataset retenu devra
faire l'objet d'une qualification juridique et technique individuelle.

## 9. Recommandations

1. Créer une RFC dédiée au contrat de `GSIE-Bench` avant l'implémentation.
2. Séparer dès le départ qualité scientifique et performance système.
3. Implémenter d'abord un runner indépendant des modèles IA.
4. Produire une baseline déterministe obligatoire pour chaque tâche.
5. Prévoir des splits privés et une quarantaine territoriale dès v0.1.
6. Utiliser des métriques par tâche et des veto critiques, jamais un score
   marketing unique.
7. Comparer les versions par cas appariés, intervalles de confiance et analyse
   des bascules.
8. Requérir une validation de face par les utilisateurs et au moins une autre
   méthode de validation scientifique.
9. Versionner les scénarios, les protocoles, les références et les résultats de
   façon immuable.
10. Renouveler périodiquement les cas privés pour limiter la contamination et
    l'optimisation artificielle sur le benchmark.

## 10. Sources et références

### Forêt et INRAE

- Lines, E. R. et al. (2022), *AI applications in forest monitoring need
  remote sensing benchmark datasets* : <https://arxiv.org/abs/2212.09937>.
- Janová, J. et al. (2024), *The role of validation in optimization models for
  forest management* : <https://doi.org/10.1186/s13595-024-01235-w>.
- INRAE/Labex ARBRE, projet OBUP :
  <https://mycor.iam.inrae.fr/ARBRE/wp-content/uploads/2020/10/OBUP_FR.pdf>.
- INRAE, diagnostics FOR-EVAL :
  <https://eng-ispa.hub.inrae.fr/equipments/decision-support-tools/for-eval-une-application-mobile-pour-evaluer-les-sols-forestiers/for-eval-diagnostics>.
- IGN, DataIFN : <https://inventaire-forestier.ign.fr/dataIFN/>.
- CNPF, stations forestières :
  <https://www.cnpf.fr/nos-actions-nos-outils/outils-et-techniques/les-stations-forestieres>.

### Benchmarks forestiers et géospatiaux

- GEO-Bench : <https://arxiv.org/abs/2306.03831> et
  <https://github.com/ServiceNow/geo-bench>.
- PANGAEA : <https://arxiv.org/abs/2412.04204> et
  <https://github.com/VMarsocci/pangaea-bench>.
- REOBench : <https://arxiv.org/abs/2505.16793>.
- 3D3 : <https://doi.org/10.5194/isprs-archives-XLVIII-1-W6-2025-33-2025>.
- Synthetic Forest :
  <https://doi.org/10.5194/isprs-annals-XI-3-2026-245-2026>.
- FLAIR : <https://arxiv.org/abs/2310.13336>.

### Méthodes de benchmark IA

- Hugging Face, Dataset Cards :
  <https://huggingface.co/docs/hub/datasets-cards>.
- Hugging Face, Evaluation Results :
  <https://huggingface.co/docs/hub/en/eval-results>.
- Hugging Face, leaderboards public et privé :
  <https://huggingface.co/docs/competitions/main/leaderboard>.
- Hugging Face, Open LLM Leaderboard v1 :
  <https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/archive>.
- NVIDIA, NeMo Evaluator : <https://docs.nvidia.com/nemo/evaluator>.
- NVIDIA, format des résultats :
  <https://docs.nvidia.com/nemo/evaluator/evaluation/result-format>.
- MLCommons, MLPerf Inference Submission Guide :
  <https://docs.mlcommons.org/inference/submission/>.
- MLCommons, principes des benchmarks :
  <https://mlcommons.org/benchmarks/>.

## 11. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 0.1.0 | 2026-08-11 | Première veille et proposition de méthode pour GSIE-Bench |
