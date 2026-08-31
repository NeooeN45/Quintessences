# Contrat d'analyse Forge → GSIE — `forge_analysis_bundle.v1`

**Date :** 2026-08-31
**Périmètre :** Forge, Data Registry et préparation d'analyse GeoSylva
**Statut :** actif pour validation hors base et tranche verticale

## Rôle

Le bundle transporte un contexte analytique déjà produit par Forge : sources
qualifiées, paramètres normalisés, features dérivées et trace de calcul. Il
permet de faire évoluer le catalogue de ressources sans ajouter une colonne
spécifique à chaque nouvelle source.

Ce contrat ne donne aucun droit d'egress. Il ne remplace pas le Data Registry,
le handoff d'acquisition ou les contrats d'observation ; il les relie par des
identifiants et des empreintes.

## Règles de validation

GSIE refuse le bundle si :

- le schéma n'est pas `forge_analysis_bundle.v1` ;
- une source n'est pas qualifiée ;
- un paramètre référence une source absente ;
- un adapter connu ne correspond pas à l'identifiant Registry ;
- SoilGrids mentionne le REST bêta ;
- une feature référence une dépendance absente ;
- le graphe des features contient un cycle ;
- un horodatage n'a pas de fuseau ;
- une valeur numérique n'est pas finie ;
- une empreinte nécessaire à la reproductibilité est absente.

Les sources inconnues peuvent être ajoutées au catalogue sans modifier ce
schéma, mais elles doivent respecter le même contrat de provenance et être
qualifiées avant consommation.

## Vérification locale ou CI

```powershell
python scripts/validate_forge_analysis_bundle.py chemin/vers/bundle.json
```

Le résultat renvoie l'identifiant de station, les compteurs de sources et de
paramètres et l'empreinte canonique. Le script n'appelle aucun fournisseur et
n'écrit pas dans PostgreSQL.

## Limite de la tranche

Cette livraison valide le paquet et son interopérabilité Forge/GSIE. Elle ne
crée pas encore un endpoint de persistance de production : l'import en base
doit rester lié à une politique d'environnement, à un profil d'analyse et à
un contrôle d'autorisation séparés.
