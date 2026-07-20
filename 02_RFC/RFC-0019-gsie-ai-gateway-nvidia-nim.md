# RFC-0019 — `gsie-ai-gateway` : couche IA serveur transverse (NVIDIA NIM et équivalents)

| Champ | Valeur |
|---|---|
| **ID** | RFC-0019 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-20 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | Nouveau composant transverse `gsie-ai-gateway`, GSIE API (nouvelles routes `/ai/*`), Botanical/Climate/Pedology Engines (consommateurs potentiels du RAG), Ignis (vision/détection), Hydro/Atmos (Earth2Studio), `03_DECISIONS/`, `PROJECT_MEMORY.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science sourcée), GSIE-CON-005 (traçabilité) |
| **RFC liées** | RFC-0017 (veille, cadrage — scindé ici), RFC-0015 (Environmental Model Fabric — registre de modèles/licences/domaine de validité, directement applicable à chaque modèle NVIDIA utilisé), RFC-0014 (garde-fou anti-invention — le RAG doit le respecter) |
| **Décision liée** | Issue de DEC-000029 (adoption du cadrage RFC-0017 et de sa scission) — ce RFC lui-même n'a pas encore de décision propre |

---

## 1. Objet

Spécifier un composant serveur unique, `gsie-ai-gateway`, comme seul
point d'entrée pour toute capacité IA générative ou d'inférence lourde
utilisée par GSIE et ses applications clientes — en commençant par le
cas d'usage à plus fort effet de levier : le **RAG scientifique**
(recherche documentaire GSIE), avant toute extension vision/voix/météo.

## 2. Ce que ce RFC ne couvre pas

- L'identification botanique Pl@ntNet — traitée par RFC-0018 (peut
  consommer ce gateway une fois disponible, mais n'en dépend pas pour
  démarrer).
- L'auto-hébergement de production de modèles NIM — explicitement hors
  périmètre tant que le matériel/l'usage ne le justifient pas (§7).
- Les Blueprints P2/P3 (DeepStream/TAO, VSS, Earth2Studio, cuOpt,
  Jetson) — mentionnés pour la feuille de route mais non spécifiés ici ;
  chacun nécessitera son propre jalon une fois le socle P0 en place.

## 3. Contexte et motivation

GSIE accumule une base de connaissances scientifique substantielle
(`GSIE/RESEARCH/`, `GSIE/KNOWLEDGE/`, `GSIE/DATASETS/`) sans moyen de
recherche sémantique dessus. Une recherche par mots-clés ne suffit pas
pour retrouver un fait autécologique précis dans un corpus de
centaines de documents. La veille RFC-0017 identifie NVIDIA NIM/RAG
Blueprint comme accélérateur possible, à condition de ne jamais lui
confier l'autorité scientifique (déjà tenue par les moteurs Evidence/
Validation de GSIE).

## 4. Principe non négociable

`PostgreSQL/PostGIS/Apache AGE` reste la vérité canonique. Tout index
vectoriel ou service NVIDIA est une **projection reconstruisible** :
en cas de perte, il doit pouvoir être régénéré intégralement à partir
de la base canonique, sans perte d'information. Aucun LLM ou VLM du
gateway n'est autoritaire — il assiste la recherche et la synthèse, il
ne valide ni ne décide (GSIE-CON-001).

## 5. Conception proposée

### 5.1 Interface

Routes stables exposées par `gsie-ai-gateway`, indépendantes du
fournisseur sous-jacent :

- `/ai/embed` — vectorisation de texte (candidat : Nemotron Embed).
- `/ai/rerank` — reclassement de résultats de recherche.
- `/ai/research` — recherche augmentée avec citations exactes
  (page/passage), inspirée du Blueprint AI-Q mais adaptée aux
  contraintes GSIE (voir §5.3).
- `/ai/chat`, `/ai/transcribe`, `/ai/vision` — réservées pour extension
  future (voix Parakeet, vision), non implémentées dans ce jalon.

Chaque appel journalise : modèle, version, prompt, paramètres, coût,
durée, niveau de confiance, citations produites, utilisateur —
exigence directe de GSIE-CON-005, cohérente avec le registre de
modèles de RFC-0015.

### 5.2 Fournisseur

Le gateway ne verrouille pas à NVIDIA : il doit permettre de comparer
Nemotron / Mistral / autres endpoints compatibles sans changer les
routes exposées à GSIE. Clés API exclusivement côté serveur.

### 5.3 Garde-fou du RAG scientifique

Toute réponse de `/ai/research` doit obligatoirement porter : les
affirmations, les sources exactes, le niveau de preuve, le domaine de
validité, les contradictions connues, l'incertitude, une mention
explicite que ce n'est pas une prescription — reprenant le vocabulaire
imposé par RFC-0015 (observation/estimation/simulation/recommandation)
et le garde-fou anti-invention de RFC-0014.

### 5.4 Évaluation

Un banc d'essai `GSIE-Eval-FR` (100 questions scientifiques FR
validées par le fondateur ou un référent) sert de critère
d'acceptation avant toute mise en service :

- Recall@10 documentaire ≥ 85 %.
- Précision des citations ≥ 95 % (chaque citation pointe réellement
  vers la source et le passage affirmés).
- Abstention obligatoire si les preuves sont insuffisantes — pas de
  réponse générée sans source.

## 6. Priorisation (reprise de RFC-0017 §2.2, confirmée ici comme périmètre P0 de ce RFC)

P0 uniquement pour ce RFC : RAG scientifique (`/ai/embed`,
`/ai/rerank`, `/ai/research`), garde-fou (`NeMo Guardrails` ou
équivalent), banc d'essai `GSIE-Eval-FR`. Tout le reste (P1 : AI-Q
étendu, Earth2Studio, cuOpt, Parakeet ; P2+ : vision/vidéo,
géospatial accéléré, Hub UE5.8) est **hors périmètre d'implémentation
de ce RFC** et nécessitera un jalon ou un RFC dédié une fois le socle
P0 validé en usage réel.

## 7. Préalables et contraintes avant toute implémentation

- **Pas d'auto-hébergement NIM en production** sur le matériel actuel
  (non supporté sous Windows/WSL, GPU insuffisant — RTX 3050 Laptop
  4 Go). Prototypage exclusivement via endpoints hébergés et Brev,
  avec plafond d'heures GPU défini avant chaque expérience.
- **Vérification de licence** par modèle/actif utilisé (Nemotron
  Embed/Rerank, tout Blueprint), enregistrée dans le `ModelRegistry`
  de RFC-0015 avant intégration.
- **Benchmark français obligatoire** avant adoption d'un modèle —
  aucune présomption de bonne performance en français (cf. Nemotron
  Parse annoncé anglais uniquement dans la veille RFC-0017 §2.3).
- **Décision fondateur explicite** (`03_DECISIONS/`) avant tout
  développement, conformément à la règle §5 de `CLAUDE.md`.
- Usage de production (au-delà du programme développeur gratuit)
  nécessite une licence NVIDIA AI Enterprise ou un endpoint partenaire
  — à ne pas engager avant charge réelle mesurée. Candidature NVIDIA
  Inception à envisager seulement après immatriculation de la
  micro-entreprise.

## 8. Alternatives considérées

- **Construire un RAG 100 % maison** (embeddings open source
  auto-hébergés, sans NVIDIA) — élimine toute dépendance externe, plus
  lent à livrer, coût d'infra à charge complète dès le départ. À
  reconsidérer si le benchmark français de Nemotron déçoit ou si les
  conditions commerciales NVIDIA se dégradent.
- **Ne pas construire de RAG du tout, recherche par mots-clés
  uniquement** — rejeté : ne passe pas à l'échelle du corpus GSIE
  actuel (`GSIE/RESEARCH/`, `GSIE/KNOWLEDGE/`).
- **Remplacer PostgreSQL/PostGIS/AGE par une base vectorielle dédiée
  (Milvus, Elasticsearch) comme source de vérité** — explicitement
  rejeté (RFC-0017 §2.5) : romprait le principe de vérité canonique
  unique.

## 9. Prochaine étape

RFC en `Draft`. Passage en `Review` à la demande du fondateur, puis
décision. Une fois adopté, seul le périmètre P0 (§6) est autorisé en
implémentation immédiate.
