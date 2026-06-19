from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alerts
from app.models.article import ArticleEntities, Articles
from app.models.processing_runs import ProcessingRuns
from app.models.tracked_assets import TrackedAssets


@dataclass(frozen=True)
class ProjectStats:
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


class ProjectStatsService:
    """Aggregate metrics for README, dashboards, and ops visibility."""

    def __init__(self, db: Session, recent_run_limit: int = 10):
        self.db = db
        self.recent_run_limit = recent_run_limit

    def get_stats(self) -> ProjectStats:
        tracked_tickers = self.db.query(func.count(TrackedAssets.ticker_id)).scalar() or 0
        completed_runs = (
            self.db.query(func.count(ProcessingRuns.run_id))
            .filter(ProcessingRuns.status == "completed")
            .scalar()
            or 0
        )
        total_articles = self.db.query(func.count(Articles.article_id)).scalar() or 0
        total_mentions = self.db.query(func.count()).select_from(ArticleEntities).scalar() or 0
        total_alerts = self.db.query(func.count(Alerts.alert_id)).scalar() or 0

        totals = self.db.query(
            func.coalesce(func.sum(ProcessingRuns.num_processed), 0),
            func.coalesce(func.sum(ProcessingRuns.estimated_llm_cost_usd), 0.0),
        ).filter(ProcessingRuns.status == "completed").one()

        recent = (
            self.db.query(ProcessingRuns)
            .filter(ProcessingRuns.status == "completed")
            .order_by(ProcessingRuns.started_at.desc())
            .limit(self.recent_run_limit)
            .all()
        )

        sample_size = len(recent)
        if sample_size == 0:
            return ProjectStats(
                tracked_tickers=tracked_tickers,
                completed_pipeline_runs=completed_runs,
                total_articles_stored=total_articles,
                total_ticker_mentions=total_mentions,
                total_alerts=total_alerts,
                total_articles_analyzed=int(totals[0]),
                total_estimated_llm_cost_usd=round(float(totals[1]), 4),
                recent_runs_sample_size=0,
                avg_articles_fetched=0.0,
                avg_articles_keyword_matched=0.0,
                avg_articles_analyzed=0.0,
                avg_run_duration_seconds=0.0,
                avg_estimated_llm_cost_usd=0.0,
                llm_selectivity_pct=0.0,
                keyword_filter_pass_rate_pct=0.0,
            )

        fetched_total = sum(r.articles_fetched for r in recent)
        keyword_total = sum(r.articles_keyword_matched for r in recent)
        analyzed_total = sum(r.num_processed for r in recent)
        cost_total = sum(r.estimated_llm_cost_usd for r in recent)

        duration_total = 0.0
        duration_count = 0
        for run in recent:
            if run.started_at and run.finished_at:
                duration_total += (run.finished_at - run.started_at).total_seconds()
                duration_count += 1

        avg_fetched = fetched_total / sample_size
        avg_keyword = keyword_total / sample_size
        avg_analyzed = analyzed_total / sample_size
        avg_cost = cost_total / sample_size
        avg_duration = duration_total / duration_count if duration_count else 0.0

        llm_selectivity = (analyzed_total / keyword_total * 100) if keyword_total else 0.0
        keyword_pass_rate = (keyword_total / fetched_total * 100) if fetched_total else 0.0

        return ProjectStats(
            tracked_tickers=tracked_tickers,
            completed_pipeline_runs=completed_runs,
            total_articles_stored=total_articles,
            total_ticker_mentions=total_mentions,
            total_alerts=total_alerts,
            total_articles_analyzed=int(totals[0]),
            total_estimated_llm_cost_usd=round(float(totals[1]), 4),
            recent_runs_sample_size=sample_size,
            avg_articles_fetched=round(avg_fetched, 1),
            avg_articles_keyword_matched=round(avg_keyword, 1),
            avg_articles_analyzed=round(avg_analyzed, 1),
            avg_run_duration_seconds=round(avg_duration, 1),
            avg_estimated_llm_cost_usd=round(avg_cost, 4),
            llm_selectivity_pct=round(llm_selectivity, 1),
            keyword_filter_pass_rate_pct=round(keyword_pass_rate, 1),
        )

    @staticmethod
    def run_duration_seconds(run: ProcessingRuns) -> Optional[float]:
        if run.started_at and run.finished_at:
            return round((run.finished_at - run.started_at).total_seconds(), 1)
        return None
