# Evidence Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Evidence Engine |
| **Catégorie** | Chaîne d'intelligence (filtre amont) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005, GSIE-CON-010 |
| **Ordre de développement** | 2 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Évaluer la qualité scientifique de chaque connaissance avant son
intégration dans GSIE et lui attribuer un niveau de preuve sourcé et
traçable.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Sources externes — publications | Donnée brute | Articles scientifiques peer-reviewed, méta-analyses |
| Sources externes — référentiels | Donnée brute | Référentiel Pédologique Français, WRB, BDNFF, IGN, Météo-France |
| Sources externes — experts | Donnée brute | Connaissances d'experts identifiés (niveau « expert ») |
| Sources externes — observations terrain | Donnée brute | Relevés de terrain, inventaires, photos |
| `GSIE/DATASETS/` | Métadonnées | Jeux de données référencés et sourcés |
| `GSIE/RESEARCH/` | Métadonnées | Bibliographie sourcée |
| Pipeline d'import | Donnée brute | Données brutes en attente de qualification |

L'Evidence Engine est le **point d'entrée amont** du système : il ne
consomme la sortie d'aucun autre moteur.

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Connaissance qualifiée | Connaissances dotées d'un niveau de preuve, d'une source et d'un identifiant de version |
| `LEARNING_ENGINE` | Signaux | Connaissances dont le niveau de preuve est susceptible d'évolution (réévaluation) |
| Journal d'audit | Trace | Historique des évaluations, conflits détectés, décisions de qualification |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Bases externes | `GSIE/DATASETS/`, `GSIE/RESEARCH/` | Sources de métadonnées et bibliographie |
| Aucun moteur | — | L'Evidence Engine ne dépend d'aucun autre moteur (amont de la chaîne) |

## 5. Contrat d'interface

### Entrée — `RawKnowledgeSubmission`

```
RawKnowledgeSubmission = {
  soumission_id     : UUID
  type_contenu      : enum { publication, referentiel, expert, observation }
  contenu           : structure libre (texte, tableau, mesure, image)
  source_candidate  : SourceReference
  date_soumission   : ISO 8601
  soumetteur        : Identifiant (utilisateur ou pipeline automatique)
}

SourceReference = {
  type_source   : enum { peer_reviewed, referentiel_officiel, expert_identifie, observation_terrain }
  auteur        : texte ou organisme
  date_publication : ISO 8601 (optionnel)
  reference     : texte (DOI, URL, citation, code référentiel)
  version_source : texte (optionnel)
}
```

### Sortie — `QualifiedKnowledge`

```
QualifiedKnowledge = {
  connaissance_id   : UUID
  contenu_normalise : structure (dépend du type de connaissance)
  evidence_level    : enum { A, B, C, D, E, F }
    // A = méta-analyse / consensus fort
    // B = établi (peer-reviewed, reproductible)
    // C = probable (peer-reviewed, domaine partiel)
    // D = expert identifié, non publié
    // E = observation terrain non publiée
    // F = incertain / contesté
  source            : SourceReference
  version           : entier (commence à 1)
  date_qualification: ISO 8601
  conflits          : liste de ConflitBibliographique (optionnel)
  statut            : enum { accepte, quarantine, refuse }
}

ConflitBibliographique = {
  source_a : SourceReference
  source_b : SourceReference
  description : texte
}
```

## 6. Garanties

- **Aucune connaissance n'entre dans le système sans niveau de preuve**
  (principe fondateur, `GSIE_CORE_BLUEPRINT.md`).
- Toute connaissance qualifiée porte une source identifiable et
  vérifiable (`GSIE-CON-002`).
- L'historique des évaluations est conservé — une réévaluation
  n'écrase jamais l'ancienne (`GSIE-CON-010`).
- Les conflits bibliographiques sont signalés, jamais résolus
  arbitrairement (`GSIE-CON-002`).
- Les connaissances sans source sont mises en quarantaine, jamais
  intégrées silencieusement (`GSIE-CON-005`).
- Fonctionnement hors-ligne complet (article T-8) — l'évaluation se
  fait sur les données déjà importées.

## 7. Cas d'usage

### Cas 1 — Import d'une publication sur l'autécologie du chêne sessile

Une publication peer-reviewed (Rameau et al., 2018) décrit l'optimum
écologique du chêne sessile sur sols acides à pH 4,5–6,0. L'Evidence
Engine évalue la source : type `peer_reviewed`, reproductible, consensus
modéré → `evidence_level = B`. La connaissance est acceptée et transmise
au Knowledge Engine. Aucune autre source ne contredit ce range pour
cette essence → aucun conflit.

### Cas 2 — Détection d'un conflit sur le seuil de vulnérabilité au gel

Deux publications donnent des seuils différents de vulnérabilité au gel
pour le sapin pectiné : -20 °C (source A, 2015) et -15 °C (source B,
2023, provenances du Sud). L'Evidence Engine qualifie les deux
connaissances (niveaux B et C respectivement), crée un
`ConflitBibliographique` référençant les deux sources, et transmet les
deux au Knowledge Engine. Aucune moyenne arbitraire n'est calculée.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
