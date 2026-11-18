# GEO-005 — Plan d’exécution V1 GeoSylva → GSIE et validation complète des comptes

| Champ | Valeur |
|---|---|
| **Identifiant** | GEO-005 |
| **Statut** | Draft d’exécution |
| **Version** | 1.1.0 |
| **Date** | 2026-09-07 |
| **Décision** | DEC-000074, DEC-000076, DEC-000077, DEC-000084 |
| **Périmètre** | GeoSylva Android 3.0 → 3.1, compte Quintessences, RGPD, Data Acquisition Fabric, verticale GeoSylva ↔ GSIE |
| **Appareil de recette** | Samsung S25 Ultra connecté par câble USB avec ADB |
| **Documents liés** | GEO-001, GEO-002, GEO-003, IDENTITE-001, RFC-0032, RFC-0041, DEC-000048, DEC-000073, DEC-000075 |

## 1. Objet et résultat attendu

Ce document est le fil d’exécution unique de la V1 fonctionnelle. Il fixe les
éléments à mettre en place, dans l’ordre, les dépendances, les preuves
attendues et les conditions de sortie. Il ne remplace ni la spécification
fonctionnelle GeoSylva 3, ni le contrat interne des moteurs GSIE.

La V1 n’est pas « un build qui s’installe ». Elle est atteinte quand le flux
suivant est démontré sur l’appareil réel :

```text
compte Quintessences
    → session sûre et restaurable
    → projet / forêt / parcelle / placette
    → observations et mesures terrain
    → calculs et synthèses forestières
    → martelage exploitable
    → données protégées, exportables et supprimables
    → acquisition qualifiée
    → verticale GeoSylva vers GSIE
    → résultat explicable et amélioration mesurée
```

La preuve doit être reproductible, attachée à un commit et séparée en preuves
de code, de données, de sécurité, de RGPD et d’appareil physique.

## 2. Règles de collaboration

### 2.1 Répartition avec Claude

Claude peut travailler sur l’interface de l’application GeoSylva : écrans,
navigation, états de chargement, erreurs, accessibilité, libellés et parcours
visuels. Il ne doit pas modifier le contrat d’identité, les migrations
Room, les repositories d’authentification ou l’API GSIE sans tranche dédiée et
coordination explicite.

Chaque livraison Claude doit fournir :

- le diff exact ;
- la liste des écrans et fichiers touchés ;
- les tests exécutés ;
- les captures ou une courte recette de navigation ;
- les comportements non traités.

### 2.2 Travail Codex par ADB

Codex prend en charge l’audit et la mise en œuvre des comptes, les contrats
API, la sécurité, la persistance de session, la purge locale et la recette
physique via ADB. Les tests par câble commencent par un appareil de test
configuré en mode développeur et ne récupèrent jamais les secrets privés de
l’application.

### 2.3 Interdiction des doublons

Avant d’ajouter une fonction, rechercher et documenter le point d’extension
existant :

| Besoin | Réutilisation prioritaire déjà présente |
|---|---|
| Session Android | `EncryptedIdentitySessionStore`, `IdentityRepositoryImpl`, `JwtSessionDecoder` |
| API identité | `identity_router.py`, `IdentityService`, `AccountLifecycleService` |
| Comptes serveur | `gsie_rgpd_identites` et les modèles `accounts.py` |
| Export RGPD | `AccountExportService` et `GET /api/v1/auth/me/export` |
| Consentements | `GET/POST /api/v1/auth/me/consents` et révocation versionnée |
| Purge locale | `DeleteAllUserDataUseCase` et les DAO `hardDeleteAll()` |
| Session de parcelles | `ParcelSyncDao`, `ParcelSyncActivationStore`, `ParcelSyncRepository` |
| Acquisition | connecteurs Forge existants et contrat `gsie_acquisition_handoff.v1` |
| Orchestration | préparation stationnelle existante, puis RFC-0041 / DEC-000073 après validation |

Une nouvelle classe qui recopie l’un de ces rôles est refusée sans justification
architecturale et test de non-régression.

## 3. État initial vérifié au 2026-08-26

