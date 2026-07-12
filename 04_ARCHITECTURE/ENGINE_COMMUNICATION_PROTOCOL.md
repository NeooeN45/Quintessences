# ENGINE_COMMUNICATION_PROTOCOL — Protocole de communication entre moteurs

| Champ | Valeur |
|---|---|
| **Livrable** | 203 — Protocole de communication entre moteurs |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-007, GSIE-CON-010 |
| **Constitutions liées** | Technique (T-1, T-2, T-6, T-7, T-8) |
| **RFC de référence** | RFC-0003 (GSIE-Net) |
| **Décision d'ouverture** | DEC-000004 |

---

## 1. Objet

Définir le protocole de communication entre les 14 moteurs de GSIE.
Ce protocole réalise l'article T-2 (couplage faible) : les moteurs
communiquent exclusivement par des interfaces contractuelles
versionnées, jamais par accès direct à l'implémentation interne.

Ce document décrit :
- le mode de communication (sync/async, message passing, event-driven) ;
- le format des messages (structure de données, pas du code) ;
- la gestion des erreurs et des retries ;
- le versioning des contrats d'interface ;
- le comportement offline-first (RFC-0003 §1, T-8).

> **Note :** ce document décrit la communication **entre moteurs
> GSIE** (in-process ou inter-process). La communication **réseau**
> entre nœuds (téléphone ↔ Edge Node ↔ serveur) est définie par
> RFC-0003 (GSIE-Net) et n'est pas dupliquée ici.

---

## 2. Mode de communication

### 2.1 Trois modes, choisis selon le couplage temporel

GSIE utilise trois modes de communication selon le besoin. Le mode
est défini par le **contrat d'interface** de chaque moteur, pas par
l'appelant.

| Mode | Couplage temporel | Cas d'usage | Exemple |
|---|---|---|---|
| **Synchrone (appel direct)** | Fort — l'appelant attend la réponse | Calculs courts, déterministes, locaux | Correlation Engine demande une donnée au GIS Engine |
| **Asynchrone (message passing)** | Faible — l'appelant publie, le moteur traite quand il peut | Tâches longues, pipeline multi-étapes | Evidence Engine publie une connaissance qualifiée → Knowledge Engine l'intègre |
| **Event-driven (pub/sub)** | Nul — l'émetteur ne sait pas qui consomme | Notifications transverses, diffusion | Learning Engine publie « modèle mis à jour » → tous les moteurs concernés se rafraîchissent |

### 2.2 Règle de choix du mode

1. **Synchrone par défaut** pour les appels intra-couche domaine
   (moteur → moteur) lorsque le calcul est court (< 1 s) et
   déterministe. Justification : simplicité, traçabilité directe,
   pas de gestion de file de messages.

2. **Asynchrone** lorsque le moteur consommateur peut mettre du temps
   (intégration dans un graphe, calcul de corrélation sur grandes
   données) ou lorsque l'appelant ne doit pas être bloqué
   (interface utilisateur en attente).

3. **Event-driven** uniquement pour les notifications transverses
   (mise à jour de modèle, invalidation de cache, synchronisation
   terminée). Jamais pour le flux principal de raisonnement — le
   flux principal est déterministe et traçable étape par étape.

**Justification :** le flux principal (Evidence → Validation) doit
être **déterministe et auditable** (CON-004, CON-005). Un pipeline
entièrement event-driven rendrait la traçabilité difficile (qui a
déclenché quoi, quand ?). Le mode synchrone pour le flux principal
garantit une chaîne d'appel explicite et journalisable. L'async et
l'event-driven sont réservés aux cas où le couplage temporel est
prohibitif.

### 2.3 Topologie de communication

```
                    ┌─────────────────────────────────┐
                    │         BUS DE MESSAGES           │
                    │  (async + event-driven)           │
                    │  File locale persistante          │
                    │  (offline-first, T-8)             │
                    └──────┬──────────────┬─────────────┘
                           │              │
            ┌──────────────▼──┐    ┌──────▼──────────┐
            │  Knowledge Eng. │    │  Learning Eng.  │
            │  (subscriber)   │    │  (subscriber)   │
            └──────────────────┘    └─────────────────┘

    FLUX PRINCIPAL (synchrone, chaîne explicite) :

    Evidence ──sync──▶ Knowledge ──sync──▶ Correlation
                                                    │
                                         ┌──────────▼──────────┐
                                         │  Moteurs domaine     │
                                         │  GIS · Climate · …   │
                                         └──────────┬──────────┘
                                                    │
              Reasoning ◀──sync── Correlation ◀─────┘
                  │
              sync│
                  ▼
              Diagnostic ──sync──▶ Recommendation ──sync──▶ Validation
```

