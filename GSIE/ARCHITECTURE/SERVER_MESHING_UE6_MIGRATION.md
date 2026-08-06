# SERVER MESHING — Stratégie de migration UE6

| Champ | Valeur |
|---|---|
| **Document** | Stratégie de migration UE6 — GSIE Server Meshing |
| **Statut** | Draft |
| **Date** | 2026-08-03 |
| **RFC liée** | RFC-0035 (§5.3, §7) |
| **Directive liée** | GSIE-DIR-0012 |
| **Décision liée** | DEC-000053 (compatibilité UE6 anticipée, pas de dépendance hard) |
| **ADR lié** | ADR-015 (interfaces abstraites pour compatibilité UE6) |
| **Documents connexes** | `SERVER_MESHING_TARGET.md` (§14), `SERVER_MESHING_ROADMAP.md`, `SERVER_MESHING_RISKS.md` (RISK-MESH-006) |

---

## 1. Mission du document

Définir la stratégie de migration du Centre de Commandement GSIE
d'Unreal Engine 5.8 vers Unreal Engine 6, dans le contexte du Server
Meshing. Cette stratégie est **anticipée** : UE6 n'est pas publié à la
date de rédaction. Le document fixe les principes et les conditions de
déclenchement, pas un calendrier.

---

## 2. Position de principe

La décision Fondateur (DEC-000053, GSIE-DIR-0012) est claire :
**compatibilité UE6 anticipée, sans dépendance hard**. Concrètement :

- Le mesh est défini par des interfaces abstraites indépendantes d'UE
  (ADR-015).
- UE5.8 est l'implémentation actuelle de `IRenderClient`.
- UE6 sera, le cas échéant, une implémentation future de la même
  interface.
- Aucune primitive spécifique à UE6 n'est utilisée dans les contrats
  de mesh.

Cette posture élimine le risque de blocage si UE6 est retardé, change
de paradigme, ou n'est jamais adopté (RISK-MESH-006).

---

## 3. Conditions de déclenchement de la migration

La migration vers UE6 n'est **jamais automatique**. Elle est déclenchée
par une décision explicite du Fondateur (DEC-xxxxxx) lorsque **toutes**
les conditions suivantes sont réunies :

1. **UE6 est publié** en version stable (pas en preview).
2. **Le mesh est opérationnel** au moins au niveau Phase 6 (multi-régions,
   handoff validé) — la migration ne se fait pas sur un prototype
   instable.
3. **Un bénéfice démontrable** d'UE6 est identifié pour le Centre de
   Commandement (ex. : primitive de rendu distribuée native,
   amélioration de performance, fonctionnalité indisponible en UE5.8).
4. **Le coût de migration est estimé** et accepté par le Fondateur.
5. **Aucune dépendance hard à UE5.8** n'existe dans les contrats de mesh
   (vérification par revue de code, ADR-015).

Si UE6 n'apporte pas de bénéfice démontrable, la migration n'a pas
lieu — UE5.8 reste l'implémentation de référence indéfiniment.

---

## 4. Stratégie technique de migration

### 4.1 Principe : adaptation, pas refonte

La migration consiste à **écrire un nouvel adaptateur** `IRenderClient`
pour UE6, sans modifier le mesh. L'adaptateur UE5.8 actuel reste
fonctionnel pendant la transition, permettant un bascuule progressif.

```
[Mesh — interfaces abstraites stables]
        │
        ├── IRenderClient adaptateur UE5.8 (existant, reste actif)
        │
        └── IRenderClient adaptateur UE6 (nouveau, Phase 7 si déclenchée)
```

### 4.2 Étapes de migration (si déclenchée)

1. **Évaluation** — audit des primitives UE6 disponibles, identification
   du bénéfice, estimation du coût (ADR dédié).
2. **Prototype** — implémentation de l'adaptateur UE6 sur un périmètre
   restreint (une zone, un scénario de navigation).
3. **Validation de neutralité** — l'adaptateur UE6 satisfait
   `IRenderClient` sans modification du mesh (ACC-MESH-P7-06).
4. **Bascule progressive** — l'adaptateur UE6 remplace l'adaptateur
   UE5.8 région par région, avec retour arrière possible.
5. **Retrait de l'adaptateur UE5.8** — uniquement après validation
   complète, si UE5.8 n'est plus requis.

### 4.3 Coexistence UE5.8 / UE6

Pendant la transition, les deux adaptateurs peuvent coexister :
- certaines régions rendues par UE5.8, d'autres par UE6 ;
- le mesh ne fait pas de distinction — il sert le même flux à tout
  `IRenderClient`.

Cette coexistence est un bénéfice direct de l'abstraction (ADR-015) :
la migration n'est pas un big-bang, mais une transition progressive.

---

## 5. Risques spécifiques à la migration

| Risque | Mitigation |
|---|---|
| UE6 introduit des primitives incompatibles avec l'interface abstraite actuelle | Révision de l'interface par RFC si nécessaire (P-MESH-07) ; l'interface est évolutive, pas figée |
| Coût de migration sous-estimé (réécriture de l'adaptateur Cesium for Unreal) | Estimation préalable obligatoire (étape 1) ; pas de migration sans coût accepté |
| Dérive : migration vers UE6 motivée par nouveauté plutôt que par bénéfice | Condition de bénéfice démontrable (§3, point 3) ; décision Fondateur explicite |
| Abandon d'UE6 par Epic Games avant la fin de la migration | Coexistence UE5.8/UE6 (§4.3) ; l'adaptateur UE5.8 reste la référence |

---

## 6. Alternatives à la migration UE6

Si UE6 n'est pas publié, n'apporte pas de bénéfice, ou est abandonné,
les alternatives suivantes satisfont le même contrat `IRenderClient` :

| Alternative | Maturité | Bénéfice |
|---|---|---|
| CesiumJS web (client de rendu léger, navigateur) | Mature | Accès distant sans installation, déploiement facile |
| Apps mobiles terrain (offline-first) | Envisagé (RFC-0035 §4) | Continuité terrain en zone d'intervention |

Aucune de ces alternatives ne modifie le mesh — elles implémentent
`IRenderClient` comme UE5.8 ou UE6. La neutralité de rendu est la
garantie que le mesh survit à toute évolution du moteur de rendu.

---

## 7. Ce que ce document n'est pas

- Ce n'est pas un engagement de migration — la migration n'a lieu que
  si les conditions de déclenchement (§3) sont réunies.
- Ce n'est pas un calendrier — la migration est conditionnelle et
  déclenchée par décision Fondateur.
- Ce n'est pas une spécification de l'adaptateur UE6 — celle-ci relève
  de l'implémentation, si et quand la migration est déclenchée.
