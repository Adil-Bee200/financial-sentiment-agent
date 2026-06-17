from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.sentiment_daily import build_sentiment_daily_response
from app.core.limiter import limiter
from app.core.timezone_util import now
from app.models.sentiment import SentimentDaily
from app.models.tracked_assets import TrackedAssets
from app.schemas.api import SentimentDailyResponse
from app.services.sentiment.sentiment_service import SentimentService

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
    sentiment = SentimentService(db)
    last_at = sentiment.get_last_analyzed_at_map(
        [(asset.symbol, row.date) for row, asset in rows]
    )

    return [
        build_sentiment_daily_response(
            asset.symbol,
            row,
            last_run_at=last_at.get((asset.symbol, row.date)),
        )
        for row, asset in rows
    ]
