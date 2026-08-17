# Étude NOOA — NVIDIA Labs Object-Oriented Agents pour l'orchestration GSIE

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/ETUDE_NOOA_ORCHESTRATION_AGENTS |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date** | 2026-08-08 |
| **Origine** | NVIDIA Developer Blog (27 juillet 2026) + GitHub NVIDIA-NeMo/labs-OO-Agents |
| **Veille liée** | `VEILLE_NVIDIA_DEV_BLOG_2026-08-08.md` §5 |
| **Processus lié** | `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md` |
| **Skill lié** | `.devin/skills/consortium-agents/SKILL.md` |
| **Décision liée** | Aucune — ce document ne modifie aucune décision. Pure recherche. |

---

## 1. Objet

Évaluer en profondeur le framework NOOA (NVIDIA Labs Object-Oriented
Agents) comme architecture cible potentielle pour la refonte de
l'orchestration d'agents GSIE. Cette étude complète la note de veille
`VEILLE_NVIDIA_DEV_BLOG_2026-08-08.md` §5 avec l'analyse du code source
open-source (Apache 2.0, GitHub `NVIDIA-NeMo/labs-OO-Agents`).

---

## 2. Identification du dépôt

| Champ | Valeur |
|---|---|
| **Dépôt** | https://github.com/NVIDIA-NeMo/labs-OO-Agents |
| **Licence** | Apache 2.0 |
| **Stars** | ~1.1k |
| **Forks** | ~157 |
| **Statut** | Alpha (Development Status :: 3 - Alpha) |
| **Python** | >=3.12, <3.14 |
| **Paper** | arXiv:2607.20709 — « NVIDIA OO Agents: Native Python Object-Oriented Agents » |
| **Blog** | https://developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/ |
| **PyPI** | `pip install nooa` (core), `nooa[cli]`, `nooa[memory]`, `nooa[bench]` |

### Dépendances core

```
pydantic >= 2.5.0
litellm >= 1.84.0      # model-agnostic LLM client
httpx >= 0.27.0
openinference-instrumentation-litellm >= 0.1.30
```

### Structure des packages

```
src/nooa/
├── agentdoc/          # TruncatingStringIO, introspection (methods, variables)
├── agents/            # SummarizationAgent, MethodSummarizer, TokenBudgetSummarizer
├── atif/              # ATIF export (agent trace interchange format)
├── config/            # TruncationConfig
├── context_blocks/    # DynamicContext, ResolvedBlock, render_context, scoped blocks
├── errors/            # Erreurs typées
├── mcp/               # MCP tools integration
├── runtime/           # ActorRuntime, EventManager, EventsApi, hooks, REPL
├── storage/           # Stockage
├── strategies/        # PredictStrategy et autres stratégies d'exécution
├── tools/             # ShellTools, TodoManager, WebPublisher, library_writing
├── trace_explorer/    # Visualisation de traces
└── tracing/           # OpenTelemetry hooks (protocol, pas d'implémentation OTel)
```

```
packages/nooa-memory/src/nooa_memory/
├── config.py          # MemoryConfig, RetrievalConfig, WritePolicy, ReflectionPolicy
├── descriptors.py     # ladder, to_numeric, to_label, to_status
├── embeddings.py      # HashingEmbedder, LiteLLMEmbedder
├── generative.py      # llm_reasoner, llm_reconciler
├── manager.py         # MemoryManager, MemoryToolsMixin
├── references.py      # parse_ref, capture, resolve, render (pass-by-reference)
├── schema.py          # Memory, MemoryType, Edge, EdgeType, MemoryRef
├── store.py           # MemoryStore (SQLite)
└── vector_backends.py # NumpyVectorIndex, SqliteVecVectorIndex, ChromaVectorIndex
```

---

## 3. Architecture technique

### 3.1 Le modèle « agent = classe Python »

