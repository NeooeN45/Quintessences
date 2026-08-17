# FieldIntake stationnel v0.1

**Statut :** Draft  
**Date :** 2026-08-12  
**Périmètre :** réception en quarantaine de données stationnelles de terrain

## Objectif

Ce contrat conserve séparément les observations brutes, les calculs dérivés,
les interprétations et les recommandations. Une incohérence est signalée dans
un rapport déterministe ; aucune valeur reçue n'est corrigée ou remplacée.

## Unités minimales

| Mesure | Unité canonique |
|---|---|
| Densité | `stems_per_ha` |
| Surface terrière | `m2/ha` |
| Diamètre | `cm` |
| Hauteur | `m` |
| Volume | `m3/ha` |
| Acidité | `pH` |
| Profondeur | `cm` |
| Précipitations / déficit hydrique | `mm` |
| Température | `degC` |

Les valeurs numériques doivent être finies et non négatives. Le pH est borné
à `[0, 14]`. Toute mesure conserve `method_id`, `method_version`, la date,
et peut référencer une source ou une incertitude.

## Calculs déterministes

Pour une densité `N` (tiges/ha) et un diamètre `d` (cm), la surface terrière
est calculée par la section circulaire :

`G = N × π/4 × (d/100)²` en m²/ha.

Pour une surface terrière `G` et une densité `N`, le diamètre quadratique moyen
est :

`d_q = 100 × √(4G/(πN))` en cm.

Ces formules sont des contrôles géométriques. Elles ne constituent ni une
méthode de cubage, ni une décision sylvicole. Les conventions d'inventaire,
les facteurs de forme, les tarifs et les seuils stationnels devront être
qualifiés dans des fiches scientifiques distinctes avant toute promotion.

## Contradictions

Le contrôle `BASAL_AREA_DIAMETER_CONTRADICTION` compare le diamètre déclaré au
diamètre quadratique dérivé. L'écart relatif par défaut est de 20 %. Le rapport
retourne les valeurs observées et dérivées, la gravité `error`, et conserve la
mesure d'origine pour expertise.

## Gouvernance et limites

- Le contrat est compatible avec le JSONB `FieldIntake` existant : aucune
  migration n'est requise pour cette première tranche.
- Toute soumission reste `quarantined` et idempotente par événement client.
- Les recommandations exigent au moins une référence de preuve et restent
  `pending_review` par défaut.
- Les seuils pédologiques, climatiques, dendrométriques et phytosanitaires ne
  sont pas encore des règles de recommandation.
- Les sources personnelles BTS et les références ONF/IGN restent soumises à
  qualification juridique et scientifique avant ingestion ou benchmark Gold.

## Références de travail

- Fiche de diagnostic forestier — conventions d'inventaire à relire par un
  expert avant certification.
- `RFC-0039 — GSIE-Bench v0.1` — séparation observation/référence/score.
- `DEC-000067` — interdiction d'intégration IA et de promotion automatique
  pendant la qualification initiale.

