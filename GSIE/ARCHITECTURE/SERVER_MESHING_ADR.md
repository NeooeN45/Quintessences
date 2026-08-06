# SERVER MESHING — Registre des ADR

| Champ | Valeur |
|---|---|
| **Document** | Registre ADR — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 |
| **RFC/ADR de référence** | RFC-0003 (GSIE-Net), RFC-0011 (métamodèle v6.2), ADR-002 (bitemporalité PostgreSQL), ADR-007 (API WebSocket + Redis), livrable 203 (communication moteurs) |
| **Portée** | Ce registre centralise les décisions d'architecture structurantes du chantier Server Meshing (RFC-0035). Chaque ADR reste subordonné à la Constitution (`00_CONSTITUTION/`) et aux 8 principes fondateurs P-MESH-01 à P-MESH-08. |

## Note de gouvernance

Ce document ne modifie aucun contrat d'interface de moteur GSIE existant
(`GSIE/ENGINES/<NOM>_ENGINE/README.md`). Toute évolution de contrat
nécessite une RFC dédiée, conformément à CON-007. Les ADR ci-dessous
sont numérotés dans la continuité du registre existant
(ADR-001 à ADR-009, `GSIE/ARCHITECTURE/`) pour éviter toute collision
d'identifiant.

---

## ADR-010 — Autorité hybride zone + type

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §5.1, option C) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Le graphe d'autorité doit déterminer, pour toute entité du jumeau et
tout instant t, quel serveur en est responsable. Deux modèles simples
existaient : autorité par zone spatiale seule (inspiration directe du
Server Object Authority de Star Citizen) ou autorité par type d'entité
seule (spécialisation fonctionnelle). RFC-0035 §5.1 documente les
options A, B et C.

### Décision

L'autorité est **hybride** : la zone spatiale est l'axe primaire (tout
serveur de zone possède les entités spatiales de son secteur), le type
d'entité est l'axe secondaire (des serveurs spécialisés — Simulation,
Learning, Knowledge, Drones — possèdent les entités transverses ou non
spatiales, indépendamment de la zone). Les conflits entre les deux axes
sont résolus par une table de priorité documentée et versionnée dans
la couche de persistance, jamais par un arbitrage implicite en code.

### Conséquences

**Positives**

- Continuité spatiale garantie pour l'opérateur (P-MESH-01) sans
  sacrifier la spécialisation fonctionnelle (simulation longue durée,
  apprentissage continu).
- Compatible avec l'existant : les 14 moteurs GSIE restent
  responsables d'un domaine, le mesh ajoute une couche de
  distribution spatiale sans redéfinir leur périmètre.

**Négatives**

- Complexité de résolution des conflits (une entité peut être
  disputée entre un serveur de zone et un serveur spécialisé).
- Nécessite une table de priorité explicite, elle-même sujette à
  évolution et donc à gouvernance (RFC si la priorité change de
  sémantique, DEC si seule la valeur change).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| A — Zone seule | Sous-optimal pour les entités transverses (drones, simulations, apprentissage) qui n'ont pas de position spatiale stable ou unique. |
| B — Type seul | Casse la continuité spatiale (P-MESH-01) : deux entités voisines pourraient dépendre de deux serveurs sans relation de proximité, rendant le rendu continu impossible à garantir. |

---

## ADR-011 — Persistance externe PostgreSQL comme source de vérité

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §2.3, §3.2) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Le Server Meshing multiplie le nombre de serveurs porteurs d'état.
Sans source de vérité externe unique, chaque serveur pourrait diverger
silencieusement, et une panne entraînerait une perte d'état
irrécupérable. Le principe P-MESH-02 (persistance externe obligatoire)
et CON-003/CON-007 imposent déjà qu'Unreal Engine ne soit jamais la
source de vérité (livrable 211 §0.2, ADR-001 livrable 208).

### Décision

PostgreSQL/PostGIS, structuré par le métamodèle v6.2 bitemporel
(RFC-0011), est la **seule** source de vérité du jumeau numérique
distribué. Aucun serveur du mesh (zone ou spécialisé) ne peut
considérer un état comme valide avant qu'il ne soit persisté en base.
L'état en mémoire d'un serveur (zone ou spécialisé, Unreal ou worker)
est une **projection reconstructible**, jamais une vérité autonome.

