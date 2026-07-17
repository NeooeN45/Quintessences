# ADR-002 — GSIE Temporal & Provenance Engine : versionnement métier intégré

| Champ | Valeur |
|---|---|
| **ID** | ADR-002 |
| **Statut** | Accepté |
| **Date** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000022, RFC-0011 |

## Contexte

Le métamodèle v6.2 exige la bitemporalité (audit F-P1-02) et la
traçabilité complète des évolutions de connaissance (CON-010). La
question n'est pas « comment historiser une ligne SQL » mais
« comment représenter l'évolution d'une connaissance scientifique dans
le temps, avec ses preuves, ses révisions, ses auteurs, ses conflits et
ses conséquences ».

Une extension comme `temporal_tables` résout le versioning générique
(transaction_time), mais ne comprend pas la sémantique scientifique :
elle ne lie pas une révision à une Evidence, ne permet pas de
reconstruire un état complet, ne produit pas de diff explicite, et ne
s'intègre pas avec PROV-O.

## Vision : Knowledge Evolution

GSIE ne versionne pas des lignes — il fait évoluer des connaissances.
Le cycle de vie d'une connaissance scientifique est :

```
Concept
  ↓
Revision (correction, ajout, fusion)
  ↓
Validation (Evidence Engine évalue)
  ↓
Publication (lifecycle_status = accepted)
  ↓
Superseded (nouvelle revision plus précise)
  ↓
Deprecated (obsolète mais conservé)
```

Chaque transition est un **événement traçable** avec auteur,
justification, preuves, et conséquences sur les décisions qui
l'utilisaient.

## Cinq concepts fondamentaux

### 1. Revision (type 29, enrichi)

Chaque ressource (Observation, Concept, Assertion, Dataset, Model,
Instance, Correlation, Recommendation…) possède des révisions
explicites. Une Revision est :

- **Append-only** (CON-010 — jamais supprimée, jamais modifiée)
- **Justifiée** (`justification` obligatoire — pourquoi on révise)
- **Auteur** (`author_id` → Agent)
- **Parent** (`parent_id` → Revision précédente — chaîne)
- **Bitemporelle** : `valid_time_start/end` (quand c'est vrai dans le
  monde) + `transaction_time` (quand le système l'a enregistré, immuable)
- **PROV-O** : `was_generated_by` → Activity (qui a produit cette
  revision, avec quelle méthode)

### 2. Validity (bitemporel métier)

Distinction entre :
- **valid_time** : période où l'information est scientifiquement valable
  (ex. « cette observation a été faite le 2024-06-15 »)
- **transaction_time** : quand le système l'a enregistré (immuable,
  ex. « GSIE a enregistré cette observation le 2024-06-16 14:32:00 »)

Implémenté en **SQL métier** (colonnes `valid_time_start`,
`valid_time_end`, `transaction_time` sur Revision), pas par extension.
Le MVCC PostgreSQL garantit l'immutabilité du transaction_time (une
Revision est insert-only, jamais UPDATEd).

### 3. Snapshot (type 30, enrichi)

Reconstruction de l'état complet d'une ressource à une date donnée. Un
Snapshot sérialise l'état de la ressource + ses relations + ses
qualifiers + son evidence en JSONB immuable. Utilisé pour :

- Reproductibilité d'un ModelRun (input = Snapshot)
- Reconstruction d'un état pour une Decision (« sur quelle version de
  la connaissance cette décision s'est-elle basée ? »)
- Audit scientifique (« que savait-on au 2024-06-15 ? »)

### 4. ResourceDiff (type 61, nouveau)

Différence explicite entre deux Revisions. Explique **ce qui a changé**
(champs modifiés, ajoutés, supprimés, relations ajoutées/retirées).
Permet à un humain ou un moteur de comprendre rapidement l'évolution
sans comparer deux snapshots complets.

```sql
CREATE TABLE resource_diff (
    id              UUID PRIMARY KEY REFERENCES resource(id),
    from_revision_id UUID REFERENCES resource(id),  -- → Revision
    to_revision_id   UUID REFERENCES resource(id),  -- → Revision
    changes          JSONB NOT NULL,  -- {added: {...}, modified: {...}, removed: {...}}
    summary          TEXT,  -- description humaine du changement
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 5. Provenance (intégration PROV-O)

Chaque Revision est liée à une `Activity` PROV (type 20) qui documente
**qui, quand, comment, à partir de quelles preuves** la revision a été
produite. Une EvidenceAssessment (type 13) peut pointer vers une
Revision spécifique. Une Decision (type 55) référence les Revisions
qu'elle utilisait au moment du choix.

```
Activity (extraction, validation, revision)
  ↓ wasGeneratedBy
