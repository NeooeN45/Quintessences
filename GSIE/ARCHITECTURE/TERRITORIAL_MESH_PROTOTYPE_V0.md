# GSIE Territorial Mesh — Prototype v0 (Nouvelle-Aquitaine)

| Champ | Valeur |
|---|---|
| **Document** | Architecture du prototype v0 — GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Documents apparentés** | `TERRITORIAL_MESH_ROADMAP.md`, `TERRITORIAL_MESH_ACCEPTANCE.md`, `SERVER_MESHING_PROTOTYPE_V0.md` |

---

## 1. Périmètre

Le prototype v0 est restreint, par décision D1 (GSIE-DIR-0013), au périmètre suivant :

- Région : **Nouvelle-Aquitaine**
- Départements : **Charente (16)**, **Deux-Sèvres (79)**
- 1 Regional Coordination Hub (RCH) : Nouvelle-Aquitaine
- 2 Departmental Operational Domain (DOD) : Angoulême (16), Niort (79)
- 2 cellules spatiales opérationnelles (1 par DOD)
- 1 drone edge traversant les 2 cellules
- 1 simulation IGNIS simplifiée exécutée sur le périmètre

Le NCP (national) est optionnel au stade v0 : il peut être configuré en mode simulé, sans qu'un second RCH ne soit requis pour valider son fonctionnement de base (voir §3).

---

## 2. Architecture

```
                         ┌─────────────────────┐
                         │   NCP (optionnel /   │
                         │   simulé — national)  │
                         └──────────┬───────────┘
                                    │ Redis Pub/Sub fédéré
                                    │ (ADR-023)
                         ┌──────────▼───────────┐
                         │   RCH Nouvelle-       │
                         │   Aquitaine (Bordeaux)│
                         └─────┬────────────┬────┘
                               │            │
                 commandes    │            │  commandes
                 ↓ / réplication ↑          ↓ / réplication ↑
                 (ADR-022)     │            │  (ADR-022)
                              ▲▼           ▲▼
                    ┌──────────────┐  ┌──────────────┐
                    │  DOD Charente │  │ DOD Deux-    │
                    │  (Angoulême)  │  │ Sèvres       │
                    │  16           │  │ (Niort) 79   │
                    └──────┬───────┘  └──────┬───────┘
                           │                 │
                    ┌──────▼───────┐  ┌──────▼───────┐
                    │  Cellule 16-A │  │ Cellule 79-A │
                    │  (spatiale)   │  │ (spatiale)   │
                    └──────┬───────┘  └──────┬───────┘
                           │                 │
                           └──────┬──────────┘
                                  │  handoff (drone edge)
                           ┌──────▼──────┐
                           │  Drone edge  │
                           │  (capsule    │
                           │  ADR-008)    │
                           └─────────────┘
```

---

## 3. Composants

| Composant | Rôle | Implémentation v0 |
|---|---|---|
| NCP | Fédération nationale (optionnel v0) | Configuré et testable en mode simulé, sans activité de fédération réelle |
| RCH Nouvelle-Aquitaine | Coordination régionale, agrégation des 2 DOD | Nœud logique, State Fabric régional (PostgreSQL + Redis) |
| DOD Charente (Angoulême) | Autorité métier départementale | State Fabric PostgreSQL local + Redis local |
| DOD Deux-Sèvres (Niort) | Autorité métier départementale | State Fabric PostgreSQL local + Redis local |
| Cellule spatiale 16-A | Granularité opérationnelle minimale, périmètre du DOD Charente | Rattachée au DOD 16 |
| Cellule spatiale 79-A | Granularité opérationnelle minimale, périmètre du DOD Deux-Sèvres | Rattachée au DOD 79 |
| Drone edge | Entité mobile traversant les 2 cellules | Capsule territoriale signée (ADR-008), simulateur de mobilité |

---

## 4. State Fabric

Le State Fabric v0 suit strictement D3 (PostgreSQL source de vérité, pas de consensus distribué) :

- **Niveau DOD** : PostgreSQL local, source de vérité pour les données de son périmètre. Redis local pour l'état volatil (présence, cache de lecture).
- **Niveau RCH** : PostgreSQL recevant la réplication logique (ADR-022) des 2 DOD, sans autorité d'écriture sur les données départementales.
- **Capsules** : le drone edge porte une capsule ADR-008 vérifiée avant mission ; le handoff transfère un contexte versionné et un jeton idempotent, tandis que les observations produites par le drone sont signées par son identité d'appareil et synchronisées selon le protocole DOD.

