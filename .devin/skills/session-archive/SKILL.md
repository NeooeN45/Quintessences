---
name: session-archive
description: Exporte et archive une session Devin dans 22_PROJECT_MEMORY/sessions/ pour traçabilité
argument-hint: "[session-id-optionnel]"
triggers:
  - user
  - model
---

# Archive de session — Traçabilité GSIE

GSIE exige la traçabilité de toutes les actions structurantes. Cette skill exporte la conversation courante (ou une session spécifique) et l'archive dans le projet.

## Processus

### 1. Identifier la session à archiver

- Si un session-id est fourni (`/session-archive sess_xxx`) → utiliser cette session
- Sinon → exporter la session courante avec `--export`

### 2. Exporter la conversation

```bash
# Session courante
devin --export "A:\Quintessences\22_PROJECT_MEMORY\sessions\session_[date]_[sujet].atif"

# Session spécifique (via Devin MCP devin_session_interact)
# Récupérer les messages et events de la session
```

### 3. Créer la fiche de synthèse

Créer un fichier markdown à côté de l'export :

```markdown
# Session [date] — [sujet]

## Métadonnées
- **Date** : [ISO date]
- **Session ID** : [ID]
- **Modèle** : [model utilisé]
- **Durée** : [durée estimée]
- **Type** : [implémentation / audit / recherche / refactoring / debug]

## Fichiers modifiés
- [liste des fichiers touchés]

## Décisions prises
- [liste des DEC créés ou référencés]

## Tests
- [résumé : X passent, Y échouent, couverture Z%]

## Résultat
- [ce qui a été accompli]

## Prochaines étapes
- [actions recommandées]
```

### 4. Mettre à jour l'index

Ajouter une entrée dans `22_PROJECT_MEMORY/sessions/INDEX.md` :

```markdown
| [date] | [sujet] | [type] | [lien vers fiche] | [DEC liés] |
```

### 5. Vérifier la cohérence

- Si la session a créé un DEC → vérifier que DEC-xxxxxx existe dans 03_DECISIONS/
- Si la session a modifié des Locked → vérifier qu'une RFC a été créée
- Si la session a implémenté un moteur → vérifier PROJECT_MEMORY.md est à jour

## Règles

- **Toujours** archiver après une session structurante (implémentation moteur, décision d'architecture, audit)
- **Jamais** archiver les sessions triviales (question simple, lecture de code)
- **Toujours** anonymiser les secrets potentiels dans l'export
- Le dossier `22_PROJECT_MEMORY/sessions/` doit être créé s'il n'existe pas
