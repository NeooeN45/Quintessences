# GSIE Territorial Mesh — Registre des Architecture Decision Records

| Champ | Valeur |
|---|---|
| **Document** | Registre ADR — GSIE Territorial Mesh |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC liée** | RFC-0036 |
| **Directive liée** | GSIE-DIR-0013 |
| **Décision liée** | DEC-000054 |
| **Portée** | ADR-020 à ADR-028, dans la continuité numérique des ADR généraux (ADR-001 à ADR-009) et des ADR Server Meshing (ADR-010 à ADR-019). |

---

## Note de gouvernance

La numérotation des ADR du présent registre poursuit la séquence globale du projet, sans réutilisation ni collision avec les ADR déjà attribués (ADR-001 à ADR-019). Tout ADR listé ci-après reste au statut **Draft** jusqu'à validation par le Fondateur et n'engage aucune modification rétroactive des contrats d'interface des 14 moteurs GSIE sans RFC dédiée.

---

## ADR-020 — Hiérarchie territoriale configurable

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §3, P-TERR-01) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Le mesh territorial doit représenter une hiérarchie à six niveaux (France, Région, Département, Territoire Opérationnel, Cellule Spatiale, Sous-cellule) qui peut évoluer (redécoupages administratifs, ajustements opérationnels) sans nécessiter une modification de code.

### Décision

La hiérarchie territoriale est portée par des données de configuration versionnées, distinctes du code applicatif. Chaque niveau référence son niveau parent par un identifiant stable ; la configuration est validée dans un espace isolé puis activée de manière atomique. Un rechargement sans interruption n'est autorisé que si la validation (unicité, absence de boucle, couverture des périmètres et compatibilité de version) réussit ; sinon la version précédente reste active.

### Conséquences

**Positives** : évolution de la hiérarchie sans déploiement de code ; traçabilité de version de configuration ; conforme à D2.

**Négatives** : complexité de validation de la configuration au chargement ; nécessité d'un schéma de validation strict pour éviter une hiérarchie incohérente (boucle, orphelin).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Hiérarchie codée en dur dans les modèles applicatifs | Viole la modularité (CON-007) et rend tout redécoupage administratif coûteux. |
| Hiérarchie entièrement dynamique sans validation de schéma | Risque de configuration incohérente non détectée avant exécution. |

---

## ADR-021 — Orthogonalité Territorial Mesh / Server Meshing

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §6, P-TERR-02) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Le Territorial Mesh (gouvernance territoriale, RFC-0036) et le Server Meshing (exécution technique, RFC-0035) portent sur des préoccupations distinctes mais interagissent nécessairement.

### Décision

Les deux chantiers restent orthogonaux. Le Territorial Mesh ne modifie ni le contrat d'autorité de rendu ni le protocole de streaming du Server Meshing ; le Server Meshing ne porte aucune logique de hiérarchie administrative. La jonction entre les deux couches se fait exclusivement via des interfaces abstraites explicites (voir ADR-015, réutilisée).

### Conséquences

**Positives** : chaque chantier reste remplaçable et testable indépendamment (CON-007) ; réduit le risque de couplage accidentel.

**Négatives** : nécessite une discipline continue de revue croisée pour éviter toute fuite d'abstraction entre les deux couches (voir RISK-TERR-016).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Fusion des deux chantiers en un seul modèle unifié | Complexifie la maintenance et viole la responsabilité unique par composant. |

---

## ADR-022 — PostgreSQL logical replication pour fédération cross-région

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §5.5, P-TERR-05, D3) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

La fédération multi-régions (Phase 6) nécessite de propager les données pertinentes entre DOD, RCH et NCP sans introduire un mécanisme de consensus distribué (D3).

### Décision

La fédération cross-région repose sur la réplication logique PostgreSQL (`logical replication`), avec PostgreSQL comme source de vérité unique par périmètre (chaque DOD est autoritaire sur ses propres données). Aucun protocole de consensus distribué (Raft, Paxos) n'est introduit.

### Conséquences

**Positives** : cohérence avec D3 ; réutilisation de compétences PostgreSQL déjà présentes dans l'équipe ; pas de dépendance nouvelle.