Aucune primitive de consensus distribué (Raft, Paxos) n'est introduite au stade v0, conformément à D3.

---

## 5. Bus d'événements

Le bus d'événements v0 suit strictement D4 (Redis Pub/Sub, pas de Kafka) :

- **Bus départemental** : chaque DOD publie ses événements locaux (transitions d'état de cellule, entrée/sortie d'entité) sur un topic Redis Pub/Sub dédié à son périmètre.
- **Bus régional** : la RCH s'abonne aux topics des 2 DOD et republie les événements agrégés pertinents sur un topic régional, selon le schéma de nommage hiérarchique défini en ADR-023.
- **Fiabilité** : l'outbox transactionnel existant (ADR-005) garantit qu'aucun événement critique n'est perdu en cas de défaillance temporaire du bus.

---

## 6. Scénarios de test

| Scénario | Description | Critère observé |
|---|---|---|
| Handoff inter-cellules | Le drone edge traverse la frontière entre cellule 16-A et cellule 79-A | Continuité de contexte, absence de perte de capsule |
| Arrêt/redémarrage | Un DOD est arrêté (état Froid) puis redémarré (état Chaud) | Absence de perte de données, reprise idempotente de la réplication et des événements |
| Drone traversant | Le drone edge traverse successivement les 2 départements en une seule mission simulée | Continuité de suivi, latence de handoff mesurée |
| Crise | Déclenchement manuel de l'état Crise sur le DOD Charente | Déclaration par le DOD, coordination par la RCH, propagation selon la portée et traçabilité complète de la transition |

---

## 7. Mesures

| Mesure | Méthode | Statut au stade Draft |
|---|---|---|
| Latence de handoff (détection → bascule confirmée) | Chronométrage instrumenté sur le scénario de traversée | À exécuter en Phase 5, aucune cible chiffrée définitive au stade Draft |
| Débit de réplication PostgreSQL DOD→RCH | Mesure du volume répliqué par unité de temps | À exécuter en Phase 5 |
| Temps de handoff perçu (subjectif, si applicable) | Observation qualitative lors du scénario drone traversant | À documenter, non contractuel |

---

## 8. Ce qui est exclu du v0

- La fédération inter-régionale complète (2e RCH) — reportée à la Phase 6.
- L'edge en production (capsules multi-niveaux étendues, synchronisation différentielle) — reportée à la Phase 8.
- L'IoT massif (multiplicité de capteurs et de drones simultanés) — non couvert, un seul drone edge au stade v0.
- La validation de compatibilité UE6 — reportée à la Phase 7.
- Toute fédération cross-pays — hors périmètre actuel (voir `TERRITORIAL_MESH_ROADMAP.md` §3, Phase 9).

---

## 9. Critères de succès

1. La hiérarchie RCH→DOD (16, 79) est instanciée et fonctionnelle sans NCP actif requis.
2. Le handoff inter-cellules du drone edge s'exécute sans perte de contexte, avec une latence mesurée et documentée.
3. Le State Fabric réplique les états publiés de chaque DOD vers la RCH, sans divergence constatée après convergence.
4. Un arrêt/redémarrage (froid→chaud) d'un DOD s'effectue sans perte de données.
5. La simulation IGNIS simplifiée s'exécute de bout en bout sur le périmètre du prototype.

Ces critères sont couverts par les critères d'acceptation détaillés dans `TERRITORIAL_MESH_ACCEPTANCE.md` §2, qui ajoute les contrôles de rejeu et de fencing.

---

## 10. Risques spécifiques au prototype

| Risque | Référence |
|---|---|
| Sous-estimation de la fédération multi-niveaux, même restreinte à 3 niveaux effectifs | RISK-TERR-001 |
| Dérive vers un serveur national monolithique dès la configuration du NCP simulé | RISK-TERR-002 |
| Latence de handoff dégradant la continuité perçue lors de la traversée du drone | RISK-TERR-011 |
| Perte de traçabilité lors d'une transition d'état manuelle mal instrumentée | RISK-TERR-005 |

Ces risques sont détaillés dans `TERRITORIAL_MESH_RISKS.md`.
