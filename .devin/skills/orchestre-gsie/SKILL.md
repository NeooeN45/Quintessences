---
name: orchestre-gsie
description: |
  Méta-orchestrateur GSIE — système d'orchestration agentique auto-évolutif
  avec loops spécialisées parallèles, consensus entre agents, mémoire
  persistante typée, auto-évolution par genome versionné, et escalade
  humaine pour les décisions critiques. Conçu pour GLM 5.2 High
  (orchestrateur) + SWE-1.6 (workers), tous deux illimités.
triggers:
  - user
  - model
---

# Orchestre GSIE — Méta-orchestration agentique auto-évolutive

## 1. Objet

Ce skill définit le protocole du **méta-orchestrateur** : un agent
GLM 5.2 High qui remplace le Fondateur pour la gestion opérationnelle
des tâches GSIE, en gérant des **loops spécialisées** parallèles,
avec auto-évolution, consensus, et escalade humaine.

## 2. Architecture

```
Fondateur (Camille)
    ↕ conversation interactive + escalades IDE
═══════════════════════════════════════════════
MÉTA-ORCHESTRATEUR (GLM 5.2 High — session courante)
    ├── GENOME (genome.md — stratégie versionnée, auto-évolutive)
    ├── MÉMOIRE (memories/ — 6 types: info, skill, episode, error, reflection, todo)
    ├── LEÇONS (lessons/ — règles apprises, auto-append)
    ├── LOOP Sécurité+Perf (SWE-1.6 — background sub-agent)
    ├── LOOP QA (SWE-1.6 — background sub-agent) [extensible]
    ├── LOOP Veille (SWE-1.6 — background sub-agent) [extensible]
    ├── AGENT CONSENSUS (GLM 5.2 — on-demand foreground)
    └── GATE ESCALADE (file-based → notification IDE)
```

## 3. Démarrage de l'orchestrateur

Quand le skill est invoqué, l'orchestrateur :

1. **Lit le genome** : `GSIE/ORCHESTRE/genome.md`
2. **Lit l'état** : `GSIE/ORCHESTRE/ETAT_ORCHESTRATEUR.md`
3. **Lit l'index mémoire** : `GSIE/ORCHESTRE/memories/MEMORY.md`
4. **Association spontanée** : sélectionne les mémoires pertinentes
   (salience × récence, max 10) et les injecte dans son contexte
5. **Identifie les loops actives** et leur statut
6. **Identifie les escalades en attente** dans `ESCALATIONS/`
7. **Décide** : reprendre les loops existantes, en lancer de nouvelles,
   ou traiter les escalades

## 4. Cycle d'une loop

Chaque loop suit le cycle generate-execute-critic :

```
PLAN → EXECUTE → VERIFY → LEARN → GATE → LOOP
         ↑          ↓
         ←←← CRITIC ←←←  (si échec, repair prompt, pas from scratch)
```

### 4.1 PLAN

La loop définit l'objectif du cycle courant. Exemple pour la loop
Sécurité+Perf :

```
Cycle 1: Audit OWASP Top 10
  - Scanner tous les endpoints de l'API GSIE
  - Vérifier : injection, auth, XSS, SSRF, IDOR, rate limiting
  - Documenter les findings dans loop_securite_perf.md
```

### 4.2 EXECUTE

La loop (sub-agent SWE-1.6 en background) exécute la tâche.
L'orchestrateur surveille via `read_subagent`.

### 4.3 VERIFY

L'orchestrateur vérifie le résultat :
- Les findings sont-ils documentés ?
- Les preuves sont-elles fournies ?
- Le format est-il respecté ?

### 4.4 CRITIC (si échec)

Si VERIFY échoue :
1. L'erreur est enregistrée dans `memories/error/`
2. La loop reçoit un **repair prompt** (pas from scratch)
3. Retry budget : max 3 tentatives
4. Si 3 échecs → escalade vers l'orchestrateur

### 4.5 LEARN

Après chaque cycle réussi :
1. Un **épisode** est enregistré dans `memories/episode/`
2. Si une leçon est apprise, elle est ajoutée dans `lessons/`
3. Le **trust score** de la loop est ajusté (+0.05 succès, -0.10 échec)
4. Après 5 épisodes, une **reflection** est distillée dans `memories/reflection/`
5. Le **genome** est mis à jour si la stratégie évolue

### 4.6 GATE

Avant de passer au cycle suivant :
- Décision **triviale** → la loop continue
- Décision **mineure** → l'orchestrateur décide et log
- Décision **importante** → agent consensus
- Décision **critique** → **ESCALADE** (pause + notification IDE)

### 4.7 LOOP

Retour au PLAN avec la mémoire du cycle précédent.

## 5. Agent consensus

Quand deux loops ont un conflit ou qu'une décision importante se pose :

1. L'orchestrateur lance un sub-agent `consensus` (GLM 5.2, foreground)
2. Le sub-agent reçoit :
   - Les arguments de chaque loop
   - Les trust scores
   - Le contexte GSIE (genome, mémoire, roadmap)
3. Le sub-agent propose un compromis avec justification
4. Si les deux loops acceptent → exécution
5. Si pas de consensus après 2 rounds → **ESCALADE**

### Trust scores

Stockés dans `consensus/trust_scores.json`. Évolution :
- +0.05 par cycle réussi
- -0.10 par cycle échoué
- Score max : 1.0 (confiance totale)
- Score min : 0.0 (désactivation de la loop)

## 6. Escalade humaine

### Format

