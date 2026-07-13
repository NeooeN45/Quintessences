# GSIE Knowledge Graph Specification — Spécification du graphe de connaissances

| Champ | Valeur |
|---|---|
| **Livrable** | 304 — Knowledge Graph Specification |
| **Phase** | 3 — Connaissance |
| **Statut** | Validated |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-3, S-5, S-7) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |
| **Documents connexes** | `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` (302), `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` (303), `GSIE/ARCHITECTURE/ENGINE_INTERFACE_CONTRACTS.md` (206), `01_DIRECTIVES/ACTIVE/GSIE-DIR-0006.md` |

---

## 1. Objet

Définir la structure formelle du graphe de connaissances de GSIE :
les types de nœuds, les types d'arêtes, leurs propriétés, les
patterns de requête, le versionnement des relations et le support du
graphe vivant exigé par la directive GSIE-DIR-0006.

Cette spécification opérationnalise trois exigences constitutionnelles :

- **CON-010** — toute relation évolue sans perdre son historique ;
- **S-3** — les conflits bibliographiques sont documentés, jamais
  résolus arbitrairement ;
- **S-5** — l'incertitude est explicite, quantifiée et affichée.

Elle sert de source de vérité unique pour l'implémentation du
Knowledge Engine en Phase 4. Le schéma formel des `KnowledgeObject`
est défini au livrable 206 (contrats d'interface) et au livrable 302
(méthode de gestion des connaissances). Le présent document spécifie
la **topologie du graphe** qui contient ces objets.

---

## 2. Types de nœuds

Le graphe contient deux familles de nœuds : les **KnowledgeObject**
(nœuds de connaissance, sourcés et versionnés) et les **entités
externes** (nœuds du domaine forestier, référencés par les
connaissances).

### 2.1 Nœuds de connaissance (KnowledgeObject)

Les six types de `KnowledgeObject` définis au livrable 302 sont les
nœuds porteurs de connaissance. Chaque nœud possède un
`connaissance_id` stable (UUID v7), un `evidence_level` (S-2), une
`source` (S-1) et un `historique` versionné (CON-010).

| Type | Description | Exemple |
|---|---|---|
| `concept` | Notion scientifique définie | « Réserve utile en eau (RUM) » |
| `relation` | Relation typée entre deux entités ou concepts | « chêne sessile est_adapte_a sol acide » |
| `regle` | Règle d'inférence applicable par le Reasoning Engine | « SI pH ∈ [4,5 ; 6,0] ET altitude < 1400 m ALORS chêne sessile adapté » |
| `seuil` | Valeur seuil scientifiquement établie | « RUM minimale pour le hêtre = 80 mm » |
| `modele` | Modèle scientifique (croissance, dynamique, propagation) | « ONF-FFN pour le douglas » |
| `classification` | Classification ou taxonomie référentielle | « Alocrisol (RPF, INRAE 2008) » |

### 2.2 Entités externes

Les entités externes sont les nœuds du domaine forestier. Elles ne
sont pas des `KnowledgeObject` : elles ne portent pas de niveau de
preuve ni d'historique versionné. Elles sont **référencées** par les
connaissances (les arêtes pointent vers elles).

| Type | Description | Source référentielle | Exemple |
|---|---|---|---|
| `Essence` | Espèce forestière (nom scientifique + vernaculaire) | GBIF / BD Forêt | `Quercus petraea` (chêne sessile) |
| `Station` | Station forestière (localisation + caractéristiques) | Référentiel stationnel régional | Station « chênaie acidiphile, Limousin » |
| `Sol` | Type ou profil de sol | RPF / WRB | Alocrisol |
| `Climat` | Contexte climatique (historique ou projection) | Météo-France / Drias | Climat atlantique, déficit hydrique 120 mm |
| `Habitat` | Habitat écologique (syntaxonomie) | EUR28 / Cahiers d'habitats | 41.2 — Chênaies-charmaies |
| `Publication` | Source scientifique référencée | DOI / bibliographie | Rameau et al. (2018) |

### 2.3 Schéma de la topologie

```
                    +------------------+
                    |   Publication    |
                    +------------------+
                           |
                    est_valide_par
                           |
    +-----------+   est_adapte_a   +-----------+   influence   +-----------+
    |  Essence  | ----------------> |   Sol     | <------------ |  Climat   |
    +-----------+                   +-----------+               +-----------+
         |                              |                           |
    croit_mieux_sur                 depend_de                  influence
         |                              |                           |
         v                              v                           v
    +-----------+                +-----------+               +-----------+
    |  Station  |                |  Seuil    |               | Modele    |
    +-----------+                | (KO)      |               | (KO)      |
         |                       +-----------+               +-----------+
    est_adapte_a                      ^
         |                        contredit
         v                            |
    +-----------+                +-----------+
    | Habitat   |                | Seuil     |
    +-----------+                | (KO alt.) |
                                 +-----------+

    Légende : KO = KnowledgeObject
    Les entités externes (Essence, Station, Sol, Climat, Habitat,
    Publication) sont des nœuds référencés.
    Les KnowledgeObject (Seuil, Modele, Regle, Concept, Relation,
    Classification) sont des nœuds sourcés et versionnés.
```

---

## 3. Types d'arêtes (relations)

Les arêtes du graphe sont les relations entre nœuds. Chaque arête est
elle-même un `KnowledgeObject` de type `relation` (voir livrable 302,
section 3.2) et hérite donc du versionnement CON-010.

### 3.1 Table complète des relations

| Relation | Description | Direction | Cardinalité | Versionnée | Exemple |
|---|---|---|---|---|---|
| `est_adapte_a` | Une essence est adaptée à une condition (sol, climat, station) | Essence -> Sol / Climat / Station | n:m | Oui | chêne sessile -> sol acide pH 4,5-6,0 |
| `influence` | Un facteur affecte un autre facteur ou une essence | Source -> Cible | n:m | Oui | pH -> disponibilité nutriments |
| `depend_de` | Une connaissance nécessite une autre pour être valide | KO -> KO | n:m | Oui | règle d'adaptation -> seuil de pH |
| `est_valide_par` | Une connaissance est confirmée par une source | KO -> Publication | n:1 | Oui | seuil de gel -> publication 2015 |
| `contredit` | Deux connaissances sont en conflit (S-3) | KO -> KO | n:m | Oui | seuil -20 degC -> contredit -> seuil -15 degC |
| `croit_mieux_sur` | Une essence pousse mieux sur un type de sol ou station | Essence -> Sol / Station | n:m | Oui | douglas -> sol profond |
| `est_substituable_par` | Une essence peut remplacer une autre dans un contexte | Essence -> Essence | n:m | Oui | chêne sessile -> hêtre (mêmes conditions) |

### 3.2 Sémantique détaillée

#### 3.2.1 `est_adapte_a`

Exprime l'adéquation d'une essence à une condition stationnelle,
pédologique ou climatique. La relation porte un `force` (0,0 a 1,0)
indiquant le degré d'adaptation. Cette relation est le pivot du
Reasoning Engine pour les recommandations de plantation.

```
ContenuRelation = {
  sujet       : UUID (Essence)
  predicat    : est_adapte_a
  objet       : UUID (Sol | Climat | Station)
  force       : decimal (0.0 a 1.0)
  description : texte
  source      : SourceReference
  evidence    : EvidenceLevel
  version     : entier
}
```

#### 3.2.2 `influence`

Exprime qu'un facteur écologique en affecte un autre. Cette relation
supporte le raisonnement causal du Correlation Engine et du Reasoning
Engine. La direction est causale : la source influence la cible.

#### 3.2.3 `depend_de`

Exprime une dépendance logique entre deux connaissances. Une règle
dépend d'un seuil ; un modèle dépend de paramètres. Si la connaissance
cible est révisée, la connaissance source doit être réévaluée.

#### 3.2.4 `est_valide_par`

Exprime qu'une connaissance est confirmée par une publication ou un
référentiel. Cardinalité n:1 : une connaissance peut être validée par
plusieurs sources, mais chaque arête pointe vers une seule
publication. Cette relation alimente le calcul d'`evidence_level`.

#### 3.2.5 `contredit`

Exprime un conflit bibliographique (S-3). Cette arête ne supprime
jamais aucune des deux connaissances. Elle déclenche la création d'un
`ConflitBibliographique` (voir section 8). Le Reasoning Engine
propage les deux positions et signale le conflit à l'utilisateur.

#### 3.2.6 `croit_mieux_sur`

Exprime une préférence de croissance. Plus forte que `est_adapte_a` :
l'essence est non seulement adaptée mais présente une productivité
supérieure. Utilisée par le Recommendation Engine pour prioriser les
essences.

#### 3.2.7 `est_substituable_par`

Exprime qu'une essence peut remplacer une autre dans un contexte
donné. Le contexte est porté par `domaines_validite`. Utilisée pour
proposer des alternatives (GSIE-CON-001 — recommandations
contournables).

### 3.3 Relations implicites (dérivées)

Le graphe supporte des relations dérivées calculées par traversal.
Elles ne sont pas stockées mais inférées à la requête :

| Relation dérivée | Calcul | Usage |
|---|---|---|
| `est_compatible_avec` | traversal : Essence -> est_adapte_a -> Station -> est_adapte_a -> Essence | Cohabitation d'essences |
| `est_en_conflit_avec` | traversal : KO -> contredit -> KO | Signalisation conflits |
| `est_dependant_transitif` | traversal : KO -> depend_de -> KO (profondeur limite) | Analyse d'impact de révision |

---

## 4. Propriétés des nœuds et arêtes

### 4.1 Propriétés communes (nœuds et arêtes)

| Propriété | Type | Obligatoire | Description |
|---|---|---|---|
| `id` | UUID v7 | Oui | Identifiant stable et ordonné temporellement |
| `type` | enum | Oui | Type du nœud ou de l'arête |
| `version` | entier | Oui | Numéro de version (commence a 1) |
| `date_integration` | ISO 8601 | Oui | Date d'intégration dans le graphe |
| `historique` | liste de VersionEntry | Oui | Historique des versions (CON-010) |
| `evidence_level` | EvidenceLevel | Oui | Niveau de preuve (S-2) |
| `source` | SourceReference | Oui | Source identifiable (S-1) |
| `domaines_validite` | liste de DomaineValidite | Non | Conditions d'application |
| `confiance` | ConfidenceLevel (0,0-1,0) | Non | Confiance probabiliste (DIR-0006) |
| `statut` | enum | Oui | `actif`, `obsolete`, `quarantine` |

### 4.2 Propriétés spécifiques aux nœuds de connaissance

| Type | Propriétés supplémentaires |
|---|---|
| `concept` | `definition`, `exemples`, `notes` |
| `relation` | `sujet`, `predicat`, `objet`, `force`, `description` |
| `regle` | `conditions`, `conclusion`, `description` |
| `seuil` | `parametre`, `valeur`, `unite`, `contexte`, `direction` |
| `modele` | `nom_modele`, `type`, `variables_entree`, `variables_sortie`, `parametres`, `incertitude` |
| `classification` | `referentiel`, `version_ref`, `categorie`, `valeur`, `parent` |

### 4.3 Propriétés spécifiques aux arêtes

| Propriété | Type | Obligatoire | Description |
|---|---|---|---|
| `sujet` | UUID | Oui | Nœud source |
| `objet` | UUID | Oui | Nœud cible |
| `predicat` | enum | Oui | Type de relation (section 3) |
| `force` | decimal (0,0-1,0) | Non | Intensité de la relation |
| `poids` | decimal (0,0-1,0) | Non | Poids probabiliste (assimilation, section 7.1) |
| `conflit_ref` | UUID | Non | Référence vers ConflitBibliographique si `contredit` |
| `contexte_application` | texte | Non | Contexte d'application de la relation |

### 4.4 Propriétés spécifiques aux entités externes

| Type | Propriétés |
|---|---|
| `Essence` | `nom_scientifique`, `nom_vernaculaire`, `famille`, `synonymes`, `taxon_id`, `taxonomie_version` |
| `Station` | `coordonnees`, `altitude`, `pente`, `exposition`, `type_stationnel`, `region` |
| `Sol` | `type_sol`, `referentiel` (RPF/WRB), `ph`, `texture`, `profondeur`, `rum` |
| `Climat` | `type_climat`, `periode`, `scenario`, `variables` (temp, precip, deficit) |
| `Habitat` | `code_eur28`, `syntaxonomie`, `description`, `essences_typiques` |
| `Publication` | `auteur`, `date_publication`, `reference` (DOI/URL), `type_source`, `version_source` |

---

## 5. Patterns de requête (KnowledgeQuery)

Le Knowledge Engine expose une interface de requête formalisée au
livrable 206 (`KnowledgeQuery`). Les patterns ci-dessous sont les
requêtes canoniques que les moteurs consommateurs adressent au
graphe.

### 5.1 Structure d'une requête

```
KnowledgeQuery = {
  requete_id   : UUID
  type         : enum { par_concept, par_relation, par_domaine,
                        par_essence, par_station, par_seuil,
                        par_modele, par_conflit }
  filtres      : map (clee-valeur selon le type)
  evidence_min : EvidenceLevel (optionnel)
  profondeur   : entier (profondeur de traversal, defaut 1)
}
```

### 5.2 Pattern 1 — « Quelles essences sont adaptées à cette station ? »

**Moteur consommateur** : Reasoning Engine, Recommendation Engine.

```
KnowledgeQuery = {
  type       : par_essence
  filtres    : {
    station_id      : <UUID de la station>
    predicat        : est_adapte_a
    force_min       : 0.5
  }
  evidence_min : C
  profondeur   : 2
}
```

**Traversal du graphe** :

```
Station --> est_adapte_a <-- Essence
                |
          (filtre force >= 0.5,
           evidence >= C)
```

**Résultat attendu** : liste d'essences avec `force`, `evidence_level`,
`source` et `domaines_validite`. Les essences en conflit (S-3) sont
incluses avec leur `ConflitBibliographique` attaché.

### 5.3 Pattern 2 — « Quelles connaissances contredisent ce seuil ? »

**Moteur consommateur** : Reasoning Engine, Validation Engine.

```
KnowledgeQuery = {
  type       : par_conflit
  filtres    : {
    connaissance_id : <UUID du seuil>
    predicat        : contredit
  }
  profondeur : 1
}
```

**Traversal du graphe** :

```
Seuil (KO) --> contredit --> Seuil_alt (KO)
                    |
              ConflitBibliographique
              { source_a, source_b, description }
```

**Résultat attendu** : liste des connaissances contradictoires, chacune
avec sa source, son `evidence_level` et le `ConflitBibliographique`
documentant le conflit. Aucune fusion arbitraire (S-3).

### 5.4 Pattern 3 — « Quels modèles s'appliquent à ce peuplement ? »

**Moteur consommateur** : Forest Dynamics Engine, Simulation Engine.

```
KnowledgeQuery = {
  type       : par_modele
  filtres    : {
    essence_principale : "Quercus petraea"
    type_modele        : croissance
    domaine_validite   : { altitude_max: 600, region: "atlantique" }
  }
  evidence_min : C
  profondeur   : 1
}
```

**Traversal du graphe** :

```
Modele (KO) --> depend_de --> Seuil (KO)
    |
    +-- domaines_validite filtre (altitude, region)
    +-- variables_entree correspond au peuplement
```

**Résultat attendu** : liste de modèles avec `variables_entree`,
`variables_sortie`, `parametres`, `incertitude` (IntervalleConfiance)
et `domaine_validite`. Les modèles hors domaine sont exclus ; les
modèles en extrapolation sont signalés (S-5).

### 5.5 Pattern 4 — « Quelles règles s'appliquent à ce contexte ? »

**Moteur consommateur** : Reasoning Engine.

```
KnowledgeQuery = {
  type       : par_concept
  filtres    : {
    type_ko     : regle
    contexte    : { ph: 5.2, altitude: 400, precipitations: 850 }
  }
  evidence_min : C
  profondeur   : 2
}
```

**Résultat attendu** : règles dont les `conditions` sont satisfaites par
le contexte, avec la chaîne `depend_de` vers les seuils utilisés.

### 5.6 Pattern 5 — « Quelles essences sont substituables ? »

**Moteur consommateur** : Recommendation Engine (alternatives).

```
KnowledgeQuery = {
  type       : par_relation
  filtres    : {
    predicat     : est_substituable_par
    essence_ref  : "Quercus petraea"
    contexte     : { ph: 5.2, altitude: 400 }
  }
  evidence_min : C
  profondeur   : 1
}
```

**Résultat attendu** : essences substituables avec `domaines_validite`
du contexte de substitution et `force` de la relation.

---

## 6. Versioning des relations (CON-010)

### 6.1 Principe

Chaque arête du graphe est un `KnowledgeObject` de type `relation`.
Elle hérite donc du versionnement complet défini par CON-010 et
détaillé au livrable 302, section 5. Une relation n'est jamais
supprimée ni écrasée : elle est archivée et remplacée par une nouvelle
version.

### 6.2 Structure d'une version de relation

```
RelationVersionnee = {
  relation_id      : UUID (stable a travers les versions)
  version          : entier
  sujet            : UUID
  predicat         : enum (section 3)
  objet            : UUID
  force            : decimal (0.0 a 1.0)
  poids            : decimal (0.0 a 1.0)
  source           : SourceReference
  evidence_level   : EvidenceLevel
  date_integration : ISO 8601
  historique       : liste de VersionEntry
  statut           : enum { actif, obsolete, quarantine }
}

VersionEntry = {
  version       : entier
  date          : ISO 8601
  justification : texte
  rfc_reference : texte (optionnel — requis pour revisions majeures)
}
```

### 6.3 Règles de versionnement

| Règle | Description |
|---|---|
| R1 | L'`relation_id` est stable ; il identifie la relation a travers toutes ses versions |
| R2 | Chaque révision incrémente `version` de 1 |
| R3 | L'ancienne version est conservée dans `historique`, jamais supprimée |
| R4 | Une révision majeure (changement de `force`, `source` ou `evidence_level`) requiert une référence RFC |
| R5 | Une révision mineure (clarification de `description`) ne requiert pas de RFC mais doit être justifiée |
| R6 | Une relation `obsolete` reste citable et traversable pour audit |
| R7 | Les recommandations passées peuvent être ré-auditées avec la version de la relation active a l'époque |

### 6.4 Exemple de cycle de versionnement

| Version | Date | Force | Source | Evidence | Justification |
|---|---|---|---|---|---|
| 1 | 2026-07-13 | 0,8 | Rameau et al. (2018) | B | Creation — chene sessile adapte a sol acide |
| 2 | 2028-03-01 | 0,7 | Dupont et al. (2028) | C | Revision — adaptation reduite en contexte mediterraneen |

Les deux versions sont conservées. Une requête datée de 2027 utilise
la version 1 ; une requête de 2028 utilise la version 2. L'audit est
toujours possible.

### 6.5 Impact sur les relations dépendantes

Lorsqu'une relation est révisée, le Knowledge Engine propage un
signal `ReassessmentSignal` (livrable 206) vers les connaissances qui
`depend_de` cette relation. Les relations dépendantes sont marquées
`quarantine` jusqu'à réévaluation par l'Evidence Engine.

```
Relation A (version 2, obsolete) --> depend_de --> Relation B (quarantine)
Relation A (version 3, actif)    --> depend_de --> Relation B (a reevaluer)
```

---

## 7. Support du graphe vivant (DIR-0006)

La directive GSIE-DIR-0006 exige un « graphe vivant » caractérisé par
trois propriétés : assimilation probabiliste, raisonnement
multi-échelle et curiosité artificielle. Cette section spécifie comment
le graphe de connaissances supporte chacune.

### 7.1 Assimilation probabiliste

#### 7.1.1 Principe

Aucune relation n'est binaire. Chaque arête porte un **poids
probabiliste** (`poids`, 0,0 a 1,0) qui représente le consensus
probabiliste construit par fusion des sources. Ce poids est distinct
de la `force` (intensité écologique) et de l'`evidence_level` (niveau
de preuve).

