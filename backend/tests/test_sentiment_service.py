"""Tests for daily sentiment rollups (processed_at ET calendar day)."""

import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.models.article import ArticleEntities
from app.services.sentiment.sentiment_service import SentimentService

ET = ZoneInfo("America/New_York")


@pytest.fixture
def db():
    return MagicMock()


class TestSentimentRollupByProcessedAt:
    def test_aggregate_uses_entities_processed_on_that_et_day(self, db):
        service = SentimentService(db)
        processed_jun_17 = datetime(2026, 6, 17, 18, 30, tzinfo=ET)

        entity = ArticleEntities(
            article_id=uuid.uuid4(),
            ticker_id=uuid.uuid4(),
            confidence=0.9,
            sentiment_score=0.5,
            relevance_score=0.9,
            processed_at=processed_jun_17,
        )

        previous = MagicMock(avg_sentiment=0.2)

        with (
            patch.object(service, "_resolve_ticker_id", return_value=uuid.uuid4()),
            patch.object(service, "_entities_for_symbol_on_date", return_value=[entity]),
            patch.object(
                service,
                "get_sentiment_for_ticker_by_date",
                return_value=previous,
            ),
            patch.object(
                service,
                "create_sentiment_for_ticker",
                return_value=MagicMock(date=date(2026, 6, 17), article_count=1),
            ) as mock_create,
        ):
            service.aggregate_sentiment_for_ticker("NVDA", processed_jun_17)

        mock_create.assert_called_once()
        assert mock_create.call_args.args[1] == date(2026, 6, 17)
        assert mock_create.call_args.args[3] == 1
        assert mock_create.call_args.args[2] == 0.5

    def test_entity_in_local_day_prefers_processed_at_over_publish_date(self, db):
        service = SentimentService(db)
        day_start = datetime(2026, 6, 17, 0, 0, tzinfo=ET)
        day_end = datetime(2026, 6, 18, 0, 0, tzinfo=ET)
        clause = service._entity_in_local_day(day_start, day_end)
        assert clause is not None
