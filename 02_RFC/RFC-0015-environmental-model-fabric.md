# RFC-0015 — Environmental Model Fabric : registre, outils, preuves et distribution des modèles scientifiques

| Champ | Valeur |
|---|---|
| **ID** | RFC-0015 |
| **Statut** | Adopté |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-18 |
| **Auteur** | Camille Perraudeau (Fondateur) — proposition rédigée à partir de l'étude externe versée en `GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md` |
| **Impact** | Tous les moteurs GSIE (garde-fou transverse étendu), `GSIE/API/` (nouveau module registre), `GSIE/ARCHITECTURE/`, GeoSylva (packs offline), Forge (bancs de benchmark), `03_DECISIONS/`, `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science), GSIE-CON-005 (traçabilité) |
| **Décision liée** | DEC-000026 (Validated) |
| **RFC liées** | RFC-0013 (ingestion données structurées ONF/CNPF/IGN), RFC-0014 (garde-fou anti-invention + pipeline d'extraction documentaire — **cette RFC en est une extension directe**, pas un remplacement) |
| **ADR liés** | ADR-007 (garde-fou transverse anti-invention) — cette RFC généralise ADR-007 des *valeurs* aux *modèles* eux-mêmes |

---

## 1. Objet

RFC-0014 a posé la règle : aucune valeur numérique, corrélation ou
conclusion ne peut circuler dans GSIE sans un `SourceReference`
résolvable. Cette règle couvre les **données**. Elle ne couvre pas
encore les **modèles** (algorithmes, poids entraînés, moteurs
scientifiques externes) que GSIE va inévitablement intégrer au fur et
à mesure de sa Phase 4 — LiDAR, hydrologie, feux, biodiversité,
climat, corrélation causale.

Cette RFC propose un **registre de modèles scientifiques**
(« Environmental Model Fabric ») qui étend la même discipline aux
modèles : chaque modèle intégré à GSIE doit porter sa licence exacte
(code/poids/données), son domaine de validité, ses métriques de
validation et son statut de gouvernance — exactement comme une
Assertion porte sa `SourceReference` et son `evidence_level`.

### 1.1 Ce que cette RFC ne couvre pas

- Le choix technique final de tel ou tel modèle par domaine (LLM,
  LiDAR, hydrologie...) — cette RFC pose le **cadre d'évaluation et
  d'intégration**, pas la décision d'adopter un modèle précis. Chaque
  intégration concrète (ex. airGR, 3DFin, DoWhy) reste une décision
  ultérieure documentée dans `03_DECISIONS/`, instruite via ce cadre.
- Le pipeline d'extraction documentaire (guides, littérature
  narrative) — c'est RFC-0014 §3.2, inchangé.
- L'ingestion de données structurées (BD Forêt, IFN...) — c'est
  RFC-0013, inchangé.

## 2. Contexte et motivation

### 2.1 Constat

L'étude externe versée le 2026-07-18
(`GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md`)
recense un écosystème riche de modèles ouverts pertinents pour
Quintessences (dendrométrie LiDAR, hydrologie, feux, biodiversité,
sols/carbone, corrélation causale, observation de la Terre, LLM
multilingues). Elle conclut cependant qu'**aucun modèle unique** ne
peut devenir le « cerveau scientifique » de Quintessences, et que le
risque principal n'est pas l'absence de modèles mais l'absence d'un
cadre qui :

- distingue la licence du **code** de celle des **poids** et de celle
  des **données** d'entraînement (une chaîne peut être verte sur un
  maillon et rouge sur un autre) ;
- documente le **domaine de validité** de chaque modèle (un tarif de
  cubage calibré sur le chêne méditerranéen ne s'applique pas au
  sapin des Vosges — même logique que la mise en garde IGN déjà
  documentée en RFC-0013) ;
- empêche un LLM de devenir la **source numérique de vérité** au lieu
  d'un simple orchestrateur/explicateur d'outils typés.

### 2.2 Le risque spécifique à nommer

Sans registre, chaque intégration de modèle deviendrait une décision
locale, non tracée, non comparable — le même risque que RFC-0014 a
nommé pour les données individuelles, mais à l'échelle d'un modèle
entier. Un modèle non qualifié pourrait se retrouver en production
sans que quiconque sache sur quelles données il a été entraîné, sous
quelle licence, ni dans quel domaine géographique/climatique/
taxonomique il reste valide.

## 3. Architecture proposée

### 3.1 Le LLM comme orchestrateur non autoritaire

Principe directement issu de l'étude (§0.2, §2) et cohérent avec
CON-001 (« l'IA assiste, ne décide jamais ») :

> **Le LLM ne calcule jamais une valeur métier lui-même.** Il traduit
> une intention en appel(s) d'outils typés, versionnés et testés ; il
> explique un résultat déjà produit par un moteur déterministe ou un
> modèle qualifié. Il ne peut ni inventer une formule, ni modifier une
> mesure, ni présenter une corrélation comme une cause.

Chaque appel d'outil et chaque résultat portent un objet de traçabilité
minimal (repris de l'étude §2.2) :

```json
{
  "tool_id": "dendrometry.volume.compute",
  "model_id": "cubage.fr.chene.zone-x",
  "model_version": "2.1.0",
  "input_observation_ids": ["obs-..."],
  "parameters": {"dbh_cm": 42.3, "height_m": 24.1},
  "result": {"volume_m3": 1.87},
  "uncertainty": {"type": "interval_95", "lower": 1.62, "upper": 2.13},
  "validity": {"status": "within_domain", "warnings": []},
  "evidence_ids": ["source-..."],
  "artifact_sha256": "...",
  "human_validation": "pending"
}
```

### 3.2 Quatre distinctions de vocabulaire imposées

Reprises de l'étude (§7.2, §11.3), à appliquer dans toute interface
utilisateur et toute réponse générée par un moteur GSIE :

1. **Observation / estimation / simulation / recommandation** — une
   mesure de terrain, une valeur dérivée d'un modèle calibré, une
   sortie de simulateur de scénario, et une option proposée au
   professionnel ne doivent jamais être présentées avec le même
   niveau de certitude visuelle.
2. **Association observée / hypothèse causale / effet estimé sous
   hypothèses / aucune conclusion possible** — le mot « cause » n'est
   affiché que si un protocole causal enregistré (§3.5) a passé ses
   tests de réfutation. Sinon, c'est au mieux une « association
   observée ».

### 3.3 Registre de modèles (`ModelRegistry`)

Nouvelle brique dans `GSIE/API/` (module `gsie_api.model_registry`,
nom de travail), avec les entités suivantes (reprises et adaptées de
l'étude §12.1) :

| Entité | Rôle |
|---|---|
| `ModelRegistry` | Entrée canonique d'un modèle : identité, nature (déterministe/statistique/physique/ML/fondation/LLM/ensemble), domaine, tâche |
| `ModelArtifact` | Artefact exécuté : URI, format, taille, SHA-256, signature, SBOM, dépendances |
| `LicenseRecord` | Licence **triple** : code, poids, données — la plus restrictive des trois est celle qui gouverne l'usage réel |
| `ApplicabilityDomain` | Domaine de validité : géographie, climat, essences/taxons, sols, combustibles, âge, diamètre, saison, résolution |
| `ValidationRun` | Jeu de test, séparation spatiale/temporelle, métriques, biais, calibration, hors-domaine (OOD), validateurs humains |

Statuts de gouvernance (repris de l'étude §12.2, alignés sur le cycle
de vie documentaire déjà en place au §5 de `CLAUDE.md`) :
`Experimental` → `Qualified` → `Approved` → `Restricted` /
`Deprecated` / `Revoked` / `Superseded`.

### 3.4 Portes automatiques (extension du garde-fou ADR-007)

Un modèle ne peut pas passer en statut `Approved` si :

- une licence (code, poids ou données) manque ou est ambiguë ;
- le hash/signature de l'artefact ne correspond pas ;
- aucun `ValidationRun` reproductible n'existe ;
- le domaine de validité n'est pas explicite ;
- le modèle ne sait pas signaler une entrée hors domaine ;
- le résultat ne peut pas être relié à ses entrées (pas de chaîne de
  provenance).

Ces portes sont le pendant, pour les modèles, de ce que
`tools/check_governance_consistency.py` fait déjà pour les valeurs
numériques non sourcées (RFC-0014 §3.1).

### 3.5 Moteur de corrélation causale (Correlation Engine v2)

Le Correlation Engine actuel (Phase 4, session 2026-07-17) calcule des
statistiques d'association (Spearman) sur des valeurs déjà fournies.
Cette RFC propose de le faire évoluer vers un pipeline en 8 étapes
(étude §11.2), sans jamais dépasser l'association sans protocole
explicite :

```
Question + variables autorisées
  → Association descriptive (déjà en place : Spearman/Pearson)
  → Contrôle statistique (taille d'échantillon, autocorrélation, FDR)
  → Graphe causal contraint par l'expert (pas décidé librement par le LLM)
  → Découverte temporelle (relations retardées à tester, pas des vérités)
  → Estimation sous hypothèses déclarées
  → Réfutation (placebo, sous-échantillonnage, confondeurs simulés)
  → Incertitude (intervalle, bootstrap, prédiction conforme)
  → Restitution sourcée (LLM explicateur, jamais décideur)
```

Bibliothèques candidates identifiées par l'étude (§11.1), à évaluer
selon le cadre §3.4 avant toute intégration : DoWhy, Tigramite,
EconML, PyMC, MAPIE. `CausalNex` est explicitement écarté (fin de vie
juin 2026, étude §11.1).

### 3.6 Packs offline signés (GeoSylva)

Reprise de l'étude §13 : tout modèle ou référentiel distribué à
GeoSylva (offline-first, RFC-0003) doit voyager dans un **pack de
mission signé**, jamais comme fichier téléchargé librement par
l'interface :

- manifeste versionné, SHA-256, signature, compatibilité d'app minimale ;
- installation atomique, rollback vers la dernière version valide ;
- licence et attribution consultables hors ligne ;
- tout résultat produit hors ligne porte la version exacte du pack
  utilisé (traçabilité, cohérent avec §3.1).

### 3.7 Progression par vertical slices mesurables

Cette RFC interdit explicitement l'ouverture d'un nouveau domaine
scientifique (eau, feux, biodiversité, sols/carbone, climat) tant que
le vertical slice forestier (registre + 1-2 modèles qualifiés +
Correlation Engine v2) n'est pas stable et utilisé en conditions
réelles. Reprend le principe déjà appliqué implicitement cette session
(Climate Engine construit source par source, testé en conditions
réelles avant extension).

## 4. Plan d'implémentation

### Phase A — socle du registre (P0, avant toute nouvelle intégration de modèle)

1. Schéma `ModelRegistry`/`ModelArtifact`/`LicenseRecord`/
   `ApplicabilityDomain`/`ValidationRun` dans le métamodèle v6.2
   (satellite table, cohérent avec RFC-0011/RFC-0012)
2. Porte CI qui refuse tout artefact sans licence, hash, origine et
   jeu de test (extension de `tools/check_governance_consistency.py`)
3. Interface d'outil typée + format de résultat immuable (§3.1)

### Phase B — Correlation Engine v2 (P1)

4. Benchmark DoWhy/Tigramite/PyMC/MAPIE sur le cadre §3.4
5. Pipeline en 8 étapes (§3.5), vocabulaire imposé (§3.2) dans toute
   sortie du moteur

### Phase C — premiers modèles qualifiés (P1-P2, hors périmètre de cette RFC)

6. Un cubage LiDAR (3DFin/lidR) et un modèle hydrologique (airGR)
   comme premiers candidats `Qualified` du registre — décision et
   intégration documentées séparément dans `03_DECISIONS/`, selon le
   cadre posé ici.

### Phase D — packs offline signés (P2)

7. Format de pack (§3.6), signature, rollback — cohérent avec
   RFC-0003 (GSIE-Net) pour GeoSylva.

## 5. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Le registre devient une bureaucratie qui ralentit toute intégration | Friction excessive, contournement informel | Portes automatiques (§3.4) plutôt que revue manuelle systématique ; statut `Experimental` disponible pour prototyper sans porte bloquante |
| Un modèle change de licence en amont (upstream) sans que GSIE le détecte | Violation de licence silencieuse | `LicenseRecord` versionné par artefact, pas par projet — un changement upstream ne s'applique qu'à un nouvel artefact explicitement enregistré |
| Le vocabulaire imposé (§3.2) n'est pas appliqué de façon cohérente dans l'UI | Confusion utilisateur entre mesure et estimation | Composant d'affichage partagé (à définir en spécification séparée), pas une convention laissée à chaque développeur d'app cliente |
| Sur-ingénierie avant tout premier modèle réel intégré | Temps perdu sur un cadre sans cas d'usage concret | Phase C (premier cubage LiDAR + hydrologie) doit suivre immédiatement Phase A, pas être repoussée indéfiniment |

## 6. Alternatives considérées

### 6.1 Ne pas formaliser de registre, documenter chaque modèle au cas par cas dans son propre dossier `ENGINES/`

**Rejetée** — c'est exactement le défaut que RFC-0014 a corrigé pour
les données (assertions dispersées, non comparables). Un modèle sans
registre central ne peut pas être audité transversalement (ex. « quels
modèles ont une licence non-commerciale en production ? »).

### 6.2 Choisir un LLM environnemental spécialisé unique comme socle

**Rejetée** — conclusion explicite de l'étude externe (§0.1, §3.2) :
un LLM spécialisé fige une photographie de son corpus d'entraînement
et ne garantit ni l'exactitude, ni la connaissance du français
technique métier, ni la capacité d'appel d'outils. Le socle doit être
un LLM général moderne (candidats à benchmarker : Apertus, Ministral 3,
Qwen3 — décision séparée, hors périmètre de cette RFC) utilisé comme
orchestrateur, pas comme oracle.

### 6.3 Laisser le Correlation Engine progresser vers la causalité sans distinction de vocabulaire stricte

**Rejetée** — contredit CON-002 (science) : présenter une corrélation
comme une cause sans protocole de réfutation est le risque
scientifique le plus grave identifié par l'étude (§11).

## 7. Conséquences

### 7.1 Positives

- Cadre unique et réutilisable pour évaluer tout modèle ouvert avant
  intégration (dendrométrie, hydrologie, feux, biodiversité, climat...)
- Extension cohérente d'ADR-007/RFC-0014 : la même discipline
  anti-invention s'applique maintenant aux modèles, pas seulement aux
  données
- Empêche la dérive vers un « LLM oracle » qui inventerait des
  résultats scientifiques

### 7.2 Négatives

- Ajoute une couche de gouvernance avant toute intégration de modèle
  — ralentit délibérément l'adoption de nouveaux modèles au profit de
  la traçabilité
- Complexité supplémentaire (nouvelles tables satellite, portes CI)

## 8. Décision requise

**Décision** : Valider cette RFC et autoriser l'implémentation du
socle du registre (§4, Phase A), en commençant par le schéma
`ModelRegistry` et la porte CI, puis le Correlation Engine v2 (Phase B).
Les intégrations de modèles concrets (Phase C) resteront des décisions
séparées, instruites via ce cadre.

**Décideur** : Camille Perraudeau (Fondateur)

## 9. Références

- `GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md` — étude source de cette RFC
- `02_RFC/RFC-0014-gouvernance-scientifique-anti-invention.md` — garde-fou anti-invention des données, étendu ici aux modèles
- `02_RFC/RFC-0013-ingestion-donnees-onf-cnpf.md` — pipeline de données structurées, non affecté par cette RFC
- `02_RFC/RFC-0003.md` — GSIE-Net, packs offline signés (§3.6)
- `GSIE/ARCHITECTURE/ADR-007-garde-fou-anti-invention.md` — généralisé ici des valeurs aux modèles
- `00_CONSTITUTION/GSIE-CON-001.md` — l'IA assiste, ne décide jamais
- `00_CONSTITUTION/GSIE-CON-002.md` — science
- `GSIE/ENGINES/CORRELATION_ENGINE/CORRELATION_ENGINE.md` — moteur concerné par §3.5

## 10. Historique

| Date | Modification | Auteur |
|---|---|---|
| 2026-07-18 | Création — RFC-0015 Draft | Camille Perraudeau |
| 2026-07-18 | Validation Fondateur — Adopté (DEC-000026 Validated) | Camille Perraudeau |
