# GSIE Territorial Mesh — Estimation de complexité et dépendances

| Champ | Valeur |
|---|---|
| **Document** | Estimation de complexité — GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Documents apparentés** | `TERRITORIAL_MESH_BACKLOG.md`, `TERRITORIAL_MESH_ROADMAP.md` |

---

## 1. Échelle de complexité

| Niveau | Durée indicative | Signification |
|---|---|---|
| S | 1 à 3 jours | Tâche isolée, faible incertitude, pas de nouvelle dépendance |
| M | 1 à 2 semaines | Tâche circonscrite, quelques dépendances internes, incertitude modérée |
| L | 3 à 6 semaines | Tâche structurante, dépendances multiples, nécessite une conception préalable |
| XL | 1 à 3 mois | Chantier à part entière, dépendances croisées entre composants, validation en plusieurs étapes |
| XXL | 3 mois et plus | Hors granularité d'une tâche unique — à décomposer avant estimation |

Ces durées sont indicatives et non contractuelles ; elles servent à la priorisation et à l'identification du chemin critique, non à un engagement de livraison daté (voir `TERRITORIAL_MESH_ROADMAP.md` §5).

---

## 2. Estimation par tâche du backlog

| Tâche | Phase | Complexité | Dépendances |
|---|---|---|---|
| TERR-T-001 — Spécification du modèle administratif territorial et codes INSEE | Phase 4 (transverse) | M | `AdministrativeUnitModel` forestier/cadastral existant, ADR-028 |
| TERR-T-002 — RBAC territorial minimal (préparation) | Phase 4 (transverse) | S | RBAC API GSIE existant |
| TERR-T-003 — Validation outbox multi-niveaux | Phase 4 (transverse) | S | ADR-005 (outbox existant) |
| TERR-T-004 — Table de correspondance frontières scientifiques/administratives | Phase 4 (transverse) | M | Référentiels scientifiques existants (GIS, Pedology, Climate) |
| TERR-P5-001 — Configuration NCP simulé | Phase 5 | S | TERR-T-001 |
| TERR-P5-002 — Instanciation RCH Nouvelle-Aquitaine | Phase 5 | M | TERR-T-001, ADR-020 |
| TERR-P5-003 — Instanciation DOD Charente | Phase 5 | M | TERR-P5-002 |
| TERR-P5-004 — Instanciation DOD Deux-Sèvres | Phase 5 | M | TERR-P5-002 |
| TERR-P5-005 — 2 cellules spatiales | Phase 5 | M | TERR-P5-003, TERR-P5-004 |
| TERR-P5-006 — Drone edge traversant | Phase 5 | L | TERR-P5-005, ADR-008/024 |
| TERR-P5-007 — Simulation IGNIS simplifiée | Phase 5 | L | TERR-P5-005, moteur Simulation GSIE |
| TERR-P5-008 — Instrumentation mesure latence | Phase 5 | S | TERR-P5-006 |
| TERR-P5-009 — Tests handoff inter-cellules | Phase 5 | M | TERR-P5-006 |
| TERR-P5-010 — Tests arrêt/redémarrage | Phase 5 | M | TERR-P5-003, TERR-P5-004 |
| TERR-P5-011 — Tests rejeu Outbox/Inbox et fencing | Phase 5 | M | TERR-P5-006, ADR-005, ADR-010 |
| TERR-P6-001 — Fédération NCP complète | Phase 6 | L | Phase 5 clôturée |
| TERR-P6-002 — 2e RCH | Phase 6 | L | TERR-P6-001 |
| TERR-P6-003 — Handoff inter-régional | Phase 6 | XL | TERR-P6-002, ADR-022 |
| TERR-P6-004 — Réplication PostgreSQL cross-région | Phase 6 | XL | ADR-022 |
| TERR-P6-005 — Test conflit territoire transfrontalier | Phase 6 | L | TERR-P6-004, ADR-028 |
| TERR-P7-001 — Orchestrateur territorial | Phase 7 | XL | Phase 6 clôturée |
| TERR-P7-002 — Supervision globale | Phase 7 | L | TERR-P7-001 |
| TERR-P7-003 — Validation compatibilité UE6 | Phase 7 | L | ADR-015, disponibilité UE6 |
| TERR-P7-004 — Scénario de charge nationale | Phase 7 | XL | TERR-P7-001, TERR-P7-002 |
| TERR-P8-001 — Extension capsules multi-niveaux | Phase 8 | M | ADR-024 |
| TERR-P8-002 — Synchronisation différentielle | Phase 8 | L | TERR-P8-001 |
| TERR-P8-003 — Validation offline complet | Phase 8 | L | TERR-P8-002, ADR-019 |

---

## 3. Chemin critique

```
Interfaces abstraites (ADR-015, D5)
        │
        ▼
Config territoriale (TERR-T-001 à TERR-T-004)
        │
        ▼
Prototype v0 (TERR-P5-001 → TERR-P5-011)
        │
        ▼
Fédération multi-régions (TERR-P6-001 → TERR-P6-005)
        │
        ▼
Mesh national (TERR-P7-001 → TERR-P7-004)
        │
        ▼
Edge production (TERR-P8-001 → TERR-P8-003)
```

Le chemin critique traverse systématiquement les tâches de configuration et de validation de handoff : toute sous-estimation sur ces tâches (voir §5) se propage directement au calendrier des phases suivantes.

---

## 4. Tâches parallélisables

| Tâches parallélisables | Justification |
|---|---|
| TERR-T-002, TERR-T-003, TERR-T-004 (Phase 4 transverse) | Aucune dépendance croisée entre ces trois préparations |
| TERR-P5-003 et TERR-P5-004 (instanciation des 2 DOD) | Deux périmètres départementaux indépendants, même modèle |
| TERR-P5-008 (instrumentation), TERR-P5-009/010 (tests) et TERR-P5-011 (rejeu/fencing) | L'instrumentation et les scénarios de résilience peuvent être préparés en parallèle de l'implémentation des deux DOD |
| TERR-P7-002 (supervision) et TERR-P7-003 (validation UE6) | Deux livrables indépendants de la Phase 7, tous deux dépendants uniquement de la clôture de la Phase 6 |

---

## 5. Risques de sous-estimation

| Tâche à risque | Raison |
|---|---|
| TERR-P5-006/007 (drone edge, simulation IGNIS) | Première intégration réelle entre le mesh territorial et un moteur métier (Simulation) ; risque de découverte tardive d'incompatibilité de contrat |
| TERR-P6-003/004 (handoff inter-régional, réplication cross-région) | Premier test réel de fédération à deux RCH ; la latence de réplication logique PostgreSQL en conditions réelles reste non mesurée avant cette étape |
| TERR-P7-001 (orchestrateur territorial) | Premier composant d'allocation dynamique du chantier ; risque d'oscillation (anti-flapping) non anticipé, à l'image du risque équivalent du Server Meshing |
| TERR-P8-002 (synchronisation différentielle) | Nécessite une définition précise du format différentiel, dépendante de la maturité des capsules étendues (TERR-P8-001) livrées juste avant |

Ces tâches font l'objet d'un suivi renforcé lors du passage en phase de spécification technique détaillée, avant tout engagement de complexité révisé.
