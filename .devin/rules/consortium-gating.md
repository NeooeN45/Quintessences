# Règle — Gating du consortium d'agents

> Règle always-on. Détermine le niveau de cérémonie du consortium
> d'agents selon le risque de la tâche. Voir
> `.devin/skills/consortium-agents/SKILL.md` pour le détail complet.

## Arbre de décision

```
La tâche touche-t-elle > 15 fichiers OU est-elle transverse ?
├─ OUI → LOURD (consortium complet, 9 phases, 4 agents)
└─ NON → Migration DB breaking OU API publique breaking OU sécurité (auth/crypto/RLS/secrets/PII) ?
   ├─ OUI → LOURD
   └─ NON → 5 à 15 fichiers OU module complet OU endpoint API nouveau ?
      ├─ OUI → STANDARD (boucle tâche, 1 implémenteur + 1 reviewer)
      └─ NON → LÉGER (micro-boucle, 1 implémenteur seul)
```

## Niveau LÉGER

| Critère | Valeur |
|---|---|
| Fichiers touchés | < 5 |
| Migration DB | Non |
| API publique | Non |
| Architecture | Non |
| Sécurité | Non |

**Process** : fix → test ciblé → inspection diff → commit.
**Agents** : 1 (implémenteur seul, auto-vérification par tests).
**Revue** : non requise (tests suffisent).
**PR** : commit direct sur branche de travail, pas de PR formelle.

## Niveau STANDARD

| Critère | Valeur |
|---|---|
| Fichiers touchés | 5 à 15 |
| Migration DB | Non, ou additive only (CREATE INDEX, ADD COLUMN nullable) |
| API publique | Endpoint nouveau, pas de breaking |
| Architecture | Module complet, pas transverse |

**Process** : qualification → reconnaissance → plan → implémentation
incrémentale → tests pyramide → PR dossier de preuve.
**Agents** : 1 implémenteur + 1 reviewer.
**Revue** : skill `/code-review` sur le diff final.
**PR** : obligatoire, template `.github/pull_request_template.md`.

## Niveau LOURD

| Critère | Valeur |
|---|---|
| Fichiers touchés | > 15 OU transverse |
| Migration DB | Oui, ou breaking (DROP, ALTER, RENAME) |
| API publique | Breaking change |
| Architecture | Transverse, nouveau moteur, nouveau sous-système |
| Sécurité | Auth, crypto, RLS, secrets, PII |

**Process** : 9 phases complètes (voir skill consortium-agents §4).
**Agents** : 4 (architecte, implémenteur, testeur adversarial, reviewer).
**Revue** : adversariale indépendante obligatoire.
**Validation Fondateur** : requise avant fusion.
**PR** : obligatoire + prompt versionné `GSIE-PROMPT-xxxx`.
**Capitalisation** : `/session-archive` + mise à jour `PROJECT_MEMORY.md`.

## Règles de bascule

1. **Une tâche commence au niveau estimé** mais peut **monter** si la
   reconnaissance révèle un risque supérieur (ex. : un fix apparemment
   simple touche en fait une API publique).

2. **Une tâche ne descend jamais** pendant l'exécution. Si elle est
   qualifiée LOURD, elle reste LOURD jusqu'à la fin.

3. **Le Fondateur peut surclasser** : il peut imposer un niveau
   supérieur à toute tâche, même si l'arbre de décision suggère
   LÉGER.

4. **Le seuil de confiance 80%** s'applique à tous les niveaux : si une
   étape du plan a une confiance < 80%, effectuer d'abord une
   investigation isolée.

5. **Pas de chevauchement de fichiers** entre sous-agents simultanés
   (règle AI_AGENT_ORCHESTRATION.md §5.4), quel que soit le niveau.

## Références

- `.devin/skills/consortium-agents/SKILL.md`
- `.devin/playbooks/feature.devin.md`
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`
- `.github/pull_request_template.md`