| Élément | Fait vérifié | Limite à ne pas masquer |
|---|---|---|
| Version Android | `app/build.gradle.kts` annonce `versionName = "3.0.0"` et `versionCode = 11` | `AI_CONTEXT.md` et `MASTER_PLAN.md` contiennent encore des références historiques à 2.4.0 |
| Spécification GeoSylva | Le parcours Projet → Forêt → Parcelle → Placette → Martelage → Observations → Calculs et synthèses est décrit | La spécification ne constitue pas une preuve d’exécution sur S25 Ultra |
| Authentification API | Inscription locale, login local, Google nonce/login/link, profil, vérification e-mail, récupération, refresh et logout existent | Google exige encore sa configuration Google Cloud réelle ; les droits d’accès, l’export complet et l’effacement final doivent être recettés |
| Cycle compte API | Export allowlisté, consentements, changement d’e-mail, sessions, MFA, demande et worker de suppression différée existent dans le code | La migration et la finalisation automatique sur un compte synthétique restent à prouver |
| Session mobile | Les jetons sont confiés à un store chiffré dédié | Il faut prouver l’absence de fuite dans logs, sauvegardes, DataStore et fichiers temporaires |
| Poste de recette ADB | Platform-Tools 36.0.0 est installé ; le S25 Ultra est autorisé et listé `device` sur le profil Android principal ; GeoSylva 3.0.0 est installé et lancé | Le Dossier sécurisé Samsung (utilisateur 150) reste hors périmètre ; la preuve ne vaut pas encore validation de production |
| Effacement mobile | `DeleteAllUserDataUseCase` purge les entités forestières et les photos | Il faut vérifier l’isolation par compte : une purge globale n’est pas compatible avec plusieurs comptes sur un même appareil |
| Data Acquisition Fabric | Handoff Forge → Registry IFN v1, sink transactionnel et rejeu idempotent sont prouvés localement | Aucun téléchargement réel, déclencheur planifié, promotion ou production n’est validé |
| Verticale GeoSylva ↔ GSIE | Préparation serveur et hydratation stationnelle existent | La façade GeoSylva, le station-link et le client mobile restent soumis à RFC-0041 / DEC-000073 |

### 3.1 Preuves de recette déjà obtenues

Sur le compte synthétique de recette, la connexion locale et l’affichage du
profil sont validés sur le S25 Ultra par ADB. La déconnexion révoque la session
et, après relance de l’activité, GeoSylva revient au formulaire sans réinjecter
la session locale. L’API locale reliée par `adb reverse` valide également
l’export, la liste des sessions, la vérification d’adresse par code, la
récupération du mot de passe et la demande puis l’annulation d’une suppression
différée.

Les statuts observés sont : vérification e-mail `202` puis `200`, reset de
mot de passe `202` puis `200`, ancien mot de passe `401`, nouveau mot de passe
`200`, demande de suppression `202` et annulation `200`. La base conserve les
enregistrements attendus et revient à `active` avec une date de suppression
nulle après annulation.

Les consentements ont ensuite été testés avec deux versions du même document et
un consentement marketing synthétique : les acceptations répondent `201`, les
versions précédentes restent historisées et la révocation répond `200` en
marquant effectivement la ligne révoquée. Le contexte RLS du compte est
désormais injecté dans les trois routes de consentement.

Le 2026-08-29, la création de compte a été exposée dans GeoSylva par une route
native dédiée (`settings/account/register`) sur le S25 Ultra. Le bouton depuis
la connexion n'ouvre plus Chrome : l'écran Compose réutilise le `LoginViewModel`,
le `LoginMode.REGISTER`, le `IdentityRepository.register` et le stockage de
session existants. La preuve ADB montre le nom affiché facultatif, l'e-mail, le
mot de passe, sa confirmation, l'aide de robustesse et le retour à la connexion.
Un envoi vide est refusé localement.

Le même jour, le scénario API réel a validé la création avec une adresse
synthétique, les consentements `terms` et `privacy` acceptés explicitement puis
révoqués, l'export RGPD avec historique, la vérification e-mail par Mailpit,
l'annulation d'une suppression différée, la reconnexion sur le même compte et
l'isolation d'un compte B. Le correctif de contexte RLS et d'export est tracé
par DEC-000077. Cette preuve API n'est pas encore une recette Android de bout
en bout : le raccordement visuel des consentements à l'inscription native doit
encore être vérifié sur le S25.

Ces preuves ne ferment pas G2 : Google réel, restauration d’une sauvegarde
locale, suppression finale à échéance, purge locale complète et isolation de
deux comptes dans l’application restent à exécuter. Le worker serveur de finalisation est désormais
implémenté par DEC-000075 et la migration 0055 est appliquée dans la base
locale ; l’exécution destructive contrôlée sur un compte synthétique reste à
prouver.

## 4. Ordre obligatoire et gates

### Gate G0 — Réconciliation et gel du périmètre

**But :** disposer d’une base de travail cohérente avant toute nouvelle
fonction.

À réaliser :

- mettre les documents de statut en accord avec le build réel 3.0.0 ;
- référencer DEC-000074 et ce document dans la roadmap, la mémoire projet et
  le changelog ;
- établir la matrice des écrans, méthodes de calcul, tables Room, endpoints,
  fichiers locaux et données personnelles ;
- confirmer l’environnement API de test/staging et la base de test ;
- brancher le S25 Ultra par ADB et enregistrer uniquement l’identifiant de
  l’appareil, la version Android et le résultat de connexion ;
- figer les identités de test synthétiques et la politique de conservation des
  preuves ;
- vérifier les modifications concurrentes de Claude avant chaque tranche.

**Sortie :** matrice de référence approuvée, appareil ADB détecté, aucun
document Locked modifié, aucun contrat GSIE inventé.

### Gate G1 — GeoSylva 3.0 → 3.1 utilisable localement

**But :** terminer le cœur produit avant de brancher la verticale GSIE.

À réaliser :

