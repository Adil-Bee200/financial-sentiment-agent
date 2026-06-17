from datetime import date, datetime
from typing import Optional

from app.core.config import settings
from app.core.timezone_util import (
    format_analysis_date_label,
    format_chart_axis_label,
    is_today_local,
)
from app.models.sentiment import SentimentDaily
from app.schemas.api import SentimentDailyResponse


def build_sentiment_daily_response(
    symbol: str,
    row: SentimentDaily,
    last_run_at: Optional[datetime] = None,
) -> SentimentDailyResponse:
    analysis_date: date = row.date
    return SentimentDailyResponse(
        symbol=symbol,
        analysis_date=analysis_date,
        analysis_date_label=format_analysis_date_label(analysis_date),
        chart_axis_label=format_chart_axis_label(analysis_date),
        timezone=settings.APP_TIMEZONE,
        avg_sentiment=row.avg_sentiment,
        article_count=row.article_count,
        momentum=row.momentum,
        std_div=row.std_div,
        last_run_at=last_run_at,
        is_current_analysis_day=is_today_local(analysis_date),
    )
