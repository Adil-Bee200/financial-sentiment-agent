import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.alert import Alerts
from app.models.article import ArticleEntities, Articles
from app.models.processing_runs import ProcessingRuns
from app.models.sentiment import SentimentDaily
from app.models.tracked_assets import TrackedAssets


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestHealth:
    def test_health_returns_ok(self, client, mock_db):
        mock_db.execute.return_value = None
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "connected"}


class TestTrackedAssets:
    def test_list_tracked_assets(self, client, mock_db):
        ticker_id = uuid.uuid4()
        created_at = datetime(2026, 6, 12, tzinfo=timezone.utc)
        asset = TrackedAssets(
            ticker_id=ticker_id,
            symbol="NVDA",
            company_name="NVIDIA",
            sector="Technology",
            created_at=created_at,
        )
        mock_db.query.return_value.order_by.return_value.all.return_value = [asset]

        response = client.get("/api/tracked-assets")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "NVDA"
        assert data[0]["company_name"] == "NVIDIA"


class TestArticles:
    def test_list_articles_requires_symbol(self, client, mock_db):
        response = client.get("/api/articles")
        assert response.status_code == 422

    def test_list_articles_unknown_symbol_returns_404(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/api/articles", params={"symbol": "FAKE"})

        assert response.status_code == 404

    def test_list_articles_with_symbol_filter(self, client, mock_db):
        ticker_id = uuid.uuid4()
        article_id = uuid.uuid4()
        published_at = datetime(2026, 6, 12, tzinfo=timezone.utc)
        article = Articles(
            article_id=article_id,
            title="NVIDIA earnings beat",
            source="Reuters",
            url="https://example.com/nvda",
            published_at=published_at,
            summary="Strong quarter",
        )
        entity = ArticleEntities(
            article_id=article_id,
            ticker_id=ticker_id,
            confidence=0.95,
            sentiment_score=0.8,
            relevance_score=0.9,
        )
        asset = TrackedAssets(ticker_id=ticker_id, symbol="NVDA", created_at=published_at)

        article_query = MagicMock()
        article_query.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (article, entity)
        ]

        def query_side_effect(*models):
            if models and models[0] is TrackedAssets:
                tracked_query = MagicMock()
                tracked_query.filter.return_value.first.return_value = asset
                return tracked_query
            if models and models[0] is Articles:
                return article_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        response = client.get("/api/articles", params={"symbol": "nvda", "limit": 5})

        assert response.status_code == 200
        data = response.json()
        assert data[0]["symbol"] == "NVDA"
        assert data[0]["sentiment_score"] == 0.8
        assert data[0]["relevance_score"] == 0.9


class TestSentiment:
    def test_list_daily_sentiment(self, client, mock_db):
        ticker_id = uuid.uuid4()
        asset = TrackedAssets(
            ticker_id=ticker_id,
            symbol="AAPL",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        row = SentimentDaily(
            ticker_id=ticker_id,
            date=date(2026, 6, 12),
            avg_sentiment=0.25,
            article_count=3,
            momentum=0.1,
            std_div=0.05,
        )
        chain = mock_db.query.return_value.join.return_value
        chain.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            (row, asset)
        ]

        response = client.get("/api/sentiment/daily", params={"symbol": "AAPL", "days": 7})

        assert response.status_code == 200
        data = response.json()
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["avg_sentiment"] == 0.25


class TestAlerts:
    def test_list_alerts(self, client, mock_db):
        ticker_id = uuid.uuid4()
        alert_id = uuid.uuid4()
        created_at = datetime(2026, 6, 12, tzinfo=timezone.utc)
        alert = Alerts(
            alert_id=alert_id,
            ticker_id=ticker_id,
            trigger_reason="Negative sentiment spike",
            sentiment_value=-0.5,
            created_at=created_at,
        )
        asset = TrackedAssets(ticker_id=ticker_id, symbol="TSLA", created_at=created_at)
        mock_db.query.return_value.join.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (alert, asset)
        ]

        response = client.get("/api/alerts", params={"limit": 10})

        assert response.status_code == 200
        data = response.json()
        assert data[0]["symbol"] == "TSLA"
        assert data[0]["trigger_reason"] == "Negative sentiment spike"


class TestPipeline:
    def test_pipeline_status_no_runs(self, client, mock_db):
        mock_db.query.return_value.order_by.return_value.first.return_value = None

        response = client.get("/api/pipeline/status")

        assert response.status_code == 200
        assert response.json()["status"] == "no_runs"

    def test_pipeline_status_latest_run(self, client, mock_db):
        run_id = uuid.uuid4()
        started = datetime(2026, 6, 16, 21, 0, tzinfo=timezone.utc)
        finished = datetime(2026, 6, 16, 21, 5, tzinfo=timezone.utc)
        run = ProcessingRuns(
            run_id=run_id,
            started_at=started,
            finished_at=finished,
            articles_fetched=120,
            num_processed=18,
            status="completed",
        )

        run_query = MagicMock()
        run_query.order_by.return_value.first.return_value = run

        alerts_query = MagicMock()
        alerts_filtered = MagicMock()
        alerts_filtered.filter.return_value.count.return_value = 2
        alerts_query.filter.return_value = alerts_filtered

        def query_side_effect(model):
            if model is ProcessingRuns:
                return run_query
            if model is Alerts:
                return alerts_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        response = client.get("/api/pipeline/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["articles_fetched"] == 120
        assert data["articles_analyzed"] == 18
        assert data["alerts_triggered"] == 2
        assert data["estimated_llm_cost"] == 0.05