1. **Interface et navigation**
   - parcours complet Projet → Forêt → Parcelle → Placette → Martelage ;
   - états vide, chargement, erreur, absence de GPS, absence de réseau et
     reprise après interruption ;
   - formulaires utilisables au soleil et avec gants autant que possible,
     accessibilité des tailles, contrastes et retours haptique/visuels ;
   - aucune donnée saisie perdue lors d’une rotation, fermeture ou coupure.

2. **Base locale**
   - migrations Room vérifiées depuis la version distribuée ;
   - transactions et relations Projet/Forêt/Parcelle/Placette/Session/Tige ;
   - distinction observation, calcul dérivé, estimation et interprétation ;
   - unités, méthode, version, précision, incertitude et horodatage conservés
     quand ils sont disponibles ;
   - sauvegarde et restauration locales testées sans écraser silencieusement
     une donnée plus récente.

3. **Calculs et synthèses**
   - surface terrière, densité, diamètre quadratique, hauteur et volumes
     selon les méthodes déjà présentes ;
   - chaque méthode doit avoir un nom stable, une version, des unités et un
     cas nominal ainsi que des cas limites ;
   - comparaison des résultats avec des valeurs de référence forestières ;
   - valeurs impossibles, données incomplètes et incohérences signalées, pas
     remplacées par des zéros ou des valeurs par défaut silencieuses.

4. **Martelage**
   - modes classique, vocal et hybride réellement enregistrés ;
   - statut de chaque tige, motif, qualité, destination éventuelle et auteur
     de la décision conservés ;
   - synthèse avant/après avec G, Dg, H, N/ha, G/ha, V/ha et les unités
     affichées ;
   - instantané de session rejouable et export vérifiable ;
   - l’application reste un outil d’aide : aucune recommandation ne devient
     automatiquement une décision forestière.

**Sortie :** parcours métier local complet démontré sur S25 Ultra, suite
Android verte, aucun crash critique, aucune perte de saisie et résultats
scientifiques relus.

### Gate G2 — Compte Quintessences et RGPD

**But :** rendre le compte utilisable et maîtrisable de bout en bout, côté
serveur et sur le téléphone.

À réaliser :

- finaliser la page native d'inscription et sa recette manuelle avec une
  adresse de test, sans redirection navigateur ni duplication du socle de
  connexion ;
- garder une identité canonique unique pour tous les fournisseurs ;
- relier la session mobile au compte sans stocker de mot de passe ni d’ID
  token en clair ;
- afficher uniquement les fournisseurs déclarés disponibles par l’API ;
- réaliser la configuration Google Cloud réelle, puis la connexion Google sur
  le S25 Ultra ;
- prouver la séparation des comptes, des sessions et des données locales ;
- compléter le cycle de restauration : récupération du mot de passe,
  annulation d’une suppression en attente et restauration d’une sauvegarde
  locale sont trois scénarios différents ;
- compléter l’effacement final serveur, son traitement des données liées et
  sa preuve d’exécution ;
- produire l’export portable sans secret et vérifier qu’il inclut toutes les
  données personnelles pertinentes, y compris les données GeoSylva quand elles
  sont synchronisées ;
- documenter les bases, finalités, durées, destinataires, droits et procédure
  de contact RGPD avec les informations juridiques réelles avant ouverture
  publique.

**Sortie :** matrice ADB G2 verte, export lisible et sans secret, suppression
locale et serveur prouvée, aucune session réutilisable après révocation,
aucune fuite de données entre deux comptes de test.

### Gate G3 — Finalisation du Data Acquisition Fabric

**But :** rendre l’acquisition de données fiable et raccordable à GSIE, après
stabilisation de l’application et de l’identité.

À réaliser dans l’ordre :

1. généraliser le contrat de handoff sans recopier les connecteurs Forge dans
   GSIE ;
2. qualifier juridiquement et techniquement les sources autorisées ;
3. assurer téléchargement borné, reprise, timeout, checksum, taille, MIME,
   déduplication et journal de provenance ;
4. gérer les versions, ETag/Last-Modified quand la source le permet, et les
   échecs sans objet partiel ;
5. persister Registry, RAW/Bronze et Silver avec transitions explicites ;
6. imposer la quarantaine pour les données incomplètes, contradictoires,
   inférées ou non validées ;
7. brancher un déclencheur planifié seulement après une décision opérateur et
   une qualification de conservation ;
8. mesurer l’observabilité, les coûts, la reprise et le rejeu idempotent.

**Sortie :** une acquisition réelle autorisée, rejouable, attribuée à une
source et version, sans promotion implicite et sans base parallèle.

### Gate G4 — Verticale GeoSylva 3.1 ↔ GSIE

**But :** réaliser la première boucle applicative complète, à partir du cœur
GeoSylva validé.

Préconditions strictes :

- RFC-0041 passée en Review puis DEC-000073 validée ;
- station de test et données acceptées disponibles dans GSIE TEST ;
- contrôle de compte et révocation du lien stationnel prouvés ;
- aucun contexte, règle ou état global fabriqué côté mobile.

À réaliser ensuite :

