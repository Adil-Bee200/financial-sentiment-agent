import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Alerts(Base):
    __tablename__ = "alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracked_assets.ticker_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger_reason = Column(Text, nullable=False)
    sentiment_value = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    tracked_asset = relationship("TrackedAssets", back_populates="alerts")
