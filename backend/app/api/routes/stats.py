from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.schemas.api import ProjectStatsResponse
from app.services.stats.project_stats_service import ProjectStatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=ProjectStatsResponse)
@limiter.limit("60/minute")
def get_project_stats(request: Request, db: Session = Depends(get_db)):
    """Aggregate project metrics for dashboards and documentation."""
    stats = ProjectStatsService(db).get_stats()
    monthly_cost = round(stats.avg_estimated_llm_cost_usd * 30, 2)
    return ProjectStatsResponse(
        **stats.__dict__,
        estimated_monthly_llm_cost_usd=monthly_cost,
    )
