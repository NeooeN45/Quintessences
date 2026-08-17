# RFC-0041 — Contrat de façade GeoSylva et identité stationnelle GSIE

| Champ | Valeur |
|---|---|
| **Identifiant** | RFC-0041 |
| **Statut** | Draft |
| **Phase** | 4 — Implémentation |
| **Auteur** | Camille Perraudeau, avec contre-analyse Devin CLI |
| **Date** | 2026-08-17 |
| **Motivation** | Réconcilier RFC-0033 avec l'orchestration actuellement implémentée et rendre possible un appel GeoSylva sans invention de règles, de qualifications ou d'état global |
| **Décision liée** | DEC-000073 — proposée |
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

## 3. Façade cliente proposée

### 3.1 Endpoint

Ajouter, sans retirer la route interne existante :

```text
POST /api/v1/orchestration/analyse-geosylva
```

La route interne `POST /api/v1/orchestration/analyse` reste disponible pour
les appels techniques et les tests de la chaîne complète. La façade traduit
l'intention GeoSylva vers le contrat interne dans une transaction contrôlée.

### 3.2 Requête d'intention

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

Le corps ne contient ni auteur, ni règle, ni qualification, ni `etat_global`, ni
`contexte`. Le compte est dérivé du JWT. `parcelle_client_id` est uniquement
une corrélation mobile : il ne peut jamais devenir une identité GSIE ou une
`SourceReference`. `station_id` doit être un UUID GSIE déjà résolu par le
mécanisme de liaison de la section 4.

Les `niveaux_preuve_declares` sont bornés aux blocs déclarables de DEC-000072.
Ils déclarent le niveau manquant d'une donnée hydratée ; ils ne qualifient ni
une règle ni une conclusion et ne peuvent pas être dérivés d'une confiance.

La façade n'accepte pas de `contexte` client. Cette restriction est volontaire :
le schéma interne accepte un contexte pour les appels techniques historiques,
mais la façade GeoSylva doit toujours passer par l'hydratation et la vérification
serveur de l'identité et de la provenance.

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

Dans l'état actuel du code, la sélection serveur des règles/qualifications et
la fourniture d'un état global stationnel ne sont pas encore implémentées. La
façade ne peut donc pas être activée avant cette tranche préparatoire. Tant que
la précondition n'est pas satisfaite, elle refuse avec des codes explicites :

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
son niveau de preuve. Le contrat `station_intake.v0.1` actuel ne porte pas
encore cet état : tant qu'une extension versionnée et validée n'existe pas,
`ETAT_GLOBAL_NON_SOURCE` est le comportement obligatoire.

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

### 3.4 Compatibilité RFC-0033

La façade porte l'enveloppe commune adoptée par RFC-0033, avec un nom de version
non ambigu :

- `requete_id` ;
- `session_id` ;
- `moteur_cible` égal à `orchestration` ;
- `contract_version`, par exemple `analyse-geosylva.v1` ;
- `payload` d'intention ;
- auteur dérivé du JWT côté serveur.

`version` au sens optimistic locking de RFC-0033 n'est pas ajouté à une
intention d'analyse : aucune ressource mutable locale n'est verrouillée par
cette demande. Ce mécanisme reste celui de DEC-000048 pour la synchronisation
des parcelles.

La façade appelle `OrchestrationEngine` directement dans le même processus,
avec la session et la transaction prévues. Elle ne réalise jamais un second
appel HTTP vers `/orchestration/analyse`.

La façade dispose d'un scope RBAC consommateur dédié, distinct de la porte
technique `EngineWriteUser`, et d'une limite explicite de 10 analyses par minute
et par compte pour le pilote. Toute évolution de cette limite doit être mesurée
et documentée.

La sortie conserve le format métier `AnalyseComplete` actuel dans `payload` et
expose également :

- `resultat_id` correspondant à `analyse_id` ;
- `requete_origine` ;
- `contract_version` et version de l'orchestration ;
- `RapportHydratation` et `RapportPreparation` ;
- sources, niveaux de preuve et chaîne d'inférence.

### 3.5 Erratum documentaire RFC-0033

RFC-0033 §2.4–2.5 décrit des routes moteurs et d'orchestration qui ne sont pas
les routes actuellement montées. RFC-0041 ne supprime pas la RFC adoptée : elle
formalise que la façade `analyse-geosylva` et la route interne actuelle sont la
réconciliation opérationnelle de ce contrat, tandis qu'un futur SDK ne doit
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

### 4.3 Opération serveur retenue

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

- contrat `analyse-geosylva.v1` ;
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

Avant passage en `Validated` :

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

## 10. Autorisation demandée

Cette RFC demande l'autorisation de concevoir et implémenter la façade et le
lien d'identité uniquement après validation de DEC-000073. La route interne,
le cœur local, la quarantaine et les règles de gouvernance existantes restent
inchangés jusque-là.