| Propriété | Sémantique | Calcul |
|---|---|---|
| `force` | Intensité écologique de la relation | Issue de la source scientifique |
| `evidence_level` | Niveau de preuve (S-2) | Attribué par l'Evidence Engine |
| `poids` | Consensus probabiliste (DIR-0006) | Fusion des sources par le Knowledge Engine |

#### 7.1.2 Formule de fusion

Lorsque plusieurs sources confirment une même relation, le poids est
calculé par fusion bayésienne simplifiée :

```
poids_fusionne = 1 - produit(1 - poids_i)   pour i = 1..n sources
```

Lorsqu'une source contredit la relation (arête `contredit`), le poids
de la relation contradictoire est réduit proportionnellement à la
confiance de la source contradictoire. Aucune source n'est supprimée
(S-3).

#### 7.1.3 Propriétés d'assimilation

| Propriété | Type | Description |
|---|---|---|
| `poids` | decimal (0,0-1,0) | Consensus probabiliste de la relation |
| `confiance` | decimal (0,0-1,0) | Confiance du nœud (DIR-0006) |
| `sources_multiples` | liste de SourceReference | Sources convergentes |
| `date_derniere_maj_poids` | ISO 8601 | Dernière mise a jour du poids |
| `facteur_decroissance` | decimal | Décroissance temporelle du poids (vieillissement) |

