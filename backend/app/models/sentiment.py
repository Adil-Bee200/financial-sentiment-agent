from sqlalchemy import Column, Date, Float, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SentimentDaily(Base):
    __tablename__ = "sentiment_daily"
    __table_args__ = (PrimaryKeyConstraint("ticker_id", "date", name="sentiment_daily_pkey"),)

    ticker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracked_assets.ticker_id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(Date, nullable=False, index=True)
    avg_sentiment = Column(Float, nullable=False)
    article_count = Column(Integer, nullable=False, default=0)
    momentum = Column(Float, nullable=True)
    std_div = Column(Float, nullable=True)

    tracked_asset = relationship("TrackedAssets", back_populates="sentiment_daily")
