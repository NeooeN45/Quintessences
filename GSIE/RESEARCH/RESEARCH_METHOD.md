# GSIE Research Method — Méthode de recherche scientifique

| Champ | Valeur |
|---|---|
| **Livrable** | 301 — Research Method (détaillée) |
| **Phase** | 3 — Connaissance |
| **Statut** | Validated |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-005, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1 à S-7) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |

---

## 1. Objet

Définir le pipeline officiel de recherche scientifique de GSIE : comment
une connaissance est identifiée, collectée, évaluée, qualifiée et
intégrée dans la base. Cette méthode opérationnalise la Constitution
Scientifique (S-1 à S-7) et alimente l'Evidence Engine (livrable 206).

---

## 2. Pipeline en 10 étapes

### Étape 1 — Recherche documentaire

**Objectif** : identifier les sources pertinentes pour un domaine ou
une question scientifique.

**Critères** :
- Mots-clés définis selon le domaine (S-6).
- Sources consultées : bases bibliographiques (Web of Science, Scopus,
  Google Scholar, HAL), référentiels institutionnels (IGN, INRAE, ONF,
  Météo-France), bases taxonomiques (GBIF, Tela Botanica, BDNFF).
- Périmètre temporel : priorité aux publications < 10 ans, sauf
  références fondatrices.
- Langue : français et anglais principalement.

**Livrable** : liste de sources candidates avec métadonnées
bibliographiques (auteur, titre, date, éditeur, DOI/URL).

### Étape 2 — Collecte des sources

**Objectif** : acquérir le contenu des sources identifiées.

**Critères** :
- Texte intégral récupéré (pas seulement le résumé).
- Données associées récupérées si disponibles (tableaux, annexes,
  données supplémentaires).
- Version exacte identifiée (DOI, ISBN, version de référentiel).
- Licence d'utilisation vérifiée (voir `19_LEGAL/`).

**Livrable** : dossier de source avec contenu intégral + métadonnées.

### Étape 3 — Évaluation scientifique

**Objectif** : qualifier la source selon les critères S-1.

**Critères de catégorisation** (S-1, par ordre de priorité décroissante) :

| Catégorie | Critères | Exemples |
|---|---|---|
| 1. Peer-reviewed | Revue indexée, comité de lecture, facteur d'impact | *Annals of Forest Science*, *Forest Ecology and Management* |
| 2. Référentiel officiel | Institution reconnue, procédure de validation | IGN BD Forêt, INRAE RPF, ONF guides sylvicoles |
| 3. Document technique | Comité de validation, organisme professionnel | Guide ONF, document CRPF |
| 4. Connaissance experte | Expert identifié, daté, signé | Témoignage forestier expérimenté |
| 5. Observation terrain | Protocole décrit, date, localisation | Inventaire terrain, placette permanente |

**Livrable** : `SourceReference` (voir livrable 206, types communs).

### Étape 4 — Attribution d'un niveau de preuve

**Objectif** : assigner un `EvidenceLevel` (A-F) à chaque connaissance
extraite de la source.

Voir livrable 306 (Evidence Framework) pour les critères détaillés et
exemples par domaine.

**Règles** :
- Le niveau est attribué par l'Evidence Engine, pas par le chercheur
  humain directement.
- Le niveau dépend de la catégorie de source (S-1) ET de la convergence
  avec d'autres sources.
- Une source unique peer-reviewed = niveau B maximum.
- Une source unique non peer-reviewed = niveau D maximum.
- Le niveau A exige un consensus multi-sources.

**Livrable** : `QualifiedKnowledge` avec `evidence_level` (livrable 206).

### Étape 5 — Modélisation conceptuelle

**Objectif** : structurer la connaissance en `KnowledgeObject` (livrable
206) selon l'ontologie (livrable 303) et le graphe (livrable 304).

**Critères** :
- Type identifié : `concept`, `relation`, `regle`, `seuil`, `modele`,
  `classification`.
- Domaine de validité défini (ex. « pH 4,5–6,0 », « altitude < 1400 m »,
  « France métropolitaine »).
- Relations avec les connaissances existantes identifiées.
- Moteurs consommateurs identifiés (ex. Diagnostic, Recommendation).

**Livrable** : `KnowledgeObject` prêt pour intégration.

### Étape 6 — Validation

**Objectif** : vérifier que la connaissance respecte toutes les règles
constitutionnelles avant intégration.

**Contrôles** (alignés sur le Validation Engine, livrable 206) :

| Contrôle | Règle | Échec si |
|---|---|---|
| Source présente | S-1 | Pas de `SourceReference` |
| Niveau de preuve présent | S-2 | Pas d'`EvidenceLevel` |
| Domaine de validité défini | S-5 | Domaine absent ou trop large |
| Conflits détectés | S-3 | Conflit non documenté |
| Version initiale | CON-010 | Pas de version 1 |
| Pas de duplication | DRY | Connaissance déjà présente |

