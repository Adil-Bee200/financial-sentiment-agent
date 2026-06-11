"""v3 schema: UUID PKs, tracked_assets hub, processing_runs

Revision ID: c9d1e2f3a4b5
Revises: f8c2a1b3d4e5
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c9d1e2f3a4b5"
down_revision: Union[str, None] = "f8c2a1b3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # Drop legacy v1/v2 tables (destructive — no prod data assumed)
    op.execute("DROP TABLE IF EXISTS alerts CASCADE")
    op.execute("DROP TABLE IF EXISTS article_entities CASCADE")
    op.execute("DROP TABLE IF EXISTS sentiment_daily CASCADE")
    op.execute("DROP TABLE IF EXISTS portfolio_tickers CASCADE")
    op.execute("DROP TABLE IF EXISTS portfolios CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS articles CASCADE")
    op.execute("DROP TABLE IF EXISTS processing_runs CASCADE")
    op.execute("DROP TABLE IF EXISTS tracked_assets CASCADE")

    op.create_table(
        "tracked_assets",
        sa.Column(
            "ticker_id",
            UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(length=128), nullable=True),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.UniqueConstraint("symbol", name="uq_tracked_assets_symbol"),
    )
    op.create_index(op.f("ix_tracked_assets_symbol"), "tracked_assets", ["symbol"], unique=False)

    op.create_table(
        "articles",
        sa.Column(
            "article_id",
            UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.UniqueConstraint("url", name="uq_articles_url"),
    )
    op.create_index(op.f("ix_articles_published_at"), "articles", ["published_at"], unique=False)
    op.create_index(op.f("ix_articles_title"), "articles", ["title"], unique=False)

    op.create_table(
        "article_entities",
        sa.Column("article_id", UUID, nullable=False),
        sa.Column("ticker_id", UUID, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.article_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticker_id"], ["tracked_assets.ticker_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "ticker_id", name="article_entities_pkey"),
    )
    op.create_index(
        op.f("ix_article_entities_ticker_id"), "article_entities", ["ticker_id"], unique=False
    )

    op.create_table(
        "sentiment_daily",
        sa.Column("ticker_id", UUID, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("avg_sentiment", sa.Float(), nullable=False),
        sa.Column("article_count", sa.Integer(), nullable=False),
        sa.Column("momentum", sa.Float(), nullable=True),
        sa.Column("std_div", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["ticker_id"], ["tracked_assets.ticker_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ticker_id", "date", name="sentiment_daily_pkey"),
    )
    op.create_index(op.f("ix_sentiment_daily_date"), "sentiment_daily", ["date"], unique=False)

    op.create_table(
        "alerts",
        sa.Column(
            "alert_id",
            UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("ticker_id", UUID, nullable=False),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("sentiment_value", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticker_id"], ["tracked_assets.ticker_id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_alerts_created_at"), "alerts", ["created_at"], unique=False)
    op.create_index(op.f("ix_alerts_ticker_id"), "alerts", ["ticker_id"], unique=False)

    op.create_table(
        "processing_runs",
        sa.Column(
            "run_id",
            UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("articles_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("num_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("processing_runs")
    op.drop_index(op.f("ix_alerts_ticker_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_sentiment_daily_date"), table_name="sentiment_daily")
    op.drop_table("sentiment_daily")
    op.drop_index(op.f("ix_article_entities_ticker_id"), table_name="article_entities")
    op.drop_table("article_entities")
    op.drop_index(op.f("ix_articles_title"), table_name="articles")
    op.drop_index(op.f("ix_articles_published_at"), table_name="articles")
    op.drop_table("articles")
    op.drop_index(op.f("ix_tracked_assets_symbol"), table_name="tracked_assets")
    op.drop_table("tracked_assets")
