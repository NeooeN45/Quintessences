# RFC-0034 — IA forestière on-device et multi-tier

| Champ | Valeur |
|---|---|
| **ID** | RFC-0034 |
| **Statut** | Adopté (2026-08-03, DEC-000050) |
| **Auteur** | Direction technique (assistée par Devin CLI, GLM-5.2 High) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000050 |
| **Périmètre** | LLM on-device (T1), edge (T2), serveur (T3) pour GeoSylva ; RAG scientifique ; identification essence ; assistant vocal |
| **Motivation** | Spécifier l'architecture IA forestière opérationnelle pour GeoSylva 3.0 en consolidant les visions existantes sans les réinventer |

## 1. Problème

GeoSylva 3.0 (GEOSYLVA-003 §15) introduit un assistant IA forestier
multi-tier. Trois documents de vision existent :
`VOLUME_CALCULATION_NEXT_GEN.md` §10 (multi-tier LLM),
`RESEARCH_OPPORTUNITIES.md` §3 (stack IA séquencée),
`VISION_LLM_SPECIALISES_GSIE_CORE` (adaptateurs LoRA, famille de modèles).
`RFC-0019` pose `gsie-ai-gateway` serveur. Mais aucun document n'arrête
les choix opérationnels : quel modèle T1, quel runtime, quel format RAG
local, quelle stratégie de quantification, quel banc d'évaluation, quelles
garanties RGPD pour l'audio.

Sans RFC, l'implémentation serait ad hoc, non reproductible, et risquerait
de violer ADR-009 (sortie LLM non citée) et le principe offline-first.

## 2. Solution proposée

### 2.1 Architecture multi-tier

Consolidée depuis GEOSYLVA-003 §15.2 :

| Tier | Modèle cible | Runtime | Réseau | Latence | Rôle |
|---|---|---|---|---|---|
| **T1 Mobile** | SmolLM3 3B (INT4) ou Phi-3-mini 4B | ONNX Runtime / llama.cpp Android | Aucun | < 500 ms | Assistance vocale, explication, identification essence |
| **T2 Edge** | Mistral 7B (AWQ 4-bit) | vLLM / NIM sur Jetson Orin | Wi-Fi local | < 3 s | RAG local, raisonnement intermédiaire |
| **T3 Serveur** | Mistral 7B servé (puis Phi-4-reasoning 14B quand dédifféré) | vLLM sur GPU serveur (RFC-0019) | 4G/Wi-Fi | < 10 s | Raisonnement profond via moteurs GSIE, RAG scientifique |

**T1 est la priorité** : c'est le seul tier qui fonctionne en forêt sans
réseau. T2 et T3 sont des amplificateurs optionnels.

### 2.2 Choix du modèle T1

| Critère | SmolLM3 3B | Phi-3-mini 4B | Llama 3.2 3B |
|---|---|---|---|
| Taille quantifié INT4 | ~1.6 GB | ~2.1 GB | ~1.6 GB |
| Licence | Apache 2.0 | MIT | Llama 3.2 Community |
| Français | Bon | Bon | Bon |
| Reasoning | Moyen | Bon | Moyen |
| Mise à jour | Active (Hugging Face) | Active (Microsoft) | Active (Meta) |
| **Choix** | **Cible P5** | Alternative | Étude |

**Justification SmolLM3 3B** : licence Apache 2.0 (pas de restriction
commerciale), taille la plus compacte, français suffisant pour assistance
vocale terrain, mise à jour active. Phi-3-mini est l'alternative si le
reasoning T1 s'avère insuffisant en tests.

### 2.3 Runtime T1

| Runtime | Avantages | Inconvénients | Statut |
|---|---|---|---|
| **ONNX Runtime** | Portabilité CPU/GPU/NPU, API Android stable, support INT4 | Pas de generation longue native (workaround) | Cible P5 |
| **llama.cpp Android** | Generation native, GGUF quantized, communauté active | Moins stable que ONNX, build NDK requis | Étude |
| **MLC LLM** | Très rapide sur GPU mobile, TVM | Maturité Android à valider | Étude |

