# Audit API GSIE ↔ GeoSylva — 2026-08-13

## Verdict

La chaîne serveur est appelable et vérifiée ; l'intégration mobile de cette
chaîne n'est pas encore ouverte. Cette séparation est saine : GeoSylva ne doit
pas fabriquer un contrat réseau incomplet ni présenter une recommandation
serveur non validée.

## Preuves serveur

- 33 tests de routeurs API passants sans base réelle ;
- 4 tests HTTP orchestration passants sur PostgreSQL réel ;
- 2 929 tests unitaires backend passants après correction des fixtures de
  cloisonnement et réalignement des tests WebSocket sur le sous-protocole JWT ;
- la réponse `POST /api/v1/orchestration/analyse` expose `analyse_id` ;
- `analysis_run` est relu dans la même base de test avec les quatre sorties
  intégrales : Reasoning, Diagnostic, Recommendation et Validation ;
- migration 0049 vérifiée par upgrade/downgrade/upgrade et comparaison du
  schéma SQLAlchemy (2 tests passants, seulement les avertissements PostGIS
  déjà connus sur les types AGE).
- le trigger PostgreSQL `analysis_run_append_only` est présent et interdit les
  mutations UPDATE/DELETE ; sa présence est contrôlée par la campagne de
  migration réelle.

## État GeoSylva

Les clients Retrofit existants sont :

- identité locale/Google via `IdentityApiService` ;
- synchronisation des parcelles via `ParcelSyncApiService` ;
- client HTTP sécurisé qui refuse les URL distantes non HTTPS et limite le
  mode local au debug.

Aucun service Kotlin ne consomme encore `/api/v1/orchestration/analyse`.
Cette absence est explicite : l'application utilise ses moteurs locaux et ne
peut donc pas encore demander une analyse serveur complète depuis une fiche.

La suite de tests JVM GeoSylva a terminé avec `BUILD SUCCESSFUL`.
Six avertissements Kotlin de tests restent documentés (paramètres nommés des
fakes, overflow volontaire/non borné, variable inutilisée et API temporaire
dépréciée) ; ils ne sont pas masqués par un seuil abaissé.

## Porte d'intégration suivante

Avant d'activer l'appel mobile :

1. versionner les DTO Kotlin sur le schéma `AnalyseRequest`/`AnalyseComplete` ;
2. ajouter `OrchestrationApiService` derrière le même client HTTPS ;
3. conserver la requête et `analyse_id` dans une file Room idempotente hors
   ligne ;
4. n'afficher une recommandation que si `validation.statut` est acceptable et
   que le niveau de preuve est visible ;
5. tester une réponse serveur réelle sur l'environnement de test GeoSylva,
   sans jamais faire pointer l'APK debug vers production.

Aucune ingestion, promotion, activation FETCH ou décision sylvicole ne découle
de cet audit.
