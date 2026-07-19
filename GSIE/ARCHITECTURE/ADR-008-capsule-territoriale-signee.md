# ADR-008 — Capsule territoriale signée, vérifiable hors-ligne

| Champ | Valeur |
|---|---|
| **ID** | ADR-008 |
| **Statut** | Proposé |
| **Date** | 2026-07-18 |
| **Auteur** | Camille Perraudeau (Fondateur) / Codex |
| **Décision liée** | DEC-000028 (renumeroté depuis DEC-000025 du pack d'origine — collision d'ID) |
| **Expérience de preuve** | EXP-0001 — Capsule territoriale et Golden Bench |

## Contexte

GeoSylva doit emporter sur le terrain les données, connaissances et
référentiels nécessaires à une mission sans dépendre du réseau. Un simple ZIP
permet le transport, mais ne prouve ni l'origine, ni l'intégrité, ni la
complétude des fichiers. À l'inverse, une infrastructure complète de mise à
jour sécurisée serait prématurée tant que le format de données et les budgets
mobiles ne sont pas mesurés.

La solution doit respecter l'offline-first, la provenance, la souveraineté et
la possibilité de remplacer ultérieurement l'implémentation sans casser les
contrats applicatifs.

## Options envisagées

1. **Archive ZIP et sommes SHA-256 sans signature.** Simple et portable, mais
   n'authentifie pas l'émetteur : un attaquant peut remplacer l'archive et
   recalculer les sommes.
2. **Manifeste canonique signé par Ed25519.** Portable, signatures courtes,
   vérification rapide et possible hors-ligne. Le client possède séparément
   la clé publique approuvée.
3. **Cadre complet TUF/Uptane dès le prototype.** Couvre rotation, rôles,
   expiration et protection anti-rollback, au prix d'une forte complexité
   avant validation des flux réels.

## Décision proposée

Retenir l'option 2 pour EXP-0001, avec une frontière de code permettant de
passer ultérieurement à TUF ou à un service de confiance équivalent.

### Conteneur v1 expérimental

Une capsule porte l'extension `.gsiecap` et contient :

```text
manifest.json
signature.json
payload/
  territory.json
  data/...
  knowledge/...
```

- `manifest.json` utilise un JSON canonique UTF-8 : clés triées, séparateurs
  compacts, absence de valeurs non finies.
- La signature Ed25519 porte exactement les octets canoniques du manifeste.
- `signature.json` contient l'algorithme, l'identifiant de clé et la signature
  Base64, ainsi que sa propre version de schéma ; la clé publique de confiance
  n'est jamais auto-approuvée depuis la capsule.
- Chaque fichier du payload est lié par chemin, taille et SHA-256.
- `capsule_id` est dérivé du contenu du manifeste afin de détecter les
  divergences de construction.
- `valid_until` est signé lorsqu'il est présent ; la démonstration utilise une
  validité courte de 30 jours.
- Les chemins absolus, traversées `..`, liens symboliques, fichiers en double,
  membres non déclarés et dépassements de budget sont rejetés.

### Modèle de confiance

La v1 suppose qu'une clé publique approuvée est installée avec l'application
ou distribuée par un canal distinct. L'ID de clé est l'empreinte SHA-256 de
sa représentation DER. Faire confiance à une clé contenue dans l'archive est
explicitement interdit.

### Versionnement

- Le manifeste porte `schema_version` selon SemVer.
- Un lecteur v1 refuse les versions majeures inconnues.
- Une évolution compatible ajoute des champs optionnels.
- Toute modification incompatible crée une version majeure et des fixtures
  de compatibilité ascendante/descendante.

## Menaces couvertes dans l'expérience

| Menace | Contrôle |
|---|---|
| Fichier modifié | SHA-256 + signature du manifeste |
| Manifeste remplacé | signature Ed25519 avec clé externe de confiance |
| Archive Zip Slip | validation stricte des chemins avant lecture |
| Fichier injecté | ensemble exact des membres déclaré dans le manifeste |
| Bombe ZIP simple | limites de taille, nombre de membres et ratio compressé |
| Mauvaise clé | comparaison de l'empreinte et vérification Ed25519 |

## Menaces non encore couvertes

- vol de la clé privée de production ;
- révocation et rotation de clés ;
- attaque par réinstallation d'une ancienne capsule encore valide ;
- délégation de signature par producteur ou territoire ;
- confidentialité du contenu, la capsule v1 assurant l'authenticité et non le
  chiffrement ;
- analyse antivirus des documents tiers.

Ces sujets sont des gates obligatoires avant production et motivent
l'évaluation de TUF/Uptane lors de l'itération suivante.

## Conséquences

- **Positive :** GeoSylva peut vérifier une mission sans réseau ni secret
  embarqué.
- **Positive :** le format est inspectable par Python, Kotlin et C++.
- **Positive :** le même artefact peut alimenter mobile, desktop et Hub.
- **Négative :** le cycle de vie des clés devient une responsabilité
  opérationnelle explicite.
- **Négative :** le ZIP n'est pas optimisé pour l'accès aléatoire à de très
  grands rasters ; les données volumineuses devront employer PMTiles, COG,
  GeoParquet ou Zarr à l'intérieur ou à côté de la capsule.

## Statut de suivi

| Date | Statut | Événement |
|---|---|---|
| 2026-07-18 | Proposé | ADR créé avec preuve exécutable EXP-0001 |
