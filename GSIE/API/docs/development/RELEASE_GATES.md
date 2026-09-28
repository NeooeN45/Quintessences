# Jalons produit et qualification de GeoSylva V3.1

| Champ | Valeur |
|---|---|
| Statut | Ordre demandé par le Fondateur ; critères de sortie proposés |
| Date | 2026-09-28 |
| Portée | Préparation ; aucune publication ni infrastructure créée |

## 1. Ordre de réalisation

1. **GeoSylva V3.1** : publication Google Play avec abonnement Quintessences.
   La V3.0 est la mise à niveau actuelle de l'application, selon le Fondateur.
2. **GSIE V1** : données territoriales, analyses et premières corrélations
   multi-échelles qualifiées sur un périmètre explicite.
3. **Artemis**.
4. **Ignis**.
5. **Hub**.
6. **Application de conversation environnementale**.
7. **Autres applications mobiles**.
8. **Drones avec IA**.

GeoSylva est le produit actif. Le serveur nécessaire à sa V3.1 est une dépendance
de ce premier jalon : comptes, droits, relevés, synchronisation, restauration,
abonnements et analyses promises. Le GSIE complet vient ensuite. Les versions
des applications suivantes seront définies dans leur cadrage propre.

« Fonctionnel à 100 % » signifie que tous les critères du périmètre de la
version sont satisfaits et prouvés. Une fonction décalée est retirée explicitement
de la promesse de cette version ; elle ne devient pas livrée par documentation.
La vision de simulation environnementale reste ouverte à des versions futures.

## 2. État réellement inspecté

Lecture du checkout GSIE `d7b400c` avec modifications locales préservées ;
GeoSylva lu dans `E:/Projets/Quintessences/apps/GeoSylva`, HEAD `b795b2e`,
avec de nombreuses modifications locales. Ces SHA seuls ne reproduisent pas
l'état examiné. Les copies `*-v1-server` ne sont pas retenues comme référence
sans réconciliation. Cet inventaire est ciblé, sans exécution Android ni service réel.

| Capacité | Preuve dans le code | Écart avant acceptation |
|---|---|---|
| Application terrain | Écrans de martelage/diagnostic, calculs, exports et persistance locale présents | Qualifier les parcours de V3.0, migrations et résultats métier |
| Compte mobile | Client identité et écrans présents, avec travaux locaux | Prouver inscription, connexion, récupération, sessions et changement de compte |
| Synchronisation mobile | `ParcelSyncRepositoryImpl`, WorkManager, file et états de conflit présents | Inventorier tous les objets réellement transmis ; prouver reprise et isolation |
| Synchronisation serveur | Routes et persistance de l'état courant d'une parcelle | Historique complet, arbres/relevés/médias et restauration cohérente non démontrés |
| Analyse GeoSylva | Client local appelle `api/v1/geosylva/analyses` | Aucun chemin correspondant trouvé dans le checkout serveur inspecté ; contrat à réconcilier |
| Analyse GSIE | Routes de moteurs et orchestration montées | Une analyse interne n'est pas encore un parcours zone → rapport autonome qualifié |
| Abonnement serveur | Route `billing/purchases/google-play` et `GooglePlayPurchaseGateway` présents ; mapping `quintessences_pro` | Vérification réelle, cycle de vie et droits à qualifier ; ne pas reconstruire un billing parallèle |
| Paiement Android | Recherche ciblée sans `BillingClient`/`ProductDetails` dans app et gradle | Intégration Play non établie par cette recherche ; audit complémentaire avant conclusion exhaustive |

Les modules scientifiques et leur nombre ne prouvent ni une précision
prévisionnelle, ni un fonctionnement national, ni une publication opérationnelle.
Aucun pourcentage global d'avancement n'est déduit de cet inventaire.

## 3. Portes de sortie GeoSylva V3.1

