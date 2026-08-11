"""Référence du Customer Stripe associé au propriétaire de facturation.

Révision: 20260805_0039
Précède: 20260805_0038
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260805_0039"
down_revision: str | None = "20260805_0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_billing"


def upgrade() -> None:
    op.add_column(
        "subscription",
        sa.Column("provider_customer_id", sa.String(255), nullable=True),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_subscription_provider_customer",
        "subscription",
        ["provider", "provider_customer_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("idx_subscription_provider_customer", table_name="subscription", schema=_SCHEMA)
    op.drop_column("subscription", "provider_customer_id", schema=_SCHEMA)
