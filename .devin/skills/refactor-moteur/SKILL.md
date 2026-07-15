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
pytest GSIE/ENGINES/[NOM]_ENGINE/tests/ -v --tb=short > /tmp/before.txt
mypy GSIE/ENGINES/[NOM]_ENGINE/ --strict > /tmp/mypy_before.txt
ruff check GSIE/ENGINES/[NOM]_ENGINE/ > /tmp/ruff_before.txt
git stash  # sauvegarder tout changement non committé
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
2. `pytest GSIE/ENGINES/[NOM]_ENGINE/tests/ -v` → doit passer
3. `mypy GSIE/ENGINES/[NOM]_ENGINE/ --strict` → doit passer
4. `ruff check GSIE/ENGINES/[NOM]_ENGINE/` → doit passer
5. Si échec → revert cette transformation, analyser, réessayer

### 5. Vérification finale
```bash
pytest GSIE/ENGINES/[NOM]_ENGINE/tests/ -v --tb=short > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt  # tests identiques
mypy GSIE/ENGINES/[NOM]_ENGINE/ --strict  # 0 erreur
ruff check GSIE/ENGINES/[NOM]_ENGINE/  # 0 erreur
```

### 6. Documentation
- Mettre à jour le README.md du moteur si l'architecture interne change
- Créer une entrée CHANGELOG.md : `refactor([nom]-engine): description`
- Si la décision est structurante → créer DEC-xxxxxx

## Règles absolues

- **Jamais** changer la signature publique d'une fonction sans RFC
- **Jamais** supprimer un test existant (sauf s'il testait un bug maintenant corrigé)
- **Jamais** refactoring + nouvelle fonctionnalité en même temps
- **Toujours** un commit par transformation (git est ton undo)
- **Toujours** tests verts entre chaque transformation
