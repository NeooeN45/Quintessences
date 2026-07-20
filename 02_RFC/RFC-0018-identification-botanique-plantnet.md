# RFC-0018 — Identification botanique assistée (Pl@ntNet) et extension du Botanical Engine

| Champ | Valeur |
|---|---|
| **ID** | RFC-0018 |
| **Statut** | Adopté (2026-07-20, DEC-000030 — volet en ligne §5 uniquement ; volet §6 hors périmètre) |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-20 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | Botanical Engine, GeoSylva (module identification, offline-first), métamodèle (extension satellite d'`AutecologyProfile`), `03_DECISIONS/`, `PROJECT_MEMORY.md`, `19_LEGAL/` (conditions Pl@ntNet) |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-001 (l'IA assiste, ne décide jamais), GSIE-CON-002 (science sourcée), GSIE-CON-005 (traçabilité) |
| **RFC liées** | RFC-0017 (veille, cadrage — scindé ici), RFC-0016 (schéma forestier — `AutecologyProfile`, TAXREF déjà résolu par `BotanicalEngine.resolve_taxref`), RFC-0015 (registre de modèles/licences, applicable à un modèle d'identification comme artefact) |
| **Spécification** | `05_SPECIFICATIONS/GEOSYLVA/GEO_004_IDENTIFICATION_BOTANIQUE_PLANTNET.md` (Draft — exigences fonctionnelles GEO-ID-01 à GEO-ID-16) |
| **Décision liée** | Issue de DEC-000029 (adoption du cadrage RFC-0017 et de sa scission) — ce RFC lui-même n'a pas encore de décision propre |

---

## 1. Objet

Doter GeoSylva d'une identification botanique **assistée**, jamais
autoritaire, en deux volets :

1. **Volet en ligne** — intégration de l'API Pl@ntNet via un serveur
   GSIE, avec un cycle `SUGGESTION_IA` → `VALIDEE_UTILISATEUR`.
2. **Volet hors ligne (secondaire, non prioritaire)** — étude de
   faisabilité d'un modèle embarqué spécialisé sur les essences
   forestières françaises, pour compléter l'offline-first de GeoSylva.

## 2. Ce que ce RFC ne couvre pas

- La négociation contractuelle avec Pl@ntNet/CIRAD (relève de
  `19_LEGAL/` et d'une démarche du fondateur, pas d'un livrable
  technique).
- L'implémentation du composant `gsie-ai-gateway` générique — traitée
  par RFC-0019 ; ce RFC ne spécifie que la route d'identification
  botanique, potentiellement portée par ce gateway une fois qu'il
  existe, ou en service autonome dans l'intervalle.
- L'entraînement effectif d'un modèle embarqué — ce RFC pose
  uniquement le critère de faisabilité et le principe d'architecture ;
  l'entraînement fera l'objet d'un jalon séparé si la faisabilité est
  confirmée.

## 3. Contexte et motivation

Le Botanical Engine résout aujourd'hui la taxonomie (GBIF, TAXREF) et
l'indigénat par sylvoécorégion, mais GeoSylva n'a aucune assistance à
l'identification de terrain : le technicien doit connaître l'essence
avant de la saisir. Une identification par photo, correctement encadrée
par la chaîne de décision professionnelle (RFC-0016 §3.3), comble ce
manque sans jamais remplacer le jugement du forestier — cohérent avec
GSIE-CON-001.

## 4. Principe non négociable

Une identification Pl@ntNet (ou tout futur modèle embarqué) est
**toujours** un `EvidenceStatement` de catégorie `modélisé` au sens du
passeport de décision (RFC-0016 §3.4), jamais `observé`. Elle ne peut
alimenter un cubage, une classe de fertilité, un conseil sylvicole ou
une conclusion écologique tant qu'elle n'est pas passée par la
validation humaine explicite.

## 5. Conception proposée

### 5.1 Modèle de données

Extension satellite (pas de nouvelle ontologie) :

- `BotanicalIdentificationRequest` — photos (empreinte numérique,
  organe photographié), date, position (si consentie), demandeur.
- `BotanicalIdentificationResult` — espèces candidates + scores,
  identifiants GBIF/POWO, version du moteur Pl@ntNet, famille,
  horodatage de la réponse.
- `BotanicalIdentificationDecision` — statut (`SUGGESTION_IA` /
  `VALIDEE_UTILISATEUR` / `REJETEE`), validateur, date de décision,
  justification si rejet.
- Sur validation, le résultat peut alimenter `AutecologyProfile`
  (RFC-0016) via un connecteur analogue à
  `engines/botanical/extraction_bridge.py` (déjà existant pour le
  pipeline documentaire) — même principe : jamais d'écriture directe
  sans passage humain.

### 5.2 Chaîne applicative

`GeoSylva (capture photo, jusqu'à 5 clichés) → file d'attente locale
(offline-first) → serveur GSIE (clé Pl@ntNet côté serveur uniquement,
retrait des métadonnées GPS avant envoi) → Pl@ntNet → normalisation
(GBIF/POWO/TAXREF) → 3 meilleures hypothèses affichées avec confiance
et écart → décision technicien (Confirmer / Ajouter une photo /
Identifier manuellement) → BotanicalIdentificationDecision`.

### 5.3 UI GeoSylva (exigences fonctionnelles, pas de maquette dans ce RFC)

- Afficher systématiquement les 3 meilleures hypothèses, jamais une
  seule espèce présentée comme certaine.
- Avertissement visuel explicite si l'écart de confiance entre la
  1ʳᵉ et la 2ᵉ hypothèse est faible (seuil à calibrer en phase pilote).
- Attribution des photos de référence Pl@ntNet (licence CC BY-SA)
  affichée si celles-ci sont montrées à l'utilisateur.

### 5.4 Offline-first

Capture et observation toujours enregistrées localement ; la requête
Pl@ntNet est mise en file, envoyée au retour réseau, notification à
réception du résultat. Une recherche manuelle locale (clé de
détermination texte, déjà couverte par le catalogue TAXREF existant)
reste disponible sans réseau, indépendamment de ce RFC.

## 6. Volet secondaire — modèle embarqué offline (étude de faisabilité seulement)

Non engagé dans ce RFC au-delà d'un cadrage :

1. **Préalable** — contacter Pl@ntNet/CIRAD pour savoir si une
   licence de leur modèle embarqué ou un partenariat est envisageable ;
   si oui, cela remplace tout développement interne.
2. **Si aucun accord** — faisabilité conditionnée à :
   - un jeu de données de départ : sous-ensemble Pl@ntNet-300K (CC BY
     4.0) filtré sur les essences forestières françaises prioritaires ;
   - un complément terrain : photos GeoSylva elles-mêmes une fois
     l'app en usage réel (source la plus stratégique à moyen terme,
     hors périmètre immédiat de ce RFC) ;
   - une architecture cible : modèle de vision léger (type
     MobileNetV3/EfficientNet-Lite), quantifié INT8, export
     ONNX → LiteRT pour Android ;
   - une exigence non négociable : le modèle doit pouvoir répondre
     « espèce inconnue / résultat insuffisant », jamais forcer un
     taxon du catalogue.
