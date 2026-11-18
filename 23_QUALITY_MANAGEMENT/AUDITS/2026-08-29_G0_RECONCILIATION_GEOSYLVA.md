# Audit G0 — Réconciliation et gel du périmètre GeoSylva

| Champ | Valeur |
|---|---|
| **Identifiant** | G0-GEOSYLVA-20260829 |
| **Statut** | Draft — G0 clôturé pour la réconciliation ; G1 à G5 ouverts |
| **Date** | 2026-08-29 |
| **Dernière mise à jour** | 2026-08-30 |
| **Périmètre** | GeoSylva 3.0 → 3.1, compte Quintessences, GSIE TEST, Forge et preuves d’environnement |
| **Références** | DEC-000074, DEC-000075, DEC-000076, DEC-000077, GEO-005, `apps/GeoSylva/CLAUDE.md` |
| **Type de contrôle** | Réconciliation documentaire et inventaire technique non destructif |

## 1. Objet

Cet audit vérifie les préconditions du Gate G0 défini par GEO-005 : disposer
d’une base de travail cohérente avant d’engager une nouvelle fonctionnalité.
Il couvre l’inventaire produit, les frontières de données, l’environnement de
recette, les identités synthétiques et les modifications concurrentes.

Ce document ne valide pas GeoSylva 3.1, G2, la production ou la verticale
GeoSylva ↔ GSIE. Il ne constitue pas un avis juridique et ne remplace pas la
recette fonctionnelle sur appareil réel.

## 2. Méthode et preuves

Les éléments suivants ont été inspectés sans lire de secret et sans mutation de
base ou de dépôt :

- `DEC-000074` et `GEO-005` ;
- `README.md`, `PROJECT_MEMORY.md`, `ROADMAP.md` et `CHANGELOG.md` ;
- `apps/GeoSylva/app/build.gradle.kts` ;
- navigation, écrans, calculs, repositories, stockage local et client API ;
- `ForestryDatabase.kt` et `DatabaseMigrations.kt` ;
- statuts Git indépendants de Quintessences, GeoSylva et Forge ;
- présence du Samsung S25 Ultra par ADB ;
- disponibilité Docker et résolution de l’environnement Compose.

## 3. État exécutif

| Contrôle G0 | Résultat | Commentaire |
|---|---|---|
| Cadrage V1 documenté | PASS PARTIEL | DEC-000074 à DEC-000077 sont documentées et référencées ; les artefacts restent des documents Draft non encore livrés dans un commit dédié. |
| Matrice produit | PASS — APPROUVÉE | La matrice est approuvée par le Fondateur le 2026-08-29 comme baseline G0 ; cette approbation ne vaut pas validation G1, G2 ou production. |
| Appareil de recette | PASS | S25 Ultra détecté par ADB, GeoSylva installé et version identifiée. |
| API/base de test | PASS — RECONTRÔLÉ | Le stack `gsie-test` est sain après chargement du profil de test, reconstruction des images et application explicite des migrations `0049 → 0055`. |
| Identités synthétiques | PASS PARTIEL | La règle d’utilisation est documentée, les campagnes connues sont enregistrées sans secret ni identifiant personnel et les limites G2 restent explicites. |
| Modifications concurrentes | PASS PARTIEL | Les WIP parent, GeoSylva et Forge sont enregistrés séparément dans le registre ; ils restent hors de la livraison G0 et aucun chevauchement n’est accepté. |
| Documents Locked | PASS OBSERVÉ | Aucun chemin modifié sous `00_CONSTITUTION/` n’a été observé dans le diff courant. |

**Verdict G0 : CLÔTURÉ POUR LA RÉCONCILIATION.** La matrice est approuvée,
l’environnement de recette est opérationnel et les WIP concurrents sont
explicitement enregistrés hors de cette livraison. G1 à G5 restent ouverts et
aucune validation de production n’est déduite.

## 3.1 Recontrôle post-remédiation

Le recontrôle du 2026-08-29 a confirmé :

- `gsie-test` isolé par ports hôte temporaires, sans arrêt du stack `gsie-*` ;
- API, PostgreSQL, Redis, MinIO, Mailpit et les deux workers en état `healthy` ;
- `/health` et `/ready` répondent HTTP 200 ;
- PostgreSQL `gsie_test` expose PostGIS, AGE et pgvector ;
- revision Alembic `20260826_0055` appliquée ;
- rôle `gsie_api` non-superuser pour l’exécution applicative ;
- build Android `assembleDebug` et installation ADB au S25 rapportées par le
  Fondateur, avec conservation des données ;
