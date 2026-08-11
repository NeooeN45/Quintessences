# Données, synchronisation, sécurité et audit

## Identifiants

Toute entité synchronisable utilise un UUID global créé côté client ou serveur.

## Distinctions importantes

- arbre permanent ;
- observation d'arbre ;
- mesure ;
- résultat calculé ;
- correction ;
- preuve.

Une observation ne doit pas être écrasée par une nouvelle campagne.

## Journal d'événements

Exemples :

- TREE_CREATED
- DIAMETER_MEASURED
- MEASUREMENT_CORRECTED
- MARKING_CHANGED
- PLOT_COMPLETED
- CALCULATION_EXECUTED
- REPORT_GENERATED
- PHOTO_ATTACHED

Champs :

- eventId ;
- aggregateId ;
- workspaceId ;
- missionId ;
- userId ;
- deviceId ;
- timestamp local ;
- timestamp serveur ;
- operation ;
- schemaVersion ;
- payload ;
- previousVersion ;
- signature ou preuve d'intégrité.

## Synchronisation

- file locale persistante ;
- envoi idempotent ;
- accusé de réception ;
- reprise ;
- synchronisation différentielle ;
- ordre causal lorsque nécessaire ;
- gestion des conflits ;
- audit.

## Conflits

Stratégies selon le champ :

- fusion ;
- dernier validateur ;
- priorité instrumentale ;
- conflit manuel ;
- branche de données ;
- verrouillage après validation.

Les données scientifiques et juridiques sensibles ne doivent pas être fusionnées silencieusement.

## Sécurité locale

- SQLCipher ;
- Android Keystore ;
- chiffrement des fichiers sensibles ;
- protection des jetons ;
- effacement sécurisé des caches ;
- biométrie optionnelle ;
- verrouillage par politique d'organisation.

## Sécurité serveur

- TLS ;
- séparation des workspaces ;
- moindre privilège ;
- comptes de service ;
- rotation des secrets ;
- sauvegardes ;
- audit ;
- observabilité ;
- tests de restauration.

## Données non supprimables automatiquement

- observations non synchronisées ;
- preuves ;
- rapports non transférés ;
- missions actives ;
- corrections en attente.

## Provenance

Chaque donnée et résultat indique :

- auteur ;
- appareil ;
- date ;
- méthode ;
- version ;
- source ;
- état ;
- validation ;
- historique.

## Consentement et amélioration des modèles

Catégories :

- données privées ;
- données partagées dans l'organisation ;
- données de recherche ;
- données anonymisées ;
- données d'amélioration de modèle.

Aucune réutilisation pour l'entraînement sans règle, consentement et traçabilité adaptés.

## Sauvegarde et restauration

- sauvegarde locale ;
- sauvegarde serveur ;
- export utilisateur ;
- test régulier de restauration ;
- conservation versionnée ;
- politique de rétention par organisation.

## Observabilité

- métriques sans données sensibles ;
- erreurs ;
- temps de synchronisation ;
- consommation de stockage ;
- réussite des packs ;
- parité des calculs ;
- qualité TreeVision ;
- taux de corrections.
