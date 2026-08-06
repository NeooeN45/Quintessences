# GSIE Server Meshing — Roadmap dédiée

| Champ | Valeur |
|---|---|
| **Chantier** | GSIE Server Meshing — Vague 2 (architecture / roadmap) |
| **Phase** | 4 — Implémentation (cadrage des Phases 5 à 7) |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **Auteur** | Camille Perraudeau (Fondateur) — instruit par agent architecte |
| **Lois fondatrices** | GSIE-CON-000, GSIE-CON-003, GSIE-CON-007, GSIE-CON-010 |
| **RFC liée** | RFC-0035, RFC-0003 (GSIE-Net), RFC-0011 (métamodèle v6.2) |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Documents apparentés** | `SERVER_MESHING_TARGET.md`, `SERVER_MESHING_PROTOTYPE_V0.md`, `ROADMAP.md` (roadmap globale du projet) |

---

## 1. Mission du document

Fixer le phasage indicatif du chantier GSIE Server Meshing, tel
qu'annoncé par GSIE-DIR-0012 §« Phasage indicatif », sans engagement
de calendrier daté. Ce document ne remplace pas `ROADMAP.md` (roadmap
globale du projet) : il en est un chantier annexe, sans impact sur les
priorités Phase 4 en cours (14 moteurs, API GSIE, Hub UE5.8, GeoSylva,
Ignis — DEC-000053 §4).

---

## 2. Relation avec la Phase 4 courante

La Phase 4 n'est pas interrompue par ce chantier. Elle prépare
toutefois le terrain du mesh par les choix suivants, déjà appliqués ou
recommandés à l'implémentation en cours :

| Préparation en Phase 4 | Bénéfice pour le mesh futur |
|---|---|
| Interfaces abstraites pour les moteurs (livrable 203, contrats `GSIE/ENGINES/*/README.md`) | Permettent l'hébergement futur par des serveurs spécialisés sans refonte. |
| CRUD générique API GSIE (ADR-007) | Base de persistance déjà compatible avec une extension au graphe d'autorité et au journal d'audit du mesh. |
| Métamodèle v6.2 bitemporel (RFC-0011) | Fournit nativement la structure de persistance externe requise par P-MESH-02. |
| Authentification JWT (ADR-007) | Réutilisable directement pour l'authentification opérateur du mesh (§sécurité, `SERVER_MESHING_TARGET.md` §11). |
| Hub UE5.8 en client léger, non source de vérité (ADR-001 livrable 208) | Principe déjà acté ; le mesh le renforce sans le contredire. |

Aucune de ces préparations ne requiert de développement dédié
supplémentaire en Phase 4 au-delà des bonnes pratiques déjà en vigueur
(interfaces claires, séparation domaine/infrastructure).

---

## 3. Phasage

### Phase 5 — Prototype v0 Landiras

| Champ | Détail |
|---|---|
| **Objectifs** | Valider persistance externe, autorité unique, streaming par pertinence, reconnexion après panne, sur une zone mono-région (voir `SERVER_MESHING_PROTOTYPE_V0.md`). |
| **Livrables** | ZoneServer minimal, graphe d'autorité simple, extension persistance, Hub UE5.8 modifié, plan de validation exécuté. |
| **Prérequis** | Validation de `SERVER_MESHING_TARGET.md` et `SERVER_MESHING_PROTOTYPE_V0.md` par le Fondateur (passage Draft → Validated). |
| **Critères de sortie** | Les cinq critères de succès du prototype v0 sont satisfaits (`SERVER_MESHING_PROTOTYPE_V0.md` §10), ou les écarts sont documentés et acceptés par le Fondateur. |
| **Dépendances** | API GSIE existante, PostgreSQL/PostGIS, Redis, Hub UE5.8. |
| **Risques** | Sous-estimation de l'effort d'adaptation du Hub ; risque de dérive de périmètre vers des fonctionnalités exclues du v0 (§6 du document prototype). |

### Phase 6 — Extension multi-régions, handoff d'autorité

| Champ | Détail |
|---|---|
| **Objectifs** | Étendre le mesh à au moins deux régions ; implémenter et valider le protocole de transfert d'autorité (`SERVER_MESHING_TARGET.md` §6) ; introduire un orchestrateur de mesh minimal. |
| **Livrables** | Orchestrateur de mesh (v1, sans partitionnement dynamique), deuxième ZoneServer, protocole de handoff opérationnel, service discovery multi-nœuds, journal d'audit étendu. |
| **Prérequis** | Phase 5 clôturée (critères de sortie satisfaits) ; ADR sur le transport inter-nœuds (annoncé `SERVER_MESHING_TARGET.md` §15). |
| **Critères de sortie** | Un transfert d'autorité entre deux régions s'exécute sans perte de données ni coupure visible côté opérateur, sur un scénario de test reproductible. |
| **Dépendances** | Phase 5, infrastructure mTLS inter-nœuds, extension du graphe d'autorité au cas bidimensionnel (zone + type) si un serveur spécialisé est introduit à ce stade. |
| **Risques** | Complexité de résolution de conflit zone/type sous-estimée ; risque de latence de handoff dégradant l'expérience opérateur ; risque de partition réseau non testée en conditions réelles. |

