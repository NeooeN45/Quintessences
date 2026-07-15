---
name: debug-moteur
description: Debug systématique d'un moteur GSIE — protocole reproductible, root cause sur symptômes
argument-hint: "[nom-du-moteur] [description-du-bug]"
triggers:
  - user
  - model
---

# Debug moteur GSIE — Protocole

> Ne JAMAIS deviner. Ne JAMAIS essayer des fixes au hasard.
> Suivre le protocole. Un bug non reproductible est un bug non réparable.

## Protocole

### 1. REPRODUIRE

```
Peut-on reproduire dans un test ?
Quel est l'input minimum qui déclenche le bug ?
Est-ce déterministe ou flaky ?
Reproduit-on en isolation ou seulement avec d'autres composants ?
```

Créer un test qui capture le bug AVANT de le fixer :

```python
@pytest.mark.asyncio
async def test_should_handle_empty_sources_without_crash(async_client):
    """Bug : moteur crash avec sources=[] au lieu de lever ValidationException"""
    response = await async_client.post(
        "/v1/engines/evidence/process",
        json={"sources": [], "confidence_threshold": 0.75}
    )
    assert response.status_code == 422  # pas 500
```

### 2. OBSERVER

Lire l'erreur COMPLÈTE, pas juste la première ligne :

```
Message d'erreur complet → stack trace → frame le plus interne d'abord
Ne pas Google la première ligne. Lire la trace complète.

Erreurs courantes :
❌ Googler "NullPointerException"
✅ Lire quelle ligne, quelle variable, quelle call chain a causé l'erreur
```

### 3. HYPOTHÈSE

Une hypothèse à la fois, la plus probable d'abord.

Causes racines courantes à vérifier :
- Null/None non géré au call site
- Race condition (async avec état partagé)
- Cache stale (données d'un état précédent)
- Mauvais environnement (config dev en prod)
- Type mismatch (sérialisation API → modèle)
- Off-by-one (pagination, index, dates)
- Timezone (toujours UTC, convertir aux frontières)
- Précision float (Decimal pour les notes, jamais == sur floats)
- Ordre des événements (assume ordre qui n'est pas garanti)

### 4. TEST

Un changement à la fois pour isoler la variable.

```python
# Avant le fix : capturer l'état
print(f"DEBUG: sources={request.sources}, types={type(request.sources)}")
print(f"DEBUG: threshold={request.confidence_threshold}")

# Appliquer UNE hypothèse
# Re-run le test de reproduction
# Si le test passe → hypothèse confirmée
# Si le test échoue encore → revert, nouvelle hypothèse
```

### 5. FIX

Corriger la cause racine, pas le symptôme.

```python
# ❌ Fix symptôme : catch l'exception et return 200
try:
    result = process(sources)
except:
    return {"data": None}  # MASQUE le bug

# ✅ Fix cause racine : valider à l'entrée
if not sources:
    raise ValidationException("Au moins une source est requise")
```

### 6. VERIFY

1. Le test de reproduction passe maintenant
2. Tous les tests existants passent toujours (pas de régression)
3. `mypy --strict` passe
4. `ruff check` passe

### 7. DOCUMENT

- Le test de reproduction reste dans la suite (il empêche la régression)
- Commenter le fix avec la cause racine si non évident
- Entrée CHANGELOG : `fix([nom]-engine): [description du bug et de la cause]`

## Binary search debugging

Pour les bugs "ça marchait avant" :

```bash
git bisect start
git bisect bad          # commit actuel cassé
git bisect good v1.6.0  # ce commit marchait
# git checkout le midpoint
# tester → git bisect good/bad → repeat
# git trouve le commit exact qui a introduit le bug
git bisect reset
```

## Rubber duck

Avant de demander de l'aide, énoncer :
1. Qu'est-ce que j'attendais ?
2. Qu'est-ce qui s'est passé ? (output exact, erreur exacte)
3. Qu'ai-je déjà essayé ?
4. Quelle est ma meilleure hypothèse ?
5. Qu'est-ce que je devrais observer pour confirmer ?

Expliquer le problème C'EST le debug. La réponse arrive souvent en cours d'explication.
