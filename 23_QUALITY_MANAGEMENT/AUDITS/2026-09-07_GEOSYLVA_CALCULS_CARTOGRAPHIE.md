# GeoSylva — cartographie des calculs et proposition GSIE mobile

Date : 2026-09-07. Statut : audit ciblé et architecture proposée, non validation de mise en production.
Snapshots : Quintessences `e55c369`, dépôt Android indépendant `b795b2e`, tous deux avec modifications locales. Les fichiers V2 non suivis font partie de cette photographie ; les commits seuls ne la reproduisent pas.

## Conclusion

Le problème principal est la coexistence de plusieurs chemins de calcul et l'absence de preuve de leur orchestration complète, pas le langage Kotlin. Le cubage V2 constitue un début réutilisable : entrées typées, résultats explicites, registre, qualification et tests. Une partie délègue cependant toujours aux tarifs historiques. La présence de tables, interfaces et documents ne prouve pas leur utilisation par les écrans.

Ce rapport complète GEO-005 §11 et `apps/GeoSylva/docs/MIGRATION_CUBAGE_MARTELAGE_SYNTHESE_V2.md`. Il ne crée pas de calendrier concurrent. Voir aussi l'audit `2026-09-07_GEOSYLVA_OFFLINE_SYNC_IA.md` et DEC-000087.

## 1. Stack constatée

| Couche | Existant inspecté | Conséquence |
|---|---|---|
| Android | Kotlin 1.9.23, Compose, AGP 8.2.2, Java 17 ; minSdk 26, target/compileSdk 35 ; version 3.0.0 | Inventaire, sans jugement de conformité Play ni de mise à jour des dépendances |
| Modules | `:app`, `:dem_pack`, `:capsule-verifier` | L'essentiel du métier réside encore dans `:app` |
| Persistance | Room 2.6.1, base ForestryDatabase v36, SQLCipher déclaré | Tester réellement les migrations et la récupération après interruption |
| Réseau et tâches | Retrofit 2.11, WorkManager 2.9, repositories et synchronisation parcelles | Étendre les mécanismes existants aux runs de calcul |
| Serveur | GSIE API Python, contrats et services existants | Conserver cette base ; vérifier séparément chaque route et son branchement |

Sources Android : `app/build.gradle.kts`, `gradle/libs.versions.toml`, `settings.gradle.kts`, `data/local/ForestryDatabase.kt`. Tous les chemins Kotlin ci-dessous sont relatifs à `apps/GeoSylva/app/src/main/java/com/forestry/counter/`.

## 2. Carte des chemins actuels

| Domaine | Appels / fichiers repérés | État constaté |
|---|---|---|
| Martelage et synthèse | `MartelageScreen` → `computeMartelageStats` dans `MartelageModels` → `ForestryCalculator.synthesisForEssence` → `TarifCalculator` | Chemin utilisé ; orchestration encore dans le composable, paramètres chargés au fil du calcul |
| V2 cubage | `domain/calculation/cubage/` : registre, méthodes géométriques, coefficient de forme, adaptateurs tarifs | Code et tests présents ; registre référencé par synthèse pour métadonnées, pas remplacement démontré de toute la chaîne historique |
| Tarifs | `TarifCalculatorAdapter` → `TarifCalculator` | Adaptation d'interface ; ne constitue pas une nouvelle validation scientifique des tarifs |
| Prix | `PriceCalculator.buildBreakdownWithReport` → `ProPricingEngine.calculate` ; `ForestryCalculator` → `calculateFromEntryOnly` | Deux politiques de prix manquants : fallback avec avertissement versus entrée explicite ; dépendance inverse vers un helper de PriceCalculator à démêler avant extraction |
| Diagnostic station | `StationDiagnosticScreen`, `SuperCorrelateurScreen`, `StationPdfExporter` → `StationDiagnosticEngine.diagnose(station)` | Les appels inspectés ne transmettent pas le contexte dendrométrique optionnel |
| Autre diagnostic | `DiagnosticMenuScreen` → `SylviculturalDiagnosticEngine` → repositories, scores, persistance | Autre modèle et autre pipeline ; clarifier périmètres avec StationObservation / StationEnvironnementale |
| Corrélations | `SuperCorrelateurEngine`, `domain/usecase/correlateur/CorrelationEngine` | Plusieurs responsabilités et indicateurs ; ne pas fusionner sur la seule similitude des noms |
| Calculs avancés | `AdvancedCalculationEngine`, `data/correlation/DataCorrelationEngine`, `StationExpertEngine` | Implémentations trouvées, mais pas de construction/appel direct identifié pour ces trois moteurs dans le périmètre principal recherché ; absence de référence textuelle n'est pas preuve absolue d'inactivité |
| Historique | `CalculationRunEntity`, `CalculationRunDao`, accessor de base | Schéma présent ; aucun écrivain applicatif trouvé pour cette entité par recherche des constructions/accessors |
| Synchronisation | Repository et workers parcelles ; contrats/services cubage côté serveur | Reprise parcelles existante ; parcours exécutable complet de vérification des runs non démontré, cf. audit offline |

