"""article_entities composite primary key

Allows multiple (article_id, ticker) rows per article.

Revision ID: f8c2a1b3d4e5
Revises: a4d6c01aa9ff
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f8c2a1b3d4e5"
down_revision: Union[str, None] = "a4d6c01aa9ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "article_entities_article_id_fkey", "article_entities", type_="foreignkey"
    )
    op.drop_constraint("article_entities_pkey", "article_entities", type_="primary")
    op.drop_index(op.f("ix_article_entities_article_id"), table_name="article_entities")
    op.create_primary_key(
        "article_entities_pkey", "article_entities", ["article_id", "ticker"]
    )
    op.create_foreign_key(
        "article_entities_article_id_fkey",
        "article_entities",
        "articles",
        ["article_id"],
        ["article_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Fails if more than one ticker row exists for the same article_id.
    op.drop_constraint(
        "article_entities_article_id_fkey", "article_entities", type_="foreignkey"
    )
    op.drop_constraint("article_entities_pkey", "article_entities", type_="primary")
    op.create_primary_key("article_entities_pkey", "article_entities", ["article_id"])
    op.create_index(
        op.f("ix_article_entities_article_id"),
        "article_entities",
        ["article_id"],
        unique=False,
    )
    op.create_foreign_key(
        "article_entities_article_id_fkey",
        "article_entities",
        "articles",
        ["article_id"],
        ["article_id"],
    )
