# Standard de qualité du code GSIE

| Champ | Valeur |
|---|---|
| Document | `CODE_QUALITY_STANDARD.md` |
| Dossier | `23_QUALITY_MANAGEMENT/PROCESSES` |
| Version | 1.0.0 |
| Date | 25 juillet 2026 |
| Statut | Proposé — validation du Fondateur requise |
| Références | `GSIE-CON-002`, `CON-004`, `CON-005`, `TECHNICAL_CONSTITUTION`, `ADR-009` |

## 1. Objet

Ce document est à coller en tête de tout prompt de développement, humain ou
agent. Il ne répète pas la Constitution : il en déduit ce qu'elle exige d'une
ligne de code.

## 2. Ce que fait cette application

GSIE dit à un forestier ce qu'il devrait savoir sur une parcelle. Un
propriétaire abattra des arbres sur la foi de ce que le système affiche. Un
commandant d'intervention décidera d'un axe d'attaque. Ces décisions engagent
des décennies et parfois des vies.

Un bug de calcul produit un mauvais chiffre. Un bug de traçabilité produit un
mauvais chiffre **auquel on croit**. Le second est bien plus grave, et c'est
celui contre lequel ce standard existe.

Le code doit donc être à la hauteur de ce qu'on lui fait dire. Concrètement :
toute sortie doit pouvoir être contestée par un tiers, reproduite à
l'identique, et remontée jusqu'à sa source.

## 3. Les six exigences

### 3.1 Rien n'existe sans source

`GSIE-CON-002` : ce qui n'est pas sourcé n'existe pas. `ADR-009` : aucune
valeur numérique, corrélation ou conclusion ne circule sans `SourceReference`
résolvable et `evidence_level` hérité d'une donnée réelle.

En pratique : aucun seuil, coefficient, pondération ou constante métier n'est
écrit dans le code. S'il t'en faut un, c'est qu'il doit venir de la requête,
d'une connaissance qualifiée ou d'un référentiel cité. Un nombre magique dans
un moteur est un refus de livraison, pas une remarque de revue.

`tools/check_governance_consistency.py` le vérifie. Ne cherche pas à le
contourner par une indirection : la règle porte sur l'origine de la valeur,
pas sur l'endroit où elle est écrite.

### 3.2 L'invariant vit dans le type, pas dans le commentaire

Une garantie exprimée en commentaire est un vœu. La même garantie exprimée
dans un modèle Pydantic ou un validateur est une propriété du système.

Si une structure ne doit pas pouvoir exister dans un certain état, elle ne
doit pas pouvoir être construite dans cet état. Une conclusion sans source,
une chaîne d'inférence trouée, un résultat tronqué qui ne le dit pas : ces
objets doivent lever à la construction, pas être détectés plus tard.

Corollaire pour les agents : si tu constates qu'un type te laisse fabriquer
un objet incohérent, tu as trouvé un défaut d'architecture. Signale-le, ne le
contourne pas.

### 3.3 Déterminisme

À entrées identiques, sortie identique. Cela signifie :

- aucun parcours de `set` ou de `dict` non ordonné dans un chemin qui produit
  de la sortie ; tri explicite partout où l'ordre est observable ;
- aucun `uuid4()` pour un identifiant qui devrait être reproductible ; dériver
  du contenu par `uuid5` avec un namespace fixe ;
- **l'horloge est une entrée, pas un effet de bord**. Un moteur qui appelle
  `datetime.now()` en son sein n'est pas testable. La date est passée en
  paramètre par l'appelant.

Le déterminisme n'est pas une élégance : c'est ce qui permet de rejouer une
recommandation d'il y a trois ans et de comprendre pourquoi elle disait cela.

### 3.4 Les limites sont visibles

`GSIE-CON-004` : toute sortie expose ses limites. Un résultat partiel le
déclare **et dit ce qui manque**. Une troncation silencieuse est un mensonge
par omission — la forme d'erreur la plus coûteuse dans ce système.