- `parcelleId` local → `gsie_resource_id` explicite, idempotent et révocable ;
- façade `analyse-geosylva` en processus vers l’orchestrateur existant ;
- DTO Kotlin versionnés, file Room/WorkManager et reprise réseau ;
- empreinte d’intention distincte de l’empreinte interne d’analyse ;
- résultat avec préparation, provenance, sources et niveau de preuve ;
- refus nommés si règle qualifiée, qualification, état global ou provenance
  manquent ;
- test de bout en bout sur une station synthétique puis sur un jeu autorisé.

**Sortie :** une analyse GeoSylva → GSIE réussie, explicable, rejouable et
isolée par compte, avec les causes de refus également prouvées.

### Gate G5 — Boucle d’amélioration contrôlée

**But :** améliorer le système à partir de preuves de terrain, pas à partir de
sorties non vérifiées.

À réaliser :

- enregistrer erreurs, incomplets, contradictions, corrections du forestier et
  contexte de reproduction ;
- séparer bug logiciel, défaut de donnée, erreur de mesure, erreur de modèle et
  divergence d’interface ;
- rejouer chaque correction sur des scénarios de référence ;
- faire valider humainement les changements scientifiques ;
- benchmarker avant tout entraînement, fine-tuning ou ajout de LLM ;
- ne jamais injecter automatiquement une sortie utilisateur dans la chaîne de
  décision.

**Sortie :** rapport d’amélioration versionné, avec gain mesuré ou décision de
ne pas modifier le système.

## 5. Registre des données du compte

### 5.1 Données canoniques serveur à conserver

Les données ci-dessous sont celles déjà modélisées ou nécessaires au cycle de
compte. Leur présence dans l’export et leur durée de conservation doivent être
vérifiées par la recette RGPD ; la table ne vaut pas avis juridique.

| Bloc | Données | Usage | Règle de sécurité |
|---|---|---|---|
| Compte canonique | UUID, statut, nom affiché, dates de création/modification, version de session, dates de désactivation/suppression | Identifier le compte partagé | UUID opaque ; aucune décision métier dans le nom |
| Identités liées | fournisseur, issuer, subject, e-mail normalisé, vérification, dernière authentification, révocation | Local, Google et futurs fournisseurs | `(provider, issuer, subject)` unique ; Google ne se déduit jamais du seul e-mail |
| Identité locale | hash Argon2id, date de changement | Authentifier localement | Mot de passe et hash exclus des exports et des logs |
| Rôles | application, rôle, date de création | Autorisation | Rôles délivrés par GSIE, jamais par Google |
| Actions sensibles | finalité, hash du code, expiration, consommation | Vérification e-mail, reset, annulation de suppression | Code en clair jamais persisté ; usage unique et délai borné |
| Consentements | type, version du document, acceptation, révocation, IP et User-Agent si nécessaires | Prouver le choix juridique | Versionner le document et ne pas transformer un consentement en acceptation générale |
| Changement d’e-mail | ancienne/nouvelle adresse normalisées, hashes des deux codes, confirmations, expiration, état | Double confirmation | Ne pas exposer une adresse à un autre compte |
| Sessions | identifiant, JTI, appareil, User-Agent, IP, émission, dernière activité, révocation | Contrôler et révoquer les accès | Lister et révoquer ; ne pas exposer le refresh token |
| Sécurité | MFA chiffré, hashes des codes de récupération, échecs de connexion, refresh révoqués | Protection du compte et détection de réutilisation | Secrets chiffrés ou hachés ; rétention documentée |
| Organisations et droits | appartenances, rôles, abonnements, habilitations quand utilisés | Accès partagé et fonctionnalités | Exporter les droits personnels sans exporter les secrets d’organisation |
| Audit | action, ressource, résultat, date, détails minimisés | Traçabilité et sécurité | Journaliser sans mot de passe, token, nonce ni code |

### 5.2 Données locales GeoSylva

Le compte ne doit pas seulement conserver son e-mail. Il doit contrôler les
données de travail qui peuvent identifier une personne, un propriétaire, une
parcelle ou une activité : projets, forêts, parcelles, placettes, sessions,
tiges, observations, photos, diagnostics, martelages, calculs dérivés,
exports, journaux locaux et files de synchronisation.

Chaque donnée métier locale doit avoir une stratégie explicite :

- propriétaire ou compte associé ;
- espace de travail ;
- auteur et appareil, si nécessaires ;
- date de création et de modification ;
- statut local et synchronisation ;
- présence dans l’export ;
- suppression logique, suppression physique ou conservation légale ;
- comportement lors de la déconnexion, du changement de compte, de la
  restauration et de la suppression.

Le `DeleteAllUserDataUseCase` existant constitue un point de départ pour la
purge, pas une preuve d’isolation multi-compte. Il purge des ensembles DAO
globaux ; il doit donc être testé et, si nécessaire, réorganisé autour d’un
compte ou d’un espace de travail avant de déclarer G2 terminé.

### 5.3 Données qui ne doivent jamais être conservées en clair

