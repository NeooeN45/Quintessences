# Pedology Engine

Moteur de **données pédologiques**.

## Périmètre

- Gérer les données de sol (texture, pH, profondeur, drainage,
  réserve utile en eau)
- Classer les sols selon les référentiels pédologiques officiels
  (Référentiel Pédologique Français, WRB)
- Fournir les caractéristiques stationnelles liées au sol
- Intégrer les données de la Base de Données des Sols et équivalents

## Principe fondamental

**Toute classification pédologique est sourcée.** Aucun seuil (pH,
texture, drainage) n'est inventé — tout provient du référentiel
cité (CON-002).

## Frontières

- Consomme les données de la `Scientific Database` et du
  `Station Repository`
- Fournit des données pédologiques à `DIAGNOSTIC_ENGINE` et
  `CORRELATION_ENGINE`
- Ne produit pas de diagnostic — fournit des données et des
  classifications

> Statut : *fondation — documentation uniquement (Phase 1)*
