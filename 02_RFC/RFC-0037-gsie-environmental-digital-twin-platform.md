# RFC-0037 — GSIE Environmental Digital Twin Platform

| Champ | Valeur |
|---|---|
| **ID** | RFC-0037 |
| **Titre** | GSIE Environmental Digital Twin Platform — plateforme de jumeau numérique environnemental fédéré |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation (cadrage de la plateforme cible) |
| **Auteur** | Camille Perraudeau (Fondateur) — proposition instruite par l'Architecte GSIE |
| **Date d'ouverture** | 2026-08-06 |
| **RFC de référence** | RFC-0011 (métamodèle v6.2), RFC-0029 (organisation physique des données), RFC-0035 (Server Meshing), RFC-0036 (Territorial Mesh) |
| **Directives liées** | GSIE-DIR-0005, GSIE-DIR-0009, GSIE-DIR-0013 |
| **Décisions liées** | DEC-000010, DEC-000013, DEC-000054 |
| **Impact** | Architecture GSIE, Hub Unreal, API, State Fabric, contrats inter-applications, GeoSylva, Ignis, Hydro, Flora, Artemis, QGISIA |

---

## 1. Résumé

Cette RFC propose de formaliser GSIE comme une **plateforme de jumeau
numérique environnemental fédéré**.

> **GSIE est un jumeau numérique environnemental fédéré. GeoSylva,
> Ignis, Hydro, Flora et Artemis sont des projections métier
> spécialisées de ce jumeau. Les Hubs Unreal sont les environnements
> immersifs permettant d'explorer, simuler et, sous contrôle humain,
> interagir avec les domaines concernés.**

GSIE ne doit donc plus être documenté comme un moteur central auquel des
applications indépendantes envoient des données isolées. Il devient le
socle partagé d'un ensemble de domaines environnementaux interconnectés,
avec un état canonique, des projections spécialisées, des simulations
branchées et des contrats d'échange versionnés.

Cette RFC ne fusionne pas les applications et ne donne pas au Hub Unreal
la responsabilité des moteurs scientifiques. Elle formalise leur
fédération.

## 2. Problème

Les documents existants décrivent correctement :

- GSIE comme moteur de connaissance et de raisonnement ;
- le Hub comme client de visualisation multi-applications ;
- Ignis comme jumeau numérique opérationnel du feu ;
- GeoSylva comme application forestière offline-first ;
- le Territorial Mesh comme couche de gouvernance ;
- le Server Meshing comme couche d'exécution distribuée.

Il manque toutefois une architecture de niveau supérieur qui définisse :

1. comment une observation GeoSylva devient une donnée exploitable par Ignis ;
2. comment un événement Ignis influence GeoSylva ou Hydro ;
3. comment les applications partagent des ressources sans dépendre
   directement les unes des autres ;
4. comment séparer l'état réel, la prévision et les scénarios ;
5. comment un Hub spécialisé reste performant tout en partageant le même
   territoire numérique ;
6. comment les demandes d'action passent d'une interface immersive vers
   un système opérationnel sans contourner l'autorité humaine.

## 3. Décision proposée

Adopter une architecture en quatre niveaux :

```text
Applications et Hubs spécialisés
        ↓ contrats de projection et d'action
GSIE Domain Services et moteurs scientifiques
        ↓ ressources, événements, simulations
State Fabric environnemental fédéré
        ↓ persistance, provenance, historique, réplication
Territorial Mesh + Server Meshing
        ↓ gouvernance territoriale + allocation technique
Infrastructure et edge
```

### 3.1 Projections métier

Chaque domaine expose une projection spécialisée du même jumeau :

| Projection | Domaine | Responsabilités principales |
|---|---|---|
| **GeoSylva** | Forêt | Inventaire, peuplements, essences, croissance, martelage, rendement, régénération |
| **Ignis** | Incendie | Détection, propagation, assimilation, enjeux, moyens, risques, scénarios de crise |
| **Hydro** | Eau | Écoulements, bassins versants, réseaux, nappes, karst, crues, qualité de l'eau |
| **Flora** | Végétation | Taxonomie, répartition, phénologie, habitats végétaux, changements écologiques |
| **Artemis** | Faune | Observations, habitats, populations, corridors, impacts et déplacements |
| **QGISIA** | SIG et analyse | Exploration, préparation, analyse et export géospatial |
| **Hub Unreal** | Immersion et supervision | Exploration, visualisation, comparaison, interaction contrôlée et supervision |

Une projection peut produire des ressources pour les autres domaines,
mais elle ne modifie jamais directement leur état interne.

### 3.2 Hubs spécialisés

