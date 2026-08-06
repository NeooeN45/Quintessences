# ============================================================================
# GSIE TERRITORIAL MESH — DIRECTIVE FONDATRICE
# Directive ID : GSIE-DIR-0013
# Version : 1.0
# Statut : Active
# Priorité : STRUCTURANTE — oriente l'organisation territoriale du jumeau numérique
# Classification : FONDATION
# Auteur : Camille Perraudeau (Fondateur)
# Date : 2026-08-06
# ============================================================================
#
# Cette Directive fondatrice fixe la vision du GSIE Territorial Mesh :
# organisation logique, administrative et opérationnelle du territoire,
# orthogonale et complémentaire au GSIE Server Meshing.
#
# Elle est complémentaire à RFC-0036 (cadre technique, Draft) et
# subordonnée à la Constitution (00_CONSTITUTION/).
#
# Elle complète GSIE-DIR-0012 sans l'invalider : GSIE-DIR-0012 reste le
# document de référence proposé pour l'exécution distribuée (Server
# Meshing), sous réserve de la validation de DEC-000053 et de sa
# Directive. GSIE-DIR-0013 est la directive de référence pour
# l'organisation territoriale (Territorial Mesh). Les deux chantiers
# restent séparés.
#
# En cas de conflit :
#   1. La Constitution prime (GSIE-CON-000).
#   2. RFC-0003 (GSIE-Net) prime pour tout ce qui touche à
#      l'architecture réseau et offline-first.
#   3. Les contrats validés du Server Meshing priment pour l'exécution
#      distribuée ; les documents encore Draft ne créent pas de contrat
#      obligatoire.
#   4. La présente Directive prime pour l'organisation administrative,
#      la gouvernance territoriale et les états opérationnels.
# ============================================================================

| Champ | Valeur |
|---|---|
| **Directive** | GSIE-DIR-0013 |
| **Titre** | GSIE Territorial Mesh — Directive fondatrice |
| **Statut** | Active |
| **Date** | 2026-08-06 |
| **RFC de référence** | RFC-0036 |
| **Décision d'ouverture** | DEC-000054 |
| **Complète** | GSIE-DIR-0012 (Draft — non invalidée, validation distincte requise) |

---

# 1. Vision

Le GSIE Territorial Mesh organise le jumeau numérique environnemental
selon la géographie administrative et opérationnelle réelle du
territoire français — France, région, département, territoire
opérationnel, cellule spatiale, sous-cellule de simulation — sans
jamais figer une association rigide entre un échelon administratif et
une machine physique.

Un préfet de région ne pilote pas un serveur ; il pilote un territoire.
Un chef de centre DFCI ne pilote pas un cluster ; il pilote une zone
d'intervention. Le Territorial Mesh donne au jumeau numérique une
structure de gouvernance qui correspond à la façon dont le territoire
est réellement administré et exploité, et délègue l'exécution physique
au GSIE Server Meshing (GSIE-DIR-0012).

---

# 2. Principes directeurs

Les dix principes fondateurs sont détaillés dans RFC-0036 §3. Résumé :

1. **P-TERR-01** — Hiérarchie territoriale configurable (national →
   régional → départemental → territoire opérationnel → cellule →
   sous-cellule), non figée dans le code.
2. **P-TERR-02** — Orthogonalité au Server Meshing : gouvernance
   (Territorial) distincte d'exécution (Meshing).
3. **P-TERR-03** — Concentration dynamique par la demande ; la
   structure territoriale reste stable.
4. **P-TERR-04** — États opérationnels explicites : froid, chaud,
   opérationnel, crise.
5. **P-TERR-05** — Persistance fédérée : PostgreSQL reste source de
   vérité, réplication logique cross-région.
6. **P-TERR-06** — Offline-first territorial : capsules signées
   (ADR-008), edge nodes à chaque DOD.
7. **P-TERR-07** — Autorité unique par périmètre : jamais deux
   autorités concurrentes sur le même territoire.
8. **P-TERR-08** — Frontières scientifiques possibles : massif, zone
   DFCI, bassin versant, réconciliées avec le découpage administratif
   sans fusion forcée.
9. **P-TERR-09** — Subordination à la connaissance : Unreal reflète,
   ne calcule pas (CON-007).
10. **P-TERR-10** — Traçabilité et gouvernance multi-niveaux : audit
    possible par territoire, à tout niveau.

---

# 3. Décisions structurantes actées

