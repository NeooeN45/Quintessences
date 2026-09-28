# Contrats et passage backend/frontend — GSIE-DEV-003

| Champ | Valeur |
|---|---|
| Statut | Draft — protocole de travail, endpoints nouveaux non adoptés |
| Version | 0.1.0 |
| Date | 2026-09-28 |

## 1. Contrat partagé

Le code FastAPI et les schémas Pydantic sont la référence des routes existantes.
`docs/openapi.json` en est une extraction versionnée à régénérer au lot B00.
L’[inventaire des routes](contracts/client-existing.route-inventory.json) liste
identité, synchronisation et orchestration ; il ne contient pas les schémas.
Pour générer un client, utiliser le véritable `docs/openapi.json`, régénéré
et comparé au code au lot B00.
Sa provenance accompagne le fichier ; aucune disponibilité distante n'en est déduite.

Les exemples et mocks de Claude reprennent ce contrat. Les routes en projet
restent isolées comme maquettes, sans pouvoir être activées par un simple
changement d'adresse de serveur. La génération d'un client conserve la version
du contrat et vérifie les erreurs aussi bien que les succès.

## 2. Éléments existants utiles au frontend

| Parcours | Routes existantes, préfixe `/api/v1` | Attention |
|---|---|---|
| Connexion disponible | `GET /auth/providers` | Afficher seulement les fournisseurs activés |
| Compte local | `POST /auth/register`, `POST /auth/login/password` | Réponses token, défi MFA ou activation MFA requise |
| Profil | `GET /auth/me`, `PATCH /auth/me` | Autorisation serveur indispensable |
| Vérification/récupération | `/auth/email/verification/*`, `/auth/password/reset/*` | Messages de récupération cohérents sans inventer l'existence d'un compte |
| Sessions | `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/sessions` | Déconnexion n'implique pas révocation instantanée de tout jeton déjà émis |
| Copie de parcelles | `GET /sync/geosylva/parcelles`, `PUT/DELETE /sync/geosylva/parcelles/{client_id}` | État courant, pas sauvegarde complète des relevés |
| Contexte stationnel | `GET /orchestration/stations/{station_id}/contexte` | Identité stationnelle et données qualifiées nécessaires |
| Analyse interne | `POST /orchestration/analyse` | Ne vaut pas façade GeoSylva prête à l'emploi |

Le contrat contient des erreurs héritées hétérogènes. Le client doit les
normaliser sans présumer une enveloppe unique déjà appliquée à toutes les routes.
Toute harmonisation serveur future respecte la compatibilité des clients.

## 3. Contrats à livrer par Codex

| Capacité | Lot propriétaire | Champs et comportements à spécifier |
|---|---|---|
| Références territoriales | B02 | Producteur, référence, limite/version, précision, SRID, droits |
| Campagnes et observations | B02/B03 | Méthode, dates, mesures/unités, révision, auteur contrôlé |
| Journal de mutations | B04 | Opération, empreinte, version de base, reçu, conflit, retry |
| Restauration | B04/B06 | Instantané, curseur, expiration, reprise, versions et retraits |
| Médias | B05 | Manifeste, taille/type/empreinte, statut et autorisation temporaire |
| Rapport GeoSylva | B08/B09 | Lieu canonique, demande, travail asynchrone si nécessaire, sources |
| Conversation PC | B10 | Conversation autorisée, événements, outils bornés, citations et coûts |

Les noms des futures routes ne sont pas fixés par cette table. Chaque lot remet
OpenAPI, jeux d'exemples synthétiques et changelog de compatibilité après revue.

## 4. État visible et état serveur

| État à afficher | Condition réelle |
|---|---|
| Enregistré sur cet appareil | Transaction locale terminée |
| À synchroniser | Opération durable dans la file locale |
| Synchronisé | Reçu serveur valide après persistance |
| Conflit à résoudre | Réponse de conflit, deux états présentés sans écrasement |
| Restauration partielle | Au moins une page ou un média manque |
| Restauré | Manifeste complet et vérifications de contenu réussies |
| Analyse indisponible | Précondition absente ou capacité non livrée |
| Analyse disponible | Résultat effectivement reçu avec état et preuves |

Un code HTTP réussi pour la copie d'une parcelle ne signifie pas que tous ses
arbres et médias sont sauvegardés. Un chargement qui échoue n'affiche pas une
liste vide comme s'il n'existait aucun relevé. Un traitement peut rester
partiel ; le frontend conserve l'explication et permet la reprise.

## 5. Frontières d'accès et gestion de session

Le serveur décide des droits sur chaque objet, version, export, média et outil.
Le frontend limite l'affichage mais ne constitue pas une barrière de sécurité.
Les données cartographiques sensibles ne sont pas publiques par défaut.
Tout partage collectif nécessite une politique explicite et des données dérivées
autorisées ; contribution terrain ne signifie pas publication ouverte.

Le contrat actuel transporte des tokens dans JSON. Pour le web, Claude ne doit
pas ajouter de stockage persistant de refresh token dans `localStorage`.
Un adaptateur serveur du frontend avec session par cookie HttpOnly, Secure et
protection CSRF peut être proposé, puis qualifié en B01 ; il n'est pas déjà livré.
La maquette peut rester sans authentification réelle, clairement marquée.
Pour une application PC native, utiliser un stockage protégé par le système
après choix de la technologie. Aucun secret d'API privilégiée dans un client.

## 6. Passage de relais accepté

Chaque lot backend remet son snapshot exact, OpenAPI, exemples, limites,
erreurs, preuve de droits et procédure locale. Claude remet écrans, clavier,
états de chargement/échec, comportements hors connexion, client et résultats
sur API de préproduction. Les deux agents inspectent le diff d'intégration.
Toute différence de schéma devient une modification tracée du contrat.

## 7. Références et historique

[Lots backend](BACKEND_WORK_PACKAGES.md), [brief frontend](FRONTEND_BRIEF.md),
[README API](../../README.md).

| Date | Évolution |
|---|---|
| 2026-09-28 | Contrats existants et protocole de raccordement documentés |
