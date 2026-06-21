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
    analyzed_at: Optional[datetime] = None
    published_at_label: Optional[str] = None
    analyzed_at_label: Optional[str] = None
    summary: Optional[str] = None
    symbol: str
    sentiment_score: Optional[float] = None
    confidence: float
    relevance_score: Optional[float] = None


class SentimentDailyResponse(BaseModel):
    symbol: str
    analysis_date: date
    analysis_date_label: str
    chart_axis_label: str
    timezone: str
    avg_sentiment: float
    article_count: int
    momentum: Optional[float] = None
    rolling_7d_sentiment: Optional[float] = None
    std_div: Optional[float] = None
    last_run_at: Optional[datetime] = None
    is_current_analysis_day: bool = False


class AlertResponse(BaseModel):
    alert_id: UUID
    symbol: str
    trigger_reason: str
    sentiment_value: float
    created_at: datetime


class PipelineStatusResponse(BaseModel):
    run_id: Optional[UUID] = None
    status: str
    last_run_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    timezone: str = "America/New_York"
    articles_fetched: int = 0
    articles_keyword_matched: int = 0
    articles_analyzed: int = 0
    articles_skipped_llm_limit: int = 0
    run_duration_seconds: Optional[float] = None
    estimated_llm_cost: float = 0.0
    llm_prompt_tokens: int = 0
    llm_completion_tokens: int = 0
    alerts_triggered: int = 0


class ProjectStatsResponse(BaseModel):
    tracked_tickers: int
    completed_pipeline_runs: int
    total_articles_stored: int
    total_ticker_mentions: int
    total_alerts: int
    total_articles_analyzed: int
    total_estimated_llm_cost_usd: float
    recent_runs_sample_size: int
    avg_articles_fetched: float
    avg_articles_keyword_matched: float
    avg_articles_analyzed: float
    avg_run_duration_seconds: float
    avg_estimated_llm_cost_usd: float
    llm_selectivity_pct: float
    keyword_filter_pass_rate_pct: float
    estimated_monthly_llm_cost_usd: float
