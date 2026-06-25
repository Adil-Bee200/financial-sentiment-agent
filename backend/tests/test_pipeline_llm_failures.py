"""Tests for pipeline LLM failure handling and run status."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.models.tracked_assets import TrackedAssets
from app.schemas.schemas_v1 import SentimentResult
from app.services.llm.ai_service import ArticleAnalysis, LlmUsage
from app.services.pipeline.pipeline_service import PipelineService


def _asset(symbol: str) -> TrackedAssets:
    return TrackedAssets(ticker_id=uuid4(), symbol=symbol)


def _nvda_article(index: int = 0) -> dict:
    return {
        "title": f"NVDA beats earnings {index}",
        "url": f"https://example.com/nvda-{index}",
        "publishedAt": f"2026-06-07T{10 - index:02d}:00:00Z",
        "source": {"name": "Reuters"},
        "description": "NVIDIA NVDA strong quarter and AI demand",
        "content": "NVIDIA reported strong earnings driven by AI chip demand.",
    }


def _success_analysis(summary: str = "Strong NVDA quarter.") -> ArticleAnalysis:
    return ArticleAnalysis(
        ok=True,
        summary=summary,
        sentiment=SentimentResult(
            sentiment_score=0.6,
            sentiment_label="positive",
            confidence=0.9,
        ),
        usage=LlmUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
    )


def _failed_analysis(error_kind: str, message: str = "failed") -> ArticleAnalysis:
    return ArticleAnalysis(ok=False, error_kind=error_kind, error_message=message)


@pytest.fixture
def pipeline_setup():
    db = Mock()
    run = Mock()
    run.run_id = uuid4()
    run.articles_fetched = 0

    with patch("app.services.pipeline.pipeline_service.ArticleIngestionService"):
        service = PipelineService(db)

    service.assets = Mock()
    service.assets.list_all.return_value = [_asset("NVDA")]
    service.ingestion = Mock()
    service.ingestion.build_date_range.return_value = ("2026-06-06T00:00:00", "2026-06-07T00:00:00")
    service._sentiment = Mock()
    service._alerts = Mock()
    service.alerts.evaluate_all_tracked.return_value = 0
    service._llm = Mock()

    return service, db, run


class TestResolveRunStatus:
    def test_completed_when_no_failures(self):
        assert PipelineService._resolve_run_status(
            auth_failure=False, processed=3, llm_failed=0, keyword_matched=3
        ) == "completed"

    def test_partial_when_some_failures(self):
        assert PipelineService._resolve_run_status(
            auth_failure=False, processed=2, llm_failed=1, keyword_matched=3
        ) == "partial"

    def test_error_on_auth_failure(self):
        assert PipelineService._resolve_run_status(
            auth_failure=True, processed=0, llm_failed=1, keyword_matched=3
        ) == "error"

    def test_error_when_all_llm_calls_fail(self):
        assert PipelineService._resolve_run_status(
            auth_failure=False, processed=0, llm_failed=3, keyword_matched=3
        ) == "error"


class TestPipelineLlmFailures:
    def test_auth_failure_aborts_without_storing_articles(self, pipeline_setup):
        service, db, run = pipeline_setup
        articles = [_nvda_article(0), _nvda_article(1)]
        service.ingestion.fetch_for_pipeline.return_value = articles
        service.ingestion.filter_new_articles.return_value = articles
        service._llm.analyze_article.return_value = _failed_analysis("auth", "invalid key")

        with patch(
            "app.services.pipeline.pipeline_service.remaining_llm_budget_for_run",
            return_value=5,
        ), patch(
            "app.services.pipeline.pipeline_service.count_llm_articles_today",
            return_value=0,
        ), patch(
            "app.services.pipeline.pipeline_service.app_now",
            return_value=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
        ):
            result = service._execute(run)

        assert result.status == "error"
        assert result.articles_processed == 0
        assert result.articles_llm_failed == 1
        assert result.error == "invalid key"
        assert service._llm.analyze_article.call_count == 1
        db.add.assert_not_called()
        assert run.status == "error"
        assert "auth_error=invalid key" in run.raw_text
        assert run.articles_llm_failed == 1

    def test_partial_when_some_articles_fail(self, pipeline_setup):
        service, db, run = pipeline_setup
        articles = [_nvda_article(0), _nvda_article(1)]
        service.ingestion.fetch_for_pipeline.return_value = articles
        service.ingestion.filter_new_articles.return_value = articles
        service._llm.analyze_article.side_effect = [
            _failed_analysis("rate_limit", "rate limited"),
            _success_analysis(),
        ]

        with patch(
            "app.services.pipeline.pipeline_service.remaining_llm_budget_for_run",
            return_value=5,
        ), patch(
            "app.services.pipeline.pipeline_service.count_llm_articles_today",
            return_value=0,
        ), patch(
            "app.services.pipeline.pipeline_service.app_now",
            return_value=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
        ):
            result = service._execute(run)

        assert result.status == "partial"
        assert result.articles_processed == 1
        assert result.articles_llm_failed == 1
        assert result.error is None
        assert service._llm.analyze_article.call_count == 2
        assert run.articles_llm_failed == 1
        assert run.status == "partial"

    def test_error_when_every_llm_call_fails(self, pipeline_setup):
        service, db, run = pipeline_setup
        articles = [_nvda_article(0), _nvda_article(1)]
        service.ingestion.fetch_for_pipeline.return_value = articles
        service.ingestion.filter_new_articles.return_value = articles
        service._llm.analyze_article.side_effect = [
            _failed_analysis("timeout", "timed out"),
            _failed_analysis("server", "server error"),
        ]

        with patch(
            "app.services.pipeline.pipeline_service.remaining_llm_budget_for_run",
            return_value=5,
        ), patch(
            "app.services.pipeline.pipeline_service.count_llm_articles_today",
            return_value=0,
        ), patch(
            "app.services.pipeline.pipeline_service.app_now",
            return_value=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
        ):
            result = service._execute(run)

        assert result.status == "error"
        assert result.articles_processed == 0
        assert result.articles_llm_failed == 2
        assert result.error == "All 2 LLM call(s) failed"
        db.add.assert_not_called()

    def test_completed_when_no_keyword_matches(self, pipeline_setup):
        service, db, run = pipeline_setup
        articles = [
            {
                "title": "Weather forecast",
                "url": "https://example.com/weather",
                "publishedAt": "2026-06-07T09:00:00Z",
                "source": {"name": "Local News"},
                "description": "Sunny skies ahead",
            }
        ]
        service.ingestion.fetch_for_pipeline.return_value = articles
        service.ingestion.filter_new_articles.return_value = articles

        with patch(
            "app.services.pipeline.pipeline_service.remaining_llm_budget_for_run",
            return_value=5,
        ), patch(
            "app.services.pipeline.pipeline_service.count_llm_articles_today",
            return_value=0,
        ), patch(
            "app.services.pipeline.pipeline_service.app_now",
            return_value=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
        ):
            result = service._execute(run)

        assert result.status == "completed"
        assert result.articles_processed == 0
        assert result.articles_llm_failed == 0
        service._llm.analyze_article.assert_not_called()
