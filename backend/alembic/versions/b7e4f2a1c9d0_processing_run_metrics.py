"""processing run metrics for stats and cost tracking

Revision ID: b7e4f2a1c9d0
Revises: c9d1e2f3a4b5
Create Date: 2026-06-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7e4f2a1c9d0"
down_revision: Union[str, None] = "c9d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column("articles_keyword_matched", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "processing_runs",
        sa.Column("articles_skipped_llm_limit", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "processing_runs",
        sa.Column("alerts_created", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "processing_runs",
        sa.Column("llm_prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "processing_runs",
        sa.Column("llm_completion_tokens", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "processing_runs",
        sa.Column("estimated_llm_cost_usd", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("processing_runs", "estimated_llm_cost_usd")
    op.drop_column("processing_runs", "llm_completion_tokens")
    op.drop_column("processing_runs", "llm_prompt_tokens")
    op.drop_column("processing_runs", "alerts_created")
    op.drop_column("processing_runs", "articles_skipped_llm_limit")
    op.drop_column("processing_runs", "articles_keyword_matched")
