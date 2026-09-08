# Quintessences — Benchmark Baseline

## Objectif

Construire une baseline reproductible pour détecter les régressions de performance avant qu'elles deviennent invisibles dans la complexité globale du projet.

Aucune valeur n'est inscrite comme baseline tant qu'elle n'a pas été réellement mesurée sur un environnement identifié. Les valeurs absentes restent **UNMEASURED**.

## Règles de mesure

Pour chaque campagne conserver :
- commit / tag ;
- date ;
- OS ;
- CPU ;
- RAM ;
- GPU si utilisé ;
- versions PostgreSQL / Redis / Python ;
- taille du dataset ;
- nombre de répétitions ;
- warm-up ;
- configuration de concurrence ;
- commandes exactes ;
- résultats bruts et synthèse.

Une comparaison n'est valide que si l'environnement ou la méthode de normalisation permet de comparer les résultats.

## Politique de régression

Seuils provisoires à réévaluer après 3 campagnes stables :
- **Alerte P2** : dégradation > 10 % sur une métrique critique répétable ;
- **Alerte P1** : dégradation > 25 % ou apparition de timeout / saturation / erreur ;
- **Blocage release** : perte de données, deadlock reproductible, fuite inter-tenant ou impossibilité de tenir la charge cible.

Un seul run anormal ne suffit pas : utiliser médiane et dispersion, puis confirmer la régression.

## Baseline API GSIE

| Métrique | Baseline | Seuil | Statut |
|---|---:|---:|---|
| Latence `/health` ASGI in-process p50 | 1,166 ms | - | 1 campagne — provisoire |
| Latence `/health` ASGI in-process p95 | 1,449 ms | - | 1 campagne — provisoire |
| Latence `/health` ASGI in-process p99 | 1,547 ms | - | 1 campagne — provisoire |
| Latence écriture simple p95 | UNMEASURED | - | À mesurer |
| Débit `/health` ASGI in-process | 830,22 req/s | - | 1 campagne — provisoire |
| Taux d'erreur sous charge | UNMEASURED | - | À mesurer |
| Temps de démarrage API | UNMEASURED | - | À mesurer |
| RSS mémoire au repos | UNMEASURED | - | À mesurer |


### BENCH-20260908-001 — `/health` ASGI in-process

| Champ | Valeur |
|---|---|
| Commit | `640998a7d03a9cf88debcefff9e766eeac558538` |
| Preuve | GitHub Actions run `34253592149`, job `api-health-baseline` réussi |
| Environnement | Linux 6.17.0-1022-azure x86_64, Python 3.12.3 |
| Méthode | ASGI in-process, sans réseau, PostgreSQL ni Redis |
| Échantillon | 100 warm-ups puis 1 000 requêtes |
| Latences | p50 1,166 ms ; p95 1,449 ms ; p99 1,547 ms ; min 1,098 ms ; max 1,831 ms |
| Débit | 830,22 req/s |
| Durée mesurée | 1,204502 s |
| RSS maximal du processus | 375,16 MiB |
| Statut | Première observation ; seuil de régression différé jusqu'à 3 campagnes comparables |

Cette campagne mesure uniquement le coût applicatif du chemin `/health`. Elle ne prouve aucune performance end-to-end, base de données, cache, réseau ou charge concurrente.

## PostgreSQL / persistance

| Métrique | Baseline | Statut |
|---|---:|---|
| INSERT resource + sous-type p95 | UNMEASURED | À mesurer |
| transaction de recommandation p95 | UNMEASURED | À mesurer |
| requêtes SQL par endpoint critique | UNMEASURED | À mesurer |
| contention sous 10 écritures concurrentes | UNMEASURED | À mesurer |
| temps migration sur dataset de référence | UNMEASURED | À mesurer |
| taille DB dataset de référence | UNMEASURED | À mesurer |

À suivre explicitement : locks, deadlocks, rollback, connexions actives, pool saturation et plans de requêtes des endpoints critiques.

## Redis / temps réel

| Métrique | Baseline | Statut |
|---|---:|---|
| round-trip cache p95 | UNMEASURED | À mesurer |
| reprise après coupure | UNMEASURED | À mesurer |
| backlog maximal soutenu | UNMEASURED | À mesurer |
| perte / doublon après retry | UNMEASURED | À mesurer |

## Ingestion / Data Ecosystem

| Métrique | Baseline | Statut |
|---|---:|---|
| objets ingérés/s | UNMEASURED | À mesurer |
| Mo/s normalisés | UNMEASURED | À mesurer |
| coût mémoire par lot | UNMEASURED | À mesurer |
| latence Bronze → Silver | UNMEASURED | À mesurer |
| latence Silver → Gold | UNMEASURED | À mesurer |
| taux de rejet données invalides | UNMEASURED | À mesurer |

## Géospatial

Scénarios de référence à figer :
1. géométrie simple ;
2. parcelle complexe ;
3. lot de 10 000 géométries ;
4. reprojection CRS ;
5. intersection / buffer / spatial join ;
6. import d'un dataset forestier de taille fixe.

Mesures : p50/p95, débit, mémoire, taille de sortie, exactitude géométrique et nombre d'objets invalides.

## GeoSylva

À mesurer dès que le chemin d'exécution automatisable est disponible :
- création d'inventaire ;
- 100 / 1 000 / 10 000 arbres ;
- calculs de surface terrière et volumes ;
- import/export ;
- synchronisation offline → online ;
- taille de base locale ;
- consommation mémoire et batterie sur campagne prolongée.

## IGNIS / Atmos / moteurs scientifiques

Deux familles de métriques doivent rester séparées :

### Performance informatique
- temps d'inférence / simulation ;
- mémoire CPU/GPU ;
- débit ;
- coût par simulation ;
- taille des données intermédiaires.

### Qualité scientifique
- erreur par rapport à une référence indépendante ;
- stabilité numérique ;
- calibration des probabilités ;
- sensibilité aux données manquantes ;
- reproductibilité avec version/modèle/dataset identiques.

Une optimisation de latence ne doit jamais être considérée comme amélioration si elle dégrade silencieusement la qualité scientifique.

## QMF / IA

À mesurer par modèle :
- temps chargement ;
- tokens/s ou unités métier/s ;
- VRAM/RAM ;
- taille poids ;
- latence p50/p95 ;
- coût API ou calcul ;
- score QEB ;
- taux de réponses non fondées ;
- stabilité entre runs.

## Format d'une campagne

```text
BENCH-YYYYMMDD-NNN
Commit:
Environnement:
Dataset:
Commande:
Répétitions:
Résultats:
Comparaison baseline:
Régression détectée: OUI/NON
Ticket associé:
```

## Priorité initiale

1. API GSIE + PostgreSQL ;
2. Recommendation Engine et chemins transactionnels ;
3. ingestion ;
4. opérations géospatiales ;
5. sync offline-first ;
6. moteurs scientifiques ;
7. QMF.

Ce document doit devenir une série temporelle de preuves, pas un tableau rempli manuellement avec des estimations.
