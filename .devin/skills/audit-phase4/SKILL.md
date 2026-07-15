---
name: audit-phase4
description: Orchestrateur — audit complet Phase 4 (qualité + sécurité + gouvernance + couverture) en parallèle
triggers:
  - user
  - model
---

# Audit Phase 4 — Quintessences

Tu es l'orchestrateur d'audit. Quand l'utilisateur invoque `/audit-phase4`, tu lances **en parallèle** les audits suivants via des sous-agents, puis tu synthétises.

## Audits parallèles

### Audit 1 — Qualité code (sous-agent `qa`)

Lance un sous-agent avec le profil `qa` qui exécute :
```bash
mypy GSIE/ --strict
ruff check GSIE/
pytest GSIE/ --cov=GSIE --cov-report=term-missing --cov-fail-under=80
```
Et rapporte : erreurs mypy, erreurs ruff, couverture par moteur, tests échoués.

### Audit 2 — Sécurité (skill /securite-gsie)

Invoque `/securite-gsie` pour vérifier :
- Aucun secret dans git (`git log -S "SECRET" --oneline`)
- PyJWT utilisé (pas python-jose)
- Auth JWT sur tous les endpoints protégés
- Rate limiting configuré
- Inputs validés avec Pydantic
- Headers sécurité activés
- Dépendances auditées (`pip audit` si disponible)

### Audit 3 — Gouvernance (skill /gsie-governance)

Invoque `/gsie-governance` pour vérifier :
- Aucun document Locked modifié (`git log --all --oneline -- "00_CONSTITUTION/*.md"`)
- PROJECT_MEMORY.md à jour avec le dernier commit
- ROADMAP.md cohérente avec l'état réel
- Tous les DEC tracés dans 03_DECISIONS/
- CHANGELOG.md à jour

### Audit 4 — Documentation (sous-agent `documentation`)

Lance un sous-agent `documentation` qui vérifie :
- Chaque moteur a un README.md avec contrat d'interface
- Les statuts de documents sont corrects
- Les sources scientifiques sont citées
- Pas de document orphelin (référencé nulle part)

## Synthèse finale

Après réception des 4 audits, produit un rapport unique :

```markdown
## Rapport Audit Phase 4 — [date]

### Score global
| Dimension | Score | Statut |
|---|---|---|
| Qualité code | XX% | ✅/⚠️/❌ |
| Sécurité | XX% | ✅/⚠️/❌ |
| Gouvernance | XX% | ✅/⚠️/❌ |
| Documentation | XX% | ✅/⚠️/❌ |

### Problèmes P0 (bloquants)
- [liste]

### Problèmes P1 (élevés)
- [liste]

### Problèmes P2 (moyens)
- [liste]

### Recommandations
- [liste priorisée]
```
