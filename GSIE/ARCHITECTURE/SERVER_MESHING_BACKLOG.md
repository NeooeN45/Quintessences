# BACKLOG SERVER MESHING — GSIE-ARCH-SM-BACKLOG v1.0.0

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-ARCH-SM-BACKLOG |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Date** | 2026-08-03 |
| **Phase** | 4 — Implémentation (préparation Phase 5+) |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents connexes** | `SERVER_MESHING_TARGET.md`, `SERVER_MESHING_PROTOTYPE_V0.md`, `SERVER_MESHING_ROADMAP.md`, `SERVER_MESHING_ACCEPTANCE.md` |

---

## 1. Résumé

Ce document décompose en tâches phasées le chantier GSIE Server Meshing acté par DEC-000053. Il couvre quatre horizons : un backlog transverse à traiter dès la Phase 4, puis les backlogs de Phase 5 (prototype v0 mono-région Landiras), Phase 6 (multi-régions, handoff) et Phase 7 (mesh national, compatibilité UE6).

## 2. Contexte et objectifs

Le Server Meshing (RFC-0035, GSIE-DIR-0012) ne doit ni retarder ni contredire les priorités de la Phase 4. Ce backlog identifie les tâches de préparation exécutables maintenant, et cadre à titre indicatif les Phases 5/6/7.

## 3. Contenu principal

### 3.1 Backlog transverse — préparation Phase 4 (MESH-PREP)

| ID | Tâche | Priorité | Effort | Dépendances |
|---|---|---|---|---|
| MESH-PREP-001 | Définir les interfaces abstraites de rendu (IRenderClient, ISceneStreamer, IEntityReplicator) | P0 | M | Aucune |
| MESH-PREP-002 | Auditer le Hub (livrable 211) pour migrer tout état critique en mémoire vers PostgreSQL/PostGIS | P0 | M | ADR-001 |
| MESH-PREP-003 | Exposer un identifiant de zone d'autorité sur chaque message API (ADR-007) | P0 | S | ADR-007 |
| MESH-PREP-004 | Introduire `authority_zone_id`/`authority_type` dans le métamodèle v6.2 | P1 | M | RFC-0011 |
| MESH-PREP-005 | Documenter dans HUB-002 la notion de couche par zone d'autorité (extension future) | P1 | S | HUB-002 |
| MESH-PREP-006 | Garantir la journalisation compatible mesh (CON-005) pour chaque service Phase 4 | P0 | S | CON-005 |
| MESH-PREP-007 | Test de non-régression : reconstruction Hub depuis PostgreSQL après redémarrage | P1 | M | MESH-PREP-002 |
| MESH-PREP-008 | Étudier compatibilité offline-first (T-8, RFC-0003) avec futur nœud mesh déconnecté | P2 | S | RFC-0003 |
| MESH-PREP-009 | ADR sur la brique de service discovery à évaluer en Phase 5 | P2 | S | Aucune |
| MESH-PREP-010 | Cartographier les 22 couches HUB-003 par candidature autorité type/zone | P2 | M | HUB-003 |

**Done (transverse)** : artefact ou test versionné, revu par le responsable architecture, sans régression HUB-001, sans nouvelle infrastructure.

### 3.2 Backlog Phase 5 — prototype v0 Landiras (MESH-P5)

| ID | Tâche | Priorité | Effort | Dépendances |
|---|---|---|---|---|
| MESH-P5-001 | Spécifier le graphe d'autorité (schéma PostgreSQL, résolution) | P0 | L | MESH-PREP-004 |
| MESH-P5-002 | Serveur de zone Landiras via interfaces abstraites | P0 | L | MESH-PREP-001, 003 |
| MESH-P5-003 | Persistance externe obligatoire pour toute entité du prototype | P0 | L | MESH-PREP-002 |
| MESH-P5-004 | Client Hub mesh-aware (multi-flux) | P0 | M | MESH-PREP-001 |
| MESH-P5-005 | Redémarrage à froid avec reconstruction depuis PostgreSQL | P0 | M | MESH-P5-003 |
| MESH-P5-006 | Journalisation complète du graphe d'autorité | P0 | S | MESH-PREP-006 |
| MESH-P5-007 | Mode dégradé offline nœud terminal | P1 | M | MESH-PREP-008 |
| MESH-P5-008 | Rapport de validation prototype v0 | P0 | S | MESH-P5-001→007 |
| MESH-P5-009 | Évaluation service discovery mono-serveur | P2 | M | MESH-PREP-009 |
| MESH-P5-010 | Écarts architecture cible vs livré | P1 | S | MESH-P5-008 |

