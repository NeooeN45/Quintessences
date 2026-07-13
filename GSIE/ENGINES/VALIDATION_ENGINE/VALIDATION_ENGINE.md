# Validation Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Validation Engine |
| **Catégorie** | Chaîne d'intelligence (contrôle final) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-001, GSIE-CON-004, GSIE-CON-005 |
| **Ordre de développement** | 13 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Vérifier la cohérence, la conformité constitutionnelle et la complétude
des diagnostics et recommandations avant leur présentation à
l'utilisateur, en bloquant toute sortie non conforme.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `RECOMMENDATION_ENGINE` | Recommandations | Ensemble de recommandations à valider |
| `DIAGNOSTIC_ENGINE` | Diagnostic | Diagnostic à valider |
| `REASONING_ENGINE` | Chaînes d'inférence | Vérification de la cohérence logique |
| `KNOWLEDGE_ENGINE` | Vérification de validité | Contrôle que les connaissances utilisées sont à jour et valides |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| Utilisateur (via interface) | Sortie validée | Diagnostic et/ou recommandations conformes, prêts pour présentation |
| Journal d'audit | Sorties bloquées | Sorties non conformes avec cause de blocage |
| `LEARNING_ENGINE` | Signaux d'échec | Sorties bloquées pour apprentissage et amélioration |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `RECOMMENDATION_ENGINE` | Sorties à valider |
| Moteur | `DIAGNOSTIC_ENGINE` | Diagnostics à valider |
| Moteur | `REASONING_ENGINE` | Chaînes d'inférence à vérifier |
| Moteur | `KNOWLEDGE_ENGINE` | Contrôle de validité des connaissances utilisées |

## 5. Contrat d'interface

### Entrée — `ValidationRequest`

```
ValidationRequest = {
  requete_id    : UUID
  type_sortie   : enum { diagnostic, recommandation, ensemble_complet }
  contenu       : Diagnostic ou RecommendationSet
  chaines_inference : liste de Conclusion (optionnel)
  connaissances_utilisees : liste de UUID (KnowledgeObject)
}
```

### Sortie — `ValidationResult`

```
ValidationResult = {
  validation_id : UUID
  requete_origine : UUID
  statut        : enum { valide, bloque, partiellement_valide }
  controles     : liste de ControleResultat
  causes_blocage : liste de CauseBlocage (si statut = bloque)
  date_validation : ISO 8601
}

ControleResultat = {
  nom_controle  : texte
  resultat      : enum { conforme, non_conforme, non_applicable }
  details       : texte
}

CauseBlocage = {
  type_cause    : enum {
    sans_niveau_preuve,
    sans_source,
    sans_chaine_inference,
    hors_domaine_validite,
    connaissance_obsolete,
    contradiction_non_signalee,
    recommandation_non_contournable,
    explicabilite_insuffisante
  }
  element_concerne : UUID
  description   : texte
}
```

## 6. Garanties

- **Aucune sortie n'atteint l'utilisateur sans validation** — la
  validation est le dernier rempart (principe fondateur).
- Toute sortie validée respecte la Constitution : explicabilité
  (`GSIE-CON-004`), traçabilité (`GSIE-CON-005`), niveaux de preuve
  affichés (`GSIE-CON-002`), recommandations contournables
  (`GSIE-CON-001`).
- Toute sortie bloquée est journalisée avec la cause précise de
  blocage.
- Le moteur ne produit **pas de contenu** — il valide et filtre
  (séparation des responsabilités).
- Les connaissances obsolètes ou invalidées sont détectées et signalées.
- Les sorties hors domaine de validité sont bloquées avec justification.

## 7. Cas d'usage

### Cas 1 — Blocage d'une recommandation sans niveau de preuve

Le Recommendation Engine produit une recommandation de plantation
d'eucalyptus. Le Validation Engine détecte qu'aucune source
scientifique ne justifie l'adaptation de l'eucalyptus à la station
(règle non sourcée). Cause de blocage : `sans_niveau_preuve` et
`sans_source`. La recommandation est bloquée et journalisée. L'erreur
est transmise au Learning Engine pour amélioration.

### Cas 2 — Validation d'un diagnostic complet

Un diagnostic de dépérissement de hêtraie est soumis. Le Validation
Engine vérifie : (1) toutes les contraintes ont un niveau de preuve →
conforme, (2) toutes les sources sont identifiées → conforme, (3) les
chaînes d'inférence sont complètes → conforme, (4) les connaissances
utilisées sont à jour (version courante du Knowledge Engine) →
conforme, (5) le diagnostic est étiqueté « diagnostic » et non
« décision » → conforme. Statut : `valide`. Le diagnostic est présenté
au forestier.

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*
