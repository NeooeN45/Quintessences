---
name: prompt-engineering
description: Prompt engineering pour GSIE — prompts efficaces pour moteurs IA, sessions Devin, playbooks
triggers:
  - user
  - model
---

# Prompt Engineering GSIE

## Principes

### 1. Sois spécifique et explicite
```
❌ "Améliore le moteur"
✅ "Ajoute la validation Pydantic sur le champ sources du modèle EvidenceRequest pour rejeter les listes vides avec une ValidationException"
```

### 2. Définis des critères d'acceptation
```
❌ "Implémente le moteur Evidence"
✅ "Implémente le moteur Evidence. Critères d'acceptation :
    1. mypy --strict passe
    2. pytest --cov couverture ≥ 80%
    3. Réponse standard {data, confidence, trace_id, engine}
    4. Validation : sources vide → 422, confidence hors [0,1] → 422"
```

### 3. Fournis le contexte nécessaire
```
❌ "Corrige le bug"
✅ "Corrige le bug dans GSIE/ENGINES/evidence/engine.py ligne 47.
    Le moteur crash avec KeyError quand 'species' est absent de la source.
    Stack trace : [coller la trace]
    Comportement attendu : lever DataSourceException si 'species' est absent."
```

### 4. Une tâche à la fois
```
❌ "Implémente le moteur Evidence, ajoute les tests, déploie en prod, et fais la doc"
✅ "Implémente le moteur Evidence" (puis séparément : tests, déploiement, doc)
```

### 5. Exemples > instructions
```
❌ "Formate la réponse correctement"
✅ "Format de réponse attendu :
    {
      \"data\": {\"evidence_id\": \"EV-001\", \"sources\": [...]},
      \"confidence\": 0.95,
      \"trace_id\": \"a3f1c2e4-...\",
      \"engine\": \"evidence\"
    }"
```

## Templates par type de tâche

### Implémentation de moteur
```
Implémente le moteur [NOM]_ENGINE.

Contrat d'interface : [coller README.md du moteur]

Conventions :
- Python 3.11+ / mypy strict / Pydantic v2
- Exceptions typées héritant de GSIEBaseException
- Réponse : {data, confidence, trace_id, engine}
- Logging structuré JSON avec trace_id + engine + latency_ms

Critères d'acceptation :
1. mypy --strict — 0 erreur
2. ruff check — 0 erreur
3. pytest --cov ≥ 80% sur la logique métier
4. Tests : nominal, empty, invalid, fallback, confidence range, trace_id
5. Respecte le contrat d'interface du README.md
```

### Debug
```
Bug : [erreur exacte ou comportement inattendu]

Expected : [comportement attendu]
Actual : [comportement actuel]

Repro :
1. [étape 1]
2. [étape 2]

Hypothèse : [meilleure hypothèse]

Fichiers impliqués :
- [fichier 1] — [pourquoi pertinent]
- [fichier 2] — [pourquoi pertinent]
```

### Code review
```
Review les changements dans [fichiers/PR].

Vérifier :
- Logique et edge cases
- Sécurité (injection, auth, secrets)
- Performance (N+1, O(n²))
- Style (fonctions ≤30 lignes, complexité ≤5)
- Tests présents et pertinents

Format : P0 (bloquant) / P1 (important) / P2 (suggestion)
```

### Handoff cloud
```
/handoff [tâche structurée avec critères d'acceptation]

Contexte :
- Branche : [nom]
- Fichiers concernés : [liste]
- Dépendances : [moteurs amont]

Contrat : [coller si pertinent]
Critères : [liste numérotée]
```

## Anti-patterns

- ❌ Prompt vague ("fais quelque chose de bien")
- ❌ Pas de critères de succès ("tu sauras quand c'est fini")
- ❌ Tâches multiples mélangées
- ❌ Pas de contexte ("tu devrais savoir")
- ❌ Instructions contradictoires
- ❌ Prompt de 500 lignes (découper en sous-tâches)

## Pour les playbooks cloud

Les playbooks sont des templates réutilisables. Structure recommandée :

```
# [Nom du playbook]

## Contexte
[Quand utiliser ce playbook]

## Variables
- {{variable1}} : [description]
- {{variable2}} : [description]

## Instructions
[Étapes structurées]

## Critères d'acceptation
[Liste numérotée]

## Post-traitement
[Que faire après]
```