**Livrable** : statut `accepte`, `quarantine` ou `refuse`.

### Étape 7 — Intégration

**Objectif** : insérer la connaissance dans le graphe de connaissances
(géré par le Knowledge Engine, livrable 206).

**Critères** :
- Seules les connaissances au statut `accepte` sont intégrées.
- Les connaissances en `quarantine` sont conservées pour réévaluation.
- Les connaissances `refuse` sont archivées pour audit.
- L'intégration crée les relations avec les connaissances existantes.

**Livrable** : `KnowledgeObject` versionné dans le graphe.

### Étape 8 — Documentation

**Objectif** : documenter la connaissance pour traçabilité (CON-005) et
explicabilité (CON-004).

**Critères** :
- Fiche de connaissance complète (voir livrable 302, Knowledge Method).
- Source citée avec référence complète.
- Niveau de preuve affiché.
- Domaine de validité explicite.
- Relations documentées.
- Moteurs consommateurs listés.

**Livrable** : fiche de connaissance dans `GSIE/KNOWLEDGE/`.

### Étape 9 — Versionnement

**Objectif** : tracer l'historique de la connaissance (CON-010, S-7).

**Critères** :
- Chaque modification crée une nouvelle version (numéro incrémenté).
- L'ancienne version est conservée dans l'historique, jamais supprimée.
- Chaque version porte une justification et une date.
- Une référence RFC est requise pour les révisions majeures (S-4).

**Livrable** : `VersionEntry` dans l'historique du `KnowledgeObject`.

### Étape 10 — Surveillance scientifique continue

**Objectif** : détecter les évolutions scientifiques qui pourraient
affecter les connaissances intégrées.

**Mécanismes** :
- **Veille bibliographique** : nouvelles publications dans les domaines
  couverts (S-6).
- **Signaux de réévaluation** : le Learning Engine (livrable 206) peut
  émettre des `ReassessmentSignal` quand des patterns émergents
  contredisent une connaissance.
- **Alertes de conflit** : une nouvelle source contredisant une
  connaissance existante déclenche un `ConflitBibliographique` (S-3).
- **Révision programmée** : les connaissances de niveau D-F sont
  réévaluées périodiquement (annuel par défaut).

**Livrable** : signaux de réévaluation traités par l'Evidence Engine.

---

## 3. Règles transverses

### 3.1 Aucune connaissance n'existe uniquement dans le code

Toute connaissance doit être documentée dans `GSIE/KNOWLEDGE/` avant
d'être référencée dans un moteur (CON-003).

### 3.2 Aucune moyenne arbitraire

Lorsque deux sources donnent des valeurs différentes pour un même
paramètre, les deux sont conservées avec leur niveau de preuve
respective. Aucune moyenne n'est calculée sans justification
scientifique (S-3).

### 3.3 Incertitude explicite

Toute incertitude doit être identifiée, quantifiée si possible, et
affichée à l'utilisateur (S-5). Voir livrable 306 pour le framework
détaillé.

### 3.4 Patrimoine scientifique

Les connaissances constituent un patrimoine versionné, réversible,
citable et ouvert (S-7). Aucune connaissance n'est supprimée — elle est
archivée ou révisée.

---

## 4. Articulation avec les moteurs

| Moteur | Rôle dans le pipeline | Étape |
|---|---|---|
| Evidence Engine | Évaluation source + niveau de preuve | 3, 4 |
| Knowledge Engine | Stockage + versionnement + requêtes | 7, 9 |
| Correlation Engine | Détection de corrélations entre connaissances | (post-7) |
| Reasoning Engine | Application des règles et inférences | (post-7) |
| Learning Engine | Signaux de réévaluation + patterns émergents | 10 |
| Validation Engine | Contrôle de conformité | 6 |

---

## 5. Cas particulier : connaissance experte non publiée

La catégorie 4 (connaissance experte) est acceptée mais encadrée :

- Niveau de preuve maximum : D.
- L'expert doit être identifié (nom, fonction, expérience).
- La connaissance doit être datée et signée.
- Elle est réévaluée si une source publiée la confirme ou l'infirme.
- Elle est signalée à l'utilisateur comme « connaissance experte non
  publiée ».

---

## 6. Cas particulier : observation terrain isolée

La catégorie 5 (observation terrain) est acceptée mais encadrée :

- Niveau de preuve maximum : F.
- Le protocole d'observation doit être décrit.
- La localisation et la date sont obligatoires.
- Elle est réévaluée si d'autres observations convergent.
- Elle est signalée à l'utilisateur comme « observation non
  recoupée ».

---

## 7. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — pipeline en 10 étapes (stub Phase 1) |
| 2026-07-13 | Détaillage Phase 3 — critères par étape, articulation moteurs, cas particuliers |

---

> Statut : *Validated — Phase 3 (Connaissance). Documentation uniquement,
> aucune implémentation (Phase 4).*