- rotation d’une session expirée et purge locale sur refresh invalide intégrées
  au parcours client ;
- page native d’inscription ajoutée et refus local d’un formulaire vide prouvé.

Le recontrôle du 2026-08-29 a ensuite exécuté le scénario API réel sur deux
comptes synthétiques : création locale, acceptation et révocation de
consentements versionnés, export RGPD avec historique, vérification e-mail par
Mailpit, demande puis annulation d’une suppression différée, reconnexion sur
le même compte et isolation du compte B. Les réponses observées sont
respectivement `201`, `200`, `202` ou `503` pour Google non configuré selon le
contrat attendu ; aucun consentement n’a été injecté automatiquement.

La création API, la restauration par annulation de suppression et l’isolation
serveur sont donc démontrées. Ces éléments ne valident pas encore la connexion
Google réelle, la restauration d’une sauvegarde locale, l’isolation
multi-compte dans l’application, la purge complète ni le parcours métier G1.

## 4. Matrice produit GeoSylva

| Fonctionnalité | Entrées et persistance | Surface identifiée | État G0 | Preuve manquante avant vendabilité |
|---|---|---|---|---|
| Accueil, bienvenue et onboarding | Préférences DataStore, autorisations Android | `Welcome`, `ProfessionSelection`, `Onboarding` | Implémenté en code | Parcours complet sur S25 Ultra, interruption/reprise et vérification des autorisations |
| Compte Quintessences | API identité, session chiffrée, préférences | `Login`, `Register`, `Account`, `PasswordRecovery`, réglages compte | Fonctionnel partiel | Création réelle avec adresse de test, consentements explicites, Google, révocation, restauration, export complet et isolation multi-compte |
| Projets | Room `ProjectEntity`, `ProjectForestCrossRef` | `Projects`, `ProjectDetail` | Fonctionnel partiel | Parcours réel avec données, suppression/restauration et rattachement contrôlé |
| Forêts | Room `ForetEntity` | `Forets`, `ForestDetail`, création forêt | Fonctionnel partiel | Parcours complet et édition ; un callback d’édition reste explicitement à traiter |
| Parcelles | Room `ParcelleEntity`, file de synchronisation | `Parcelles`, création parcelle, carte, diagnostic, martelage | Fonctionnel partiel | Persistance multi-compte, sauvegarde/restauration et synchronisation réelle |
| Placettes | Room `PlacetteEntity`, sessions, tiges | `Placettes`, `PlacetteDetail`, évolution, essence/diamètre | Fonctionnel partiel | Tests terrain, relations, reprise après fermeture et validation des unités |
| Inventaire et saisie des tiges | `TigeEntity`, `TreeObservationEntity`, `MeasurementEntity` | saisie essence/diamètre, GPS, hauteur, qualité | Implémenté en code | Scénario nominal et limites comparés à des références forestières |
| Calculs dendrométriques | calculateurs Kotlin et `CalculationRunEntity` | calculateur, synthèse, martelage, évolution | Fonctionnel mais non libéré | Version, formule, unités, incertitude, valeurs impossibles et comparaison indépendante |
| Cubage et tarifs | `ForestryCalculator`, `EnhancedForestryCalculator`, `ExpertForestryCalculator`, `TarifCalculator`, `PriceCalculator` | 7 méthodes annoncées dans le README | Fonctionnel partiel | Relecture scientifique et jeu de référence reproductible par essence/méthode |
| Martelage | tiges, sessions, exports et calculs dérivés | `Martelage`, cartes et synthèses associées | Fonctionnel partiel | Modes classique/vocal/hybride, instantané rejouable, avant/après et recette terrain |
| IBP | `IbpEvaluationEntity`, `IbpEvaluationDao` | évaluation, projets, historique, comparaison, référence | Fonctionnel partiel | Relecture CNPF, cas limites, export complet et preuve sur données réelles autorisées |
| Diagnostics forestiers | station, diagnostic sylvicole, flore, habitat | menu/résultat diagnostic, station, ripisylve, classification | Fonctionnel partiel | Provenance de chaque donnée, distinction calcul/interprétation et refus des données manquantes |
| Cartographie et GPS | WKT, précision, caches, couches et tuiles | `Map`, recherche, mesures, couches, shapefile, offline | Fonctionnel partiel | CRS, précision GPS, absence réseau, tuiles hors ligne et import/export vérifiés sur appareil |
| Exports | fichiers app-privés et partage Android | PDF, CSV, XLSX, GeoJSON, Shapefile, GPX | Implémenté en code | Inventaire des données exportées, absence de secrets, restauration et contrôle des fichiers temporaires |
| Sauvegarde/import local | WorkManager, `BackupService`, `BackupWorker`, use cases | réglages sauvegarde, import/export | Fonctionnel partiel | Backup réel, restauration sans écrasement silencieux et purge complète |
| Packs et données de référence | fichiers d’application et préférences | `PackManager`, essences, tarifs, documentation | Fonctionnel partiel | version, licence, checksum et mise à jour/retrait contrôlés |
| Synchronisation parcelles | `ParcelSyncEntity`, `ParcelSyncWorker`, API dédiée | file locale et trois routes de synchronisation | Fonctionnel partiel | serveur de test actif, reprise réseau, idempotence et isolation par compte |
| Verticale GSIE | aucun nouveau contrat mobile autorisé à ce stade | future façade et station-link | Bloqué par gouvernance | validation de RFC-0041 et DEC-000073, puis tranche dédiée |