Un calcul qui s'arrête sur une borne n'est pas une erreur : c'est un résultat
honnête qui doit porter sa borne. Ne lève pas d'exception là où il faut
informer, et n'informe pas discrètement dans un log là où il faut retourner
la donnée.

### 3.5 Les erreurs sont explicites

`TECHNICAL_CONSTITUTION` T-7 : les erreurs sont loggées avant d'être
propagées, explicites, jamais masquées, jamais transformées en comportement
par défaut.

Un `except` qui avale, une valeur de repli silencieuse, un `None` retourné à
la place d'une explication : interdits. Le message nomme l'objet fautif — la
règle, la variable, le champ — pas seulement le symptôme.

À l'inverse, ne lève pas d'erreur pour un cas légitime. Une absence de
résultat quand aucune règle ne s'applique est un résultat, pas une panne.

### 3.6 La séparation des responsabilités est réelle

`GSIE-CON-007` : une responsabilité par module, contrat d'interface
documenté, dépendances acycliques. Un moteur qui produit un diagnostic *et*
une recommandation viole le contrat, même si le code fonctionne.

Un moteur ne devine pas. S'il lui faut une information, elle lui est fournie
ou il déclare ne pas pouvoir conclure. Deviner, c'est inventer, et inventer
est interdit.

## 4. Portes de livraison

Un livrable n'est pas terminé tant que ces cinq commandes ne passent pas.
Elles sont rapportées avec leur code de sortie réel.

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src --strict
python -m pytest tests/unit -q
python tools/check_governance_consistency.py     # depuis la racine
```

Interdictions permanentes : aucun test désactivé, marqué `skip` ou `xfail`
pour faire passer la suite ; aucune assertion affaiblie pour accommoder une
implémentation ; aucune dépendance nouvelle sans justification `T-10`.

## 5. Ce qui distingue un bon test ici

Un test qui vérifie que le code fait ce qu'il fait ne sert à rien. Un bon test
sur ce projet vérifie qu'**une sortie fausse est impossible** :

- qu'une conclusion ne peut pas citer une source qu'elle n'a pas utilisée ;
- qu'une prémisse en trop est rejetée, parce qu'une justification excédentaire
  est une fausse justification ;
- que dix exécutions donnent la même sortie, y compris après permutation de
  l'ordre des entrées ;
- que la borne annoncée est réellement respectée ;
- qu'un cas limite produit une erreur nommée, pas un silence.

Le cas nominal mérite un test. Les cas qui feraient mentir le système en
méritent dix.

## 6. Séparation entre écrire et vérifier

`RFC-0022` §2.4 : l'agent qui produit un changement ne le valide pas seul.

Un agent qui écrit un moteur n'écrit pas les tests adversariaux de ce moteur.
Un agent qui trouve un défaut dans le code d'un autre **ne le corrige pas** :
il livre un test rouge et le motif. Un défaut corrigé par celui qui l'a trouvé
est un défaut qui disparaît sans avoir été vu.

## 7. Ce qu'on attend d'un rapport de fin

1. fichiers créés ou modifiés, liste exacte ;
2. ce que fait le code, en cinq lignes ;
3. les cinq commandes avec leurs codes de sortie réels ;
4. tests écrits : combien, et ce qu'ils rendent impossible ;
5. **décisions prises faute de spécification** — la section la plus utile :
   si elle est longue, la spécification était insuffisante et il faut le dire ;
6. ce qui n'a pas pu être vérifié — jamais vide ;
7. risques résiduels.

Un « je n'ai pas pu vérifier » vaut mieux qu'une affirmation non fondée. Un
rapport qui annonce une commande non exécutée est une non-conformité au sens
du QMS, pas une maladresse.

## 8. Enfin

La qualité recherchée n'est pas l'élégance. C'est qu'un forestier puisse
contester une sortie du système, remonter jusqu'à la publication qui la
fonde, et constater soit qu'elle est juste, soit exactement où elle se trompe.

Tout le reste en découle.