### Conséquences

**Positives**

- Tout serveur du mesh peut être tué et redémarré sans perte de
  connaissance (reconstitue son état depuis PostgreSQL).
- Cohérent avec l'existant : prolonge directement ADR-001/ADR-002 et
  le principe déjà acté pour le Hub UE5.8 seul.
- Simplifie l'audit : une seule base canonique à interroger pour
  toute question de traçabilité (CON-005, CON-010).

**Négatives**

- Latence d'écriture systématique avant validation d'un état —
  incompatible avec un besoin de temps réel dur (non requis ici,
  GSIE fait de la simulation scientifique, pas de la physique de
  jeu temps réel, cf. RFC-0035 §2.4).
- PostgreSQL devient un point de contention potentiel si le nombre de
  serveurs de zone croît fortement — nécessite une stratégie de
  partitionnement/réplication logique (suivi en Vague 3, hors
  périmètre du prototype Landiras).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| État en mémoire UE comme référence, persistance en tâche de fond asynchrone | Contredit directement P-MESH-02 et le principe déjà constitutionnalisé qu'Unreal Engine n'est pas la source de vérité. Réintroduirait le risque de perte d'état à la panne, exactement le défaut que le Server Meshing doit corriger (RFC-0035 §2.1 point 3). |

---

## ADR-012 — Réplication par pertinence (Replication Graph) vs réplication totale

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §2.4) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Un serveur de zone ou un client de rendu n'a pas besoin de connaître
l'état complet du jumeau : seules les entités visibles, interagissantes
ou pertinentes pour son périmètre courant doivent être répliquées.
Inspiration directe du Replication Graph de Star Citizen (RFC-0035
§2.4), à adapter à un contexte scientifique et non ludique.

### Décision

Le mesh réplique **par pertinence** : un serveur ou un client ne reçoit
que les entités visibles depuis sa zone (frustum + marge pour les
clients de rendu) ou interagissantes avec son périmètre fonctionnel
(pour les serveurs spécialisés). La réplication totale (chaque serveur
reçoit l'état complet du mesh) est écartée comme mode par défaut.

### Conséquences

**Positives**

- Réduit la charge réseau et le coût de calcul, cohérent avec
  P-MESH-04 (concentration dynamique des ressources).
- Permet la scalabilité du mesh à mesure que le nombre de régions et
  d'entités augmente (au-delà du prototype mono-région).

**Négatives**

- Introduit une logique de filtrage de pertinence qui doit
  elle-même être testée et documentée — un bug de filtrage peut
  masquer une entité pertinente sans erreur visible.
- Le calcul de pertinence dynamique alourdit l'orchestrateur (ADR-016)
  qui doit maintenir une vue à jour des zones d'intérêt.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Réplication totale | Ne passe pas à l'échelle au-delà d'une seule région. Contredit P-MESH-04 (concentration dynamique) : un serveur inactif recevrait autant de données qu'un serveur actif. |

### Note de phasage

Le prototype mono-région (Landiras) ne nécessite pas de filtrage de
pertinence inter-serveurs complexe — un seul serveur possède toute la
zone. Cet ADR fixe le principe cible ; son implémentation complète est
différée à l'extension multi-régions (RFC-0035 §5.2, option B).

---

## ADR-013 — Redis Pub/Sub pour bus inter-nœuds

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (existant, étendu) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

L'API GSIE utilise déjà Redis Pub/Sub comme bus de messages
(ADR-007, livrable 203). Le Server Meshing doit choisir un bus
inter-nœuds pour la communication entre l'orchestrateur, les serveurs
de zone et les serveurs spécialisés. Les alternatives usuelles pour ce
type de topologie sont Kafka, NATS ou un protocole custom au-dessus de
GSIE-Net (RFC-0003).

### Décision

Redis Pub/Sub reste le bus inter-nœuds du mesh pour le prototype
mono-région et l'extension multi-régions à périmètre limité (RFC-0035
§5.2, options A et B). L'infrastructure existante (ADR-007) est
étendue, pas remplacée.

