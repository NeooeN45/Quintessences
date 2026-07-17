# ADR-005 — Outbox/Inbox : transactional outbox pattern

| Champ | Valeur |
|---|---|
| **ID** | ADR-005 |
| **Statut** | Accepté |
| **Date** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000022, RFC-0011 |

## Contexte

L'audit v5 (point 3) a identifié que `LISTEN/NOTIFY` seul n'est pas un
bus durable : si un consommateur est indisponible lors du NOTIFY, le
message est perdu. Le métamodèle v6.1 spécifie `OutboxEvent` et
`ConsumerInbox` (niveau D, infrastructure) pour garantir la livraison
des événements métier (nouvelle assertion ingérée, conflit détecté,
révision publiée).

## Options envisagées

1. **LISTEN/NOTIFY seul** — utiliser PostgreSQL LISTEN/NOTIFY pour
   notifier les consommateurs. Avantage : simple, natif PG. Inconvénient
   : pas durable (message perdu si consommateur indisponible).

2. **Transactional outbox + worker** — écrire les événements dans une
   table `outbox_event` dans la même transaction que la donnée, puis un
   worker relaye les événements vers les consommateurs (ou vers
   LISTEN/NOTIFY). Avantage : durable, exactly-once, pas de message
   perdu. Inconvénient : table supplémentaire + worker à maintenir.

3. **Kafka / RabbitMQ** — broker de messages externe. Avantage :
   mature, scalable. Inconvénient : service supplémentaire, complexité
   opérationnelle, surdimensionné pour la Vague 1.

## Décision

**Option 2 : transactional outbox + worker.**

```sql
CREATE TABLE outbox_event (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id  UUID REFERENCES resource(id),
    event_type    VARCHAR(64) NOT NULL,
    payload       JSONB NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at  TIMESTAMPTZ  -- NULL si non traité
);

CREATE TABLE consumer_inbox (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id      UUID REFERENCES outbox_event(id),
    consumer      VARCHAR(64) NOT NULL,
    status        VARCHAR(32) NOT NULL DEFAULT 'pending',
    processed_at  TIMESTAMPTZ,
    error         TEXT,
    PRIMARY KEY (event_id, consumer)
);
```

### Fonctionnement

1. **Producteur** : lors d'une transaction métier (ex. ingestion
   d'assertion), insère la donnée ET l'événement dans `outbox_event`
   dans la même transaction.
2. **Worker** : un processus Python (asyncio) poll `outbox_event` où
   `processed_at IS NULL`, distribue aux consommateurs via
   `consumer_inbox`, marque `processed_at` quand tous les consommateurs
   ont traité.
3. **Consommateur** : chaque moteur ou service s'enregistre comme
   consommateur, lit son `consumer_inbox`, traite, marque `processed_at`.

### Types d'événements (Vague 1)

| Event | Déclencheur | Consommateurs |
|---|---|---|
| `assertion.ingested` | Nouvelle Assertion accepted | Knowledge Engine, Learning Engine |
| `assertion.revised` | Revision créée | Knowledge Engine, Reasoning Engine |
| `conflict.detected` | ConflictCluster créé | Knowledge Engine, Reasoning Engine |
| `evidence.assessed` | EvidenceAssessment créée | Knowledge Engine |

## Conséquences

- **Positives** : durabilité garantie, exactly-once, pas de service
  externe, transactionnel avec la donnée métier.
- **Négatives** : table `outbox_event` grandit (partitionnement par
  temps à prévoir), worker à maintenir, latence de polling (configurable,
  1-5s en Vague 1).
- **Implémentation différée** : spécifiée en Vague 0, implémentée
  uniquement si un besoin asynchrone réel émerge en Vague 1. Si les
  moteurs fonctionnent en synchrone, l'outbox n'est pas nécessaire
  immédiatement.

## Statut de suivi

- 2026-07-15 : Proposé (RFC-0011 / DEC-000022)
- Vague 0 : spécification détaillée (schéma + worker)
- Vague 1+ : implémentation si besoin asynchrone confirmé

## Validation (2026-07-17)

ADR-005 accepté par le Fondateur, conformément à DEC-000022 (§ « Adopte
les 6 ADR-001 à ADR-006 »), déjà Validated depuis le 2026-07-16. Le
schéma outbox/inbox est déjà implémenté (migration 0002) ; le worker de
relais reste différé à Vague 1+ selon besoin réel (inchangé).