**Done (Phase 5)** : persistance externe démontrée (aucune perte après redémarrage forcé), journalisation complète (voir `SERVER_MESHING_ACCEPTANCE.md` §3).

### 3.3 Backlog Phase 6 — multi-régions, handoff (MESH-P6)

| ID | Tâche | Priorité | Effort | Dépendances |
|---|---|---|---|---|
| MESH-P6-001 | Deuxième région, transfert d'autorité inter-serveurs | P0 | XL | MESH-P5-001→008 |
| MESH-P6-002 | Protocole de handoff sans coupure visible | P0 | XL | MESH-P6-001 |
| MESH-P6-003 | Résolution conflits autorité hybride (entité transverse) | P0 | L | MESH-P6-002 |
| MESH-P6-004 | Réplication logique PostgreSQL inter-régions | P0 | L | MESH-P5-003 |
| MESH-P6-005 | Test partition réseau (CAP) | P1 | L | MESH-P6-004 |
| MESH-P6-006 | Seuil de latence de handoff acceptable | P0 | M | MESH-P6-002 |
| MESH-P6-007 | Traçabilité des transferts inter-régions | P0 | M | MESH-P5-006 |
| MESH-P6-008 | Enseignements pour préparation Phase 7 | P1 | S | MESH-P6-001→007 |

**Done (Phase 6)** : handoff démontré sans perte de données ni coupure visible, traçabilité complète.

### 3.4 Backlog Phase 7 — mesh national (MESH-P7)

| ID | Tâche | Priorité | Effort | Dépendances |
|---|---|---|---|---|
| MESH-P7-001 | Extension nationale, partitionnement dynamique complet | P0 | XXL | MESH-P6-001→008 |
| MESH-P7-002 | Orchestrateur de concentration dynamique des ressources | P0 | XL | MESH-P7-001 |
| MESH-P7-003 | Migration UE6 si pertinente (stratégie dédiée) | P1 | XL | SERVER_MESHING_UE6_MIGRATION.md |
| MESH-P7-004 | Observabilité complète du mesh national | P0 | L | MESH-P7-001 |
| MESH-P7-005 | Résilience panne serveur régional (reprise auto) | P0 | L | MESH-P7-001 |
| MESH-P7-006 | Audit conformité aux 8 principes GSIE-DIR-0012 | P0 | M | MESH-P7-001→005 |

**Done (Phase 7)** : couverture nationale, concentration dynamique démontrée sur cas réel, 8 principes audités.

### 3.5 Matrice de dépendances

| Tâche amont | Tâches avales |
|---|---|
| MESH-PREP-001 | MESH-P5-002, MESH-P5-004 |
| MESH-PREP-002 | MESH-P5-003, MESH-P5-005 |
| MESH-PREP-003 | MESH-P5-002 |
| MESH-PREP-004 | MESH-P5-001 |
| MESH-PREP-006 | MESH-P5-006, MESH-P6-007 |
| MESH-P5-* | tout MESH-P6-* |
| MESH-P6-* | tout MESH-P7-* |

Chemin critique : interfaces abstraites → persistance externe → prototype mono-région → handoff multi-régions → mesh national.

## 4. Sources et références

RFC-0035, GSIE-DIR-0012, DEC-000053, RFC-0003, RFC-0011, ADR-007, HUB-001/002/003, livrables 211/212.

## 5. Historique

| Version | Date | Auteur | Modifications |
|---|---|---|---|
| 1.0.0 | 2026-08-03 | Devin (rédaction documentaire) | Création initiale |