Fichier dans `GSIE/ORCHESTRE/ESCALATIONS/YYYY-MM-JJ_NNN_loop.md` :

```markdown
# ESCALADE #NNN — [Sujet court]

## Statut: EN ATTENTE DE RÉPONSE

## Question
[Question claire et directe]

## Contexte
[Éléments pertinents, impact, risque]

## Options
A) [option 1]
B) [option 2]
C) [option 3]

## Recommandation
[Option recommandée + justification]

## Impact
- Temps: [estimation]
- Fichiers: [liste]
- Breaking: [oui/non]

## Réponse attendue
Réponds A, B, C ou ta propre option.
```

### Notification IDE

L'orchestrateur affiche dans la conversation :

```
🚨 ESCALADE #001 — [Sujet]
   Question: [question]
   Options: A) ... B) ... C) ...
   Recommandation: [option]
   → Réponds A, B, C ou ta propre option
```

La loop reste en **PAUSE** jusqu'à la réponse du Fondateur.

### Résolution

1. Le Fondateur répond (A, B, C, ou option custom)
2. L'orchestrateur transmet la décision à la loop
3. La loop reprend avec la décision
4. L'escalade est marquée comme RÉSOLUE dans le fichier

## 7. Auto-évolution du genome

L'orchestrateur réécrit le genome quand :

1. **Nouvelle leçon apprise** → ajout dans `lessons/` + genome
2. **Pattern récurrent détecté** → nouveau lever d'amélioration
3. **Trust score d'une loop < 0.3** → désactivation + investigation
4. **5 épisodes complétés** → reflection distillée
5. **Stratégie obsolète** → mise à jour des priorités

Le genome est **versionné** : chaque évolution incrémente la version
et enregistre la date + le motif dans la section "Évolution du genome".

## 8. Mémoire typée

6 types de mémoire (inspiré NOOA MemoryManager) :

| Type | Description | Quand l'enregistrer |
|---|---|---|
| `info` | Fait durable, convention, règle | Connaissance permanente sur GSIE |
| `skill` | Procédure réutilisable | Comment faire quelque chose |
| `episode` | Ce qui s'est passé | Après chaque cycle de loop |
| `error` | Erreur passée | Quand une loop échoue |
| `reflection` | Insight distillé | Après 5 épisodes |
| `todo` | Engagement en attente | Tâche à faire |

Chaque mémoire a :
- `type` : un des 6 types
- `salience` : 0.0 à 1.0 (pertinence)
- `importance` : 0.0 à 1.0 (impact)
- `date` : YYYY-MM-JJ
- `contenu` : description textuelle

### Association spontanée

Avant chaque cycle, l'orchestrateur :
1. Lit `memories/MEMORY.md` (l'index)
2. Sélectionne par `salience × récence` (max 10)
3. Priorité : `error > reflection > info > skill > episode > todo`
4. Injecte les mémoires dans son contexte

## 9. Commandes de l'orchestrateur

| Commande | Action |
|---|---|
| `/orchestre-gsie` | Démarre l'orchestrateur (lit genome + mémoire + état) |
| `/orchestre status` | Affiche l'état courant (loops, escalades, trust scores) |
| `/orchestre loop securite` | Lance/manuelle la loop Sécurité+Perf |
| `/orchestre loop qa` | Lance la loop QA |
| `/orchestre loop veille` | Lance la loop Veille |
| `/orchestre consensus` | Force un consensus sur un conflit |
| `/orchestre escalades` | Liste les escalades en attente |
| `/orchestre genome` | Affiche le genome courant |
| `/orchestre memoire` | Affiche l'index mémoire |
| `/orchestre evolution` | Force une évolution du genome |

## 10. Gating hérité

Le gating adaptatif du consortium existant s'applique toujours :

| Niveau | Critère | Process |
|---|---|---|
| LÉGER | < 5 fichiers, pas de risque | 1 agent, micro-boucle |
| STANDARD | 5-15 fichiers | 1 implémenteur + 1 reviewer |
| LOURD | > 15 fichiers, breaking, sécurité | 4 agents, 9 phases |

L'orchestrateur utilise ce gating pour chaque tâche produite par une loop.

## 11. Limites et garde-fous

1. **Maximum 3 loops simultanées** (limite de parallélisme)
2. **Pas de chevauchement de fichiers** entre loops
3. **Pas de push, fusion ou déploiement** sans autorisation explicite
4. **Pas de modification de documents Locked**
5. **Tout en français**
6. **Budget retry** : 3 par tâche, puis escalade
7. **Trust score < 0.3** → désactivation de la loop
8. **Consensus échoué 2x** → escalade humaine

## 12. Fichiers de référence

| Fichier | Rôle |
|---|---|
| `GSIE/ORCHESTRE/genome.md` | Stratégie versionnée |
| `GSIE/ORCHESTRE/ETAT_ORCHESTRATEUR.md` | État courant |
| `GSIE/ORCHESTRE/memories/MEMORY.md` | Index mémoire |
| `GSIE/ORCHESTRE/loop_securite_perf.md` | Mémoire loop sécu+perf |
| `GSIE/ORCHESTRE/ESCALATIONS/` | File d'escalade |
| `GSIE/ORCHESTRE/consensus/trust_scores.json` | Trust scores |
| `.devin/agents/orchestrateur.md` | Profil agent orchestrateur |
| `.devin/agents/loop-worker.md` | Profil agent worker |
| `.devin/agents/consensus.md` | Profil agent consensus |
