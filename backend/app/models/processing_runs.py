import uuid

from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ProcessingRuns(Base):
    __tablename__ = "processing_runs"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    articles_fetched = Column(Integer, nullable=False, default=0)
    num_processed = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=True)
