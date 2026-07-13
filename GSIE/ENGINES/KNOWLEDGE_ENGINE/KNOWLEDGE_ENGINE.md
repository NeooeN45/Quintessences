# Knowledge Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Knowledge Engine |
| **Catégorie** | Chaîne d'intelligence (base de connaissances) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-003, GSIE-CON-005, GSIE-CON-010 |
| **Ordre de développement** | 1 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Centraliser, structurer et versionner toutes les connaissances
scientifiques qualifiées de GSIE dans un graphe de connaissances
interrogeable, constituant la source unique de vérité pour tous les
moteurs de raisonnement.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `EVIDENCE_ENGINE` | Connaissance qualifiée | Connaissances dotées d'un niveau de preuve et d'une source (`QualifiedKnowledge`) |
| `LEARNING_ENGINE` | Proposition de révision | Connaissances dont le niveau de preuve ou le contenu est susceptible d'évolution |
| `GSIE/KNOWLEDGE/` | Ontologies et règles | Ontologies, taxonomies et règles scientifiques structurées |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `CORRELATION_ENGINE` | Connaissances normalisées | Règles, seuils et relations pour le croisement de données |
| `REASONING_ENGINE` | Connaissances normalisées | Concepts, relations et règles d'inférence pour le raisonnement |
| `DIAGNOSTIC_ENGINE` | Connaissances normalisées | Référentiels stationnels et sylvicoles |
| `RECOMMENDATION_ENGINE` | Connaissances normalisées | Règles sylvicoles, gammes d'optimum, exigences d'essences |
| `FOREST_DYNAMICS_ENGINE` | Connaissances normalisées | Modèles de croissance, paramètres de production |
| `BOTANICAL_ENGINE` | Ontologie | Structure taxonomique et relations nomenclaturales |
| `VALIDATION_ENGINE` | Vérification de validité | Contrôle que les connaissances utilisées dans une sortie sont à jour et valides |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `EVIDENCE_ENGINE` | Filtre amont obligatoire — aucune connaissance n'entre sans qualification |
| Moteur | `LEARNING_ENGINE` | Révisions proposées par apprentissage (sous réserve de validation) |
| Base | `GSIE/KNOWLEDGE/` | Ontologies et règles scientifiques sourcées |

## 5. Contrat d'interface

### Entrée — `QualifiedKnowledge` (depuis Evidence Engine)

Voir `EVIDENCE_ENGINE.md` §5. Le Knowledge Engine reçoit les
connaissances au statut `accepte`.

### Sortie — `KnowledgeQueryResult`

```
KnowledgeQueryResult = {
  requete_id      : UUID
  connaissances   : liste de KnowledgeObject
  total           : entier
  version_graph   : texte (version du graphe au moment de la requête)
}

KnowledgeObject = {
  connaissance_id   : UUID
  type              : enum { concept, relation, regle, seuil, modele, classification }
  contenu           : structure typée selon `type`
  evidence_level    : enum { A, B, C, D, E, F }
  source            : SourceReference
  version           : entier
  date_integration  : ISO 8601
  historique        : liste de VersionEntry
  domaines_validite : liste de DomaineValidite (optionnel)
}

VersionEntry = {
  version     : entier
  date        : ISO 8601
  justification : texte
  rfc_reference : texte (optionnel)
}

DomaineValidite = {
  parametre  : texte (ex. « pH », « altitude », « climat »)
  minimum    : valeur (optionnel)
  maximum    : valeur (optionnel)
  unite      : texte (optionnel)
}
```

### Requête — `KnowledgeQuery`

```
KnowledgeQuery = {
  requete_id : UUID
  type       : enum { par_concept, par_relation, par_domaine, par_essence, par_station }
  filtres    : map (clé-valeur selon le type)
  evidence_min : enum { A, B, C, D, E, F } (optionnel — filtre par niveau de preuve minimum)
}
```

## 6. Garanties

- **Source unique de vérité** — aucun autre moteur ne stocke de
  connaissance scientifique ; tous interrogent le Knowledge Engine.
- Toute connaissance est versionnée et son historique est conservé
  (`GSIE-CON-010`).
- Aucune logique d'inférence — le Knowledge Engine stocke et fournit,
  il ne raisonne pas (séparation des responsabilités, `GSIE-CON-007`).
- Toute connaissance est traçable jusqu'à sa source et son niveau de
  preuve (`GSIE-CON-005`).
- Le graphe de connaissances est interrogeable hors-ligne (article T-8).
- Une connaissance dont la source est invalidée est révisée via
  procédure documentée, jamais supprimée silencieusement.

## 7. Cas d'usage

### Cas 1 — Interrogation des exigences autécologiques du hêtre

Le Diagnostic Engine demande au Knowledge Engine toutes les
connaissances relatives aux exigences du hêtre (pH, altitude, climat,
sol). Le Knowledge Engine retourne une `KnowledgeQueryResult`
contenant les objets de connaissance avec leurs niveaux de preuve, leurs
sources (Rameau et al., 2018 ; ONF, 2020) et leurs domaines de validité.
Le Diagnostic Engine sait que le hêtre préfère les pH 5,0–7,0
(evidence B) et les altitudes 0–1400 m (evidence B, domaine France
métropolitaine).

### Cas 2 — Révision d'un seuil de vulnérabilité au gel

Une nouvelle publication (2028) invalide le seuil de -20 °C pour le
sapin pectiné au profit de -15 °C pour les provenances du Sud. Le
Knowledge Engine archive la version 1 (seuil -20 °C, source 2015) dans
l'historique, crée la version 2 (seuil -15 °C, source 2028) avec
justification. Les recommandations émises entre 2015 et 2028 restent
explicables : on sait quel seuil était utilisé (`GSIE-CON-010`).

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