## 5. Navigation et écrans

`ForestryNavigation.kt` déclare 45 routes `Screen`, organisées autour de :

- entrée : bienvenue, connexion, récupération, sélection du métier, onboarding ;
- premier niveau : cinq onglets de navigation ;
- projets, forêts, parcelles et placettes ;
- saisie des tiges, carte, recherche, mesures et martelage ;
- IBP, diagnostics, ripisylve, classification et corrélateur ;
- réglages, compte, sécurité, tarifs, documentation et packs.

Le code contient également 415 déclarations `@Composable` sous la surface des
écrans. Ce nombre mesure des fonctions composables, pas 415 écrans distincts ;
il ne doit pas être présenté comme un nombre de fonctionnalités validées.

Une route d’exploration renvoie encore volontairement sans action pour des
catégories non raccordées. Cela confirme que la présence d’une route ou d’un
composable ne suffit pas à déclarer le parcours produit terminé.

## 6. Base locale et données persistées

### 6.1 Empreinte technique observée

- 38 déclarations Room `@Entity` ;
- 36 DAO ;
- version de base déclarée : **35** ;
- migrations déclarées de la version 1 jusqu’à 35, dont `33 → 34` et `34 → 35` ;
- chiffrement SQLCipher via une clé issue d’Android Keystore ;
- base : `forestry_counter.db`.

### 6.2 Entités Room inventoriées

| Groupe | Entités |
|---|---|
| Structure de travail | `ProjectEntity`, `ProjectForestCrossRef`, `ForetEntity`, `ParcelleEntity`, `PlacetteEntity`, `InventaireSessionEntity` |
| Inventaire | `TigeEntity`, `EssenceEntity`, `PermanentTreeEntity`, `TreeObservationEntity`, `MeasurementEntity` |
| Calculs et unités | `CounterEntity`, `GroupEntity`, `GroupVariableEntity`, `FormulaEntity`, `ParameterEntity`, `CalculationRunEntity`, `UnitEntity`, `AdvancedCalculationEntity` |
| Diagnostic et connaissance locale | `IbpEvaluationEntity`, `DiagnosticSylvicoleEntity`, `ObservationFloreEntity`, `ArbreHabitatEntity`, `EvidenceEntity`, `DataCorrelationEntity`, `DataInterpretationEntity`, `EntityRelationEntity`, `FloraFtsEntity` |
| Environnement | `StationEnvironnementaleEntity`, `StationEntity`, `RipisylveEntity`, `AlerteSanitaireEntity`, `FertiliteEssenceSerEntity`, `ProjectionClimatiqueSerEntity`, `ValeurFonciereEntity`, `GpsContextCacheEntity` |
| Synchronisation et audit local | `ParcelSyncEntity`, `EventLogEntity` |

### 6.3 Données personnelles ou potentiellement identifiantes

Les catégories suivantes doivent être incluses dans la matrice de conservation et
d’isolation :

- nom et e-mail du propriétaire forestier ;
- nom de l’opérateur ou de l’évaluateur ;
- compte propriétaire de la donnée et rattachement organisationnel ;
- noms de projets, forêts, parcelles et placettes ;
- coordonnées GPS, précision, altitude et traces WKT ;
- photographies d’arbres ou de placettes ;
- journaux d’événements et métadonnées d’appareil ;
- files de synchronisation ;
- fichiers d’export, de sauvegarde et de mesure ;
- session d’identité, qui doit rester dans le store chiffré dédié.

### 6.4 Fichiers et stockages hors Room

Les points de stockage identifiés sont :