3. **Registre de modèle** — si un modèle embarqué est un jour entraîné,
   il doit être enregistré dans le `ModelRegistry` de RFC-0015
   (artefact, licence, domaine de validité, run de validation) comme
   tout autre modèle scientifique GSIE.

Ce volet reste `à l'étude` — aucun jalon de réalisation n'est ouvert
par ce RFC pour l'entraînement lui-même.

## 7. Alternatives considérées

- **Aucune assistance à l'identification** — statu quo possible, mais
  laisse le terrain sans aide alors que la demande est documentée
  (RFC-0017 §1.2).
- **Modèle embarqué en premier, sans passer par Pl@ntNet en ligne** —
  rejeté : nécessite un corpus qui n'existe pas encore et retarderait
  toute valeur livrée de plusieurs mois, sans bénéfice de traçabilité
  supplémentaire par rapport au volet en ligne.
- **Écriture automatique de l'essence sans validation** — rejeté sans
  discussion possible : contredit GSIE-CON-001.

## 8. Préalables avant toute implémentation

- Confirmation écrite de Pl@ntNet sur les conditions d'usage commercial
  (au-delà de 500 requêtes/jour gratuites) avant toute mise en
  production — bloquant pour un déploiement au-delà d'un prototype
  interne sous quota gratuit.
- Vérification du texte exact des licences CC BY-SA (photos de
  référence) et CC BY (observations) avant affichage dans l'UI.
- Décision fondateur (`03_DECISIONS/`) explicite avant tout
  développement, conformément à la règle §5 de `CLAUDE.md` (Draft →
  Review → Validated).

## 9. Suivi d'implémentation

**Adopté le 2026-07-20 (DEC-000030)** — volet en ligne (§5) uniquement.
Implémentation par tranches verticales, sur le modèle de RFC-0016 :

**Tranche 1/N (schéma de données) — Complète (2026-07-20).** Les trois
entités du §5.1 sont implémentées, sans aucun appel réseau vers
Pl@ntNet :

| Entité | Statut |
|---|---|
| `BotanicalIdentificationRequest` | Implémentée (nouvelle table `botanical_identification_request`) |
| `BotanicalIdentificationResult` | Implémentée (nouvelle table `botanical_identification_result`) |
| `BotanicalIdentificationDecision` | Implémentée (nouvelle table `botanical_identification_decision`), contrainte SQL empêchant une validation/rejet sans validateur et date de décision |

Fichiers : `gsie_api.infrastructure.models.identification` (nouveau),
extension de `resources/validators.py` et
`infrastructure/models/enums.py` (2 nouveaux enums :
`PlantOrgan`, `IdentificationDecisionStatus`). Registre de types
resources 86 → 89. 339 tests unitaires (279 passed + 60 skipped avant
cette tranche → 339 passed après, aucun échec).
`check_governance_consistency.py` OK.

**Reste à faire** : Tranche 2 (client Pl@ntNet côté serveur — appel
réseau réel, nécessite la confirmation écrite de Pl@ntNet sur les
conditions commerciales, préalable §8), Tranche 3 (routes serveur
GSIE), Tranche 4 (intégration app mobile GeoSylva, retrait EXIF GPS
effectif, UI des 3 hypothèses). Le §6 (modèle embarqué) reste à
l'étude, hors périmètre de DEC-000030.
