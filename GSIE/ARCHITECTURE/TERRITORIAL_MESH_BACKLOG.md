# GSIE Territorial Mesh — Backlog phasé

| Champ | Valeur |
|---|---|
| **Chantier** | GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Documents apparentés** | `TERRITORIAL_MESH_ROADMAP.md`, `TERRITORIAL_MESH_COMPLEXITY.md`, `TERRITORIAL_MESH_PROTOTYPE_V0.md` |

---

## 1. Backlog transverse Phase 4 (préparations sans interruption)

Ces tâches ne relèvent pas d'une phase du mesh territorial : elles préparent le terrain en Phase 4 sans en retarder les priorités.

| ID | Tâche | Justification |
|---|---|---|
| TERR-T-001 | Spécifier le modèle administratif territorial et les codes INSEE région/département | Déterminer si une entité `TerritorialAdministrativeUnit` distincte est nécessaire et définir sa correspondance avec `AdministrativeUnitModel` sans fusionner les hiérarchies (D2, ADR-028). Aucune migration de code avant validation de cette spécification. |
| TERR-T-002 | Préparer un RBAC territorial minimal (scopes région/département) sans l'activer | Permet à la Phase 5 de démarrer sans dette RBAC (voir ADR-026). |
| TERR-T-003 | Valider que l'outbox transactionnel existant (ADR-005) supporte un routage à plusieurs niveaux de topic | Prérequis technique du bus d'événements fédéré (D4, ADR-023). |
| TERR-T-004 | Documenter la table de correspondance frontières scientifiques ↔ limites administratives (INSEE) | Évite une réconciliation improvisée en Phase 5 (voir ADR-028, RISK-TERR-015). |

---

## 2. Phase 5 — Prototype v0 (Nouvelle-Aquitaine)

| ID | Tâche | Description |
|---|---|---|
| TERR-P5-001 | Configurer le NCP (national) en mode optionnel/simulé | Le NCP n'est pas indispensable au prototype mono-région mais sa configuration doit être testée en amont (D1). |
| TERR-P5-002 | Instancier la RCH Nouvelle-Aquitaine | Nœud de coordination régionale, point d'entrée de la hiérarchie pour le prototype. |
| TERR-P5-003 | Instancier le DOD Charente (16) | Autorité métier départementale, State Fabric PostgreSQL local. |
| TERR-P5-004 | Instancier le DOD Deux-Sèvres (79) | Second DOD, condition nécessaire pour tester le handoff inter-DOD. |
| TERR-P5-005 | Créer 2 cellules spatiales opérationnelles (1 par DOD) | Granularité minimale pour observer une transition d'état et un handoff. |
| TERR-P5-006 | Intégrer 1 drone edge traversant les 2 cellules | Valide le handoff en conditions de mobilité réelle. |
| TERR-P5-007 | Implémenter une simulation IGNIS simplifiée sur le périmètre | Valide l'intégration du mesh territorial avec un scénario métier représentatif (incendie). |
| TERR-P5-008 | Instrumenter la mesure de latence de handoff inter-cellules | Alimente le KPI de `TERRITORIAL_MESH_ROADMAP.md` §5. |
| TERR-P5-009 | Écrire et exécuter les tests de handoff inter-cellules | Valide la continuité de contexte lors d'un déplacement. |
| TERR-P5-010 | Écrire et exécuter les tests d'arrêt/redémarrage (froid→chaud) | Valide la résilience d'un composant sans perte d'état (D6). |
| TERR-P5-011 | Tester le rejeu Outbox/Inbox et le fencing de handoff | Valide l'idempotence des effets métier, le rejet des epochs anciens et l'absence de double écriture. |

---

## 3. Phase 6 — Extension multi-régions

| ID | Tâche | Description |
|---|---|---|
| TERR-P6-001 | Activer la fédération NCP complète | Passage du NCP optionnel/simulé à un rôle actif de fédération nationale. |
| TERR-P6-002 | Instancier une 2e RCH | Condition nécessaire pour tester un handoff inter-régional réel. |
| TERR-P6-003 | Implémenter le protocole de handoff inter-régional | Étend le handoff inter-cellules (Phase 5) au niveau régional. |
| TERR-P6-004 | Mettre en œuvre la réplication PostgreSQL cross-région (ADR-022) | Fondation technique du handoff inter-régional. |
| TERR-P6-005 | Tester la résolution de conflit sur territoire à cheval entre deux régions | Couvre RISK-TERR-003. |

---

## 4. Phase 7 — Mesh national

| ID | Tâche | Description |
|---|---|---|
| TERR-P7-001 | Concevoir l'orchestrateur territorial (allocation dynamique de cellules) | Nécessaire à la concentration dynamique territoriale à l'échelle nationale. |
| TERR-P7-002 | Mettre en place la supervision globale (tableau de bord multi-niveaux) | Observabilité indispensable à l'échelle nationale. |
| TERR-P7-003 | Conduire la validation de compatibilité UE6 sur un composant représentatif | Couvre D7 sans dépendance hard prématurée. |
| TERR-P7-004 | Tester un scénario de charge réelle multi-départementale (crise) | Valide les états opérationnels à grande échelle (ADR-025). |

---

## 5. Phase 8 — Edge production

| ID | Tâche | Description |
|---|---|---|
| TERR-P8-001 | Étendre les capsules ADR-008 au multi-niveaux (ADR-024) | Ajoute des champs versionnés de manière compatible, après validation du schéma et des fixtures ; aucune rupture implicite du contrat existant. |
| TERR-P8-002 | Implémenter la synchronisation différentielle edge→DOD | Réduit le volume de données à resynchroniser après une coupure. |
| TERR-P8-003 | Valider le mode offline complet sur une sous-cellule | Couvre RISK-TERR-008. |

---

## 6. Chemin critique

```
Interfaces abstraites (ADR-015, D5)
        │
        ▼
Config territoriale (modèle administratif dédié, RBAC, outbox — §1)
        │
        ▼
Prototype v0 (Phase 5)
        │
        ▼
Fédération multi-régions (Phase 6)
        │
        ▼
Mesh national (Phase 7)
        │
        ▼
Edge production (Phase 8)
```

Aucune tâche des phases 6 à 8 ne peut démarrer avant la clôture des critères de sortie de la phase précédente (voir `TERRITORIAL_MESH_ROADMAP.md` §4).

---

## 7. Estimation de complexité (échelle S/M/L/XL/XXL)

| ID | Complexité | Voir détail |
|---|---|---|
| TERR-T-001 à TERR-T-004 | S à M | `TERRITORIAL_MESH_COMPLEXITY.md` §2 |
| TERR-P5-001 à TERR-P5-011 | M à L | `TERRITORIAL_MESH_COMPLEXITY.md` §2 |
| TERR-P6-001 à TERR-P6-005 | L à XL | `TERRITORIAL_MESH_COMPLEXITY.md` §2 |
| TERR-P7-001 à TERR-P7-004 | XL | `TERRITORIAL_MESH_COMPLEXITY.md` §2 |
| TERR-P8-001 à TERR-P8-003 | L à XL | `TERRITORIAL_MESH_COMPLEXITY.md` §2 |

L'échelle complète et les dépendances détaillées sont documentées dans `TERRITORIAL_MESH_COMPLEXITY.md`.
