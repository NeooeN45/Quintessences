# GSIE Territorial Mesh — Roadmap dédiée

| Champ | Valeur |
|---|---|
| **Chantier** | GSIE Territorial Mesh — couche logique de gouvernance territoriale |
| **Phase** | 4 — Implémentation (cadrage des Phases 5 à 9) |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 (Territorial Mesh), RFC-0035 (Server Meshing, couche d'exécution sous-jacente) |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Documents apparentés** | `TERRITORIAL_MESH_BACKLOG.md`, `TERRITORIAL_MESH_ADR.md`, `TERRITORIAL_MESH_PROTOTYPE_V0.md`, `SERVER_MESHING_ROADMAP.md`, `ROADMAP.md` (roadmap globale du projet) |

---

## 1. Mission du document

Fixer le phasage indicatif du chantier GSIE Territorial Mesh, tel qu'annoncé par GSIE-DIR-0013, sans engagement de calendrier daté. Le Territorial Mesh est une **couche logique de gouvernance** superposée au Server Meshing (RFC-0035) : là où le Server Meshing organise l'exécution technique (serveurs de zone, autorité de rendu, streaming), le Territorial Mesh organise la **hiérarchie administrative et opérationnelle** (France → Région → Département → Territoire Opérationnel → Cellule Spatiale → Sous-cellule) et ses états (Froid, Chaud, Opérationnel, Crise). Ce document ne remplace pas `ROADMAP.md` : il en est un chantier annexe, sans impact sur les priorités Phase 4 en cours (14 moteurs, API GSIE, Hub UE5.8, GeoSylva, Ignis).

---

## 2. Relation avec la Phase 4 courante

La Phase 4 n'est pas interrompue par ce chantier. Elle prépare déjà le terrain du mesh territorial par des choix acquis ou recommandés à l'implémentation en cours :

| Préparation en Phase 4 | Bénéfice pour le mesh territorial futur |
|---|---|
| Spécification du modèle territorial administratif | Définir une entité `TerritorialAdministrativeUnit` distincte ou une correspondance avec le modèle forestier/cadastral `AdministrativeUnitModel`, sans fusion implicite des référentiels (voir ADR-028 et `TERRITORIAL_MESH_BACKLOG.md`). |
| RBAC existant (API GSIE) | Base à étendre en RBAC territorial scopé par périmètre (voir ADR-026). |
| Outbox/inbox transactionnel (ADR-005) | Fondation directement réutilisable pour le bus d'événements fédéré multi-niveaux (voir ADR-023). |
| Interfaces abstraites de compatibilité UE6 (ADR-015, Server Meshing) | Modèle repris pour découpler la gouvernance territoriale de son exécution technique (voir D5, ADR-021). |
| Capsule territoriale signée (ADR-008) | Base expérimentale réutilisée ; toute extension de schéma est additive, versionnée et soumise à validation (voir ADR-024). |

Ces préparations ne doivent pas interrompre les priorités de Phase 4. Elles nécessitent toutefois du cadrage documentaire et des validations ciblées, notamment TERR-T-001 ; aucune migration de modèle ou activation du RBAC territorial n'est autorisée avant validation des spécifications correspondantes.

---

## 3. Phasage

### Phase 5 — Prototype v0 Nouvelle-Aquitaine

| Champ | Détail |
|---|---|
| **Objectifs** | Valider la hiérarchie NCP (optionnel) → RCH → DOD → Cellule sur un périmètre restreint et réel ; valider le State Fabric fédéré (PostgreSQL + Redis + capsules ADR-008) ; valider le bus d'événements fédéré ; mesurer les latences de handoff. |
| **Livrables** | RCH Nouvelle-Aquitaine, DOD Charente (16), DOD Deux-Sèvres (79), 2 cellules spatiales, 1 drone edge traversant, simulation IGNIS simplifiée, scénario arrêt/redémarrage, rapport de mesure de latence. |
| **Prérequis** | Validation de RFC-0036 et de `TERRITORIAL_MESH_PROTOTYPE_V0.md` par le Fondateur (passage Draft → Validated), spécification du modèle administratif territorial (TERR-T-001) et validation de l'ADR-008 expérimental pour le périmètre de preuve. |
| **Critères de sortie** | Les critères de succès du prototype v0 sont satisfaits (`TERRITORIAL_MESH_PROTOTYPE_V0.md` §9), ou les écarts sont documentés et acceptés par le Fondateur. |
| **Dépendances** | Server Meshing prototype v0 (Landiras) fonctionnel ou en cours de validation, PostgreSQL, Redis, capsules ADR-008. |
| **Risques** | Sous-estimation de la fédération multi-niveaux (RISK-TERR-001) ; dérive vers un serveur national monolithique (RISK-TERR-002). |

### Phase 6 — Extension multi-régions, fédération NCP complète

| Champ | Détail |
|---|---|
| **Objectifs** | Étendre le mesh territorial à une seconde région ; valider la fédération NCP complète (national) ; implémenter et tester le handoff inter-régional. |
| **Livrables** | 2e RCH activée, fédération NCP opérationnelle sur 2 régions, protocole de handoff inter-régional, réplication PostgreSQL cross-région (ADR-022). |
| **Prérequis** | Phase 5 clôturée (critères de sortie satisfaits) ; ADR-022 validé. |
| **Critères de sortie** | Un handoff inter-régional s'exécute sans perte de données ni incohérence d'état, sur un scénario reproductible. |
| **Dépendances** | Phase 5, mTLS multi-niveaux (voir ADR-017 réutilisé), RBAC territorial (ADR-026). |
| **Risques** | Autorités concurrentes sur territoire transfrontalier (RISK-TERR-003) ; conflit de synchronisation edge→DOD (RISK-TERR-010). |

### Phase 7 — Mesh national, concentration dynamique territoriale, validation UE6

| Champ | Détail |
|---|---|
| **Objectifs** | Étendre le mesh territorial à l'échelle nationale ; implémenter la concentration dynamique de cellules par charge opérationnelle ; valider la neutralité vis-à-vis d'UE6 (D7, ADR-015). |
| **Livrables** | NCP national opérationnel, orchestrateur territorial (allocation dynamique de cellules), tableau de bord de supervision globale, validation de compatibilité UE6 sur un composant représentatif. |
| **Prérequis** | Phase 6 clôturée ; clarification du statut UE6. |
| **Critères de sortie** | Le mesh national fonctionne avec au moins un scénario de charge réelle (exemple : crise multi-départementale) sans dégradation de traçabilité. |
| **Dépendances** | Phase 6, infrastructure d'observabilité distribuée, ADR-025 (états opérationnels comme signal de gouvernance). |
| **Risques** | Sur-ingénierie (RISK-TERR-013) ; coûts d'infrastructure par niveau (RISK-TERR-006). |

### Phase 8 — Edge nodes production

| Champ | Détail |
|---|---|
| **Objectifs** | Passer les capsules territoriales (ADR-008, ADR-024) en production sur les cellules et sous-cellules ; implémenter la synchronisation différentielle ; valider le mode offline complet. |
| **Livrables** | Capsules edge en production, mécanisme de synchronisation différentielle, plan de test offline complet, documentation opérationnelle terrain. |
| **Prérequis** | Phase 7 clôturée ; ADR-008 et son schéma de capsule validés pour la production, rotation/révocation des clés spécifiée et testée. |
| **Critères de sortie** | Une sous-cellule edge fonctionne en autonomie complète pendant une durée définie sans connectivité, puis se resynchronise sans perte ni conflit non résolu. |
| **Dépendances** | Phase 7, ADR-019 (offline-first, Server Meshing) réutilisé et étendu. |
| **Risques** | Cas offline mal couverts (RISK-TERR-008) ; conflit de synchronisation edge→DOD (RISK-TERR-010). |

### Phase 9 — Fédération cross-pays (hors scope actuel)

Mention pour mémoire uniquement. La fédération territoriale au-delà des frontières nationales françaises n'est **pas planifiée** dans le périmètre actuel de RFC-0036 et de GSIE-DIR-0013. Toute évolution vers ce périmètre nécessiterait une nouvelle RFC et une décision tracée dédiée, sans lien de dépendance implicite avec les phases 5 à 8.

---

## 4. Tableau de dépendances entre phases

| Phase | Dépend de | Bloque |
|---|---|---|
| Phase 5 | Validation de RFC-0036 et `TERRITORIAL_MESH_PROTOTYPE_V0.md` | Phase 6 |
| Phase 6 | Phase 5 clôturée + ADR-022 validé | Phase 7 |
| Phase 7 | Phase 6 clôturée + clarification UE6 | Phase 8 |
| Phase 8 | Phase 7 clôturée + ADR-019 étendu | Cible long terme (Phase 9 hors scope) |
| Phase 9 | Hors scope — aucune dépendance planifiée | — |

---

## 5. Indicateurs de progression (KPI techniques)

| Indicateur | Phase de référence | Cible indicative |
|---|---|---|
| Taux de perte de données lors d'un handoff inter-cellules | Phase 5 | 0 % (aucune perte tolérée) |
| Latence de handoff inter-niveaux (détection → bascule confirmée) | Phase 5 → 6 | À affiner à l'issue du prototype ; objectif qualitatif : imperceptible en usage opérationnel |
| Nombre de DOD actifs simultanément dans le mesh | Phase 5 → 7 | 2 (Phase 5) → national (Phase 7) |
| Temps de resynchronisation après reconnexion edge | Phase 8 | Suivi, cible affinée après premiers tests |
| Couverture des scénarios de partition réseau testés | Phase 5 → 8 | Croissante, aucun scénario critique non testé avant passage de phase |

Ces indicateurs sont indicatifs et seront affinés lors de la spécification technique de chaque phase — ils ne constituent pas des engagements contractuels au stade Draft.

---

## 6. Critères de décision « passer à la phase suivante »

Le passage d'une phase à la suivante n'est jamais automatique. Il requiert :

1. **Les critères de sortie de la phase courante sont satisfaits**, tels que documentés au §3, ou les écarts sont explicitement acceptés par le Fondateur et tracés (DEC-xxxxxx).
2. **Aucune régression** sur les principes P-TERR-01 à P-TERR-10 (RFC-0036) n'a été constatée pendant la phase courante.
3. **Aucun impact non maîtrisé sur les priorités Phase 4** en cours — le Territorial Mesh reste un chantier annexe qui ne doit pas absorber les ressources critiques des 14 moteurs, de l'API GSIE et des applications clientes sans décision explicite du Fondateur.
4. **Une décision tracée** (DEC-xxxxxx) ouvre formellement la phase suivante, à l'image de DEC-000054 pour l'ouverture du chantier global.

---

## 7. Ce que ce document n'est pas

- Ce n'est pas un engagement de date — le phasage est indicatif ; `ROADMAP.md` reste l'unique référence de calendrier daté du projet.
- Ce n'est pas une autorisation de démarrage de la Phase 5 — celle-ci requiert la validation préalable de RFC-0036 et de `TERRITORIAL_MESH_PROTOTYPE_V0.md` par le Fondateur.
- Ce n'est pas une modification du contrat d'interface d'un moteur GSIE existant — toute évolution de ce type suit la procédure RFC (voir `GSIE/ENGINES/<NOM>_ENGINE/README.md`).
- Ce n'est pas une fusion du Territorial Mesh et du Server Meshing — les deux chantiers restent orthogonaux (voir ADR-021).
