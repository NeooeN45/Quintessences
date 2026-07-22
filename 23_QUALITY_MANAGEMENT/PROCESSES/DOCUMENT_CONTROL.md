# Processus de contrôle documentaire et des sources de vérité

| Champ | Valeur |
|---|---|
| Document | DOCUMENT_CONTROL.md |
| Dossier | 23_QUALITY_MANAGEMENT/PROCESSES |
| Version | 1.0.0 |
| Date | 21 juillet 2026 |
| Statut | Adopté |
| Référence | QUALITY_MANUAL.md |

## 1. Objet

Ce processus empêche qu'une conversation, un brouillon, une copie de
configuration ou une documentation ancienne soit utilisée comme vérité
courante. Le registre machine-lisible
`SOURCE_OF_TRUTH_REGISTRY.json` désigne les corpus autorisés, leur
propriétaire et leur prochaine date de revue.

## 2. Hiérarchie d'autorité

En cas de contradiction dans un même domaine, l'ordre suivant s'applique :

1. Constitution et documents `Locked`.
2. Directives actives et décisions validées.
3. RFC adoptées et spécifications approuvées.
4. Contrats exécutables de l'implémentation : migrations, schémas, API,
   validations et tests.
5. Mémoire projet, feuille de route et changelog.
6. Manuel, politique et processus qualité.
7. README explicatifs, journaux, notes de session, conversations et
   brouillons archivés.

Un contrat exécutable décrit ce que le logiciel fait, mais ne peut pas
annuler une règle constitutionnelle, juridique ou scientifique. Une
conversation avec un agent IA est une source de contexte, jamais une
autorisation ni une décision.

Le registre est l'index de cette hiérarchie. Il ne remplace pas les contenus
qu'il référence.

## 3. États documentaires

| État | Usage autorisé |
|---|---|
| `canonique` | Peut fonder une décision dans son périmètre. |
| `reference` | Apporte un détail ; doit être confronté aux sources supérieures. |
| `archive` | Contexte historique uniquement ; doit indiquer `superseded_by`. |
| Brouillon | Proposition non applicable tant qu'elle n'est pas adoptée. |

Un document dont la date `next_review` est dépassée est **expiré**. Il ne
doit plus être présenté comme actuel avant revue, même si son contenu semble
plausible.

## 4. Règles obligatoires

- Toute source canonique a un propriétaire, une date de dernière revue et
  une date de prochaine revue.
- Toute duplication indique explicitement le document canonique et évite de
  recopier les valeurs susceptibles d'évoluer.
- Les valeurs métier externes conservent l'URL, la version, la date de
  consultation et, si disponible, le hash de l'artefact.
- Les schémas générables (OpenAPI, migrations, lockfiles) sont générés depuis
  leur source ; ils ne sont pas édités indépendamment.
- Une source remplacée est déplacée dans un espace d'archive ou marquée
  obsolète avec un lien `superseded_by`.
- Toute PR modifiant une source canonique met à jour les références
  dépendantes, le registre si nécessaire, la mémoire, la roadmap et le
  changelog.
- Le contrôle `python tools/check_source_of_truth.py` est bloquant en CI.

## 5. Fréquences minimales

| Type | Revue maximale |
|---|---|
| État projet, roadmap, changelog | Mensuelle et après changement d'état |
| Directives, RFC actives, spécifications, QMS | Trimestrielle |
| Décisions | Semestrielle |
| Constitution | Annuelle ou après amendement |
| Source scientifique ou réglementaire | Selon sa volatilité, au plus annuelle |
| Archive | Pas de revue périodique ; interdiction d'usage canonique |

Une source réglementaire, tarifaire, sécuritaire ou logicielle volatile peut
exiger une période plus courte.

## 6. Traitement d'une contradiction

1. Identifier le périmètre exact et les documents en conflit.
2. Appliquer la hiérarchie et vérifier le statut dans le registre.
3. Si l'arbitrage est déjà validé, corriger les copies et archiver l'ancien
   contenu dans la même PR.
4. Si l'arbitrage change l'architecture, le droit, la science ou le QMS,
   ouvrir une RFC et obtenir la décision compétente avant modification.
5. Ajouter un test ou un contrôle automatique quand la contradiction est
   détectable par machine.
6. Tracer la correction dans le changelog et la mémoire projet.

## 7. Preuve de revue

Une revue de fraîcheur confirme au minimum :

- que le propriétaire et le statut sont toujours corrects ;
- que les liens, versions et hypothèses externes sont encore valides ;
- que le code, les migrations et la documentation décrivent le même contrat ;
- que les documents remplacés ne restent pas présentés comme actuels ;
- que la prochaine date de revue correspond au risque réel.

Modifier uniquement la date sans vérifier ces points est une
non-conformité qualité.

## 8. Indicateurs

- zéro source canonique expirée ;
- zéro identifiant dupliqué dans le registre ;
- zéro chemin canonique absent ;
- délai de correction d'une contradiction critique inférieur à 24 heures ;
- 100 % des changements structurants reliés à une décision ou une RFC.

## 9. Références

- `../QUALITY_MANUAL.md`
- `../SOURCE_OF_TRUTH_REGISTRY.json`
- `../../00_CONSTITUTION/README.md`
- `../../03_DECISIONS/README.md`