Revision 3
  ↓ assessedBy
EvidenceAssessment (level=B)
  ↓ usedBy
Decision (« planter du chêne sessile »)
  ↓ basedOn
Revision 3 (au moment de la décision)
```

## Options envisagées

1. **Extension `temporal_tables`** (fork nearform) — versioning générique
   par triggers. Avantage : moins de code. Inconvénient : ne comprend
   pas la sémantique scientifique, pas de diff, pas de lien
   Revision↔Evidence↔Decision, pas d'intégration PROV-O native.

2. **Extension `pgMemento`** — historisation par audit log JSONB.
   Avantage : capture automatique des changements. Inconvénient :
   générique, pas métier, diff implicite (JSONB diff), pas de lien
   avec Evidence/Decision.

3. **GSIE Temporal & Provenance Engine** (moteur métier intégré) —
   Revision + Validity + Snapshot + Diff + PROV-O implémentés en
   SQL métier + Python. Avantage : contrôle total, intégration native
   avec Evidence/Decision/PROV-O, diff explicite, snapshot
   reproductible. Inconvénient : plus de code à écrire et maintenir.

4. **Event Sourcing** — chaque changement est un événement immuable,
   l'état est reconstruit par replay. Avantage : audit parfait.
   Inconvénient : complexité de reconstruction, surdimensionné pour
   la plupart des ressources. **Retenu partiellement** : Event
   Sourcing pour les ressources à haute fréquence de changement
   (Observations de capteurs temps réel), pas pour tout GSIE.

## Décision

**Option 3 : GSIE Temporal & Provenance Engine.**

Le versioning est implémenté en **SQL métier** (pas d'extension) avec :

### Schéma

```sql
-- Revision universelle (déjà type 29, enrichie)
CREATE TABLE revision (
    id                 UUID PRIMARY KEY REFERENCES resource(id),
    target_id          UUID NOT NULL REFERENCES resource(id),
    version            INTEGER NOT NULL,
    author_id          UUID REFERENCES resource(id),  -- → Agent
    justification      TEXT NOT NULL,
    parent_id          UUID REFERENCES resource(id),  -- → Revision précédente
    valid_time_start   TIMESTAMPTZ NOT NULL,
    valid_time_end     TIMESTAMPTZ,
    transaction_time   TIMESTAMPTZ NOT NULL DEFAULT now(),  -- immuable
    activity_id        UUID REFERENCES resource(id),  -- → Activity PROV
    diff_id            UUID REFERENCES resource(id),  -- → ResourceDiff
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index pour requêtes historiques
CREATE INDEX idx_revision_target ON revision(target_id);
CREATE INDEX idx_revision_valid_time ON revision(valid_time_start, valid_time_end);
CREATE INDEX idx_revision_transaction ON revision(transaction_time);
CREATE INDEX idx_revision_parent ON revision(parent_id);

-- Snapshot (déjà type 30, enrichi)
CREATE TABLE snapshot (
    id               UUID PRIMARY KEY REFERENCES resource(id),
    target_id        UUID NOT NULL REFERENCES resource(id),
    revision_id      UUID REFERENCES resource(id),  -- → Revision capturée
    captured_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    serialized_state JSONB NOT NULL,  -- état complet : champs + relations + qualifiers + evidence
    checksum         VARCHAR(128) NOT NULL
);

-- ResourceDiff (type 61, nouveau)
CREATE TABLE resource_diff (
    id               UUID PRIMARY KEY REFERENCES resource(id),
    from_revision_id UUID NOT NULL REFERENCES resource(id),
    to_revision_id   UUID NOT NULL REFERENCES resource(id),
    changes          JSONB NOT NULL,  -- {added: {...}, modified: {...}, removed: {...}}
    summary          TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Garanties

1. **Immutabilité** : une Revision est INSERT-only (jamais UPDATE ni
   DELETE). Le MVCC PostgreSQL garantit que `transaction_time` est
   immuable. Enforce par trigger BEFORE UPDATE/DELETE qui lève une
   exception.

2. **Chaîne de révision** : `parent_id` forme une liste chaînée.
   La première revision d'une ressource a `parent_id = NULL`.

3. **Reconstruction historique** : `SELECT * FROM revision WHERE
   target_id = ? AND transaction_time <= '2024-06-15' ORDER BY
   version DESC LIMIT 1` donne la dernière revision connue à cette
   date.

4. **Diff explicite** : chaque transition de revision a un
   `ResourceDiff` qui documente les changements champ par champ.

5. **PROV-O** : chaque Revision est liée à une `Activity` qui documente
   le processus (extraction, validation, correction expert, fusion
   taxonomique).

6. **Lien Evidence ↔ Revision** : `EvidenceAssessment` peut évaluer
   une revision spécifique. Quand une revision est superseded, les
   EvidenceAssessment précédentes sont conservées (historique
   d'évaluation).

7. **Lien Decision ↔ Revision** : `Decision.evidence_refs` peut
   pointer vers des Revisions spécifiques, pas seulement des
   Citations. Cela permet de répondre : « sur quelle version de la
   connaissance cette décision s'est-elle basée ? »

### Implémentation Python (Vague 1)

```python
class TemporalEngine:
    """Moteur de versionnement métier GSIE."""

    def create_revision(
        self, target_id: UUID, author: Agent,
        justification: str, new_state: dict,
        activity: Activity | None = None,
    ) -> Revision:
        """Crée une nouvelle revision d'une ressource."""
        parent = self.get_latest_revision(target_id)
        version = parent.version + 1 if parent else 1
        diff = self.compute_diff(parent, new_state) if parent else None
        revision = Revision(
            target_id=target_id, version=version, author_id=author.id,
            justification=justification, parent_id=parent.id if parent else None,
            valid_time_start=datetime.now(UTC), activity_id=activity.id if activity else None,
            diff_id=diff.id if diff else None,
        )
        return self.repo.save(revision)

    def get_state_as_of(
        self, target_id: UUID, timestamp: datetime
    ) -> dict | None:
        """Reconstruit l'état d'une ressource à une date donnée."""
        rev = self.repo.get_latest_before(target_id, timestamp)
        return self.reconstruct_state(rev) if rev else None

    def compute_diff(self, old: Revision, new_state: dict) -> ResourceDiff:
        """Calcule le diff explicite entre deux états."""
        old_state = self.reconstruct_state(old)
        changes = {
            "added": {k: v for k, v in new_state.items() if k not in old_state},
            "modified": {k: {"from": old_state[k], "to": v} for k, v in new_state.items() if k in old_state and old_state[k] != v},
            "removed": {k: old_state[k] for k in old_state if k not in new_state},
        }
        return ResourceDiff(from_revision_id=old.id, changes=changes, summary=self.summarize(changes))
```

## Conséquences

- **Positives** : contrôle total, intégration native avec
  Evidence/Decision/PROV-O, diff explicite, snapshot reproductible,
  pas de dépendance extension, sémantique scientifique (Knowledge
  Evolution, pas versioning de lignes).
- **Négatives** : plus de code à écrire et maintenir (TemporalEngine
  Python + triggers SQL + tests). Pas de support natif `AS OF SYSTEM
  TIME` (requêtes via `transaction_time <= ?`).
- **Mitigation** : le TemporalEngine est un moteur GSIE à part entière
  (comme Evidence Engine, Knowledge Engine). Il a ses propres tests
  (Vague 1). Le code est métier, donc testable et auditable.
- **Event Sourcing partiel** : pour les ressources à haute fréquence
  (capteurs temps réel), un pattern Event Sourcing sera évalué en
  Vague 2+ si le volume de revisions justifie.

## Technologies considérées (référence)

| Technologie | Rôle | Statut |
|---|---|---|
| PostgreSQL MVCC | Immutabilité transaction_time | **Utilisé** (natif) |
| Triggers SQL | Enforce append-only sur Revision | **Utilisé** (Vague 1) |
| PROV-O | Provenance des revisions | **Utilisé** (via Activity type 20) |
| pgMemento | Historisation par audit log | **Évalué** — pas retenu (trop générique) |
| Event Sourcing | Replay d'événements | **Différé** — pour capteurs temps réel uniquement |
| Apache Iceberg | Data Lake versionné | **Différé** — pour DataAsset volumineux |
| Delta Lake | Data Lake versionné | **Différé** — alternative à Iceberg |
| temporal_tables | Versioning générique | **Non retenu** — remplacé par Temporal Engine |
| Neo4j | Graphe de revisions | **Différé** — AGE benchmark (ADR-003) |

## Statut de suivi

- 2026-07-15 : Proposé (RFC-0011 / DEC-000022)
- Vague 0 : spécification détaillée du TemporalEngine (interface +
  schéma SQL + triggers)
- Vague 1 : implémentation TemporalEngine + tests + intégration
  Evidence/Decision

## Validation (2026-07-17)

ADR-002 accepté par le Fondateur, conformément à DEC-000022 (§ « Adopte
les 6 ADR-001 à ADR-006 »), déjà Validated depuis le 2026-07-16. Le
Temporal & Provenance Engine (Revision append-only) est déjà implémenté
(migration 0002) et testé.