- mot de passe ;
- refresh token, access token et ID token Google ;
- nonce Google/OIDC ;
- code de vérification, reset ou annulation ;
- secret MFA et codes de récupération ;
- fichiers temporaires d’export contenant des données non chiffrées ;
- données personnelles dans `Logcat`, exception non filtrée, capture d’écran
  de recette ou dépôt Git.

## 6. Parcours RGPD à rendre opérationnels

### 6.1 Création et information

À l’inscription, l’utilisateur doit comprendre la finalité du compte, les
données nécessaires, les fournisseurs impliqués, les durées et les droits.
Les conditions et la politique de confidentialité sont acceptées par version
explicite. Le marketing reste séparé et révocable.

### 6.2 Consultation et rectification

Le compte doit permettre de relire l’identité canonique, le fournisseur, le
statut de vérification, les sessions, les consentements et les paramètres
pertinents. Le nom affiché est rectifiable. Le changement d’e-mail exige la
double confirmation déjà prévue par le serveur et invalide les sessions selon
le contrat existant.

### 6.3 Portabilité et export

`GET /api/v1/auth/me/export` est le point de départ serveur. Il doit être
recetté sur un compte riche et un compte vide, puis comparé à l’inventaire des
données. L’export doit être structuré, lisible, daté, sans secret et inclure
les données personnelles GeoSylva synchronisées ou indiquer clairement leur
canal d’export séparé.

### 6.4 Restauration

Le mot « restauration » couvre trois fonctions à tester séparément :

1. **récupération du compte** : reset du mot de passe avec anti-énumération et
   révocation des anciennes sessions ;
2. **annulation d’une suppression** : retour du statut `pending_deletion` à
   `active` avant l’échéance, avec code à usage unique ;
3. **restauration d’un appareil ou d’une sauvegarde** : réimport des données
   GeoSylva dans le bon compte, sans réintroduire un jeton expiré ni écraser
   une version plus récente.

La restauration opérateur d’une base PostgreSQL est un scénario
d’infrastructure distinct ; elle ne doit pas être présentée à l’utilisateur
comme une restauration de compte.

### 6.5 Suppression

Le parcours doit couvrir :

- demande authentifiée et confirmation forte ;
- passage en suppression différée et révocation des sessions ;
- notification et possibilité d’annuler pendant le délai prévu ;
- finalisation automatique à l’échéance ;
- purge ou anonymisation documentée des données liées, exports, fichiers,
  caches, files, liens GeoSylva et objets synchronisés ;
- conservation limitée des preuves légalement obligatoires, séparée du profil
  actif et sans réactivation possible ;
- confirmation finale et vérification négative par API, base, téléphone et
  stockage objet.

Au 2026-08-26, la demande différée et son annulation sont présentes côté API.
La finalisation automatique est implémentée par le worker décrit dans
DEC-000075, la migration 0055 est appliquée dans l’environnement local et la
fonction SQL a passé CPT-16 sur un compte synthétique dédié ; le smoke test
non destructif du processus worker reste à prouver.

La politique serveur retenue est : tombstone `user_account` désactivé,
suppression des liens d'identité, secrets, sessions, droits personnels,
consentements, répliques `geosylva_parcels` et autres données exclusivement
rattachées au compte ; conservation des organisations partagées et de la
preuve d'audit, avec masquage des adresses e-mail historiques. Cette politique
ne vaut pas validation juridique de la durée de conservation des journaux ou
des données de facturation.

## 7. Recette ADB sur Samsung S25 Ultra

### 7.1 Préparation

Sur le poste de travail :

```powershell
adb version
adb devices -l
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
```

Le numéro de série est conservé dans la preuve locale si nécessaire, mais ne
doit pas être publié avec des données de compte. Installer uniquement un APK
de test signé pour l’environnement ciblé :

```powershell
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb shell pm clear com.forestry.counter
```

La commande `pm clear` est destructive pour les données locales de test ; elle
est autorisée uniquement sur l’appareil et le compte de recette identifiés.

Pour les logs :

```powershell
adb logcat -c
adb logcat -v time | Select-String "forestry.counter|Identity|Auth|RGPD"
```

La recette doit contrôler que les logs ne contiennent ni e-mail complet,
secret, token, nonce, code d’action ou contenu de parcelle.

### 7.2 Matrice de tests compte