#### 7.1.4 Règles

- Le poids n'est jamais présenté comme une vérité (DIR-0006, cadrage
  constitutionnel CON-004).
- Le poids est affiché avec son intervalle de confiance (S-5).
- Une relation dont le poids tombe sous un seuil (0,3 par défaut) est
  marquée `quarantine` et signalée au Learning Engine pour
  réévaluation.
- Le Learning Engine peut ajuster le poids via `KnowledgeUpdate`
  (livrable 206) sur la base de retours terrain ou de simulations.

### 7.2 Raisonnement multi-échelle

#### 7.2.1 Principe

DIR-0006 exige un raisonnement simultané à plusieurs échelles
spatiales. Le graphe supporte cette exigence par un attribut d' échelle
sur les nœuds et les arêtes.

#### 7.2.2 Échelles définies

| Échelle | Description | Exemple de nœud | Exemple de relation |
|---|---|---|---|
| `arbre` | Individu arbre | Essence (individu) | influence (un arbre ombrage un autre) |
| `peuplement` | Groupe d'arbres homogène | Station (peuplement) | est_adapte_a (essence -> peuplement) |
| `massif` | Ensemble de peuplements | Station (massif) | influence (massif -> climat local) |
| `paysage` | Territoire cohérent | Climat (paysage) | est_substituable_par (a l'echelle paysage) |

#### 7.2.3 Propriété d'échelle

```
EchelleSpatial = enum { arbre, peuplement, massif, paysage }
```

Chaque nœud et chaque arête portent un `echelle` optionnel. Les
requêtes peuvent filtrer par échelle ou demander une propagation
inter-échelles.

#### 7.2.4 Propagation inter-échelles

Le Reasoning Engine peut propager une conclusion d'une échelle à une
autre via le graphe. La propagation respecte les règles suivantes :

| Direction | Règle | Exemple |
|---|---|---|
| arbre -> peuplement | Agrégation (moyenne pondérée par poids) | Santé d'un arbre -> santé du peuplement |
| peuplement -> massif | Agrégation spatiale | Risque sanitaire -> risque massif |
| massif -> paysage | Agrégation + extrapolation signalée | Vulnérabilité massif -> vulnérabilité paysage |
| paysage -> massif | Désagrégation (toujours signalée comme extrapolation, S-5) | Climat paysage -> climat massif |
| massif -> peuplement | Désagrégation (extrapolation signalée) | — |
| peuplement -> arbre | Désagrégation (extrapolation signalée) | — |

Toute propagation descendante (désagrégation) est marquée comme
**extrapolation** et affichée comme telle à l'utilisateur (S-5).

#### 7.2.5 Schéma multi-échelle

```
  Paysage
    |
    | (agregation / desagregation)
    |
  Massif
    |
    | (agregation / desagregation)
    |
  Peuplement
    |
    | (agregation / desagregation)
    |
  Arbre
```

### 7.3 Curiosité artificielle

#### 7.3.1 Principe

DIR-0006 exige que le système identifie spontanément les zones de
faible confiance et propose des actions pour les améliorer. Le graphe
supporte cette exigence par un mécanisme de **zones d'incertitude**.

#### 7.3.2 Structure d'une zone d'incertitude

```
ZoneIncertitude = {
  zone_id          : UUID
  description      : texte (ex. « adaptation du sapin pectine en contexte mediterraneen »)
  nœuds_concernes  : liste de UUID (KnowledgeObject ou entites)
  relations_concernees : liste de UUID (arêtes a faible poids)
  poids_moyen      : decimal (0.0 a 1.0)
  evidence_moyen   : EvidenceLevel
  echelle          : EchelleSpatial
  actions_proposees: liste de ActionCuriosite
  date_detection   : ISO 8601
}

ActionCuriosite = {
  type       : enum { demande_observation, demande_publication,
                      recalcul_simulation, interrogation_source,
                      repositionnement_capteur }
  description: texte
  priorite   : enum { faible, modere, eleve }
  cout_estime: texte (optionnel)
}
```

#### 7.3.3 Règles

- La curiosité artificielle produit des **propositions**, jamais des
  décisions automatiques (DIR-0006, cadrage RFC-0004 §8.3/§8.4).
- Une zone d'incertitude est créée quand :
  - le poids moyen d'un cluster de relations est inferieur a 0,4 ;
  - l'`evidence_level` moyen est D, E ou F ;
  - un `ConflitBibliographique` non résolu est présent ;
  - le Learning Engine détecte un écart entre simulation et réalité.
- Les zones d'incertitude sont priorisées par impact (nombre de
  moteurs consommateurs affectés) et par faisabilité de l'action.
