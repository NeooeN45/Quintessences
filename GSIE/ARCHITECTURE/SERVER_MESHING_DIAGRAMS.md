# SERVER MESHING — Diagrammes

| Champ | Valeur |
|---|---|
| **Document** | Diagrammes — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **Format** | ASCII art — convertible en Mermaid pour la documentation future (voir note finale) |

## Note préliminaire

Ces diagrammes illustrent l'architecture conceptuelle décrite dans
RFC-0035 (§3, §4) et les décisions du registre ADR
(`SERVER_MESHING_ADR.md`). Ils sont volontairement schématiques :
le détail technique complet relève de l'architecture cible
(`SERVER_MESHING_TARGET.md`). Aucun diagramme ci-dessous
n'introduit de dépendance hard à Unreal Engine 6 ni ne suppose une
persistance en mémoire comme source de vérité.

---

## 1. Diagramme de composants

```
┌───────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATEUR DE MESH                        │
│  - Graphe d'autorité (zone + type)                                │
│  - Découpage spatial adaptatif                                    │
│  - Décisions de transfert d'autorité                              │
│  - Journal d'audit immuable                                       │
└───────────────┬───────────────────────────────┬───────────────────┘
                │  Redis Pub/Sub                 │  Redis Pub/Sub
                │  (bus inter-nœuds, mTLS)        │
   ┌────────────▼────────────┐        ┌──────────▼──────────────┐
   │   SERVEURS DE ZONE       │        │  SERVEURS SPÉCIALISÉS   │
   │  (autorité spatiale)     │        │  (autorité par type)    │
   │  - Zone Landiras (proto) │        │  - Simulation           │
   │  - Zone Aquitaine (V1)   │        │  - Learning              │
   │  - Zone Corse (V1)       │        │  - Knowledge             │
   │  - ...                   │        │  - Drones                │
   └────────────┬─────────────┘        └──────────┬───────────────┘
                │                                    │
                └───────────────────┬────────────────┘
                                    │  Écriture/lecture (SQL)
                    ┌───────────────▼────────────────────┐
                    │       COUCHE DE PERSISTANCE          │
                    │  PostgreSQL/PostGIS (source vérité)  │
                    │  Métamodèle v6.2 (bitemporel)        │
                    │  Graphe d'autorité persisté           │
                    └───────────────┬────────────────────┘
                                    │  Flux répliqué (pertinence)
                    ┌───────────────▼────────────────────┐
                    │         CLIENTS DE RENDU             │
                    │  Hub UE5.8 (salle de commandement)   │
                    │  CesiumJS web (léger, distant)       │
                    │  Apps mobiles terrain (offline-first)│
                    └───────────────────────────────────────┘
```

**Légende** :
- `→` (trait plein) : flux de données ou de commande.
- Orchestrateur : composant unique logique (ADR-016), haute disponibilité
  hors périmètre du prototype.
- Serveurs de zone / spécialisés : instances multiples, interchangeables
  (P-MESH-07).
- Couche de persistance : source de vérité unique (ADR-011), jamais
  contournée.
- Clients de rendu : consommateurs uniquement, aucune autorité (ADR-011).

---

## 2. Diagramme de flux de données

```
[Observation terrain / capteur / opérateur]
        │
        ▼
[Ingestion — Evidence Engine]
        │  qualification A-F, SourceReference
        ▼
[Serveur de zone compétent (autorité spatiale)]
        │  écriture obligatoire avant validité (P-MESH-02)
        ▼
[COUCHE DE PERSISTANCE — PostgreSQL/PostGIS]
        │  bitemporel : temps de validité + temps de transaction
        ▼
[Graphe d'autorité mis à jour]
        │
        ├──────────────► [Bus Redis Pub/Sub — notification de changement]
        │                         │
        │                         ▼
        │              [Serveurs intéressés — réplication par pertinence]
        │                         │
        ▼                         ▼
[Journal d'audit — traçabilité]  [Clients de rendu abonnés]
                                    │
                                    ▼
                        [Rendu opérateur — Hub / web / terrain]
```

**Légende** :
- La persistance intervient **avant** toute notification — aucun état
  n'est considéré valide avant écriture en base (ADR-011).
