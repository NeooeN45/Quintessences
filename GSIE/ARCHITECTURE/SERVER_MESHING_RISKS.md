# SERVER MESHING — Registre de risques

| Champ | Valeur |
|---|---|
| **Document** | Registre de risques — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Portée** | Ce registre détaille et complète le tableau de risques préliminaire de RFC-0035 §8. Il couvre l'ensemble du chantier Server Meshing, du prototype mono-région (Landiras) à l'extension multi-régions. |

## Échelle utilisée

**Sévérité** : Critique / Élevée / Moyenne / Faible
**Probabilité** : Élevée / Moyenne / Faible

---

## Registre des risques

| ID | Description | Sévérité | Probabilité | Impact | Mitigation | Propriétaire | Statut |
|---|---|---|---|---|---|---|---|
| RISK-MESH-001 | Complexité du transfert d'autorité (handoff) entre serveurs de zone lors du franchissement d'une frontière | Élevée | Élevée | Coupure ou incohérence visible pour l'opérateur, perte d'autorité d'une entité pendant la transition | Prototype mono-région d'abord (aucun handoff réel requis) ; extension progressive à deux régions dédiée à valider spécifiquement le handoff ; journal d'audit obligatoire pour chaque transfert (P-MESH-06) | Architecte GSIE | Ouvert |
| RISK-MESH-002 | Conflits de réplication multi-serveurs sur une même entité (écritures concurrentes) | Élevée | Moyenne | État divergent entre serveurs, décision fondée sur une donnée incorrecte | Bitemporalité du métamodèle v6.2 (ADR-014) ; règles de résolution par domaine documentées avant activation de tout second serveur | Architecte GSIE | Ouvert |
| RISK-MESH-003 | Partition réseau entre serveurs (théorème CAP) | Moyenne | Moyenne | Divergence temporaire d'état, risque de décision opérateur sur donnée obsolète | Mode dégradé offline-first documenté (ADR-019) ; réconciliation bitemporelle au retour de connectivité | Architecte GSIE | Ouvert |
| RISK-MESH-004 | Sur-ingénierie avant besoin réel démontré | Moyenne | Élevée | Effort de développement détourné des priorités Phase 4 (14 moteurs, API, Hub, GeoSylva, Ignis) sans bénéfice opérationnel immédiat | Phasage strict (RFC-0035 §5.2) ; aucun mesh multi-serveurs avant saturation démontrée d'une région unique ; revue de gating avant chaque extension de périmètre | Fondateur | Ouvert |
| RISK-MESH-005 | Coût d'infrastructure croissant avec le nombre de serveurs de zone et spécialisés | Moyenne | Moyenne | Dépassement budgétaire, dépendance à des ressources cloud non provisionnées | Concentration dynamique des ressources comme levier d'optimisation (P-MESH-04) ; suivi de coût par région dès le prototype | Fondateur | Ouvert |
| RISK-MESH-006 | Dépendance implicite à UE6 non livré ou incompatible avec les hypothèses d'abstraction retenues | Faible | Faible | Retard de migration du client de rendu, refonte de l'interface abstraite | Compatibilité UE6 anticipée par interfaces abstraites (ADR-015), sans dépendance hard ; UE5.8 reste l'implémentation de référence | Architecte GSIE | Ouvert |
| RISK-MESH-007 | Latence inter-nœuds dégradant la continuité spatiale perçue par l'opérateur | Moyenne | Moyenne | Coupure ou saccade visible lors d'un déplacement traversant une frontière de serveur, contredisant P-MESH-01 | Réplication par pertinence (ADR-012) pour limiter le volume ; tests de latence dès le prototype à deux régions | Backend | Ouvert |
| RISK-MESH-008 | Surface d'attaque accrue par la multiplication des nœuds du mesh | Élevée | Faible | Compromission d'un serveur exposant l'ensemble du graphe d'autorité | mTLS obligatoire inter-nœuds (ADR-017) ; rotation de certificats ; revue de sécurité avant tout déploiement multi-régions | Sécurité GSIE | Ouvert |
| RISK-MESH-009 | Perte de traçabilité lors d'une décision automatique du mesh (redécoupage, transfert, allocation) | Critique | Faible | Décision de mesh non explicable, contradiction avec CON-005/CON-010 et P-MESH-06 | Journal d'audit immuable obligatoire pour toute décision de mesh ; identifiant traçable par transfert d'autorité ; revue de conformité avant activation en production | Qualité GSIE | Ouvert |
| RISK-MESH-010 | Scalabilité limitée de l'orchestrateur centralisé au-delà d'un certain nombre de régions | Moyenne | Faible | Goulot d'étranglement, latence de décision de mesh croissante | Clause de réévaluation explicite (ADR-016) ; métriques de charge de l'orchestrateur suivies dès le prototype | Architecte GSIE | Ouvert |
| RISK-MESH-011 | Migration de données existantes (Hub UE5.8 monolithique) vers le modèle mesh sans perte ni corruption | Élevée | Moyenne | Perte d'historique, incohérence entre l'état pré-mesh et post-mesh | Persistance externe déjà en place comme base de départ (ADR-011) ; plan de migration dédié avant toute bascule en production | Backend | Ouvert |
| RISK-MESH-012 | Manque de formation de l'équipe aux concepts de mesh distribué (autorité, handoff, bitemporalité appliquée à la réplication) | Moyenne | Moyenne | Erreurs d'implémentation, dette technique, contournements informels de la gouvernance | Documentation dédiée (registre ADR, diagrammes) ; revue de code obligatoire sur tout composant de mesh | Architecte GSIE | Ouvert |
| RISK-MESH-013 | Régression de performance du Hub UE5.8 actuel pendant la transition vers un client de mesh | Élevée | Moyenne | Dégradation de l'expérience opérateur en salle de commandement, alors que le Hub est en production | Migration incrémentale (le Hub reste fonctionnel en mode mono-serveur pendant tout le prototype) ; tests de non-régression de performance avant chaque bascule | Unreal | Ouvert |
| RISK-MESH-014 | Gouvernance multi-régions insuffisamment définie (qui décide en cas de conflit inter-régions, priorité opérationnelle) | Moyenne | Moyenne | Blocage de décision ou arbitrage informel non traçable en situation de crise multi-régions | Table de priorité documentée dès l'extension à deux régions (ADR-010) ; RFC dédiée si un arbitrage inter-régions structurant apparaît | Fondateur | Ouvert |
| RISK-MESH-015 | Dépendances externes (PostgreSQL, Redis, Cesium for Unreal) non disponibles ou dégradées en production | Moyenne | Faible | Indisponibilité partielle du mesh, mode dégradé prolongé | Mode dégradé offline-first (ADR-019) ; suivi de disponibilité des dépendances ; pas de nouvelle dépendance externe introduite sans ADR (ADR-013) | Backend | Ouvert |
| RISK-MESH-016 | Dérive de périmètre du prototype mono-région vers un mesh multi-serveurs non planifié | Moyenne | Moyenne | Reproduction du risque de sur-ingénierie (RISK-MESH-004) par extension informelle plutôt que par décision tracée | Critères de passage explicites entre prototype v0 et v1 documentés dans la roadmap dédiée ; toute extension de périmètre nécessite une décision tracée | Fondateur | Ouvert |