- Les actions proposées sont transmises au Learning Engine puis au
  Validation Engine pour présentation à l'utilisateur.

#### 7.3.4 Exemple

```
ZoneIncertitude = {
  zone_id          : <UUID>
  description      : "Adaptation du sapin pectine en contexte mediterraneen montagnard"
  nœuds_concernes  : [<UUID sapin>, <UUID climat mediterraneen>]
  relations_concernees : [<UUID est_adapte_a v1>, <UUID est_adapte_a v2>]
  poids_moyen      : 0.35
  evidence_moyen   : D
  echelle          : massif
  actions_proposees: [
    { type: demande_publication,
      description: "Recherche de publications sur la tolerance au deficit hydrique du sapin pectine en altitude < 1000 m",
      priorite: eleve },
    { type: demande_observation,
      description: "Observation terrain de peuplements de sapin pectine en Provence calcaire",
      priorite: modere }
  ]
}
```

---

## 8. Gestion des conflits (S-3)

### 8.1 Principe

Lorsque deux sources scientifiques se contredisent, la Constitution
Scientifique (S-3) exige : aucune suppression, documentation du
conflit, signalisation à l'utilisateur, aucune fusion arbitraire. Le
graphe implémente cette exigence par la structure
`ConflitBibliographique` et l'arête `contredit`.

