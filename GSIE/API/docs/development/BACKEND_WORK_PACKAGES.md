# Lots backend — GSIE-DEV-002

| Champ | Valeur |
|---|---|
| Statut | Draft — backlog de réalisation |
| Version | 0.1.0 |
| Date | 2026-09-28 |
| Agent principal | Codex |

## 1. Ordre et périmètre

Le jalon actif est **GeoSylva V3.1**, après la refonte V3.0, avec abonnement
Quintessences et publication Play. B00–B08, les rapports GeoSylva nécessaires
de B09 et la qualification du billing existant servent ce jalon. Les analyses
multi-échelles de GSIE suivent. B10 appartient au sixième jalon produit,
après Artemis, Ignis et Hub. Voir [les portes de sortie](RELEASE_GATES.md).
Les dépendances techniques ci-dessous ne valent pas ordre de lancement produit.

Ajouter à B01/G8 la qualification de l'abonnement existant, sans nouvelle
identité ni nouveau catalogue parallèle : achat Android, validation serveur,
liaison au compte, acquittement et cycle de vie des droits.

| Lot | Dépendances | Résultat attendu |
|---|---|---|
| B00 | Aucune | Baseline reproductible et inventaire de contrats |
| B01 | B00 | Parcours de compte et isolation qualifiés |
| B02 | B00 | Identité territoriale et relevés spécifiés |
| B03 | B01, B02 | Relevés et révisions persistés sans perte |
| B04 | B03 | Journal de synchronisation et restauration cohérente |
| B05 | B03 | Médias privés, récupérables et contrôlés |
| B06 | B04, B05 | Récupération complète et sauvegarde vérifiées |
| B07 | B01, B06 | Préproduction OVHcloud qualifiée |
| B08 | B02, B03, B06 | Façade d'analyse GeoSylva raccordée |
| B09 | B08 | Rapports territoriaux datés et reproductibles |
| B10 | B01, B09 | Outils du dialogue environnemental PC |

Les contrats de B02 à B05 sont à spécifier avant leur migration. B00 et la
qualification de l'existant peuvent commencer maintenant. Les RFC-0041 et
RFC-0042 restent proposées ; une nouvelle API ou un nouveau schéma doit être
réconcilié et tracé avant son implémentation, sans bloquer l'audit existant.

## 2. B00 — une baseline utilisable

Lire `AGENTS.md`, `GSIE/API/AGENTS.md`, la configuration, `pyproject.toml`,
Compose, les workflows et les tests. Documenter les versions réellement
résolues dans un environnement Python 3.12 isolé. Distinguer dépendance absente,
service absent et défaut du code. Reprendre les contrôles existants, sans
mettre à jour toutes les dépendances en bloc.

Sorties : procédure de démarrage local vérifiée, matrice tests/services,
OpenAPI régénéré et diff expliqué, schéma Alembic de départ, inventaire
fonctionnel de l'application GeoSylva à synchroniser. Le dépôt GeoSylva est
externe : sa version est relevée avant tout changement de contrat mobile.
Le correctif de rejeu est publié séparément dans la PR #61, non fusionnée.
Les documents de préparation ne contiennent pas ce changement de code ;
relever les branches et préserver les travaux locaux dans le rapport.

Acceptation : environnement vierge identifiable, contrôles exécutés avec
résultats et raisons des exclusions ; aucune prétention de production.
La revue générale de l'état du projet signalée expirée reste distincte.

## 3. B01 — comptes, droits et sessions

Périmètre : `auth/`, `core/auth.py`, `core/rbac.py`, contexte RLS, routes
privées et tests associés. Réutiliser inscription, vérification d'e-mail,
connexion, récupération, MFA et sessions ; ne pas construire une identité
parallèle dans le frontend.

