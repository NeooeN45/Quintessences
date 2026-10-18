# DEC-000092 — Confidentialité des dépôts de code

| Champ | Valeur |
|---|---|
| ID | DEC-000092 |
| Statut | Draft — instruction du fondateur consignée, application à vérifier |
| Date | 2026-10-18 |
| Décideur | Camille Perraudeau (Fondateur) |
| Nature | Organisation et confidentialité |

## Instruction

Le fondateur demande : « Passe en privé, mais de manière sécurisée ».
Le périmètre est Quintessences et GeoSylva, encore publics lors de la vérification.
Forge, Hub et horizon-origin-web sont déjà privés. L’archive geosylva-privacy
et les informations destinées au public restent traitées séparément.

## État d’exécution

Les deux appels GitHub de changement de visibilité ont été tentés le 18 octobre
2026 et refusés avec HTTP 403, « Resource not accessible by integration ».
La décision n’est donc pas présentée comme appliquée. La permission
administrative de l’intégration ou une intervention du propriétaire est nécessaire.

## Conditions opérationnelles

- Préserver les historiques et les changements locaux ; aucun force-push.
- Vérifier les accès, intégrations et protections de branches privées selon l’offre.
- Anticiper le retrait des graphes GitHub Pages ; aucun CNAME n’y est déclaré.
- Conserver la diffusion du site commercial dans son dépôt et hébergement distincts.
- Séparer la distribution des APK TEST de l’accès au dépôt privé.
- Ne pas modifier rétroactivement les licences, transférer les dépôts ou acheter
  un abonnement sans décision correspondante.

Les forks publics et copies existantes ne deviennent pas privés par cette opération.
Le contrôle effectif de visibilité après application sera consigné dans la mémoire.

## Référence

[GitHub — conséquences d’un changement de visibilité](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility), consulté le 18 octobre 2026.
