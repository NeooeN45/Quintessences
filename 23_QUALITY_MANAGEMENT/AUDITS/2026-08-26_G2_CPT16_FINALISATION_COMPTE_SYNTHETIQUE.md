# Rapport de recette G2 — CPT-16 finalisation serveur d’un compte synthétique

| Champ | Valeur |
|---|---|
| **Date** | 2026-08-26 |
| **Campagne** | ADB-G2-20260826-finalizer-01 |
| **Périmètre** | Fonction PostgreSQL de finalisation RGPD, migration `20260826_0055` |
| **Environnement** | Docker local, API et PostgreSQL sains ; Alembic `20260826_0055` en tête |
| **Compte ciblé** | Compte synthétique neuf, UUID `d90680a3-d7f3-4b1d-8016-15c285ceac31` |
| **Références** | DEC-000075, GEO-005, CPT-16 |

## Objet

Prouver la finalisation irréversible d’un compte synthétique sans toucher au
compte de recette conservé pour GeoSylva ni à un autre compte.

Le worker Compose n’a pas été démarré pour cette preuve destructive. La
fonction `gsie_rgpd_identites.finalize_due_account_deletions(integer)` a été
exécutée directement afin de borner explicitement la cible et de contrôler la
transaction. Le smoke test non destructif du processus worker reste à faire.

## Préconditions et garde-fous

- le compte synthétique a été créé pendant la campagne ;
- une première demande API a été refusée car l’adresse n’était pas encore
  vérifiée ; aucun compte de recette existant n’a été réutilisé ;
- avant marquage, le nombre de comptes échus était `0` ;
- le marquage `pending_deletion` et l’échéance passée ont été appliqués avec
  une clause d’identité sur l’UUID, le nom synthétique et le statut `active` ;
- la fonction a été appelée avec un lot de taille `1` dans la même transaction ;
- résultat retourné par la fonction : `processed = 1`.

## Résultats observés après commit

| Contrôle | Résultat |
|---|---:|
| Statut du compte | `disabled` |
| `display_name` anonymisé | oui |
| `deleted_at` renseigné | oui |
| dates de suppression différée effacées | oui |
| liens d’identité | `0` |
| credential local | `0` |
| sessions actives | `0` |
| consentements | `0` |
| rôles | `0` |
| tokens d’action | `0` |
| demandes de changement d’e-mail | `0` |
| secret et codes MFA | `0` |
| échecs de connexion et refresh révoqués | `0` |
| appartenance d’organisation | `0` |
| répliques `geosylva_parcels` | `0` |
| abonnements et entitlements | `0` |

La trace d’audit finale est présente avec `action=delete`, `status_code=200` et
`event=account_deletion_finalized`. Les deux lignes d’audit du compte ne
conservent plus d’adresse e-mail (`audit_emails_remaining = 0`).

## Conclusion

La migration 0055 et le cœur SQL de la politique DEC-000075 sont validés en
environnement local sur un compte synthétique dédié. CPT-16 est **vert pour la
fonction de finalisation**. G2 reste ouvert pour le worker en exécution opérée,
la restauration de sauvegarde, la purge locale complète, l’isolation de deux
comptes et la configuration Google réelle.

