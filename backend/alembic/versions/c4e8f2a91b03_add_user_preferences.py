"""Add user preferences JSONB column

Revision ID: c4e8f2a91b03
Revises: 1b54abd0550f
Create Date: 2026-11-12 07:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c4e8f2a91b03"
down_revision: Union[str, Sequence[str], None] = "1b54abd0550f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_PREFS = (
    '{"email_notifications": true, "processing_alerts": true, '
    '"dark_mode": false, "show_confidence": true, "auto_process": false}'
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(f"'{DEFAULT_PREFS}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "preferences")
