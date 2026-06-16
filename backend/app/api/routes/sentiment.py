from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.core.timezone_util import now
from app.models.sentiment import SentimentDaily
from app.models.tracked_assets import TrackedAssets
from app.schemas.api import SentimentDailyResponse

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/daily", response_model=list[SentimentDailyResponse])
@limiter.limit("60/minute")
def list_daily_sentiment(
    request: Request,
    symbol: Optional[str] = Query(default=None, description="Filter by ticker symbol"),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = now().date() - timedelta(days=days - 1)
    query = (
        db.query(SentimentDaily, TrackedAssets)
        .join(TrackedAssets, SentimentDaily.ticker_id == TrackedAssets.ticker_id)
        .filter(SentimentDaily.date >= start_date)
    )
    if symbol:
        query = query.filter(TrackedAssets.symbol == symbol.upper())

    rows = query.order_by(SentimentDaily.date.desc(), TrackedAssets.symbol).all()
    return [
        SentimentDailyResponse(
            symbol=asset.symbol,
            date=row.date,
            avg_sentiment=row.avg_sentiment,
            article_count=row.article_count,
            momentum=row.momentum,
            std_div=row.std_div,
        )
        for row, asset in rows
    ]
