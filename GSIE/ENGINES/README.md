# 09 — Engines

## Objectif

Regrouper les moteurs exécutables de GSIE. Chaque moteur est un
composant indépendant, testable isolément et interrogeable via une
interface claire.

## Responsabilités

- Implémenter les capacités du système expert
- Respecter les contrats d’interface documentés dans
  [ENGINE_INTERFACE_CONTRACTS.md](../ARCHITECTURE/ENGINE_INTERFACE_CONTRACTS.md),
  en tenant compte de leur statut documentaire
- Garantir l'explicabilité de chaque sortie

## Ce qui peut y être ajouté

- Définitions, périmètres et limites des moteurs
- Implémentations autorisées par la gouvernance de la Phase 4

## Ce qui est interdit

- Implémenter un moteur sans l’autorisation et les prérequis documentaires
  exigés par la gouvernance courante
- Ajouter des règles métiers non sourcées

## Liens

- [ARCHITECTURE](../ARCHITECTURE/) : contrats et flux
- [05_SPECIFICATIONS](../../05_SPECIFICATIONS/) : exigences
- [KNOWLEDGE](../KNOWLEDGE/) : connaissances et règles sourcées
- [ALGORITHMS](../ALGORITHMS/) : méthodes formelles
- [MODELS](../MODELS/) : modèles utilisés