---

## 3. Format des messages

### 3.1 Principe : structure de données, pas du code

Les messages entre moteurs sont des **structures de données
sérialisables** (serde côté Rust, Pydantic côté Python). Aucun
moteur ne reçoit du code exécutable d'un autre (sécurité, T-9).

Le format de sérialisation est **JSON** pour les messages
inter-process et **MessagePack** pour les messages in-process
(performances). Les deux sont produits depuis les mêmes schémas
typés (serde / Pydantic), garantissant la cohérence.

**Justification du choix :**
- **JSON** — universel, lisible, debuggable, interopérable avec
  TypeScript (interfaces) et Go (API temps réel) ;
- **MessagePack** — binaire compact, désérialisation rapide, pour
  les appels in-process où la lisibilité n'est pas nécessaire ;
- **Pas de protobuf/gRPC par défaut** — ajoute une couche de
  génération de code et un runtime supplémentaire. Justifié
  uniquement si le volume ou la performance l'exige (à évaluer par
  ADR dédié). L'hypothèse courante est JSON + MessagePack.

### 3.2 Enveloppe de message standard

Tout message entre moteurs respecte l'enveloppe suivante. Les champs
sont obligatoires sauf indication contraire.

```
EnveloppeMessage {
  // --- Identification ---
  message_id      : UUID v7       // identifiant unique du message
  trace_id        : UUID v7       // identifiant de trace (chaîne complète)
  parent_id       : UUID v7?      // message qui a déclenché celui-ci (null si racine)

  // --- Routage ---
  source_engine   : string        // nom du moteur émetteur (ex: "evidence")
  target_engine   : string        // nom du moteur destinataire (ex: "knowledge")
  operation       : string        // opération demandée (ex: "qualify_evidence")

  // --- Versioning ---
  contract_version: string        // version du contrat d'interface (ex: "1.2.0")

  // --- Temporalité ---
  timestamp       : ISO 8601      // heure d'émission (UTC, précision ms)
  expires_at      : ISO 8601?     // expiration (pour les messages différés)

  // --- Charge utile ---
  payload         : Payload       // structure typée propre à l'opération

  // --- Métadonnées de traçabilité ---
  evidence_level  : enum?         // niveau de preuve (A-F) si applicable (S-2)
  source_refs     : SourceRef[]?  // références des sources citées (S-1)
  audit_context   : AuditContext? // contexte d'audit (utilisateur, mission, etc.)
}
```

### 3.3 Structure de la charge utile (Payload)

La charge utile est **typée par opération**. Chaque opération d'un
moteur définit son schéma de payload dans son contrat d'interface
(livrable 206). Exemple conceptuel (pas du code métier) :

```
Payload — opération "qualify_evidence" (Evidence Engine) {
  knowledge_id    : string        // identifiant stable de la connaissance
  raw_value       : any           // valeur brute entrante
  unit            : string?       // unité si applicable
  proposed_source : SourceRef     // source proposée par l'importateur
  context         : dict          // contexte additionnel (station, date, etc.)
}

Payload — réponse "qualify_evidence" {
  knowledge_id    : string
  evidence_level  : enum          // A=Prouvé, B=Établi, ..., F=Observation (S-2)
  confidence      : float         // 0.0 à 1.0
  conflicts       : ConflictRef[]?// conflits bibliographiques détectés (S-3)
  qualified_at    : ISO 8601      // horodatage de la qualification
  trace           : TraceEntry[]  // chaîne de décision de l'Evidence Engine
}
```

### 3.4 Référence de source (SourceRef)

Toute connaissance circulant dans GSIE porte ses sources (S-1). La
structure `SourceRef` est commune à tous les messages :

```
SourceRef {
  source_id       : string        // identifiant stable de la source
  source_type     : enum          // publication | referentiel | technique | expert | observation (S-1)
  citation        : string        // citation bibliographique complète
  url             : string?       // URL ou DOI si applicable
  accessed_at     : ISO 8601      // date d'accès à la source
  version         : string?       // version du référentiel (ex: "RPF 2008")
}
```

### 3.5 Contexte d'audit (AuditContext)

```
AuditContext {
  user_id         : string?       // identifiant de l'utilisateur (si terrain)
  mission_id      : string?       // identifiant de la mission (bundle)
  station_id      : string?       // identifiant de la station concernée
  device_id       : string?       // identifiant du nœud (RFC-0003)
  offline         : boolean       // true si le message a été produit hors-ligne
  sync_pending    : boolean       // true si en attente de synchronisation
}
```