Un même socle Unreal peut proposer plusieurs modes ou plugins métier :

- Hub Ignis : crise incendie, front, météo, drones, véhicules, aéronefs ;
- Hub GeoSylva : visite forestière, évolution temporelle, rendement,
  martelage et scénarios sylvicoles ;
- Hub Hydro : écoulements, crues, réseaux souterrains et karstiques ;
- Hub scientifique : comparaison de couches et scénarios multi-domaines.

Ces modes partagent le territoire, les entités, les observations et les
scénarios, mais conservent leurs modèles et workflows spécialisés.

## 4. Modèle d'échange canonique

Toute donnée inter-domaines doit utiliser une ressource GSIE versionnée,
une enveloppe d'événement ou une projection explicitement documentée.

### 4.1 Ressources communes

Les types suivants sont transverses :

- `TerritorialResource` ;
- `Observation` ;
- `EnvironmentalState` ;
- `Forecast` ;
- `Scenario` ;
- `SimulationRun` ;
- `SimulationResult` ;
- `Mission` ;
- `ActionRequest` ;
- `Recommendation` ;
- `Decision` ;
- `ProvenanceRecord`.

Chaque ressource porte au minimum :

```text
resource_id
resource_type
schema_version
source_domain
source_application
geometry
spatial_reference
valid_time
transaction_time
provenance
confidence
status
scenario_id (optionnel)
trace_id
```

### 4.2 Distinction des états

Une donnée ne peut pas être à la fois une observation réelle et une
prévision non signalée.

| État | Signification |
|---|---|
| **Réel** | Observation ou état validé du territoire |
| **Dérivé** | Résultat calculé à partir de données réelles |
| **Prévision** | Projection probable avec incertitude |
| **Simulé** | Résultat d'un scénario hypothétique |
| **Proposé** | Recommandation non validée par l'opérateur |
| **Décidé** | Action validée par l'autorité compétente |

Les scénarios sont des branches :

```text
État réel canonique
  ├── Scénario incendie aggravé
  ├── Scénario changement d'essences
  ├── Scénario régénération naturelle
  ├── Scénario crue post-incendie
  └── Scénario intervention validée
```

Une simulation ne modifie jamais silencieusement l'état réel.

## 5. Interconnexion des domaines

### 5.1 GeoSylva → Ignis

GeoSylva peut publier :

- structure et densité des peuplements ;
- essences et strates de combustible ;
- biomasse et état hydrique ;
- accès forestiers et pistes ;
- travaux sylvicoles et coupures de combustible ;
- observations terrain versionnées.

Ignis consomme ces données pour alimenter la propagation, l'analyse des
enjeux et les scénarios de risque.

### 5.2 Ignis → GeoSylva

Ignis peut publier :

- surfaces brûlées ;
- intensité et durée d'exposition ;
- mortalité estimée ;
- zones de régénération à surveiller ;
- risque de dépérissement post-incendie ;
- observations et historiques de feu.

GeoSylva peut créer des scénarios de restauration, de changement
d'essences et d'évolution des peuplements.

### 5.3 Hydro ↔ Ignis

Hydro fournit à Ignis :

- points d'eau ;
- accessibilité hydraulique ;
- bassins versants ;
- état des sols et de l'humidité ;
- risques d'inondation ou de ruissellement.

Ignis fournit à Hydro :

- perte de couvert végétal ;
- zones brûlées ;
- sols exposés ;
- risque d'érosion et de ruissellement post-incendie.

### 5.4 Flora et Artemis

Flora et Artemis partagent avec GeoSylva et Ignis :

- habitats ;
- observations ;
- corridors ;
- changements de végétation ;
- impacts des incendies, sécheresses et crues.

Les observations restent attribuées à leur domaine producteur et ne sont
pas fusionnées sans règle de provenance et de résolution.

## 6. Interactions et actions physiques

Le Hub peut :

- sélectionner une entité ;
- afficher son état et sa provenance ;
- lancer un scénario ;
- comparer des résultats ;
- annoter une zone ;
- demander une observation ;
- préparer une mission ;
- proposer une trajectoire ;
- soumettre une demande d'action.

Il ne commande jamais directement un drone, un véhicule, un Canadair,
une vanne ou un autre acteur physique.

Le flux normatif est :

```text
Intention opérateur
    ↓
ActionRequest versionnée
    ↓
Contrôle d'autorité territoriale et RBAC
    ↓
Validation humaine requise si action critique
    ↓
Adaptateur opérationnel autorisé
    ↓
Accusé de réception et état d'exécution
    ↓
Audit et retour vers le jumeau
```

