# GSIE Territorial Mesh — Diagrammes

| Champ | Valeur |
|---|---|
| **Livrable** | TERRITORIAL_MESH_DIAGRAMS |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date** | 2026-08-06 |
| **RFC** | RFC-0036 |
| **RFC de référence** | RFC-0035 (GSIE Server Meshing) |
| **Format** | ASCII art — convertible en Mermaid pour la documentation future |

## Note préliminaire

Ces diagrammes illustrent l'architecture conceptuelle du Territorial
Mesh décrite dans RFC-0036 (§3 et suivants) et détaillée dans
`TERRITORIAL_MESH_STATE_FABRIC.md`, `TERRITORIAL_MESH_EVENT_BUS.md` et
`TERRITORIAL_MESH_MATRICES.md`. Ils sont volontairement schématiques ;
aucun diagramme n'introduit de dépendance à une implémentation
spécifique et n'infirme le principe de source de vérité unique
(ADR-011).

---

## 1. Diagramme de composants

```
┌─────────────────────────────────────────────────────────────────┐
│                                NCP                                │
│   National Control Plane — PostgreSQL national                   │
│   gsie_gouvernance · carte territoriale · audit fédéré           │
│   Bus national (Redis Pub/Sub)                                    │
└───────────────────────────────┬───────────────────────────────────┘
                                 │ mTLS (ADR-017)
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│      RCH        │      │      RCH        │      │      RCH        │
│  Region A        │      │  Region B        │      │  Region N        │
│  PostgreSQL       │      │  PostgreSQL       │      │  PostgreSQL       │
│  Bus régional      │      │  Bus régional      │      │  Bus régional      │
└────────┬──────────┘      └────────┬──────────┘      └────────┬──────────┘
         │                          │                          │
    ┌────┴────┐                ┌────┴────┐                ┌────┴────┐
    ▼         ▼                ▼         ▼                ▼         ▼
┌───────┐ ┌───────┐        ┌───────┐ ┌───────┐        ┌───────┐ ┌───────┐
│  DOD   │ │  DOD   │        │  DOD   │ │  DOD   │        │  DOD   │ │  DOD   │
│ Dépt 1 │ │ Dépt 2 │        │ Dépt 3 │ │ Dépt 4 │        │ Dépt … │ │ Dépt … │
│PostgreS│ │PostgreS│        │PostgreS│ │PostgreS│        │PostgreS│ │PostgreS│
│ Bus dép │ │ Bus dép │        │ Bus dép │ │ Bus dép │        │ Bus dép │ │ Bus dép │
└───┬───┘ └───┬───┘        └───┬───┘ └───┬───┘        └───┬───┘ └───┬───┘
    │         │                │         │                │         │
┌───▼───┐ ┌───▼───┐        ┌───▼───┐ ┌───▼───┐        ┌───▼───┐ ┌───▼───┐
│Cellule│ │Cellule│        │Cellule│ │Cellule│        │Cellule│ │Cellule│
│Spatiale│ │Spatiale│       │Spatiale│ │Spatiale│       │Spatiale│ │Spatiale│
└───┬───┘ └───┬───┘        └───┬───┘ └───┬───┘        └───┬───┘ └───┬───┘
    │         │                │         │                │         │
    ▼         ▼                ▼         ▼                ▼         ▼
  Edge      Edge              Edge      Edge              Edge      Edge
(capsule) (capsule)         (capsule) (capsule)         (capsule) (capsule)
```

---

## 2. Diagramme de hiérarchie territoriale

```
France
  │
  ├── Région (RCH)
  │     │
  │     ├── Département (DOD)
  │     │     │
  │     │     ├── Territoire Opérationnel
  │     │     │     │
  │     │     │     ├── Cellule Spatiale
  │     │     │     │     │
  │     │     │     │     ├── Sous-cellule
  │     │     │     │     └── Sous-cellule
  │     │     │     │
  │     │     │     └── Cellule Spatiale
  │     │     │
  │     │     └── Territoire Opérationnel
  │     │
  │     └── Département (DOD)
  │
  └── Région (RCH)
```

