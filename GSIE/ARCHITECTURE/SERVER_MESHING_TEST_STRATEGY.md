# SERVER MESHING — Stratégie de test

| Champ | Valeur |
|---|---|
| **Document** | Stratégie de test — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents connexes** | `SERVER_MESHING_ACCEPTANCE.md`, `SERVER_MESHING_PROTOTYPE_V0.md`, `SERVER_MESHING_BACKLOG.md` |

---

## 1. Mission du document

Définir la stratégie de test du chantier Server Meshing, cohérente avec
la stratégie de test transverse du projet (`/tests-gsie`) et les
conventions de l'API GSIE (`AGENTS.md` — `respx`, `pytest-asyncio`
mode auto, nommage `should_[expected]_when_[condition]`).

---

## 2. Pyramide de tests appliquée au mesh

```
              ┌───────────────────┐
              │  Tests E2E mesh    │  Phase 6+ (scénarios multi-régions)
              │  (Landiras réel)   │  Phase 5 (scénarios mono-région)
              └───────────────────┘
          ┌───────────────────────────┐
          │  Tests d'intégration mesh   │  Persistance + ZoneServer + Hub
          │  (PostgreSQL test, Redis)   │  Phase 5+
          └───────────────────────────┘
      ┌───────────────────────────────────┐
      │  Tests unitaires composants mesh    │  Interfaces, autorité, handoff
      │  (mocks/fakes, pas de réseau)       │  Phase 4 (préparation) → Phase 5+
      └───────────────────────────────────┘
```

---

## 3. Tests unitaires (Phase 4 → Phase 5)

### 3.1 Périmètre

| Composant | Tests unitaires | Outil |
|---|---|---|
| Interfaces abstraites (`IRenderClient`, `IZoneServer`, etc.) | Contrats validés par des implémentations de test (fakes) | `pytest` |
| Graphe d'autorité (résolution, conflit zone/type) | Logique de résolution isolée, sans base de données | `pytest` |
| Journal d'audit (format, immuabilité) | Append-only vérifié, identifiant traçable unique | `pytest` |
| Pertinence (filtre de réplication) | Logique de filtrage isolée | `pytest` |

### 3.2 Conventions

- Nommage : `should_[expected]_when_[condition]`
- Structure : Arrange → Act → Assert
- `pytest-asyncio` mode `auto` (pas de `@pytest.mark.asyncio`)
- Fakes/stubs préférés aux mocks
- Edge cases : zone vide, entité sans autorité, autorité en double, partition réseau simulée

---

## 4. Tests d'intégration (Phase 5+)

### 4.1 Périmètre

| Scénario | Composants impliqués | Outil |
|---|---|---|
| Persistance externe (écriture → lecture → reconstruction) | ZoneServer + PostgreSQL test | `pytest` + base de test |
| Streaming par pertinence | ZoneServer + Redis Pub/Sub + client fake | `pytest` + Redis test |
| Journal d'audit (écriture réelle en base) | ZoneServer + PostgreSQL | `pytest` + base de test |
| Reconnexion après panne | ZoneServer arrêté/redémarré + client fake | `pytest` + gestion de processus |

### 4.2 Infrastructure de test

- **PostgreSQL de test** : base dédiée, schéma migré, données Landiras
  de synthèse (pas de données de production).
- **Redis de test** : instance dédiée ou `fakeredis` pour les tests
  unitaires, Redis réel pour les tests d'intégration.
- **Pas de dépendance au Hub UE5.8 réel** pour les tests d'intégration
  backend : un client de rendu fake implémente `IRenderClient`.

---

## 5. Tests E2E (Phase 5 → Phase 6+)

### 5.1 Phase 5 — Landiras

| Scénario E2E | Critère validé |
|---|---|
| Navigation opérateur dans Landiras via le mesh | ACC-MESH-P5-01 |
| Arrêt brutal ZoneServer + redémarrage | ACC-MESH-P5-02, P5-03 |
| Coupure Hub → reconnexion automatique | ACC-MESH-P5-04 |
| Nœud terminal offline → online | ACC-MESH-P5-05 |

