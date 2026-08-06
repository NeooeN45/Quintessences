# Ignis ↔ GSIE — Intégration au jumeau numérique environnemental fédéré

| Champ | Valeur |
|---|---|
| **Application** | Ignis |
| **Rôle** | Projection métier incendie et premier cas opérationnel du jumeau vivant |
| **Statut** | Draft — cadrage d'intégration |
| **Référence** | RFC-0037, `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md` |

## 1. Positionnement

Ignis fournit la projection incendie du jumeau numérique GSIE :
détection, assimilation, propagation, analyse d'enjeux, suivi des
moyens et scénarios de crise.

Le MVP reste le jumeau numérique et l'analyse d'enjeux sur données
existantes. Les drones réels et les commandes opérationnelles sont des
extensions contrôlées, jamais une dépendance initiale.

## 2. Données consommées

Ignis peut consommer :

- peuplements, combustibles et accès forestiers de GeoSylva ;
- relief, météo, sols et hydrographie des moteurs GSIE ;
- bâtiments, infrastructures et enjeux ;
- observations drones et capteurs ;
- historiques de feux et données nationales.

## 3. Données publiées

- observations et détections ;
- front observé et front prédit ;
- vecteurs et intensités estimés ;
- scénarios probabilistes ;
- enjeux menacés et délais ;
- zones brûlées et impacts post-feu ;
- missions et demandes d'observation ;
- provenance, incertitude et état de validation.

## 4. Boucle opérationnelle

```text
Prévision → observation → assimilation → recalage → scénario
                                      ↓
                              State Fabric GSIE
```

Une prévision n'est jamais présentée comme une observation et une
recommandation n'est jamais une commande automatique.

## 5. Hub Ignis

Le Hub Ignis affiche le territoire, le feu, la météo, les moyens et les
scénarios dans Unreal. Toute action critique passe par une demande
versionnée, un contrôle d'autorité et une validation humaine avant tout
adaptateur opérationnel.
