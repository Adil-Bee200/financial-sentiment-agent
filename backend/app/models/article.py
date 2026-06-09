import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, PrimaryKeyConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Articles(Base):
    __tablename__ = "articles"

    article_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False, index=True)
    source = Column(Text, nullable=True)
    url = Column(Text, nullable=False, unique=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)

    entities = relationship(
        "ArticleEntities", back_populates="article", cascade="all, delete-orphan"
    )


class ArticleEntities(Base):
    __tablename__ = "article_entities"
    __table_args__ = (PrimaryKeyConstraint("article_id", "ticker_id", name="article_entities_pkey"),)

    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracked_assets.ticker_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    article = relationship("Articles", back_populates="entities")
    tracked_asset = relationship("TrackedAssets", back_populates="article_entities")