### Conséquences

**Positives**

- Aucune nouvelle dépendance technologique à ce stade — cohérent avec
  la mise en garde RFC-0035 §7 contre le choix prématuré d'une
  technologie de service mesh.
- Continuité avec l'existant en production (ADR-007) : pas de
  migration, pas de double infrastructure de messagerie à maintenir.
- Suffisant pour le volume de messages du prototype (une région,
  nombre limité de serveurs spécialisés).

**Négatives**

- Redis Pub/Sub ne garantit pas la livraison (fire-and-forget) : un
  message perdu lors d'une coupure réseau n'est pas rejoué. Ce risque
  est couvert par la persistance PostgreSQL (ADR-011), qui reste la
  vérité de référence indépendamment du bus.
- Ne passe pas nativement à l'échelle cross-région à très fort volume
  (contrairement à Kafka) — réévaluation explicitement prévue si le
  mesh dépasse le périmètre multi-régions.

### Alternatives rejetées (pour ce stade)

| Option | Raison du rejet à ce stade |
|---|---|
| Kafka | Sur-ingénierie pour un prototype mono-région (RFC-0035 §8, risque « sur-ingénierie avant besoin réel »). Complexité opérationnelle disproportionnée par rapport au volume actuel. |
| NATS | Introduirait une nouvelle dépendance sans bénéfice démontré au périmètre du prototype. À réévaluer si le besoin de garanties de livraison (JetStream) devient structurant. |
| Protocole custom sur GSIE-Net | GSIE-Net (RFC-0003) est encore à l'état de proposition. Construire un bus custom avant la stabilisation de GSIE-Net inverserait l'ordre des dépendances. |

### Clause de réévaluation

Cette décision est **révisable sans RFC** dès que le mesh dépasse
2 régions actives simultanément ou que la garantie de livraison des
messages devient un exigence documentée (voir ADR-019, mode dégradé).
Toute migration effective vers Kafka ou NATS nécessite en revanche un
nouvel ADR et une décision tracée.

---

## ADR-014 — Bitemporalité du métamodèle v6.2 comme mécanisme de réplication

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §2.3, §6.3) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

