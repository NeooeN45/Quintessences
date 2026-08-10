# Qualification FETCH SoilGrids — 2026-08-10

## Décision

**FETCH reste fermé.** La licence des produits SoilGrids est annoncée CC BY
4.0 par ISRIC, ce qui confirme la base juridique déjà enregistrée dans
SCI-001 sous réserve d'attribution. La voie technique actuelle de l'adapter,
l'API REST v2.0, est toutefois officiellement en pause, en bêta, sans garantie
de disponibilité et limitée par une politique d'usage équitable.

GSIE ne doit donc pas activer FETCH sur `rest.isric.org`. ISRIC recommande WCS
pour obtenir des sous-ensembles raster et WebDAV pour les cartes complètes.
Les cartes complètes atteignent environ 5 Go chacune et une propriété complète
environ 120 Go : elles sont hors du périmètre du premier worker borné.

## Contrat technique fermé, encore non activé

- service : WCS uniquement ;
- endpoint fixe : `https://maps.isric.org/mapserv` ;
- version : WCS `2.0.1` ;
- format : `GEOTIFF_INT16` / `image/tiff` uniquement ;
- borne GSIE : 8 MiB et 1 000 000 pixels natifs de 250 m ;
- CRS d'entrée et de sortie : EPSG:152160 (Homolosine SoilGrids) ;
- timeout : 30 secondes ;
- concurrence initiale : une opération par worker ;
- checksum local : SHA-256 ;
- attribution CC BY 4.0 obligatoire dans les droits et l'actif.

Le contrat code les allowlists suivantes :

- propriétés : `bdod`, `cec`, `cfvo`, `clay`, `nitrogen`, `ocd`, `phh2o`,
  `sand`, `silt`, `soc`, `wv003`, `wv1500` ;
- profondeurs : `0-5cm`, `5-15cm`, `15-30cm`, `30-60cm`, `60-100cm`,
  `100-200cm` ;
- sorties : `Q0.05`, `Q0.5`, `mean`, `Q0.95`.

`ocs` est exclu du premier périmètre car ses intervalles de stock ne suivent
pas tous le contrat standard à six profondeurs. La requête est structurée :
aucune URL, query, map ou couverture arbitraire n'est acceptée.

Ces bornes sont des limites GSIE prudentes, pas des limites publiées par
ISRIC. `fetch_enabled` demeure `false` jusqu'à décision opérateur et sonde TLS
réussie.

## Effet sur QualityAssessment

La documentation officielle permet de caractériser la résolution native de
250 m et l'existence d'intervalles d'incertitude, mais elle ne démontre pas à
elle seule l'exactitude positionnelle, temporelle ou thématique d'un extrait
concret. Aucun run complet n'est persisté et aucune promotion n'est autorisée.

## Vérification du service réel

La documentation officielle confirme WCS, les 24 combinaisons usuelles par
propriété, `GEOTIFF_INT16`, EPSG:152160 et les identifiants de couverture.

Après désactivation de l'interception antivirus, la sonde réelle
`DescribeCoverage` réussit avec validation TLS normale : HTTP 200, XML WCS
2.0, couverture `bdod_0-5cm_mean`, EPSG:152160, résolution 250 m et grille
globale `159242 × 58033`. TLS n'a pas été désactivé ou contourné.

La vérification des douze propriétés a toutefois révélé une divergence du
service réel : onze identifiants `*_0-5cm_mean` sont valides, tandis que
`/map/wv003.map` retourne une page MapServer « Unable to access file » sous
HTTP 200. Le serveur expose à la place `/map/wv0033.map`, avec 30 couvertures.
La documentation métier continue d'employer `wv003` pour la teneur en eau à
33 kPa. Le contrat GSIE distingue désormais explicitement le code métier
`wv003` du code d'accès WCS `wv0033`. `wv0033` reste refusé comme propriété
métier indépendante ; les onze autres propriétés conservent un mapping
identité. Le contrat produit `wv0033_0-5cm_mean` et `/map/wv0033.map` sans
autoriser de couverture arbitraire.

La correction contractuelle est couverte par les tests et la campagne élargie
compte **99 tests passants**. À ce stade de la qualification, FETCH restait
fermé et aucun `GetCoverage` n'avait encore été exécuté.

## Premier micro-extrait autorisé

Le Fondateur a ensuite autorisé explicitement, par DEC-000061, un unique
`GetCoverage` `bdod_0-5cm_mean`. L'emprise représente 100 pixels estimés,
largement sous le plafond de 10 000. Le flux reçu est un `image/tiff` de 569
octets, avec le SHA-256
`a6fd8b120b11e64612cdf3ee22854d8db28413cbe7bd480291cfb203ee24840e`.

Le DataAsset RAW unique `a584c377-ff39-4e58-967a-7304b732bb47` est publié dans
MinIO sous `s3://gsie-assets/raw/fetch/soilgrids/a584c377-ff39-4e58-967a-7304b732bb47.tif`.
Le round-trip MinIO est identique octet pour octet. La version Registry reste
`discovered` et aucune promotion automatique n'a eu lieu. FETCH canonique
reste fermé.

## Récepteur borné préparé

Le worker sait recevoir un flux autorisé sans le charger en mémoire. Par
contrat, le worker seul produit un reçu et ne crée pas implicitement de
`DataAsset` :

1. qualification et capacité FETCH avant réseau ;
2. endpoint et limites de requête ;
3. timeout global incluant adapter, lecture et destination ;
4. contrôle du MIME et de `Content-Length` avant lecture ;
5. comptage réel de chaque chunk avec arrêt au premier octet excédentaire ;
6. SHA-256 calculé pendant le streaming ;
7. comparaison du checksum attendu lorsqu'il existe ;
8. `commit()` de la destination uniquement après succès complet ;
9. `abort()` sur MIME, taille, chunk, vide, checksum, timeout ou exception.

Le reçu du worker contient seulement taille, SHA-256 et MIME. Avant
DEC-000061, aucun DataAsset n'avait été créé. Depuis l'autorisation unique, un
seul DataAsset RAW a été publié explicitement après validation du reçu. Aucun
autre DataAsset n'a été créé, aucune promotion n'a été déclenchée et le
registre canonique SoilGrids reste fermé.

Validation : 36 tests ciblés adapter/FETCH/WCS/resolver/qualité passants,
Ruff propre, mypy strict propre sur 19 fichiers et smoke Docker sans réseau.

Avant DEC-000061, le sink MinIO transactionnel et le timeout d'abandon avaient
été prouvés sans connexion SoilGrids. DEC-000061 prouve désormais l'unique
chaîne fournisseur → sink → MinIO → DataAsset. Cela ne change pas la décision
canonique : `fetch_enabled` reste `false`.

## Sources officielles

- https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html
- https://docs.isric.org/globaldata/soilgrids/index.html
- https://docs.isric.org/globaldata/soilgrids/wcs.html