| # | Décision | Valeur |
|---|---|---|
| **D1** | Périmètre prototype v0 | Nouvelle-Aquitaine, DOD Charente (16) + Deux-Sèvres (79) |
| **D2** | Hiérarchie territoriale | National → Régional → Départemental → Territoire opérationnel → Cellule → Sous-cellule |
| **D3** | Source de vérité | PostgreSQL/PostGIS (ADR-011) — pas de consensus distribué (Raft/Paxos) introduit |
| **D4** | Bus fédéré | Redis Pub/Sub par niveau avec routage inter-niveaux — pas de Kafka |
| **D5** | Compatibilité Server Meshing | Interfaces abstraites (ADR-015) pour ne bloquer aucune évolution du Server Meshing |
| **D6** | États opérationnels | Froid / chaud / opérationnel / crise, à chaque niveau de composant |
| **D7** | Dépendances externes | Pas de dépendance hard à UE6 ni à AWS pour la première itération |

---

# 4. Périmètre hors-scope

Sont explicitement **hors périmètre** de la présente Directive et du
prototype v0 :

- **Fédération cross-pays.** Le Territorial Mesh est cadré pour le
  territoire français métropolitain. Toute extension transfrontalière
  requiert une RFC dédiée.
- **IoT massif.** L'ingestion de flux massifs de capteurs IoT
  territoriaux n'est pas traitée par le Territorial Mesh ; elle relève
  des moteurs Evidence et GIS et de leurs propres chantiers.
- **Keycloak / gestion d'identité fédérée.** L'authentification et
  l'autorisation multi-niveaux s'appuient sur les mécanismes de
  sécurité déjà en place (mTLS, ADR-017) ; l'introduction d'un
  fournisseur d'identité fédéré (Keycloak ou équivalent) est différée
  à une itération ultérieure et fera l'objet d'une RFC séparée.

---

# 5. Livrables attendus

Le chantier produit **20 livrables dédiés**, complétés par **un lot de
synchronisation** des trois fichiers racine existants, répartis comme suit :

| Vague | Livrables |
|---|---|
| Gouvernance (3) | RFC-0036, GSIE-DIR-0013, DEC-000054 |
| Architecture cible (9) | `TERRITORIAL_MESH_TARGET.md`, `TERRITORIAL_MESH_NATIONAL_CONTROL_PLANE.md`, `TERRITORIAL_MESH_REGIONAL_HUB.md`, `TERRITORIAL_MESH_DEPARTMENTAL_DOMAIN.md`, `TERRITORIAL_MESH_DYNAMIC_CELLS.md`, `TERRITORIAL_MESH_STATE_FABRIC.md`, `TERRITORIAL_MESH_EVENT_BUS.md`, `TERRITORIAL_MESH_MATRICES.md`, `TERRITORIAL_MESH_DIAGRAMS.md` |
| Roadmap et qualité (8) | `TERRITORIAL_MESH_ROADMAP.md`, `TERRITORIAL_MESH_BACKLOG.md`, `TERRITORIAL_MESH_RISKS.md`, `TERRITORIAL_MESH_ADR.md`, `TERRITORIAL_MESH_ACCEPTANCE.md`, `TERRITORIAL_MESH_TEST_STRATEGY.md`, `TERRITORIAL_MESH_PROTOTYPE_V0.md`, `TERRITORIAL_MESH_COMPLEXITY.md` |
| Synchronisation (lot) | Mise à jour de `PROJECT_MEMORY.md`, `ROADMAP.md` et `CHANGELOG.md` — aucun nouveau document dédié |

Les 17 documents d'architecture et de cadrage, ainsi que RFC-0036,
sont au statut **Draft** pour validation ultérieure du Fondateur. La
présente Directive est **Active** par DEC-000054 et cette décision est
au statut **Validé**, conformément au cycle de vie documentaire (CLAUDE.md §5).

---

# 6. Critères de succès

Le chantier est considéré réussi lorsque les conditions suivantes sont
réunies :

1. **Prototype v0 fonctionnel** : la hiérarchie NCP → RCH
   Nouvelle-Aquitaine → DOD Charente + DOD Deux-Sèvres est instanciée
   en configuration, les transitions d'état (froid/chaud/opérationnel/
   crise) sont déclenchables et traçables, et le State Fabric fédéré
   réplique les états publiés de chaque DOD vers la RCH avec convergence
   vérifiée.
2. **Non-régression Phase 4** : aucune priorité en cours (14 moteurs,
   API GSIE, Hub UE5.8, GeoSylva, Ignis) n'est retardée ou dégradée par
   l'ouverture du chantier Territorial Mesh.
3. **Compatibilité Server Meshing préservée** : aucun contrat
   d'interface du Server Meshing (ADR-010 à ADR-019) n'est modifié sans
   RFC dédiée.
4. **Traçabilité complète** : chaque décision structurante du chantier
   est enregistrée dans `03_DECISIONS/` et reflétée dans
   `PROJECT_MEMORY.md`.

---

# Note de gouvernance

Cette Directive est **Active** dès son ouverture par la décision
DEC-000054. Toute évolution de cette Directive requiert une RFC.

> « Le jumeau numérique environnemental doit être organisé comme le
> territoire qu'il représente — jamais comme l'infrastructure qui le
> calcule. »
