# Vision long terme — LLM spécialisés, orchestrateur central et GSIE-Core

| Champ | Valeur |
|---|---|
| **Type** | Veille / vision stratégique long terme (non actionnable à ce stade) |
| **Date** | 2026-07-20 |
| **Origine** | Analyse conduite par le fondateur (Camille Perraudeau) via ChatGPT, versée telle quelle pour traçabilité |
| **Statut** | Matière première non validée scientifiquement — n'autorise aucune implémentation, ne crée aucun périmètre RFC |
| **Horizon** | Plusieurs années — postérieur à RFC-0019 (`gsie-ai-gateway`, périmètre P0 : un seul modèle externe + RAG) |
| **Documents liés** | `02_RFC/RFC-0017-veille-plantnet-nvidia-nim.md`, `02_RFC/RFC-0019-gsie-ai-gateway-nvidia-nim.md`, `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md` |

---

## 1. Évaluation d'une instance L40S 48 Go pour l'entraînement

- Bon pour LoRA/QLoRA sur modèles 7-14B (9/10) ; correct sur 30-32B
  avec optimisations (6/10) ; faible sur 70B (2/10) ; irréaliste pour
  préentraîner un LLM depuis zéro (0/10) ; peu adapté en serveur
  permanent, notamment si l'instance ne peut pas être mise en pause
  (4/10).
- Le L40S (48 Go ECC, FP8/BF16/FP16) est une vraie carte
  d'entraînement/inférence, largement supérieure au poste actuel du
  fondateur (RTX 3050 Laptop 4 Go).
- QLoRA réduit fortement la mémoire nécessaire (jusqu'à ~60 % selon la
  documentation NVIDIA citée) au prix d'un entraînement 50-200 % plus
  lent que LoRA classique.
- Coût indicatif à 1,06 $/h : 4h ≈ 4,24 $, 8h ≈ 8,48 $, 24h ≈ 25,44 $,
  100h ≈ 106 $, 30 jours continus ≈ 763,20 $.
- Risques opérationnels signalés sur ce type d'instance : préversion,
  pas de pause/reprise, disque fixe (~625 Gio), suppression possible
  avec toutes les données si les crédits s'épuisent → considérer tout
  stockage sur l'instance comme temporaire, sauvegarder
  systématiquement datasets/configs/métriques/adaptateurs en externe,
  et supprimer l'instance dès la fin d'une expérience.

## 2. Ce que « notre propre LLM » devrait signifier

