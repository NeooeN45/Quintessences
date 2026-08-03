# IDENTITÉ — Authentification multi-fournisseurs 1.2.0

| Champ | Valeur |
|---|---|
| **Identifiant** | IDENTITE-001 |
| **Statut** | Draft |
| **Version** | 1.2.0 |
| **Date** | 2026-08-03 |
| **Auteur** | Direction technique (assistée par Codex) |
| **Décision** | DEC-000044, DEC-000045, DEC-000046 |

## 1. Résumé

Cette spécification définit les exigences du compte Quintessences et des
connexions locale, Google et professionnelle future. Elle s’applique à
tous les clients de l’API GSIE.

## 2. Exigences fonctionnelles

| ID | Exigence | Priorité | Critère d’acceptation |
|---|---|---|---|
| ID-F-001 | Le système attribue un UUID canonique à chaque compte | P0 | Le même `sub` GSIE est obtenu avec tous les fournisseurs rattachés |
| ID-F-002 | Un utilisateur peut créer un compte par e-mail et mot de passe | P0 | Une inscription valide crée le compte, le lien local et le rôle `user` |
| ID-F-003 | Un utilisateur peut se connecter avec son compte local | P0 | Des identifiants valides produisent des jetons GSIE |
| ID-F-004 | Le serveur publie les fournisseurs réellement disponibles | P0 | `/auth/providers` distingue actif, non configuré et en développement |
| ID-F-005 | Un utilisateur peut se connecter avec Google lorsque configuré | P0 | Un ID token valide et un nonce actif produisent des jetons GSIE |
| ID-F-006 | Une première connexion Google peut créer un compte | P0 | Création uniquement si aucun compte correspondant à l’e-mail vérifié n’existe |
| ID-F-007 | Un compte existant n’est jamais fusionné automatiquement par e-mail | P0 | L’API retourne `ACCOUNT_LINK_REQUIRED` |
| ID-F-008 | Un utilisateur authentifié peut rattacher Google explicitement | P0 | Le lien conserve l’UUID canonique existant |
| ID-F-009 | Tous les fournisseurs partagent refresh, verify et logout | P0 | Les jetons suivent le contrat JWT RS256 actuel |
| ID-F-010 | La connexion professionnelle apparaît comme « En développement » | P1 | Aucun flux OIDC/SAML n’est déclenché avant configuration |
| ID-F-011 | Les rôles sont issus de Quintessences, pas du fournisseur public | P0 | Les claims Google ne peuvent pas accorder `admin` ou un rôle métier |
| ID-F-012 | Les applications utilisent le même compte | P0 | GeoSylva, Web, PC, Artemis, Hydro et Ignis acceptent le même `sub` |
| ID-F-013 | GeoSylva propose un espace compte distinct de la page de connexion | P0 | L'utilisateur peut consulter sa session et se déconnecter sans quitter les paramètres |
| ID-F-014 | GeoSylva conserve ses fonctions de terrain lorsque GSIE est indisponible | P0 | Une erreur réseau d'identité n'empêche pas l'accès aux données locales |
| ID-F-015 | Huit pressions successives sur la version activent les options développeur | P1 | Le compteur indique les pressions restantes puis rend l'écran diagnostic accessible |
| ID-F-016 | Les options développeur présentent un diagnostic GSIE en lecture seule | P1 | Disponibilité, latence, version, environnement et dépendances sont consultables sans commande distante |
| ID-F-017 | Un utilisateur authentifié peut consulter et modifier son nom affiché | P0 | Le profil mis à jour est relu avec le même UUID canonique |
| ID-F-018 | Un compte local peut vérifier son adresse électronique | P0 | Un code valide à usage unique marque l'adresse comme vérifiée |
| ID-F-019 | Un utilisateur peut récupérer son mot de passe sans énumération de comptes | P0 | Adresse connue ou inconnue produit la même réponse publique |
| ID-F-020 | Une récupération révoque les anciennes sessions | P0 | Un refresh token émis avant le changement est refusé |

## 3. Exigences de sécurité

