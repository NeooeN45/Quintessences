# GeoSylva — examen offline-first, synchronisation et IA locale

| Champ | Valeur |
|---|---|
| Date | 2026-09-07 |
| Statut | Revue ciblée de code ; contrats proposés, sans preuve E2E |
| Périmètre | GeoSylva Android et API GSIE, fichiers locaux en cours de développement |
| Autorité produit | DEC-000087 ; GEO-005 reste le plan d'exécution |

## 1. État réellement observé

| Capacité | Preuve dans le dépôt | Limite |
|---|---|---|
| Calcul cubage local | `domain/calculation/cubage/`, `CubageMethodRegistry.kt` ; référence aux métadonnées dans `MartelageSynthesisTab.kt` | La référence au registre ne prouve pas l'exécution de toutes les nouvelles méthodes depuis l'interface |
| Diagnostic embarqué | `domain/diagnostic/SylviculturalDiagnosticEngine.kt`, `EssenceSuitabilityScorer.kt` | Existence de code ; exactitude scientifique et parcours appareil non recettés ici |
| Reprise réseau parcelles | `ParcelSyncRepositoryImpl.kt`, `ParcelSyncWorker.kt`, `ParcelSyncDao.kt` | WorkManager avec contrainte réseau et backoff ; périmètre parcelles, pas une preuve de synchronisation de tous les calculs/photos/placettes |
| Fusion serveur | `mergeFromServer`, états de conflit et protection des modifications locales dans le repository | La résolution scientifique et l'invalidation des synthèses ne sont pas démontrées |
| Contrat cubage | RFC-0042 et `GSIE/API/docs/GEOSYLVA_CUBAGE_OFFLINE_FIRST_V1.md` | Les routes cubage annoncées ne sont pas trouvées dans les routeurs de `GSIE/API/src` |
| Vérification cubage | `geosylva/cubage_service.py` conserve et relit le paquet | `verification=None` et `server_verification_id=None` : aucun recalcul serveur fourni par ce service |
| Packs | `domain/usecase/pack/PackManager.kt` | Téléchargement HTTPS/checksum, reprise partielle ; packs territoriaux, pas preuve d'un installateur IA signé et qualifié |
| Benchmark et runtime IA | Recherche ciblée dans `app/src/main` | Aucun benchmark matériel ou chargement ONNX/LiteRT/Vosk/Whisper trouvé ; absence non certifiée au-delà du périmètre recherché |
| Voix | `SettingsHomeScreen.kt` utilise `RecognizerIntent` | Recherche dans les réglages ; ni saisie forestière structurée ni garantie hors ligne |
| Entraînement futur | `DiagnosticTrainingDataExporter.kt` exporte features et scores comme labels | Des scores produits par les règles ne sont pas des annotations expertes indépendantes |
| Architecture IA | RFC-0034 adoptée, incluant RAG, packs et voix | Les choix et latences documentaires ne constituent pas des performances prouvées sur téléphone |

Chemins Android ci-dessus relatifs à
`apps/GeoSylva/app/src/main/java/com/forestry/counter/`.
Recherche et lecture uniquement ; aucun test Android, serveur Docker ou modèle exécuté.

## 2. Flux cible proposé

```text
mesures / photos / localisation
  → validation locale et stockage durable
  → calcul local versionné → résultat immédiatement consultable
  → file d'envoi durable
  → GSIE vérifie le paquet et recalcule quand la comparaison est possible
  → événement de vérification récupérable même si le push est perdu
  → contrôle du compte, de l'objet et de la révision
  → transaction locale : correction + historique + invalidation des dérivés
  → synthèses et cache reconstruits → information utilisateur
```

La base locale et les fichiers durables sont la source de lecture de l'interface.
Un cache effaçable ne doit jamais être l'unique copie d'une mesure ou d'un calcul.
Le serveur garde le registre scientifique distant ; les deux rôles ne s'opposent pas.

### 2.1 Synchronisation et correction

- Identifiants stables par compte/organisation, placette, observation et calcul ;
  révision, unités, méthode/version, paramètres, sources et empreintes conservés.
- Enregistrement métier et mise en file dans la même transaction lorsque possible ;
  références de photos validées par manifeste et transfert reprenable.
- Livraison répétable avec effet idempotent ; accusé de réception durable,
  retries bornés et backoff, reprise après fermeture/redémarrage et panne serveur.
- Une vérification cible un calcul précis et sa révision. Une réponse ancienne
  ne peut pas écraser une modification plus récente ni les données d'un autre compte.
- Même méthode et entrées comparables : écart au-delà des tolérances scientifiques
  explicites → correction justifiée. Nouvelle méthode ou données différentes :
  résultat versionné distinct, pas déclaration automatique d'erreur terrain.
- Mesure brute contestée : conserver l'original et demander une revue ; aucune
  valeur déduite par une IA ne devient silencieusement une mesure observée.
- Correction prouvée d'un résultat dérivé : nouvelle version courante, ancien
  résultat conservé, recalcul des synthèses dépendantes et invalidation du cache.
- Conserver le rapport avant/après, motif, méthode, auteur/service, date et sources.
  L'application peut expliquer pourquoi la valeur affichée a changé.

