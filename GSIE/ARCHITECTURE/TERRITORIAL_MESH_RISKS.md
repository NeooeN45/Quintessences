# GSIE Territorial Mesh — Registre de risques

| Champ | Valeur |
|---|---|
| **Document** | Registre de risques — GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Portée** | Ce registre couvre l'ensemble du chantier Territorial Mesh, du prototype v0 Nouvelle-Aquitaine à l'edge en production. Il complète, sans le dupliquer, `SERVER_MESHING_RISKS.md` (couche d'exécution technique sous-jacente). |

---

## 1. Méthodologie

**Sévérité** : Critique / Élevée / Moyenne / Faible
**Probabilité** : Élevée / Moyenne / Faible
**Mitigation** : mesure(s) déjà décidée(s) ou recommandée(s), avec référence à l'ADR ou au principe applicable.
**Propriétaire** : rôle responsable du suivi du risque (non une personne nommée).

Un risque reste enregistré même après mitigation ; son statut n'est clos que sur décision tracée constatant sa disparition effective.

---

## 2. Registre des risques

| ID | Description | Sévérité | Probabilité | Impact | Mitigation | Propriétaire | Statut |
|---|---|---|---|---|---|---|---|
| RISK-TERR-001 | Sous-estimation de la complexité de fédération à plusieurs niveaux hiérarchiques (national/régional/départemental/territoire/cellule/sous-cellule) | Critique | Élevée | Retards en cascade, architecture instable dès la Phase 5 | Prototype v0 volontairement restreint à 3 niveaux effectifs (RCH/DOD/cellule), NCP simulé (D1) ; extension progressive et tracée par phase | Architecte GSIE | Ouvert |
| RISK-TERR-002 | Dérive de conception vers un serveur national monolithique masquant la hiérarchie territoriale | Élevée | Moyenne | Perte de la modularité requise par CON-007 et P-TERR (autorité unique par périmètre) | Autorité unique par périmètre actée (ADR-027) ; revue d'architecture avant toute centralisation excessive du NCP | Architecte GSIE | Ouvert |
| RISK-TERR-003 | Autorités concurrentes sur un territoire à cheval entre deux périmètres (région, département) | Élevée | Moyenne | Incohérence de décision opérationnelle, conflit de résolution non tracé | Table de correspondance frontières scientifiques/administratives (ADR-028) ; test dédié en Phase 6 (TERR-P6-005) | Architecte GSIE | Ouvert |
| RISK-TERR-004 | Complexité distribuée introduite sans besoin réel démontré | Moyenne | Élevée | Effort détourné des priorités Phase 4 sans bénéfice opérationnel | Phasage strict (`TERRITORIAL_MESH_ROADMAP.md` §3) ; aucune extension de périmètre sans critère de sortie satisfait | Fondateur | Ouvert |
| RISK-TERR-005 | Perte de traçabilité ou double écriture lors d'une transition d'état ou d'un handoff multi-niveaux | Critique | Faible | Décision opérationnelle non explicable, deux autorités écrivant simultanément, contradiction avec CON-005/CON-010 | Journal d'audit obligatoire, jetons idempotents et epoch de fencing pour chaque handoff/transition (ADR-025) ; capsules et signatures d'appareil (ADR-008/024) | Qualité GSIE | Ouvert |
| RISK-TERR-006 | Coûts d'infrastructure croissants avec le nombre de niveaux et de nœuds actifs | Moyenne | Moyenne | Dépassement budgétaire à l'échelle nationale | Suivi de coût par niveau dès le prototype ; concentration dynamique territoriale comme levier d'optimisation (Phase 7) | Fondateur | Ouvert |
| RISK-TERR-007 | Sécurité insuffisante entre niveaux hiérarchiques (mTLS, RBAC territorial) | Élevée | Moyenne | Compromission d'un niveau exposant les niveaux supérieurs ou inférieurs | mTLS inter-niveaux réutilisé (ADR-017, Server Meshing) ; RBAC territorial scopé par périmètre (ADR-026) | Sécurité GSIE | Ouvert |
| RISK-TERR-008 | Cas offline mal couverts pour les cellules et sous-cellules edge | Moyenne | Moyenne | Perte ou incohérence de données lors d'une coupure réseau prolongée | Capsules territoriales signées (ADR-008/024) ; scénarios offline dédiés en Phase 8 | Backend | Ouvert |
| RISK-TERR-009 | Régression du Hub UE5.8 en production pendant l'intégration de la couche territoriale | Élevée | Moyenne | Dégradation de l'expérience opérateur alors que le Hub est en service | Interfaces abstraites (ADR-015/021) découplant gouvernance et exécution ; non-régression testée avant chaque bascule | Unreal | Ouvert |
| RISK-TERR-010 | Conflit de synchronisation entre une cellule edge et son DOD de rattachement | Moyenne | Moyenne | Divergence d'état, décision fondée sur une donnée obsolète | Synchronisation différentielle (Phase 8), signature des observations, arbitrage explicite du DOD et conservation des révisions concurrentes ; PostgreSQL source de vérité, pas de fusion automatique (D3) | Backend | Ouvert |
| RISK-TERR-011 | Latence ou double prise en charge lors d'un handoff inter-niveaux | Moyenne | Moyenne | Coupure, retard perceptible ou deux cellules écrivant simultanément lors d'un déplacement | Mesure instrumentée dès le prototype (TERR-P5-008), jeton idempotent et epoch de fencing ; réplication ciblée par pertinence | Backend | Ouvert |
| RISK-TERR-012 | Partition réseau entre niveaux hiérarchiques | Moyenne | Moyenne | Divergence temporaire d'état, décision sur donnée obsolète | Mode dégradé offline-first (ADR-019 réutilisé) ; réconciliation au retour de connectivité | Architecte GSIE | Ouvert |
| RISK-TERR-013 | Sur-ingénierie de la hiérarchie territoriale (niveaux ou mécanismes non justifiés par un besoin réel) | Moyenne | Moyenne | Complexité non maîtrisée, dette technique, non-conformité au principe YAGNI | Périmètre du prototype v0 volontairement restreint (D1) ; critères de sortie explicites avant toute extension | Fondateur | Ouvert |
| RISK-TERR-014 | Dépendance prématurée à UE6 ou AWS avant confirmation de disponibilité | Faible | Faible | Refonte d'interface, retard de migration | Aucune dépendance hard (D7) ; interfaces abstraites (ADR-015) ; UE5.8 reste la référence d'implémentation | Architecte GSIE | Ouvert |
| RISK-TERR-015 | Frontières scientifiques (bassins versants, massifs forestiers) mal réconciliées avec les limites administratives (INSEE) | Moyenne | Moyenne | Incohérence entre le découpage opérationnel et le découpage administratif, double comptage ou zone orpheline | Table de correspondance dédiée, sans fusion forcée des deux référentiels (ADR-028) | Architecte GSIE | Ouvert |
| RISK-TERR-016 | Confusion de gouvernance entre Territorial Mesh et Server Meshing (chevauchement de responsabilités) | Moyenne | Moyenne | Duplication d'effort, incohérence de conception entre les deux chantiers | Orthogonalité actée et documentée (ADR-021) ; revue croisée avant toute évolution touchant les deux chantiers | Architecte GSIE | Ouvert |

---

## 3. Top 6 des risques à surveiller en priorité

1. **RISK-TERR-005** — Perte de traçabilité ou double écriture multi-niveaux. Sévérité Critique : toute survenance contredit directement CON-005 et CON-010. Surveillance continue du journal d'audit dès la première transition d'état du prototype.
2. **RISK-TERR-001** — Sous-estimation de la fédération multi-niveaux. Sévérité Critique et probabilité élevée : risque le plus structurant pour la tenue du phasage.
3. **RISK-TERR-010** — Conflits edge→DOD et arbitrage d'observations. Les signatures d'appareil et l'arbitrage explicite doivent être testés avant la production edge.
4. **RISK-TERR-002** — Dérive vers un serveur national monolithique. Contredit directement CON-007 (modularité) si non surveillé dès la conception du NCP.
5. **RISK-TERR-009** — Régression du Hub UE5.8. Le Hub reste en production pendant toute la durée du chantier ; aucune dégradation n'est tolérée sans décision explicite.
6. **RISK-TERR-003** — Autorités concurrentes sur territoire transfrontalier. Risque activé dès la Phase 6 (2e RCH), à traiter avant toute extension nationale.

---

## 4. Risques hors périmètre

Les risques suivants sont explicitement **hors périmètre** du présent registre, car hors du périmètre actuel de RFC-0036 et de GSIE-DIR-0013 :

- **Fédération cross-pays** — mentionnée pour mémoire en Phase 9 (`TERRITORIAL_MESH_ROADMAP.md` §3), aucune analyse de risque n'est requise avant l'ouverture d'une RFC dédiée.
- **IoT massif** (capteurs de terrain à grande échelle) — non couvert par le prototype v0 (1 seul drone edge) ; à analyser lors d'une extension future si décidée.
- **Keycloak ou tout fournisseur d'identité tiers** — le RBAC territorial (ADR-026) s'appuie sur le mécanisme d'authentification existant de l'API GSIE ; aucune dépendance à un fournisseur d'identité externe n'est planifiée.