Vérifier sur PostgreSQL avec le rôle applicatif réel : accès croisé à une
parcelle, une révision, un export et un média ; compte désactivé ; session
révoquée ; rotation et réutilisation de refresh token ; reprise concurrente.
Le JWT d'accès peut avoir une fenêtre de validité après déconnexion : mesurer
et documenter le comportement existant avant de choisir une révocation plus
immédiate. Protéger la récupération contre les fuites d'identité ; quotas par
compte et par source réseau sans pénaliser toutes les équipes derrière une IP.

Acceptation : séparation démontrée à l'API et dans la base, comportement des
sessions expliqué et parcours de récupération utilisable. Préparer les preuves
avec données synthétiques et revue de sécurité indépendante.

## 4. B02 — lieux, limites et relevés

Périmètre : RFC-0041/0042, métamodèle existant `Place`, `Observation`, `Revision`,
`Source`, `TemporalContext`, règles de droit et contrat GeoSylva.

Spécifier une matrice de correspondance avec les types existants avant d'ajouter
une table : identité locale, lieu GSIE, référence producteur, version de limite,
géométrie/SRID, précision, campagne, auteur, méthode, unité et incertitude.
Une parcelle administrative, une unité forestière et un bassin versant peuvent
se superposer. Une trace GPS est conservée comme source avec sa précision.
Une référence manquante ou non licenciée n'est jamais inventée.

Écrire des exemples synthétiques : deux utilisateurs, deux parcelles, deux
campagnes et une correction. Définir `observed_at`, réception serveur et
disponibilité pour l'analyse ; une correction rétroactive ne change pas ce
qui était disponible lors d'une analyse passée. Prévoir changement de limite,
division/fusion et liens vers les versions anciennes sans double comptage.

Acceptation : contrat versionné, règles de transition, licences qualifiées,
validation géométrique et matrice de réutilisation relus. La future sélection
obligatoire d'une zone nécessite un parcours compatible avec le terrain hors ligne.

## 5. B03 — persistance des relevés

Ajouter uniquement les schémas nécessaires après B02. Enregistrer campagnes,
arbres, mesures et observations dans un journal de révisions. Une correction
produit une nouvelle révision liée à celle qu'elle remplace ; un nouveau
relevé reste un événement distinct. L'état courant est une projection.

Migrations additives d'abord ; conserver les clients existants et les données
de `gsie_synchronisation.geosylva_parcels`. Définir l'import des anciennes copies
comme migration de provenance, sans inventer les versions déjà écrasées.
Encadrer retrait logique, rectification, effacement légal et archivage par les
politiques applicables ; « historique durable » ne signifie pas conservation
illimitée de toute donnée personnelle.

Acceptation : commit atomique relevé/révision/projection, collision contrôlée,
aucun historique perdu, isolation des révisions, migration et rollback compatibles.
Une migration descendante destructrice n'est pas exécutée sur des données réelles.

## 6. B04 — journal, reprise et restauration

Périmètre : `sync/`, persistance des opérations, migrations et contrats clients.
Définir l'identifiant d'opération par compte/appareil, l'empreinte canonique de
la mutation et la durée de conservation des reçus. Le compte est issu de
l'authentification, jamais d'un auteur librement fourni par le client.

Dans la même transaction : autorisation, contrôle de version, insertion de la
révision et du reçu, mise à jour de la projection. Le même identifiant et le
même contenu retournent un reçu stable ; un contenu différent produit un conflit.
Le retry après perte de réponse ne crée pas un second événement.

Spécifier un instantané figé par compte, ses objets et leurs versions, puis un
curseur de changements. Ne pas supposer qu'un numéro de séquence alloué est
un ordre de commit : contrôler les transactions concurrentes et la fermeture
de l'instantané. Curseurs opaques, bornés, liés au compte et au filtre, avec
expiration explicite ; reprise possible après interruption.

Acceptation : aucune omission ou duplication sous écritures concurrentes ;
deux appareils ; même création concurrente ; correction et suppression ;
opération ancienne rejouée ; reprise au milieu d'un transfert ; ancienne
application toujours utilisable pendant la transition. Définir limites des
lots, pagination, quotas et version minimale client.

## 7. B05 — pièces jointes et stockage