La réplication multi-serveurs pose un problème classique de résolution
de conflits : deux serveurs peuvent proposer des états divergents pour
une même entité (ex. lors d'un handoff mal synchronisé). Les modèles
usuels de résolution sont les CRDTs (Conflict-free Replicated Data
Types), le last-write-wins (LWW), ou l'exploitation de la bitemporalité
déjà présente dans le métamodèle v6.2 (Revision + Snapshot +
ResourceDiff + PROV-O, ADR-002).

### Décision

La résolution de conflit de réplication s'appuie sur la
**bitemporalité du métamodèle v6.2** déjà adoptée (ADR-002, RFC-0011) :
chaque écriture porte un temps de validité métier et un temps de
transaction, ce qui permet de départager deux propositions d'état
concurrentes sans perte d'historique, quel que soit l'ordre d'arrivée
réseau.

### Conséquences

**Positives**

- Aucune nouvelle structure de données à introduire — le mesh
  s'appuie sur un mécanisme déjà validé et implémenté (ADR-002).
- Préserve intégralement la traçabilité (P-MESH-06, CON-010) : un
  conflit résolu reste visible dans l'historique, contrairement au
  LWW qui écrase silencieusement une version.
- Cohérent avec P-MESH-08 (subordination à la connaissance) : la
  résolution de conflit ne peut jamais faire disparaître une
  observation, même contredite ultérieurement.

**Négatives**

- Plus complexe à raisonner qu'un LWW simple pour les développeurs
  non familiers du modèle bitemporel — nécessite une documentation
  d'usage dédiée pour les futurs contributeurs du mesh.
- Ne résout pas seule les conflits de **logique métier** (deux
  serveurs modifiant la même entité pour des raisons contradictoires) :
  la bitemporalité horodate les versions, la sémantique de résolution
  fine reste à documenter par domaine (Reasoning, Diagnostic) au fil
  de l'implémentation.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| CRDTs | Introduit une famille de structures de données supplémentaire, redondante avec la bitemporalité déjà en place. Les CRDTs excellent pour la convergence automatique sans coordination, mais le mesh GSIE a déjà une autorité hybride explicite (ADR-010) qui rend la convergence automatique moins nécessaire qu'une résolution par autorité + historique. |
| Last-write-wins | Contredit directement P-MESH-06 (traçabilité complète) et CON-010 (évolution sans perte d'historique) : un LWW écrase une version sans en garder la trace exploitable au même niveau que la bitemporalité. |

---

## ADR-015 — Interfaces abstraites pour compatibilité UE6 anticipée

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §5.3, option B) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Le Centre de Commandement GSIE fonctionne actuellement sous
Unreal Engine 5.8. UE6 n'est pas publié à la date de rédaction. Trois
postures sont possibles face à cette incertitude (RFC-0035 §5.3) :
dépendre exclusivement d'UE5.8, définir des interfaces abstraites
compatibles avec une future migration, ou cibler explicitement UE6 dès
maintenant.

### Décision

Le mesh est défini par des **interfaces abstraites** (transport,
réplication, autorité, rendu) indépendantes d'Unreal Engine. UE5.8 est
l'implémentation actuelle du client de rendu ; UE6 sera, le cas échéant,
une implémentation future de la même interface. Aucune dépendance hard
à une version spécifique d'Unreal Engine n'est introduite dans les
contrats de mesh.

### Conséquences

**Positives**

- Élimine tout risque de blocage si UE6 est retardé, change de
  primitives, ou n'est jamais adopté (P-MESH-07, modularité).
- Le client CesiumJS web et les apps mobiles terrain, déjà envisagés
  comme clients de rendu alternatifs (RFC-0035 §4), bénéficient de la
  même interface sans traitement spécial.

**Négatives**

- Légère surcharge d'abstraction dès l'implémentation initiale
  (couche d'interface même quand un seul client existe).
- Le contrat abstrait doit être conçu avec soin pour ne pas figer
  prématurément des hypothèses propres à UE5.8 qui se révéleraient
  incompatibles avec UE6 — risque résiduel documenté dans le registre
  de risques (RISK-MESH-006).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| UE5.8 uniquement, sans abstraction | Migration future coûteuse — toute évolution vers UE6 nécessiterait de retraverser l'ensemble du code de mesh. Contredit P-MESH-07. |
| UE6 comme cible explicite dès maintenant | Dépendance à un produit non publié ; risque de construire sur des primitives hypothétiques qui ne correspondront pas à la version finale d'UE6. |

---

## ADR-016 — Orchestrateur de mesh centralisé

| Champ | Valeur |
|---|---|
| **Statut** | Accepté |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Le mesh a besoin d'une fonction qui décide du découpage spatial, de
l'allocation des serveurs et des transferts d'autorité (RFC-0035 §4).
Deux familles d'approches existent : un orchestrateur centralisé
(vue unique, décisions arbitrées) ou un modèle décentralisé de type
gossip (chaque serveur négocie localement avec ses voisins, sans
autorité centrale).

### Décision

Le mesh adopte un **orchestrateur centralisé** pour le prototype
mono-région et l'extension multi-régions à périmètre limité. Il détient
la vue d'ensemble du graphe d'autorité, décide des transferts et
journalise chaque décision (P-MESH-06).

### Conséquences

**Positives**

- Un seul point de vérité pour les décisions de mesh, ce qui
  simplifie considérablement la traçabilité et l'audit (CON-005,
  CON-010) par rapport à un consensus distribué.
- Le nombre de serveurs du prototype (une région, quelques serveurs
  spécialisés) reste dans le domaine de validité d'un orchestrateur
  centralisé — un modèle gossip serait une réponse à un problème
  d'échelle qui n'existe pas encore (risque de sur-ingénierie,
  RFC-0035 §8).

**Négatives**

- Point de défaillance unique potentiel — nécessite une stratégie de
  haute disponibilité (réplication de l'orchestrateur lui-même, ou
  reconstruction rapide depuis PostgreSQL) documentée avant tout
  déploiement multi-régions à fort enjeu opérationnel.
- Ne passe pas nativement à un très grand nombre de régions —
  clause de réévaluation explicite ci-dessous.

### Alternatives rejetées (pour ce stade)

| Option | Raison du rejet à ce stade |
|---|---|
| Décentralisé type gossip | Complexité de mise en œuvre et de preuve de correction disproportionnée par rapport au périmètre du prototype mono-région et de l'extension à deux régions. Rendrait la traçabilité des décisions de mesh (P-MESH-06) beaucoup plus difficile à garantir formellement. |

### Clause de réévaluation

À documenter par une nouvelle RFC si le mesh doit dépasser un nombre
de régions rendant l'orchestrateur centralisé un goulot d'étranglement
démontré par métrique (voir registre de risques, RISK-MESH-010).

---

## ADR-017 — mTLS pour la sécurité inter-nœuds

| Champ | Valeur |
|---|---|
| **Statut** | Accepté |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Les communications entre l'orchestrateur, les serveurs de zone et les
serveurs spécialisés transitent sur un réseau qui peut, à terme,
traverser plusieurs datacenters ou régions. Une sécurisation
inter-nœuds est requise, cohérente avec les standards de sécurité
transverses du projet (`/securite-gsie`).

### Décision

L'authentification et le chiffrement inter-nœuds du mesh utilisent
**mTLS** (authentification mutuelle par certificat) entre tous les
composants serveur du mesh (orchestrateur, serveurs de zone, serveurs
spécialisés). Les clients de rendu (Hub UE5.8, apps terrain) restent
authentifiés par le mécanisme JWT déjà en place côté API GSIE — mTLS
concerne strictement le plan inter-serveurs.

### Conséquences

**Positives**

- Chaque nœud du mesh prouve son identité à chaque connexion, sans
  dépendre d'un secret partagé statique qui, s'il est compromis,
  compromettrait l'ensemble du mesh.
- Cohérent avec les principes de sécurité par défaut du projet
  (HTTPS partout, pas de fallback non chiffré).

**Négatives**

- Nécessite une infrastructure de gestion de certificats (émission,
  rotation, révocation) — coût opérationnel non nul, à budgétiser
  dès le prototype pour éviter une dette de sécurité différée.
- Complexifie le déploiement local de développement (certificats
  auto-signés nécessaires même en environnement de test).

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Token partagé (shared secret) | Point de compromission unique : la fuite d'un seul token expose l'ensemble du mesh sans possibilité de révocation fine par nœud. |
| VPN inter-nœuds | Ajoute une couche réseau supplémentaire à opérer sans bénéfice d'authentification applicative fine par nœud ; ne remplace pas la nécessité d'authentifier chaque service, seulement le transport. |

---

## ADR-018 — Partitionnement spatial par grille adaptative

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §2.4, §3.4) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Le partitionnement spatial doit permettre au mesh de concentrer
dynamiquement les ressources sur les zones actives (P-MESH-04) sans
imposer un découpage figé. Les modèles usuels sont la grille adaptative
(cellules redécoupées selon la charge), le quadtree (subdivision
récursive hiérarchique) et le diagramme de Voronoï (cellules définies
par des points d'ancrage).

### Décision

Le partitionnement spatial du mesh repose sur une **grille adaptative** :
les zones sont des cellules dont la granularité se resserre localement
en fonction de métriques de charge (activité de simulation, nombre
d'opérateurs connectés, alertes en cours), conformément à l'inspiration
Star Citizen documentée en RFC-0035 §2.4 (spatial partitioning).

### Conséquences

**Positives**

- Redécoupage local simple à raisonner et à journaliser (P-MESH-06) :
  une cellule se subdivise ou fusionne, sans recalcul global de la
  structure.
- Correspond directement au cas d'usage cité en RFC-0035 §2.1
  (incendie en Corse nécessitant une sous-zone haute précision) sans
  nécessiter de restructuration complexe de l'arbre spatial global.

**Négatives**

- Moins efficace qu'un quadtree pour représenter des densités
  d'entités très hétérogènes sur de grandes étendues vides — risque
  jugé acceptable au périmètre du prototype mono-région, à réévaluer
  à l'extension multi-régions.
- Le redécoupage adaptatif introduit une logique de seuil (quand
  subdiviser, quand fusionner) qui doit être documentée et testée
  pour éviter un battement (oscillation) de la topologie.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Quadtree | Plus complexe à journaliser de façon lisible pour l'audit (P-MESH-06) : la structure hiérarchique récursive rend le suivi d'un redécoupage individuel moins direct qu'une cellule de grille. Réévaluable si la densité d'entités devient très hétérogène à l'échelle nationale. |
| Diagramme de Voronoï | Dépend de points d'ancrage dont le déplacement recalcule l'ensemble des frontières de cellules — comportement moins prévisible et plus coûteux à tracer qu'un redécoupage local de grille. |

---

## ADR-019 — Mode dégradé offline-first en cas de partition réseau

| Champ | Valeur |
|---|---|
| **Statut** | Accepté (RFC-0035 §3.5, P-MESH-05) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000053 |

### Contexte

Le théorème CAP impose un choix face à une partition réseau entre
disponibilité et cohérence forte. Le projet a déjà tranché ce choix au
niveau des nœuds terminaux (RFC-0003 §4, modèle Git offline-first) ;
il reste à confirmer ce choix explicitement au niveau du mesh de
serveurs, conformément à P-MESH-05.

### Décision

En cas de partition réseau entre serveurs du mesh, le système privilégie
la **disponibilité** (mode dégradé offline-first) plutôt que la
cohérence forte. Un serveur de zone isolé continue de servir ses
clients de rendu locaux avec l'état dont il dispose, journalise ses
écritures localement, et se resynchronise avec la couche de persistance
et le reste du mesh au retour de connectivité, en s'appuyant sur la
bitemporalité (ADR-014) pour réconcilier les divergences.

### Conséquences

**Positives**

- Cohérent avec le modèle déjà en production pour les nœuds terminaux
  (RFC-0003) : le mesh étend un principe déjà validé plutôt que d'en
  introduire un nouveau.
- Un opérateur en zone d'intervention (ex. incendie) n'est jamais
  bloqué par une coupure réseau vers l'orchestrateur central.

**Négatives**

- Fenêtre de divergence temporaire entre l'état local d'un serveur
  isolé et l'état global du mesh — acceptable pour un jumeau
  scientifique traçable (la réconciliation est historisée), mais
  exige une documentation claire du mode dégradé pour les opérateurs.
- La réconciliation à la reconnexion peut révéler des conflits de
  logique métier au-delà de ce que la bitemporalité résout seule
  (ADR-014) — nécessite des règles de résolution par domaine, à
  documenter au fil de l'implémentation.

### Alternatives rejetées

| Option | Raison du rejet |
|---|---|
| Cohérence forte (blocage en cas de partition) | Contredit directement P-MESH-05 et le principe offline-first déjà constitutionnalisé pour l'ensemble du projet (T-8). Bloquerait un opérateur terrain précisément dans les situations où la continuité de service est la plus critique (crise, incendie). |

---

## Suivi du registre

| ADR | Statut | Prochaine étape |
|---|---|---|
| ADR-010 | Accepté | Détail dans l'architecture cible (Vague 2) |
| ADR-011 | Accepté | Aucune — cohérent avec l'existant |
| ADR-012 | Accepté | Implémentation différée à l'extension multi-régions |
| ADR-013 | Accepté | Clause de réévaluation si >2 régions actives |
| ADR-014 | Accepté | Documentation des règles de résolution par domaine à produire |
| ADR-015 | Accepté | Conception du contrat d'interface abstrait (Vague 3) |
| ADR-016 | Accepté | Stratégie de haute disponibilité de l'orchestrateur à documenter |
| ADR-017 | Accepté | Infrastructure de gestion de certificats à budgétiser |
| ADR-018 | Accepté | Seuils de subdivision/fusion à documenter et tester |
| ADR-019 | Accepté | Règles de résolution de conflit par domaine à produire |
