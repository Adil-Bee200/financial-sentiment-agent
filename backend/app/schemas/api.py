from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TrackedAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker_id: UUID
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    created_at: datetime


class ArticleResponse(BaseModel):
    article_id: UUID
    title: str
    source: Optional[str] = None
    url: str
    published_at: datetime
    summary: Optional[str] = None
    symbol: str
    sentiment_score: Optional[float] = None
    confidence: float
    relevance_score: Optional[float] = None


class SentimentDailyResponse(BaseModel):
    symbol: str
    date: date
    avg_sentiment: float
    article_count: int
    momentum: Optional[float] = None
    std_div: Optional[float] = None


class AlertResponse(BaseModel):
    alert_id: UUID
    symbol: str
    trigger_reason: str
    sentiment_value: float
    created_at: datetime