Réutiliser `infrastructure/object_storage.py` et l'abstraction S3 existante.
Créer un manifeste lié à une révision : taille, type, empreinte, origine et
statut. Vérifier contenu réel, limites et droits ; traiter les données EXIF
selon la politique de localisation. Les objets sont privés et les liens
temporaires restent limités à l'opération autorisée.

Traiter dépôt interrompu, objet en attente, validation finale, doublon et objet
orphelin. La déduplication ne doit pas révéler la présence d'un fichier chez un
autre compte. La base et S3 n'ont pas de transaction commune : une machine
d'états et la réconciliation doivent rendre explicites les transferts incomplets.

Acceptation : restauration avec empreintes vérifiées ; refus croisé ; fichier
malformé/quota ; expiration ; absence de média sans succès mensonger.

## 8. B06 — récupération et reprise après incident

La restauration d'une application et la restauration de l'infrastructure sont
deux parcours à vérifier. L'export forestier complète l'export de compte existant.
Les sauvegardes couvrent tous les schémas métier, les manifests, les médias,
la configuration et les moyens de récupération des clés.

Améliorer `scripts/test_restore.sh` : vérifier des seuils réels, pas seulement
afficher un nombre de tables `public`. Restauration sur un environnement isolé,
comparaison de relevés et empreintes, accès et versions après restauration.
Journaliser chaque preuve sans données privées. Définir rétention, fréquence,
objectifs de perte/délai et procédure de restauration avant d'en faire une promesse.

Acceptation : réinstallation réelle de GeoSylva et restauration serveur isolée
avec résultats concordants ; pertes et délai mesurés ; échec d'une sauvegarde
déclenche une alerte ; opération de reprise documentée et reproductible.

## 9. B07 — préproduction OVHcloud

Qualifier [l'architecture candidate](OVHCLOUD_DEPLOYMENT.md) ; construire les
images Linux et les services nécessaires à partir de versions identifiées.
Prévoir réseau privé, comptes d'exploitation, secrets, courriers transactionnels,
alertes, sauvegardes distantes et retour arrière. L'infrastructure déclarative
est préparée avec plan relu avant toute commande ou dépense cloud.

Acceptation : pilote synthétique complet, isolation, reprise, TLS et montée
en charge représentative ; capacité et coût mesurés ; validation explicite
avant exposition de données réelles. Une instance unique n'est pas qualifiée HA.

## 10. B08 à B10 — exploiter les données fiables

B08 raccorde les identités stationnelles et la façade GeoSylva selon RFC-0041 :
règles et qualifications disponibles côté serveur, sans contexte fabriqué.
L'ingestion scientifique passe par le Data Registry et les procédures Forge.

B09 produit des rapports sur une question, une zone et une période : versions
consommées, qualité, couverture, droits et modèles conservés ; absence de
mesure et conflit explicites. Les anciennes campagnes servent aux tendances,
avec effort d'échantillonnage et surfaces évitant les doubles comptes.

B10 expose des outils bornés à l'assistant environnemental : lire les données
autorisées, demander un rapport et retrouver ses preuves. Requêtes et documents
externes ne confèrent aucun droit ni autorité. Chaque réponse distingue faits,
hypothèses, simulations et limites ; coûts/temps d'exécution sont bornés.
Les écritures et actions sensibles suivent une confirmation humaine appropriée.

Acceptation : jeux d'évaluation métier, refus d'accès et de réponse sans preuve,
reproduction de rapports, retour utilisateur traçable. La simulation physique
et les prévisions restent un programme scientifique ultérieur, pas une simple
extension de la conversation.

## 11. Références et historique

[README du dossier](README.md), [RFC-0042](../../../../02_RFC/RFC-0042-observation-territoriale-simulation-environnementale.md),
[RFC-0041](../../../../02_RFC/RFC-0041-contrat-facade-geosylva-identite-stationnelle.md).

| Date | Évolution |
|---|---|
| 2026-09-28 | Découpage de la réalisation backend et portes d'acceptation |
