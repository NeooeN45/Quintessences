# Identité, authentification et comptes d'entreprise

## Décision d'architecture

Une seule identité interne Quintessences est utilisée par toutes les applications. Google, les passkeys et les systèmes d'entreprise sont des moyens de connexion fédérés, pas des comptes indépendants.

## Composants recommandés

- Keycloak comme autorité centrale d'identité ;
- PostgreSQL pour la persistance ;
- OpenID Connect et OAuth 2.0 ;
- Authorization Code Flow avec PKCE S256 sur Android ;
- passkeys/WebAuthn comme méthode Quintessences principale ;
- Google comme fournisseur externe ;
- Microsoft Entra ID, Google Workspace, Okta, Keycloak tiers ou SAML pour les entreprises ;
- service d'autorisation métier GSIE séparé.

## Identifiant interne

Chaque utilisateur possède un UUID Quintessences immuable.

Ne jamais utiliser comme clé principale :

- l'adresse électronique ;
- le nom ;
- le Google `sub` ;
- l'identifiant Microsoft.

Les identités externes sont liées à l'identité Quintessences.

## Modèle

```text
QuintessencesUser
  - id UUID
  - status
  - createdAt

ExternalIdentity
  - provider
  - providerSubject
  - verifiedEmail
  - linkedAt

Organization
Workspace
Membership
Role
Capability
Device
Session
Subscription
```

## Organisation et espace de travail

Le compte personnel reste unique. Les entreprises, établissements et partenaires sont des organisations ou workspaces.

Un même utilisateur peut être :

- propriétaire dans son entreprise ;
- intervenant dans un lycée ;
- prestataire dans une collectivité ;
- technicien dans une organisation cliente.

## Flux Google

1. GeoSylva ouvre l'URL Keycloak dans le navigateur système.
2. L'utilisateur choisit Google.
3. Google authentifie l'utilisateur.
4. Keycloak crée ou retrouve l'identité Quintessences.
5. GeoSylva reçoit des jetons Quintessences, jamais un jeton Google utilisé directement contre GSIE.

## Connexion Quintessences

Méthode principale :

- passkey ;
- biométrie ou code de l'appareil ;
- seconde passkey ou clé matérielle ;
- codes de récupération ;
- TOTP en secours.

Les mots de passe peuvent être conservés comme solution de compatibilité, pas comme méthode privilégiée.

## Connexion entreprise

- découverte par domaine ;
- redirection vers le fournisseur de l'organisation ;
- retour vers Keycloak ;
- émission de jetons Quintessences uniformes ;
- politique MFA de l'entreprise respectée.

## Liaison de comptes

Ne jamais fusionner automatiquement deux identités sur la seule base d'une adresse électronique.

Procédure :

1. identité externe nouvelle détectée ;
2. adresse déjà connue ;
3. demande de reconnexion avec un moyen déjà lié ;
4. confirmation explicite ;
5. création de la liaison ;
6. journal d'audit.

## Flux Android

- client public ;
- aucun secret dans l'APK ;
- Authorization Code + PKCE ;
- navigateur système ou Custom Tab ;
- App Link vérifié ;
- access token court ;
- rotation des refresh tokens ;
- stockage protégé par Android Keystore ;
- réauthentification pour les opérations sensibles.

## Hors ligne

GeoSylva met en cache :

- identité minimale ;
- workspace actif ;
- capacités ;
- missions ;
- droits essentiels ;
- expiration de la politique hors ligne.

La durée hors ligne dépend :

- de l'abonnement ;
- de la sensibilité ;
- de la politique de l'organisation ;
- du rôle.

L'expiration ne doit pas supprimer les données. Elle peut limiter la création de nouvelles opérations sensibles jusqu'à reconnexion.

## Séparation identité / autorisation métier

Keycloak gère :

- identité ;
- sessions ;
- fournisseurs ;
- MFA ;
- rôles généraux.

GSIE gère :

- accès à une forêt ;
- modification d'une mission ;
- validation d'un inventaire ;
- accès aux tarifs ;
- export sensible ;
- publication d'un pack.

## Sécurité administrative

Pour les administrateurs :

- passkey obligatoire ;
- second facteur de secours ;
- durée de session réduite ;
- journal de connexion ;
- révocation des appareils ;
- validation renforcée des actions critiques.
