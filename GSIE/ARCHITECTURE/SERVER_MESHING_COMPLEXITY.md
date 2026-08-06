# SERVER MESHING — Estimation complexité et dépendances

| Champ | Valeur |
|---|---|
| **Document** | Estimation complexité et dépendances — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents connexes** | `SERVER_MESHING_BACKLOG.md`, `SERVER_MESHING_ROADMAP.md`, `SERVER_MESHING_PROTOTYPE_V0.md` |

---

## 1. Mission du document

Fournir une estimation **qualitative** de la complexité et des
dépendances des tâches du backlog Server Meshing
(`SERVER_MESHING_BACKLOG.md`). Cette estimation n'est pas un engagement
de durée — elle utilise l'échelle du backlog (S, M, L, XL, XXL) pour
comparer les tâches entre elles et identifier le chemin critique.

---

## 2. Échelle de complexité

| Niveau | Signification | Ordre de grandeur (indicatif) |
|---|---|---|
| S | Faible — quelques jours, composant isolé | 1-3 jours |
| M | Moyen — une à deux semaines, composant avec intégration | 1-2 semaines |
| L | Élevé — plusieurs semaines, composant avec intégration et tests | 3-6 semaines |
| XL | Très élevé — un à plusieurs mois, sous-système complet | 1-3 mois |
| XXL | Exceptionnel — trimestre+, évolution architecturale majeure | 3+ mois |

Ces ordres de grandeur sont indicatifs et non contractuels — la
roadmap globale (`ROADMAP.md`) reste l'unique référence de calendrier.

---

## 3. Estimation par tâche

### 3.1 Backlog transverse (MESH-PREP)

| ID | Complexité | Dépendances techniques | Dépendances organisationnelles |
|---|---|---|---|
| MESH-PREP-001 | M | Aucune (interfaces abstraites pures) | Revue architecture |
| MESH-PREP-002 | M | ADR-001, accès au code Hub UE5.8 | Coordination Unreal |
| MESH-PREP-003 | S | ADR-007, code API GSIE | Aucune |
| MESH-PREP-004 | M | RFC-0011, migrations PostgreSQL | Coordination backend |
| MESH-PREP-005 | S | HUB-002 | Aucune |
| MESH-PREP-006 | S | CON-005, services Phase 4 existants | Aucune |
| MESH-PREP-007 | M | MESH-PREP-002 | Coordination Unreal + backend |
| MESH-PREP-008 | S | RFC-0003 | Aucune |
| MESH-PREP-009 | S | Aucune (étude) | Aucune |
| MESH-PREP-010 | M | HUB-003 | Coordination Unreal |

**Total transverse** : 5×S + 5×M. Réalisable en parallèle des priorités
Phase 4, sans les interrompre.

### 3.2 Phase 5 — Prototype v0 Landiras (MESH-P5)

| ID | Complexité | Dépendances techniques | Notes |
|---|---|---|---|
| MESH-P5-001 | L | MESH-PREP-004, PostgreSQL | Schéma + logique de résolution |
| MESH-P5-002 | L | MESH-PREP-001, 003 | Nouveau composant serveur |
| MESH-P5-003 | L | MESH-PREP-002 | Audit + migration d'état |
| MESH-P5-004 | M | MESH-PREP-001 | Adaptateur Hub |
| MESH-P5-005 | M | MESH-P5-003 | Test de reconstitution |
| MESH-P5-006 | S | MESH-PREP-006 | Extension journal existant |
| MESH-P5-007 | M | MESH-PREP-008 | Test mode dégradé |
| MESH-P5-008 | S | MESH-P5-001→007 | Rédaction rapport |
| MESH-P5-009 | M | MESH-PREP-009 | Évaluation |
| MESH-P5-010 | S | MESH-P5-008 | Rédaction écarts |

**Total Phase 5** : 3×S + 4×M + 3×L. Chemin critique :
P5-001 (graphe) + P5-002 (serveur) + P5-003 (persistance) en
parallèle, puis P5-004 (Hub) + P5-005 (redémarrage).

### 3.3 Phase 6 — Multi-régions, handoff (MESH-P6)

| ID | Complexité | Dépendances techniques | Notes |
|---|---|---|---|
| MESH-P6-001 | XL | MESH-P5-* | Deuxième région + handoff |
| MESH-P6-002 | XL | MESH-P6-001 | Protocole complet |
| MESH-P6-003 | L | MESH-P6-002 | Résolution conflits |
| MESH-P6-004 | L | MESH-P5-003 | Réplication logique |
| MESH-P6-005 | L | MESH-P6-004 | Test CAP |
| MESH-P6-006 | M | MESH-P6-002 | Seuil documenté |
| MESH-P6-007 | M | MESH-P5-006 | Extension journal |
| MESH-P6-008 | S | MESH-P6-001→007 | Rédaction enseignements |

