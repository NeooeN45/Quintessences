---
name: naming-conventions
description: Conventions de nommage GSIE — identifiants tracés, fichiers, variables, DB
triggers:
  - user
  - model
---

# Conventions de nommage Quintessences

## Identifiants tracés (obligatoires)

| Préfixe | Usage | Exemple |
|---|---|---|
| `GSIE-FND-xxx` | Documents fondateurs | `GSIE-FND-001.md` |
| `GSIE-CON-xxx` | Articles constitutionnels | `GSIE-CON-007.md` |
| `GSIE-DIR-xxxx` | Directives | `GSIE-DIR-0011.md` |
| `RFC-xxxx` | Propositions d'évolution | `RFC-0004.md` |
| `DEC-xxxxxx` | Décisions tracées | `DEC-000018.md` |
| `GSIE-PROMPT-xxxx` | Prompts versionnés | `GSIE-PROMPT-0001.md` |
| `DS-xxx` | Datasets catalogués | `DS-029` |

## Code Python (moteurs + API)

```python
# Variables : snake_case, noms révélateurs d'intention
forest_plot_count = 42        # ✓
n = 42                         # ✗

# Booléens : préfixe is/has/can/should
is_validated = True
has_geolocation = True
can_process_batch = False

# Constantes : SCREAMING_SNAKE
MAX_BATCH_SIZE = 100
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
SRID_WGS84 = 4326

# Fonctions : verbes d'action
def fetch_evidence_records():  # ✓
def evidence():                # ✗

# Classes : PascalCase
class EvidenceEngine:
class ForestPlotRepository:
```

## Kotlin (GeoSylva Android)

```kotlin
// Pas de !! — utiliser ?.let ou require
val name = plot?.name ?: return  // ✓
val name = plot!!.name            // ✗

// Pas d'Any non typé
fun processPlot(plot: ForestPlot): Result  // ✓
fun processPlot(data: Any): Any            // ✗
```

## Fichiers et dossiers

- Documentation : `SCREAMING_SNAKE_CASE.md` (ex: `EVIDENCE_FRAMEWORK.md`)
- Modules Python : `snake_case.py`
- Classes Python : `PascalCase` dans `snake_case.py`
- Dossiers : `SCREAMING_SNAKE_CASE` pour la documentation, `snake_case` pour le code

## Base de données

- Tables : `snake_case` pluriel
- Colonnes : `snake_case`
- Index : `idx_{table}_{colonne}`
- Contraintes : `fk_{table}_{ref}`, `uq_{table}_{colonne}`, `ck_{table}_{condition}`
