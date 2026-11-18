# RFC-0041 — Contrat de façade GeoSylva et identité stationnelle GSIE

| Champ | Valeur |
|---|---|
| **Identifiant** | RFC-0041 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation |
| **Auteur** | Camille Perraudeau, avec contre-analyse Devin CLI |
| **Date** | 2026-08-17 |
| **Motivation** | Réconcilier RFC-0033 avec l'orchestration actuellement implémentée et rendre possible un appel GeoSylva sans invention de règles, de qualifications ou d'état global |
| **Décision liée** | DEC-000093 — principes et route validés avec mise à jour ; complète DEC-000073 |
| **Dernière mise à jour** | 2026-11-15 — adaptation documentaire, statut Draft conservé |
| **RFC liées** | RFC-0015, RFC-0020, RFC-0033, RFC-0040 |
| **Décisions liées** | DEC-000048, DEC-000049, DEC-000071, DEC-000072 |
| **Lois fondatrices** | GSIE-CON-000, GSIE-CON-001, GSIE-CON-002, GSIE-CON-004, GSIE-CON-005, GSIE-CON-007 |

---

## 1. Problème

RFC-0033 et DEC-000049 ont adopté un contrat d'interface GeoSylva fondé sur une
enveloppe commune, un SDK Kotlin, un cache SQLCipher et une file WorkManager.
L'API GSIE actuelle expose toutefois une route d'orchestration interne dont le
contrat exige directement `regles`, `qualifications` et `etat_global`.

GeoSylva connaît une intention de travail, des données locales et, après
synchronisation, une référence de parcelle. Il ne possède pas nécessairement les
règles GSIE qualifiées ni un état global sourcé. Lui demander de fabriquer ces
champs créerait une requête valide en apparence mais scientifiquement
injustifiable.

Un second écart concerne l'identité : le `parcelleId` local de GeoSylva n'est
pas automatiquement le UUID d'une `Place` GSIE. Or DEC-000072 exige que
`station_id` résolve une `Place` ou une soumission `FieldIntake` acceptée.

La présente RFC ne remplace pas RFC-0033 et ne modifie pas le contrat interne
des moteurs. Elle ajoute une façade cliente et un lien d'identité explicite.

## 2. Principes retenus

1. **Le cœur local reste autonome.** Une panne réseau place la demande en
   attente d'amplification ; elle ne bloque ni la saisie ni les calculs locaux.
2. **GeoSylva envoie une intention, pas une règle inventée.** Les règles,
   qualifications et l'état global ne peuvent venir que d'une capacité GSIE
   porteuse, sourceée et versionnée. Cette capacité est une précondition de la
   façade ; son absence provoque un refus nommé, jamais une valeur de repli.
3. **Aucun défaut silencieux.** L'absence d'une règle, d'une qualification,
   d'un état global ou d'une provenance produit un blocage explicite.
4. **`station_id` est un identifiant GSIE.** Un identifiant local est relié à
   une ressource GSIE par un lien explicite, révocable et contrôlé par compte,
   jamais par convention de chaîne.
5. **Le même moteur déterministe peut être local ou distant.** Le basculement
   ne change ni le modèle scientifique ni la nature de la décision
   (RFC-0003 §6bis, RFC-0020).
6. **Les modèles de perception restent hors de la chaîne de décision.**
   RFC-0040 ne permet ni teacher-student, ni apprentissage fédéré, ni mise à
   jour automatique des poids sur Reasoning, Diagnostic ou Recommendation.
7. **La préparation est figée.** Les règles, qualifications, contexte et état
   global retenus sont persistés avec leurs identifiants, versions et sources ;
   un rejeu ne re-sélectionne pas silencieusement une autre connaissance.

## 3. Façade cliente asynchrone retenue

### 3.1 Endpoint et suivi

Par décision du Fondateur du 15 novembre 2026, enregistrée dans DEC-000093,
la façade cliente retenue est le parcours asynchrone existant :

```text
POST /api/v1/geosylva/analyses
GET  /api/v1/geosylva/analyses/{id}
GET  /api/v1/geosylva/analyses/{id}/result
```