**Négatives** : la réplication logique implique une latence de propagation non nulle, à mesurer et documenter (voir RISK-TERR-011) ; nécessite une stratégie de résolution de conflit par domaine en cas d'écriture concurrente rare.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Base de données distribuée avec consensus (CockroachDB, etcd) | Contredit explicitement D3 et introduit une complexité opérationnelle disproportionnée au besoin actuel. |
| Synchronisation applicative manuelle | Risque élevé d'incohérence non détectée, absence de garantie transactionnelle. |

---

## ADR-023 — Redis Pub/Sub fédéré multi-niveaux

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §5.6, D4) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Le bus d'événements territorial doit propager les événements (transitions d'état, alertes, handoffs) entre les niveaux de la hiérarchie sans introduire de nouvelle dépendance technique (D4).

### Décision

Le bus d'événements fédéré repose sur Redis Pub/Sub, avec un schéma de topic hiérarchique reflétant la structure territoriale (exemple : `terr.rch.nouvelle-aquitaine.dod.16.evenement`). Le routage inter-niveaux s'appuie sur ce schéma de nommage ; la durabilité et le rejeu reposent sur l'Outbox/Inbox (ADR-005), pas sur Redis Pub/Sub. Les consommateurs doivent être idempotents.

### Conséquences

**Positives** : cohérence avec D4 ; réutilisation directe de l'infrastructure Redis déjà en place pour le Server Meshing (ADR-013) ; schéma de topic simple à auditer.

**Négatives** : Redis Pub/Sub ne garantit pas la persistance des messages non consommés ; l'outbox pallie ce point pour les événements critiques mais nécessite une discipline d'implémentation stricte.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Kafka ou tout autre broker de streaming distribué | Contredit explicitement D4 et introduit une charge opérationnelle disproportionnée pour le volume d'événements attendu au stade prototype. |

---

## ADR-024 — Capsules territoriales pour edge

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §5.5, P-TERR-06, réutilisation ADR-008) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Les cellules et sous-cellules edge (drones, capteurs, terminaux terrain) doivent fonctionner en mode dégradé ou offline avec une synchronisation traçable, en s'appuyant sur le mécanisme expérimental proposé par ADR-008.

### Décision

Le conteneur expérimental défini par ADR-008 est réutilisé comme
base. Toute extension destinée au Territorial Mesh (identifiant du
niveau d'origine, référence de synchronisation différentielle) doit être
additive, versionnée et validée comme évolution de schéma avant usage.
Aucune nouvelle primitive de capsule n'est introduite au stade
prototype, et aucune compatibilité de production n'est présumée tant
qu'ADR-008 reste au statut Proposé.

### Conséquences

**Positives** : continuité avec l'artefact edge expérimental d'ADR-008 ; aucune primitive concurrente n'est introduite ; réduit le risque décrit en RISK-TERR-008 sous réserve de la validation du nouveau schéma.

**Négatives** : l'extension du contenu de la capsule doit être versionnée
avec soin et accompagnée de fixtures de compatibilité ; la rotation et
la révocation des clés restent des gates avant production.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Nouveau format de capsule dédié au territorial | Duplique un mécanisme existant sans justification, contraire au principe DRY et à CON-007. |

---

## ADR-025 — États opérationnels comme signal de gouvernance

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §3, P-TERR-04, D6) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Chaque nœud territorial (NCP, RCH, DOD, cellule) doit pouvoir signaler son état opérationnel selon une sémantique adaptée à son niveau (Froid, Chaud, Opérationnel, Crise) pour piloter la supervision et l'allocation de ressources (D6).

### Décision

Les quatre états opérationnels sont modélisés comme un signal de gouvernance explicite, porté par chaque nœud du mesh territorial et propagé via le bus d'événements fédéré (ADR-023). Les transitions d'état sont tracées dans le journal d'audit et ne déclenchent aucune action automatique irréversible sans validation humaine en état Crise.

### Conséquences

