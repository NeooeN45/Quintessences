# Registre des prompts GSIE

| ID | Agent cible | Objet | État | Dépendance | Revue |
|---|---|---|---|---|---|
| GSIE-PROMPT-0001 | Claude via Devin | Contre-audit du jalon de fiabilité | BLOQUÉE | Snapshot local à rendre accessible | Codex |
| GSIE-PROMPT-0002 | GLM 5.2 via Devin | Matrice de validation des trois dépôts | BLOQUÉE | Snapshot local à rendre accessible | Codex |
| GSIE-PROMPT-0003 | Claude via Devin | Contre-audit de la refondation constitutionnelle | VALIDÉE | Rapport `694d81d`, snapshot `3616b78` | Codex — RFC en revue |
| GSIE-PROMPT-0004 | GLM 5.2 via Devin | Contre-audit n°2 — A1 procédure de révision des `Locked` (C-01) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0005 | GLM 5.2 via Devin | Contre-audit n°2 — A2 rang de la Vision (C-02) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0006 | GLM 5.2 via Devin | Contre-audit n°2 — A3 articles constitutionnels contredits (C-03, C-04) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0007 | GLM 5.2 via Devin | Contre-audit n°2 — A4 taxonomie et classes R0–R5 (C-09, C-15, C-16) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0008 | GLM 5.2 via Devin | Contre-audit n°2 — A5 classification, habilitation R5, arrêt, journal (C-10, C-13) | VALIDÉE | Snapshot `b4096b6` | Architecte — FAVORABLE |
| GSIE-PROMPT-0009 | GLM 5.2 via Devin | Contre-audit n°2 — A6 régime temporel et apprentissage (C-08, C-11) | VALIDÉE | Snapshot `b4096b6` | Architecte — FAVORABLE |
| GSIE-PROMPT-0010 | GLM 5.2 via Devin | Contre-audit n°2 — A7 données, licences, conformité (C-12, C-18, C-19) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0011 | GLM 5.2 via Devin | Contre-audit n°2 — A8 testabilité et contrôles automatiques (C-05, C-06, C-14) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0012 | GLM 5.2 via Devin | Contre-audit n°2 — A9 cohérence du corpus et traçabilité (C-07, C-17, O-1 à O-3) | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0013 | GLM 5.2 via Devin | Contre-audit n°2 — A10 red team sur les 793 lignes ajoutées | VALIDÉE | Snapshot `b4096b6` | Architecte — RÉSERVÉ |
| GSIE-PROMPT-0014 | GLM 5.2 via Devin | Reasoning tranche 1 — R1 tests d'invariants des schémas | VALIDÉE | 36 tests verts | Architecte — accepté |
| GSIE-PROMPT-0015 | SWE 1.7 via Devin | Reasoning tranche 1 — R2 cœur d'inférence | REJETÉE | Aucun fichier produit, deux tentatives | Architecte — repris en interne |
| GSIE-PROMPT-0016 | SWE 1.7 via Devin | Reasoning tranche 1 — R3 tests adversariaux du moteur | VALIDÉE | 18 tests, 8 défauts trouvés | Architecte — accepté |
| GSIE-PROMPT-0017 | GLM 5.2 via Devin | Reasoning tranche 1 — R4 routeur et intégration | VALIDÉE | 9 tests d'intégration verts (PostgreSQL/PostGIS via testcontainers) | Architecte — accepté |
| GSIE-PROMPT-0018 (interne) | Aucun — Codex | Diagnostic Engine tranche R4 — routeur et intégration (montage sur `app.py`) | VALIDÉE | 6 routes exposées sous `/api/v1`, test de montage ajouté | Architecte — repris en interne, non délégué |
| GSIE-PROMPT-0019 (interne) | Aucun — Codex | Persistance des diagnostics — nouveau type `diagnostic`, dérivation `uuid5`, migration | VALIDÉE | 544 tests unitaires verts, 8 tests de persistance ajoutés | Architecte — repris en interne, non délégué |
| GSIE-PROMPT-0020 (interne) | Aucun — Codex | Rebaselining Alembic — baseline autonome `20260726_0001` (DEC-000036) | VALIDÉE | Cycle réel vert (base vierge → `upgrade head` → contrôle de dérive → `downgrade base` → `upgrade head`) sur PostgreSQL 16/PostGIS/AGE | Architecte — repris en interne, non délégué |
| GSIE-PROMPT-0021 (interne) | Aucun — Codex | Outbox worker — retry et dead letter (ADR-005) | VALIDÉE | Worker outbox au moins une fois, événements filtrés RGPD | Architecte — repris en interne, non délégué |
| GSIE-PROMPT-0022 (interne) | Aucun — Codex | API Resources — CRUD générique sur les types de resources enregistrés | VALIDÉE | 8 endpoints `/api/v1/resources`, RBAC fermé avant chargement | Architecte — repris en interne, non délégué |
| GSIE-PROMPT-0023 | GLM 5.2 via Devin | Résilience des dix clients d'API externes (chemins de panne amont) | À LANCER | Audit fiabilité 2026-07-28, harnais de mutation 8/8 | Architecte |
| GSIE-PROMPT-0024 | GLM 5.2 via Devin | Raccordement des dix clients sur `ResilientHttpClient` (abstraction livrée non branchée) | À LANCER | Suite de GSIE-PROMPT-0023 | Architecte |
| GSIE-PROMPT-0025 | GLM 5.2 via Devin | Élargissement de l'inventaire des sources de données (179 recensées, angles morts géographiques, thématiques et modes d'accès distants) | À LANCER | Suite de l'audit `RFC-0029` §11 | Architecte |
| GSIE-PROMPT-0026 | GLM 5.2 via Devin | Vérification des URL de l'inventaire existant (232 testées, contre-audit Architecte : 6,5 % de péremption réelle) | RENDU | Suite de GSIE-PROMPT-0025 | Architecte |
| GSIE-PROMPT-0027 | GLM 5.2 via Devin | Schémas de domaine — sept migrations, une par schéma (RFC-0029 validée par DEC-000039) | À LANCER | Suite du lot RGPD `20260728_0011`/`0012` | Architecte |

> **Note** : Les entrées marquées « interne » (GSIE-PROMPT-0018 à 0022)
> correspondent à du travail structurant réalisé directement par
> l'Architecte/Codex sans délégation à un agent Devin (Claude ou GLM 5.2).
> Aucun prompt versionné dédié n'a été rédigé au préalable. Elles sont
> tracées ici pour exhaustivité, conformément à
> `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`, et documentées
> en détail dans `CHANGELOG.md` (entrées du 2026-07-26).

## Règle de mise à jour

Le statut, le snapshot attribué et le verdict de revue sont mis à jour à
chaque transition. Un prompt bloqué peut être préparé, mais ne doit pas être
présenté comme exécuté.
