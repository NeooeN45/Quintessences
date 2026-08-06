---
name: audit-skills-devin
description: Audite toutes les skills Devin du projet, détecte les doublons, déclencheurs faibles, liens morts et écarts de gouvernance
argument-hint: "[optionnel: skill ou catégorie]"
triggers:
  - user
---

# Audit des skills Devin GSIE

Tu audites l'outillage Devin du dépôt sans modifier les skills par défaut. Ta
mission est de maintenir un catalogue cohérent, focalisé et sûr.

## Périmètre

- `.devin/skills/*/SKILL.md` ;
- `.devin/rules/` ;
- `.devin/playbooks/` ;
- `.devin/agents/` ;
- `AGENTS.md` ;
- `GSIE/PROMPTS/REGISTER.md` ;
- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`.

## Contrôles

Pour chaque skill :

1. frontmatter valide (`name`, `description`, déclencheurs cohérents) ;
2. responsabilité unique et description non ambiguë ;
3. distinction claire entre lecture, proposition, écriture et exécution ;
4. absence de contournement de Constitution, documents `Locked` ou secrets ;
5. références existantes et chemins corrects ;
6. commandes compatibles avec le dépôt et Windows si concerné ;
7. critères de sortie et format de rapport ;
8. absence de duplication avec une autre skill, une règle ou un playbook ;
9. compatibilité avec le gating `LÉGER / STANDARD / LOURD` ;
10. langue française et identifiants conformes au projet.

## Détection de doublons

Comparer les skills par :

- responsabilité ;
- déclencheurs ;
- fichiers canoniques manipulés ;
- sortie attendue ;
- niveau de risque.

Une skill de composition peut appeler une skill spécialisée, mais ne doit pas
copier son contenu.

## Format de sortie

```markdown
# Audit des skills Devin — [date]

## Synthèse
- Skills analysées :
- Conformes :
- À corriger :
- Doublons :
- Risques élevés :

## Observations par skill
| Skill | Niveau | Observation | Action |
|---|---|---|---|

## Corrections prioritaires
1. [P0]
2. [P1]
3. [P2]

## Patches proposés
[diff ou liste précise ; ne pas appliquer sans confirmation]
```

## Garde-fous

- Mode lecture seule par défaut.
- Ne modifie jamais une skill externe non révisée.
- Ne supprime jamais une skill sans décision explicite.
- Ne crée pas de skill pour un simple paragraphe qui peut être ajouté à une
  skill existante.
- Toute skill qui écrit dans le dépôt doit demander une confirmation explicite
  ou être appelée dans une mission déjà autorisée.
