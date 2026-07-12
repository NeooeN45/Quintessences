# Guide du contributeur — GSIE

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Avant de contribuer

1. Lis le `CLAUDE.md` racine (gouvernance) et le `README.md` du dossier visé.
2. Lis les documents parents dans la hiérarchie (Vision → Constitution → …).
3. Vérifie l'en-tête du fichier cible : **identifiant réel** et **statut**.

## Règles non négociables

- **La Constitution prime.** Rien ne contredit `00_CONSTITUTION/`.
- **Ne jamais modifier un `Locked`** directement → passer par un `RFC`.
- **Pas de code métier en Phase 1** (aucun moteur exécutable, API, SDK, app).
- **Français** partout.
- **Toute affirmation scientifique est sourcée.**
- **L'IA assiste, ne décide jamais** : le Fondateur valide.

## Cheminement d'une contribution

| Étape | Action |
|---|---|
| 1 | Créer/éditer un document en statut `Draft`. |
| 2 | Le porter en `Review` (le livrable précédent doit l'être au minimum). |
| 3 | Validation du Fondateur → `Validated`. |
| 4 | Verrouillage éventuel → `Locked` (RFC pour rouvrir). |

## Proposer une évolution structurante

Toute évolution de la Constitution, de la hiérarchie ou d'un `Locked` passe par
un `RFC` dans `02_RFC/` (jamais supprimé, conservé pour traçabilité). Un RFC
adopté produit une décision `DEC-` dans `03_DECISIONS/`.

## Après contribution

Synchroniser `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md`. Aucune décision
perdue.

## En cas de doute

Entre « avancer vite » et « respecter la gouvernance », choisir **toujours** la
gouvernance, et signaler le conflit plutôt que le contourner.
