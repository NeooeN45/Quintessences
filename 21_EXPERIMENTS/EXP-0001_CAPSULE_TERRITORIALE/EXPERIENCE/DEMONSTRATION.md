# Scénario de démonstration — 5 minutes

## Promesse montrée

« Avant une mission sans réseau, GSIE prépare un contexte territorial. Le
téléphone peut vérifier que ce contexte vient d'un émetteur approuvé, qu'il
n'a pas été modifié et que ses calculs de référence restent reproductibles. »

## Préparation

```bash
cd 21_EXPERIMENTS/EXP-0001_CAPSULE_TERRITORIALE
python --version
make demo
```

La commande doit terminer par `DÉMONSTRATION GSIE : SUCCÈS` et retourner le
code processus `0`.

## Déroulé narratif

1. **Montrer le territoire.** Ouvrir
   `fixtures/territoire-reference/payload/territory.json` et rappeler qu'il
   est synthétique, donc adapté aux tests mais pas à une décision forestière.
2. **Montrer la capsule.** Présenter `build/demo-territoire.gsiecap` comme le
   futur objet téléchargeable dans GeoSylva.
3. **Montrer la confiance.** Ouvrir `build/verification-report.json` : la clé,
   la signature, le nombre de fichiers et l'empreinte de chaque contenu ont
   été contrôlés hors-ligne.
4. **Montrer la science.** Ouvrir `build/golden-bench-report.json` : chaque cas
   expose les entrées, l'attendu, l'obtenu, la tolérance et l'état de revue.
5. **Montrer l'honnêteté.** Souligner que le calcul peut passer tout en restant
   « à valider scientifiquement ». GSIE ne confond pas exactitude logicielle
   et autorité scientifique.
6. **Montrer le résultat final.** Ouvrir
   `build/demonstration-report.json`, futur artefact de CI et de recette.

## Critères de succès visibles

| Contrôle | Résultat attendu |
|---|---|
| Construction | capsule créée |
| Signature | valide avec la clé publique approuvée |
| Intégrité | tous les fichiers et tailles correspondent au manifeste |
| Golden Bench | aucun écart hors tolérance |
| Gouvernance | aucun cas en attente n'est présenté comme « expert-validé » |
| Réseau | aucun appel effectué |

## Démonstration de rejet

Les scénarios hostiles sont automatisés afin d'éviter de modifier à la main
les fixtures de référence :

```bash
make test
```

Les tests prouvent notamment que :

- un payload altéré est rejeté ;
- une signature contrôlée avec la mauvaise clé est rejetée ;
- une archive contenant un chemin `../` est rejetée ;
- un membre en double est rejeté ;
- un résultat numérique hors tolérance fait échouer le banc.

## Ce que la démonstration ne prétend pas montrer

- un téléchargement réel depuis GSIE ;
- une clé de production ;
- une donnée environnementale officielle ;
- une formule validée par le CNPF, l'ONF ou l'INRAE ;
- une intégration Android ou Unreal déjà terminée.

Ces limites doivent rester visibles pendant toute présentation externe.

