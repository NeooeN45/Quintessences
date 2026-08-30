# Handoff d'acquisition Forge → GSIE

Cette tranche implémente le passage contrôlé d'une acquisition produite par
Forge vers le Data Registry GSIE, conformément à RFC-0038.

## Responsabilités

- Forge découvre et récupère les octets avec son connecteur existant.
- Forge produit un handoff `gsie_acquisition_handoff.v1` contenant le
  `DatasetManifest` GSIE et la preuve de l'archive brute.
- GSIE vérifie le chemin de staging, la taille et le SHA-256.
- GSIE archive l'objet sous `raw/fetch/forge/` via le sink transactionnel.
- GSIE applique le manifeste existant avec `ManifestRegistryService`.

Le handoff ne crée ni `Provider`, ni Dataset Registry parallèle, ni nouvelle
base de données. Le statut initial reste `discovered` et aucune promotion
automatique vers `validated`, `staging`, `production` ou `Gold` n'est possible.

## Matrice de couverture des sources

La liste du registre juridique est contrôlée par
`gsie_api.governance.source_coverage`. Chaque source doit déclarer un état
opérationnel explicite : adapter de requête, handoff Forge, métadonnées seules,
TDM éphémère, partenaire, blocage ou absence de branchement. L'audit est sans
réseau et sans base :

```powershell
cd E:\Projets\Quintessences\GSIE\API
python scripts\audit_source_coverage.py
```

La commande doit rester bloquante tant qu'un adapter n'est pas relié à une
source autorisée. Au 2026-08-30, elle recense 23 sources et signale
`ADAPTER_WITHOUT_SOURCE_BINDING:soilgrids` : l'adapter actuel cible encore le
REST bêta interdit, alors que la voie canonique déclarée est le WCS. Cette
erreur n'autorise ni FETCH ni promotion ; elle doit être levée par un adapter
WCS qualifié, avec allowlist des couvertures, puis par une preuve d'intégration
rejouable.

## Première verticale : IFN

```powershell
cd E:\Projets\Quintessences\Forge
uv run forge scrape --source ifn --dataset derniere-campagne `
  --output-dir outputs\ifn `
  --gsie-handoff outputs\ifn\gsie-acquisition.json
```

Puis, depuis `GSIE/API`, en dry-run :

```powershell
python scripts/import_gsie_acquisition_handoff.py `
  ..\..\Forge\outputs\ifn\gsie-acquisition.json `
  --staging-root ..\..\Forge\outputs\ifn
```

L'option `--apply` archive dans le backend ObjectStorage configuré et écrit
les projections Registry dans PostgreSQL. La commande ne réalise aucun appel
au fournisseur : l'acquisition a déjà été produite par Forge.

## Garanties

- chemins relatifs POSIX uniquement, sans traversée de dossier ;
- artefact brut immuable et vérifié par SHA-256 ;
- clés de stockage déterministes, donc rejouables ;
- second passage sans réécriture d'un objet identique ;
- objet divergent refusé ;
- nettoyage de l'objet nouvellement créé si l'application PostgreSQL échoue ;
- licence et source contrôlées par le `DatasetManifest` GSIE ;
- avertissement scientifique IFN conservé dans les métadonnées et la
  description du dataset.

La transaction PostgreSQL reste sous la responsabilité du script appelant.
La suppression physique d'une donnée n'est jamais utilisée pour corriger une
divergence : une nouvelle version ou une nouvelle révision est nécessaire.
