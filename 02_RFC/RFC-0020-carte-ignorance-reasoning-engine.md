# RFC-0020 — Carte de l'ignorance : première implémentation du Reasoning Engine (périmètre forestier)

| Champ | Valeur |
|---|---|
| **ID** | RFC-0020 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-20 |
| **Auteur** | Camille Perraudeau (Fondateur), design co-construit avec l'agent GSIE (brainstorming) |
| **Impact** | Reasoning Engine (première implémentation de code — jusqu'ici documenté seulement, Phase 2, ordre 10 dans `ENGINE_DEVELOPMENT_ORDER.md`), Botanical/Forest Dynamics Engines (consommés), registre de modèles (RFC-0015, réutilisé pour le barème), packs offline signés GeoSylva (RFC-0015), GeoSylva (consommateur, hors périmètre technique de ce RFC) |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science sourcée), GSIE-CON-003 (connaissance avant code), GSIE-CON-005 (traçabilité) |
| **RFC liées** | RFC-0015 (Environmental Model Fabric — `ModelModel`/`ModelVersionModel` réutilisés pour le barème, packs offline signés), RFC-0016 (schéma forestier — `AutecologyProfile`, `StationObservation.determination_uncertainty`, `EvidenceLevel`, pattern `human_validator`/`SilviculturalRule`), RFC-0014 (garde-fou anti-invention ADR-007, directement applicable au barème de poids) |
| **Veille d'origine** | `GSIE/RESEARCH/VEILLE_INNOVATIONS_QUINTESSENCES_2026-07-20.md` §2.1 (piste 1 — retenue comme prioritaire) |
| **Décision liée** | Aucune — RFC en Draft, aucune implémentation autorisée |

---

## 1. Objet

Implémenter une première capacité concrète du **Reasoning Engine**
(l'un des 14 moteurs GSIE documentés, sans code à ce jour) : calculer,
pour une observation ou une parcelle forestière, un **score
d'incertitude explicable** et une **recommandation de la mesure
suivante la plus utile** pour réduire cette incertitude — jamais une
action déclenchée automatiquement, toujours une suggestion au
forestier (GSIE-CON-001).

Périmètre volontairement restreint au domaine forestier/GeoSylva pour
ce premier RFC. La généralisation à Ignis/Hydro/Atmos/Terra n'est pas
engagée ici — elle sera un RFC séparé si le résultat forestier est
concluant.

## 2. Ce que ce RFC ne couvre pas

- Un modèle statistique/bayésien de valeur de l'information — rejeté
  au profit d'un barème déterministe et explicable (voir §5), cohérent
  avec l'exigence ADR-007 (rien d'inventé, tout sourcé ou marqué
  comme heuristique).
- La création d'un 15ᵉ moteur — cette capacité reste dans le
  Reasoning Engine déjà acté (14 moteurs, architecture non modifiée).
- Le déclenchement automatique d'une mission terrain — la
  recommandation reste une suggestion contournable.
- L'implémentation côté GeoSylva (Kotlin) elle-même — ce RFC couvre le
  calcul serveur GSIE et le format du barème distribué ; la
  consommation offline par l'app est mentionnée (§6) mais son
  implémentation technique relève d'un ticket GeoSylva séparé.
- Le calcul détaillé des pénalités de contradiction/péremption
  (formules exactes) — posé en principe au §5, à préciser en Tranche 2
  sur la base de cas réels plutôt que théoriquement à l'avance.

## 3. Contexte et motivation

GSIE dispose déjà de signaux d'incertitude épars mais jamais agrégés
ni exploités activement : `EvidenceLevel` (A-F) sur chaque assertion,
`determination_uncertainty` sur `StationObservation` (RFC-0016),
`ConflictRecord`/`ConflictClusterModel` pour les contradictions entre
sources. Aujourd'hui, rien ne les combine pour répondre à la question
qu'un forestier se pose réellement sur le terrain : *« que devrais-je
mesurer maintenant pour améliorer le plus possible ma décision ? »*.
La veille du 2026-07-20 (`VEILLE_INNOVATIONS_QUINTESSENCES_2026-07-20.md`)
identifie cette capacité comme la piste d'innovation la plus
directement utile et la plus proche de la faisabilité technique
immédiate parmi 14 pistes évaluées.

## 4. Principe non négociable

Le score d'incertitude et la recommandation sont toujours des sorties
du **Reasoning Engine**, jamais calculées « de mémoire » par un LLM
(cohérent avec le principe déjà posé en RFC-0019 §4 pour tout futur
gateway IA). Le barème de poids utilisé n'est jamais présenté avec une
confiance uniforme : un poids sourcé et un poids heuristique non
sourcé doivent être visuellement et structurellement distincts dans
toute sortie (GSIE-CON-002, ADR-007).

## 5. Conception

### 5.1 Modèle de données

Deux nouveaux types de resource (registre GSIE, pattern
`@register_type` déjà en place) :

- **`IgnoranceAssessment`** — sujet évalué (`StationObservation` ou
  `AutecologyProfile`), score global (0-1), décomposition par cause
  (variable manquante, `EvidenceLevel` faible, contradiction,
  péremption), date de calcul, version du barème utilisé
  (`model_version_id`).
- **`ObservationRecommendation`** — liée à un `IgnoranceAssessment` :
  liste ordonnée de mesures suggérées (`variable`, `gain_estime`,
  `methode_suggeree`), jamais une seule recommandation imposée sans
  alternative visible.

Le **barème de poids** (`variable → impact estimé sur la décision`)
n'est **pas** une nouvelle table : il réutilise `ModelModel`/
`ModelVersionModel` (déjà existants, RFC-0015 — `ApplicabilityDomain`,
`LicenseRecord`, `ValidationRun` s'appliquent donc directement, sans
duplication).

### 5.2 Garde-fou sur le barème (détail du principe §4)

Chaque entrée du barème porte :
- une source publiée (référence bibliographique) **ou** l'étiquette
  explicite `heuristique_non_sourcee` ;
- un `evidence_level` (A-F, `F` obligatoire si non sourcé) ;
- un statut de cycle de vie (`draft`/`accepted`/…) — le passage à
  `accepted` exige un `human_validator` non nul, exactement le pattern
  déjà imposé pour `SilviculturalRule` (RFC-0016 §3.2, contrainte SQL
  `ck_silvicultural_rule_human_validation_required`).

### 5.3 Algorithme (déterministe, explicable)

```
score_ignorance(sujet) =
    Σ (poids[variable] × indicateur_manquant_ou_incertain[variable])
    + pénalité_contradictions(ConflictRecord liés au sujet)
    + pénalité_péremption(âge de la donnée vs domaine de validité)

prochaine_mesure = argmax(poids[variable] × indicateur_manquant[variable])
    parmi les variables du domaine de validité applicable au sujet
```

Chaque terme du score doit être traçable jusqu'à sa source dans la
sortie — cohérent avec le passeport de décision à 5 catégories
(RFC-0016 §3.4) : le score lui-même est une valeur `calculée`, jamais
`observée`.

### 5.4 Distribution vers GeoSylva (mix serveur-source-de-vérité / calcul local)

Le barème validé (`accepted`) est empaqueté dans les **packs offline
signés** déjà prévus par RFC-0015. GeoSylva télécharge le pack et
exécute **localement, sans réseau**, le même calcul déterministe
(§5.3) — pas d'appel réseau nécessaire pour afficher une recommandation
sur le terrain. Au retour du réseau, les nouvelles observations
remontent à GSIE, qui recalcule côté serveur (source de vérité) et
peut affiner le barème avec plus de données au fil du temps. Ce
principe prolonge directement l'offline-first déjà exigé pour
GeoSylva (RFC-0003) et la piste « patches scientifiques hors ligne »
de la veille d'innovation.

## 6. Plan par tranches (sur le modèle RFC-0016/RFC-0018)

- **Tranche 1** — schéma de données uniquement (`IgnoranceAssessment`,
  `ObservationRecommendation`), aucun calcul réel, tests de
  validation des champs obligatoires (même porte de validation que
  `fertility_class`/`identification_decision`, RFC-0016/RFC-0018).
- **Tranche 2** — premier barème réel, volontairement restreint (2-3
  variables sourcées, ex. profondeur de sol, humidité — à choisir sur
  des sources déjà présentes dans `GSIE/RESEARCH/`), calcul serveur
  (`score_ignorance`), tests sur cas réels.
- **Tranche 3** — export du barème validé dans un pack offline signé ;
  l'implémentation du calcul côté GeoSylva (Kotlin) est un chantier
  séparé, hors périmètre technique de ce RFC GSIE.

## 7. Alternatives considérées

- **Modèle statistique/bayésien de valeur de l'information** —
  théoriquement plus proche de la recherche en *active sensing*
  citée par la veille d'origine, mais nécessiterait un modèle
  probabiliste calibré par domaine avant toute Phase A, plus lourd à
  valider scientifiquement et moins auditable qu'un barème
  déterministe. Rejeté pour ce premier RFC — pourrait être reconsidéré
  si le barème déterministe montre ses limites après usage réel.
- **Nouveau moteur dédié (15ᵉ moteur)** — séparation plus nette mais
  romprait l'architecture à 14 moteurs déjà actée sans bénéfice net
  pour un premier cas d'usage. Rejeté.
- **Logique entièrement côté GeoSylva** — romprait GSIE-CON-003
  (connaissance/calcul scientifique centralisé dans GSIE) et
  empêcherait Ignis/Hydro de réutiliser la même logique plus tard.
  Rejeté au profit du mix retenu (§5.4) : barème sourcé et validé côté
  GSIE, calcul exécuté localement par l'app à partir de ce barème.

## 8. Prochaine étape

RFC en `Draft`. Passage en `Review` à la demande du fondateur, puis
décision (`03_DECISIONS/`) avant toute implémentation — seule la
Tranche 1 (§6) serait autorisée en premier, comme pour RFC-0016 et
RFC-0018.