**Choix** : ONNX Runtime en première tranche (stabilité, portabilité).
llama.cpp en étude parallèle si la génération longue (> 200 tokens) est
nécessaire pour l'explication des calculs.

### 2.4 RAG local T1 (offline)

**Index embarqué** :

- Format : SQLite-vec (extension SQLite vectorielle) ou FAISS mobile
- Taille cible : < 200 MB (sous-set des documents les plus pertinents)
- Contenu : guides martelage ONF, autécologie essences locales (Botanical
  Engine cache), fiches méthodes §7.2
- Mise à jour : via packs de données (§9 GEOSYLVA-003), pas en temps réel

**Pipeline RAG T1** :

```text
Question forestier
    │
    ▼
Embedding question (MiniLM-L6 v2, ONNX, < 25 MB)
    │
    ▼
Recherche top-k dans index local (cosine similarity)
    │
    ▼
Prompt = question + contextes récupérés + contraintes ADR-009
    │
    ▼
SmolLM3 3B (génération < 500 ms)
    │
    ▼
Réponse + citations (source_reference obligatoire)
```

**Garde-fou** : si aucune citation n'est produite, la réponse est marquée
« sans source — à vérifier » et n'alimente aucune recommandation.

### 2.5 RAG serveur T3 (online)

Conforme à RFC-0019 (`gsie-ai-gateway`) :

- `pgvector` déjà activé (migration 20260731_0024)
- Routes : `/ai/embed` (indexation), `/ai/rerank` (re-ranking),
  `/ai/research` (RAG avec citations exactes)
- Sources : ONF, CNPF, INRAE, IGN, `GSIE/KNOWLEDGE/`, `GSIE/RESEARCH/`
- Garde-fou : PostgreSQL = vérité canonique, LLM = assistant

### 2.6 Cascade T1 → T2 → T3

**Règles** (consolidées depuis GEOSYLVA-003 §15.3) :

1. T1 répond seul si la question est dans le périmètre des calculs locaux
   et connaissances cachées. Aucune donnée envoyée au serveur.
2. T1 délègue à T2/T3 uniquement pour raisonnement profond. Délégation
   **explicite et tracée** dans la session de martelage.
3. T3 appelle les moteurs GSIE (RFC-0033) et renvoie une conclusion
   **expliquée avec chaîne d'inférence** — jamais un verdict brut.
4. Le LLM ne produit jamais une valeur numérique forestière de lui-même.
5. Le forestier voit la cascade : badge « réponse locale / edge / serveur ».

**Format de délégation** (tracé en session) :

```json
{
  "delegation_id": "uuid-v4",
  "session_id": "uuid-v4",
  "tier_source": "T1 | T2 | T3",
  "prompt_envoye": "string (hashé pour RGPD si sensible)",
  "moteur_invoque": "correlation | reasoning | diagnostic | ...",
  "resultat_id_recu": "uuid-v5",
  "latence_ms": 3200,
  "date": "ISO 8601"
}
```

### 2.7 Identification essence on-device

