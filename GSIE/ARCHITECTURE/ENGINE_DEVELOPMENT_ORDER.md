# ENGINE_DEVELOPMENT_ORDER — Ordre de développement des moteurs

| Champ | Valeur |
|---|---|
| **Livrable** | 204 — Ordre de développement des moteurs |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-004, GSIE-CON-005, GSIE-CON-007, GSIE-CON-010 |
| **Constitutions liées** | Technique (T-1, T-2, T-5, T-7) |
| **RFC de référence** | RFC-0003 (GSIE-Net) |
| **Décision d'ouverture** | DEC-000004 |

---

## 1. Objet

Définir l'ordre de développement des 14 moteurs de GSIE, justifier
cet ordre par les dépendances, identifier les parallélisations
possibles et définir les critères de complétude de chaque moteur.

> **Note de gouvernance :** ce document planifie l'ordre de
> développement pour la **Phase 4** (Implémentation). En Phase 2
> (Architecture), aucun moteur n'est implémenté — ce document
> prépare la séquence d'implémentation future (DEC-000004).

---

## 2. Graphe de dépendances

L'ordre de développement est dicté par le **graphe de dépendances**
des moteurs. Un moteur ne peut être développé que si ses
dépendances amont sont fonctionnelles (T-1 : graphe acyclique).

```
                    ┌──────────────┐
                    │   EVIDENCE   │  (aucune dépendance moteur)
                    │   ENGINE     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  KNOWLEDGE   │  (dépend: Evidence)
                    │  ENGINE      │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┬────────────────┐
          │                │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │    GIS      │  │  BOTANICAL  │  │  PEDOLOGY   │  │  CLIMATE    │
   │  ENGINE     │  │  ENGINE     │  │  ENGINE     │  │  ENGINE     │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │                │
          └────────────────┼────────────────┴────────────────┘
                           │
                    ┌──────▼──────┐
                    │ CORRELATION │  (dépend: Knowledge + tous les moteurs domaine)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  REASONING  │  (dépend: Knowledge, Correlation)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  DIAGNOSTIC │  (dépend: Reasoning + moteurs domaine)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │FOREST DYN.  │  (dépend: Knowledge, Correlation)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ SIMULATION  │  (dépend: Forest Dynamics, Climate)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │RECOMMENDATION│ (dépend: Diagnostic, Simulation)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ VALIDATION  │  (dépend: Recommendation, Diagnostic)
                    │  ENGINE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  LEARNING   │  (dépend: tous les moteurs — transverse)
                    │  ENGINE     │  (développé en dernier)
                    └─────────────┘
```

> **Note de cohérence avec le livrable 206 (contrats d'interface) :**
> Le graphe ci-dessus représente les **dépendances de développement**
> (un moteur ne peut être implémenté que si ses dépendances amont sont
> fonctionnelles). Il se distingue de la **matrice d'interactions** du
> livrable `ENGINE_INTERFACE_CONTRACTS.md`, qui décrit les **flux de
> données à l'exécution**. Les deux visions sont complémentaires et
> cohérentes :
>
> - Les moteurs domaine (GIS, Botanical, Pedology, Climate) dépendent de
>   Knowledge Engine **pour le développement** (cache, ontologie), mais
>   n'échangent pas de flux direct avec Knowledge à l'exécution — la
>   matrice d'interactions les montre émettant vers Diagnostic et
>   Simulation uniquement.
> - Correlation Engine dépend de tous les moteurs domaine pour le
>   développement (les données doivent être disponibles pour être
>   croisées), mais à l'exécution, Correlation requête Knowledge (flux
>   direct `KnowledgeQuery`) — c'est Knowledge qui centralise l'accès
>   aux données domaine.
> - Forest Dynamics Engine est positionné en Vague 4 (dépend de
>   Knowledge et Correlation pour le développement) ; à l'exécution, il
>   émet vers Diagnostic et Simulation, conformément à la matrice.

---

## 3. Ordre de développement

L'ordre est organisé en **vagues**. Chaque vague ne commence que
lorsque la vague précédente a atteint ses critères de complétude
(§5). Au sein d'une vague, les moteurs peuvent être parallélisés
(§4).

### Vague 0 — Fondations (préalables aux moteurs)