```python
from nooa import Agent

class SupportAgent(Agent):
    """You are a support agent for a customer service system."""

    order_db: OrderDB  # état de l'objet, visible par le modèle, passé par référence

    def is_refund_eligible(self, order: Order) -> bool:
        """Return whether an order is eligible for a refund."""
        return order.delivered and order.days_since_delivery <= 30

    @strategy(PredictStrategy())
    async def classify(self, message: str) -> TicketKind:
        """Classify the customer message into the best ticket kind."""
        ...

    async def triage(self, message: str, photo: Image | None,
                     order: Order | None) -> Ticket:
        """Triage a customer message and create a support ticket."""
        ...
```

**Règles clés :**
- Les méthodes avec `...` (ellipsis) comme corps sont complétées à
  l'exécution par une boucle LLM (ActorRuntime).
- Les méthodes avec un corps normal sont du Python déterministe.
- Les `docstrings` sont les prompts du modèle.
- Les `type annotations` sont des contrats enforced (validation
  pydantique des retours).
- Les `fields` typés sont l'état persistant de l'agent.

### 3.2 ActorRuntime — la boucle d'exécution

`ActorRuntime` (src/nooa/runtime/actor.py, ~2800 lignes) est le cœur
d'exécution :
- **Signal queue** : exécution sérialisée, pas de concurrence non
  contrôlée.
- **REPL Jupyter-style** : le modèle écrit du Python qui s'exécute dans
  un namespace avec accès à `self`, imports et helpers.
- **Context window management** : collapse/archival automatique des
  événements quand la fenêtre de contexte se remplit
  (`_ARCHIVE_TARGET_UTILIZATION = 0.60`).
- **Recovery** : `ContextWindowExceededError` → archival ciblé jusqu'à
  60% d'utilisation, puis retry.
- **HarnessMetrics** : tracking des tokens, think tags, JSON fixes,
  etc.

### 3.3 Système d'événements (EventManager)

- `EventManager` : event sourcing, append-only.
- `EventsApi` : API model-callable pour inspecter et gérer l'historique.
- `EventQuery` : requêtes sur l'historique d'événements.
- Types d'événements : `ExecutionResult`, `ExecutionSignal`,
  `LLMCallStart`, `LLMCallEnd`, `LLMComplete`, `LLMOutput`,
  `SystemPrompt`.

### 3.4 Context blocks

- `DynamicContext` : blocs de contexte dynamiques injectés dans le
  prompt.
- `ResolvedBlock` : bloc résolu avec son contenu.
- `render_context` : rendu des blocs dans le prompt.
- Scoped blocks : `_scoped_blocks_var`, `_scoped_events_var` via
  contextvars.
- `CachedBlockFormatter` : cache des blocs pour éviter le re-rendu.

### 3.5 Système de mémoire (nooa-memory)

Architecture « brain-inspired, fully additive » :

| Composant | Rôle |
|---|---|
| `MemoryStore` | SQLite human-readable, schema versionné |
| `MemoryManager` | Orchestration : install, recall, remember, reflect |
| `MemoryToolsMixin` | Mixin pour ajouter `self.recall()`, `self.remember()` à un agent |
| `Memory` | Record typé (type, importance, tags) |
| `Edge` / `EdgeType` | Relations typées : supports, contradicts, derived-from |
| `MemoryRef` | Référence pass-by-reference à un objet live |
| `Embedder` | HashingEmbedder (CPU), LiteLLMEmbedder (LLM) |
| `VectorIndex` | Numpy, sqlite-vec, Chroma |

Policies configurables :
- `WritePolicy` : quand écrire en mémoire
- `RetrievalConfig` : comment récupérer (similarity, keyword, hybrid)
- `SpontaneousConfig` : rappel spontané chaque tour
- `ReflectionPolicy` : consolidation offline (merge, link, distill, prune)
- `ForgetPolicy` : decay + pruning

---

## 4. Comparaison avec l'architecture GSIE actuelle

### 4.1 Orchestration d'agents

