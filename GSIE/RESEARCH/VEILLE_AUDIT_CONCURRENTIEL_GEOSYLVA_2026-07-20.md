# Veille — Audit concurrentiel GeoSylva et applications forestières comparables

| Champ | Valeur |
|---|---|
| **Type** | Veille concurrentielle / audit externe non vérifié par l'équipe |
| **Date** | 2026-07-20 |
| **Origine** | Échange conduit par le fondateur (Camille Perraudeau) via ChatGPT, versé tel quel pour traçabilité |
| **Statut** | **Affirmations non vérifiées sur le code réel de `apps/GeoSylva`** (dépôt Git externe, non audité par l'agent à la date de cette veille). À confirmer avant toute correction. |
| **Documents liés** | `apps/GeoSylva/` (dépôt externe, propre `.git`, ignoré par le repo parent) |

---

## 1. Verdict général de l'échange source

GeoSylva aurait un périmètre fonctionnel très large (inventaire,
dendrométrie, martelage, IBP, cartographie hors ligne, exports,
clinomètre, valorisation, suivi temporel) mais ne devrait pas être
positionnée comme simplement « meilleure » que les solutions
professionnelles matures. Positionnement proposé : GeoSylva comme
« système d'exploitation hors ligne du travail forestier », pas comme
liste de fonctionnalités plus longue qu'un concurrent.

## 2. Applications citées comme sources d'inspiration

| Famille | Applications citées | Avantage identifié | Idée de reprise pour GeoSylva |
|---|---|---|---|
| ONF | Marteloscope (QR code, scénarios, formation, back-office) | Simulation pédagogique de martelage | Scénarios préparés au bureau, QR/NFC arbre, mode formation avec score |
| ONF/filière | PLATEXFOR (désignation → vente → chantier → cubage → contrôle) | Chaîne complète jusqu'à la vente | Lot de bois, transmission exploitant, suivi chantier, contrôle après coupe |
| ONF grand public | Forêts en poche | Cartes/alertes géolocalisées, contenu local | Favoris, alertes territoriales, mode public distinct du mode pro |
| SIG terrain | QField, Mergin Maps, ArcGIS Field Maps | Projets configurables, formulaires, sync GNSS | Export/import GeoPackage, projet QGIS officiel, UUID stables |
| Inventaire pro | Forest Metrix, MobileMap Cruise, FScruiser | Protocoles configurables, maturité métier | Éditeur de protocole (placettes, relascope, transects, champs, formules) |
| Inventaire vision | TRESTIMA, KATAM | Photo/vidéo analysées automatiquement | Mesure assistée avec confiance affichée, jamais présentée comme vérité |
| Inventaire LiDAR/AR | Arboreal Forest | Mesure rapide par téléphone, précision publiée | Diamètre/hauteur assistés + calibration locale |
| Collecte ouverte | Open Foris Ground/Collect (FAO/Google) | Sync bidirectionnelle robuste, reprise après panne | Chef de mission, opérateurs, missions assignées, reprise après redémarrage/batterie |
| Diagnostic FR | BioClimSol, For-Eval, ClimEssences | Risque climatique/station/sol sourcé | Connecteurs réglementés, recommandations sourcées |
| Mesure bois | Timbeter, Cubabois | Cubage/piles/traçabilité matérielle | Photo-cubage, compas électronique Bluetooth |

**Non évaluable en l'état** : l'application « Désignation » elle-même
n'a pas pu être auditée précisément (pas de documentation publique
suffisante trouvée par l'échange source) — comparaison directe
impossible sans captures/documentation fournies par le fondateur.

## 3. Points signalés comme problèmes concrets sur GeoSylva

**Important : ces points sont issus d'une lecture externe du README et
du changelog publics de GeoSylva par un tiers (ChatGPT), pas d'un audit
du code par l'agent GSIE. Chacun doit être vérifié dans le dépôt réel
(`apps/GeoSylva/`) avant toute correction.**

1. **Usage de `GlobalScope`** pour la capture GPS continue hors écran
   (cité depuis le changelog) — architecture Android à risque (cycle
   de vie non maîtrisé). Remplacement suggéré : scope applicatif
   supervisé, `Service` au premier plan si acquisition persistante
   nécessaire, ou `WorkManager`.
2. **IBP potentiellement en retard sur la méthodologie CNPF** — le
   CNPF aurait publié une mise à jour v3.2 en avril 2026 (seuils et
   classification modifiés) alors que GeoSylva afficherait encore
   « IBP v3 ». À vérifier : version exacte implémentée vs v3.2
   officielle, et reformuler l'étiquette si non certifiée par le CNPF.
3. **Export GeoJSON en Lambert-93** — le standard GeoJSON (RFC 7946)
   impose WGS84 lon/lat ; les CRS alternatifs ont été retirés du
   standard. Suggestion : GeoJSON en WGS84, GeoPackage pour
   Lambert-93, métadonnées de CRS explicites.
4. **Contradiction de licence** — le dépôt annoncerait AGPL-3.0 tout
   en affichant « forks not allowed », ce qui contredit les termes de
   l'AGPL. **Point le plus prioritaire à vérifier** (implication
   légale directe) — à trancher entre AGPL réelle (forks autorisés)
   ou licence propriétaire/dépôt privé.
