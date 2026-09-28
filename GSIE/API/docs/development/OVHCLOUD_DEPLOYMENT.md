# Préparation OVHcloud — GSIE-DEV-005

| Champ | Valeur |
|---|---|
| Statut | Draft — architecture candidate, aucune ressource commandée |
| Version | 0.1.0 |
| Date | 2026-09-28 |
| Hébergeur envisagé | OVHcloud Startup Program, admission non confirmée |

## 1. Choix de départ

Le premier environnement OVHcloud doit rester une préproduction privée et
réversible. Le dépôt actuel suppose une image PostgreSQL personnalisée avec
PostGIS, Apache AGE, pgvector, pgAudit et pgBackRest, plus Redis, MinIO/S3,
API FastAPI et worker outbox. Cette combinaison correspond mieux à une ou
plusieurs instances Public Cloud administrées par Quintessences qu'à un
PostgreSQL managé dont les extensions sont imposées par le fournisseur.

La documentation officielle OVHcloud consultée le 28 septembre 2026 indique
que le niveau Start fournit aux startups sélectionnées 10 000 euros de crédits
sur 12 mois et six heures d'entretien technique. Elle indique aussi que les
crédits sont destinés aux solutions éligibles et que l'admission dépend d'un
POC/MVP, d'un site fonctionnel et d'un besoin technique détaillé. Ce sont des
informations de programme, pas une attribution à HorizonOrigin.

OVHcloud liste PostGIS, pgvector et pgaudit parmi les extensions de PostgreSQL
managé, mais Apache AGE n'apparaît pas dans la liste consultée. AGE est donc
une précondition à confirmer par écrit avant de choisir cette option. Le dépôt
actuel doit rester portable vers une VM privée tant que cette réponse n'est pas
obtenue.

## 2. Architecture candidate

```text
Internet
   │
DNS + TLS + protection réseau
   │
API FastAPI (instance privée, aucun port DB public)
   ├── PostgreSQL/PostGIS/AGE/pgvector/pgAudit (volume chiffré)
   ├── Redis (rate limit, sessions, outbox, privé)
   ├── S3 Object Storage (médias et sauvegardes chiffrées)
   └── worker outbox / observabilité
```

Le site public reste séparé de l'API et des données. Claude développe contre
un contrat d'API et un jeu synthétique. Le frontend ne reçoit jamais de
connexion directe à la base ou de clé S3 permanente.

## 3. Environnements

| Environnement | Données | Exposition | Preuve avant passage |
|---|---|---|---|
| Développement local | synthétiques | localhost | migrations, tests, OpenAPI |
| Préproduction OVH | synthétiques puis pilote autorisé | accès restreint, TLS | RLS, reprise, sauvegarde hors hôte |
| Production | données autorisées | domaine public filtré | charge, alertes, restauration chronométrée, retour arrière |

Chaque environnement possède un projet, un namespace, des secrets, des buckets
et des sauvegardes distincts. Aucun volume de développement n'est réutilisé.

## 4. Déploiement progressif

1. Créer le projet OVHcloud et vérifier l'éligibilité exacte des services avant
   toute dépense.
2. Déployer une instance de préproduction avec accès SSH par clé, pare-feu,
   mises à jour, réseau privé et ports publics limités à TLS.
3. Injecter les secrets depuis Secret Manager ou fichiers protégés, jamais dans
   Git, l'image ou les logs.
4. Lancer les migrations explicitement sur une base neuve et vérifier les
   extensions réellement disponibles.
5. Configurer l'Object Storage S3 pour médias et copie hors hôte ; tester
   empreintes, liens temporaires et expiration.
6. Vérifier le parcours compte → relevé synthétique → synchronisation →
   restauration avec deux comptes et deux appareils simulés.
7. Mesurer mémoire, CPU, stockage, transfert, temps de requête et coût avant
   toute mise à disposition réelle.

## 5. Sauvegarde et continuité

Le dépôt local pgBackRest n'est pas une protection suffisante contre la perte
de l'instance. Activer un second dépôt Object Storage, vérifier le chiffrement,
la rétention et la récupération des clés. Tester une restauration isolée qui
compare schémas métier, relevés versionnés, manifests et empreintes médias.
RPO et RTO restent des mesures à obtenir ; les cibles documentées dans le dépôt
ne sont pas des garanties OVHcloud.

Le profil applicatif HA ne crée pas une haute disponibilité complète lorsqu'il
partage le même hôte, la même base et le même Redis. Une architecture multi-AZ
sera une décision séparée après mesure de charge et de budget.

## 6. Compatibilité OVHcloud à demander

Avant sélection d'un service managé, obtenir une réponse écrite sur :

- version PostgreSQL et disponibilité de PostGIS, pgvector, pgAudit et AGE ;
- extensions ou fonctions nécessaires au schéma et à l'orchestration ;
- sauvegarde, restauration à un instant, rétention et export hors service ;
- réseau privé, TLS, rôles, paramètres RLS et logs sans données sensibles ;
- régions, localisation des données, quotas, coûts et évolution des crédits ;
- Object Storage, versioning, réplication et suppression protégée.

Sans réponse positive pour AGE ou sans nécessité de ce composant, deux voies
restent possibles : garder PostgreSQL complet sur VM privée, ou adapter une
version managée à l'architecture GSIE après décision tracée. Aucun choix n'est
automatique.

## 7. Références et historique

[Startup Program OVHcloud](https://startup.ovhcloud.com/fr/startups/),
[FAQ du programme](https://startup.ovhcloud.com/fr/faq-support/),
[produits éligibles](https://docs.ovhcloud.com/fr/guides/account-and-service-management/startup-program/available-products),
[extensions PostgreSQL managé](https://docs.ovhcloud.com/en/guides/public-cloud/databases/postgresql-extensions),
[Object Storage S3](https://docs.ovhcloud.com/fr/guides/storage-and-backup/object-storage/s3-location).

| Date | Évolution |
|---|---|
| 2026-09-28 | Architecture candidate et questions de compatibilité préparées |
