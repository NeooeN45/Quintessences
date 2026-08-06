---
name: refactor-moteur
description: Refactoring sécurisé d'un moteur GSIE — préserve le comportement, tests avant/après
argument-hint: "[nom-du-moteur]"
triggers:
  - user
  - model
---

# Refactoring moteur GSIE

## Principe absolu

> Le comportement externe du moteur DOIT rester identique.
> Les tests existants DOIVENT passer avant et après le refactoring.
> Si un test échoue après → le refactoring a changé le comportement → **revert**.

## Processus

### 1. État initial (baseline)
```bash
# Capturer l'état actuel
cd GSIE/API
.\.venv\Scripts\python.exe -m pytest tests/unit/ -q -k [nom] --tb=short > before-tests.txt
.\.venv\Scripts\python.exe -m mypy src/gsie_api/ > before-mypy.txt
.\.venv\Scripts\python.exe -m ruff check src/ tests/ > before-ruff.txt
# Si le working tree est sale : arrêter et demander l'arbitrage du Fondateur.
# Ne jamais masquer automatiquement des changements locaux avec git stash.
```

### 2. Analyse du code
- Lire `engine.py` — identifier les fonctions > 30 lignes
- Lire `models.py` — identifier les modèles complexes
- Identifier la complexité cyclomatique > 5
- Identifier la duplication de code
- Identifier les responsabilités multiples (violation SRP)

### 3. Plan de refactoring
Lister les transformations prévues :
- Extraction de fonctions (fonctions > 30 lignes)
- Extraction de classes (violation SRP)
- Simplification conditionnelle (complexité > 5)
- Élimination de duplication (DRY)
- Renommage (variables/fonctions non révélatrices d'intention)

### 4. Exécution — une transformation à la fois

Pour CHAQUE transformation :
1. Faire la transformation
2. `.\.venv\Scripts\python.exe -m pytest tests/unit/ -q -k [nom]` → doit passer
3. `.\.venv\Scripts\python.exe -m mypy src/gsie_api/` → doit passer
4. `.\.venv\Scripts\python.exe -m ruff check src/ tests/` → doit passer
5. Si échec → revert cette transformation, analyser, réessayer

### 5. Vérification finale
```bash
.\.venv\Scripts\python.exe -m pytest tests/unit/ -q -k [nom] --tb=short > after-tests.txt
diff before-tests.txt after-tests.txt  # comparer le résultat de référence
.\.venv\Scripts\python.exe -m mypy src/gsie_api/  # 0 erreur
.\.venv\Scripts\python.exe -m ruff check src/ tests/  # 0 erreur
```

### 6. Documentation
- Mettre à jour le README.md du moteur si l'architecture interne change
- Créer une entrée CHANGELOG.md : `refactor([nom]-engine): description`
- Si la décision est structurante → créer DEC-xxxxxx

## Règles absolues

- **Jamais** changer la signature publique d'une fonction sans RFC
- **Jamais** supprimer un test existant (sauf s'il testait un bug maintenant corrigé)
- **Jamais** refactoring + nouvelle fonctionnalité en même temps
- **Toujours** un checkpoint vérifiable par transformation ; commit uniquement si autorisé
- **Toujours** tests verts entre chaque transformation
