# ORCHESTRE GSIE — Système d'orchestration agentique auto-évolutif

> Méta-orchestrateur qui gère des loops spécialisées en parallèle,
> avec auto-évolution, consensus entre agents, et escalade humaine
> pour les décisions critiques.

## 1. Objet

Ce dossier contient le système d'orchestration agentique de GSIE.
Il remplace le consortium 9-phases par une architecture plus large :
un **méta-orchestrateur** qui gère plusieurs **loops spécialisées**
tournant en parallèle, avec :

- **Auto-évolution** via genome versionné (pattern azena-ai + NOOA)
- **Consensus** entre agents (pattern DySCo sparse + Aegean)
- **Escalade IDE** pour les décisions critiques (pattern AI-Q Clarifier)
- **Mémoire persistante** file-based (pattern OpenAI SDK + NOOA)
- **Self-healing** generate-execute-critic (pattern LangGraph)

## 2. Architecture

```
Camille (Fondateur)
    ↕ conversation interactive + escalades IDE
═══════════════════════════════════════════════
MÉTA-ORCHESTRATEUR (GLM 5.2 High — session Devin courante)
    │
    ├── GENOME (genome.md — stratégie versionnée, auto-évolutive)
    ├── MÉMOIRE (memories/ — 6 types: info, skill, episode, error, reflection, todo)
    ├── LEÇONS (lessons/ — règles apprises, auto-append)
    │
    ├── LOOP Sécurité+Perf (SWE 1.7 max — background sub-agent)
    ├── LOOP Veille (SWE 1.7 max — background sub-agent) [extensible]
    ├── LOOP QA (SWE 1.7 max — background sub-agent) [extensible]
    │
    ├── AGENT CONSENSUS (GLM 5.2 — on-demand foreground)
    └── GATE ESCALADE (file-based → notification IDE)
```

## 3. Niveaux de décision

| Niveau | Qui décide | Exemple | Comportement |
|---|---|---|---|
| Trivial | Loop agent | Nom de variable, format | Décide seul |
| Mineur | Orchestrateur | Ordre des tâches, priorité | Décide seul + log |
| Important | Consensus agents | Choix d'architecture, dépendance | Consensus → si échec, escalade |
| Critique | Fondateur (pause) | RFC, breaking change, sécurité | **Pause + notification IDE** |

## 4. Cycle de vie d'une loop

```
PLAN → EXECUTE → VERIFY → LEARN → GATE → LOOP
         ↑          ↓
         ←←← CRITIC ←←←  (si échec, repair prompt, pas from scratch)
```

- **Retry budget** : max 3 tentatives par tâche
- **Repair prompt** : l'agent reçoit l'erreur et corrige, ne recommence pas tout
- **Error memory** : chaque échec est enregistré dans `memories/error/`
- **Reflection** : après 5 épisodes, l'orchestrateur distille une reflection

## 5. Structure des fichiers

```
GSIE/ORCHESTRE/
├── README.md                          — ce fichier
├── genome.md                          — stratégie versionnée, auto-évolutive
├── ETAT_ORCHESTRATEUR.md              — état courant, loops actives
├── loop_securite_perf.md              — mémoire de la loop sécu+perf
├── memories/
│   ├── MEMORY.md                      — index de toutes les mémoires
│   ├── info/                          — faits durables (conventions, règles)
│   ├── skill/                         — procédures réutilisables
│   ├── episode/                       — ce qui s'est passé (historique cycles)
│   ├── error/                         — erreurs passées (éviter répétition)
│   ├── reflection/                    — insights distillés d'épisodes
│   └── todo/                          — engagements en attente
├── lessons/                           — leçons apprises (auto-append)
├── ESCALATIONS/                       — questions en pause (attendent réponse)
│   └── README.md                      — format d'escalade
└── consensus/
    ├── trust_scores.json              — scores de confiance par loop
    └── historique_consensus.md        — décisions de consensus passées
```

## 6. Modèles

| Rôle | Modèle | Raison |
|---|---|---|
| Méta-orchestrateur | GLM 5.2 High | Contexte 1M, tokens illimités, raisonnement profond |
| Loop workers | SWE 1.7 max | Rapide, économique, illimité, bon pour tâches ciblées |
| Agent consensus | GLM 5.2 High | Nécessite raisonnement multi-perspectives |

## 7. Sources d'inspiration

- **NOOA** (NVIDIA-NeMo/labs-OO-Agents) — MemoryManager, ReflectionEngine
- **Hermes/NemoClaw** (NVIDIA) — Skills-and-Memory loop
- **AI-Q Blueprint** (NVIDIA) — Clarifier Agent, escalation logic
- **azena-ai** — Genome-driven loop (genome.md versionné)
- **DySCo** — Consensus sparse avec trust scores
- **LangGraph** — Generate-Execute-Critic self-healing
- **OpenAI Agents SDK** — File-based memory, approval interruptions

## 8. Skill Devin associé

`/orchestre-gsie` — skill qui définit le protocole complet, les templates
de loops, les règles de consensus et d'escalade.