- `DataStore` pour les préférences et états de parcours ;
- session d’identité chiffrée ;
- photos sous `getExternalFilesDir(null)/photos/{placetteId}` ;
- mesures sous `getExternalFilesDir(null)/measurements` ;
- URI d’image d’arrière-plan persistée dans les préférences ;
- sauvegardes et fichiers générés par les use cases d’export ;
- caches et files WorkManager.

La purge et l’isolation multi-compte de ces emplacements ne sont pas encore une
preuve G0 ; elles appartiennent aux recettes G1/G2 prévues dans GEO-005.

## 7. Calculs et règles scientifiques

Les points d’entrée identifiés sont :

- `ForestryCalculator` ;
- `EnhancedForestryCalculator` ;
- `ExpertForestryCalculator` ;
- `PeuplementAvantCoupeCalculator` ;
- `TarifCalculator` ;
- `PriceCalculator` ;
- `ProPricingEngine` ;
- `MartelageModels` ;
- calculateurs IBP, unités, prix et croissance.

Le principe G0 retenu est le suivant : un calcul peut être présent dans le code
sans être déclaré scientifiquement libéré. Chaque valeur devra être reliée à une
méthode, une version, une unité, une provenance et un cas de référence. Un modèle
de langage ne pourra remplacer aucune formule dendrométrique.

## 8. API et environnements

### 8.1 API déclarées côté Android

Le client Retrofit expose 36 opérations :

- 33 opérations d’identité : fournisseurs, inscription, connexion locale et
Google, liaison, refresh, logout, profil, export, consentements, e-mail,
mot de passe, suppression, sessions, MFA et vérification ;
- 3 opérations de synchronisation de parcelles : upsert, suppression et lecture ;
- sondes `health` et `ready` incluses dans l’interface d’identité.

La façade `analyse-geosylva` et le `station-link` ne sont pas encore autorisés,
car RFC-0041 et DEC-000073 ne sont pas validées.

### 8.2 Environnement API

- Docker Desktop répond en version serveur `29.6.2` ;
- `.env.test.example` charge un environnement `gsie-test` distinct avec des
  ports locaux dédiés pour la base, Redis, MinIO, Mailpit et l’API ;
- le stack `gsie-test` est sain : API, PostgreSQL, Redis, MinIO, Mailpit et les
  deux workers sont `healthy`, et l’API répond `200` sur `/health` et `/ready` ;
- `.env.test.example` et `.env.staging.example` imposent des noms de projet,
  bases et namespaces distincts ;
- un `.env.enc` existe localement, mais sa présence ne constitue pas une preuve
que Compose ou l’API de recette sont opérationnels ;
- aucun secret n’a été lu, copié ou écrit par cet audit.

**État :** l’environnement API/base de recette est démontré et opérationnel
pour la campagne de comptes du 2026-08-29. Cela ne constitue pas une preuve de
staging ou de production.

## 9. Appareil de recette ADB

| Élément | Valeur observée |
|---|---|
| Modèle | Samsung `SM-S938B` / S25 Ultra |
| Android | 16 |
| SDK | 36 |
| Package | `com.forestry.counter` |
| Version installée | `3.0.0` |
| Version code | 11 |
| Target SDK | 35 |
| ADB | état `device` |

L’identifiant ADB technique a été observé par l’outil, mais n’est pas recopié ici
pour limiter la diffusion de données d’appareil. Le profil Samsung utilisateur 150
n’est pas accessible depuis le shell ADB courant ; GEO-005 le classe hors périmètre
de cette première recette.

Cette preuve démontre la détection de l’appareil et la présence de l’APK. Elle ne
démontre pas encore le parcours métier G1, l’isolation G2 ni la production.

## 10. Identités synthétiques et conservation des preuves

Les documents de référence imposent :

- comptes de recette synthétiques et révocables ;
- comptes Google de test distincts des comptes personnels d’administration ;
- aucune adresse, mot de passe, token, code ou donnée réelle dans Git, les logs ou
les captures ;
- conservation de l’identifiant de campagne, des commits, de l’environnement, du
modèle Android, des cas exécutés, des résultats et des anomalies.

La campagne `ADB-G2-20260826-finalizer-01` fournit un exemple de campagne
synthétique et de preuve destructive bornée. Elle ne fixe pas encore à elle seule
le registre de campagne global de G0 ni les durées de conservation pour toutes les
preuves Android.

## 11. Modifications concurrentes observées

### Dépôt parent Quintessences

Le dépôt est sur `feat/schemas-de-domaine`, en avance de deux commits, avec des
modifications et fichiers non committés dans plusieurs familles :

