# GSIE Territorial Mesh — Critères d'acceptation

| Champ | Valeur |
|---|---|
| **Document** | Critères d'acceptation — GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Documents apparentés** | `TERRITORIAL_MESH_PROTOTYPE_V0.md`, `TERRITORIAL_MESH_TEST_STRATEGY.md`, `TERRITORIAL_MESH_ROADMAP.md` |

---

## 1. Principes

1. **Critères binaires** — chaque critère est satisfait ou non satisfait ; aucune évaluation qualitative floue n'est acceptée comme preuve de clôture de phase.
2. **Traçabilité obligatoire** — la preuve de satisfaction de chaque critère (log, rapport de test, capture d'audit) est conservée et référencée dans la décision de clôture de phase (DEC-xxxxxx).
3. **Non-régression Phase 4** — aucun critère d'acceptation du présent document ne peut être satisfait au prix d'une régression sur les priorités Phase 4 en cours (14 moteurs, API GSIE, Hub UE5.8, GeoSylva, Ignis).

---

## 2. Critères Phase 5 (prototype v0)

| ID | Critère | Preuve attendue |
|---|---|---|
| ACC-TERR-P5-01 | La hiérarchie NCP (simulé) → RCH Nouvelle-Aquitaine → DOD Charente/Deux-Sèvres est instanciée en configuration et chargée sans erreur | Journal de démarrage, configuration versionnée (voir ADR-020) |
| ACC-TERR-P5-02 | Les transitions d'état (Froid, Chaud, Opérationnel, Crise) sont déclenchables manuellement et tracées dans le journal d'audit | Extrait de journal d'audit pour au moins une transition par état |
| ACC-TERR-P5-03 | Le State Fabric réplique les données publiées de chaque DOD vers la RCH, sans divergence constatée après convergence | Rapport de test DOD→RCH et vérification de convergence pour les deux DOD |
| ACC-TERR-P5-04 | Le handoff inter-cellules, via le RCH pour les deux DOD, fonctionne sans perte de contexte ni double écriture grâce à un jeton idempotent et un epoch de fencing | Rapport de test de handoff, état des epochs, absence d'écriture acceptée avec un epoch ancien et latence mesurée |
| ACC-TERR-P5-05 | Le drone edge traverse les 2 cellules sans interruption de suivi perceptible | Enregistrement du scénario de traversée, absence de coupure documentée |
| ACC-TERR-P5-06 | La simulation IGNIS simplifiée s'exécute de bout en bout sur le périmètre du prototype | Rapport d'exécution de la simulation |
| ACC-TERR-P5-07 | Un composant peut être arrêté puis redémarré (transition froid→chaud) sans perte de données | Rapport de test arrêt/redémarrage, comparaison d'état avant/après |
| ACC-TERR-P5-08 | La latence de handoff est mesurée et documentée, même en l'absence de cible chiffrée définitive | Rapport de mesure (`TERRITORIAL_MESH_PROTOTYPE_V0.md` §7) |
| ACC-TERR-P5-09 | Un événement critique rejoué après une livraison Redis incertaine ne produit qu'un effet métier | Rapport Outbox/Inbox, identifiant d'événement, déduplication et état final unique |

---

## 3. Critères Phase 6 (multi-régions)

| ID | Critère | Preuve attendue |
|---|---|---|
| ACC-TERR-P6-01 | La fédération NCP complète agrège correctement les données des 2 RCH actives | Rapport d'agrégation, cohérence vérifiée |
| ACC-TERR-P6-02 | Un handoff inter-régional s'exécute sans perte de données ni incohérence d'état | Rapport de test de handoff inter-régional |
| ACC-TERR-P6-03 | La réplication PostgreSQL cross-région (ADR-022) converge dans un délai documenté | Rapport de mesure de convergence |
| ACC-TERR-P6-04 | Un cas de territoire à cheval entre deux régions est résolu sans conflit d'autorité non tracé | Rapport de test dédié (TERR-P6-005) |

---

## 4. Critères Phase 7 (mesh national)

| ID | Critère | Preuve attendue |
|---|---|---|
| ACC-TERR-P7-01 | L'orchestrateur territorial alloue dynamiquement des cellules selon la charge opérationnelle observée | Rapport de scénario de charge |
| ACC-TERR-P7-02 | La supervision globale reflète l'état de tous les niveaux actifs sans donnée manquante | Capture du tableau de bord de supervision |
| ACC-TERR-P7-03 | Un scénario de crise multi-départementale est exécuté sans dégradation de traçabilité | Rapport de scénario, journal d'audit complet |
| ACC-TERR-P7-04 | La compatibilité UE6 est démontrée sur un composant représentatif sans modification des interfaces du mesh | Rapport de validation de compatibilité |

---

## 5. Critères Phase 8 (edge production)

| ID | Critère | Preuve attendue |
|---|---|---|
| ACC-TERR-P8-01 | Une sous-cellule edge fonctionne en autonomie complète pendant une durée définie sans connectivité | Rapport de test offline |
| ACC-TERR-P8-02 | La resynchronisation après reconnexion s'effectue sans perte ni conflit non résolu | Rapport de resynchronisation |
| ACC-TERR-P8-03 | La synchronisation différentielle réduit mesurablement le volume de données transférées par rapport à une synchronisation complète | Rapport de mesure comparatif |

---

## 6. Non-régression Phase 4

Aucun critère ci-dessus n'est considéré satisfait si sa mise en œuvre a provoqué l'une des régressions suivantes, à vérifier avant toute clôture de phase :

- Dégradation de performance ou de disponibilité du Hub UE5.8 en production.
- Modification non tracée d'un contrat d'interface d'un moteur GSIE existant.
- Interruption ou ralentissement constaté du développement des 14 moteurs GSIE, de l'API GSIE ou des applications clientes (GeoSylva, Ignis) sans décision explicite du Fondateur.
