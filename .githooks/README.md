# Hooks Git versionnés — Quintessences

Ces hooks remplacent les scripts historiquement stockés dans `.git/hooks/`
(non versionnés). Ils appliquent les gardes-fous de gouvernance et de
sécurité du projet.

## Activation (une fois par clone)

```bash
git config core.hooksPath .githooks
```

## Contenu

| Hook | Rôle | Bloquant |
|---|---|---|
| `pre-commit` | Cohérence de gouvernance + scan secrets du diff stagé | Oui |
| `post-commit` | Diagnostic sécurité rapide en arrière-plan | Non |
| `pre-push` | Diagnostic complet : secrets, config, Bandit, pip-audit, npm-audit | Oui |

Contournement d'urgence (à tracer) : `git push --no-verify`.
