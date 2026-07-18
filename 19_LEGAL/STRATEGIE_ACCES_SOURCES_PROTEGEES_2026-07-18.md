# Stratégie d'accès légal aux sources sylvicoles protégées (ClimEssences, BioClimSol, CNPF, ONF)

**Date : 18 juillet 2026**
**Origine :** note juridique fournie par le Fondateur, versée telle quelle pour référence. Complète `GSIE/RESEARCH/CORPUS_SYLVICOLE_SCIENTIFIQUE_QUINTESSENCES_2026-07-18.md` §3 et §13 (verrou juridique ClimEssences/BioClimSol) et RFC-0016.

**Avertissement :** ceci est une note de travail, pas un avis juridique. Une validation par un juriste spécialisé en propriété intellectuelle et données publiques reste indispensable avant toute commercialisation exploitant ces méthodes.

---

## Principe directeur

Contourner le problème d'accès, mais jamais contourner les droits ou les protections techniques. La stratégie la plus intelligente consiste à reconstruire notre propre connaissance depuis les sources amont, ouvertes ou légalement accessibles, au lieu de recopier ClimEssences ou BioClimSol.

## Méthodes évaluées

| Méthode | Faisable ? | Utilisation |
|---|---|---|
| Données sous Licence Ouverte | Oui | Copie, adaptation, redistribution et usage commercial avec attribution. |
| Remonter aux bibliographies de ClimEssences | Oui | Utiliser ClimEssences comme catalogue, puis extraire les informations des publications originales ouvertes. |
| Demander les documents/données administratives | Oui | Demande directe à l'établissement, puis CADA en cas de refus applicable. |
| Fouille de textes et données | Sous conditions | Accès licite, absence d'opposition du titulaire, stockage sécurisé et destruction des copies. |
| Réécriture « clean room » | Oui, prudemment | Produire nos propres assertions et modèles depuis plusieurs sources, sans recopier textes, tableaux ou base. |
| Import de documents par l'utilisateur | Possible | Index exclusivement local, aucune remontée serveur ni redistribution ; conditions de licence à respecter. |
| Métadonnées + liens profonds | Oui | Conserver titre, organisme, version, URL et références sans intégrer le contenu protégé. |
| Partenariat/API officielle | Oui | Meilleure solution à long terme pour ClimEssences et BioClimSol. |
| Contourner comptes, paywalls, CAPTCHA ou limites techniques | **Non** | Risque juridique, contractuel et réputationnel majeur. |

## Le meilleur « détour » pour ClimEssences

On utilise ses fiches comme carte de navigation :

1. Relever la bibliographie et les organismes cités.
2. Retrouver les publications originales sur HAL, INRAE, AgroParisTech, ONF Open Data, data.gouv.fr ou les revues ouvertes.
3. Extraire des affirmations atomiques depuis ces sources originales.
4. Réécrire l'information dans notre propre modèle scientifique.
5. Faire valider chaque assertion par un forestier.
6. Citer la publication originale, pas simplement la fiche ClimEssences.

Ainsi, on peut reconstruire progressivement notre propre `AutecologyProfile` (RFC-0016 §3.1) sans reproduire leur texte, leur présentation ou leur base. Ce chemin est directement compatible avec le pipeline d'extraction documentaire déjà en place (RFC-0014 §3.2, `Forge/src/dataset_forge/documents/`) : HAL et OpenAlex sont déjà connectés (session du 2026-07-18, `MultiSourceDocumentSearcher`).

## La fouille de textes peut aider, mais ce n'est pas une porte dérobée

Le droit français permet sous conditions la fouille de textes et données auxquelles on a accédé licitement, sauf opposition appropriée du titulaire. Les copies doivent être sécurisées puis détruites à la fin de la fouille. Cela peut servir à détecter des valeurs, tendances et relations, mais ne donne pas automatiquement le droit de redistribuer les documents, leurs textes ou un RAG permettant de les reconstituer (article L122-5-3 du Code de la propriété intellectuelle).

Transformer une base en milliers de fragments ou embeddings ne rend pas nécessairement l'opération licite : le producteur peut interdire l'extraction substantielle, mais aussi l'extraction répétée et systématique de petites parties (articles L342-1 et L342-2).

## Exploiter beaucoup plus fortement les données publiques

Les informations publiques communiquées ou publiées par une administration sont en principe réutilisables dans le cadre du CRPA, avec leurs conditions propres (article L321-1 du CRPA).

Lorsque la Licence Ouverte 2.0 est explicitement indiquée, elle autorise notamment l'adaptation, la redistribution et l'exploitation commerciale, sous réserve d'attribution et de transparence sur la source.

On peut aussi demander directement : les données sources, les exports CSV/GeoJSON, les dictionnaires de données, les versions historiques, les méthodes et rapports administratifs, les documents dans un format exploitable. Si une administration refuse de communiquer un document normalement accessible, la CADA peut être saisie après le refus.

## Architecture recommandée — modes d'ingestion

Chaque source doit recevoir un mode d'ingestion :

| Mode | Signification |
|---|---|
| `OPEN_COPY` | Copie et redistribution autorisées |
| `TDM_EPHEMERAL` | Analyse temporaire, source non redistribuée |
| `LOCAL_USER_ONLY` | Document importé et indexé uniquement sur l'appareil |
| `METADATA_LINK` | Titre, version, citation et lien uniquement |
| `PARTNER_LICENSE` | Contenu utilisé selon un accord CNPF/ONF |
| `FORBIDDEN` | Aucune ingestion |

Pour ClimEssences, le mode initial est `METADATA_LINK` (ses conditions actuelles interdisent généralement la copie et la redistribution sans autorisation écrite). Pour BioClimSol, c'est `PARTNER_LICENSE`.

**Implémenté** dans `gsie_api.governance.source_registry` (`IngestionMode`, champ `mode_ingestion` de `ScientificSourceEntry`) — voir commit associé.

## Conclusion

La voie la plus solide : sources ouvertes + bibliographies amont + demandes CADA + données terrain propres + import local + partenariats institutionnels. Cela permet de construire un corpus très riche sans dépendre juridiquement d'une aspiration clandestine.