Conforme à RFC-0018 (volet hors-ligne, à l'étude) :

- Modèle TFLite/ONNX, entraîné sur PureForest dataset IGN
- Classification ~50 essences françaises courantes (première tranche)
- Quantification INT8 (taille < 50 MB)
- Dégradation gracieuse : score < seuil → proposer Pl@ntNet au retour réseau
- Statut reste `SUGGESTION_IA`, jamais validation automatique

**Pipeline** :

```text
Photo capture (CameraX)
    │
    ▼
Prétraitement (resize 224x224, normalisation)
    │
    ▼
TFLite inference (PureForest model, < 100 ms)
    │
    ▼
Top-3 hypothèses + scores
    │
    ▼
Si score max < seuil (0.7) → marquer EN_ATTENTE_PLANTNET
    │
    ▼
Décision forestier (VALIDEE_UTILISATEUR | REJETEE)
```

### 2.8 Assistant vocal T1

Trois cas d'usage (GEOSYLVA-003 §15.7) :

1. **Saisie vocale de mesures** — Vosk FR offline → transcription →
   remplissage formulaire. Confirmation visuelle obligatoire.
2. **Explication des calculs** — « pourquoi ce volume ? » → LLM récupère
   le résultat local et l'explique avec la source. Ne recalcule pas.
3. **Question contextuelle** — « quelle essence adaptée ? » → LLM
   consulte cache local (autécologie). Si vide → propose T3 au retour réseau.

**RGPD audio** :

- Audio brut supprimé après transcription sauf accord spécifique (§6.2).
- Commandes sensibles (suppression, validation session) exigent
  confirmation visuelle.
- Mode vocal peut être forcé/désactivé par le technicien.

### 2.9 Distribution via packs

Les modèles et index RAG sont distribués via les **packs de données**
(§9 GEOSYLVA-003), pas via le Play Store :

| Pack | Contenu | Taille |
|---|---|---|
| « Assistant terrain FR » | SmolLM3 3B INT4 + index RAG local + MiniLM-L6 | ~500 MB |
| « Identification essences » | TFLite PureForest INT8 | ~50 MB |
| « Documentation ONF/CNPF » | Index RAG complémentaire | ~200 MB |

Chaque pack expose version, date, source, licence, empreinte, signature
(§9). Mises à jour en Wi-Fi, de préférence en charge, réversibles.

### 2.10 Quantification

| Modèle | Quantization | Taille | Perte accuracy | Outil |
|---|---|---|---|---|
| SmolLM3 3B | INT4 (GPTQ) | ~1.6 GB | < 4% | AutoGPTQ |
| Mistral 7B (T2) | AWQ 4-bit | ~4 GB | < 3% | AutoAWQ |
| TFLite essences | INT8 | ~50 MB | < 2% | TFLite Converter |
| MiniLM-L6 (embeddings) | INT8 | ~25 MB | < 1% | ONNX Runtime |

**Validation** : banc `GSIE-Eval-FR` (RFC-0019) avant activation. Le banc
teste justesse des citations, refus d'inventer, respect du format enveloppe.

### 2.11 Adaptateurs LoRA

Conforme à VISION_LLM_SPECIALISES §2 :

| Adaptateur | Application | Tier | Statut |
|---|---|---|---|
| `GeoSylva-Forest` | GeoSylva | T2/T3 | Étude (post-P5) |
| `GSIE-Research` | GSIE Core | T3 | Étude (post-P5) |

**T1 reste généraliste** (pas de LoRA) : contrainte mémoire + simplicité
de mise à jour. Un LoRA ajoute ~100-300 MB, ce qui complique la
distribution via packs.

### 2.12 Banc d'évaluation GSIE-Eval-FR

Tout modèle LLM doit passer le banc avant activation opérationnelle
(RFC-0019). Le banc teste :

- **Justesse des citations** : la réponse cite-t-elle une source réelle
  présente dans l'index RAG ?
- **Refus d'inventer** : le modèle refuse-t-il de produire une valeur
  numérique sans invoquer un moteur ?
- **Respect du format enveloppe** : la réponse contient-elle
  `source_reference` + `evidence_level` ?
- **Français forestier** : le vocabulaire est-il correct (essences,
  tarifs, sylviculture) ?
- **Latence** : T1 < 500 ms, T2 < 3 s, T3 < 10 s.

Un modèle qui échoue au banc est marqué `experimental` et ne peut alimenter
une recommandation opérationnelle sans consentement (§7.1 GEOSYLVA-003).

## 3. Garde-fous

- **ADR-009** : toute sortie LLM contient `source_reference` ou invoque
  un moteur. Défaut bloquant sinon.
- **GSIE-CON-001** : le forestier reste le décideur. Toute recommandation
  est contournable.
- **GSIE-CON-004** : toute conclusion est explicable (chaîne d'inférence).
- **Offline-first** : T1 fonctionne sans réseau. T2/T3 sont
  amplificateurs, jamais dépendances.
- **RGPD** : audio brut supprimé après transcription sauf accord. Pas
  de donnée personnelle envoyée au serveur sans consentement.
- **Pas de LLM sans moteur** : le LLM invoque un moteur pour toute valeur
  numérique forestière. Une sortie non citée est un défaut bloquant.

## 4. Migration et impact

- **GeoSylva** : nouveau module `domain/ai/` (LLM client, RAG local,
  assistant vocal), nouveau module `data/ai/` (ONNX Runtime, TFLite,
  Vosk), nouveaux packs de données (§9), migration Room pour cache
  RAG local.
- **API GSIE** : `gsie-ai-gateway` (RFC-0019) à implémenter pour T3.
  Routes `/ai/embed`, `/ai/rerank`, `/ai/research`.
- **Tests** : banc `GSIE-Eval-FR`, tests unitaires RAG local, tests
  integration cascade T1→T3 (mock serveur), tests RGPD audio.

## 5. Alternatives envisagées

| Alternative | Pourquoi rejetée |
|---|---|
| Llama 3.2 3B comme T1 | Licence Llama 3.2 Community (restriction commerciale potentielle) vs Apache 2.0 SmolLM3 |
| Mistral 7B comme T1 | Trop lourd pour on-device (7B INT4 = ~4 GB, RAM insuffisante sur appareils cibles) |
| API cloud comme T1 (OpenAI, Mistral API) | Violente offline-first ; pas utilisable en forêt sans réseau |
| Pas de RAG local T1 | Le LLM répondrait de mémoire → violation ADR-009 |
| LoRA sur T1 | Contrainte mémoire + complexité distribution packs |

## 6. Statut et validation

- **Statut** : Adopté (2026-08-03, DEC-000050).
- **Décision liée** : DEC-000050 (Phase P5) active l'implémentation.
- **Dépendances** : P4 (connexion GSIE Serveur, RFC-0033) terminé.
  `gsie-ai-gateway` (RFC-0019) implémenté pour T3.
- **Différé** : vLLM + Phi-4-reasoning 14B (RFC-0031) — T3 utilise
  Mistral 7B servé en attendant.

## 7. Références

- `GEOSYLVA_3_SPECIFICATION_FONCTIONNELLE.md` §15 (LLM on-device et
  multi-tier)
- `apps/GeoSylva/docs/VOLUME_CALCULATION_NEXT_GEN.md` §10 (multi-tier LLM),
  §6 (méthodes IA), §8 (entraînement), §15 (détection essence), §16
  (martelage IA)
- `apps/GeoSylva/RESEARCH_OPPORTUNITIES.md` §3 (stack IA séquencée,
  modèles on-device, datasets)
- `GSIE/RESEARCH/VISION_LLM_SPECIALISES_GSIE_CORE_2026-07-20.md`
  (adaptateurs LoRA, famille de modèles, principe "LLM appelle moteurs")
- `02_RFC/RFC-0019-gsie-ai-gateway-nvidia-nim.md` (gsie-ai-gateway,
  RAG scientifique, banc GSIE-Eval-FR)
- `02_RFC/RFC-0018-identification-botanique-plantnet.md` (identification
  botanique, volet hors-ligne)
- `02_RFC/RFC-0031-feuille-de-route-post-veille-2026-08-02.md` (vLLM +
  Phi-4-reasoning différé)
- `GSIE/ARCHITECTURE/ADR-009-garde-fou-anti-invention.md`
- `apps/GeoSylva/docs/RGPD_AUDIT_REPORT.md` (RGPD audio, données perso)