Le POST accepte un job avec HTTP 202 ; le code existant fournit `Location`,
`Retry-After`, `analysis_id`, `status_url` et `result_url`. Le suivi expose
l'état du job ; le résultat fournit la projection scientifique lorsqu'elle
est disponible. Ces éléments de transport sont constatés dans
`GSIE/API/src/gsie_api/geosylva/router.py` et `schemas.py` au snapshot
`9e6864b353c8c03d15c067dffd2b358f7a57d94f`.

Une acceptation HTTP 202 n'est ni une validation scientifique ni une preuve
que les données requises existent. Les refus de préparation restent
obligatoires et doivent être identifiables dans le suivi asynchrone. La
correspondance des codes publics reste un écart documenté, pas une garantie
acquise par l'existence de la route.

Le chemin initial du 17 août est conservé en section 11 comme historique ;
il n'est plus la cible cliente à construire. La route interne
`POST /api/v1/orchestration/analyse` conserve son rôle technique. La façade
appelle la chaîne interne en processus, sans second appel HTTP.

### 3.2 Requête d'intention et contrat existant

Le principe reste celui de DEC-000073 : intention mobile, auteur dérivé du
JWT, `station_id` GSIE relié explicitement ; aucune règle, qualification,
valeur d'état global ou contexte scientifique fabriqué par le client.

Le DTO existant est `GeoSylvaAnalysisRequest` dans
`GSIE/API/src/gsie_api/geosylva/schemas.py`. L'alignement du chemin n'adopte
pas implicitement tous ses champs. Le modèle logique initial, reproduit en
section 11, ne doit pas être envoyé tel quel à l'API asynchrone actuelle.

| Notion | Représentation existante constatée | Limite de l'alignement |
|---|---|---|
| Version de requête | `schema_version = geosylva.analysis.request.v1` | Constat du DTO existant ; ne remplace pas silencieusement toute l'enveloppe RFC-0033. |
| Identité de l'intention | `request_id`, égal à l'en-tête `Idempotency-Key` | Correspond au rôle logique de `requete_id` ; empreinte distincte de celle du moteur interne. |
| Identité stationnelle | `station_id` UUID | Le typage UUID ne prouve ni le lien actif ni le contrôle du compte. |
| Question et objectif | `question`, `objective` | Intentions ; ne constituent pas une connaissance scientifique. |
| Niveaux déclarés | `evidence_levels` | Restent bornés aux déclarations admises par DEC-000072 ; aucune qualification de règle ou conclusion. |
| Déclarations supplémentaires | `geometry`, `species_taxref_ids`, obligatoires | Extension du contrat initial à arbitrer ; ni faits acceptés ni contexte scientifique autoritaire. |

Les lignes 38 à 58 de `geosylva/service.py` préparent depuis la station GSIE
et n'injectent pas `geometry` ni `species_taxref_ids` dans le contexte du
moteur. Leur statut d'emprise ou d'espèces demandées doit être explicité avant
homologation du contrat. Leur existence dans une requête n'en fait pas une
observation sourcée, une `SourceReference` ou un lien stationnel valide.

La correspondance des autres champs d'enveloppe, notamment `session_id`, reste
à qualifier : aucun champ absent ne doit être ajouté ou remplacé tacitement.
Cette mise à jour ne définit donc pas un nouveau corps JSON exécutable et ne
corrige aucun DTO. Voir les écarts E01 et E02 du
[rapport de revue](../23_QUALITY_MANAGEMENT/AUDITS/AUDIT_DEC_000073_2026-11-15.md).

La façade n'accepte pas un contexte scientifique client à la place de
l'hydratation serveur. Le schéma interne peut conserver son rôle pour les
appels techniques historiques ; la façade GeoSylva reste soumise au contrôle
de l'identité stationnelle, du compte et de la provenance.

### 3.3 Préparation côté serveur

La façade exécute une étape de préparation explicable avant la chaîne. Cette
étape est une capacité serveur séparée, transactionnelle et sans état mutable
hors de la session :

