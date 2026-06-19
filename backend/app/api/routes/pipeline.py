from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.core.config import settings
from app.models.alert import Alerts
from app.models.processing_runs import ProcessingRuns
from app.schemas.api import PipelineStatusResponse
from app.services.stats.project_stats_service import ProjectStatsService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status", response_model=PipelineStatusResponse)
@limiter.limit("60/minute")
def get_pipeline_status(request: Request, db: Session = Depends(get_db)):
    """Latest pipeline run metrics from processing_runs + alerts in that window."""
    run = (
        db.query(ProcessingRuns)
        .order_by(ProcessingRuns.started_at.desc())
        .first()
    )
    if not run:
        return PipelineStatusResponse(status="no_runs")

    window_end = run.finished_at
    alerts_query = db.query(Alerts).filter(Alerts.created_at >= run.started_at)
    if window_end is not None:
        alerts_query = alerts_query.filter(Alerts.created_at <= window_end)

    cost = run.estimated_llm_cost_usd if run.estimated_llm_cost_usd > 0 else 0.0

    return PipelineStatusResponse(
        run_id=run.run_id,
        status=run.status,
        last_run_at=window_end or run.started_at,
        started_at=run.started_at,
        timezone=settings.APP_TIMEZONE,
        articles_fetched=run.articles_fetched,
        articles_keyword_matched=run.articles_keyword_matched,
        articles_analyzed=run.num_processed,
        articles_skipped_llm_limit=run.articles_skipped_llm_limit,
        run_duration_seconds=ProjectStatsService.run_duration_seconds(run),
        estimated_llm_cost=cost,
        llm_prompt_tokens=run.llm_prompt_tokens,
        llm_completion_tokens=run.llm_completion_tokens,
        alerts_triggered=alerts_query.count(),
    )
