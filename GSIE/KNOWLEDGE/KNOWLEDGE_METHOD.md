# GSIE Knowledge Method — Méthode de gestion des connaissances

| Champ | Valeur |
|---|---|
| **Livrable** | 302 — Knowledge Method (détaillée) |
| **Phase** | 3 — Connaissance |
| **Statut** | Validated |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-005, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1 à S-7) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |
| **Documents connexes** | `GSIE/RESEARCH/RESEARCH_METHOD.md` (301), `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` (306), `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` (303), `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` (304) |

---

## 1. Objet

Définir le cycle de vie complet d'une connaissance dans GSIE : comment
elle est créée, structurée, versionnée, révisée et archivée. Cette
méthode opérationnalise CON-010 (historique), S-4 (révision) et S-7
(patrimoine) et définit la structure exacte des `KnowledgeObject` du
livrable 206.

---

## 2. Structure d'une connaissance (KnowledgeObject)

Tout `KnowledgeObject` (voir livrable 206, schéma formel) doit comporter :

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `connaissance_id` | UUID | Oui | Identifiant stable et unique |
| `type` | enum | Oui | `concept`, `relation`, `regle`, `seuil`, `modele`, `classification` |
| `contenu` | structure typée | Oui | Dépend du type (voir §3) |
| `evidence_level` | EvidenceLevel | Oui | A à F (S-2, voir livrable 306) |
| `source` | SourceReference | Oui | Source identifiable et vérifiable (S-1) |
| `version` | entier | Oui | Commence à 1, incrémenté à chaque révision |
| `date_integration` | ISO 8601 | Oui | Date d'intégration dans le graphe |
| `historique` | liste de VersionEntry | Oui | Historique des versions (CON-010) |
| `domaines_validite` | liste de DomaineValidite | Non | Conditions d'application |
| `moteurs_consommateurs` | liste de texte | Non | Moteurs qui utilisent cette connaissance |
| `relations` | liste de RelationRef | Non | Liens avec d'autres connaissances (voir livrable 304) |

### Champs additionnels (fiche de documentation)

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `titre` | texte | Oui | Titre court descriptif |
| `description` | texte | Oui | Description en français |
| `domaine_scientifique` | enum (S-6) | Oui | Domaine de la Constitution Scientifique |
| `mots_cles` | liste de texte | Non | Mots-clés pour la recherche |
| `conflits` | liste de ConflitBibliographique | Non | Conflits avec d'autres sources (S-3) |

---

## 3. Types de connaissance et structure du contenu

### 3.1 Type `concept`

Une notion scientifique définie.

```
ContenuConcept = {
  definition     : texte
  exemples       : liste de texte (optionnel)
  notes          : texte (optionnel)
}
```

Exemple : « Réserve utile en eau (RUM) » — quantité d'eau maximale que
le sol peut retenir et mettre à disposition des plantes.

### 3.2 Type `relation`

Une relation entre deux concepts ou entités.

```
ContenuRelation = {
  sujet          : UUID (KnowledgeObject ou entité)
  predicat       : enum { est_adapte_a, influence, depend_de, est_valide_par, contredit, croit_mieux_sur, ... }
  objet          : UUID (KnowledgeObject ou entité)
  description    : texte
  force          : decimal (0.0 à 1.0, optionnel)
}
```

Exemple : « chêne sessile » `est_adapte_a` « sol acide pH 4,5–6,0 ».

### 3.3 Type `regle`

Une règle d'inférence applicable par le Reasoning Engine.

```
ContenuRegle = {
  conditions     : liste de Condition
  conclusion     : texte
  description    : texte
}
Condition = {
  variable       : texte (ex. « pH », « altitude », « precipitations »)
  operateur      : enum { egal, superieur, inferieur, compris_dans, est_un }
  valeur         : texte ou IntervalleValeur
}
```

Exemple : SI pH compris dans [4,5 ; 6,0] ET altitude < 1400 m ET
précipitations > 700 mm/alors chêne sessile adapté.

### 3.4 Type `seuil`

Une valeur seuil scientifiquement établie.

```
ContenuSeuil = {
  parametre      : texte (ex. « pH », « RUM », « gel »)
  valeur         : decimal ou IntervalleValeur
  unite          : texte (ex. « pH », « mm », « °C »)
  contexte       : texte (ex. « hêtre, plaine, déficit hydrique »)
  direction      : enum { minimum, maximum, optimal, critique }
}
```