### 8.2 Structure d'un ConflitBibliographique

```
ConflitBibliographique = {
  conflit_id    : UUID
  connaissance_a: UUID (KnowledgeObject — version specifique)
  connaissance_b: UUID (KnowledgeObject — version specifique)
  source_a      : SourceReference
  source_b      : SourceReference
  description   : texte (description neutre du desaccord)
  contexte      : texte (conditions dans lesquelles le conflit se manifeste)
  date_detection: ISO 8601
  statut        : enum { documente, en_rfc, resolu, non_resolvable }
  rfc_reference : texte (optionnel — si une resolution est proposee)
  positions     : liste de PositionConflit
}

PositionConflit = {
  source        : SourceReference
  evidence_level: EvidenceLevel
  argument      : texte
  contexte_validite: texte
}
```

### 8.3 Règles de gestion

| Règle | Description |
|---|---|
| C1 | Un conflit est créé dès qu'une arête `contredit` est ajoutée |
| C2 | Les deux connaissances restent dans le graphe, aucune n'est supprimée |
| C3 | Le conflit est attaché aux deux connaissances via `conflit_ref` |
| C4 | Le Reasoning Engine propage les deux positions, pas une moyenne |
| C5 | Le Validation Engine bloque toute sortie qui masquerait le conflit (`contradiction_non_signalee`) |
| C6 | Une résolution ne peut se faire que par RFC et comité scientifique (S-3) |
| C7 | Un conflit `non_resolvable` reste indéfiniment documenté |
| C8 | Le statut `resolu` déclenche l'archivage de la connaissance invalidée (version obsolète, CON-010) |

