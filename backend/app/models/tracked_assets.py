import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TrackedAssets(Base):
    __tablename__ = "tracked_assets"

    ticker_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(16), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    company_name = Column(String(128), nullable=True)
    sector = Column(String(64), nullable=True)

    alerts = relationship("Alerts", back_populates="tracked_asset", cascade="all, delete-orphan")
    sentiment_daily = relationship(
        "SentimentDaily", back_populates="tracked_asset", cascade="all, delete-orphan"
    )
    article_entities = relationship(
        "ArticleEntities", back_populates="tracked_asset", cascade="all, delete-orphan"
    )