**Total Phase 6** : 1×S + 2×M + 3×L + 2×XL. Chemin critique :
P6-001 + P6-002 (handoff) → P6-003 (conflits) + P6-004 (réplication).

### 3.4 Phase 7 — Mesh national (MESH-P7)

| ID | Complexité | Dépendances techniques | Notes |
|---|---|---|---|
| MESH-P7-001 | XXL | MESH-P6-* | Extension nationale |
| MESH-P7-002 | XL | MESH-P7-001 | Orchestrateur complet |
| MESH-P7-003 | XL | UE6_MIGRATION.md | Migration si déclenchée |
| MESH-P7-004 | L | MESH-P7-001 | Observabilité |
| MESH-P7-005 | L | MESH-P7-001 | Résilience régionale |
| MESH-P7-006 | M | MESH-P7-001→005 | Audit conformité |

**Total Phase 7** : 1×M + 2×L + 2×XL + 1×XXL. Chemin critique :
P7-001 (extension) → P7-002 (orchestrateur) → P7-005 (résilience).

---

## 4. Dépendances externes critiques

| Dépendance | Impact si indisponible | Mitigation |
|---|---|---|
| PostgreSQL/PostGIS | Bloque tout le mesh (source de vérité) | Déjà en production ; pas de risque d'indisponibilité |
| Redis Pub/Sub | Bloque la communication inter-nœuds | Déjà en production ; mode dégradé offline-first (ADR-019) |
| Hub UE5.8 (code existant) | Bloque MESH-PREP-002, MESH-P5-004 | Code disponible ; coordination avec l'équipe Unreal |
| Cesium for Unreal | Requis pour le rendu 3D du Hub | Déjà intégré ; pas de risque nouveau |
| UE6 (non publié) | Bloque MESH-P7-003 si migration décidée | Non bloquant : UE5.8 reste la référence (ADR-015) |

---

## 5. Chemin critique global

```
MESH-PREP-001 (interfaces) ──┐
MESH-PREP-002 (audit Hub) ───┤
MESH-PREP-003 (zone_id API) ─┤
                              ▼
MESH-P5-001 (graphe) + MESH-P5-002 (serveur) + MESH-P5-003 (persistance)
                              │
                              ▼
MESH-P5-004 (Hub) + MESH-P5-005 (redémarrage) → MESH-P5-008 (validation)
                              │
                              ▼
MESH-P6-001 + MESH-P6-002 (handoff) → MESH-P6-003 + MESH-P6-004
                              │
                              ▼
MESH-P7-001 (national) → MESH-P7-002 (orchestrateur) → MESH-P7-005 (résilience)
```

Aucune tâche du chemin critique ne peut être sautée sans invalider
les critères d'acceptation de sa phase (`SERVER_MESHING_ACCEPTANCE.md`).

---

## 6. Facteurs de risque sur l'estimation

| Facteur | Impact sur l'estimation | Mitigation |
|---|---|---|
| Apprentissage de l'équipe (mesh distribué, bitemporalité) | Majoration possible des tâches L et XL | Documentation dédiée (ADR, diagrammes) ; revue de code |
| Stabilité de GSIE-Net (RFC-0003, encore proposition) | MESH-PREP-008 et Phase 6 dépendent de sa stabilisation | Suivi de RFC-0003 ; ne pas construire sur GSIE-Net avant validation |
| Disponibilité de l'équipe Unreal | MESH-PREP-002, MESH-P5-004 requièrent coordination | Planification avec l'équipe Unreal dès Phase 4 |
| Dérive de périmètre (RISK-MESH-016) | Majoration non prévue | Gating strict (features expérimentales documentées à part) |

---

## 7. Ce que cette estimation n'est pas

- Ce n'est pas un engagement de durée — les ordres de grandeur sont
  indicatifs, la roadmap globale reste la référence de calendrier.
- Ce n'est pas une prévision de charge — l'allocation de ressources
  relève du Fondateur, pas de ce document.
- Ce n'est pas une garantie de linéarité — les tâches L et XL peuvent
  révéler des complexités imprévues pendant l'implémentation ; tout
  écart est tracé et la révision du backlog est explicite.
