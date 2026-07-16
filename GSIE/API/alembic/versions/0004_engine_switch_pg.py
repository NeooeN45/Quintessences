"""Migration 0004 — Bascule des moteurs vers le schéma v6.2

Étape 3/4 du plan de migration progressive (ADR-004 Validated).

Cette migration bascule les moteurs GSIE du store in-memory vers le
repository PG sur le schéma v6.2. Elle inclut :
- L'adaptation du Knowledge Engine (engine.py) pour utiliser le repository PG
- L'adaptation des tests Python (33 tests Knowledge + 11 tests pipeline)
- Un feature flag `gsie_engine_backend=pg|memory` pour le repli

⚠️ Cette migration est un placeholder — elle sera complétée lors de la
bascule effective des moteurs (Vague 1, après validation des migrations
0002 et 0003 sur une base de test).

Rollback : repli sur le store in-memory via feature flag
(gsie_engine_backend=memory). Aucune modification de schéma.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Bascule des moteurs vers le repository PG sur schéma v6.2.

    ⚠️ Placeholder — à compléter lors de la bascule effective.

    Actions prévues :
    1. Vérifier que les données v6.2 sont présentes (count assertion = count knowledge_objects)
    2. Activer le feature flag gsie_engine_backend=pg
    3. Lancer les tests adaptés (33 Knowledge + 11 pipeline)
    4. Si échec : repli sur gsie_engine_backend=memory (downgrade implicite)
    """
    # Vérification de cohérence (non-bloquante, warning dans les logs)
    op.execute("""
        DO $$
        DECLARE
            v6_1_count INTEGER;
            v6_2_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v6_1_count FROM knowledge_objects;
            SELECT COUNT(*) INTO v6_2_count FROM assertion;
            IF v6_1_count != v6_2_count THEN
                RAISE NOTICE '⚠️ Incohérence migration : knowledge_objects=%, assertion=%', v6_1_count, v6_2_count;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Repli sur le store in-memory via feature flag.

    Aucune modification de schéma — le repli se fait par configuration
    (gsie_engine_backend=memory dans .env).
    """
    pass