---

## 4. Gestion des erreurs et retries

### 4.1 Principes (T-7)

Conformément à la Constitution Technique (T-7) :

- les erreurs sont **journalisées avant propagation** ;
- les erreurs sont **explicites** (code, message, cause) ;
- les erreurs ne sont **jamais masquées** (pas de catch silencieux) ;
- une erreur n'est **jamais transformée en comportement par défaut**.

### 4.2 Structure d'erreur standard

Toute erreur renvoyée par un moteur respecte la structure suivante :

```
EngineError {
  error_code      : string        // code normalisé (ex: "EVIDENCE_INVALID_SOURCE")
  error_message   : string        // message lisible (français)
  error_category  : enum          // validation | not_found | timeout | internal | contract
  retryable       : boolean       // l'appelant peut-il réessayer ?
  retry_after_ms  : int?          // délai recommandé avant retry (si retryable)
  cause           : EngineError?  // erreur cause (chaînage)
  context         : dict          // contexte pour le diagnostic
  trace_id        : UUID v7       // identifiant de trace pour corrélation logs
}
```

### 4.3 Catégories d'erreurs

| Catégorie | Signification | Retryable ? | Action de l'appelant |
|---|---|---|---|
| `validation` | Les entrées ne respectent pas le contrat | Non | Corriger les entrées, ne pas réessayer tel quel |
| `not_found` | La ressource demandée n'existe pas | Non | Remonter à l'utilisateur ou créer la ressource |
| `timeout` | Le moteur n'a pas répondu dans le délai | Oui | Réessayer avec backoff (§4.4) |
| `internal` | Erreur interne du moteur | Oui (avec prudence) | Réessayer avec backoff, alerter si persistant |
| `contract` | Version de contrat incompatible | Non | Négocier la version (§5) ou échouer |

### 4.4 Stratégie de retry (backoff exponentiel)

Pour les erreurs `retryable` (timeout, internal) :

```
Retry 1 : attendre 500 ms
Retry 2 : attendre 1000 ms  (×2)
Retry 3 : attendre 2000 ms  (×2)
Retry 4 : attendre 4000 ms  (×2)
Retry 5 : attendre 8000 ms  (×2)
→ Échec définitif après 5 tentatives (total ~15.5 s)
```

**Paramètres :**
- délai initial : 500 ms ;
- multiplicateur : 2 ;
- tentatives maximales : 5 ;
- délai maximal par retry : 30 s (plafond) ;
- jitter : ±20 % du délai (évite le thundering herd).

**Justification du backoff exponentiel :** un moteur surchargé a
besoin de temps pour se rétablir. Des retries immédiats aggravent la
surcharge. Le jitter évite que tous les appelants réessayent
simultanément.

### 4.5 Circuit breaker

Au-delà des retries par message, un **circuit breaker** protège les
moteurs contre les appels en cascade vers un moteur défaillant :

| État | Condition | Comportement |
|---|---|---|
| **Fermé** (normal) | < 5 erreurs consécutives | Appels normaux |
| **Ouvert** (bloqué) | ≥ 5 erreurs consécutives | Appels rejetés immédiatement (fail-fast) pendant 30 s |
| **Semi-ouvert** (test) | Après 30 s en état ouvert | 1 appel test autorisé ; succès → fermé, échec → ouvert |

**Justification :** un moteur en panne ne doit pas entraîner tout le
pipeline dans une cascade de timeouts. Le circuit breaker échoue
vite (fail-fast) et permet au reste du système de continuer
fonctionner en mode dégradé documenté (T-8).

### 4.6 Idempotence

Toutes les opérations de moteurs sont **idempotentes** : un même
message avec le même `message_id` produit le même résultat, qu'il
soit traité une ou plusieurs fois.

**Justification :** en mode offline-first (RFC-0003 §4), les
messages peuvent être dupliqués lors de la synchronisation
(retransmission, merge). L'idempotence garantit que les doublons
n'ont pas d'effet de bord. Le `message_id` (UUID v7) est la clé de
déduplication.

---

## 5. Versioning des contrats d'interface

### 5.1 Principe (T-6)

Tout contrat d'interface est **versionné**. Une évolution de contrat
ne casse pas les consommateurs existants. Le versioning suit
**SemVer** (Semantic Versioning) adapté aux contrats d'interface :