---

## Matrice sévérité × probabilité

```
                    PROBABILITÉ
                Faible      Moyenne      Élevée
            ┌───────────┬───────────┬───────────┐
 Critique   │           │           │  RISK-009 │
            │           │           │ (proba    │
            │           │           │  réévaluée│
            │           │           │  faible)  │
            ├───────────┼───────────┼───────────┤
 Élevée     │ RISK-008  │ RISK-002  │ RISK-001  │
            │           │ RISK-011  │           │
            │           │ RISK-013  │           │
            ├───────────┼───────────┼───────────┤
 Moyenne    │ RISK-010  │ RISK-003  │ RISK-004  │
            │ RISK-015  │ RISK-005  │           │
            │           │ RISK-007  │           │
            │           │ RISK-012  │           │
            │           │ RISK-014  │           │
            │           │ RISK-016  │           │
            ├───────────┼───────────┼───────────┤
 Faible     │ RISK-006  │           │           │
            └───────────┴───────────┴───────────┘
```

Note de lecture : RISK-MESH-009 (perte de traçabilité) est classé en
sévérité Critique en raison de l'incompatibilité directe avec CON-005
et CON-010 en cas de survenance, malgré une probabilité estimée faible
grâce aux mitigations déjà intégrées à la conception (ADR-014, ADR-016).
Un risque Critique reste suivi indépendamment de sa probabilité.

---

## Top 5 des risques à surveiller en priorité

1. **RISK-MESH-009** — Perte de traçabilité lors d'une décision automatique
   du mesh. Sévérité Critique : toute survenance contredit directement
   la Constitution (CON-005, CON-010). Surveillance continue du journal
   d'audit dès la première décision d'orchestrateur.
2. **RISK-MESH-001** — Complexité du handoff d'autorité. Risque le plus
   probable et le plus structurant pour la validité du pattern de mesh ;
   condition de passage du prototype v0 (mono-région) au prototype v1
   (deux régions).
3. **RISK-MESH-004** — Sur-ingénierie avant besoin réel. Risque
   transverse à tout le chantier ; sa maîtrise conditionne la
   préservation des priorités Phase 4 en cours.
4. **RISK-MESH-002** — Conflits de réplication multi-serveurs. Risque
   technique central dès l'introduction d'un second serveur de zone ;
   directement lié à la validité d'ADR-014.
5. **RISK-MESH-013** — Régression de performance du Hub UE5.8 actuel.
   Le Hub est en production ; toute dégradation perçue par l'opérateur
   pendant la transition menace l'adoption du chantier au-delà de sa
   justification technique.

---

## Stratégie de revue des risques

### Fréquence

- **Revue légère** : à chaque fin de vague du chantier Server Meshing
  (Vague 1, 2, 3 — voir `SERVER_MESHING_ROADMAP.md`), pour
  mettre à jour statut, sévérité et probabilité de chaque risque.
- **Revue complète** : avant toute extension de périmètre structurante
  (passage du prototype v0 mono-région au prototype v1 multi-régions ;
  passage du prototype v1 à un déploiement multi-régions opérationnel).

### Déclencheurs de revue immédiate (hors cycle planifié)

- Survenance effective d'un risque classé Élevée ou Critique.
- Toute décision (DEC-xxxxxx) modifiant un principe fondateur P-MESH-01
  à P-MESH-08.
- Tout changement de statut d'une dépendance externe listée
  (RFC-0035 §6.3) : API GSIE, métamodèle v6.2, GSIE-Net, PostgreSQL,
  Cesium for Unreal, Redis Pub/Sub.
- Toute proposition de RFC modifiant un ADR du registre
  `SERVER_MESHING_ADR.md`.

### Propriétaires et responsabilité

Chaque risque a un propriétaire nommé (rôle, pas nécessairement une
personne unique) responsable de proposer une mise à jour de statut à
chaque revue. Le Fondateur conserve l'autorité finale sur
l'acceptation d'un risque résiduel non mitigé.

### Traçabilité des revues

Toute mise à jour de ce registre issue d'une revue est mentionnée dans
`PROJECT_MEMORY.md` si elle change le statut d'un risque classé Élevée
ou Critique, conformément à la règle de traçabilité transverse du
projet.