### 2.2 Information utilisateur

Journal durable dans l'application pour chaque vérification terminée : conforme,
corrigée, à revoir, non comparable ou bloquée ; états de reprise visibles.
Notification Android si autorisée, dédupliquée par identifiant d'événement.
Si la permission est refusée ou le push perdu, récupération par synchronisation
et affichage dans l'application au prochain accès. Ne pas promettre un push
immédiat garanti lorsque le téléphone n'est pas joignable.

## 3. Socle mobile et packs IA

Le socle embarqué couvre les fonctions terrain déclarées, avec calculs
déterministes et méthodes vérifiées, sans dépendance à un modèle téléchargé.
L'IA enrichit les hypothèses, corrélations et synthèses ; ses résultats restent
identifiés comme inférences, avec provenance, version et limites.

### 3.1 Sélection sur le téléphone

Benchmark initial court et borné : mémoire disponible et pic mémoire réel,
stockage, latence sur un échantillon, compatibilité runtime/accélérateur,
échauffement et impact batterie. Aucun seuil ni modèle n'est choisi sans mesure.
Un premier lancement hors réseau doit rester utilisable et reporter les packs.

Deux étapes évitent un téléchargement massif avant de connaître le matériel :
sonde embarquée légère, puis essai du pack candidat avant son activation.
La sélection est propre à chaque capacité : un téléphone peut accepter la voix
mais pas le modèle d'analyse. Repli vers le socle si manque de mémoire,
chaleur excessive, échec de chargement ou incompatibilité.

Réutiliser le gestionnaire existant en l'étendant : manifeste signé, hash,
version, taille, runtime, compatibilité de schéma, provenance d'entraînement,
validation scientifique et capacité requise. Téléchargement reprenable,
activation atomique, dernière version fonctionnelle conservée pour retour arrière.
Le téléchargement ne doit pas bloquer l'utilisation terrain.

### 3.2 Qualité de l'IA

Comparer chaque modèle à la méthode locale sans IA, sur des placettes de test
indépendantes et relues, avec séparation des sites/dates pour éviter les fuites.
Évaluer erreurs, calibration, données manquantes et capacité à s'abstenir.
Un modèle n'est activé que si les gains et les limites sont établis.
Les scores exportés par le moteur actuel peuvent servir à une distillation,
mais ne prouvent pas une amélioration scientifique sur ce même moteur.
L'utilisation de données terrain pour entraînement doit être explicitement cadrée.

## 4. Saisie vocale terrain

Évaluer un petit moteur de transcription locale et un parseur métier borné :
essence, diamètre, hauteur, unité et objet cible. Le modèle d'analyse et le
modèle vocal sont distincts ; aucun gros modèle génératif n'est requis par principe.

Exemple : « chêne, diamètre trente-deux centimètres, hauteur dix-huit mètres »
→ champs structurés → contrôles d'unités/plausibilité → relecture et validation.
Une ambiguïté comme « treize/trente » ou une unité absente exige clarification.
Prévoir correction et annulation vocales, bruit du vent, micro/casque et pauses.

RFC-0034 exige actuellement une confirmation visuelle. Un parcours entièrement
mains libres doit donc faire préciser ce contrat : confirmation orale des mesures
non ambiguës proposée, opérations sensibles toujours protégées selon leur contrat.
Ne pas supposer que l'appel vocal Android existant est local : vérifier le moteur
et le mode hors ligne sur l'appareil. Audio brut éphémère selon RFC-0034.

## 5. Ordre d'exécution dans GEO-005

1. Brancher et prouver un calcul local avec persistance et reprise après arrêt.
2. Exposer le contrat cubage existant, vérifier le calcul côté serveur et
   prouver l'idempotence PostgreSQL, les conflits et l'isolation.
3. Ajouter la réconciliation versionnée, le recalcul des dépendances et le
   journal/notifications ; recette réseau coupé et messages réordonnés.
4. Benchmark matériel et installation d'un pack de test signé sans activer
   de modèle scientifique non qualifié.
5. Évaluer séparément voix métier et modèle d'analyse, puis qualifier leur diffusion.

Critères bloquants : zéro perte de mesure après redémarrage, aucune application
de correction au mauvais compte/objet/révision, pas de doublon après réponse perdue,
app fonctionnelle sans pack, pas de promotion d'une hypothèse IA en observation.
Tester aussi crash pendant application d'une correction, notification refusée,
disque plein, pack corrompu et migration d'une base locale 2.8 synthétique.

## 6. Sources et liens

- [DEC-000087](../../03_DECISIONS/DEC-000087.md)
- [RFC cubage](../../02_RFC/RFC-0042-contrat-offline-first-cubage-geosylva-gsie.md)
- [RFC IA mobile](../../02_RFC/RFC-0034-ia-forestiere-on-device.md)
- [GEO-005](../../05_SPECIFICATIONS/GEOSYLVA/GEO_005_V1_PILOTAGE_GEOSYLVA_GSIE.md)
- [Architecture Android offline-first](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [Reconnaissance vocale Android](https://developer.android.com/reference/android/speech/SpeechRecognizer)