### 8.4 Affichage à l'utilisateur

Le Validation Engine présente le conflit comme suit :

```
Conflit bibliographique documente (S-3) :
  Position A : seuil de gel du sapin pectine = -20 degC
    Source : Source 2015, evidence B
    Contexte : provenances du Nord
  Position B : seuil de gel du sapin pectine = -15 degC
    Source : Source 2028, evidence C
    Contexte : provenances du Sud
  GSIE presente les deux positions. Aucune moyenne arbitraire calculee.
```

### 8.5 Schéma de gestion d'un conflit

```
KO_a (seuil -20 degC, v1)          KO_b (seuil -15 degC, v1)
         |                                 |
         +-------- contredit --------------+
                         |
                ConflitBibliographique
                { source_a, source_b,
                  description, statut: documente }
                         |
            +------------+------------+
            |                         |
     Reasoning Engine           Validation Engine
     (propage les deux)         (signale a l'utilisateur,
                                 bloque la fusion arbitraire)
```

---

## 9. Incertitude dans le graphe (S-5)

### 9.1 Principe

La Constitution Scientifique (S-5) exige que toute incertitude soit
identifiée, quantifiée si possible, affichée et jamais masquée. Le
graphe porte l'incertitude à trois niveaux : sur les nœuds, sur les
arêtes et sur les résultats de traversal.

