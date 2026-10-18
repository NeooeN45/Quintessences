# Signaler une vulnérabilité

Ne publiez ni secret, ni donnée client, ni preuve exploitable dans une issue,
une pull request, une capture ou un journal public.

Utilisez **Security → Report a vulnerability** si cette fonction est disponible
sur le dépôt. Sinon, écrivez à **camille@perraudeau.mozmail.com** pour convenir
d’un canal privé. Le premier message contient uniquement le composant concerné,
la version, l’impact estimé et un moyen de vous recontacter, sans secret.
La présence de ce fichier ne signifie pas que le signalement privé GitHub est activé.

## Périmètre et traitement

Les versions en développement et distribuées peuvent être signalées.
La correction et le calendrier sont évalués selon l’impact ; aucun délai de
prise en charge ni programme de récompense n’est garanti.

Si un identifiant a été exposé : le révoquer ou le renouveler chez le fournisseur,
vérifier les accès et les journaux, puis retirer sa présence dans le code.
Effacer un fichier ou rendre le dépôt privé ne révoque pas un secret.
Une réécriture d’historique doit être préparée séparément, avec sauvegarde et
coordination des contributeurs ; elle ne supprime pas les copies externes.

## Contrôles du dépôt

- Permissions CI minimales et actions référencées par commit immuable.
- Gitleaks 8.30.1 vérifié par SHA-256 : historique Git, résultats masqués.
- Refus des fichiers d’environnement et de signature versionnés ; les rares
  fixtures cryptographiques publiques de test sont vérifiées par empreinte.
- Aucun secret de production ni donnée client requis pour les tests.
- Revue des dépendances et licences avant mise à jour ; aucune fusion automatique.

Ces contrôles ne constituent pas un audit exhaustif du logiciel ou du serveur.
Les autorisations GitHub, sauvegardes, clés de signature et traitements de
données doivent aussi être suivis hors du dépôt.