## 3. Écarts prioritaires

### A. Erreurs transformées en absence de résultat — chemin actif

`domain/calculation/MartelageModels.kt`, dans `computeMartelageStats`, intercepte `Throwable` et remplace une synthèse en erreur par des lignes vides et des totaux nuls. Des volumes absents deviennent ensuite `0.0` dans l'agrégation. Des compteurs de complétude existent : ne pas les supprimer, mais distinguer explicitement résultat partiel, blocage et erreur. L'interception couvre aussi l'annulation coroutine. Les chargements de paramètres de `ForestryCalculator` ont également des replis silencieux.

Action : état de calcul typé propagé jusqu'à l'écran et l'export ; laisser remonter l'annulation ; bannir un zéro présenté comme volume mesuré lorsque le calcul a échoué.

### B. Run annoncé immuable mais contrat DAO mutable — branchement non prouvé

`data/local/entity/CalculationRunEntity.kt` décrit une preuve immuable ; `CalculationRunDao.kt` autorise `@Insert(REPLACE)` et `@Update`. Cela permet de modifier une preuve portant le même identifiant. Le lien observation utilise une suppression en cascade, à concilier explicitement avec suppression utilisateur et rétention.

Action : définir insertion sans remplacement, supersession par nouveau run, état de vérification séparé, politique de suppression. Brancher la sauvegarde transactionnelle du run et de l'événement à synchroniser avant de revendiquer une traçabilité réelle.

### C. Validation numérique incomplète — méthodes V2

`cubage/GeometricCubageMethods.kt` contrôle essentiellement les valeurs `<= 0`. `NaN` ne satisfait pas ce test et l'infini positif le franchit ; les data classes d'entrée n'imposent pas de finitude. Le résultat peut donc être `Valid` avec un volume non fini si cette entrée atteint directement le moteur. Constat par lecture, sans reproduction instrumentée ajoutée dans cet audit.

Action : validation de finitude des entrées et sorties, bornes métier documentées, tests NaN/infini/dépassement, unités et domaine de validité. La qualification géométrique d'une formule ne prouve pas son exactitude sur toute forme réelle de tronc.

### D. Surface oubliée dans un indicateur — helper non retrouvé dans les appels UI

`domain/usecase/station/StationDiagnosticEngine.kt:90` calcule l'espacement par `sqrt(10000 / n)` alors que la méthode reçoit `surfaceHa`. Pour un nombre d'arbres observé sur cette surface, il faudrait intégrer la densité : `sqrt(10000 * surfaceHa / n)`. Exemple arithmétique : 100 arbres sur 0,1 ha, hauteur dominante 20 m → indice 15,81 %, au lieu de 50 %. Le problème est latent dans ce helper ; les appels UI inspectés passent seulement la station à `diagnose`.

Action : qualifier le protocole d'échantillonnage, tester invariance à densité constante, puis décider du branchement dendrométrique. Ne pas annoncer un correctif utilisateur sans ce branchement.

### E. Qualification et provenance insuffisamment portées par chaque résultat

Les adaptateurs tarifs sont déclarés expérimentaux, mais un calcul réussi retourne `Valid`. Le tarif historique peut sélectionner des valeurs de repli par essence/famille ou défaut. La qualification du registre et les réserves d'une exécution doivent accompagner le résultat, l'historique et le PDF. Pour biomasse/carbone/corrélations avancées : tables, populations de calibration, incertitudes, domaine géographique et méthode statistique restent à auditer avant activation professionnelle. Des données d'entraînement exportées depuis des scores automatiques ne sont pas des vérités terrain expertes.

## 4. Architecture proposée — DEC-000088, non encore adoptée

Conserver Kotlin pour le moteur mobile et Python pour GSIE serveur. Extraire progressivement un noyau Kotlin pur indépendant de Compose, Room et du réseau, en réutilisant `cubage/`. Ne choisir Rust qu'après un profilage montrant une limite concrète et un bénéfice supérieur au coût JNI, compilation multi-ABI et maintenance.

