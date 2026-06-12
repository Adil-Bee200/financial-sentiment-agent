from unittest.mock import Mock, patch
from uuid import uuid4

from app.models.tracked_assets import TrackedAssets
from app.services.pipeline.pipeline_service import PipelineService


def _asset(symbol: str) -> TrackedAssets:
    return TrackedAssets(ticker_id=uuid4(), symbol=symbol)


class TestPipelinePreview:
    def test_preview_matches_without_llm(self):
        db = Mock()
        nvda = _asset("NVDA")
        aapl = _asset("AAPL")

        assets = Mock()
        assets.list_all.return_value = [nvda, aapl]

        fetched = [
            {
                "title": "NVDA beats earnings",
                "url": "https://example.com/nvda",
                "publishedAt": "2026-06-07T10:00:00Z",
                "source": {"name": "Reuters"},
                "description": "NVIDIA NVDA strong quarter",
            },
            {
                "title": "Weather forecast",
                "url": "https://example.com/weather",
                "publishedAt": "2026-06-07T09:00:00Z",
                "source": {"name": "Local News"},
                "description": "Sunny skies ahead",
            },
        ]

        with patch("app.services.pipeline.pipeline_service.ArticleIngestionService"):
            service = PipelineService(db)
        service.assets = assets
        service.ingestion = Mock()
        service.ingestion.build_date_range.return_value = ("2026-06-06T00:00:00", "2026-06-07T00:00:00")
        service.ingestion.fetch_for_pipeline.return_value = fetched
        service.ingestion.filter_new_articles.return_value = fetched

        with patch(
            "app.services.pipeline.pipeline_service.remaining_llm_budget_for_run",
            return_value=5,
        ):
            result = service.preview()

        assert result.status == "completed"
        assert result.articles_fetched == 2
        assert result.articles_new == 2
        assert result.articles_keyword_matched == 1
        assert result.articles_skipped_no_keyword == 1
        assert result.articles_would_llm == 1
        assert len(result.matched_articles) == 1
        assert result.matched_articles[0].title == "NVDA beats earnings"
        assert result.matched_articles[0].symbols == ["NVDA"]
        assert result.matched_articles[0].would_send_to_llm is True
        assert service._llm is None

    def test_preview_respects_llm_budget(self):
        db = Mock()
        assets = Mock()
        assets.list_all.return_value = [_asset("NVDA")]

        articles = [
            {
                "title": f"NVDA news {index}",
                "url": f"https://example.com/{index}",
                "publishedAt": f"2026-06-07T{10 - index:02d}:00:00Z",
                "source": {"name": "Reuters"},
                "description": "NVDA update",
            }
            for index in range(3)
        ]

        with patch("app.services.pipeline.pipeline_service.ArticleIngestionService"):
            service = PipelineService(db)
        service.assets = assets
        service.ingestion = Mock()
        service.ingestion.build_date_range.return_value = ("2026-06-06T00:00:00", "2026-06-07T00:00:00")
        service.ingestion.fetch_for_pipeline.return_value = articles
        service.ingestion.filter_new_articles.return_value = articles

        with patch(
            "app.services.pipeline.pipeline_service.remaining_llm_budget_for_run",
            return_value=1,
        ):
            result = service.preview()

        assert result.articles_keyword_matched == 3
        assert result.articles_would_llm == 1
        assert result.articles_over_llm_budget == 2
        llm_flags = [article.would_send_to_llm for article in result.matched_articles]
        assert llm_flags == [True, False, False]

    def test_preview_without_tracked_assets(self):
        db = Mock()
        with patch("app.services.pipeline.pipeline_service.ArticleIngestionService"):
            service = PipelineService(db)
        service.assets = Mock()
        service.assets.list_all.return_value = []

        result = service.preview()

        assert result.status == "completed"
        assert result.tracked_symbol_count == 0
        assert result.matched_articles == []