- identité, auth, audit, object storage et contact public ;
- README, ROADMAP, mémoire et changelog ;
- décisions `DEC-000074`, `DEC-000075`, spécification `GEO-005` et audit G2 ;
- acquisition Forge côté API ;
- travaux WeatherNext/Atmos ;
- site public et documents de recherche.

### Dépôt GeoSylva

Le dépôt indépendant est sur `main` et contient des modifications non committées
sur le client identité, le repository, les modèles, la navigation, la création de
forêt, la carte/recherche et le retour haptique, ainsi qu’un artefact de mémoire
Obsidian non suivi.

### Dépôt Forge

Le dépôt indépendant est sur `master`, en avance d’un commit. Des modifications
non committées portent sur le contrat de connecteur, l’IFN, la CLI, les tests et
le nouveau handoff `gsie_acquisition`. `scratch_ifn/` reste non suivi et doit être
exclu de tout commit.

**Conclusion de contrôle :** ces travaux ne doivent pas être mélangés dans une
livraison G0 unique. Aucun fichier de code de ces WIP n’a été modifié pour
clôturer G0 ; les corrections documentaires et les rapports de cette campagne
sont tracés séparément.

## 12. Contrôles résiduels après clôture G0

### Contrôles G0 réalisés

1. Les WIP des dépôts parent, GeoSylva et Forge sont identifiés dans le
registre opérationnel et restent hors de la livraison G0.
2. L’environnement `gsie-test` est démarré avec un profil de test séparé, des
ports hôte temporaires et des secrets non committés ; `/health`, `/ready`, la
base, le namespace, les workers et les rôles ont été vérifiés.
3. La matrice est approuvée par le Fondateur le 2026-08-29 comme baseline de
réconciliation, sans validation implicite de G1, G2 ou de la production.

### Écarts documentaires hors périmètre G0

4. Le README GeoSylva a été corrigé pour annoncer Room v35 et 38 entités ;
la cohérence des autres affirmations produit reste à vérifier dans les gates
fonctionnels.
5. Le dépôt parent annonce 14 moteurs « implémentés » ; cette formulation doit
être distinguée de la vendabilité, car l’audit moteur précédent classe encore
Correlation et Forest Dynamics comme incomplets, Learning et Simulation comme
des prototypes.
6. Les affirmations de fonctionnalités GeoSylva doivent distinguer code présent,
test automatisé, preuve sur S25 Ultra et validation scientifique.

### Écarts à traiter dans les gates suivants

7. La migration Room v35 et toutes les migrations depuis la version distribuée
 doivent être exécutées sur appareil ou émulateur contrôlé.
8. La purge et l’isolation de la base, des photos, des files, des caches et des
 sauvegardes doivent être prouvées avec deux comptes synthétiques.
9. Le parcours métier complet et les calculs doivent être comparés à des valeurs
 forestières de référence avant toute annonce commerciale.

## 13. Suite après clôture G0

| Priorité | Action | Responsable proposé | Porte |
|---|---|---|---|
| 1 | Poursuivre le cœur local GeoSylva 3.0 → 3.1 : navigation, persistance, calculs, synthèses et martelage | Claude/agent Android | G1 |
| 2 | Exécuter la recette compte/RGPD : worker, restauration, purge locale et isolation de deux comptes | Codex | G2 |
| 3 | Recetter la création réelle avec adresse de test et relier explicitement les consentements versionnés | Codex + Fondateur | G2 |
| 4 | Conserver le handoff IFN et le Data Acquisition Fabric dans une tranche séparée, avec ses propres tests et preuves | Agent Forge/API | G3 |
| 5 | Ne pas implémenter la façade mobile GSIE avant validation de RFC-0041 et DEC-000073 | Fondateur | G4 |

## 14. Conclusion

G0 est clôturé pour la réconciliation du périmètre et de l’environnement de
recette. La matrice a été approuvée par le Fondateur, l’environnement `gsie-test`
a été vérifié jusqu’à la revision Alembic `20260826_0055`, le README GeoSylva a
été réaligné sur Room v35 et les WIP concurrents sont enregistrés séparément.

Cette clôture ne valide pas GeoSylva 3.1, le compte RGPD, la connexion Google,
la restauration, l’isolation multi-compte, les calculs forestiers ou la
production. G1 et G2 restent les prochaines portes opérationnelles ; G3, G4 et
G5 restent soumis à leurs preuves propres. Aucune promotion, aucun déploiement
et aucune façade mobile GSIE supplémentaire ne sont autorisés par ce rapport.
