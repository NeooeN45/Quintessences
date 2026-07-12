# GSIE-CON-004 — Toute décision doit être explicable

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

Toute recommandation produite par GSIE doit être entièrement
explicable. Chaque résultat doit permettre de comprendre :

- pourquoi il est proposé ;
- quelles données sont utilisées ;
- quelles règles sont appliquées ;
- quel est son niveau de confiance ;
- quelles sont ses limites.

## Pourquoi

Une recommandation non expliquée ne peut être vérifiée, améliorée ni
enseignée. En foresterie, le forestier engage sa responsabilité légale
lorsqu'il suit une recommandation. Si le système ne peut pas justifier
sa sortie, le forestier ne peut pas évaluer le risque qu'il prend en
l'utilisant.

L'explicabilité est aussi la condition de l'amélioration : un système
dont on ne comprend pas les sorties ne peut pas être corrigé lorsqu'il
se trompe.

## Les cinq questions fondamentales

Chaque sortie de GSIE doit répondre à ces cinq questions :

1. **Pourquoi ?** — la chaîne de raisonnement, étape par étape.
2. **Avec quelles données ?** — les entrées utilisées et leur source.
3. **Selon quelles règles ?** — les règles, coefficients et modèles
   appliqués.
4. **Avec quel niveau de confiance ?** — le niveau de preuve et
   l'incertitude.
5. **Quelles limites ?** — les conditions hors domaine, les biais
   connus.

## Conséquences pour les moteurs

Chaque moteur devra produire :

- les sources utilisées ;
- les règles appliquées ;
- les calculs réalisés ;
- les hypothèses ;
- les incertitudes ;
- les moteurs sollicités.

Aucun moteur ne peut produire une sortie sans ces métadonnées.

## Exemple

Une recommandation d'essence présente les paramètres pédologiques (pH,
texture, profondeur), climatiques (température, précipitations),
topographiques (altitude, exposition), les publications scientifiques
mobilisées (références bibliographiques), les facteurs limitants et le
niveau de confiance global. Le forestier peut vérifier chaque élément.

## Contre-exemple

Un moteur produit un score « 87/100 » pour une essence sans décomposer
le calcul. Le forestier ne sait pas si le score tient compte du pH, du
climat ou de la pente. C'est une violation de CON-004. Le score doit
être décomposé en facteurs explicites avec leurs contributions
individuelles.

## Références

- `AI_CONSTITUTION.md` — Article IA-2 (Explicabilité obligatoire) et
  IA-3 (Pas de boîte noire)
- `TECHNICAL_CONSTITUTION.md` — Article T-3 (Subordination du code à la
  connaissance)
- `GSIE-CON-001` — Le forestier reste le décideur

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.
