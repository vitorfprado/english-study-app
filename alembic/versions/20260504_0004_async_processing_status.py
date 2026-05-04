"""async processing status fields

Revision ID: 20260504_0004
Revises: 20260503_0003
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260504_0004"
down_revision: Union[str, None] = "20260503_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "material",
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="completed"),
    )
    op.add_column("material", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column(
        "exercise_deck",
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="completed"),
    )
    op.add_column("exercise_deck", sa.Column("processing_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercise_deck", "processing_error")
    op.drop_column("exercise_deck", "processing_status")
    op.drop_column("material", "processing_error")
    op.drop_column("material", "processing_status")