### 9.2 Incertitude sur les nœuds

| Propriété | Type | Description |
|---|---|---|
| `evidence_level` | EvidenceLevel | Niveau de preuve (S-2) — incertitude épistémique |
| `confiance` | decimal (0,0-1,0) | Confiance probabiliste (DIR-0006) |
| `incertitude` | IntervalleConfiance | Intervalle de confiance (pour seuils et modèles) |
| `domaines_validite` | liste de DomaineValidite | Limite de validité — extrapolation signalée |

### 9.3 Incertitude sur les arêtes

| Propriété | Type | Description |
|---|---|---|
| `poids` | decimal (0,0-1,0) | Consensus probabiliste — incertitude de fusion |
| `force` | decimal (0,0-1,0) | Intensité écologique — peut porter un intervalle |
| `conflit_ref` | UUID | Référence vers un conflit non résolu (S-3) |

### 9.4 Propagation de l'incertitude

Lors d'une traversal du graphe (requête multi-sauts), l'incertitude se
propage. Le Knowledge Engine calcule l'incertitude cumulée du
résultat.

#### 9.4.1 Formule de propagation

Pour une chaîne de relations de profondeur n, la confiance cumulée
est :

```
confiance_cumulee = produit(confiance_i)   pour i = 1..n
```

Pour une fusion de m sources convergentes sur un même nœud :

```
confiance_fusionnee = 1 - produit(1 - confiance_j)   pour j = 1..m
```

#### 9.4.2 Exemple

```
Essence (confiance 0.8) --est_adapte_a (poids 0.7)--> Sol (confiance 0.9)

Confiance cumulee = 0.8 * 0.7 * 0.9 = 0.504
```

Le résultat est présenté avec `confiance = 0.50` et l'intervalle de
confiance associé. Aucune présentation sous forme de certitude (S-5).

### 9.5 Affichage de l'incertitude

Le Validation Engine (livrable 206) reçoit l'incertitude calculée par
le Knowledge Engine et l'inclut dans toute sortie validée.

| Niveau de confiance | Affichage | Couleur (UI) |
|---|---|---|
| >= 0,8 | « Confiance élevée » | Vert |
| 0,5 - 0,79 | « Confiance modérée » | Orange |
| 0,3 - 0,49 | « Confiance faible — à interpréter avec prudence » | Jaune |
| < 0,3 | « Incertitude forte — zone d'incertitude signalée » | Rouge |

