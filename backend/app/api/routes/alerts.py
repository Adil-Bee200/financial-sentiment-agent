from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.models.alert import Alerts
from app.models.tracked_assets import TrackedAssets
from app.schemas.api import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
@limiter.limit("60/minute")
def list_alerts(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Alerts, TrackedAssets)
        .join(TrackedAssets, Alerts.ticker_id == TrackedAssets.ticker_id)
        .order_by(Alerts.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        AlertResponse(
            alert_id=alert.alert_id,
            symbol=asset.symbol,
            trigger_reason=alert.trigger_reason,
            sentiment_value=alert.sentiment_value,
            created_at=alert.created_at,
        )
        for alert, asset in rows
    ]