| Changement | Type de version | Compatibilité |
|---|---|---|
| Ajout d'un champ optionnel dans la payload | **Patch** (1.0.0 → 1.0.1) | Rétrocompatible |
| Ajout d'une nouvelle opération | **Minor** (1.0.1 → 1.1.0) | Rétrocompatible |
| Suppression ou renommage d'un champ | **Major** (1.1.0 → 2.0.0) | **Cassante** — nécessite migration |

### 5.2 Négociation de version

Chaque message porte `contract_version` (§3.2). Le moteur
destinataire vérifie la compatibilité :

1. **Versions majeures identiques** → compatible (les différences
   minor/patch sont gérées par défaut de valeur pour les champs
   absents).
2. **Versions majeures différentes** → erreur `contract` (§4.3).
   L'appelant doit utiliser la version supportée par le moteur.

### 5.3 Coexistence de versions

Pendant une migration, un moteur peut supporter **deux versions
majeures simultanément** (ex: v1 et v2). La version est indiquée
dans le `contract_version` du message. Le moteur route vers
l'implémentation correspondante.

**Justification :** dans un système distribué offline-first
(RFC-0003), tous les nœuds ne se mettent pas à jour simultanément.
Un téléphone en terrain peut avoir la v1 pendant que le serveur a la
v2. La coexistence garantit que la synchronisation continue de
fonctionner pendant la transition.

### 5.4 Déprécation

Une version majeure dépréciée suit le cycle :

1. **Annonce** — la version est marquée `deprecated` dans le contrat ;
2. **Période de grâce** — 6 mois minimum (le moteur supporte v1 et
   v2) ;
3. **Retrait** — la version n'est plus supportée (major bump
   obligatoire pour les consommateurs restants).

Aucun retrait sans période de grâce (CON-010 — l'historique évolue,
il ne disparaît pas brutalement).

---

## 6. Offline-first — communication sans réseau

### 6.1 Principe (T-8, RFC-0003 §1, §4)

Les moteurs communiquent **localement** sur le nœud terminal, sans
réseau. La communication inter-nœuds (téléphone ↔ serveur) est
gérée par GSIE-Net (RFC-0003) et est **transparente** pour les
moteurs : un moteur ne sait pas s'il s'exécute localement ou
distantement.

### 6.2 File de messages persistante

En mode asynchrone et event-driven, les messages transitent par une
**file locale persistante** (SQLite sur le nœud terminal). Cette
file garantit :

- **persistance** — un message produit hors-ligne n'est pas perdu
  en cas de crash ;
- **ordre** — les messages sont traités dans l'ordre d'émission
  (par moteur, par clé de partition) ;
- **déduplication** — le `message_id` évite les doublons (§4.6) ;
- **rejeu** — en cas d'erreur, le message reste dans la file et est
  retenté (§4.4).

```
┌──────────────────────────────────────────────────────┐
│  NŒUD TERMINAL (téléphone, hors-ligne)                │
│                                                       │
│  ┌─────────┐    sync    ┌──────────────┐              │
│  │ Evidence│───────────▶│  Knowledge   │              │
│  └─────────┘            └──────┬───────┘              │
│                                │ async                │
│                                ▼                      │
│                         ┌──────────────┐              │
│                         │  FILE LOCALE  │              │
│                         │  (SQLite)     │              │
│                         │  persistante  │              │
│                         └──────┬───────┘              │
│                                │                      │
│  ┌─────────┐                   │                      │
│  │ Learning│ ◀──── event ──────┘                      │
│  └─────────┘                                          │
│                                                       │
│  ┌──────────────────────────────────────┐            │
│  │  COUCHE GSIE-NET (RFC-0003)           │            │
│  │  Synchronisation différée             │            │
│  │  (quand le réseau revient)            │            │
│  └──────────────────────────────────────┘            │
└──────────────────────────────────────────────────────┘
```

### 6.3 Synchronisation différée (RFC-0003 §4)

La synchronisation inter-nœuds suit le modèle **orienté données**
(RFC-0003 §4, §5) :

1. **Commit local** — chaque modification produite par un moteur est
   un commit sur un objet identifié (ex: arbre 154, DBH modifié) ;
2. **File de synchronisation** — les commits sont placés dans une
   file de sync (distincte de la file de messages locale) ;
3. **Fenêtre de connectivité** — quand le réseau revient, GSIE-Net
   pousse les commits vers le serveur (ou les Edge Nodes) ;
4. **Merge** — le serveur fusionne les commits, résout les conflits
   (RFC-0003 §4) ;
5. **Pull** — le serveur renvoie les commits des autres nœuds ;
6. **Intégration** — les moteurs locaux intègrent les données
   fusionnées.