1. vérifier que `station_id` appartient au compte JWT via `GsieResourceLink` ;
2. résoudre `station_id` selon DEC-000072 ;
3. hydrater le contexte et produire le `RapportHydratation` ;
4. charger les règles applicables depuis une source Knowledge Engine
   implémentée, acceptée et versionnée ;
5. conserver uniquement les règles dans leur domaine de validité et dont la
   `SourceReference` est résolvable ;
6. charger les qualifications validées associées à chaque règle ;
7. charger un état global porté par une source acceptée et explicitement liée à
   la station ;
8. refuser si l'une de ces capacités ou preuves manque ;
9. exécuter Reasoning → Diagnostic → Recommendation → Validation.

Le constat d'absence de préparation du 17 août n'est plus l'état du code
examiné : `engines/orchestration/preparation.py` contient désormais
`StationPreparationService`, la sélection des règles/qualifications et le
chargement d'un état accepté. Cette présence ne prouve ni le lien stationnel,
ni les provenances en base, ni la conformité des reprises ou des réponses.
Les portes techniques restent ouvertes. Si une précondition manque, la
façade doit refuser avec des codes explicites, y compris après acceptation
asynchrone du job :

```text
AUCUNE_REGLE_QUALIFIEE
QUALIFICATION_REGLE_MANQUANTE
ETAT_GLOBAL_NON_SOURCE
PROVENANCE_PREPARATION_INCOMPLETE
```

Un défaut d'infrastructure distinct provoque une erreur de disponibilité ; il
ne doit jamais être converti en blocage scientifique ni en valeur par défaut.

L'état global ne peut provenir que d'une ressource ou d'un `FieldIntake`
`accepted` dont le schéma porte explicitement cet état, sa date, sa source et
son niveau de preuve. Le code examiné déclare `EtatGlobalPayload` avec
`schema_version = global_state.v0.1` et vérifie un état dans les soumissions
acceptées. Un modèle déclaré ne prouve pas qu'une donnée acceptée et sourcée
existe pour la station demandée : si elle manque ou n'est pas admissible,
`ETAT_GLOBAL_NON_SOURCE` reste le comportement obligatoire.

Le `RapportPreparation` est immuable et contient au minimum :

- identifiants, versions et empreintes des règles sélectionnées ;
- qualifications utilisées et correspondance règle → qualification ;
- état global, source, date et niveau de preuve ;
- blocs construits et non constructibles ;
- niveaux de preuve utilisés ;
- identifiant/empreinte du contexte effectivement consommé ;
- causes de blocage éventuelles.

Aucune valeur par défaut `sain`, aucune qualification automatique et aucune
conversion confiance → niveau de preuve ne sont autorisées.

### 3.4 Compatibilité RFC-0033 et restitution

RFC-0033 reste la référence d'enveloppe commune. Le BFF asynchrone distingue
l'identité de la demande (`request_id`), celle du job (`analysis_id`) et le
résultat scientifique. Le relevé des représentations existantes en section
3.2 ne vaut pas homologation de l'enveloppe complète.

`version` au sens optimistic locking de RFC-0033 n'est pas ajouté à une
intention d'analyse : aucune ressource mutable locale n'est verrouillée par
cette demande. Ce mécanisme reste celui de DEC-000048 pour la synchronisation
des parcelles.

La façade appelle `OrchestrationEngine` directement dans le processus serveur,
avec la session et la transaction prévues. Elle ne réalise pas de second appel
HTTP vers `/orchestration/analyse`. Les droits consommateur dédiés et la limite
pilote de 10 analyses par minute **et par compte** restent exigés ; le code de
limitation réseau ne suffit pas à démontrer cette dernière condition.

Le résultat doit conserver les sources, niveaux de preuve, chaîne d'inférence,
`RapportHydratation` et `RapportPreparation` demandés par DEC-000073. La
projection existante `ScientificAnalysisResult` expose des observations,
versions et empreintes ; sa restitution partielle des rapports est signalée
en E05 du rapport de revue. Aucune nouvelle forme de réponse n'est inventée
ici et aucune conservation complète n'est déclarée livrée sans preuve.

### 3.5 Erratum documentaire RFC-0033

