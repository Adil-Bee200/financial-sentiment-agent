from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl


class TrackedAsset(BaseModel):
    ticker_id: UUID
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    created_at: datetime


class TrackedAssetCreate(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None


class Alerts(BaseModel):
    alert_id: UUID
    ticker_id: UUID
    trigger_reason: str
    sentiment_value: float
    created_at: datetime


class SentimentDaily(BaseModel):
    ticker_id: UUID
    date: date
    avg_sentiment: float
    article_count: int
    momentum: Optional[float] = None
    std_div: Optional[float] = None


class ArticleEntities(BaseModel):
    article_id: UUID
    ticker_id: UUID
    confidence: float
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None
    processed_at: Optional[datetime] = None


class Articles(BaseModel):
    article_id: UUID
    title: str
    source: Optional[str] = None
    url: HttpUrl
    published_at: datetime
    summary: Optional[str] = None
    raw_text: Optional[str] = None


class ProcessingRun(BaseModel):
    run_id: UUID
    started_at: datetime
    finished_at: Optional[datetime] = None
    articles_fetched: int
    num_processed: int
    status: str
    raw_text: Optional[str] = None


class RelevanceResult(BaseModel):
    relevant: bool
    companies: List[str]
    confidence: float


class SentimentResult(BaseModel):
    sentiment_score: float
    sentiment_label: str
    confidence: float
