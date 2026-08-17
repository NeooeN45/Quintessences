# RFC-0040 — Contrôle qualité des modèles de perception embarqués, sans mise à jour automatique

| Champ | Valeur |
|---|---|
| **ID** | RFC-0040 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-08-17 |
| **Auteur** | Camille Perraudeau (Fondateur), design co-construit avec l'agent GSIE (brainstorming) |
| **Impact** | Registre de modèles (RFC-0015, étendu), futurs modèles de perception mobiles (GeoSylva, Artemis), Evidence Engine (consommateur des corrections humaines), UI de validation (pattern Pl@ntNet) |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science sourcée), GSIE-CON-005 (traçabilité) |
| **RFC liées** | RFC-0015 (registre de modèles — cette RFC en est une extension, pas un remplacement), RFC-0020 (pattern `human_validator`, pattern `heuristique_non_sourcee`, réutilisés ici), RFC-0014 (garde-fou anti-invention, base d'ADR-009) |
| **ADR liés** | ADR-009 (garde-fou transverse anti-invention) — interdiction citée et étendue explicitement à l'apprentissage fédéré |
| **Origine** | Discussion du 2026-08-17 sur l'amélioration de la chaîne de raisonnement GSIE, à partir de cinq propositions externes ("vibe coding" versées en conversation par le Fondateur, non conservées comme document séparé) |
| **Décision liée** | Aucune — RFC en Draft, aucune implémentation autorisée |

---

## 1. Objet

Établir un mécanisme de contrôle qualité pour les futurs modèles de
perception embarqués (classifieurs de défauts, maladies, essences,
imagerie drone) — **sans jamais permettre la mise à jour automatique
de leurs poids**, conformément à ADR-009.

Deux volets, de maturité très différente :

1. **Monitoring passif** — exploiter les corrections humaines déjà
   produites par le pattern `SUGGESTION_IA → VALIDEE_UTILISATEUR`
   comme signal de dérive. Aucun nouveau modèle serveur requis.
2. **Rejeu serveur** (shadow comparison) — comparer un modèle léger
   embarqué à un modèle lourd serveur équivalent. Mécanisme posé
   maintenant, mais **structurellement inactif** tant qu'aucun modèle
   lourd qualifié n'existe pour la même tâche.

## 2. Ce que ce RFC ne couvre pas

- Le choix ou l'entraînement d'un modèle de perception concret
  (défauts, maladies, essences) — ce RFC pose le mécanisme de
  surveillance, pas les modèles eux-mêmes. Voir
  `GSIE/RESEARCH/REGISTRE_APPS_MOBILES.md` (OPP-031, OPP-018) et
  `GSIE/RESEARCH/REGISTRE_APPS_CLIENTES.md` (OPP-021) pour l'état des
  candidats — tous encore SURVEILLER/BENCHMARKER, bloqués par
  l'absence de corpus annoté.
- Toute forme de mise à jour automatique de poids, de retraining
  déclenché automatiquement, ou de redistribution de modèle sans
  passer par le cycle de vie RFC-0015 (Experimental → Qualified →
  Approved) avec `human_validator` non nul — **interdiction
  permanente, non négociable** (ADR-009).
- L'orchestration de la chaîne de raisonnement (Reasoning →
  Diagnostic → Recommendation → Validation) — hors périmètre. Cette
  chaîne reste déterministe (`ENGINE_COMMUNICATION_PROTOCOL.md` §2.2)
  et n'est pas concernée : ce mécanisme surveille des classifieurs de
  perception, jamais une décision sylvicole.
- Le taux d'échantillonnage exact des rejeux — posé comme paramètre
  opérationnel réglable (§4.4), jamais comme constante scientifique.

## 3. Contexte et motivation

Une discussion sur l'amélioration de la chaîne de raisonnement GSIE
(2026-08-17) a examiné cinq propositions externes, dont une
architecture « teacher-student + shadow reasoning + apprentissage
fédéré » censée synchroniser des modèles mobiles légers avec des
modèles serveur lourds.

L'examen, confronté au code et aux RFC existants, a montré que :

- **La chaîne de décision n'a pas ce besoin.** RFC-0020 y répond déjà
  par un barème déterministe partagé serveur/mobile — même calcul des
  deux côtés, aucune divergence possible parce que ce n'est pas un
  modèle statistique.
