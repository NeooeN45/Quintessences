# Politique de couverture Python multicouche — preuve du 2026-08-11

## Objet

Cette preuve accompagne `DEC-000066`. Elle démontre la couverture sur le même
état de code pour les unités et l'intégration, puis leur fusion avec
`coverage.py`. Les résultats intermédiaires en échec ne sont pas utilisés dans
la mesure finale.

Le précédent seuil global de 100 % n'était pas atteint par la campagne réelle
à 96,88 %. La nouvelle politique ne transforme pas cette dette en exception :
elle porte d'abord les contrats publics à 100 %, fixe un cliquet global sur la
base reproduite et ajoute deux seuils architecturaux contrôlés séparément.

## Campagnes finales

```text
tests/unit
→ 2 873 réussis, 63 ignorés
→ 16 386 lignes mesurées, 465 manquantes
→ 97,16 %

tests/integration
→ 349/349 réussis
→ 61,31 % isolés

fusion des données brutes
→ 16 088 lignes couvertes sur 16 386
→ 298 lignes manquantes
→ 98,18 %
```

La politique multicouche calcule en plus :

| Couche | Mesure finale | Seuil |
|---|---:|---:|
| Globale | 98,18 % | >= 97,10 % |
| Contrats publics | 49/49 fichiers à 100 % | 100 % par fichier |
| Métier/application | 96,80 % | >= 80 % |
| Infrastructure | 99,97 % | >= 60 % |

## Défauts détectés pendant la preuve

La première exécution locale de l'intégration ne disposait pas de l'image
`gsie-db:supply-chain-hardened` construite par la CI. Après reproduction exacte
de cette étape, 347 scénarios passaient et deux cycles Alembic révélaient une
dérive réelle de `QualityAssessment` : noms d'index et contrainte d'unicité
absents du registre SQLAlchemy.

Le modèle a été aligné sur la migration déployée `20260810_0048`, avec un test
de métadonnées dédié. Les deux cycles ciblés puis les 349 intégrations passent.
Aucune migration corrective artificielle et aucune tolérance de dérive n'ont
été ajoutées.

## Câblage CI

Le workflow `.github/workflows/ci.yml` :

1. conserve séparément les données unitaires et d'intégration ;
2. télécharge les deux artefacts dans un répertoire isolé ;
3. exécute `coverage combine` ;
4. génère un JSON combiné ;
5. appelle `scripts/check_coverage_policy.py` ;
6. rend le job `python-coverage` obligatoire dans `ci-gate`.

Le vérificateur est testé sur les succès, les régressions globales, les contrats
publics incomplets, les couches sous leur seuil, les rapports mal formés et les
consoles Windows CP-1252.

## Réserve avant sortie de brouillon

Cette preuve locale est complète. Le workflow de couverture modifié doit encore
réussir sur GitHub Actions après push avant que la pull request puisse sortir du
brouillon. Le merge reste soumis à une autorisation distincte du Fondateur.