Rejet explicite de l'idée d'un unique gros modèle GSIE entraîné depuis
zéro (trop coûteux, difficile à évaluer, probablement moins performant
qu'un modèle existant). Architecture proposée à la place :

```
Modèle fondation multilingue
        +
adaptateurs LoRA spécialisés
        +
RAG scientifique versionné
        +
outils GSIE déterministes
        +
évaluations scientifiques
        +
validation humaine
```

Adaptateurs LoRA envisagés, partageant un même modèle de base (NIM
peut servir plusieurs adaptateurs LoRA sur un modèle de base compatible
selon la doc NVIDIA citée) :

- `GSIE-Research` — recherche, comparaison des preuves et citations.
- `GeoSylva-Forest` — sylviculture, dendrométrie, autécologie.
- `Ignis-Operations` — analyse d'incidents, appels d'outils.
- `Hydro-Atmos` — explication de modèles et scénarios.
- `GSIE-Data` — extraction structurée depuis des documents.

### 2.1 Répartition des responsabilités (point le plus solide de l'analyse)

| Besoin | Meilleure solution |
|---|---|
| Connaissances scientifiques | RAG avec sources versionnées |
| Calculs dendrométriques | Moteurs déterministes |
| Routage et optimisation | cuOpt ou OR-Tools |
| Propagation incendie | Simulateur physique |
| Style et comportement expert | LoRA/SFT |
| Choix des outils | Fine-tuning supervisé |
| Sécurité | Guardrails + règles métier |
| Fiabilité mesurable | Benchmark indépendant |

Principe retenu comme non négociable si cette voie est un jour
poursuivie : le modèle appelle les moteurs GSIE pour calculer, puis
explique — il ne calcule jamais « de mémoire » un volume, une surface
terrière, un indice de risque ou une recommandation sylvicole. Cohérent
avec GSIE-CON-001 et avec le principe déjà posé dans RFC-0019 §4.

## 3. Stratégie d'entraînement proposée (si un jour engagée)

1. **`GSIE-Eval-FR` avant tout entraînement** — 200 à 500 cas de test
   forestiers validés par des professionnels (questions, cas
   sous-déterminés, contradictions entre guides, calculs nécessitant
   un outil, différences régionales, refus attendus, extraction de
   tableaux, vocabulaire terrain, citations exactes). Jamais dans les
   données d'entraînement ; séparé par documents/régions/périodes pour
   éviter les fuites. Déjà cohérent avec le jalon `GSIE-Eval-FR`
   mentionné en RFC-0019 §6.
2. **Choix d'un modèle de base 8-14B** — comparer un modèle 7-9B, un
   modèle 12-14B et une référence API, sur qualité française,
   utilisation d'outils, licence commerciale, compatibilité LoRA,
   servabilité NIM/vLLM, score sur `GSIE-Eval-FR`.
3. **Dataset petit et propre** — viser 1 000 à 5 000 exemples excellents
   plutôt que 100 000 exemples synthétiques incertains ; chaque exemple
   porte instruction, contexte, réponse attendue, références, niveau de
   preuve, domaine géographique, limites, appel d'outil éventuel,
   résultat déterministe, justification d'abstention.
4. **Entraînement LoRA** — modèle 8-14B, BF16 si la mémoire le permet,
   QLoRA seulement si nécessaire, contextes courts au départ,
   sauvegardes régulières, jeu de test jamais modifié.
5. **Évaluation comparative obligatoire** — base seul / base+RAG /
   base+LoRA / base+LoRA+RAG / base+LoRA+RAG+outils. Le LoRA n'est
   conservé que s'il améliore mesurablement sans dégrader les
   connaissances générales. Indicateurs : exactitude scientifique,
   précision des citations, taux d'affirmations non supportées,
   capacité d'abstention, choix correct des outils, conformité JSON,
   exactitude des entités forestières, robustesse aux contradictions,
   latence et coût.

### 3.1 Test minimal proposé avant tout engagement financier

Session de 4 à 8h (~4,24-8,48 $) : installer l'environnement, charger
un modèle 8-14B, lancer un LoRA sur 500-1 000 exemples, exécuter
`GSIE-Eval-FR`, sauvegarder l'adaptateur, supprimer l'instance. Si gain
mesurable → dataset plus grand. Sinon → améliorer les données plutôt
que payer plus de GPU.

## 4. Famille de modèles envisagée à terme

| Modèle | Taille cible | Fonction |
|---|---|---|
| GSIE Expert | 8-14B | Recherche, raisonnement, outils |
| GeoSylva Field | 3-7B | Extraction vocale, assistant terrain |
| Ignis Vision | Modèle vision spécialisé | Fumée, feu, drone, incidents |
| Hydro/Atmos | Modèles scientifiques | Prévisions et simulations |
| Embed/Rerank | ~1B | Recherche documentaire |

Piste : le modèle terrain pourrait être distillé/quantifié pour
tourner localement ou sur une passerelle Jetson, l'app Android
conservant ses données et calculs déterministes hors ligne (cohérent
avec l'exigence offline-first de GeoSylva, RFC-0003).

## 5. Orchestrateur central — architecture multi-niveaux

Rôle proposé pour un futur modèle central : comprendre la demande, la
décomposer, choisir les spécialistes, leur transmettre le contexte
nécessaire, comparer leurs résultats, détecter les contradictions,
solliciter les moteurs déterministes, produire une synthèse sourcée
avec incertitude. Il ne calcule jamais lui-même une propagation de
feu, une surface terrière ou une prévision hydrologique.

Routage à trois niveaux proposé :

| Niveau | Traitement |
|---|---|
| Simple | Règle, recherche ou petit modèle |
| Professionnel | Spécialiste 7-14B + RAG |
| Complexe | Orchestrateur central + plusieurs spécialistes |

### 5.1 Danger explicitement identifié (multi-agents)

Faire dialoguer plusieurs modèles n'améliore pas automatiquement la
vérité : risque de répétition d'erreur, influence mutuelle, consensus
halluciné, surconsommation de tokens, perte de provenance, boucles sans
conclusion. D'où l'exigence d'un **protocole structuré** entre modèles
(claim / evidence / method / confidence / validity_scope /
uncertainties / recommended_next_tool en JSON), jamais de conversation
libre entre agents.

## 6. GSIE-Core — un modèle natif pour GSIE lui-même

Proposition d'un modèle transversal (`GSIE-Core`) entraîné pour
comprendre le métamodèle et l'ontologie GSIE, les entités
(Resource/Assertion/Evidence/Observation/Scenario/Recommendation), les
relations entre domaines (forêt/eau/atmosphère/sol/biodiversité/
incendie), les niveaux de preuve, la provenance, les protocoles de
validation, les moteurs/outils disponibles, les contraintes de
sécurité, les formats d'échange.

Rôle : transformer une demande en **plan scientifique traçable**, pas
mémoriser toute la science.

### 6.1 Ce que GSIE-Core ne devrait jamais faire seul

Inventer une donnée manquante ; réaliser mentalement des calculs
scientifiques critiques ; transformer une hypothèse en connaissance
validée ; déclencher une alerte opérationnelle ; prescrire une
intervention sylvicole ; commander des moyens d'urgence ; modifier une
preuve ou une observation originale ; attribuer son propre niveau de
confiance sans méthode définie. Chaque action importante doit passer
par un moteur déterministe, une règle métier ou une validation
humaine — directement aligné avec GSIE-CON-001.

### 6.2 Protocole structuré proposé (exemple)

```json
{
  "objective": "Évaluer la résilience forestière de la parcelle 42",
  "required_domains": ["forestry", "climate", "soil", "hydrology"],
  "tools": ["parcel_context", "climate_projection", "species_autecology", "water_balance"],
  "constraints": {
    "territory": "parcel-42",
    "horizon": "2050",
    "evidence_minimum": "B",
    "human_validation_required": true
  },
  "expected_output": {
    "type": "scenario_comparison",
    "citations_required": true,
    "uncertainties_required": true
  }
}
```

### 6.3 Emplacement architectural proposé

`GSIE-Core` comme service séparé, aux côtés de `gsie-ai-gateway`,
`gsie-tool-registry`, `gsie-model-registry`, `gsie-evaluation`,
`gsie-knowledge`, `gsie-validation` — jamais intégré directement dans
PostgreSQL ni dans chaque application cliente. Les applications
(GeoSylva, Ignis, Hub) interrogent GSIE, qui décide du modèle à
utiliser. Le registre de modèles (déjà posé par RFC-0015 —
`ModelRegistry`) conserverait pour chaque modèle : base, version,
licence, empreinte du checkpoint, adaptateur LoRA, dataset
d'entraînement, résultats d'évaluation, capacités autorisées, domaines
interdits, date de validation, état expérimental/production.

### 6.4 Génération par génération (horizon indicatif, non engagé)

1. Modèle externe performant derrière `gsie-ai-gateway`, prompt
   système + RAG + outils + sorties JSON — **c'est le périmètre déjà
   posé par RFC-0019 §6, aucune nouveauté ici.**
2. Modèle ouvert 8-14B + adaptateur `GSIE-Core-LoRA` (métamodèle,
   appels d'outils, niveaux de preuve, analyse de contradictions,
   génération de plans, règles d'abstention).
3. Modèle GSIE 30-70B spécialisé dans l'orchestration
   multidisciplinaire, supervisant les petits modèles.
4. Distillation de GSIE-Core vers plusieurs versions (serveur complète,
   intermédiaire collectivités, compacte terrain, embarquée Jetson,
   très légère GeoSylva hors ligne).

## 7. Principes retenus comme non négociables si cette vision est un jour poursuivie

1. Le modèle central coordonne, **GSIE gouverne** — cohérent avec
   GSIE-CON-000 (primauté) et GSIE-CON-001.
2. Les connaissances restent dans le RAG et le graphe, jamais
   uniquement dans les poids d'un modèle.
3. Les calculs restent dans des moteurs scientifiques vérifiables,
   jamais « de mémoire » par un LLM.
4. Chaque spécialiste doit produire des preuves structurées (JSON
   typé), pas une opinion en texte libre.

## 8. Ce que ce document n'est pas

- Ce n'est pas un RFC, ni une décision, ni une autorisation
  d'implémentation.
- Il ne modifie pas le périmètre de RFC-0019 (`gsie-ai-gateway`), qui
  reste volontairement limité à un seul modèle externe + RAG
  scientifique en P0.
- Aucune donnée scientifique ci-dessus n'est sourcée au niveau exigé
  par GSIE-CON-005 — c'est une vision d'architecture, pas une
  connaissance validée.
- À rouvrir formellement (RFC dédié) seulement quand RFC-0019 aura
  démontré son socle en usage réel et que les moyens (financiers,
  matériels) le justifieront.