- **Les tâches de perception ont, elles, un besoin réel et déjà
  documenté.** Des modèles mobiles légers y sont légitimes, sur le
  pattern déjà accepté de Pl@ntNet
  (`SUGGESTION_IA → VALIDEE_UTILISATEUR`,
  `VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md` §1.3).
- **L'apprentissage fédéré tel que proposé est explicitement interdit
  par ADR-009** : *« toute promotion automatique d'un pattern
  statistique détecté (Learning Engine) en connaissance validée, sans
  repasser par l'Evidence Engine »*.

Ce RFC formalise ce qui reste légitime de la proposition — la
surveillance de dérive — sous une forme qui respecte cette
interdiction plutôt que de la contourner.

## 4. Conception

### 4.1 Volet 1 — Monitoring passif (sans nouveau modèle serveur)

Chaque confirmation ou correction humaine d'une suggestion de modèle
de perception (pattern Pl@ntNet) est déjà une donnée réelle, tracée
par l'Evidence Engine. Ce volet n'ajoute aucun mécanisme nouveau : il
agrège ce qui existe déjà, par `model_id`/version, en taux de
confirmation/correction, par tranche de confiance, par région. Le
rapport est de **lecture seule** ; il informe une décision humaine de
requalification, il ne la déclenche jamais lui-même.

### 4.2 Volet 2 — Rejeu serveur, structurellement conditionné

Deux nouveaux types de resource (registre GSIE, pattern
`@register_type` déjà en place) :

**`PerceptionReplayJob`** :
- `subject_observation_id` — l'observation mobile source (photo +
  classification légère)
- `light_model_version_id`, `heavy_model_version_id` — références au
  registre RFC-0015
- `status` — `pending` / `completed` / `failed`
- `triggered_at`, `executed_at` — le job ne s'exécute qu'au retour
  réseau, jamais bloquant côté mobile (offline-first, RFC-0003)

**`PerceptionDeltaReport`** :
- `replay_job_id`
- `light_model_prediction`, `heavy_model_prediction` — étiquette et
  confiance, chacune avec son `SourceReference`
- `agreement` — booléen, **comparaison déterministe** (même étiquette
  en tête) ; jamais un jugement de LLM (ADR-009 : « toute sortie de
  LLM non citée » interdite comme donnée décisive)
- `seuil_depasse` — booléen, calculé sur une fenêtre glissante de
  rapports pour une version de modèle donnée
- `revue_humaine_statut` — `en_attente` / `traitee`
- `revue_humaine_decision` — `modele_leger_confirme` /
  `requalification_necessaire` / `non_concluant`, `reviewer_id`

### 4.3 La précondition structurelle

`PerceptionReplayJob` ne peut être créé que si un `ModelVersionModel`
de statut `Qualified` ou `Approved` existe dans le registre RFC-0015
pour le même `ApplicabilityDomain` que le modèle léger. Ce n'est pas
une règle procédurale — c'est une **contrainte d'intégrité
vérifiable** : sans modèle lourd qualifié, la création du job échoue
avec une erreur nommée (`AUCUN_MODELE_LOURD_QUALIFIE`), cohérent avec
la discipline « aucun silence » déjà appliquée dans l'hydratation de
l'orchestration.

Aujourd'hui, cette précondition n'est remplie pour aucune tâche de
perception (voir §2) — **le volet 2 est donc posé mais inactif dès
l'adoption**, jusqu'à ce qu'un premier modèle serveur qualifié existe
pour une tâche donnée.

### 4.4 Taux d'échantillonnage — paramètre, pas constante

Le rejeu ne porte pas sur 100 % des observations synchronisées (coût
serveur). Le taux est un paramètre de configuration réglé
empiriquement après un premier volume réel de données, explicitement
marqué `heuristique_operationnelle_non_scientifique` dans sa
documentation — même discipline que le barème
`heuristique_non_sourcee` de RFC-0020 §5.2. Aucune valeur n'est
proposée ici comme scientifiquement justifiée.

### 4.5 Ce que le désaccord déclenche — et sa limite absolue

Au-delà du seuil (fenêtre glissante, paramètre réglable), la version
du modèle léger est ajoutée à une file de revue humaine, exposée à
travers le même mécanisme d'UI que les suggestions Pl@ntNet (statut à
traiter, jamais silencieux). Le réviseur humain décide ; si
`requalification_necessaire`, la version suit le cycle RFC-0015
standard (nouveau `ValidationRun`, nouvelle version, `human_validator`
non nul avant tout passage à `accepted`/`Approved`).

