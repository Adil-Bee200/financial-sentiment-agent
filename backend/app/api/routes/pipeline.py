from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.models.alert import Alerts
from app.models.processing_runs import ProcessingRuns
from app.schemas.api import PipelineStatusResponse

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Observed typical run cost until token usage is tracked in the DB.
_OBSERVED_LLM_COST_PER_RUN = 0.05


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

    return PipelineStatusResponse(
        run_id=run.run_id,
        status=run.status,
        last_run=window_end or run.started_at,
        started_at=run.started_at,
        articles_fetched=run.articles_fetched,
        articles_analyzed=run.num_processed,
        estimated_llm_cost=_OBSERVED_LLM_COST_PER_RUN,
        alerts_triggered=alerts_query.count(),
    )