Exemple : RUM minimale pour le hêtre = 80 mm (Rameau et al., 2018).

### 3.5 Type `modele`

Un modèle scientifique (croissance, dynamique, propagation).

```
ContenuModele = {
  nom_modele     : texte (ex. « ONF-FFN », « INRAE-MARGINAL »)
  type           : enum { croissance, dynamique, propagation, climatique }
  variables_entree : liste de texte
  variables_sortie : liste de texte
  parametres     : map (clé-valeur)
  domaine_validite : texte
  incertitude    : IntervalleConfiance (optionnel)
}
```

Exemple : modèle de croissance ONF-FFN pour le douglas (source : ONF
2019, evidence B).

### 3.6 Type `classification`

Une classification ou taxonomie référentielle.

```
ContenuClassification = {
  referentiel    : texte (ex. « RPF », « WRB », « GBIF », « BD Forêt »)
  version_ref    : texte
  categorie      : texte (ex. « type de sol », « essence », « habitat »)
  valeur         : texte (ex. « Alocrisol », « Quercus petraea »)
  parent         : texte (optionnel — classification hiérarchique)
}
```

Exemple : Alocrisol (RPF, INRAE 2008).

---

## 4. Cycle de vie d'une connaissance

```
Création → Validation → Intégration → Utilisation → Révision → Archivage
   │           │            │             │             │           │
   │           │            │             │             │           └─ conservée, jamais supprimée
   │           │            │             │             └─ nouvelle version, ancienne archivée
   │           │            │             └─ moteurs consomment
   │           │            └─ ajout au graphe (Knowledge Engine)
   │           └─ Evidence Engine qualifie (accepte/quarantine/refuse)
   └─ Research Method (étapes 1-5, livrable 301)
```

### 4.1 Création

Une connaissance est créée par le pipeline de recherche (livrable 301,
étapes 1-5). Elle reçoit :
- un `connaissance_id` stable (UUID v7)
- une version initiale (1)
- un `evidence_level` (par l'Evidence Engine)
- un statut `accepte`, `quarantine` ou `refuse`

### 4.2 Validation

Le Validation Engine (livrable 206) vérifie la conformité
constitutionnelle. Voir livrable 301, étape 6.

### 4.3 Intégration

La connaissance est ajoutée au graphe par le Knowledge Engine. Les
relations avec les connaissances existantes sont créées.

### 4.4 Utilisation

Les moteurs consommateurs interrogent la connaissance via
`KnowledgeQuery` (livrable 206). Chaque utilisation est tracée
(CON-005).

### 4.5 Révision

Une connaissance peut être révisée quand (S-4) :
- sa source est invalidée
- une nouvelle publication la contredit
- le consensus évolue

Procédure :
1. Identification du besoin (signal du Learning Engine ou veille).
2. Évaluation de la nouvelle source par l'Evidence Engine.
3. Création d'une nouvelle version (numéro incrémenté).
4. L'ancienne version est archivée dans `historique` (jamais
   supprimée, CON-010).
5. Mise à jour des relations.
6. Documentation de la justification (`VersionEntry`).

### 4.6 Archivage

Une connaissance obsolète n'est **jamais supprimée**. Elle est :
- marquée comme `obsolete` dans son statut
- conservée dans le graphe avec son historique
- toujours citable par son `connaissance_id` stable
- potentiellement réactivée si le consensus évolue à nouveau

---

## 5. Versionnement (CON-010, S-7)

### 5.1 Structure d'une VersionEntry

```
VersionEntry = {
  version       : entier
  date          : ISO 8601
  justification : texte
  rfc_reference : texte (optionnel — requis pour révisions majeures)
}
```

### 5.2 Règles

- La version 1 est la création initiale.
- Chaque révision incrémente la version de 1.
- L'ancienne version est conservée intégralement dans `historique`.
- Une révision majeure (changement de valeur, de source ou de niveau de
  preuve) requiert une référence RFC.
