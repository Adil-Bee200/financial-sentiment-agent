"""processing run llm failure count

Revision ID: d3a8f1c2b9e0
Revises: b7e4f2a1c9d0
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d3a8f1c2b9e0"
down_revision: Union[str, None] = "b7e4f2a1c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column("articles_llm_failed", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("processing_runs", "articles_llm_failed")