| ID | Scénario | Preuve attendue |
|---|---|---|
| CPT-01 | Inscription locale valide | Compte créé, UUID stable, session reçue, aucun secret en clair |
| CPT-02 | E-mail dupliqué, mot de passe faible, payload invalide | Erreurs bornées, pas d’énumération, aucun compte partiellement créé |
| CPT-03 | Déconnexion puis reconnexion locale | Logout révoque le refresh ; nouvelle session contrôlée |
| CPT-04 | Rotation refresh et rejeu ancien refresh | Rotation acceptée une fois ; ancien jeton refusé |
| CPT-05 | Vérification e-mail | Code à usage unique, expiration et statut relu |
| CPT-06 | Reset mot de passe | Réponse publique identique compte connu/inconnu ; anciennes sessions invalides |
| CPT-07 | Connexion Google nouvelle | Nonce, signature, issuer, audience, expiration et e-mail vérifiés ; compte créé une fois |
| CPT-08 | Liaison Google à un compte local | Liaison explicite ; même UUID ; aucune fusion automatique par e-mail |
| CPT-09 | Google non configuré ou nonce rejoué | Fournisseur signalé indisponible ou preuve refusée sans fuite |
| CPT-10 | Profil et changement d’e-mail | Nom rectifiable ; double confirmation ; sessions gérées |
| CPT-11 | Consentements | Versions acceptées, relues et révocables séparément |
| CPT-12 | Sessions et révocation | Session courante, autre session et révocation inter-compte testées |
| CPT-13 | Export | JSON lisible, complet selon inventaire, daté, sans token/hash/secret |
| CPT-14 | Demande de suppression | Statut `pending_deletion`, sessions révoquées, délai et notification prouvés |
| CPT-15 | Annulation de suppression | Code valide restaure le compte ; code expiré/rejoué refusé |
| CPT-16 | Finalisation de suppression | Compte, liens, données liées, caches et sessions ne permettent plus de connexion |
| CPT-17 | Purge locale | Base, photos, files, préférences personnelles et session chiffrée traitées |
| CPT-18 | Deux comptes sur le même S25 | Aucune donnée, session, export ou file du compte A visible par B |
| CPT-19 | Sauvegarde/restauration | Données restaurées dans le bon compte ; pas d’écrasement silencieux |
| CPT-20 | Offline et reconnexion | La saisie locale continue ; la synchronisation reprend sans doublon |
| CPT-21 | MFA si activé | Activation, challenge, codes de récupération, révocation et logs sûrs |
| CPT-22 | Désinstallation/réinstallation | Aucun retour silencieux d’une session ou donnée supprimée |

### 7.3 Identités de test

Les comptes de recette doivent être synthétiques et facilement révocables,
par exemple une adresse dédiée au domaine de test avec suffixe de campagne.
Les comptes Google de test doivent être déclarés dans l’écran de consentement
Google et ne doivent pas être les comptes personnels utilisés pour
l’administration du projet.

Chaque campagne conserve :

- identifiant de campagne ;
- commit de l’APK et de l’API ;
- environnement et version de base ;
- modèle et version Android ;
- cas exécutés, résultat et horodatage ;
- identifiants techniques pseudonymisés ;
- anomalie, reproduction et décision.

## 8. Critères de sortie V1

La V1 GeoSylva/GSIE est déclarée fonctionnelle uniquement si :

- G0 à G5 sont clôturés avec preuves ;
- GeoSylva 3.1 fonctionne sur le S25 Ultra, pas uniquement sur émulateur ;
- les calculs et le martelage sont comparés à des références et leurs limites
  sont affichées ;
- les comptes local et Google passent la matrice CPT sans fuite ni mélange ;
- export, récupération, restauration, révocation, consentements et suppression
  sont démontrés ;
- l’isolation par compte couvre API, Room, fichiers, photos, caches, files et
  sauvegardes ;
- les données acquises ont provenance, checksum, statut de qualification et
  stratégie de promotion ;
- la verticale GeoSylva ↔ GSIE est idempotente, révocable, explicable et
  fail-closed ;
- la boucle d’amélioration commence par un benchmark et une validation humaine ;
- la documentation juridique réelle est complète avant toute ouverture
  publique.

## 9. Preuves à produire

Les rapports doivent être déposés dans `23_QUALITY_MANAGEMENT/AUDITS/` ou dans
le dépôt externe concerné, puis référencés ici et dans `PROJECT_MEMORY.md`. Le
registre opérationnel des campagnes est
`23_QUALITY_MANAGEMENT/AUDITS/REGISTRE_CAMPAGNES_RECETTE.md` :

- audit de convergence GeoSylva 3.0 → 3.1 ;
- rapport de recette ADB comptes/RGPD ;
- inventaire des données personnelles et matrice de conservation ;
- rapport export/restauration/suppression ;
- rapport d’isolation multi-compte Room/fichiers ;
- preuve Google Cloud et recette OIDC ;
- preuve Data Acquisition Fabric et rejeu ;
- preuve de verticale GeoSylva ↔ GSIE ;
- benchmark et rapport de boucle d’amélioration.

Une preuve locale ou un build vert ne vaut pas preuve de production. Toute
limite doit rester écrite dans le statut.

## 10. Prochaine action

La prochaine tranche Codex prépare les preuves G2 : établir une baseline
reproductible de CI, puis recetter comptes, restauration et isolation sur
l'environnement de test. L'interface 3.0 peut avancer sur des fichiers distincts.
Les contrats et tests de synchronisation peuvent être préparés avant la recette
finale 3.1 ; leur livraison reste soumise aux gates. Cette distinction évite
d'attendre une 3.1 complète pour développer la synchronisation qu'elle exige.

## 11. Pilotage du lancement — clarification du 2026-09-07

### 11.1 Jalons produit

