# RFC-0032 — Identité Quintessences multi-fournisseurs

| Champ | Valeur |
|---|---|
| **ID** | RFC-0032 |
| **Statut** | Adopté (2026-08-03, DEC-000044) |
| **Auteur** | Direction technique (assistée par Codex) |
| **Date** | 2026-08-03 |
| **Décision liée** | DEC-000044 |
| **Périmètre** | Comptes Quintessences, API GSIE, clients Web, PC et mobiles |
| **Motivation** | Fournir une identité commune à tout l’écosystème sans coupler les applications à un fournisseur de connexion |

## 1. Problème

GeoSylva, Artemis, Hydro, Ignis, les clients Web et PC ainsi que le
Centre de Commandement doivent reconnaître le même utilisateur et les
mêmes droits. L’API GSIE possède déjà des jetons JWT RS256 et des refresh
tokens rotatifs, mais son seul point d’entrée par mot de passe est un
compte de développement non persisté.

Créer un compte par application ou confondre le compte Quintessences avec
un compte Google produirait des identités incompatibles, des données
dupliquées et une dépendance durable à un fournisseur externe.

## 2. Solution adoptée

### 2.1 Compte canonique

Chaque personne possède un `user_account` Quintessences identifié par un
UUID stable. Les moyens de connexion sont des liens révocables vers ce
compte et ne constituent jamais le compte lui-même.

Les fournisseurs prévus sont :

| Fournisseur | Première version | Rôle |
|---|---|---|
| `local` | Actif | Adresse e-mail et mot de passe Argon2id ; vérification de l’adresse requise avant ouverture publique |
| `google` | Actif lorsque le client OAuth serveur est configuré | Connexion Google via OpenID Connect |
| `oidc` / `saml` | En développement | Fédération avec les comptes professionnels des futurs partenaires |

Les applications consomment toutes le même contrat d’authentification
GSIE. Elles ne stockent aucune logique d’identité métier et ne créent pas
de comptes propres.

### 2.2 Frontière de confiance

Un client Google transmet un jeton d’identité au module d’identité GSIE.
Le serveur vérifie sa signature, son émetteur, son audience, son
expiration et un nonce à usage unique. Le couple `(issuer, sub)` est la
clé externe stable ; l’adresse e-mail n’est jamais utilisée comme
identifiant Google.

Après authentification, GSIE émet ses propres jetons d’accès courts et
refresh tokens rotatifs. Aucun jeton Google ne donne directement accès à
un moteur GSIE.

### 2.3 Rattachement explicite

Une adresse e-mail identique ne suffit jamais à fusionner deux comptes.
Si Google retourne une adresse déjà rattachée à un compte local, l’API
répond `ACCOUNT_LINK_REQUIRED`. L’utilisateur doit alors s’authentifier
avec le compte Quintessences existant et confirmer explicitement le
rattachement de Google.

Un compte ne pourra pas retirer son dernier moyen de connexion utilisable.
La suppression physique des historiques d’authentification est interdite
au code applicatif ; les procédures RGPD d’effacement ou d’anonymisation
seront réalisées par un processus spécialisé et audité.

### 2.4 Autorisations

L’identité et l’autorisation restent distinctes. Les rôles sont attachés
au compte et à une application ou un périmètre. Une connexion Google
n’accorde aucun privilège supplémentaire. Une future appartenance à une
organisation fera l’objet d’un lien explicite et d’un mapping de rôles
administré côté serveur.

### 2.5 Interface

Les interfaces présentent :

1. « Continuer avec Google » ;
2. « Créer un compte » ou « Se connecter avec une adresse e-mail » ;
3. « Connexion professionnelle — En développement ».

Les noms et logos de l’ONF, du CNPF, d’INRAE ou de toute autre institution
ne sont pas présentés comme partenaires avant accord formel.

### 2.6 Données et sécurité

- les comptes et liens de fournisseurs vivent dans le périmètre isolé
  `gsie_rgpd_identites` ;
- les mots de passe sont hachés avec Argon2id et ne sont jamais journalisés ;
- les jetons d’identité, refresh tokens et nonces ne sont jamais journalisés ;
- les endpoints publics sont limités en débit et répondent avec des erreurs
  génériques ;
