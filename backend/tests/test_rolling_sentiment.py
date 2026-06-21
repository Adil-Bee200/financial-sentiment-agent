"""Tests for article-weighted rolling sentiment."""

import uuid
from datetime import date

from app.models.sentiment import SentimentDaily
from app.services.sentiment.sentiment_service import SentimentService


def _row(day: date, avg: float, count: int) -> SentimentDaily:
    return SentimentDaily(
        ticker_id=uuid.uuid4(),
        date=day,
        avg_sentiment=avg,
        article_count=count,
        momentum=0.0,
    )


class TestRollingSentiment:
    def test_article_weighted_rolling_from_rows(self):
        rows = [
            _row(date(2026, 6, 11), 0.2, 2),
            _row(date(2026, 6, 12), 0.4, 4),
            _row(date(2026, 6, 13), 0.0, 0),
            _row(date(2026, 6, 14), 0.6, 2),
        ]
        result = SentimentService.article_weighted_rolling_sentiment_from_rows(
            rows,
            end_date=date(2026, 6, 14),
            window_days=7,
        )
        # (0.2*2 + 0.4*4 + 0.6*2) / (2+4+2) = 3.2/8 = 0.4
        assert result == 0.4

    def test_rolling_returns_none_when_no_articles(self):
        rows = [_row(date(2026, 6, 14), 0.5, 0)]
        assert (
            SentimentService.article_weighted_rolling_sentiment_from_rows(
                rows,
                end_date=date(2026, 6, 14),
                window_days=7,
            )
            is None
        )

    def test_rolling_uses_only_days_in_window(self):
        rows = [
            _row(date(2026, 6, 1), 1.0, 10),
            _row(date(2026, 6, 14), 0.0, 2),
        ]
        result = SentimentService.article_weighted_rolling_sentiment_from_rows(
            rows,
            end_date=date(2026, 6, 14),
            window_days=7,
        )
        assert result == 0.0