### Phase 7 — Mesh national, concentration dynamique, UE6

| Champ | Détail |
|---|---|
| **Objectifs** | Étendre le mesh à l'échelle nationale ; implémenter le partitionnement spatial dynamique et la concentration dynamique de ressources (P-MESH-04) ; valider la neutralité de moteur de rendu par une implémentation ou un test de compatibilité UE6. |
| **Livrables** | Orchestrateur de mesh complet (redécoupage adaptatif, allocation de ressources), tableau de bord d'observabilité mesh, validation de `IRenderClient` sur un second moteur de rendu (UE6 ou CesiumJS web). |
| **Prérequis** | Phase 6 clôturée ; disponibilité confirmée d'une cible UE6 ou d'une alternative de validation de neutralité (CesiumJS web). |
| **Critères de sortie** | Le mesh national fonctionne avec redécoupage automatique observé sur au moins un scénario de charge réelle (exemple : alerte incendie) ; la neutralité de rendu est démontrée sans modification des interfaces du mesh. |
| **Dépendances** | Phase 6, disponibilité ou clarification du statut d'UE6, infrastructure d'observabilité distribuée. |
| **Risques** | Dépendance non anticipée à des primitives UE6 non confirmées (mitigé par l'absence de dépendance hard, `SERVER_MESHING_TARGET.md` §14) ; risque d'oscillation du partitionnement dynamique (anti-flapping insuffisant) ; risque de dérive de coût d'infrastructure à l'échelle nationale. |

---

## 4. Tableau de dépendances entre phases

| Phase | Dépend de | Bloque |
|---|---|---|
| Phase 5 | Validation de `SERVER_MESHING_TARGET.md` et `SERVER_MESHING_PROTOTYPE_V0.md` | Phase 6 |
| Phase 6 | Phase 5 clôturée + ADR transport inter-nœuds | Phase 7 |
| Phase 7 | Phase 6 clôturée + clarification UE6 | Cible long terme (aucune phase suivante définie) |

---

## 5. Indicateurs de progression (KPI techniques)

| Indicateur | Phase de référence | Cible indicative |
|---|---|---|
| Taux de perte de données après panne serveur | Phase 5 | 0 % (aucune perte tolérée, P-MESH-02) |
| Latence de handoff (détection → bascule confirmée) | Phase 6 | À définir lors de l'ADR transport ; objectif qualitatif : imperceptible pour l'opérateur |
| Nombre de régions actives simultanément dans le mesh | Phase 6 → 7 | 2 (Phase 6) → national (Phase 7) |
| Taux de redécoupages annulés pour oscillation (anti-flapping) | Phase 7 | Suivi, pas de cible numérique fixée a priori |
| Couverture des scénarios de partition réseau testés | Phase 6 → 7 | Croissante, aucun scénario critique non testé avant passage en Phase 7 |

Ces indicateurs sont indicatifs et seront affinés lors de la
spécification technique de chaque phase — ils ne constituent pas des
engagements contractuels au stade Draft.

---

## 6. Critères de décision « passer à la phase suivante »

Le passage d'une phase à la suivante n'est jamais automatique. Il
requiert :

1. **Les critères de sortie de la phase courante sont satisfaits**,
   tels que documentés au §3, ou les écarts sont explicitement
   acceptés par le Fondateur et tracés (DEC-xxxxxx).
2. **Aucune régression** sur les principes fondateurs (GSIE-DIR-0012
   §huit principes) n'a été constatée pendant la phase courante.
3. **Aucun impact non maîtrisé sur les priorités Phase 4** en cours
   au moment de la décision (DEC-000053 §4) — le mesh reste un
   chantier qui ne doit pas absorber les ressources critiques des 14
   moteurs, de l'API GSIE et des applications clientes sans décision
   explicite du Fondateur.
4. **Une décision tracée** (DEC-xxxxxx) ouvre formellement la phase
   suivante, à l'image de DEC-000053 pour l'ouverture du chantier
   global.

---

## 7. Ce que ce document n'est pas

- Ce n'est pas un engagement de date — le phasage est indicatif, la
  roadmap globale (`ROADMAP.md`) reste l'unique référence de
  calendrier daté du projet.
- Ce n'est pas une autorisation de démarrage de la Phase 5 — celle-ci
  requiert la validation préalable de `SERVER_MESHING_TARGET.md` et
  `SERVER_MESHING_PROTOTYPE_V0.md` par le Fondateur.
- Ce n'est pas une modification de la roadmap Phase 4 courante — voir
  §2 pour la relation exacte.