| # | Composant | Justification |
|---|---|---|
| 0a | Modèle de données scientifique (livrable 205) | Les moteurs manipulent des entités ; le modèle doit exister avant tout moteur |
| 0b | Protocole de communication (livrable 203) | Les moteurs communiquent par ce protocole ; il doit être défini avant |
| 0c | Stack technologique (livrable 202) | Les moteurs sont implémentés dans cette stack ; elle doit être validée |
| 0d | Contrats d'interface (livrable 206) | Chaque moteur a un contrat ; les contrats amont doivent être définis |

### Vague 1 — Filtre amont et base de connaissances

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 1 | **Evidence Engine** | Aucune | Filtre amont obligatoire — aucune donnée n'entre sans niveau de preuve (S-2). Sans Evidence, aucun moteur ne peut recevoir des données qualifiées. |
| 2 | **Knowledge Engine** | Evidence | Centralise les connaissances qualifiées. Tous les autres moteurs consomment le Knowledge Graph. Sans Knowledge, aucun moteur ne peut requêter des connaissances. |

**Justification de la vague 1 :** ces deux moteurs sont la **porte
d'entrée** du système. Evidence qualifie, Knowledge structure. Sans
eux, le pipeline n'a ni entrée ni stockage. Ils sont strictement
séquentiels : Knowledge dépend d'Evidence (une connaissance n'entre
dans le graphe qu'après qualification).

### Vague 2 — Moteurs domaine (données de référence)

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 3 | **GIS Engine** | Knowledge (cache) | Fournit les données géospatiales (parcelles, relief). Indépendant des autres moteurs domaine. |
| 4 | **Botanical Engine** | Knowledge (ontologie) | Fournit taxonomie et autécologie. Indépendant des autres moteurs domaine. |
| 5 | **Pedology Engine** | Knowledge (cache) | Fournit les données pédologiques. Indépendant des autres moteurs domaine. |
| 6 | **Climate Engine** | Knowledge (cache) | Fournit les données climatiques. Indépendant des autres moteurs domaine. |

