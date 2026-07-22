# RFC-0021 — Socle de fiabilité d'entreprise pour Quintessences

| Champ | Valeur |
|---|---|
| **Statut** | Adopté (2026-07-21, DEC-000031) |
| **Auteur** | Direction technique |
| **Date** | 2026-07-21 |
| **Décision liée** | DEC-000031 |
| **Périmètre** | API GSIE, GeoSylva, Forge, QMS et CI |

## 1. Problème

L'audit croisé du code et de la documentation a identifié des mécanismes
capables d'échouer ouverts ou silencieusement : contrôles de rôle
contournables, rejeu de refresh token, authentification WebSocket déclarative,
publication d'événements après commit sans garantie, migrations automatiques,
repli de stockage non sûr, téléchargement externe non borné, SSRF sur
redirections, réouverture non chiffrée de la base mobile, ingestion de faits
non idempotente et documents anciens encore présentés comme actuels.

Ces risques ne peuvent pas être traités uniquement par des commentaires ou
une checklist. Les invariants doivent être exécutables et testés.

## 2. Décision proposée

### 2.1 Échec fermé par défaut

- Toute API sensible exige une identité et un rôle explicites.
- Une configuration de production incomplète bloque le démarrage.
- Un stockage, un bus ou une coordination obligatoires ne se replient pas
  silencieusement vers une implémentation locale.
- Les exceptions ne sont absorbées que si le résultat dégradé est explicite,
  observable et autorisé par configuration.

### 2.2 Frontières externes bornées

Toute URL fournie par un utilisateur doit être HTTPS, sans identifiants, puis
validée avant la requête et après chaque redirection. Les résolutions privées,
locales, link-local, multicast et plages réservées sont refusées. Le nombre
de redirections, la taille annoncée et la taille réellement lue sont bornés.
Un téléchargement incomplet est supprimé.

Tout document JSON externe est validé par schéma et règles métier avant
persistance. Une donnée non finie, négative hors contrat, dupliquée ou trop
volumineuse est rejetée.

### 2.3 Intégrité transactionnelle

Les mutations GSIE et leurs événements utilisent un outbox transactionnel.
La diffusion est au moins une fois ; chaque événement porte un identifiant
stable et les consommateurs doivent être idempotents.

Les refresh tokens sont à usage unique et rotés. L'opération de consommation
est atomique dans l'environnement distribué.

Les migrations destructives ne sont jamais déclenchées implicitement au
démarrage. Elles exigent un drapeau d'exécution, une confirmation de
sauvegarde et une autorisation destructive distincte.

### 2.4 Mobile et données locales

Tous les workers GeoSylva réutilisent la base SQLCipher ouverte par
l'application ; aucune seconde ouverture Room en clair n'est autorisée.
Les fichiers de sauvegarde sont écrits dans un temporaire puis renommés
atomiquement. Leur nom et leur métadonnée de portée décrivent exactement les
données exportées.

Les référentiels scientifiques intégrés indiquent leur version et sont testés
contre la source officielle en vigueur.

### 2.5 Forge

Forge refuse les chemins locaux via l'API distante, applique des rôles
cumulatifs, limite les téléchargements PDF/HTML, protège chaque redirection,
génère des identifiants de faits sur le contenu complet normalisé et rend
l'ingestion idempotente pour un lot et un corpus existant.

Les conteneurs applicatifs s'exécutent sans privilège root, exposent une
readiness vérifiant Redis et n'écoutent sur l'hôte local par défaut.

### 2.6 Qualité continue

Les dépôts appliquent au minimum :

- formatage et lint sans erreur ;
- typage strict pour Python ;
- tests unitaires et d'intégration adaptés au risque ;
- couverture Python globale minimale de 80 % lorsque mesurée ;
- lockfile contrôlé et installation verrouillée ;
- compilation avant tests ;
- permissions CI minimales, concurrence annulable et délais bornés ;
- revue obligatoire des zones critiques via CODEOWNERS ;
- description de PR incluant preuve, sécurité, migration et retour arrière.

### 2.7 Sources de vérité

Un registre versionné attribue à chaque corpus canonique un propriétaire, une
autorité, une date de dernière revue et une prochaine revue. La CI bloque un
registre expiré, incomplet, dupliqué ou pointant vers un chemin absent.

Les conversations et notes de session restent des archives contextuelles.
Elles ne sont jamais une décision ni une source actuelle.

## 3. Critères d'acceptation

- Les suites unitaires GSIE et Forge réussissent entièrement.
- Les tests GeoSylva couvrent le SSRF, la validation tarifaire et le barème
  IBP.
- Ruff et mypy strict réussissent sur Forge ; Ruff et mypy strict réussissent
  sur l'API GSIE.
- Les diffs sont exempts d'erreur d'espace et les configurations Compose sont
  syntaxiquement valides.
- Le registre documentaire et ses tests réussissent en local et en CI.
- Chaque risque non supprimé est consigné ci-dessous, sans être présenté
  comme résolu.

## 4. Risques résiduels acceptés provisoirement

1. La migration d'une ancienne base GeoSylva Room non chiffrée vers
   SQLCipher nécessite un protocole de migration et des fixtures réelles.
2. La sauvegarde mobile actuelle couvre les compteurs, pas encore une reprise
   complète de toutes les entités.
3. La protection SSRF applicative ne remplace pas une politique egress réseau
   et un résolveur/proxy contrôlé contre le DNS rebinding.
4. **Traité le 2026-07-22 pour le déploiement local partagé** : les mutations
   LanceDB sont sérialisées par verrou de fichier interprocessus et protégées
   par un test à quatre processus. La garantie ne s'étend pas au multi-hôtes :
   une contrainte `fact_id UNIQUE` canonique ou une coordination distribuée
   testée reste obligatoire avant cette montée en charge.
5. Les métadonnées de licence GSIE sont contradictoires entre la racine et
   l'API. Aucun automatisme ne peut arbitrer une décision juridique.
6. GeoSylva conserve **564 avertissements Kotlin/Android Lint** inventoriés
   le 2026-07-21, à réduire par lots sans modifier aveuglément les calculs
   métier ; aucune erreur Lint bloquante ne subsiste.

## 5. Déploiement et retour arrière

Chaque dépôt utilise une branche dédiée. Les changements de sécurité et de
schéma sont livrés séparément, après CI verte. La migration GSIE est exécutée
comme une étape contrôlée avant l'application, jamais par chaque réplique.

Le retour arrière applicatif est autorisé seulement si les migrations restent
compatibles. L'outbox est conservé pendant un rollback afin de ne pas perdre
les événements. Les clés API et secrets sont rotés après tout incident
d'exposition.

## 6. Alternatives rejetées

- Se limiter à documenter les risques : aucune prévention exécutable.
- Autoriser des replis locaux automatiques en production : état divergent et
  perte de preuve.
- Corriger tous les avertissements mobiles en une seule réécriture :
  risque disproportionné de régression scientifique et métier.
- Modifier automatiquement la licence : décision juridique hors compétence
  technique.