- La réplication vers les clients de rendu est filtrée par pertinence
  (ADR-012), pas diffusée intégralement.
- Le journal d'audit est alimenté en parallèle de la mise à jour du
  graphe d'autorité, jamais en différé (P-MESH-06).

---

## 3. Diagramme de transfert d'autorité (séquence handoff entre deux serveurs de zone)

```
Opérateur      Serveur Zone A     Orchestrateur     Serveur Zone B     Persistance
   │                 │                  │                  │                │
   │ déplacement ────►│                  │                  │                │
   │  vers frontière  │                  │                  │                │
   │                 │  entité approche  │                  │                │
   │                 │  frontière ──────►│                  │                │
   │                 │                  │ décision de       │                │
   │                 │                  │ transfert          │                │
   │                 │                  │ (P-MESH-03/06)     │                │
   │                 │                  │───── prépare ─────►│                │
   │                 │                  │      handoff        │                │
   │                 │                  │                    │  lit dernier    │
   │                 │                  │                    │  état ─────────►│
   │                 │                  │                    │◄──── état ──────│
   │                 │◄── confirme B prêt ──────────────────│                │
   │                 │  transfère       │                  │                │
   │                 │  autorité ───────►│                  │                │
   │                 │                  │──── notifie ──────►│                │
   │                 │                  │     transfert       │                │
   │                 │                  │                    │  devient        │
   │                 │                  │                    │  autorité       │
   │                 │                  │                    │  ───────────────►│
   │                 │                  │                    │  (écrit)        │
   │                 │                  │◄── confirme ────────│                │
   │                 │  arrête de       │                  │                │
   │                 │  répliquer        │                  │                │
   │                 │                  │──── journal ───────────────────────►│
   │                 │                  │     audit (identifiant traçable)     │
   │  continuité ────────────────────────────────────────────►│                │
   │  perçue (sans coupure)                                    │                │
```

**Légende** :
- Le transfert d'autorité est arbitré par l'orchestrateur, jamais par
  négociation directe non journalisée entre serveurs de zone (ADR-016).
- L'écriture en persistance précède la confirmation du transfert
  (ADR-011) : le serveur B ne devient autorité qu'après lecture
  cohérente de l'état.
- L'opérateur ne perçoit aucune coupure (P-MESH-01) : le client de
  rendu bascule son abonnement sans interruption visible.
- Chaque étape porte un identifiant traçable inscrit au journal
  d'audit (P-MESH-06).

---

## 4. Diagramme de partitionnement spatial (grille adaptative)

```
Situation normale (charge homogène) :

  ┌────┬────┬────┬────┐
  │ Z1 │ Z2 │ Z3 │ Z4 │     Chaque cellule = 1 serveur de zone
  ├────┼────┼────┼────┤     Granularité uniforme
  │ Z5 │ Z6 │ Z7 │ Z8 │
  └────┴────┴────┴────┘

Situation d'alerte (incendie détecté en Z6) :

  ┌────┬────┬────┬────┐
  │ Z1 │ Z2 │ Z3 │ Z4 │     Zones en veille (charge faible)
  ├────┼────┼────┼────┤     ────────────────────────────
  │ Z5 │6a│6b│ Z7 │ Z8 │     Z6 subdivisée en sous-cellules
  │    ├──┼──┤    │    │     haute précision (6a, 6b, ...)
  │    │6c│6d│    │    │     Ressources concentrées (P-MESH-04)
  └────┴──┴──┴────┴────┘
```

**Légende** :
- `Z1`...`Z8` : cellules de grille en régime normal, granularité
  uniforme.
