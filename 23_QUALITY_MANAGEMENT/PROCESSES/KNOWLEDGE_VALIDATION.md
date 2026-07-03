# Processus de Validation des Connaissances

| Champ        | Valeur                          |
|--------------|---------------------------------|
| Document     | KNOWLEDGE_VALIDATION.md         |
| Dossier      | 23_QUALITY_MANAGEMENT/PROCESSES |
| Version      | 1.0.0                           |
| Date         | 2 juillet 2026                  |
| Statut       | Adopté                          |
| Référence    | QUALITY_MANUAL.md               |

---

## 1. Objet

Le présent processus définit les règles et étapes de validation de toute
connaissance avant son intégration au Knowledge Graph du projet GSIE. Il
garantit que chaque triplet, chaque entité et chaque relation introduit dans
le graphe est tracé, sourcé, évalué par l'Evidence Engine et validé par un
expert humain.

---

## 2. Périmètre

Le processus s'applique à toute source documentaire ingérée par la
plateforme GSIE, qu'il s'agisse de documents forestiers, de bases
taxonomiques, de rapports d'inventaire ou de publications scientifiques. Il
couvre l'ensemble du cycle : ingestion, extraction, évaluation, validation et
intégration.

---

## 3. Processus en 8 étapes

```
1. Source identifiée
       |
2. Licence vérifiée
       |
3. Ingestion (OCR / parsing)
       |
4. Extraction entités / relations
       |
5. Evidence Engine évalue
       |
6. Validation expert humain
       |
7. Intégration graphe + Version_KB
       |
8. Snapshot signé
```

### 3.1 Source identifiée

Le data steward identifie la source documentaire, enregistre ses métadonnées
(auteur, date, éditeur, type de document) et crée un ticket d'ingestion dans
le système de suivi.

### 3.2 Licence vérifiée

La licence de la source est contrôlée. Toute source dont la licence est
incompatible avec les termes d'utilisation de GSIE est rejetée. La décision
est tracée dans le journal d'ingestion.

### 3.3 Ingestion (OCR / parsing)

Le document est ingéré par le pipeline d'OCR ou de parsing. Le texte brut
est extrait et stocké. Les erreurs d'OCR sont signalées pour correction
manuelle si le taux de confiance est inférieur à 90 %.

### 3.4 Extraction entités / relations

Le Knowledge Engine extrait les entités (espèces, genres, familles,
localisations) et les relations taxonomiques, écologiques ou géographiques.
Chaque extraction est associée à un extrait textuel (span) justifiant la
proposition.

### 3.5 Evidence Engine évalue

L'Evidence Engine évalue chaque proposition en attribuant un niveau de
preuve, un score de confiance et un statut parmi : `CONFIRMED`,
`PROBABLE`, `CONJECTURAL`, `CONTRADICTED`. Les contradictions avec les
connaissances existantes sont détectées et tracées.

### 3.6 Validation expert humain

Un expert validateur examine les propositions évaluées par l'Evidence Engine.
Il confirme, corrige ou rejette chaque proposition. Son avis est enregistré
avec identifiant, date et justification.

### 3.7 Intégration graphe + Version_KB

Les propositions validées sont intégrées au Knowledge Graph. Une nouvelle
version de la base de connaissances (`Version_KB`) est créée avec un
identifiant incrémental et un journal des modifications.

### 3.8 Snapshot signé

Un snapshot de la `Version_KB` est généré, haché et signé cryptographiquement.
Le hash et la signature sont archivés pour garantir l'intégrité et la
non-répudiation de la base de connaissances.

---

## 4. Règles

| Règle | Description |
|-------|-------------|
| R1 | Aucune connaissance ne peut être intégrée sans source identifiée et tracée. |
| R2 | Aucune connaissance ne peut être intégrée sans passage par l'Evidence Engine. |
| R3 | Une connaissance de statut `CONJECTURAL` ne peut être utilisée sans marquage explicite dans le graphe. |
| R4 | Toute contradiction entre sources doit être tracée et résolue ou signalée. |
| R5 | Chaque intégration produit une nouvelle `Version_KB` avec snapshot signé. |
| R6 | Aucune modification directe du graphe en production n'est autorisée hors de ce processus. |

---

## 5. Rôles et responsabilités

| Rôle               | Responsabilités |
|--------------------|-----------------|
| Data steward       | Identifie les sources, vérifie les licences, initie l'ingestion, supervise le suivi. |
| Evidence Engine    | Évalue automatiquement les propositions, attribue niveaux de preuve et scores de confiance, détecte les contradictions. |
| Expert validateur  | Valide, corrige ou rejette les propositions issues de l'Evidence Engine. Apporte l'expertise métier forestière. |
| Knowledge Engine   | Extrait les entités et relations, intègre les propositions validées, gère les versions de la base de connaissances. |

---

## 6. Critères de validation

L'expert validateur évalue chaque proposition selon les critères suivants :

| Critère                | Description | Seuil d'acceptation |
|------------------------|-------------|---------------------|
| Niveau de preuve       | Évaluation de l'Evidence Engine. | >= `PROBABLE` |
| Cohérence              | Absence de contradiction avec le graphe existant. | Aucune contradiction non résolue |
| Complétude provenance  | Source, auteur, date et extrait textuel présents. | 100 % des champs renseignés |
| Score de confiance     | Score attribué par l'Evidence Engine. | >= 0,70 sur 1,00 |

Une proposition ne respectant pas l'un de ces critères est rejetée ou
renvoyée en correction.

---

## 7. Rejet et correction

### 7.1 Cause de rejet

Lorsqu'une proposition est rejetée, l'expert validateur ou l'Evidence Engine
doit enregistrer une cause parmi les suivantes :

| Code | Cause |
|------|-------|
| REJ-01 | Source insuffisante ou non fiable. |
| REJ-02 | Contradiction non résolue avec connaissance existante. |
| REJ-03 | Niveau de preuve insuffisant (inférieur à `PROBABLE`). |
| REJ-04 | Extraction erronée (OCR, parsing, entité mal identifiée). |
| REJ-05 | Licence incompatible. |

### 7.2 Action corrective

Une action corrective est définie et assignée. Elle peut consister en :

- la recherche d'une source complémentaire ;
- la correction manuelle de l'extraction ;
- la soumission à un second expert validateur en cas de désaccord ;
- la révision des paramètres de l'Evidence Engine.

### 7.3 Re-soumission

Après correction, la proposition est re-soumise au processus à l'étape
appropriée (3.3 ingestion, 3.4 extraction ou 3.5 évaluation). Le nombre de
cycles de re-soumission est limité à 3. Au-delà, la source est archivée et
clôturée comme non exploitable.

---

## 8. Traçabilité

Chaque étape du processus est journalisée dans le système de suivi. Le
journal contient au minimum :

- l'identifiant de la source ;
- l'identifiant de la proposition ;
- l'horodatage de chaque étape ;
- l'identifiant de l'acteur (humain ou système) ;
- la décision et sa justification.

Les journaux sont conservés pour la durée de vie de la base de connaissances
et sont auditables à tout moment.

---

## 9. Références

- `QUALITY_MANUAL.md` -- Manuel qualité du projet GSIE.
- `INCIDENT_MANAGEMENT.md` -- Processus de traitement des non-conformités.
- `DOCUMENT_REVIEW.md` -- Processus de revue documentaire.

---

*Fin du document.*
