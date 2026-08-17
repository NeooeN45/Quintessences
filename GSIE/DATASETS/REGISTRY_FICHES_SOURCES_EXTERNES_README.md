# Fiches Registry des sources externes — 2026-08-13

| Champ | Valeur |
|---|---|
| **Statut** | Draft — non appliqué à la base active |
| **Périmètre** | Sources canoniques, fiches scientifiques, services QGISIA et Treekipedia |
| **Ressources locales** | Exclues volontairement ; `E:\Documents` sera la dernière tranche |
| **Nombre de fiches** | 158 pré-fiches réparties par niveau d'intégration |

## 1. Ce que contient une fiche

Chaque entrée JSON contient le squelette minimal de qualification :

- `source_registry_id`, titre, producteur et type de ressource ;
- niveau de besoin d'intégration (`I0`, `I1`, `I2`, `I3`, `I4` ou `X`) ;
- statut Registry et mode d'ingestion ;
- distribution, méthode d'accès, URL, format et licence ;
- territoire, période et grain natif ;
- niveau de preuve, qualité et santé ;
- attribution, entraînement IA, données dérivées et redistribution offline ;
- références documentaires et blocages explicites.

Les fichiers I1 à I4 sont des **pré-fiches d'inventaire**, pas encore des
fiches juridiquement complètes. Les champs `à_qualifier` ne sont pas des
valeurs provisoires utilisables : ils signifient que la source reste
`METADATA_ONLY` et juridiquement bloquée. Le lot I0 a reçu une première revue
détaillée dans `QUALIFICATION_REGISTRY_I0_2026-08-13.md` et un manifeste
candidat séparé, non appliqué.

## 2. Fichiers par niveau

| Niveau | Fichier(s) | Contenu |
|---|---|---|
| I0 | `REGISTRY_FICHES_SOURCES_I0_2026-08-13.json` | Socle déjà consommé ou indispensable |
| I1 | `REGISTRY_FICHES_SOURCES_I1_2026-08-13.json` | Intégration métier prioritaire |
| I2 | `REGISTRY_FICHES_SOURCES_I2_*.json` | Recherche scientifique, hydro, télédétection et services QGISIA |
| I3 | `REGISTRY_FICHES_SOURCES_I3_2026-08-13.json` | Treekipedia/Silvi et ressources partenaires |
| I4 | `REGISTRY_FICHES_SOURCES_I4_2026-08-13.json` | Ressources locales différées — aucune ressource locale n'y est activée |
| X | `REGISTRY_FICHES_SOURCES_X_2026-08-13.json` | Ressources obsolètes ou remplacées, notamment Prométhée |

Les fichiers sont séparés pour éviter une application accidentelle du brouillon
à la base active. Ils ne remplacent pas `REGISTRY_MANIFEST.json` et ne doivent
pas être passés à l'application de manifeste sans décision opérateur dédiée.

Le fichier `REGISTRY_MANIFEST_I0_CANDIDATE_2026-08-13.json` respecte le schéma
du manifeste applicatif mais reste lui aussi un candidat. Sa conformité de
schéma ne constitue ni une autorisation d'application ni un droit de copie.

## 3. Garde d'intégration

```text
fiche Registry complète
    ↓
provenance et producteur vérifiés
    ↓
licence et droits dérivés vérifiés
    ↓
version, couverture, grain et schéma vérifiés
    ↓
QualityAssessment et santé
    ↓
qualification FETCH source par source
    ↓
adaptateur borné + checksum
```

Une fiche ne donne aucun droit de copie. L'entraînement IA et la redistribution
offline restent `false` tant qu'une autorisation explicite n'est pas inscrite.

## 4. Contrôles effectués

Les 158 fichiers d'entrée JSON ont été validés par lecture Python : le nombre
d'entrées déclaré correspond au nombre d'objets, et aucun fichier ne contient
de ressource locale de `E:\Documents`.

## 5. Étapes suivantes

1. ~~Corriger SCI-001 pour séparer les produits Météo-France, GBIF et IGN.~~
   Réalisé par DEC-000068, avec identités historiques fermées.
2. Exécuter l'audit SQL en lecture seule prévu par le plan de migration.
3. Faire valider puis rejouer en `dry-run` le manifeste candidat I0.
4. Ouvrir une seule source à la fois, avec décision opérateur et FETCH borné.
5. Qualifier ensuite I1 puis I2/I3 ; traiter `E:\Documents` en dernier.
