# Dossier de relecture experte — Farges / contradiction dendrométrique

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-BENCH-REVIEW-FARGES-001 |
| **Statut** | Review |
| **Version** | 0.1.0 |
| **Date** | 2026-08-12 |
| **Scénario** | `quarantine.farges.dendrometry.001` |
| **Niveau actuel** | Silver / quarantaine |
| **Décision attendue** | pending / qualified / rejected |

## 1. Objet de la relecture

Ce dossier doit permettre à deux relecteurs indépendants de vérifier si le
cas des Farges peut devenir un scénario Gold. Il ne demande pas de corriger le
document source et ne vaut pas certification. Tant que toutes les rubriques ne
sont pas signées, le runner Closed doit rester bloqué.

## 2. Données à vérifier

| Valeur | Valeur déclarée | Contrôle demandé | Résultat |
|---|---:|---|---|
| Densité `N` | 325 tiges/ha | protocole et population couverte | À renseigner |
| Surface terrière `G` | 20,5 m²/ha | méthode de mesure et unité | À renseigner |
| Diamètre moyen | 53 cm | moyenne arithmétique ou quadratique ; distribution | À renseigner |
| Volume | 1 255 m³/ha annoncé dérivé | tarif, facteur de forme, écorce, population | À renseigner |

Le contrôle géométrique donne :

```text
dq = 100 × √(4 × 20,5 / (π × 325)) ≈ 28,34 cm
```

L'écart avec 53 cm doit être expliqué par une différence de population,
d'indicateur (moyenne arithmétique contre diamètre quadratique), de surface ou
de convention. Il est interdit de choisir silencieusement la valeur la plus
plausible.

## 3. Checklist scientifique

- [ ] Localisation, date et peuplement observé confirmés.
- [ ] Inventaire intégral ou échantillonnage identifié.
- [ ] Surface inventoriée et facteur d'expansion documentés.
- [ ] Définition de `N`, `G`, diamètre moyen et diamètre quadratique fournie.
- [ ] Distribution des diamètres ou liste tige par tige disponible pour revue.
- [ ] Formule de volume, tarif, facteur de forme et écorce documentés.
- [ ] Unités et arrondis vérifiés.
- [ ] Incertitudes et tolérances fixées.
- [ ] Les symptômes sanitaires sont séparés d'un diagnostic confirmé.
- [ ] Les recommandations interdites et réponses d'abstention sont définies.

## 4. Checklist juridique et provenance

- [ ] Le Fondateur confirme le droit d'utiliser la fiche dans un benchmark fermé.
- [ ] Le droit de produire des annotations dérivées est explicite.
- [ ] Aucune copie de PDF/DOCX, figure ou texte substantiel n'est distribuée.
- [ ] Le scénario conserve une référence locale stable et un checksum si une
      copie de travail est autorisée.
- [ ] L'usage pour entraînement IA est explicitement autorisé ou interdit.
- [ ] Le périmètre de confidentialité des coordonnées et propriétaires est
      vérifié.

## 5. Décision des relecteurs

Chaque relecteur remplit une fiche séparée avec un identifiant, son périmètre
d'expertise, son indépendance, les revendications contrôlées et une décision
`approve`, `request_changes` ou `reject`. Deux avis indépendants sont requis.

```text
Relecteur : ____________________    Expertise : ____________________
Indépendance déclarée : oui / non  Date : __________________________
Revendications vérifiées : _________________________________________
Tolérances fixées : oui / non      Alternatives définies : oui / non
Vetos de recommandation : oui / non
Décision : approve / request_changes / reject
Notes et sources : _________________________________________________
Signature ou référence de décision : _______________________________
```

## 6. Porte de qualification

La fonction `assess_gold_qualification` exige deux avis indépendants couvrant
la science, les droits, les revendications, les tolérances, les alternatives et
les vetos. Elle ne modifie aucun scénario. Le résultat `qualified` est une
condition nécessaire, mais la promotion Gold reste une décision explicite du
Fondateur conformément à RFC-0039 et DEC-000067.

## 7. État initial

```text
Scénario : Silver / quarantaine
Qualification : pending_expert_review
Closed : BLOQUÉ
Promotion : INTERDITE
IA / ingestion : INTERDITES
```