**Positives** : cohérence avec D6 ; base pour la concentration dynamique territoriale (Phase 7) ; conforme au principe de décision humaine (CON-001, l'IA assiste mais ne décide jamais).

**Négatives** : nécessite une définition précise et partagée des seuils de transition entre états, à documenter séparément pour éviter une interprétation divergente entre niveaux.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| État implicite déduit uniquement de métriques techniques (charge CPU, nombre de connexions) | Ne reflète pas nécessairement la réalité opérationnelle métier et prive l'opérateur humain d'un signal explicite et auditable. |

---

## ADR-026 — RBAC territorial

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — `TERRITORIAL_MESH_TARGET.md` §9, sécurité) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Les droits d'accès et d'action doivent être scopés par périmètre territorial (un opérateur départemental n'a pas nécessairement les mêmes droits sur un autre département) tout en permettant des rôles transverses (supervision nationale, audit).

### Décision

Le RBAC existant de l'API GSIE est étendu par un scope territorial explicite, attaché à chaque rôle. Un rôle peut être scopé à un périmètre unique (DOD, RCH) ou déclaré transverse (NCP, audit). Aucun nouveau fournisseur d'identité n'est introduit (voir RISK-TERR hors périmètre §4 de `TERRITORIAL_MESH_RISKS.md`).

### Conséquences

**Positives** : réutilisation du RBAC existant, pas de nouvelle dépendance ; scopage clair et auditable.

**Négatives** : nécessite une extension du modèle de rôle existant, à valider par une revue de sécurité avant activation en Phase 5.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Système d'autorisation entièrement nouveau et dédié au territorial | Duplique un mécanisme existant sans justification. |

---

## ADR-027 — Autorité unique par périmètre

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §3, P-TERR-07) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Pour éviter toute ambiguïté décisionnelle (voir RISK-TERR-002, RISK-TERR-003), chaque niveau de la hiérarchie territoriale doit avoir un rôle d'autorité clairement défini et non concurrent.

### Décision

Le DOD est l'autorité métier de référence sur son périmètre départemental (source de vérité opérationnelle). La RCH assure un rôle de coordination régionale (agrégation, arbitrage de conflits selon la politique applicable) sans se substituer à l'autorité métier du DOD. Le NCP assure un rôle de fédération nationale (agrégation, supervision) sans autorité métier directe sur un territoire donné. Les arbitrages et transferts utilisent un epoch de fencing.

### Conséquences

**Positives** : élimine l'ambiguïté d'autorité par construction ; cohérent avec D2 et avec l'autorité hybride déjà actée pour le Server Meshing (ADR-010).

**Négatives** : nécessite un protocole d'escalade documenté pour les cas où un DOD est indisponible (mode dégradé, voir ADR-019 réutilisé).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Autorité partagée par consensus entre DOD adjacents | Contredit D3 (pas de consensus distribué) et introduit une latence de décision incompatible avec les scénarios de crise. |

---

## ADR-028 — Frontières scientifiques réconciliées par table de correspondance

| Champ | Valeur |
|---|---|
| **Statut** | Draft (proposition — RFC-0036 §3, P-TERR-08) |
| **Date** | 2026-08-06 |
| **Décision liée** | DEC-000054 |

### Contexte

Les frontières scientifiques pertinentes pour les moteurs GSIE (bassins versants, massifs forestiers, zones climatiques) ne coïncident pas nécessairement avec les limites administratives (INSEE) utilisées par la hiérarchie territoriale (voir RISK-TERR-015).

### Décision

Aucune fusion forcée des deux référentiels n'est effectuée. Une table de correspondance explicite associe chaque unité administrative aux zones scientifiques qui la recouvrent, avec un taux de recouvrement documenté lorsque la correspondance n'est pas exacte. Les moteurs domaine (GIS, Climate, Pedology, Botanical, ForestDynamics) continuent de raisonner sur leurs référentiels scientifiques natifs ; la couche territoriale consulte la table de correspondance pour toute opération nécessitant un croisement.

### Conséquences

**Positives** : préserve l'intégrité scientifique des référentiels existants (CON-005) ; évite toute distorsion des données pour des raisons administratives.

**Négatives** : nécessite la maintenance continue de la table de correspondance à mesure que les référentiels scientifiques ou administratifs évoluent.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Redéfinition des zones scientifiques pour coïncider avec les limites administratives | Porterait atteinte à la validité scientifique des référentiels (contradiction avec CON-005, la science avant l'opinion). |
