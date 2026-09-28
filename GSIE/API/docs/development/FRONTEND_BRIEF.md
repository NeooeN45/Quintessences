# Brief frontend pour Claude — GSIE-DEV-004

| Champ | Valeur |
|---|---|
| Statut | Draft — brief de préparation |
| Version | 0.1.0 |
| Date | 2026-09-28 |
| Agent principal | Claude |

## 1. Mission

Priorité du Fondateur : finir **GeoSylva V3.1** pour Google Play avec abonnement
Quintessences. V3.0 désigne la refonte actuelle. Claude reprend les écrans de
l'application existante et leurs états, sur une copie dont les modifications
locales sont préservées. Les parcours génériques ci-dessous servent GeoSylva ;
le site est secondaire et la conversation PC vient après GSIE, Artemis, Ignis
et Hub. Lire [les portes de sortie](RELEASE_GATES.md), en particulier G8.

Préparer le frontend Quintessences autour des états et contrats réellement
disponibles. L'interface doit aider une personne à comprendre ce qui est
enregistré, synchronisé, en conflit, restauré ou analysé. Elle ne doit pas
faire croire qu'une fonction planifiée existe déjà.

Le travail peut avancer avec des données synthétiques et sans accès à une base
privée. Il doit rester remplaçable quand les contrats B02 à B06 seront livrés.

## 2. Parcours à construire dans l'ordre

1. **Accueil et orientation** : présenter GeoSylva, GSIE, le Hub et la future
   conversation PC avec leur état réel.
2. **Compte** : inscription, connexion, activation e-mail, récupération,
   MFA, sessions et déconnexion. Prévoir les réponses de défi MFA et les
   erreurs anti-énumération.
3. **Espace terrain** : liste personnelle, sélection d'une zone, état hors
   connexion, file de synchronisation et conflit explicable.
4. **Historique** : afficher version, auteur, dates, source géographique,
   correction et suppression logique quand le contrat backend le permettra.
5. **Rapport** : afficher question, période, données utilisées, sources,
   incertitudes et validation humaine. Les résultats simulés portent leur statut.
6. **Abonnement Quintessences dans GeoSylva** : présenter les offres réellement
   définies, achat/restauration, droits reçus du serveur et états de paiement.
   Aucun droit payant ne dépend d'un indicateur contrôlé uniquement par le client.

### Jalon ultérieur, exclu de la mission GeoSylva V3.1

La conversation PC sera construite après GSIE, Artemis, Ignis et Hub, au lot
B10 : question, contexte de zone, outils, citations et résultats partiels.

## 3. Contraintes d'interface

- Une zone peut avoir plusieurs sources et versions ; afficher l'origine et la
  précision plutôt qu'un libellé unique ambigu.
- Les données hors ligne sont clairement séparées des données confirmées par le
  serveur.
- Une synchronisation partielle permet de reprendre ; elle ne remplace pas les
  objets manquants par une liste vide.
- Une erreur de droit, de réseau, de quota ou de conflit possède un message et
  une action de récupération distincts.
- Les cartes et coordonnées précises restent masquées tant que le serveur ne
  les autorise pas.
- L'accessibilité clavier, le contraste, les états de chargement et l'usage
  mobile restent testables sans données réelles.

## 4. Données de démonstration

Utiliser uniquement un jeu synthétique versionné dans le projet frontend :
une forêt A avec deux parcelles, deux utilisateurs, deux campagnes, une
correction et un média. Marquer l'interface « démonstration » tant qu'elle
n'interroge pas un serveur de préproduction. Ne pas copier de relevé réel,
de secret, de token ou de coordonnée privée dans le dépôt ou les captures.

## 5. Passage au backend

Chaque écran documente la route, la version du contrat, les champs obligatoires,
les erreurs et les états de reprise. Claude remet un client isolé, des tests de
présentation et une note des hypothèses. Si une réponse serveur manque, la
maquette affiche l'état indisponible et ouvre une demande de contrat au lot
backend ; elle ne déduit pas le champ depuis l'interface.

Le frontend ne parle jamais directement à PostgreSQL, Redis, S3 ou aux clés
privilégiées. Les appels de conversation passent par les outils bornés du
serveur. Un rafraîchissement de page ne doit pas exposer un refresh token dans
`localStorage` ; le choix d'une session web protégée est à qualifier avec B01.

## 6. Critères de sortie

- Parcours de compte accessible et états d'erreur testés.
- Parcours hors ligne lisible sans promettre un accusé serveur.
- Contrat OpenAPI et exemples associés à chaque écran raccordé.
- Aucune route future présentée comme active.
- Tests d'affichage sur téléphone et écran PC, avec clavier et lecteur d'écran.
- Capture de démonstration reproductible à partir du jeu synthétique.

## 7. Références et historique

[Accord backend/frontend](CONTRACT_HANDOFF.md), [lots backend](BACKEND_WORK_PACKAGES.md),
[site public](https://quintessences-platform.com/).

| Date | Évolution |
|---|---|
| 2026-09-28 | Brief initial pour préparer le travail frontend indépendant |