- `6a`...`6d` : subdivision adaptative de la cellule Z6 lorsqu'une
  métrique de charge (alerte incendie, activité de simulation, nombre
  d'opérateurs) dépasse un seuil documenté (ADR-018).
- Zones grisées conceptuellement « en veille » : ressources de calcul
  et de rendu réduites, sans arrêt de la persistance sous-jacente.
- Toute subdivision/fusion est décidée par l'orchestrateur et
  journalisée (P-MESH-06).

---

## 5. Diagramme de séquence — navigation opérateur traversant une frontière de serveur

```
Opérateur (Hub)        Client de rendu        Serveur Zone A     Serveur Zone B
     │                       │                       │                  │
     │  déplace la caméra ──►│                       │                  │
     │                       │  entité dans          │                  │
     │                       │  frustum + marge ─────►│                  │
     │                       │◄── flux répliqué ──────│                  │
     │  rendu continu ◄──────│                       │                  │
     │                       │                       │                  │
     │  franchit la          │                       │                  │
     │  frontière ──────────►│                       │                  │
     │                       │  frustum recouvre     │                  │
     │                       │  désormais Zone B ────┼─────────────────►│
     │                       │◄──────────────────────┼── flux répliqué ─│
     │  rendu continu ◄──────│                       │                  │
     │  (aucune coupure       │                       │                  │
     │   visible, P-MESH-01) │                       │                  │
```

**Légende** :
- Le client de rendu maintient une scène unique et s'abonne
  simultanément à plusieurs serveurs (P-MESH-01, RFC-0035 §3.1).
- L'abonnement au flux de la zone B démarre avant la désinscription
  complète de la zone A pour éviter tout trou de rendu (chevauchement
  volontaire de marge, cf. réplication par pertinence, ADR-012).
- Ce diagramme concerne le rendu ; le transfert d'autorité applicatif
  correspondant est détaillé dans le diagramme 3.

---

## 6. Diagramme de séquence — panne d'un serveur de zone et bascule

```
Orchestrateur      Serveur Zone A (down)     Persistance      Serveur de secours
     │                     │                       │                  │
     │── heartbeat ───────►│                       │                  │
     │◄── (timeout, pas de réponse) ─────           │                  │
     │  détecte panne      │                       │                  │
     │  (P-MESH-06 :        │                       │                  │
     │   journalise         │                       │                  │
     │   l'incident)         │                       │                  │
     │                     │                       │                  │
     │── requête dernier ──┼──────────────────────►│                  │
     │   état connu Zone A  │                       │                  │
     │◄── état bitemporel ──┼───────────────────────│                  │
     │   (ADR-011, ADR-014) │                       │                  │
     │                     │                       │                  │
     │── désigne serveur ──┼───────────────────────┼─────────────────►│
     │   de secours          │                       │                  │
     │                     │                       │  reconstitue     │
     │                     │                       │  état ◄──────────│
     │                     │                       │                  │
     │◄── confirme prêt ────┼───────────────────────┼──────────────────│
     │── déclare nouvelle ──┼───────────────────────┼─────────────────►│
     │   autorité (journal   │                       │                  │
     │   d'audit)             │                       │                  │
     │                     │                       │                  │
     │── notifie clients ──┼───────────────────────┼──────────────────►│
     │   de rendu (nouveau    │                       │  bascule flux    │
     │   flux à écouter)       │                       │                  │
```

**Légende** :
- Aucun état n'est perdu : le serveur de secours reconstitue son état
  entièrement depuis la persistance externe (ADR-011), jamais depuis
  une réplique mémoire du serveur en panne.
- La bitemporalité (ADR-014) garantit que l'état reconstitué correspond
  au dernier état valide connu, avec son historique complet.
- La détection de panne et la désignation du serveur de secours sont
  intégralement journalisées (P-MESH-06, RISK-MESH-009).
- Ce scénario ne suppose aucune haute disponibilité native de
  l'orchestrateur lui-même — sujet distinct, voir ADR-016 et
  RISK-MESH-010.

---

## 7. Diagramme de déploiement (topologie réseau, régions, datacenters)

```
┌─────────────────────────── RÉGION AQUITAINE ───────────────────────────┐
│                                                                          │
│   ┌────────────────────┐        ┌────────────────────┐                 │
│   │  Datacenter A       │        │  Datacenter B        │                │
│   │  - Serveur Zone     │  mTLS  │  - PostgreSQL/PostGIS│                │
│   │    Landiras (proto) │◄──────►│    (source vérité)   │                │
│   │  - Redis Pub/Sub    │        │  - Réplication         │                │
│   │    (nœud local)      │        │    logique (Vague 3)  │                │
│   └──────────┬──────────┘        └──────────────────────┘                │
│              │ mTLS                                                       │
└──────────────┼─────────────────────────────────────────────────────────┘
               │
               │  Réseau inter-régions (mTLS, RFC-0035 §6.3 GSIE-Net)
               │
┌──────────────┼─────────────────────────────────────────────────────────┐
│              ▼                    RÉGION EXTENSION (V1, hors proto)     │
│   ┌────────────────────┐        ┌────────────────────┐                 │
│   │  Datacenter C        │        │  ORCHESTRATEUR         │                │
│   │  - Serveur Zone       │  mTLS  │  DE MESH (centralisé) │                │
│   │    (V1, ex. Corse)     │◄──────►│  - Graphe d'autorité   │                │
│   │  - Serveurs            │        │  - Journal d'audit     │                │
│   │    spécialisés         │        │    immuable            │                │
│   └────────────────────┘        └──────────┬─────────────┘                │
└─────────────────────────────────────────────┼──────────────────────────┘
                                               │  Redis Pub/Sub, mTLS
                                    ┌──────────▼──────────┐
                                    │  CLIENTS DE RENDU     │
                                    │  Hub UE5.8 (LAN/VPN)  │
                                    │  CesiumJS (Internet)  │
                                    │  Apps terrain (offline)│
                                    └───────────────────────┘
```

**Légende** :
- Périmètre du prototype v0 (RFC-0035 §5.2 option A) : uniquement le
  bloc « Région Aquitaine » (zone Landiras), sans orchestrateur
  multi-régions actif.
- Le bloc « Région Extension » illustre la cible du prototype v1
  (deux régions) — non déployé au périmètre actuel.
- Toute liaison inter-datacenter et inter-région est mTLS (ADR-017).
- La réplication logique PostgreSQL cross-région est explicitement
  différée (ADR-011, note de phasage) au-delà du prototype.

---

## 8. Diagramme d'états — cycle de vie d'une entité dans le mesh

```
                    ┌──────────────┐
                    │   CRÉATION    │
                    │ (ingestion,   │
                    │  Evidence      │
                    │  Engine)       │
                    └──────┬───────┘
                           │ écriture persistance (ADR-011)
                           ▼
                    ┌──────────────┐
              ┌────►│  SOUS AUTORITÉ │◄────┐
              │     │  D'UN SERVEUR   │     │
              │     │  (zone et/ou    │     │
              │     │   type, ADR-010)│     │
              │     └──────┬───────┘     │
              │            │ franchissement de frontière
              │            │ ou changement de pertinence type
              │            ▼
              │     ┌──────────────┐
              │     │   TRANSFERT    │
              │     │  D'AUTORITÉ    │
              │     │   (handoff,    │
              │     │  diagramme 3)  │
              │     └──────┬───────┘
              │            │ confirmation persistance
              └────────────┘
                           │
                           │ fin de pertinence
                           │ (archivage, obsolescence)
                           ▼
                    ┌──────────────┐
                    │  DESTRUCTION   │
                    │ (archivage      │
                    │  bitemporel,    │
                    │  jamais de      │
                    │  suppression     │
                    │  physique de     │
                    │  l'historique)   │
                    └──────────────┘
```

**Légende** :
- « Destruction » ne signifie jamais suppression physique de
  l'historique : le métamodèle bitemporel (ADR-014, CON-010) conserve
  la trace de toute entité, même hors d'usage opérationnel.
- Le cycle « sous autorité → transfert → sous autorité » peut se répéter
  un nombre indéfini de fois au cours de la vie d'une entité mobile
  (ex. front de feu, drone).
- Toute transition d'état est journalisée (P-MESH-06).

---

## Note de convertibilité Mermaid

Les diagrammes ci-dessus sont rédigés en ASCII art pour rester lisibles
sans rendu graphique et pour ne dépendre d'aucun outil externe pendant
la phase de cadrage (Vague 2). Ils sont conçus pour être **convertibles**
en syntaxe Mermaid (`graph`, `sequenceDiagram`, `stateDiagram-v2`) dans
une itération future de la documentation technique, sans changement de
structure logique — chaque bloc, flèche et légende ci-dessus correspond
directement à un nœud, une arête ou une note Mermaid équivalente. Cette
conversion est différée à la production de la documentation technique
de référence (Vague 3, hors périmètre de ce document).