Selon DEC-000084, **3.0 termine l'interface** ; **3.1 vise le produit fiable
et commercialisable**, avec backend repris, calculs hors ligne, comptes et
synchronisation GSIE. La version affichée ne clôture aucun gate à elle seule.
Les paramètres, photos et localisations pris en charge doivent figurer dans
les contrats et les scénarios de recette ; leur simple stockage ne démontre
pas leur exploitation scientifique.

### 11.2 Lots de travail proposés

Ce tableau est le backlog de lancement de GEO-005, pas un registre de preuves.
Un responsable proposé n'implique aucune mission déjà envoyée à Devin.

| Lot | Responsable proposé | Dépendance | Critère de sortie | État au 2026-09-07 |
|---|---|---|---|---|
| L0 — Baseline et CI | Codex | Snapshot des deux dépôts | Commits ou diff de travail identifié, résultats et durées archivés, skips justifiés | En cours : workflow serveur enrichi localement ; GitHub non exécuté |
| L1 — Interface 3.0 | Agent interface dans Devin, revue fondateur | Matrice G0 | Parcours et états vide/erreur/offline validés sur appareil ; régressions visuelles tracées | En cours selon le Fondateur ; non recetté dans cette intervention |
| L2 — Backend mobile 3.1 | Mission Devin bornée, revue Codex | Contrats L1 stabilisés | Migrations depuis une base 2.8 synthétique, calculs de référence, photos/localisation, sauvegarde et restauration | À prouver ; réutiliser calculs et persistance existants |
| L3 — Comptes | Codex | G2 et infrastructure TEST | CPT-01 à CPT-22 applicables prouvés ; isolation compte A/B y compris fichiers et files | Preuves historiques partielles ; à rejouer sur le snapshot candidat |
| L4 — Synchronisation et analyse | Codex + mission mobile distincte | L2/L3, données qualifiées G3 | Reprise sans perte ni doublon, conflits explicites, résultat sourcé dans le mobile | API et client présents ; E2E appareil non prouvé |
| L5 — Exploitation cloud | Codex, choix fournisseur par Fondateur | L3/L4, besoin mesuré | Staging HTTPS, migrations, sauvegarde restaurée, alertes et retour arrière testés | TEST Docker local déclaré ; staging distant à préparer |
| L6 — Distribution et vente | Fondateur + préparation technique Codex | L1 à L5 et recette G0–G5 | AAB signé, installation via piste de test Play, mise à jour et droits d'abonnement recettés | Gratuit avec abonnement ; compte Play personnel existant, conversion à examiner |

Cadence proposée : une mission interface et une mission serveur/qualité au
maximum, sur des fichiers distincts. Une mission se termine par un résultat
vérifiable avant l'ajout d'un autre chantier dans le même périmètre.

### 11.3 Chaîne de validation et vitesse

| Niveau | Existant inspecté | Complément à réaliser | Fréquence cible |
|---|---|---|---|
| Boucle locale | pytest, Ruff, mypy ; tests Gradle | Tests ciblés du comportement modifié et régression ; références indépendantes pour les calculs | Chaque itération |
| PR serveur | Unitaires, mutations, Testcontainers, couverture combinée, Rust, Docker et sécurité dans `.github/workflows/ci.yml` | Exploiter JUnit, classer les skips, mesurer les durées avant cache ou découpage | Chaque PR, sans retirer les portes existantes |
| PR Android | Lint, unitaires, APK debug, bundle release non signé et gate | Recette instrumentée sur émulateur des parcours stables ; migrations Room | Chaque PR ; scénarios lourds à cadencer après mesure |
| E2E système | Suites API et banc HA présents | Mobile → API → DB/worker → mobile ; comptes synthétiques et données forestières attendues | Candidate 3.1 et modifications de contrat |
| Pannes et charge | Scripts de benchmark/HA existants | Réseau coupé, expiration de session, processus tué, reprise worker, panne DB, conflits et volume de photos | Campagne dédiée après scénario nominal |
| Release | `bundleRelease` Android en CI | Signature, installation Play, upgrade 2.8 → 3.1, restauration serveur et rollback | Chaque candidate commerciale |

Le JUnit rend visibles les cas réussis, en erreur ou ignorés et leurs durées.
Il ne transforme pas un test mocké en preuve d'intégration. Le garde-fou
`GSIE_REQUIRE_DOCKER=1` doit être actif sur l'intégration obligatoire.
Les rapports CI ajoutés sont conservés 14 jours avec les artefacts existants ;
les preuves d'une release doivent être archivées durablement dans la campagne.

Pistes de rapidité repérées, à traiter après baseline : le build Docker API
est refait dans le scan de sécurité ; le workflow Android se déclenche sur
push de branches et PR. Étudier la réutilisation d'image et la déduplication
sans supprimer de vérification ni masquer une exécution requise.

### 11.4 Boucle de travail IA

Réutiliser `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md` et
`GSIE/PROMPTS/REGISTER.md` : une mission versionnée, un snapshot, des fichiers
attribués, des critères d'acceptation et une preuve reproductible.

