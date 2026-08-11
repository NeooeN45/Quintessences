---
name: methode-glm52-high
description: Méthode de travail GLM 5.2 High pour les recherches approfondies et les validations par preuves
triggers:
  - user
  - model
---

# Note de méthode — GLM 5.2 High (Devin CLI)

> Pour les futures sessions : si le LLM actif est GLM 5.2 High, adopter cette méthode.

## Méthode "débridée" validée par le Fondateur (2026-07-27)

Le Fondateur autorise explicitement, pour les tâches demandées avec GLM 5.2 High :

1. **Tokens illimités** — utiliser autant de tokens que nécessaire, sans économie.
2. **Sous-agents en parallèle massif** — lancer autant de sous-agents que pertinent,
   en plusieurs vagues successives si besoin.
3. **Recherche approfondie** — web_search, webfetch, lecture de docs, comparaison
   de solutions, sans limite de profondeur.
4. **Rapports de progression toutes les ~20 minutes** — format simple, court,
   pour suivre l'avancement.
5. **Approche "best in class"** — viser le meilleur état de l'art, pas le minimum
   viable. Rechercher les meilleures pratiques, la meilleure sécurité, la meilleure
   performance possible.
6. **Pas de surcharge cognitive du Fondateur** — décider et exécuter, valider
   par tests et preuves, reporter seulement les décisions structurantes.

## Contexte d'application

Cette méthode a été validée sur la campagne d'amélioration de la base de données
GSIE (PostgreSQL 16 + PostGIS 3.4 + Apache AGE, 116 tables). L'audit initial
(score ~43%) a identifié 5 P0, 10 P1, 15 P2. La campagne vise à porter la base
à 100% de fiabilité, sécurité et performance.

## Compétences à mobiliser

- Skills : `postgresql-postgis`, `securite-gsie`, `deploiement`, `audit-phase4`
- Sous-agents : `qa`, `backend`, `sig`, `architecte`, `subagent_general`
- Recherche : `web_search` sur PostgreSQL best practices, pgBackRest, RLS,
  PgBouncer, partitioning, index tuning, disaster recovery