Ces tests E2E nécessitent le Hub UE5.8 réel (ou un équivalent de test
implémentant `IRenderClient`). Ils sont **manuels** en Phase 5, avec
capture comparative et critère de réussite explicite.

### 5.2 Phase 6+ — Multi-régions

| Scénario E2E | Critère validé |
|---|---|
| Navigation traversant une frontière de serveur | ACC-MESH-P6-03 |
| Handoff d'autorité entre deux régions | ACC-MESH-P6-02 |
| Panne d'un serveur de zone → reprise | ACC-MESH-P6-09 |
| Partition réseau → mode dégradé → réconciliation | ACC-MESH-P6-07, P6-08 |

Ces scénarios sont automatisables via un harnais de test dédié
(orchestration de conteneurs Docker simulant les nœuds du mesh).

---

## 6. Tests de mutation

Conformément à `AGENTS.md` (API GSIE), toute garde de résilience
spécifique au mesh ajoute une mutation dans le harnais de mutation
exist (`tests/mutation/harnais.py` ou un harnais dédié au mesh si le
périmètre devient distinct).

| Garde mesh candidate | Mutation associée |
|---|---|
| Refus d'écriture sans persistance confirmée (P-MESH-02) | Supprimer la garde → un test doit échouer (état non persisté accepté) |
| Refus de transfert d'autorité sans écriture préalable | Supprimer la garde → un test doit échouer (transfert sans état) |
| Journalisation obligatoire d'une décision de mesh (P-MESH-06) | Supprimer la garde → un test doit échouer (décision non tracée) |

---

## 7. Tests de performance et de charge

| Phase | Test | Objectif |
|---|---|---|
| Phase 5 | Benchmark comparatif Hub direct vs Hub via mesh | Latence de rendu équivalente (ACC-MESH-P5-08) |
| Phase 6 | Latence de handoff (détection → bascule confirmée) | Imperceptible pour l'opérateur (objectif qualitatif) |
| Phase 7 | Charge nationale (nombre de régions, d'entités, d'opérateurs) | Pas de dégradation linéaire, concentration dynamique observée |

Les tests de performance sont **différés** à la phase où ils deviennent
pertinents — pas de benchmark national en Phase 5 (YAGNI).

---

## 8. Tests de sécurité

| Test | Phase | Objectif |
|---|---|---|
| mTLS inter-nœuds (certificat invalide rejeté) | Phase 6 | ADR-017 respecté |
| Authentification opérateur (JWT) sur le mesh | Phase 5 | ADR-007 réutilisé, pas de contournement |
| Séparation des rôles (client de rendu ne peut pas écrire en persistance) | Phase 5 | ADR-011 respecté |

---

## 9. Couverture cible

| Couche | Cible | Justification |
|---|---|---|
| Logique métier mesh (autorité, handoff, pertinence) | 80% | Logique critique, conforme aux standards du projet |
| Persistance (extensions schéma mesh) | 70% | Intégration avec PostgreSQL existant, tests d'intégration prioritaires |
| Interfaces abstraites (fakes de test) | 100% des contrats | Un fake par interface, validant le contrat |
| Hub UE5.8 (adaptateur IRenderClient) | Manuel + benchmark | Le rendu Unreal n'est pas couvert par des tests automatisés |

---

## 10. Ce que cette stratégie n'est pas

- Ce n'est pas un plan de test détaillé (cas de test nommés) — celui-ci
  relève de l'implémentation, phase par phase.
- Ce n'est pas une autorisation de retarder les tests — les tests
  unitaires sont écrits **avec** le code, conformément aux standards du
  projet.
- Ce n'est pas un engagement de couverture chiffrée contraignant — les
  cibles sont indicatives, la priorité reste la validité des critères
  d'acceptation (`SERVER_MESHING_ACCEPTANCE.md`).