| Porte | Résultat exigé | Preuve à conserver |
|---|---|---|
| G1 — terrain | Martelage, diagnostic, calculs, cartes et exports du périmètre utilisables hors ligne | Parcours métier et résultats de référence approuvés |
| G2 — territoire | Zone choisie via référentiel ou GPS ; provenance, précision, limites et date conservées | Campagnes synthétiques sur deux parcelles ; mode hors ligne explicite |
| G3 — comptes | Compte Quintessences, récupération et isolation entre utilisateurs | Scénarios mobile/API/base et compte désactivé |
| G4 — données | Observations, arbres, campagnes, versions et médias inclus dans le contrat retenu | Matrice objet local → serveur → restauration sans perte |
| G5 — synchronisation | Reprise après coupure, doublons sans effet, conflit sans écrasement | Scénarios réseau et concurrence ; reçu après persistance |
| G6 — restauration | Après réinstallation, récupération des données promises et de leurs versions | Comparaison du manifeste et des contenus, pas seulement nombre de parcelles |
| G7 — analyse | Rapport GeoSylva correspondant au lieu et aux données, sources et limites visibles | Appel mobile réel au serveur ; résultat reproductible et indisponibilité explicite |
| G8 — abonnement | Offre Quintessences raccordée au compte ; achats validés côté serveur et droits cohérents | Achat de test, récupération, renouvellement, annulation, expiration et remboursement |
| G9 — exploitation | Préproduction, sauvegarde/restauration, supervision et reprise après incident | Rapport d'exercice et configuration identifiée |
| G10 — Play | Build de diffusion, signature maîtrisée, migrations depuis V3.0 et fiche conforme aux capacités | Validation sur appareils et piste de test Play ; critères courants de la Console vérifiés |

Choix du Fondateur du 2026-09-28 : **terrain hors ligne gratuit ; synchronisation
et analyses avec abonnement Quintessences**. Le prix, les quotas et les modalités
de récupération des données déjà stockées après expiration restent à arbitrer.
Ne pas supprimer les relevés à l'expiration
d'un abonnement. Distinguer droit d'analyse payante et droits sur les données.

La validation initiale du token Google existe côté serveur. Le cycle de vie
doit aussi être qualifié : liaison sûre au compte, absence de réattribution
d'un achat, acquittement, notifications authentifiées, rejeux et rapprochement
avec l'état Google. Vérifier notamment la différence entre annulation et fin
effective d'accès, ainsi que la période de grâce. Références officielles :
[intégration Billing](https://developer.android.com/google/play/billing/integrate),
[cycle de vie](https://developer.android.com/google/play/billing/lifecycle/subscriptions),
[notifications](https://developer.android.com/google/play/billing/rtdn-reference).

## 4. GSIE V1 après GeoSylva

Réutiliser le Data Registry et Forge. Définir un jeu de qualification : forêt
avec parcelles de deux utilisateurs, plusieurs campagnes et une correction.
Conserver toutes les versions ; agréger selon la question, sans compter deux
fois un arbre ou sommer deux inventaires successifs comme deux peuplements.

Critères : passage observation → parcelle → forêt/bassin → territoire ; période
et couverture explicites ; données publiques avec provenance et droits ;
comparabilité des protocoles ; diagnostics/rapports datés et reproductibles ;
premières corrélations avec incertitude, biais d'échantillonnage et limites
causales visibles ; retour utilisateur traçable. Une précision prédictive
supérieure exige une comparaison scientifique indépendante.

## 5. Exécution immédiate

Compléter B00 par l'inventaire GeoSylva V3.0, contrats et abonnement existants.
Rendre chaque porte G1–G10 mesurable avant de changer les migrations/API.
Codex développe le socle serveur ; Claude traite les écrans GeoSylva convenus
et leur raccordement au contrat. Le Hub et la conversation PC restent dans
leurs jalons ultérieurs. Aucun démarrage de second produit avant acceptation
ou décision explicite du Fondateur.