| Responsabilité | Cible proposée |
|---|---|
| UI Compose + ViewModel | Saisie, affichage des états et réserves ; aucun choix scientifique implicite dans un composable |
| Cas d'usage mobile | Constituer un snapshot d'entrée, sélectionner méthode/version, exécuter, sauvegarder run et événement dans une transaction |
| Noyau GSIE mobile Kotlin | Fonctions déterministes, unités explicites, validation, méthodes qualifiées, incertitude et provenance ; sans dépendance Android |
| Adaptateurs données | Room durable, repositories existants, snapshots de référentiels ; cache dérivé reconstructible |
| Synchronisation | Outbox persistante, clés idempotentes, accusés, réessais avec backoff, déduplication serveur, reprise après arrêt et conflits explicites |
| GSIE Python | Autorisation, vérification comparable, calculs lourds, versions des méthodes et données ; Registry canonique, Forge publie ses handoffs |
| Identité / droits | Identité interne liée à Google, essai global de 14 jours activé explicitement, abonnement vérifié serveur, exemptions et droits entreprise ; politique hors ligne à préciser |
| IA optionnelle | Contrat indépendant du calcul déterministe ; benchmark RAM/latence/énergie, packs signés/versionnés et reprise des téléchargements ; saisie manuelle toujours disponible |

Flux cible : observation locale → snapshot → calcul local → run durable + outbox → envoi autorisé → vérification GSIE → décision versionnée → transaction locale → projection UI et notification durable. Un push est un signal de réveil, pas la source de vérité. Après un push perdu, une synchronisation suivante doit récupérer la décision.

Contrat de run à compléter dans les contrats existants : identifiant, auteur/organisation, révision des observations, hash du snapshot, versions moteur/méthode/référentiels, unités, paramètres, résultats, qualité/incertitude, horodatage, parent supersédé. La comparaison nécessite un périmètre et des versions compatibles ; un enrichissement cloud n'est pas automatiquement une erreur mobile. Les corrections de résultats ne réécrivent pas les observations terrain.

L'accès réseau et les modèles ne doivent jamais conditionner la sauvegarde terrain. Une expiration de droits hors ligne nécessite une politique explicite ; conserver l'accès aux observations et ne pas assimiler absence de réseau et absence de droit.

Références d'architecture consultées : [Android offline-first](https://developer.android.com/topic/architecture/data-layer/offline-first), [modularisation Android](https://developer.android.com/topic/modularization/patterns), [migrations Room](https://developer.android.com/training/data-storage/room/migrating-db-versions). Ces références ne valident pas les formules forestières.

## 5. Ordre de réalisation et preuves attendues

1. Figer un snapshot candidat des deux dépôts et enregistrer des cas métier représentatifs avant modification. Inventorier sources et tolérances indépendantes, pas seulement reproduire les anciens résultats.
2. Fiabiliser le cubage V2 : entrées finies, statuts, provenance, replis explicites, annulation. Extraire le noyau sans changer simultanément tous les algorithmes.
3. Basculer un parcours vertical : arbre/placette → cubage → run durable → synthèse/PDF du même run. Comparer ancien/nouveau en mode diagnostic, sans double résultat utilisateur.
4. Ajouter vérification serveur des runs et réconciliation ; démontrer pertes réseau, envoi dupliqué, arrêt après commit, réponse répétée, conflit et changement de version.
5. Étendre aux prix, station, environnement et corrélations avec qualification séparée. Ajouter photos et localisation via contrats traçables, consentement et qualité des données.
6. Intégrer droits commerciaux, migration 2.8, sauvegarde/restauration et isolation des comptes. Tester appareil réel avant mise en vente.
7. Intégrer les packs IA et la voix derrière capacités mesurées et scénario de dégradation ; modifier le contrat vocal existant avant de promettre le mains libres complet.

CI rapide sur PR : noyau, contrats, cas numériques indépendants, lint et compilation concernés. Intégration : API et vrais services Docker/Testcontainers, migrations, idempotence et isolation. E2E Android : parcours sélectionnés hors ligne/reprise/correction/export et migration. Campagnes longues planifiées : appareils, charge et endurance. Aucun seuil de durée ou performance arbitraire avant mesure du baseline.

## 6. Preuves obtenues et limites

Commande exécutée dans le dépôt Android : `./gradlew.bat :app:testDebugUnitTest --tests 'com.forestry.counter.domain.calculation.*' --offline --console=plain`.

Résultat : BUILD SUCCESSFUL, 1 min 42 s ; 23 suites JUnit, **357 tests, 0 échec, 0 erreur, 0 ignoré**. Rapports : `apps/GeoSylva/app/build/test-results/testDebugUnitTest/TEST-*.xml`. La compilation de tests a signalé notamment un overflow dans un test DataCorrelationEngine hors du filtre exécuté ; ce n'est pas un résultat d'exécution de ce test.

Cette campagne vérifie uniquement le package sélectionné. Elle ne couvre pas l'ensemble des diagnostics stationnels, la science de toutes les méthodes, Room sur appareil, les migrations, les API, Docker, Google Play, les modèles IA ni l'E2E. Le premier bootstrap Gradle a échoué en sandbox ; la relance autorisée a réussi. Aucun code métier modifié, aucun déploiement, aucune suppression des travaux en cours.