RFC-0033 §2.4–2.5 décrit des routes moteurs et d'orchestration qui ne sont pas
les routes actuellement montées. RFC-0041 ne supprime pas la RFC adoptée : elle
retient maintenant la façade asynchrone décrite en section 3.1 et conserve la
route interne. L'ancienne proposition est archivée en section 11. La
réconciliation des DTO et des preuves reste à qualifier ; un SDK ne doit
jamais coder contre un endpoint non vérifié dans OpenAPI.

## 4. Identité parcelle locale → ressource GSIE

### 4.1 Principe

La synchronisation de parcelle conserve le `client_id` local et doit retourner
ou permettre de récupérer un identifiant GSIE stable lorsqu'une ressource
stationnelle est créée ou liée.

Le contrat cible est :

```text
parcelleId local → gsie_resource_id UUID → Place / station_id
```

Le client ne déduit jamais le UUID par hachage ou concaténation.

### 4.2 Stockage mobile

La première implémentation utilise une table de lien dédiée, isolée par compte
et révocable :

```text
GsieResourceLink
- account_id
- local_entity_type
- local_entity_id
- gsie_resource_id
- gsie_resource_type
- state: active | revoked
- server_version
- linked_at
- revoked_at nullable
```

Cette table évite d'ajouter immédiatement un UUID et une provenance incomplète
à toutes les entités historiques GeoSylva. L'extension des entités reste une
tranche ultérieure si le modèle de données le justifie.

### 4.3 Opération serveur retenue — à construire

**État au 15 novembre 2026 : endpoint non retrouvé dans le snapshot serveur
examiné, encore à construire.** Le présent texte décrit la cible et non un
service livré ou une migration exécutée.

Le choix est fixé sur un endpoint dédié, sans modifier la sémantique du PUT de
synchronisation parcellaire :

```text
POST /api/v1/sync/geosylva/parcelles/{client_id}/station-link
```

Le corps porte un `operation_id` UUID stable et une version de contrat. Le
serveur vérifie que la parcelle appartient au compte JWT, que son instantané
est disponible et que la géométrie/les métadonnées nécessaires à la `Place`
sont conformes. Il crée ou retourne le même lien de façon idempotente ; il ne
crée jamais deux `Place` pour le même triplet compte/type/identifiant local.

La contrainte serveur est unique sur :

```text
(account_id, local_entity_type, local_entity_id)
```

Le serveur retourne `gsie_resource_id`, `gsie_resource_type`, l'état du lien et
la version de l'instantané utilisé. Une tombstone ou une suppression de la
`Place` révoque le lien ; une analyse utilisant un lien révoqué est refusée.

La décision préserve DEC-000048 : activation explicite de la synchronisation,
propriétaire dérivé du JWT, version serveur et HTTP 409 sans écrasement
automatique. L'accès à un `station_id` est toujours contrôlé par appartenance
au compte, même si l'UUID est difficile à deviner.

## 5. File mobile et idempotence

Les noms ci-dessous décrivent la cible logique de file ; ils ne prouvent pas
sa présence dans un APK. La clé d'intention logique `requete_id` correspond
au rôle de `request_id` dans le BFF asynchrone existant.

La file GeoSylva reprend le pattern de DEC-000048 et de RFC-0033 :

```text
OrchestrationAnalyseQueue
- account_id
- requete_id unique par compte
- station_gsie_id
- request_json
- response_json nullable
- state
- retry_count
- queued_at
- last_attempt_at
- next_attempt_at
- completed_at nullable
- last_error_code nullable
- last_error_message nullable et borné
```

États :

```text
QUEUED | SENDING | SUCCEEDED | RETRYABLE_ERROR |
PERMANENT_ERROR | BLOCKED | CONFLICT
```

Règles :

- l'empreinte de l'intention reçue par la façade est calculée avant toute
  préparation serveur ;
- cette empreinte d'intention est stockée séparément de l'empreinte interne de
  `AnalyseRequest` utilisée par DEC-000071 ;
- même `requete_id` et même intention : retour de la preuve liée, sans
  re-sélection dynamique des règles ;