**Légende** : chaque niveau hérite de l'autorité de son parent pour ce
qui relève de la gouvernance, mais dispose d'une autorité métier
propre à son périmètre (voir `TERRITORIAL_MESH_MATRICES.md` §2).

---

## 3. Diagramme de flux de données

```
[NCP]  gouvernance, référentiel territorial
   │  ▲
   │  │ synthèse           │ politiques
   ▼  │
[RCH]  coordination régionale, cache tiède
   │  ▲
   │  │ réplication continue  │ politiques relayées
   ▼  │
[DOD]  autorité métier, source de vérité, cache chaud
   │  ▲
   │  │ commandes / résultats  │ capsules
   ▼  │
[Cellule]  simulation locale, exécution de mission
   │  ▲
   │  │ acquisition terrain     │ capsule signée
   ▼  │
[Edge]  offline-first, SQLite/SQLCipher, sync différentielle
```

---

## 4. Diagramme de transfert d'autorité

### 4.1 Handoff inter-cellules (au sein d'un même DOD)

```
Cellule A          DOD             Cellule B
   │                 │                  │
   │ approche ───────►│                  │
   │ frontière        │                  │
   │                  │ décision handoff │
   │                  ├─────────────────►│
   │                  │                  │ prise d'autorité
   │◄─────────────────┤                  │
   │ libération        │                  │
   │                  │ persistance +    │
   │                  │ epoch fencing    │
```

### 4.2 Handoff inter-niveaux (transfert d'autorité DOD → DOD via RCH)

```
DOD Source        RCH             DOD Cible
   │                 │                  │
   │ demande de       │                  │
   │ transfert ───────►│                  │
   │                  │ vérification     │
   │                  │ autorité         │
   │                  ├─────────────────►│
   │                  │                  │ accepte
   │◄─────────────────┤◄─────────────────┤
   │ confirmation      │ notification     │
   │                  │ fédérée (NCP)    │
```

---

## 5. Diagramme de charge (concentration dynamique)

```
Situation normale :

NCP  ───────────────────────────────────────  (charge minimale)
RCH-A [██]  RCH-B [██]  RCH-C [██]           (charge équilibrée)
DOD-1 [█] DOD-2 [█] DOD-3 [█] DOD-4 [█]      (charge équilibrée)

Montée en crise (DOD-3 déclare crisis.declared) :

NCP  ─────────────────────────────────────── [█]  (supervision accrue)
RCH-A [██]  RCH-B [██]  RCH-C [████████]           (priorisation région C)
DOD-1 [█] DOD-2 [█] DOD-3 [██████████] DOD-4 [░]   (DOD-3 priorisé,
                                                       DOD-4 dégradé si
                                                       ressources partagées)
```

---

## 6. Diagramme offline (edge en autonomie)

```
┌──────────────────────────────────────────────────┐
│                     DOD                            │
│  1. Construit capsule .gsiecap pour la mission     │
│  2. Signe (Ed25519) — clé de confiance externe      │
└─────────────────────┬──────────────────────────────┘
                      │ transfert avant départ
                      ▼
┌──────────────────────────────────────────────────┐
│                    EDGE                            │
│  3. Vérifie signature + intégrité (SHA-256)         │
│  4. Charge dans SQLite/SQLCipher                     │
│  5. Fonctionne en autonomie totale (offline)         │
│     — acquisition terrain, exécution mission          │
│  6. Accumule les modifications localement             │
└─────────────────────┬──────────────────────────────┘
                      │ retour réseau
                      ▼
┌──────────────────────────────────────────────────┐
│                     DOD                            │
│  7. Sync différentielle (jeton de sync)              │
│  8. Résolution de conflit si nécessaire (arbitrage)  │
│  9. Écriture append-only (aucune perte, CON-010)     │
└──────────────────────────────────────────────────┘
```

---

## 7. Diagramme de réplication State Fabric

```
                     ┌───────────────┐
                     │      NCP        │
                     └───────▲───────┘
                             │ synthèse
                     ┌───────┴───────┐
                     │      RCH        │
                     └───────▲───────┘
                             │ réplication logique continue
                     ┌───────┴───────┐
                     │      DOD        │
                     └───────▲───────┘
                             │ sync différentielle (capsule)
                     ┌───────┴───────┐
                     │      Edge       │
                     └───────────────┘
```