5. **Précision GPS potentiellement survendue** — un smartphone sous
   couvert forestier n'est pas un instrument topographique ; le terme
   « GPS de précision » pourrait être trompeur sans préciser
   HDOP/type de fix/incertitude.
6. **Tarifs et coefficients de valorisation présentés comme fixes**
   (ex. multiplicateurs A=2,5, B=1,5) sans territoire/date/source/
   version — suggestion de rendre ces grilles versionnées et
   traçables.
7. **UX potentiellement monolithique** — `MapScreen` cité à plus de
   3000 lignes, accessibilité tactile/lecture d'écran à vérifier en
   conditions terrain réelles (soleil, pluie, gants).
8. **Maturité de test à confirmer** — 420+ tests unitaires annoncés,
   mais l'échange source note l'absence mentionnée de tests
   instrumentés Android, tests de migration systématiques, tests
   longue campagne/batterie/redémarrage à grande échelle (5000-100000
   arbres).

## 4. Intégrations proposées, par priorité

1. **Paquet de mission hors ligne** (priorité 1 selon l'échange) —
   téléchargement signé avant mission (parcelles, fonds de carte,
   protocoles, référentiel essences, versions des moteurs) avec
   validation explicite « Mission prête ». Rejoint directement la
   piste « Patches scientifiques hors ligne » de
   `VEILLE_INNOVATIONS_QUINTESSENCES_2026-07-20.md`.
2. **Couche d'adaptateurs matériel Bluetooth** (compas électronique,
   télémètre laser, GNSS externe, NFC/QR) — sans dépendance à un seul
   fabricant.
3. **Mode martelage étendu** — cockpit avec objectifs sylvicoles,
   comparaison avant/après (capital résiduel, biodiversité, stabilité,
   risque sanitaire, combustible), historique complet des décisions.
4. **Connecteur Pl@ntNet/iNaturalist** — identification comme
   suggestion uniquement, jamais validation automatique (cohérent avec
   RFC-0018 déjà adopté pour Pl@ntNet, volet en ligne).
5. **Connecteurs Ignis/Hydro** — GeoSylva comme capteur territorial :
   combustible/continuité vers Ignis, ripisylves/zones humides vers
   Hydro. Hub'Eau cité comme source hydrométrique quasi temps réel ;
   NASA FIRMS/EFFIS cités comme contexte incendie non tactique
   (délai ~3h, non fiable à l'échelle locale selon la doc NASA citée).

## 5. Feuille de route proposée (indicative, non engagée)

| Horizon | Objectif |
|---|---|
| 0-6 semaines | Fiabiliser le socle : retirer `GlobalScope`, tester les migrations, corriger licence/IBP/GeoJSON/tarifs, accessibilité, sauvegarde/restauration |
| 6-12 semaines | Interopérabilité : GeoPackage, projet QGIS officiel, UUID stables, GNSS Bluetooth, paquet de mission |
| 3-6 mois | Travail en équipe : comptes/rôles, missions assignées, sync idempotente, résolution de conflits |
| 6-12 mois | Différenciation : mesure assistée vision/LiDAR, Pl@ntNet, suivi chantier, lots de bois, connecteurs Ignis/Hydro |

## 6. Ce que ce document n'est pas

- Ce n'est **pas** un audit du code réel de `apps/GeoSylva` — c'est une
  lecture externe du README/changelog public par un tiers non-GSIE.
  Chaque point du §3 doit être revérifié dans le dépôt avant action
  (le point licence en particulier est à vérifier en priorité, vu son
  implication légale).
- Aucun RFC ni décision n'est ouvert par ce document.
- Les comparatifs concurrentiels (PLATEXFOR, QField, Open Foris, etc.)
  sont basés sur la documentation publique de ces outils, non sur un
  test direct par l'équipe GSIE.
