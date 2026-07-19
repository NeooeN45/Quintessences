# Sécurité de la capsule expérimentale

## Propriétés visées

- **Authenticité :** le manifeste a été signé par une clé approuvée.
- **Intégrité :** chaque fichier correspond à la taille et au SHA-256 signés.
- **Complétude :** aucun fichier déclaré ne manque et aucun membre inattendu
  n'est accepté.
- **Sûreté d'extraction :** aucun chemin ne peut sortir du répertoire cible.

La confidentialité n'est pas une propriété de la v1 : une capsule peut être
lue par toute personne qui la possède.

## Règles de clés

- La clé privée de démonstration est générée dans `build/` et ne doit jamais
  être réutilisée en production.
- Une clé privée de production ne doit jamais être commitée, embarquée dans
  GeoSylva ou copiée dans la capsule.
- GeoSylva doit posséder une liste de clés publiques approuvées obtenue par un
  canal distinct.
- L'identifiant de clé est dérivé de la clé publique ; il ne vaut pas à lui
  seul approbation.
- La signature est vérifiée avant toute installation ou lecture métier.

## Contrôles du prototype

- Ed25519 via `cryptography` ;
- JSON canonique strict ;
- SHA-256 pour chaque membre ;
- refus des liens symboliques côté source ;
- refus des chemins absolus, `..`, antislashs et noms non canoniques ;
- refus des membres ZIP dupliqués ou non déclarés ;
- limites configurables de nombre de fichiers, taille totale et ratio de
  compression ;
- écriture atomique du résultat final.

## Limites avant production

| Risque | Travail requis |
|---|---|
| Clé compromise | révocation, rotation et procédure d'urgence |
| Capsule ancienne valide | compteur/version minimale et protection rollback |
| Délégation producteurs | rôles et chaîne de confiance, évaluer TUF |
| Vol du terminal | SQLCipher/stockage OS et chiffrement éventuel du payload |
| Archive très volumineuse | streaming, quotas et benchmark Android |
| Document tiers hostile | filtrage de types, sandbox et antivirus si nécessaire |
| Déni de service calculatoire | budgets CPU/mémoire et timeouts |
| Mise à jour interrompue | staging, fsync, renommage atomique et retour arrière |

## Gate de revue sécurité

Avant intégration Android, une revue doit couvrir : modèle de confiance,
protection de la clé privée, rotation, révocation, rollback, limites ZIP,
stockage local, journalisation sans données sensibles et comportement en cas
d'horloge terminal incorrecte.