**Aucun chemin de ce mécanisme ne modifie un poids, ne déclenche un
entraînement, ni ne change un statut sans validation humaine
explicite.** C'est la limite absolue de ce RFC, non négociable
(ADR-009).

## 5. Plan par tranches (sur le modèle RFC-0016/RFC-0018/RFC-0020)

- **Tranche 1** — schéma seul (`PerceptionReplayJob`,
  `PerceptionDeltaReport`), aucun calcul réel, tests de validation des
  champs obligatoires et de la précondition §4.3.
- **Tranche 2** — volet 1 (monitoring passif) : agrégation des
  confirmations/corrections déjà tracées par l'Evidence Engine. Ne
  dépend d'aucun modèle serveur lourd — activable dès qu'un premier
  modèle de perception mobile est en production.
- **Tranche 3** — volet 2 (rejeu serveur) : job réel, gated par §4.3.
  Reste inactif tant qu'aucun modèle lourd qualifié n'existe pour la
  tâche concernée.
- **Tranche 4** — file de revue humaine intégrée à l'UI, sur le
  pattern Pl@ntNet déjà défini.

## 6. Alternatives considérées

### 6.1 Apprentissage fédéré (proposition externe d'origine)

**Rejetée** — contredit explicitement ADR-009 (interdiction de
promotion automatique d'un pattern statistique en connaissance
validée sans passer par l'Evidence Engine). Aucune reformulation ne
rend cette approche conforme sans supprimer précisément ce qui la
définit : la redistribution automatique de poids.

### 6.2 Teacher-Student pour la chaîne de décision

**Rejetée** — RFC-0020 répond déjà à ce besoin par un barème
déterministe partagé serveur/mobile, sans modèle divergent. Introduire
un modèle statistique dans Reasoning/Diagnostic/Recommendation
violerait ADR-009 (absence de `SourceReference` traçable pour une
sortie de classification) et CON-001 (la boîte noire déciderait à la
place du forestier).

### 6.3 Construire le rejeu serveur sans précondition structurelle

**Rejetée** — une règle « ne pas activer avant qu'un modèle lourd
existe » non vérifiée mécaniquement est une discipline qu'un futur
contributeur peut oublier d'appliquer. La précondition en contrainte
d'intégrité (§4.3) rend l'erreur impossible plutôt que déconseillée.

## 7. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| La file de revue humaine grossit plus vite que la capacité de revue | Signaux de dérive jamais traités, valeur du mécanisme nulle | Taux d'échantillonnage réglable à la baisse (§4.4) ; priorisation par ampleur du désaccord |
| Le volet 2 reste inactif indéfiniment faute de modèle lourd serveur | Investissement en schéma sans usage réel | Les Tranches 1-2 (schéma + monitoring passif) livrent de la valeur indépendamment de la Tranche 3 |
| Confusion entre « désaccord signalé » et « modèle faux » | Requalification injustifiée d'un modèle correct | La décision reste humaine (§4.5) ; le rapport documente les deux prédictions, jamais un verdict |

## 8. Décision requise

**Décision** : Valider cette RFC et autoriser l'implémentation de la
Tranche 1 (schéma) et de la Tranche 2 (monitoring passif, sans
dépendance à un modèle lourd). Les Tranches 3-4 restent conditionnées
à l'existence d'un premier modèle de perception qualifié — décision
séparée le moment venu, instruite via le cadre posé ici.

**Décideur** : Camille Perraudeau (Fondateur)

## 9. Références

- `02_RFC/RFC-0015-environmental-model-fabric.md` — registre de
  modèles, cycle de vie, étendu ici aux modèles de perception
- `02_RFC/RFC-0020-carte-ignorance-reasoning-engine.md` — précédent du
  barème déterministe partagé et du pattern `heuristique_non_sourcee`
- `02_RFC/RFC-0014-gouvernance-scientifique-anti-invention.md` — base
  d'ADR-009
- `GSIE/ARCHITECTURE/ADR-009-garde-fou-anti-invention.md` —
  interdiction citée et étendue ici à l'apprentissage fédéré
- `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md`
  §1.3 — pattern `SUGGESTION_IA → VALIDEE_UTILISATEUR`
- `GSIE/RESEARCH/REGISTRE_APPS_MOBILES.md` (OPP-031, OPP-018),
  `GSIE/RESEARCH/REGISTRE_APPS_CLIENTES.md` (OPP-021) — état des
  modèles de perception candidats
- `00_CONSTITUTION/GSIE-CON-001.md` — l'IA assiste, ne décide jamais
