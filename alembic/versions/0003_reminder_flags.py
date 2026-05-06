"""add reminder_24h_sent and reminder_2h_sent to appointments

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-06 16:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column(
            "reminder_24h_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "appointments",
        sa.Column(
            "reminder_2h_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("appointments", "reminder_2h_sent")
    op.drop_column("appointments", "reminder_24h_sent")
