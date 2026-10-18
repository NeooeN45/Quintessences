# Qualité et sécurité du dépôt Quintessences

État du socle : 18 octobre 2026. Ce guide décrit des contrôles techniques ;
il ne modifie ni la licence ni les droits d’accès GitHub.

## Avant de modifier ou publier

1. Lire les instructions du dépôt et vérifier `git status` et la branche active.
2. Récupérer les références distantes ; comparer les historiques avant toute fusion.
3. Conserver les changements non commités et les travaux des autres sessions.
4. Travailler sur une branche dédiée. Aucun reset destructif, force-push ou déploiement implicite.
5. Examiner le diff et ouvrir une PR avec les validations réellement exécutées.

## Contrôles reproductibles

```sh
python tools/check_source_of_truth.py
python tools/check_governance_consistency.py
python -m unittest discover -s tools/tests -p "test_*.py"
# API : depuis GSIE/API, uv sync --locked --extra dev puis contrôles de ci.yml
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
python3 .github/scripts/check_repository.py
```

Le garde analyse les fichiers **versionnés**. Les fichiers sensibles ne doivent
pas être ajoutés à Git ; les modèles `.env.example` ne contiennent que des valeurs fictives.
Les exceptions cryptographiques de test sont autorisées par chemin et SHA-256,
jamais par une exclusion globale du dossier de tests.

Le workflow `repository-security.yml` installe Gitleaks 8.30.1 depuis sa release
officielle et vérifie l’empreinte de l’archive avant exécution. Il analyse
l’historique Git disponible, avec masquage intégral des secrets détectés.
Un scan réussi ne prouve pas l’absence de toute vulnérabilité ni de toute donnée personnelle.
Aucun fichier contenant une valeur de secret ne doit être publié comme artefact de CI.

## Chaîne de confiance

- Actions externes référencées par SHA complet ; contrôle et revue à chaque mise à jour.
- Jeton Git non conservé après le checkout des jobs de vérification.
- Permissions `contents: read` par défaut ; droits supplémentaires limités aux jobs qui en ont besoin.
- Délais de jobs bornés ; exécutions obsolètes annulées.
- Dependabot propose des mises à jour ; aucune fusion ni montée majeure automatique.
- CODEOWNERS identifie le mainteneur. Il ne remplace pas une règle de protection
  de branche configurée dans GitHub ni une revue indépendante.

## Sauvegarde et confidentialité

GitHub n’est pas l’unique sauvegarde. Conserver aussi des archives chiffrées des
sources, références Git et fichiers nécessaires à la reconstruction, sur un
support indépendant ; tester leur restauration. Les clés de production et de
signature sont sauvegardées séparément, avec des droits plus restreints.

Les APK et sites publiés exposent nécessairement leur code client. Aucun secret
serveur ne doit y être embarqué. L’obfuscation n’est pas une protection absolue.
La visibilité privée protège l’accès au dépôt, pas les copies déjà diffusées.

Pour une vulnérabilité : suivre [SECURITY.md](../SECURITY.md).
