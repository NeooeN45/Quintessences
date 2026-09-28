# Préparer le développement du serveur Quintessences

| Champ | Valeur |
|---|---|
| Identifiant | GSIE-DEV-001 |
| Statut | Draft — préparation autorisée, services futurs non livrés |
| Version | 0.1.0 |
| Date | 2026-09-28 |
| Responsable | Camille Perraudeau ; backend Codex, frontend Claude |

## 1. Point de départ

La première livraison doit permettre à une personne de créer un compte,
enregistrer un relevé sur une zone, synchroniser ses données et retrouver
ses relevés après réinstallation, avec historique et droits vérifiables.
Le backend existant est conservé et développé progressivement.

Le présent dossier prépare l'exécution ; il ne certifie ni la production,
ni la restauration complète, ni les prévisions scientifiques. OVHcloud est
l'hébergeur envisagé par le Fondateur ; admission, crédits et ressources
effectivement disponibles restent à confirmer.

## 2. Documents à utiliser

Lire d'abord [les jalons V3.1](RELEASE_GATES.md) et
[l'inventaire B00](BASELINE_GEOSYLVA.md), qui distingue les copies locales
et GitHub. La préparation du chat PC n'est pas le lot actif.

| Document | Utilité |
|---|---|
| [Lots backend](BACKEND_WORK_PACKAGES.md) | Ordre de développement, dépendances, sorties et preuves |
| [Accord backend/frontend](CONTRACT_HANDOFF.md) | Contrats existants, futurs et règles de raccordement |
| [Brief frontend](FRONTEND_BRIEF.md) | Travail de Claude : GeoSylva V3.1 ; autres interfaces selon les jalons |
| [Préparation OVHcloud](OVHCLOUD_DEPLOYMENT.md) | Architecture candidate, compatibilité, coûts et passage en production |
| [Tableau machine](work-packages.json) | Lots et dépendances lisibles par les outils |
| [Inventaire des routes](contracts/client-existing.route-inventory.json) | Inventaire documentaire des routes ; ne permet pas de générer un client |

L’inventaire est un instantané documentaire des routes, pas un fichier OpenAPI.
Il doit être régénéré depuis l'application et comparé au code au lot B00.
Il ne contient aucun futur endpoint de restauration ou de conversation.

## 3. Démarrer avec Codex et Claude

Codex commence par [GSIE-PROMPT-0030](../../../PROMPTS/GSIE-PROMPT-0030-backend-baseline.md).
Claude commence par [GSIE-PROMPT-0031](../../../PROMPTS/GSIE-PROMPT-0031-frontend-preparation.md).
Ces missions sont préparées pour une copie locale et un seul lot à la fois.
Chaque nouvelle conversation reçoit les fichiers du lot et le snapshot réel,
avec les changements locaux nécessaires ; un ancien SHA seul ne les contient pas.

Un seul agent écrit un fichier à un instant donné. Codex possède les modèles,
migrations, routes, contrôles d'accès et contrats ; Claude possède les écrans,
leurs textes et le client réseau. Une demande de nouveau champ revient au contrat
commun avant que le client s'en serve. Le Fondateur arbitre les choix produit.

## 4. Boucle de livraison

1. Choisir le premier lot dont les dépendances sont acceptées.
2. Lire ses contrats et réconcilier le plan avec le code réel.
3. Livrer une tranche utilisable avec migration et compatibilité si nécessaires.
4. Vérifier les scénarios métier et les frontières de sécurité concernés.
5. Relire le diff, conserver les preuves et synchroniser l'état documentaire.
6. Donner à Claude le contrat, les exemples synthétiques et le statut disponible.

Une interface montrée sur données fictives reste étiquetée démonstration.
Une implémentation locale ne devient pas automatiquement un service publié.
La préparation ne nécessite aucune commande payante ni accès à des données réelles.

## 5. Références et historique

[RFC-0042](../../../../02_RFC/RFC-0042-observation-territoriale-simulation-environnementale.md),
[DEC-000075](../../../../03_DECISIONS/DEC-000075.md),
[README API](../../README.md),
[processus IA](../../../../23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md).

| Date | Évolution |
|---|---|
| 2026-09-28 | Préparation des lots et du travail partagé à la demande du Fondateur |