*Voir `TERRITORIAL_MESH_STATE_FABRIC.md` §4 et §11 pour le détail des
flux et des fréquences.*

---

## 8. Diagramme du bus fédéré

```
┌──────────────────────────────────────────────┐
│                Bus national (NCP)               │
└─────────────────────▲────┬──────────────────────┘
       fédération ascendante│  │fédération descendante
                            │  ▼
┌──────────────────────────────────────────────┐
│               Bus régional (RCH) ×N             │
└─────────────────────▲────┬──────────────────────┘
                            │  ▼
┌──────────────────────────────────────────────┐
│            Bus départemental (DOD) ×N            │
└─────────────────────▲────┬──────────────────────┘
                            │  ▼
┌──────────────────────────────────────────────┐
│                 Bus de cellule                    │
└──────────────────────────────────────────────┘
```

*Voir `TERRITORIAL_MESH_EVENT_BUS.md` §3 et §11 pour le détail des
types d'événements et de la fédération.*

---

## 9. Diagramme de sécurité

```
┌───────────────────────────────────────────────────────────┐
│  NCP ⇄ RCH ⇄ DOD ⇄ Cellule       mTLS (ADR-017)             │
│  Chaque flux authentifié par certificat de service           │
└───────────────────────────┬───────────────────────────────┘
                             │
┌───────────────────────────▼───────────────────────────────┐
│  RBAC territorial                                             │
│  NCP : rôles de gouvernance nationale                         │
│  RCH : rôles de coordination régionale                        │
│  DOD : rôles métier départementaux                             │
│  Cellule : rôles de simulation locale                          │
│  Edge : RBAC local restreint à la mission (capsule)             │
└───────────────────────────┬───────────────────────────────┘
                             │
┌───────────────────────────▼───────────────────────────────┐
│  Audit                                                        │
│  Journal fédéré immuable (NCP) ← relais audit (RCH, DOD)      │
│  Journal de mission dans la capsule (Edge)                     │
└───────────────────────────┬───────────────────────────────┘
                             │
┌───────────────────────────▼───────────────────────────────┐
│  Chiffrement                                                  │
│  At-rest : volumes PostgreSQL (NCP/RCH/DOD)                     │
│  At-rest local : SQLCipher (Edge)                               │
└───────────────────────────────────────────────────────────┘
```

---

## 10. Diagramme du prototype v0 (Nouvelle-Aquitaine)

```
┌───────────────────────────────────────────────────────────┐
│                     RCH — Nouvelle-Aquitaine                  │
│              PostgreSQL régional · cache Redis régional         │
└───────────────┬─────────────────────────────┬───────────────┘
                │                              │
        ┌───────▼────────┐            ┌────────▼───────┐
        │  DOD — Charente  │            │ DOD — Deux-Sèvres│
        │  PostgreSQL       │            │  PostgreSQL       │
        │  départemental      │            │  départemental      │
        └───────┬────────┘            └────────┬───────┘
                │                              │
        ┌───────▼────────┐                     │
        │ Cellule Spatiale │                     │
        │ (Territoire       │                     │
        │  Opérationnel #1) │                     │
        └───────┬────────┘                     │
                │                     ┌────────▼───────┐
                ▼                     │ Cellule Spatiale │
        ┌────────────────┐            │ (Territoire       │
        │  Edge — Drone 1  │            │  Opérationnel #2) │
        │  capsule .gsiecap │            └────────────────┘
        │  SQLite/SQLCipher │
        └────────────────┘
```

**Périmètre du prototype** : 1 région (Nouvelle-Aquitaine), 2
départements (Charente, Deux-Sèvres), 2 cellules spatiales, 1 drone
edge. Ce périmètre restreint permet de valider la chaîne complète
NCP-optionnel → RCH → DOD → Cellule → Edge sans complexité de
volumétrie nationale, conformément à l'approche incrémentale de
RFC-0035 (Vague 1).