**Transparence pour les moteurs :** les moteurs ne gèrent pas la
synchronisation. Ils produisent et consomment des messages locaux.
La couche GSIE-Net (infrastructure) gère la sync. Un moteur ne sait
pas si une connaissance est issue d'un commit local ou distant.

### 6.4 Conflits de synchronisation

Lorsque deux nœuds modifient le même objet hors-ligne (RFC-0003 §4) :

| Type de conflit | Stratégie | Justification |
|---|---|---|
| **Champs différents** | Merge automatique (champ par champ) | Pas de conflit réel — les deux modifications coexistent |
| **Même champ, valeurs différentes** | Conflit documenté, résolution manuelle ou par règle métier | S-3 : pas de fusion arbitraire sans justification |
| **Suppression vs modification** | Préservation de la modification (la suppression est annulée) | CON-010 : l'historique ne disparaît pas |

Tout conflit est **journalisé** avec les deux versions, les
`device_id` et les horodatages. Le conflit est signalé à
l'utilisateur si la résolution automatique n'est pas possible
(RFC-0003 §8 — le serveur pilote la qualité).

---

## 7. Journalisation et traçabilité

### 7.1 Chaîne de trace (trace_id)

Chaque message porte un `trace_id` (UUID v7). Ce trace_id est
propagé à tous les messages enfants (via `parent_id`). La chaîne
complète d'un diagnostic, de l'acquisition à la recommandation, est
reconstituable à partir du `trace_id`.

### 7.2 Entrée de journal (LogEntry)

Chaque moteur produit des entrées de journal structurées (T-7) :

```
LogEntry {
  timestamp       : ISO 8601      // horodatage (UTC, ms)
  trace_id        : UUID v7       // chaîne de trace
  message_id      : UUID v7       // message traité
  engine          : string        // moteur émetteur
  operation       : string        // opération effectuée
  level           : enum          // debug | info | warn | error
  duration_ms     : int           // durée de traitement
  result          : enum          // success | error | degraded
  error           : EngineError?  // erreur si applicable
  context         : dict          // contexte additionnel
}
```

### 7.3 Immuabilité du journal

Le journal est **append-only** (CON-010). Aucune entrée n'est
modifiée ou supprimée. Le journal est stocké localement (SQLite) et
synchronisé avec le serveur (GSIE-Net).

---

## 8. Résumé des règles

| Règle | Référence | Statut |
|---|---|---|
| Communication par interfaces contractuelles uniquement | T-2 | Obligatoire |
| Aucun accès direct à l'implémentation interne d'un autre moteur | T-1 | Obligatoire |
| Graphe de dépendances acyclique | T-1 | Obligatoire |
| Messages = structures de données sérialisables, pas du code | T-9 | Obligatoire |
| Toute erreur est journalisée avant propagation | T-7 | Obligatoire |
| Pas de catch silencieux | T-7 | Obligatoire |
| Opérations idempotentes (déduplication par message_id) | RFC-0003 §4 | Obligatoire |
| Contrats versionnés (SemVer) | T-6 | Obligatoire |
| Coexistence de versions majeures pendant migration | T-6, CON-010 | Obligatoire |
| File locale persistante pour l'offline-first | T-8, RFC-0003 §1 | Obligatoire |
| Synchronisation orientée données (commits), pas orientée messages | RFC-0003 §4, §5 | Obligatoire |
| Trace_id propagé sur toute la chaîne | CON-005 | Obligatoire |
| Journal append-only | CON-010 | Obligatoire |
| Niveau de preuve affiché à l'utilisateur | S-2 | Obligatoire |

---

## 9. Ce que ce document ne fait PAS

- Il n'implémente aucun code (Phase 2 — interdit, DEC-000004).
- Il ne définit pas les contrats détaillés de chaque moteur
  (livrable 206 — `ENGINE_INTERFACE_CONTRACTS.md`).
- Il ne définit pas le protocole réseau GSIE-Net (RFC-0003).
- Il ne choisit pas de format de sérialisation définitif pour tous
  les cas (JSON/MessagePack par défaut, gRPC à évaluer par ADR).
- Il ne contredit aucun article constitutionnel.

---

## 10. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — version squelette (Phase 1) |
| 2026-07-12 | Enrichissement Phase 2 — modes, format, erreurs, versioning, offline-first |

---

## 11. Validation

Document en statut **Draft**. Passage en `Review` soumis à
validation du Fondateur. Aucune modification destructive sans
versionnement préalable (CON-010, T-6).
