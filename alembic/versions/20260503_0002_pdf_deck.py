"""pdf upload fields and exercise_deck

Revision ID: 20260503_0002
Revises: 20260503_0001
Create Date: 2026-05-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_0002"
down_revision: Union[str, None] = "20260503_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("material", sa.Column("pdf_original_name", sa.String(length=512), nullable=True))
    op.add_column("material", sa.Column("pdf_stored_path", sa.String(length=512), nullable=True))
    op.create_table(
        "exercise_deck",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("exercise_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["material.id"], ondelete="CASCADE"),
    )
    op.add_column("exercise", sa.Column("deck_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_exercise_deck_id",
        "exercise",
        "exercise_deck",
        ["deck_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_exercise_deck_id", "exercise", type_="foreignkey")
    op.drop_column("exercise", "deck_id")
    op.drop_table("exercise_deck")
    op.drop_column("material", "pdf_stored_path")
    op.drop_column("material", "pdf_original_name")