- Une révision mineure (clarification, ajout d'exemple) ne requiert pas
  de RFC mais doit être justifiée.

### 5.3 Exemple de cycle de versionnement

| Version | Date | Justification | Source | Evidence |
|---|---|---|---|---|
| 1 | 2026-07-13 | Création — seuil de gel du sapin pectiné | Source 2015 | B |
| 2 | 2028-03-01 | Révision — provenances du Sud plus vulnérables | Source 2028 | C |

Les deux versions sont conservées. Les recommandations émises entre 2015
et 2028 restent explicables : on sait quel seuil était utilisé.

---

## 6. Domaines de validité

### 6.1 Structure

```
DomaineValidite = {
  parametre : texte (ex. « pH », « altitude », « climat », « région »)
  minimum   : decimal (optionnel)
  maximum   : decimal (optionnel)
  unite     : texte (optionnel)
}
```

### 6.2 Règles

- Toute connaissance scientifique a un **domaine de validité** — une
  règle vraie en plaine peut être fausse en montagne.
- Le domaine est explicite et affiché à l'utilisateur.
- Une connaissance utilisée hors de son domaine de validité est
  signalée comme **extrapolation** (S-5).
- Le Validation Engine (livrable 206) bloque les sorties hors domaine
  (`hors_domaine_validite`).

### 6.3 Exemples

| Connaissance | Domaine de validité |
|---|---|
| Chêne sessile adapté pH 4,5–6,0 | pH ∈ [4,5 ; 6,0], France métropolitaine |
| Hêtre vulnérable au déficit hydrique | Altitude < 800 m, France atlantique |
| Douglas croissance 12 m³/ha/an | Sols profonds, pH 4,5–6,5, précipitations > 800 mm |

---

## 7. Relations entre connaissances

Voir livrable 304 (Knowledge Graph Specification) pour le détail formel.

### 7.1 Types de relations

| Relation | Description | Exemple |
|---|---|---|
| `est_adapte_a` | Une essence est adaptée à une condition | Chêne sessile → sol acide |
| `influence` | Un facteur affecte un autre | pH → disponibilité nutriments |
| `depend_de` | Une connaissance nécessite une autre | Règle d'adaptation → seuil de pH |
| `est_valide_par` | Une connaissance est confirmée par une source | Seuil de gel → publication 2015 |
| `contredit` | Deux connaissances sont en conflit (S-3) | Seuil -20 °C → contredit → seuil -15 °C |
| `croit_mieux_sur` | Une essence pousse mieux sur un type de sol | Douglas → sol profond |
| `est_substituable_par` | Une essence peut remplacer une autre | Chêne sessile → hêtre (mêmes conditions) |

### 7.2 Versionnement des relations

Chaque relation est versionnée. Si une relation est invalidée par une
nouvelle source, elle est archivée (jamais supprimée) et la nouvelle
relation est créée avec sa source et son niveau de preuve.

---

## 8. Mapping moteurs consommateurs

| Moteur | Types consommés | Exemple |
|---|---|---|
| Knowledge Engine | Tous | Stockage et requêtes |
| Correlation Engine | `seuil`, `modele` | Croisement de paramètres |
| Reasoning Engine | `regle`, `seuil` | Inférences |
| Diagnostic Engine | `concept`, `seuil`, `relation` | État et risques |
| Recommendation Engine | `regle`, `relation`, `modele` | Recommandations |
| Simulation Engine | `modele`, `seuil` | Projections |
| Forest Dynamics Engine | `modele`, `classification` | Croissance |
| Botanical Engine | `classification`, `concept` | Taxonomie |
| Pedology Engine | `classification`, `seuil` | Types de sol |
| Climate Engine | `modele`, `seuil` | Données climatiques |
| GIS Engine | `classification` | Données spatiales |

---

## 9. Règles transverses

1. **Aucune connaissance n'existe uniquement dans le code** (CON-003).
2. **Aucune connaissance sans source** (S-1, CON-002).
3. **Aucune connaissance sans niveau de preuve** (S-2).
4. **Aucune suppression** — archivage uniquement (CON-010, S-7).
5. **Conflits documentés** — jamais résolus arbitrairement (S-3).
6. **Incertitude affichée** — jamais masquée (S-5).
7. **Domaine de validité explicite** — extrapolation signalée (S-5).

---

## 10. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — liste de champs requis (stub Phase 1) |
| 2026-07-13 | Détaillage Phase 3 — cycle de vie, 6 types, versionnement, domaines de validité, relations, mapping moteurs |

---

> Statut : *Validated — Phase 3 (Connaissance). Documentation uniquement,
> aucune implémentation (Phase 4).*
