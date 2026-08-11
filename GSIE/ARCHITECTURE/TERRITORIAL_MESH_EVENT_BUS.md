# GSIE Territorial Mesh — Bus d'événements fédéré

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_EVENT_BUS |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **ADR liés** | ADR-005 (Outbox/Inbox), ADR-008 (capsule territoriale signée), ADR-013 (Redis Pub/Sub), ADR-017 (mTLS) |
| **Lois constitutionnelles** | GSIE-CON-007 (modularité), GSIE-CON-010 (évolution sans perte d'historique) |

---

## 1. Rôle

Le **bus d'événements fédéré** du Territorial Mesh assure la
propagation asynchrone et récupérable des changements d'état à travers la
hiérarchie territoriale (France → Région → Département → Territoire
Opérationnel → Cellule → Sous-cellule). Il permet à chaque niveau de
réagir aux événements pertinents pour son périmètre sans être couplé
directement aux autres niveaux, conformément au principe de couplage
faible (T-2, RFC-0035 §2.3).

## 2. Principes

### 2.1 Redis Pub/Sub par niveau (ADR-013, pas de Kafka)

Chaque niveau territorial (national, régional, départemental) dispose
de son propre bus Redis Pub/Sub. Ce choix, cohérent avec le Server
Meshing (RFC-0035, bus inter-nœuds Redis Pub/Sub mTLS), évite
l'introduction d'un broker externe de type Kafka, jugé surdimensionné
pour la volumétrie actuelle (ADR-005 §Options envisagées, option 3
écartée).

### 2.2 Fédération par routage inter-niveaux

Les bus ne sont pas isolés : un routeur de fédération propage les
événements pertinents d'un niveau à l'autre, selon un filtre explicite
de pertinence (§4). Un événement n'est jamais diffusé « en cascade »
sans filtre — la fédération n'est pas une simple répétition.

### 2.3 Outbox/Inbox pour durabilité (ADR-005, au moins une fois)

Tout événement structurant (changement d'état territorial, transfert
d'autorité, déclaration de crise) est écrit dans une table
`outbox_event` dans la même transaction que la donnée métier
correspondante, avant toute publication Redis. Redis Pub/Sub reste un
mécanisme de notification best-effort ; l'Outbox conserve l'événement
jusqu'à sa publication et les tables de relais/Inbox assurent une
livraison **au moins une fois**. Chaque consommateur doit être
idempotent, de sorte que l'effet métier soit effectivement unique. Le
système ne revendique pas d'exactly-once de bout en bout.

### 2.4 Garantie d'ordre par entité

La clé de partition de chaque événement est `entity_id` (identifiant
du territoire, de la cellule ou de l'entité métier concernée). Tous
les événements relatifs à la même entité sont traités dans l'ordre
d'émission, garanti par un numéro de séquence par entité inscrit dans
`outbox_event.payload`.

### 2.5 Dead letter queue structurée

Tout événement dont le traitement échoue de manière répétée (au-delà
d'un seuil de tentatives configuré) est déplacé vers une file de
rejet (`dead_letter`) avec la trace complète de l'échec. Un workflow
de reprise manuel ou automatisé (selon la nature de l'échec) permet le
rejeu contrôlé — jamais la perte silencieuse d'un événement.

## 3. Topologie

```
Bus national (NCP)
  événements de gouvernance, supervision fédérée
       │ fédération descendante (politiques) ▼
       │ fédération ascendante (synthèse)     ▲
Bus régional (RCH)  ×N régions
  événements inter-départementaux, activation DOD
       │ ▼▲
Bus départemental (DOD)  ×N départements
  événements métier, cellules, edge
       │ ▼▲
Bus de cellule
  événements de simulation et handoff inter-cellules du Server Meshing
  (pas un bus Redis territorial supplémentaire)
```

| Niveau | Portée | Exemples d'événements typiques |
|---|---|---|
| National (NCP) | Gouvernance, supervision de l'ensemble du mesh | `authority.transferred` (inter-régional), `crisis.declared` (nationale) |
| Régional (RCH) | Coordination inter-départementale | `territory.activated`, `crisis.declared` (régionale) |
| Départemental (DOD) | Métier, cellules, edge | `cell.handoff`, `edge.synced`, `territory.deactivated` |
| Cellule | Simulation et transfert local du Server Meshing | `cell.handoff` (intra-territoire) |

## 4. Fédération

**Routage ascendant** : un événement départemental (DOD) ne remonte
vers le bus régional (RCH) que s'il est marqué `federation_scope:
regional` ou supérieur dans son enveloppe. Un événement régional ne
remonte vers le national que s'il est marqué `federation_scope:
national`. Ce marquage est décidé à l'émission par le producteur,
conformément au type d'événement (§5).

**Routage descendant** : les politiques et référentiels émis par le
NCP (schéma `gsie_gouvernance`, voir `TERRITORIAL_MESH_STATE_FABRIC.md`
§3) sont diffusés vers tous les RCH, qui les rediffusent vers leurs
DOD. Ce sens de propagation ne transporte jamais de donnée métier
opérationnelle — uniquement de la gouvernance.

| Sens | Déclencheur | Filtre |
|---|---|---|
| Ascendant (DOD → RCH → NCP) | Événement marqué `federation_scope ≥ regional` | Pertinence explicite au niveau parent |
| Descendant (NCP → RCH → DOD) | Publication de politique ou de référentiel territorial | Toujours diffusé (gouvernance) |

## 5. Types d'événements

| Événement | Émetteur typique | Portée par défaut |
|---|---|---|
| `territory.activated` | DOD | Régionale |
| `territory.deactivated` | DOD | Régionale |
| `cell.handoff` | Cellule / DOD | Départementale |
| `authority.transferred` | RCH / NCP | Régionale ou nationale |
| `crisis.declared` | DOD / RCH | Régionale, nationale si escalade |
| `crisis.resolved` | DOD / RCH | Même portée que la crise déclarée |
| `edge.synced` | DOD | Départementale |
| `conflict.detected` | Edge / DOD | Départementale |

## 6. Outbox/Inbox

Reprise directe du schéma ADR-005, appliqué à chaque niveau
territorial (une paire `outbox_event` / `consumer_inbox` par instance
PostgreSQL NCP/RCH/DOD) :

```sql
CREATE TABLE outbox_event (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_instance    VARCHAR(128) NOT NULL,
    entity_id          UUID NOT NULL,           -- clé de partition (§7)
    sequence_no        BIGINT NOT NULL,         -- séquence par entity_id/source
    event_type         VARCHAR(64) NOT NULL,
    schema_version     VARCHAR(16) NOT NULL,
    federation_scope   VARCHAR(16) NOT NULL,    -- local | departmental | regional | national
    causation_id       UUID,
    occurred_at        TIMESTAMPTZ NOT NULL,
    payload            JSONB NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at       TIMESTAMPTZ,
    UNIQUE (source_instance, entity_id, sequence_no)
);

CREATE TABLE consumer_inbox (
    event_id       UUID NOT NULL,               -- peut provenir d'un niveau distant
    consumer       VARCHAR(128) NOT NULL,
    status         VARCHAR(32) NOT NULL DEFAULT 'pending',
    attempts       INT NOT NULL DEFAULT 0,
    processed_at   TIMESTAMPTZ,
    error          TEXT,
    PRIMARY KEY (event_id, consumer)
);

CREATE TABLE outbox_delivery (
    event_id       UUID NOT NULL,
    destination     VARCHAR(128) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    attempts        INT NOT NULL DEFAULT 0,
    delivered_at    TIMESTAMPTZ,
    error           TEXT,
    PRIMARY KEY (event_id, destination)
);

CREATE TABLE dead_letter (
    event_id       UUID NOT NULL,
    destination     VARCHAR(128) NOT NULL,
    failed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    attempts        INT NOT NULL,
    error           TEXT NOT NULL,
    payload         JSONB NOT NULL,
    PRIMARY KEY (event_id, destination)
);
```

`sequence_no` doit être attribué dans la même transaction que l'écriture
métier, avec un compteur sérialisé par `(source_instance, entity_id)`.
Une contrainte `UNIQUE` seule ne suffit pas à produire une séquence sans
trou ni course concurrente ; l'implémentation doit donc verrouiller le
compteur ou utiliser une procédure SQL atomique.

**Worker** : un worker par niveau territorial poll `outbox_event`
(`published_at IS NULL`), publie sur le bus Redis local et enregistre
l'état de relais par destination. Un relais peut republier après une
panne ; le consommateur déduplique via `consumer_inbox` et son
identifiant d'événement. **Retry** : incrémentation d'`attempts` à
chaque échec, avec backoff exponentiel. Au-delà du seuil de tentatives,
l'événement est déplacé en **dead letter** (§2.5) avec conservation de
l'historique complet des tentatives (CON-010).

## 7. Garantie d'ordre

La clé de partition `entity_id` est systématiquement l'identifiant de
l'entité territoriale ou métier concernée par l'événement (territoire,
cellule, mission edge). Le couple `(source_instance, entity_id)` définit
le flux ordonné et `UNIQUE` garantit une séquence sans doublon. Le
worker de relais traite les événements d'un même flux strictement dans
l'ordre de `sequence_no`, même en cas de parallélisation entre flux
différents. Les consommateurs rejettent ou mettent en attente un
événement dont le prédécesseur manque ; l'ordre causal entre niveaux
est porté par `causation_id` et ne doit pas être déduit de l'horloge.

## 8. États opérationnels

| État | Comportement du bus |
|---|---|
| **Froid** | Aucun worker de relais actif ; les écritures Outbox restent persistées et accumulées sans publication. |
| **Chaud** | Bus minimal : relais des événements de portée régionale/nationale uniquement, latence de polling élevée (5-15s). |
| **Opérationnel** | Bus normal : relais de tous les événements marqués, latence de polling standard (1-5s, cohérent ADR-005). |
| **Crise** | Bus priorisé : file dédiée pour le territoire en crise, latence de polling réduite, dead letter surveillée en temps réel. |

## 9. Sécurité

- **mTLS (ADR-017)** entre tous les nœuds Redis fédérés et les workers
  de relais.
- **Authentification des publishers** : chaque producteur (DOD, RCH,
  NCP, cellule) publie avec une identité de service distincte,
  vérifiée par certificat mTLS, jamais par simple canal Redis nommé.
- **ACL par niveau** : un DOD ne peut publier que sur son propre canal
  départemental et sur les canaux de fédération ascendante autorisés ;
  il ne peut jamais publier directement sur le bus national.

## 10. Mode dégradé

| Panne | Comportement |
|---|---|
| **Panne bus régional (RCH)** | Les bus départementaux (DOD) continuent en autonomie complète ; les événements à portée régionale/nationale s'accumulent dans l'Outbox local en attente de reprise. |
| **Panne bus national (NCP)** | Aucun impact sur l'exploitation régionale/départementale ; accumulation des événements de gouvernance en attente. |
| **Reprise** | À la remontée d'un bus, reprise des relais depuis `outbox_delivery`, rejeu ordonné par `(source_instance, entity_id)` et déduplication via `consumer_inbox`, sans purge ni réordonnancement arbitraire. |

## 11. Diagramme ASCII — topologie du bus fédéré

```
┌─────────────────────────────────────────────────────────────┐
│                    BUS NATIONAL (NCP)                        │
│         gouvernance · supervision · crise nationale          │
└───────────────────────────┬────────────────────────┬─────────┘
        fédération descendante│                        │fédération ascendante
        (politiques)          ▼                        ▲ (synthèse)
┌───────────────────────────────────────────────────────────────┐
│                  BUS RÉGIONAL (RCH)  ×N régions                │
│        inter-départemental · activation DOD · crise régionale  │
└───────────────────────────┬────────────────────────┬─────────┘
                             ▼                        ▲
┌───────────────────────────────────────────────────────────────┐
│               BUS DÉPARTEMENTAL (DOD)  ×N départements          │
│        métier · cellules · edge · territory.activated           │
└───────────────────────────┬────────────────────────┬─────────┘
                             ▼                        ▲
┌───────────────────────────────────────────────────────────────┐
│                      BUS DE CELLULE                              │
│              simulation · handoff inter-cellules                  │
└───────────────────────────────────────────────────────────────┘
```