| ID | Exigence | Critère d’acceptation |
|---|---|---|
| ID-S-001 | Les mots de passe sont hachés avec Argon2id | Aucun mot de passe ni hash réversible n’est stocké |
| ID-S-002 | Le mot de passe contient entre 12 et 128 caractères | Les entrées hors bornes sont refusées avant traitement |
| ID-S-003 | Les erreurs de connexion n’énumèrent pas les comptes | Même statut et même message pour compte inconnu et mot de passe faux |
| ID-S-004 | Le jeton Google est vérifié côté serveur | Signature, `iss`, `aud`, `exp`, `sub` et e-mail vérifié contrôlés |
| ID-S-005 | Google utilise un nonce à usage unique | Nonce expiré, absent ou rejoué refusé |
| ID-S-006 | Google est identifié par `(issuer, sub)` | L’e-mail n’est jamais la clé externe |
| ID-S-007 | Les endpoints publics sont limités en débit | Limites spécifiques déclarées sur chaque route |
| ID-S-008 | Les secrets et données d’authentification sont absents des logs | Revue des événements structurés sans e-mail, jeton, nonce ni mot de passe |
| ID-S-009 | Les comptes désactivés ne peuvent plus ouvrir de session | Connexion locale et Google refusées |
| ID-S-010 | Le code applicatif ne peut pas supprimer physiquement les comptes | Le rôle d'exécution ne possède pas `DELETE` sur les tables d'identité |
| ID-S-011 | Les jetons mobiles sont stockés dans un espace chiffré | Aucun jeton n'est présent dans DataStore, les logs ou une préférence en clair |
| ID-S-012 | Le mode développeur local n'accorde aucune autorisation | Son activation ne modifie ni les rôles ni les claims GSIE |
| ID-S-013 | Le diagnostic développeur exclut les données sensibles | Aucun mot de passe, jeton, nonce, e-mail ou secret n'est affiché |
| ID-S-014 | Une future commande réservée au Fondateur est contrôlée côté serveur | Un geste local ou une valeur embarquée ne suffit jamais à autoriser la commande |
| ID-S-015 | Les codes d'action sont aléatoires, hachés, expirables et à usage unique | Aucun code en clair n'est persisté et sa durée maximale est de 15 minutes |
| ID-S-016 | La récupération de mot de passe est anti-énumération | Statut, corps et délai ne révèlent pas l'existence du compte |
| ID-S-017 | Le transport des courriels est chiffré hors développement local | STARTTLS ou TLS direct est requis en production |

## 4. Exigences de données

| ID | Exigence |
|---|---|
| ID-D-001 | Les tables d’identité sont placées dans `gsie_rgpd_identites` |
| ID-D-002 | `(provider, issuer, subject)` porte une contrainte unique |
| ID-D-003 | L’e-mail est normalisé avant comparaison et stockage |
| ID-D-004 | Les dates sont stockées en UTC avec fuseau |
| ID-D-005 | Les changements de mot de passe et dernières authentifications sont horodatés |
| ID-D-006 | Les rôles sont associés à un périmètre applicatif explicite |
| ID-D-007 | Les actions sensibles conservent seulement type, empreinte, expiration et date de consommation |

## 5. Exigences d'interface

L'ordre visuel recommandé est : Google, séparateur « ou », formulaire
e-mail/mot de passe, puis connexion professionnelle désactivée avec le
libellé « En développement ». Le client doit suivre `/auth/providers` et
ne jamais simuler un fournisseur actif.

GeoSylva présente trois surfaces distinctes :

1. la page de connexion et de création de compte ;
2. l'espace compte, le profil et la vérification d'adresse ;
3. la récupération du mot de passe ;
4. les options développeur, activées après huit pressions sur la version.

L'espace développeur est un diagnostic local en lecture seule. Il ne doit
jamais être présenté comme un espace d'administration sécurisé. Toute
commande future réservée au Fondateur dépend d'un rôle signé dans la session
GSIE et d'une vérification serveur sur chaque requête.

## 6. Hors périmètre de la tranche initiale

- authentification multifacteur et passkeys ;
- administration des organisations ;
- fédération OIDC/SAML ;
- usage de logos institutionnels ;
- synchronisation hors-ligne de nouveaux comptes.

## 7. Traçabilité

| Exigences | Source |
|---|---|
| ID-F-001 à ID-F-012 | RFC-0032 §2 et §3 |
| ID-S-001 à ID-S-010 | RFC-0032 §2.2, §2.3 et §2.6 |
| ID-D-001 à ID-D-006 | GSIE-ARCH-IDENTITE-001 §3 et §4 |
| ID-F-017 à ID-F-020, ID-S-015 à ID-S-017, ID-D-007 | DEC-000046 |

## 8. Historique des modifications

| Date | Version | Modification |
|---|---|---|
| 2026-08-03 | 1.0.0 | Première spécification issue de DEC-000044 |
| 2026-08-03 | 1.1.0 | Parcours GeoSylva et diagnostic développeur issus de DEC-000045 |
| 2026-08-03 | 1.2.0 | Profil, vérification e-mail, récupération et révocation issus de DEC-000046 |