Les systèmes externes restent propriétaires de leurs protocoles de
commande. GSIE les intègre via des adaptateurs, sans contourner les
systèmes réglementaires ou les téléopérateurs.

## 7. Performance et interconnectivité

Les flux sont classés par criticité :

| Classe | Exemple | Transport et cible |
|---|---|---|
| **P0 temps réel** | Télémétrie, front actif, alerte critique | WebSocket ou flux équivalent, p95 à mesurer et état périmé explicite |
| **P1 opérationnel** | Propagation, vecteurs météo, scénarios rapides | Flux asynchrone priorisé, recalage Ignis autour de 5 min |
| **P2 volumineux** | LiDAR, 3D Tiles, splats, rasters | HTTP/objet/tileset, cache et streaming spatial |
| **P3 différé** | Historique, RETEX, recalculs nationaux | Jobs asynchrones, reproductibles et versionnés |

Règles de performance :

- le rendu Unreal ne bloque jamais sur un calcul scientifique lourd ;
- les flux sont spatialisés, filtrés par pertinence et limités par LOD ;
- les données statiques sont servies en tuiles et mises en cache ;
- les événements sont soumis au backpressure et à la déduplication ;
- une donnée périmée est signalée, jamais présentée comme actuelle ;
- chaque projection peut fonctionner avec le dernier état cohérent connu.

## 8. Relation avec les architectures existantes

- RFC-0011 fournit le métamodèle et la bitemporalité ;
- RFC-0029 organise les schémas et projections physiques ;
- RFC-0035 fournit le Server Meshing ;
- RFC-0036 fournit le Territorial Mesh ;
- `HUB-002` fournit le contrat de couches Hub ;
- `ENGINE_COMMUNICATION_PROTOCOL.md` fournit l'enveloppe des messages
  entre moteurs ;
- GeoSylva reste offline-first ;
- Ignis reste le premier cas opérationnel du jumeau vivant.

Cette RFC ajoute la fédération des domaines sans fusionner leurs moteurs,
leurs dépôts ou leurs bases internes.

## 9. Phasage proposé

### P0 — Contrats communs

- valider l'enveloppe de ressource inter-domaines ;
- définir les états réel/dérivé/prévision/simulé/proposé/décidé ;
- définir la provenance et la bitemporalité ;
- étendre HUB-002 sans casser les couches existantes.

### P1 — Tranche Ignis

- replay d'un incendie historique (voir `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_USE_CASES.md`, UC-001 et UC-003) ;
- front simulé ;
- météo et enjeux ;
- drone simulé ;
- scénario comparatif ;
- Hub Unreal ;
- journal complet.

### P2 — Interopérabilité GeoSylva/Ignis

- peuplements et combustibles vers Ignis ;
- contours brûlés et impacts vers GeoSylva ;
- séparation stricte des observations et scénarios.

### P3 — Hydro et impacts croisés

- écoulement et bassins versants ;
- ruissellement post-incendie (UC-001) ;
- crues éclair et karst (UC-004) ;
- crues et zones vulnérables ;
- affichage multi-domaines dans le Hub.

### P4 — Fédération territoriale et Server Meshing

- cellules spécialisées ;
- réplication par pertinence ;
- handoffs ;
- mode dégradé ;
- concentration dynamique du calcul.

## 10. Critères d'acceptation de la RFC

La proposition sera prête pour validation lorsque :

1. le contrat inter-domaines est versionné et relié à HUB-002 ;
2. un événement GeoSylva peut être consommé par Ignis sans accès direct à
   la base GeoSylva ;
3. un résultat Ignis peut être affiché dans GeoSylva comme donnée dérivée
   ou scénario, sans écraser l'observation forestière ;
4. un scénario ne peut pas modifier l'état réel sans décision explicite ;
5. le Hub affiche l'origine, la date, la version, l'incertitude et le
   statut de chaque donnée ;
6. une demande de commande critique exige une validation humaine et un
   audit complet ;
7. une coupure réseau n'empêche pas la consultation du dernier état
   cohérent connu ;
8. les performances sont mesurées par classe P0/P1/P2/P3.

## 11. Hors périmètre

- remplacement immédiat des bases propres aux applications ;
- commande autonome d'aéronefs ou de drones ;
- adoption d'un broker distribué supplémentaire sans preuve de besoin ;
- fédération internationale ;
- implémentation simultanée de tous les domaines ;
- migration forcée de `AdministrativeUnitModel` ;
- dépendance obligatoire à UE6 ou AWS.

## 12. Statut de la proposition

RFC-0037 est une proposition Draft. Elle formalise la vision de
plateforme et n'autorise pas à elle seule une modification de contrat
public, une commande physique, une migration de schéma ou une mise en
production opérationnelle.