- les portées Google initiales sont limitées à `openid email profile` ;
- la création de compte et la première connexion exigent un accès réseau ;
  le mode hors-ligne des applications ne contourne jamais l’authentification
  serveur.

## 3. Contrats initiaux

| Méthode | Endpoint | Objet |
|---|---|---|
| `GET` | `/api/v1/auth/providers` | Capacités de connexion activées |
| `POST` | `/api/v1/auth/register` | Création d’un compte local |
| `POST` | `/api/v1/auth/login/password` | Connexion locale |
| `POST` | `/api/v1/auth/google/nonce` | Nonce Google court et à usage unique |
| `POST` | `/api/v1/auth/login/google` | Connexion ou création par Google |
| `POST` | `/api/v1/auth/link/google` | Rattachement Google explicite à un compte authentifié |

Les endpoints historiques `/auth/refresh`, `/auth/verify` et
`/auth/logout` restent communs à tous les fournisseurs. Le login de
développement reste séparé et interdit en préproduction et production.

## 4. Déploiement progressif

| Tranche | Contenu | Critère de sortie |
|---|---|---|
| I1 | Modèle de compte, fournisseur local, découverte des capacités | Inscription et connexion locales testées |
| I2 | Nonce et validation Google côté serveur | Jeton Google valide accepté, rejeu et jeton invalide refusés |
| I3 | Rattachement explicite et page de sécurité | Aucun rapprochement silencieux par e-mail |
| I4 | Organisations et fédération OIDC/SAML | Premier partenaire contractuel et pilote isolé |

## 5. Alternatives considérées

### 5.1 Un compte par application

Rejeté : les projets, autorisations et historiques seraient fragmentés et
la convergence vers le Centre de Commandement deviendrait coûteuse.

### 5.2 Google comme identité principale

Rejeté : le fonctionnement de Quintessences dépendrait d’un tiers et les
comptes locaux ou professionnels deviendraient des exceptions.

### 5.3 Fusion automatique par adresse e-mail

Rejeté : une adresse peut évoluer ou ne pas être une preuve d’identité
suffisante. Une fusion silencieuse ouvre un risque de prise de contrôle de
compte.

### 5.4 Déployer immédiatement un IAM externe complet

Différé : Keycloak ou Authentik restent évaluables lorsque le premier
besoin SAML/LDAP réel sera contractualisé. Le contrat Quintessences reste
indépendant afin de permettre ce remplacement sans modifier les clients.

## 6. Impacts et risques

- nouvelle migration Alembic dans le périmètre d’identités ;
- nouveaux endpoints publics à protéger contre l’énumération de comptes et
  les attaques par force brute ;
- nouvelles dépendances maintenues pour Argon2id et la validation officielle
  des jetons Google ;
- mise à jour nécessaire des SDK Kotlin, Python et TypeScript ;
- configuration OAuth, écran de consentement et vérification de marque Google
  nécessaires avant activation publique ;
- fédération professionnelle non activée par cette RFC.

## 7. Conformité

Cette RFC préserve :

- `GSIE-CON-006` : architecture et contrats documentés avant le code ;
- `GSIE-CON-007` : applications clientes découplées du fournisseur ;
- `GSIE-CON-008` : GSIE reste le moteur commun, les applications restent clientes ;
- `RFC-0021` : JWT RS256, rotation des refresh tokens et sécurité fermée ;
- `RFC-0029` : données identifiantes isolées des données scientifiques et
  des outils de visualisation.

## 8. Sources techniques

- [Android Developers — Implémenter Sign in with Google avec Credential Manager](https://developer.android.com/identity/sign-in/credential-manager-siwg-implementation)
- [Google — Référence OpenID Connect et stabilité du claim `sub`](https://developers.google.com/identity/openid-connect/reference)
- [Google — Vérifier un jeton d’identité côté serveur](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [OWASP — Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

## 9. Historique

| Date | Événement |
|---|---|
| 2026-08-03 | Proposition issue de la réflexion sur l’écosystème multi-clients |
| 2026-08-03 | Adoption explicite par Camille Perraudeau ; décision DEC-000044 |
