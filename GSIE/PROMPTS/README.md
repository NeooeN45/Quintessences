# Prompts opérationnels GSIE

## Objet

Ce dossier contient les missions versionnées confiées aux agents IA de
développement. Les prompts appliquent RFC-0022, DEC-000032 et le processus
QMS d'orchestration.

Un prompt est un contrat de tâche, pas une source scientifique ni une
autorisation de fusion.

## Règles

- Identifiant immuable : `GSIE-PROMPT-xxxx`.
- Une mission, un périmètre et un agent principal par prompt.
- Le snapshot de départ doit être identifiable avant exécution.
- Aucun secret ni donnée personnelle dans le prompt ou le rapport.
- Les non-objectifs et conditions d'arrêt sont obligatoires.
- Aucune tâche distante sur des changements locaux non accessibles.
- Aucun commit, push, merge ou déploiement sans autorisation explicite.
- Le résultat revient à Codex pour inspection du diff et reproduction des
  preuves.
- Le Fondateur conserve l'arbitrage final.

## Cycle

`PROPOSÉE → PRÊTE → ASSIGNÉE → EN_COURS → EN_REVUE → VALIDÉE → INTÉGRÉE`

États alternatifs : `BLOQUÉE`, `REJETÉE`, `ANNULÉE`.

## Choix de l'agent

| Profil | Usage privilégié |
|---|---|
| Claude | Architecture, analyse transverse, revue adversariale, ambiguïtés |
| GLM 5.2 | Implémentation bornée, inventaire, validation reproductible |
| Codex | Orchestration, revue du diff, vérification et décision technique |

Le choix reste fondé sur le risque et le résultat attendu, pas sur une
présomption d'infaillibilité du modèle.

## Fichiers

- `REGISTER.md` : registre humain des missions.
- `TEMPLATE_TASK.md` : contrat minimal à copier.
- `GSIE-PROMPT-xxxx-*.md` : prompts concrets.