**Justification de la vague 2 :** les moteurs domaine sont les
**sources de données** que le raisonnement croisera. Ils dépendent
de Knowledge (pour le cache et l'ontologie) mais sont **indépendants
entre eux** — ils peuvent être développés en parallèle (§4). Ils
doivent précéder Correlation, qui les croise tous.

### Vague 3 — Croisement et raisonnement

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 7 | **Correlation Engine** | Knowledge + tous les moteurs domaine | Croise les données multi-domaines. Nécessite que tous les moteurs domaine soient fonctionnels pour avoir des données à croiser. |
| 8 | **Reasoning Engine** | Knowledge, Correlation | Raisonne sur les connaissances et les corrélations. Dépend de Correlation pour les croisements. |

**Justification de la vague 3 :** Correlation ne peut être développé
que lorsque les moteurs domaine fournissent des données. Reasoning
dépend de Correlation — il est strictement après. Ces deux moteurs
sont séquentiels dans la vague.

### Vague 4 — Diagnostic et dynamique

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 9 | **Diagnostic Engine** | Reasoning + moteurs domaine | Synthétise un diagnostic à partir des conclusions et des données domaine. Dépend de Reasoning. |
| 10 | **Forest Dynamics Engine** | Knowledge, Correlation | Modélise la croissance et la dynamique. Dépend de Correlation pour les croisements. Indépendant de Diagnostic. |

**Justification de la vague 4 :** Diagnostic et Forest Dynamics
dépendent tous deux de la vague 3 mais sont **indépendants entre
eux** — ils peuvent être parallélisés. Diagnostic synthétise l'état
actuel ; Forest Dynamics projette l'évolution.

### Vague 5 — Simulation et recommandation

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 11 | **Simulation Engine** | Forest Dynamics, Climate | Projette des scénarios long terme. Dépend de Forest Dynamics pour la croissance et de Climate pour les projections climatiques. |
| 12 | **Recommendation Engine** | Diagnostic, Simulation | Propose des recommandations à partir du diagnostic et des simulations. Dépend des deux. |

**Justification de la vague 5 :** Simulation dépend de Forest
Dynamics (vague 4). Recommendation dépend de Diagnostic (vague 4)
et de Simulation (vague 5) — elle est donc strictement après
Simulation.

### Vague 6 — Validation

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 13 | **Validation Engine** | Recommendation, Diagnostic | Dernier rempart avant l'utilisateur. Dépend des sorties de Recommendation et de Diagnostic. |

**Justification de la vague 6 :** Validation est le **dernier
moteur du pipeline principal**. Elle valide les sorties de
Recommendation (et indirectement tout le pipeline amont). Elle ne
peut être développée que lorsque le pipeline complet produit des
sorties à valider.

### Vague 7 — Apprentissage (transverse)

| # | Moteur | Dépendances | Justification de la position |
|---|---|---|---|
| 14 | **Learning Engine** | Tous les moteurs (transverse) | Améliore les modèles à partir des retours terrain. Transverse — interagit avec tous les moteurs. Développé en dernier car il nécessite un pipeline complet fonctionnel pour avoir des retours à apprendre. |

**Justification de la vague 7 :** Learning est transverse et
**rétroactif** — il alimente Knowledge, Correlation et Reasoning en
retour. Il ne peut être développé que lorsque le pipeline principal
fonctionne de bout en bout, car il apprend des retours d'expérience
sur le pipeline complet.

### 3.1 Positionnement des moteurs transverses

Trois moteurs ont un statut particulier par rapport à la chaîne
principale (Evidence → Knowledge → Correlation → Reasoning →
Diagnostic → Recommendation → Validation). Ils ne sont pas des
maillons linéaires de cette chaîne mais des moteurs **transverses**
qui l'alimentent ou la prolongent. Leur positionnement dans la
séquence de développement est explicité ci-dessous.

| Moteur | Vague | Positionnement | Justification |
|---|---|---|---|
| **Forest Dynamics Engine** | Vague 4 (parallèle à Diagnostic) | Après la chaîne Knowledge → Correlation, **en parallèle** de Diagnostic | Forest Dynamics modélise la croissance et la dynamique forestière. Il dépend de Knowledge (structures) et Correlation (croisements) mais **pas** de Reasoning ni de Diagnostic — il est donc indépendant de Diagnostic et peut être développé en parallèle. Il alimente Simulation (vague 5) en projections de croissance. |
| **Simulation Engine** | Vague 5 (après Forest Dynamics, avant Recommendation) | **Après** Forest Dynamics et Climate, **avant** Recommendation | Simulation projette des scénarios long terme. Elle dépend de Forest Dynamics (croissance) et Climate (projections climatiques) pour ses conditions aux limites. Elle alimente Recommendation en scénarios comparés. Elle est strictement après Forest Dynamics (vague 4) et avant Recommendation (même vague 5, séquentiel). |
| **Learning Engine** | Vague 7 (après le pipeline complet) | **En dernier**, après Validation (vague 6) | Learning est le seul moteur **rétroactif** : il remonte des corrections vers Evidence (réévaluation de preuve), Knowledge (mises à jour) et Correlation (feedback). Il nécessite un pipeline complet fonctionnel de bout en bout pour disposer de retours d'expérience à apprendre. Un démarrage en mode passif (collecte seule) est prévu avant l'apprentissage actif (voir §7, risques). |

**Synthèse du positionnement :**

- **Forest Dynamics** se développe **en parallèle** de la chaîne
  principale (Vague 4), dès que Knowledge et Correlation sont
  fonctionnels. Il n'attend pas Diagnostic.
- **Simulation** se développe **après** Forest Dynamics et Climate,
  mais **avant** Recommendation — il est sur le chemin critique entre
  les moteurs domaine/transverses et la recommandation.
- **Learning** se développe **en dernier** (Vague 7), une fois le
  pipeline complet fonctionnel. Il est le seul moteur qui boucle le
  système (rétroaction vers les moteurs amont).

> **Note :** Forest Dynamics est classé parmi les moteurs domaine dans
> la documentation des moteurs (`GSIE/ENGINES/`) mais fonctionne ici
> comme un moteur transverse car il n'est pas un maillon linéaire de
> la chaîne d'intelligence — il alimente Simulation et Diagnostic
> sans être traversé par le flux Evidence → Validation.

---

## 4. Parallélisation possible

### 4.1 Matrice de parallélisation

```
Temps →
Vague 0:  [0a modèle] [0b proto] [0c stack] [0d contrats]
              └────────── fondations ──────────┘
Vague 1:  [1 Evidence] → [2 Knowledge]
                              │
Vague 2:              ┌──────┼──────┬──────┐
                      │      │      │      │
                   [3 GIS][4 Bot][5 Ped][6 Clim]  ← PARALLÈLE
                      └──────┼──────┴──────┘
                             │
Vague 3:              [7 Correlation] → [8 Reasoning]
                             │
Vague 4:              ┌──────┴──────┐
                   [9 Diagnostic][10 Forest Dyn.]  ← PARALLÈLE
                      └──────┬──────┘
                             │
Vague 5:              [11 Simulation] → [12 Recommendation]
                             │
Vague 6:              [13 Validation]
                             │
Vague 7:              [14 Learning]
```

### 4.2 Parallélisations identifiées

| Vague | Moteurs parallélisables | Condition |
|---|---|---|
| Vague 2 | GIS, Botanical, Pedology, Climate | Knowledge Engine fonctionnel (vague 1 complète) |
| Vague 4 | Diagnostic, Forest Dynamics | Reasoning et Correlation fonctionnels (vague 3 complète) |

### 4.3 Parallélisation non possible

| Vague | Moteurs séquentiels | Raison |
|---|---|---|
| Vague 1 | Evidence → Knowledge | Knowledge dépend d'Evidence (qualification préalable) |
| Vague 3 | Correlation → Reasoning | Reasoning dépend de Correlation (croisement préalable) |
| Vague 5 | Simulation → Recommendation | Recommendation dépend de Simulation (scénarios préalables) |
| Vague 6 | Validation (seul) | Dépend de toute la chaîne amont |
| Vague 7 | Learning (seul) | Transverse, dépend du pipeline complet |

### 4.4 Gain théorique de parallélisation

Avec 2 équipes de développement :

- **Sans parallélisation :** 14 moteurs séquentiels = 14 unités de
  temps.
- **Avec parallélisation (vagues 2 et 4) :** vague 2 (4 moteurs en
  parallèle = 1 unité au lieu de 4) + vague 4 (2 moteurs en
  parallèle = 1 unité au lieu de 2) = **11 unités de temps** (gain
  ~21 %).

> Le gain réel dépend de la taille des moteurs. Les moteurs domaine
> (vague 2) sont susceptibles d'être plus simples que les moteurs
> de raisonnement (vagues 3-5), ce qui amplifie le gain.

---

## 5. Critères de complétude par moteur

Chaque moteur est considéré **complet** lorsque **tous** les
critères suivants sont satisfaits. Ces critères découlent de la
Constitution Technique (T-1, T-5) et de la Constitution Scientifique
(S-1 à S-7).

### 5.1 Critères communs (tous moteurs)

| # | Critère | Référence |
|---|---|---|
| C1 | Document de moteur détaillé (responsabilité, entrées/sorties, dépendances, garanties, cas d'usage) | T-1, livrable 207 |
| C2 | Contrat d'interface versionné et documenté | T-2, livrable 206 |
| C3 | Tests unitaires — couverture ≥ 80 % sur la logique métier | T-5 |
| C4 | Tests d'intégration aux frontières avec les moteurs dépendances | T-5 |
| C5 | Tests fonctionnels sur les cas d'usage documentés | T-5 |
| C6 | Journalisation structurée (toute opération est tracée) | CON-005, T-7 |
| C7 | Gestion des erreurs explicite (codes, messages, retryable) | T-7 |
| C8 | Mode hors-ligne documenté et fonctionnel (ou mode dégradé documenté) | T-8 |
| C9 | Aucune dépendance circulaire | T-1 |
| C10 | Documentation correspond au comportement (validation documentaire) | T-5, CON-006 |

### 5.2 Critères spécifiques par moteur

| Moteur | Critère spécifique supplémentaire |
|---|---|
| **Evidence Engine** | Niveau de preuve attribué à toute entrée (S-2) ; conflits bibliographiques détectés et documentés (S-3) |
| **Knowledge Engine** | Ontologie et Knowledge Graph opérationnels ; historique des révisions conservé (CON-010, S-4) |
| **Correlation Engine** | Matrice de corrélations justifiées (chaque corrélation cite ses sources) |
| **Reasoning Engine** | Chaîne d'inférence documentée pour toute conclusion (CON-004) ; contradictions détectées |
| **Diagnostic Engine** | Confiance et incertitudes documentées (S-5) ; ne prescrit pas d'action |
| **Recommendation Engine** | Alternatives proposées (pas une seule option) ; recommandations contournables (CON-001) ; refus journalisés |
| **Validation Engine** | Toute sortie non conforme est bloquée avec cause journalisée ; respect de la Constitution vérifié |
| **GIS Engine** | Toute donnée géospatiale est sourcée et datée ; cache local fonctionnel hors-ligne |
| **Climate Engine** | Projections affichées avec scénario (RCP/SSP) et incertitude (S-5) ; mode dégradé temps réel documenté |
| **Pedology Engine** | Toute classification pédologique cite son référentiel (RPF, WRB) ; aucun seuil inventé (CON-002) |
| **Botanical Engine** | Évolutions taxonomiques tracées (CON-010) ; synonymes gérés ; référentiels officiels (Tela Botanica, GBIF, BDNFF) |
| **Forest Dynamics Engine** | Modèles de croissance sourcés ; perturbations prises en compte |
| **Simulation Engine** | Chaque scénario est explicable (CON-004) ; résultats présentés comme scénarios, pas décisions (CON-001) |
| **Learning Engine** | Toute sortie est explicable et traçable (CON-004) ; ne remplace jamais Knowledge Engine ni les règles expertes ; l'IA assiste, ne décide pas (CON-001) |

---

## 6. Ordre synthétique

| Vague | Moteur(s) | Catégorie | Parallélisable ? | Critère de passage à la vague suivante |
|---|---|---|:---:|---|
| 0 | Fondations (modèle, protocole, stack, contrats) | Préalable | Partiel | Tous les livrables Phase 2 validés |
| 1 | Evidence → Knowledge | Chaîne principale | Non | Knowledge Engine complet (C1-C10) |
| 2 | GIS · Botanical · Pedology · Climate | Moteurs domaine | **Oui** | Tous les moteurs domaine complets (C1-C10) |
| 3 | Correlation → Reasoning | Chaîne principale | Non | Reasoning Engine complet (C1-C10) |
| 4 | Diagnostic · Forest Dynamics | Chaîne principale + transverse | **Oui** | Les deux moteurs complets (C1-C10) |
| 5 | Simulation → Recommendation | Transverse + chaîne principale | Non | Recommendation Engine complet (C1-C10) |
| 6 | Validation | Chaîne principale | Non | Validation Engine complet (C1-C10) |
| 7 | Learning | Transverse | Non | Learning Engine complet (C1-C10) + pipeline complet fonctionnel |

---

## 7. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Evidence Engine trop rigoureux (tout rejeté) | Pipeline bloqué, aucune connaissance n'entre | Mode dégradé documenté : niveau F (Observation) accepté par défaut avec signalisation |
| Knowledge Graph trop complexe pour la vague 1 | Retard sur toute la suite | Commencer par un graphe minimal (essences, stations, sources) ; étendre par itération |
| Moteurs domaine (vague 2) avec des sources incomplètes | Correlation (vague 3) a des données partielles | Chaque moteur domaine définit un mode dégradé documenté (T-8) ; Correlation gère les données manquantes |
| Parallélisation vague 2 avec 1 seule équipe | Pas de gain de temps | Sérialiser dans l'ordre GIS → Botanical → Pedology → Climate (priorité aux données les plus utilisées) |
| Learning Engine (vague 7) nécessite beaucoup de données terrain | Pas assez de retours pour apprendre | Démarrer avec un Learning Engine passif (collecte seule) avant l'apprentissage actif |

---

## 8. Ce que ce document ne fait PAS

- Il n'implémente aucun code (Phase 2 — interdit, DEC-000004).
- Il n'estime pas la durée de développement de chaque moteur (à
  évaluer en Phase 3/4).
- Il n'attribue pas de ressources humaines (décision organisationnelle
  hors périmètre architecture).
- Il ne contredit aucun article constitutionnel.

---

## 9. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — version squelette (Phase 1, 13 moteurs listés) |
| 2026-07-12 | Enrichissement Phase 2 — vagues, dépendances, parallélisation, critères de complétude, 14 moteurs |
| 2026-07-12 | Correction audit — en-tête gouvernance (CON-004, CON-005, T-7), graphe dépendances (Climate Engine), note cohérence livrable 206, positionnement moteurs transverses, colonne Catégorie tableau synthétique |

---

## 10. Validation

Document en statut **Draft**. Passage en `Review` soumis à
validation du Fondateur. Aucune modification destructive sans
versionnement préalable (CON-010, T-6).