1. Reproduire le défaut ou écrire le scénario d'acceptation avant le correctif.
2. Modifier le périmètre attribué et exécuter les tests correspondants.
3. Revoir le diff et les résultats, y compris skips, erreurs et avertissements.
4. Comparer les résultats scientifiques à des vecteurs calculés indépendamment.
5. Enregistrer la preuve dans le registre des campagnes ; clore seulement le
   périmètre prouvé. Une répétition du même échec impose un diagnostic nouveau.

L'IA n'abaisse pas les assertions, les seuils ni les exigences scientifiques
pour obtenir du vert. Les résultats d'une autre IA sont vérifiés sur le code.

### 11.5 Décisions encore ouvertes

DEC-000085 fixe désormais un **essai unique de 14 jours pour tout
Quintessences**, lié au compte Google, puis un abonnement payant. Les comptes
testeurs activés par le Fondateur sont exemptés de paiement. Le futur mode
entreprise est lié à l'organisation, administré par elle et le Fondateur,
sans essai. La règle est documentée ; son activation n'est pas implémentée.
Le périmètre des abonnements payants ne se déduit pas du partage de l'essai.

DEC-000086 fixe le départ : bouton **« Démarrer mon essai »**, activation
unique confirmée par GSIE ; aucune activation à l'installation ou à la connexion.

- Parcours de souscription à préciser ; réutiliser `gsie_api.billing`
  plutôt que créer un compteur par application.
- Abonnement confirmé : prix, fonctionnalités gratuites/payantes, durée des
  droits hors ligne, expiration et reprise des achats à spécifier.
- TEST Docker local confirmé par le Fondateur ; staging distant, fournisseur,
  budget et volumétrie cible à définir.
- Compte Play personnel existant déclaré ; examiner sa conversion et la
  configuration des comptes Google de test avant toute nouvelle inscription.
- Périmètre scientifique exact de la première 3.1, régions et jeux de référence.

Google documente le passage personnel → professionnel avec création,
validation et association d'un profil de paiement approprié. Vérifier les
options du compte existant avant de le recréer. Son état n'a pas été inspecté.

Réutiliser `gsie_api.billing` : une route de vérification Google Play et une
passerelle existent déjà. Leur présence ne prouve pas le cycle d'abonnement.
La recette doit couvrir achat en attente, activation vérifiée côté serveur,
acquittement, renouvellement, annulation, expiration, remboursement,
notifications rejouées/désordonnées, restauration et association au bon compte.
Les notifications RTDN doivent déclencher la relecture de l'état auprès de
Google. Le comportement hors ligne et l'accès aux données après expiration
restent des décisions produit, pas des valeurs implicites ajoutées par l'IA.

Les exigences Play seront revérifiées lors de la distribution. Aucun
partenariat, subvention, hébergement acheté ou publication n'est présumé acquis.

### 11.6 Références techniques de cette mise à jour

- [Autonomie, réconciliation et IA mobile : examen du 2026-09-07](../../23_QUALITY_MANAGEMENT/AUDITS/2026-09-07_GEOSYLVA_OFFLINE_SYNC_IA.md)
- [Exigences offline-first et packs IA](../../03_DECISIONS/DEC-000087.md)
- [Rapports et artefacts GitHub Actions](https://docs.github.com/en/actions/tutorials/store-and-share-data)
- [Sortie et rapports pytest](https://docs.pytest.org/en/stable/how-to/output.html)
- [Décision de jalons](../../03_DECISIONS/DEC-000084.md)
- [Essai commun, testeurs et entreprises](../../03_DECISIONS/DEC-000085.md)
- [Activation explicite de l'essai](../../03_DECISIONS/DEC-000086.md)
- [Conversion du compte Play](https://support.google.com/googleplay/android-developer/answer/13634888?hl=fr)
- [Vérification des achats](https://developer.android.com/google/play/billing/security?hl=en)
- [Notifications RTDN](https://developer.android.com/google/play/billing/rtdn-reference)

### 11.7 Complément offline-first confirmé par le Fondateur

DEC-000087 étend le périmètre à un socle GSIE mobile autonome, aux corrections
serveur versionnées avec information systématique et aux packs IA sélectionnés
par benchmark matériel. Réutiliser RFC-0042 et RFC-0034 ; ne pas recopier les
14 services cloud dans l'application. La saisie et le calcul local restent
disponibles sans pack IA ni réseau pour leur périmètre couvert.

L2 porte la persistance/calcul local ; L4 porte synchronisation, vérification,
réconciliation et journal de notification. Le benchmark et les modèles constituent
des sous-lots distincts à qualifier, sans affirmer leur disponibilité pour 3.1.
La confirmation visuelle de RFC-0034 doit être réexaminée pour la saisie réellement
mains libres demandée. Les observations originales et les calculs historiques
restent conservés lors de la mise à jour d'un résultat courant corrigé.

La revue liée à §11.6 constate des composants existants, mais ni routes cubage
branchées ni recalcul serveur dans le service cubage inspecté. Aucun test E2E
ou benchmark mobile n'a été exécuté lors de cet examen.