| Aspect | GSIE actuel (`consortium-agents`) | NOOA |
|---|---|---|
| **Unité d'agent** | Prompt + callbacks + graphe de workflow | 1 classe Python |
| **État** | Dicts sérialisés entre moteurs | Fields typés sur l'objet |
| **Communication** | Sérialisation JSON répétée | Pass-by-reference (objets live) |
| **Mémoire** | Knowledge Engine (DB PostgreSQL) | SQLite + vector index, relations typées |
| **Orchestration** | 9 phases, 4 rôles, gating adaptatif | Boucles Python programmables |
| **Tracing** | Logging structuré (gsie_api.core.logging) | EventManager + ATIF export + OTel hooks |
| **Context management** | Manuel (compaction ad hoc) | Automatique (collapse à 60%, archival) |
| **Model-agnostic** | Non (lié à l'orchestrateur) | Oui (LiteLLM, tous providers) |
| **Typage** | Pydantic schemas (déjà présent) | Type annotations = contrats enforced |
| **Tests** | Tests unitaires séparés | Agent testable comme toute classe Python |

### 4.2 Convergence naturelle

GSIE utilise déjà :
- **Pydantic v2** pour les schemas → NOOA utilise pydantic >= 2.5
- **Python 3.12** → NOOA requiert >= 3.12
- **Typage strict** (mypy --strict) → NOOA utilise mypy strict
- **ruff** pour le lint → NOOA utilise ruff
- **pytest-asyncio** mode auto → NOOA utilise pytest-asyncio mode auto
- **Logging structuré** → NOOA utilise logging standard + hooks

### 4.3 Divergences à résoudre

| Point | GSIE | NOOA | Résolution |
|---|---|---|---|
| **DB** | PostgreSQL + PostGIS + AGE | SQLite | NOOA memory = couche agent, pas remplacement DB métier |
| **Async** | asyncpg + FastAPI async | asyncio natif | Compatible |
| **LLM provider** | N/A (pas d'LLM en production) | LiteLLM (tous providers) | À configurer quand besoin |
| **Sandboxing** | N/A | OpenShell recommandé | Container Docker pour exécution code LLM |
| **Maturité** | Production (Phase 4) | Alpha (research preview) | Ne pas migrer maintenant, évaluer |

---

## 5. Mapping des concepts NOOA vers GSIE

### 5.1 Les 14 moteurs GSIE comme agents NOOA (futur)

```python
from nooa import Agent

class CorrelationEngineAgent(Agent):
    """Tu es le moteur de corrélation GSIE. Tu détectes et quantifies
    les corrélations statistiques significatives entre variables issues
    de sources hétérogènes. Tu ne produis jamais de recommandation."""

    session: AsyncSession  # état : session DB de la requête
    rng: Generator          # état : générateur aléatoire pour réfutation

    def classify_strength(self, abs_coefficient: float) -> CorrelationStrength:
        """Classe |coefficient| selon l'échelle Evans (1996)."""
        for threshold, strength in _STRENGTH_THRESHOLDS:
            if abs_coefficient >= threshold:
                return strength
        return CorrelationStrength.negligible

    async def compute(self, request: CorrelationComputeRequest) -> CorrelationResult:
        """Calcule une corrélation entre deux variables et la persiste."""
        ...  # boucle LLM pour orchestration, ou corps déterministe
```

### 5.2 Le consortium comme hiérarchie d'agents

```python
class ArchitectAgent(Agent):
    """Tu es l'architecte du consortium GSIE. Tu analyses et conçois
    l'architecture. Tu ne modifies aucun fichier."""
    ...

class ImplementerAgent(Agent):
    """Tu es l'implémenteur du consortium GSIE. Tu appliques le plan
    validé par incréments vérifiables."""
    codebase: Codebase  # pass-by-reference
    ...

class QAAgent(Agent):
    """Tu es le testeur adversarial du consortium GSIE. Tu pars du
    principe que l'implémentation est incorrecte."""
    ...

class ReviewerAgent(Agent):
    """Tu es le reviewer du consortium GSIE. Tu examines le diff final
    contre les critères d'acceptation."""
    ...
```

### 5.3 Mémoire Knowledge Engine → NOOA Memory

| Knowledge Engine (actuel) | NOOA Memory (proposition) |
|---|---|
| Règles sourcées en PostgreSQL | `Memory(type="rule", importance="HIGH")` |
| Pas de relations typées entre règles | `Edge(type=EdgeType.supports, src=rule_a, dst=rule_b)` |
| Pas de recall spontané | `SpontaneousConfig` : rappel automatique chaque tour |
| Pas de reflection | `ReflectionPolicy` : consolidation offline (merge, link, distill) |
| Pas de forgetting | `ForgetPolicy` : decay + pruning |

---

## 6. Évaluation des risques

### 6.1 Risques d'adoption

| Risque | Sévérité | Mitigation |
|---|---|---|
| **Maturité Alpha** | Haute | Ne pas migrer en production maintenant. Évaluer sur un prototype isolé. |
| **Sécurité code LLM** | Haute | NOOA exécute du code LLM généré. Defense-in-depth (AST checks, deny-list) mais pas un containment boundary. OS-level isolation obligatoire (container/VM). |
| **Dépendance LiteLLM** | Moyenne | LiteLLM >= 1.84.0 requis. Vérifier compatibilité avec providers cibles. |
| **Couplage à NVIDIA** | Faible | Apache 2.0, model-agnostic, pas de lock-in NVIDIA. |
| **Performance** | Moyenne | ActorRuntime est sérialisé (signal queue). Pas de parallélisme intra-agent. Multi-agent via instances séparées. |
| **Windows compatibility** | Moyenne | NOOA utilise asyncio natif. sqlite-vec peut nécessiter compilation. Tester sur Windows. |

### 6.2 Risques de non-adoption

| Risque | Impact |
|---|---|
| **Complexité ajoutée** | NOOA ajoute une couche d'abstraction. Si GSIE n'a pas besoin d'agents LLM autonomes, c'est un overhead inutile. |
| **Divergence avec consortium-agents** | Le skill `consortium-agents` est déjà opérationnel. Migrer vers NOOA nécessite une refonte. |

---

## 7. Recommandation

### Court terme (Phase 4 — maintenant)

**Ne pas migrer.** Le skill `consortium-agents` est opérationnel et
adapté au workflow GSIE actuel (9 phases, 4 rôles, gating adaptatif).
NOOA est en statut Alpha et ne doit pas être introduit en production.

### Moyen terme (Phase 5 — après stabilisation Phase 4)

**Prototyper un agent GSIE sur NOOA** dans un environnement isolé
(container Docker) pour :
1. Évaluer la facilité de migration d'un moteur (ex : Correlation Engine)
2. Mesurer le gain de pass-by-reference vs sérialisation
3. Tester le système de mémoire typée (relations supports/contradicts)
4. Valider la compatibilité Windows + asyncio + FastAPI

### Long terme (Phase 6+ — si prototype concluant)

**Évaluer la migration progressive** du consortium vers NOOA si :
- NOOA atteint un statut Beta/Production
- Le prototype démontre un gain mesurable (tokens, latence, qualité)
- Le besoin d'agents LLM autonomes se concrétise (Learning Engine,
  Reasoning Engine avec LLM)

### Conditions de non-adoption

Ne pas adopter NOOA si :
- GSIE n'a pas besoin d'agents LLM autonomes (les moteurs sont
  déterministes)
- Le consortium actuel suffit pour l'orchestration
- La complexité ajoutée outweigh le gain

---

## 8. Sources

- [NOOA GitHub](https://github.com/NVIDIA-NeMo/labs-OO-Agents) — code source Apache 2.0
- [Paper arXiv:2607.20709](https://arxiv.org/abs/2607.20709) — « NVIDIA OO Agents: Native Python Object-Oriented Agents »
- [Blog NVIDIA](https://developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/) — Cabral & Furgale, 27 juillet 2026
- [NOOA Quick Start examples](https://github.com/NVIDIA-NeMo/labs-OO-Agents/blob/main/examples/README.md) — 11 tutoriels progressifs
- [NOOA pyproject.toml](https://github.com/NVIDIA-NeMo/labs-OO-Agents/blob/main/pyproject.toml) — dépendances et configuration
- [NOOA runtime/actor.py](https://github.com/NVIDIA-NeMo/labs-OO-Agents/blob/main/src/nooa/runtime/actor.py) — ActorRuntime (~2800 lignes)
- [NOOA memory package](https://github.com/NVIDIA-NeMo/labs-OO-Agents/tree/main/packages/nooa-memory) — MemoryManager, MemoryStore, vector backends