L'affichage texte est obligatoire ; la couleur est un complément
ergonomique. L'incertitude est **toujours** affichée, jamais masquée
(S-5).

### 9.6 Extrapolation hors domaine

Une connaissance utilisée hors de son `domaines_validite` est
signalée comme **extrapolation**. Le Validation Engine bloque les
sorties hors domaine (`hors_domaine_validite`, livrable 206) sauf si
l'utilisateur a explicitement demandé une extrapolation, auquel cas
elle est affichée comme telle.

```
Connaissance : RUM minimale pour le hetre = 80 mm
Domaine      : altitude < 800 m, France atlantique
Utilisation  : altitude 1200 m, France mediterraneenne
Statut       : EXTRAPOLATION (S-5)
```

---

## 10. Implémentabilité (Phase 4)

Cette section identifie les éléments qui devront être implémentés en
Phase 4 par le Knowledge Engine. Elle ne contient aucun code métier
(interdit en Phase 3) mais définit les contrats d'implémentation.

### 10.1 Stockage du graphe

| Aspect | Choix recommandé | Justification |
|---|---|---|
| Type de stockage | Graphe natif (ex. Neo4j) ou relationnel avec tables de jointure | Traversal multi-sauts, requêtes par predicat |
| Indexation | Index sur `relation_id`, `sujet`, `objet`, `predicat`, `evidence_level` | Performance des KnowledgeQuery |
| Versioning | Table d'historique partitionnée par date | CON-010 — conservation intégrale |
| Persistance offline | SQLite local (cache du graphe) | Offline-first (livrable 206) |

### 10.2 Interface d'implémentation

Le Knowledge Engine doit implémenter les opérations suivantes (à
spécifier en Phase 4) :

| Opération | Entrée | Sortie | Description |
|---|---|---|---|
| `ajouter_connaissance` | QualifiedKnowledge | KnowledgeObject | Ajoute un nœud au graphe |
| `ajouter_relation` | ContenuRelation | RelationVersionnee | Ajoute une arête versionnée |
| `rechercher` | KnowledgeQuery | KnowledgeQueryResult | Exécute une requête traversable |
| `propager_incertitude` | liste de UUID | decimal + IntervalleConfiance | Calcule l'incertitude cumulée |
| `detecter_conflit` | UUID, UUID | ConflitBibliographique | Crée un conflit documenté |
| `detecter_zone_incertitude` | liste de filtres | liste de ZoneIncertitude | Identifie les zones de faible confiance |
| `propager_revision` | UUID (relation révisée) | liste de ReassessmentSignal | Propage l'impact d'une révision |
| `fusionner_sources` | liste de SourceReference + poids | decimal (poids fusionné) | Assimilation probabiliste |

### 10.3 Contrats de cohérence

| Contrat | Garantie |
|---|---|
| Aucune suppression | Toute opération d'archivage conserve l'historique (CON-010) |
| Aucune fusion arbitraire | Toute fusion de sources contradictoires est bloquée (S-3) |
| Incertitude explicite | Toute sortie du graphe porte `confiance` et `incertitude` (S-5) |
| Traçabilité | Toute relation est citable par `relation_id` + `version` (CON-005) |
| Offline-first | Le graphe fonctionne en cache local hors-ligne (livrable 206) |

---

## 11. Références

- `00_CONSTITUTION/GSIE-CON-002.md` — La science avant tout
- `00_CONSTITUTION/GSIE-CON-003.md` — La connaissance avant le code
- `00_CONSTITUTION/GSIE-CON-010.md` — Évolution sans perte d'historique
- `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md` — Articles S-3, S-5, S-7
- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0006.md` — Vision du moteur cognitif (graphe vivant)
- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0007.md` — Lancement Phase 3 Connaissance
- `GSIE/ARCHITECTURE/ENGINE_INTERFACE_CONTRACTS.md` — Livrable 206 (contrats d'interface)
- `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` — Livrable 302 (méthode de gestion des connaissances)
- `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` — Livrable 303 (ontologie forestière)
- `GSIE/ENGINES/KNOWLEDGE_ENGINE/` — Documentation du Knowledge Engine

---

## 12. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — stub Phase 1 (nœuds et relations de base) |
| 2026-07-13 | Détaillage Phase 3 — types de nœuds et d'arêtes, propriétés, patterns de requête, versionnement des relations, support du graphe vivant (DIR-0006), gestion des conflits (S-3), incertitude (S-5), implémentabilité Phase 4 |

---

> Statut : *Validated — Phase 3 (Connaissance). Documentation uniquement,
> aucune implémentation (Phase 4).*
