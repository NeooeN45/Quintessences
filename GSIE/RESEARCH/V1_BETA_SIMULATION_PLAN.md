# Quintessences — Plan de simulation V1 bêta

## But

Ce document définit la campagne de validation à exécuter lorsque Quintessences atteint officiellement l'état **V1 bêta**. L'objectif n'est pas seulement de vérifier que l'application « fonctionne », mais de provoquer volontairement des conditions réalistes, dégradées et adverses afin de mesurer la robustesse du système.

## Déclencheur V1 bêta

La campagne devient active dès qu'un marqueur officiel et non ambigu est présent dans GitHub, par exemple :

- release ou tag `v1.0.0-beta*` ;
- version applicative déclarée `1.0.0-beta*` ;
- document de release ou milestone explicitement marqué V1 bêta ;
- branche de release dédiée accompagnée d'un artefact bêta.

Un simple commentaire ou une intention de roadmap ne suffit pas.

## Principes

- Tests reproductibles et documentés.
- Scénarios déterministes lorsque possible, complétés par du fuzzing / property-based testing.
- Chaque échec doit fournir : entrée, contexte, logs, version/commit, comportement attendu, comportement observé.
- Toute correction d'un défaut bêta doit ajouter un test de non-régression.
- Les simulations scientifiques doivent distinguer précision numérique, stabilité, plausibilité et traçabilité des sources.

## Matrice de simulations

### 1. Charge et concurrence

- création concurrente des mêmes ressources ;
- écritures simultanées sur un même objet métier ;
- rafales de requêtes API ;
- ingestion simultanée de plusieurs sources ;
- contention PostgreSQL / Redis ;
- files de messages saturées ;
- reprise après timeout ;
- tests d'idempotence des endpoints sensibles.

Mesures : latence p50/p95/p99, erreurs, deadlocks, doublons, pertes de données, débit, saturation mémoire/CPU.

### 2. Réseau et offline-first

- perte réseau complète en cours de saisie ;
- réseau intermittent ;
- très forte latence ;
- reconnexion avec modifications concurrentes ;
- données locales anciennes ;
- reprise d'upload interrompu ;
- synchronisation après plusieurs jours offline ;
- résolution de conflits CRDT / métier.

Critère majeur : aucune donnée terrain légitime ne doit être perdue silencieusement.

### 3. Données corrompues ou incohérentes

- coordonnées invalides ;
- géométries auto-intersectées ;
- CRS incorrect ;
- unités incohérentes ;
- valeurs dendrométriques impossibles ;
- timestamps futurs / anciens ;
- fichiers tronqués ;
- doublons ;
- identifiants contradictoires ;
- métadonnées de provenance manquantes.

Attendu : rejet explicite, quarantaine ou dégradation contrôlée — jamais correction silencieuse non traçable.

### 4. Multi-tenant / RLS / sécurité

- tentative de lecture inter-organisation ;
- tentative de modification inter-workspace ;
- IDs valides appartenant à un autre tenant ;
- soft-delete puis accès direct ;
- scopes insuffisants ;
- token expiré ;
- replay ;
- mutation de paramètres d'autorisation ;
- imports contenant des références vers une autre organisation.

Critère : aucune fuite de données transversale.

### 5. Provenance et explicabilité

- recommandation sans source ;
- source supprimée / indisponible ;
- chaîne de provenance partielle ;
- données issues de plusieurs versions d'un dataset ;
- conflit entre sources ;
- preuve scientifique remplacée par une source plus récente ;
- export puis réimport d'une conclusion.

Critère : chaque résultat important doit rester retraçable jusqu'aux données et règles utilisées.

### 6. GeoSylva terrain

- inventaire de grande parcelle ;
- plusieurs centaines / milliers d'arbres ;
- campagnes longues offline ;
- import/export CSV/XLSX/PDF ;
- changements d'essence ou de protocole ;
- mesures aberrantes ;
- placettes imbriquées ;
- séries temporelles ;
- données GPS bruitées ;
- calculs de surface terrière, volumes et classes de diamètre avec cas limites.

Comparer les résultats à des jeux de référence calculés indépendamment.

### 7. IGNIS / Atmos

- changement brutal de vent ;
- données météo manquantes ;
- downscaling indisponible ;
- divergence entre sources météo ;
- propagation simulée proche d'une limite de domaine ;
- panne d'une source satellite ;
- incident avec forte densité d'événements ;
- mise à jour tardive d'une observation terrain.

Le système doit afficher clairement incertitude, âge des données et limites du modèle.

### 8. Hydro / Terra / Flora / Artemis

- crues et séries temporelles irrégulières ;
- capteurs incohérents ;
- profils de sols incomplets ;
- observations naturalistes incertaines ;
- détection d'espèce à faible confiance ;
- camera traps produisant de grandes rafales ;
- données de localisation sensibles ;
- fusion de sources hétérogènes.

### 9. GSIE Server

- redémarrage d'un nœud ;
- panne Redis ;
- panne PostgreSQL secondaire ;
- réplica en retard ;
- service dépendant indisponible ;
- partition réseau ;
- récupération après crash ;
- migrations en présence de données anciennes ;
- restauration snapshot / backup.

### 10. Hub Unreal / jumeau numérique

- forte densité d'entités ;
- streaming spatial ;
- chargement / déchargement de cellules ;
- perte du serveur d'autorité ;
- réplication avec latence ;
- incident changeant de cellule ;
- affichage de données anciennes ;
- incohérence entre état visuel et état serveur.

### 11. IA / QMF

- hallucination sur donnée absente ;
- données hors distribution ;
- changement de version d'un modèle ;
- modèle local indisponible ;
- fallback vers un autre modèle ;
- prompt injection via document ingéré ;
- réponse contradictoire avec les règles métier ;
- dérive de benchmark ;
- test de déterminisme / variance ;
- coût et latence sous charge.

Toute sortie IA à impact métier doit conserver son modèle, sa version, son contexte pertinent, sa confiance et ses preuves.

## Niveaux de campagne

### Smoke
Exécution très rapide à chaque build bêta.

### Regression
Suite complète sur fonctions critiques.

### Stress
Charge, concurrence, mémoire, saturation et longues durées.

### Chaos
Pannes volontaires de services, réseau, stockage et dépendances.

### Scientific Validation
Comparaison à des références connues et contrôle des erreurs numériques.

### Field Simulation
Scénarios réalistes de technicien terrain, DFCI, inventaire et collecte hors réseau.

## Sortie de chaque campagne

Produire un rapport comportant :

1. commit / version testée ;
2. environnement ;
3. scénarios exécutés ;
4. taux de réussite ;
5. P0/P1/P2/P3 découverts ;
6. régressions ;
7. performances ;
8. écarts scientifiques ;
9. tests manquants ;
10. décision : GO / GO AVEC RISQUES / NO-GO.

## Critères minimaux avant sortie de bêta

- Aucun P0 ouvert.
- Aucun P1 non accepté explicitement.
- Aucun défaut connu de fuite inter-tenant.
- Aucune perte silencieuse de données terrain.
- Migrations et restauration testées.
- Provenance des résultats critiques vérifiée.
- Tests de non-régression présents pour chaque défaut majeur corrigé.
- Benchmarks scientifiques documentés pour les moteurs produisant des résultats décisionnels.

Ce plan doit évoluer avec l'architecture : tout nouveau moteur ou composant critique doit ajouter ses propres scénarios avant d'être considéré comme bêta-ready.