- même `requete_id` et intention différente : `CONFLICT`, pas de boucle ;
- le `RapportPreparation` fige les règles, qualifications, état global et
  contexte consommés, avec leurs versions et empreintes ;
- HTTP 401 : renouvellement JWT une fois ;
- réseau, 408, 425, 429, 5xx : retry borné ;
- 400, 404, 409 : aucune nouvelle tentative automatique ;
- la réponse complète est conservée dans SQLCipher ;
- aucun jeton n'est écrit dans la file.

La séparation des deux empreintes est obligatoire : l'évolution ultérieure du
Knowledge Engine ne doit pas transformer un rejeu réseau en faux conflit, ni
permettre de rejouer silencieusement une préparation différente.

## 6. Tranches obligatoires avant activation

DEC-000093 fixe le lancement aux métiers technicien forestier et conducteur
de travaux forestiers. Tout chantier hors GeoSylva est gelé jusqu'à sa
sortie. Les dépendances GSIE strictement nécessaires à ces deux parcours ne
constituent pas une autorisation de reprendre d'autres chantiers.

Les tranches ci-dessous restent des portes à qualifier. Leur présence dans
la RFC ou dans le code ne signifie pas qu'elles sont closes.

### Tranche 0 — Préconditions serveur

- spécifier la ressource de règles applicables et son domaine de validité ;
- spécifier les qualifications validées liées aux règles ;
- versionner un schéma stationnel portant l'état global sourcé, ou confirmer
  son absence durable ;
- créer les erreurs `AUCUNE_REGLE_QUALIFIEE`,
  `QUALIFICATION_REGLE_MANQUANTE` et `ETAT_GLOBAL_NON_SOURCE` ;
- persister `RapportPreparation` et son empreinte ;
- ajouter les tests PostgreSQL et le harnais de mutation des gardes.

Tant que cette tranche n'est pas livrée, l'analyse façade reste bloquée de
manière explicite. Elle ne doit pas donner un faux succès.

### Tranche 1 — Identité stationnelle

- endpoint `station-link` dédié et idempotent ;
- contrôle d'appartenance au compte ;
- table de liens avec révocation ;
- tests de création, rejeu, conflit, suppression et accès inter-comptes.

### Tranche 2 — Façade et file mobile

- réconciliation de l'intention avec le DTO existant `geosylva.analysis.request.v1`, sans homologation implicite des champs supplémentaires ;
- appel en processus vers l'orchestrateur interne ;
- scope RBAC consommateur ;
- file Room, cache SQLCipher et Worker ;
- idempotence des intentions et conservation des preuves.

### Tranche 3 — Activation GeoSylva

- DTO Kotlin ;
- test contractuel MockWebServer ;
- test sur GSIE TEST avec Place et données acceptées ;
- écran de résultat explicitement non décisionnel ;
- aucune activation de production avant les preuves documentées.

## 7. Ce qui n'est pas inclus

- aucune modification de modèle de perception ;
- aucune intégration d'un LLM dans le raisonnement ;
- aucune synchronisation complète des tiges, photos ou diagnostics dans cette
  tranche ;
- aucun mesh LoRa, Edge Node ou bundle `mission_zone` ;
- aucun appel fournisseur externe pendant l'hydratation ;
- aucun état global par défaut ;
- aucune modification des documents Locked ;
- aucun déploiement VPS ou production.

## 8. Alternatives rejetées

### 8.1 Faire construire `regles` et `qualifications` par GeoSylva

Rejeté : GeoSylva ne possède pas toujours le Knowledge Engine, la qualification
scientifique ou le domaine de validité nécessaires.

### 8.2 Ajouter `sain` par défaut

Rejeté : l'absence d'état est une ignorance à rapporter, pas un état écologique.

### 8.3 Utiliser `parcelleId` comme `station_id`

Rejeté : les espaces d'identifiants sont distincts et cette convention rendrait
les preuves non résolvables.

### 8.4 Remplacer immédiatement RFC-0033

Rejeté : RFC-0033 est adoptée. La présente RFC ajoute une façade compatible et
ne supprime pas le contrat moteur existant.

