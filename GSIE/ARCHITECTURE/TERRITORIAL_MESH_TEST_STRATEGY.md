# GSIE Territorial Mesh — Stratégie de test

| Champ | Valeur |
|---|---|
| **Document** | Stratégie de test — GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Documents apparentés** | `TERRITORIAL_MESH_ACCEPTANCE.md`, `TERRITORIAL_MESH_PROTOTYPE_V0.md`, `23_QUALITY_MANAGEMENT/` |

---

## 1. Pyramide de tests

```
                    ▲
                   / \
                  / E2E \          ← Phase 6 et suivantes
                 /-------\
                / Intégra-\        ← à partir de Phase 5
               /   tion    \
              /-------------\
             /   Unitaires   \     ← dès Phase 4 (préparations)
            /-----------------\
```

La base de la pyramide (tests unitaires) est constituée dès les préparations Phase 4 (§1 de `TERRITORIAL_MESH_BACKLOG.md`). Les tests d'intégration démarrent avec le prototype v0 (Phase 5). Les tests de bout en bout (E2E) complets, couvrant plusieurs niveaux hiérarchiques réels, ne deviennent pertinents qu'à partir de la Phase 6 (multi-régions).

---

## 2. Tests unitaires

| Cible | Exemples |
|---|---|
| Logique métier territoriale | Validation de la hiérarchie (pas de boucle, pas d'orphelin — ADR-020) ; résolution d'un identifiant de périmètre. |
| Transitions d'état | Transition Froid→Chaud, Chaud→Opérationnel, Opérationnel→Crise, et retours autorisés ; rejet des transitions non autorisées. |
| Routage du bus d'événements | Construction du topic hiérarchique (ADR-023) ; correspondance entre un événement et ses abonnés attendus par niveau. |

Couverture attendue dès l'introduction du code correspondant, sans attendre la fin d'une phase (principe « les tests sont écrits avec le code, jamais après »).

---

## 3. Tests d'intégration

| Cible | Exemples |
|---|---|
| Hiérarchie NCP→RCH→DOD | Chargement de configuration complète, propagation d'un événement de test à travers les 3 niveaux. |
| Réplication PostgreSQL | Écriture sur un DOD, vérification de la convergence sur la RCH dans un délai documenté (ADR-022). |
| Handoff | Simulation d'un déplacement de drone entre 2 cellules de DOD distincts, vérification de la continuité de contexte, du jeton idempotent et de l'absence de double écriture grâce à l'epoch de fencing. |
| Outbox/Inbox | Publication interrompue après notification Redis, rejeu de l'événement, déduplication par `consumer_inbox` et effet métier unique. |
| Ordre causal | Livraison hors ordre et perte temporaire d'un prédécesseur, vérification de la mise en attente puis du rejeu via `causation_id` et `sequence_no`. |
| Capsules edge | Écriture d'une observation signée en mode offline simulé, vérification de la resynchronisation après reconnexion et de l'arbitrage d'un conflit. |

---

## 4. Tests de bout en bout (E2E)

| Cible | Exemples |
|---|---|
| Prototype v0 complet | Scénario complet Nouvelle-Aquitaine : instanciation, drone traversant, simulation IGNIS simplifiée, mesure de latence, arrêt/redémarrage. |
| Scénarios de crise | Déclenchement d'un état Crise sur un DOD, vérification de la propagation correcte vers la RCH et de la traçabilité complète. |
| Scénarios offline | Coupure réseau simulée d'une sous-cellule pendant une durée définie, vérification de la continuité de fonctionnement local puis de la resynchronisation. |

---

## 5. Tests de performance

| Métrique | Méthode |
|---|---|
| Latence de handoff (détection → bascule confirmée) | Chronométrage instrumenté sur le scénario de traversée du drone edge (Phase 5), reproduit à charge croissante en Phase 6-7. |
| Débit de réplication PostgreSQL | Mesure du volume répliqué par unité de temps entre DOD et RCH, sous charge simulée. |
| Charge de cellules | Simulation de multiples entités actives simultanément sur une cellule, mesure du temps de réponse du State Fabric local. |

---

## 6. Tests de sécurité

| Cible | Exemples |
|---|---|
| mTLS inter-niveaux | Vérification du rejet d'une connexion sans certificat valide entre deux niveaux hiérarchiques (réutilisation ADR-017). |
| RBAC territorial | Vérification qu'un rôle scopé à un DOD ne peut agir sur un autre DOD sans droit transverse explicite (ADR-026). |
| Audit | Vérification que toute transition d'état et tout handoff génère une entrée d'audit non falsifiable, incluant l'epoch d'autorité. |
| Fencing | Vérification qu'une écriture portant un epoch ancien est rejetée après handoff ou reprise sur panne. |
| Clés edge | Vérification que la clé SQLCipher provient du keystore/secret matériel de l'appareil et qu'une capsule seule ne permet pas de déchiffrer la base. |

Une revue de sécurité dédiée est requise avant toute activation du RBAC territorial en dehors de l'environnement de prototype (voir ADR-026).

---

## 7. Tests de mutation

Les tests de mutation ciblent en priorité les mécanismes de résilience et les transitions d'état, où une régression silencieuse aurait un impact critique :

- Gardes de résilience (mode dégradé offline-first, réutilisation ADR-019).
- Transitions d'état (garantir qu'aucune mutation du code de transition ne passe inaperçue sans faire échouer un test).

Le taux de détection de mutants sur ces deux périmètres est suivi comme indicateur de robustesse de la suite de tests, distinct de la couverture de ligne.

---

## 8. Couverture cible

| Périmètre | Cible |
|---|---|
| Logique métier territoriale (hiérarchie, transitions d'état, routage) | 80 % |
| Ensemble du chantier Territorial Mesh (hors code d'infrastructure tiers) | 60 % minimum |

Ces cibles sont alignées sur les standards généraux du projet et ne constituent pas une dérogation spécifique au chantier Territorial Mesh.
