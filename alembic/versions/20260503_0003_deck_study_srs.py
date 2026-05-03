"""deck study run and exercise srs

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_0003"
down_revision: Union[str, None] = "20260503_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deck_study_run",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("queue_ids_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["deck_id"], ["exercise_deck.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "exercise_srs",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("interval_days", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("ease", sa.Float(), nullable=False, server_default=sa.text("2.5")),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("lapses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exercise_id"),
    )


def downgrade() -> None:
    op.drop_table("exercise_srs")
    op.drop_table("deck_study_run")