### 8.5 Ajouter `account_id` à toutes les tables locales

Reporté : la file d'analyse doit être isolée par compte, mais une refonte de
toutes les tables métier dépasse cette tranche et n'est pas nécessaire pour
le premier test serveur.

## 9. Portes de validation

La validation des principes et du choix de façade par DEC-000093 ne clôt pas
ces portes et ne promeut pas la RFC entière en document validé. Son statut
reste Draft. Avant passage en `Validated` :

1. capacité serveur de préparation effectivement implémentée ou refus nommé
   `AUCUNE_REGLE_QUALIFIEE` vérifié ;
2. schéma versionné portant l'état global sourcé, ou refus
   `ETAT_GLOBAL_NON_SOURCE` vérifié ;
3. test contractuel de la façade et de l'enveloppe RFC-0033 ;
4. test de résolution `parcelleId → gsie_resource_id` avec contrôle du compte ;
5. test de révocation du lien et de refus d'un lien révoqué ;
6. test d'absence de règle ou d'état global sans valeur par défaut ;
7. tests d'hydratation et de quarantaine sur PostgreSQL réel ;
8. test d'idempotence de l'intention et de l'empreinte interne séparément ;
9. test de figement et de rejeu du `RapportPreparation` ;
10. test de migration Room de la version courante ;
11. tests Worker de retry, conflit et erreur permanente ;
12. test de conservation du rapport, des sources et de la chaîne d'inférence ;
13. Ruff, mypy, tests Android et tests d'intégration ;
14. relecture du run CI sur un snapshot Git stabilisé.

## 10. Décision acquise et suites distinctes

DEC-000093 enregistre la décision du Fondateur du 15 novembre 2026 :
DEC-000073 est validée avec mise à jour pour ses principes, la façade
asynchrone retenue et les deux métiers de lancement. DEC-000073 reste
inchangée comme trace historique ; la nouvelle décision la complète.

La présente mission ne réalise que cet enregistrement documentaire.
`station-link`, la réconciliation contractuelle et les preuves des écarts
restent des travaux distincts, sans activation, migration ou déploiement
implicites. Le cœur local, la route interne et les garde-fous de provenance
restent préservés.

## 11. Historique de la proposition

| Date | État et évolution |
|---|---|
| 2026-08-17 | Proposition initiale Draft, liée à DEC-000073 proposée : façade envisagée sous le chemin d'orchestration reproduit ci-dessous. |
| 2026-11-15 | DEC-000093 enregistre « validée avec mise à jour » : principes conservés, façade asynchrone existante retenue, station-link restant à construire et gel des chantiers hors GeoSylva. La RFC reste Draft. |

### 11.1 Chemin initial — historique, non cible cliente

La section 3.1 du 17 août proposait :

```text
POST /api/v1/orchestration/analyse-geosylva
```

Ce choix est remplacé par celui de la section 3.1 courante. Il n'est pas une
seconde façade à implémenter.

### 11.2 Modèle d'intention initial — historique, non payload actuel

La proposition du 17 août présentait le modèle suivant ; il ne correspond pas
au corps accepté tel quel par le DTO asynchrone existant :

```json
{
  "contract_version": "analyse-geosylva.v1",
  "requete_id": "uuid-v4",
  "session_id": "uuid-v4",
  "station_id": "uuid-gsie-place",
  "parcelle_client_id": "parcelle-locale-123",
  "question": "Quelles essences sont adaptées à cette station ?",
  "objectif_forestier": "production",
  "alternatives_demandees": true,
  "niveaux_preuve_declares": {
    "pedologie": "F",
    "peuplement": "F"
  }
}
```

Le texte initial complet est conservé dans [le snapshot de départ immuable](https://github.com/NeooeN45/Quintessences/blob/9e6864b353c8c03d15c067dffd2b358f7a57d94f/02_RFC/RFC-0041-contrat-facade-geosylva-identite-stationnelle.md),
blob Git `f194c48624a8a09b336de0490f47a3f9d8edd3fa`. La présente mise à jour ne
réécrit pas DEC-000073 et ne présente pas les préconditions historiques comme
des fonctions déjà livrées.
