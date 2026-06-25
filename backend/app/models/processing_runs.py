import uuid

from sqlalchemy import Column, DateTime, Float, Integer, Text
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
    articles_keyword_matched = Column(Integer, nullable=False, default=0)
    articles_skipped_llm_limit = Column(Integer, nullable=False, default=0)
    articles_llm_failed = Column(Integer, nullable=False, default=0)
    alerts_created = Column(Integer, nullable=False, default=0)
    llm_prompt_tokens = Column(Integer, nullable=False, default=0)
    llm_completion_tokens = Column(Integer, nullable=False, default=0)
    estimated_llm_cost_usd = Column(Float, nullable=False, default=0.0)
    status = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=True)
