import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.alert import Alerts
from app.models.article import Articles
from app.models.processing_runs import ProcessingRuns
from app.models.tracked_assets import TrackedAssets
from app.services.stats.project_stats_service import ProjectStatsService


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


class TestProjectStatsService:
    def test_run_duration_seconds(self):
        started = datetime(2026, 6, 17, 22, 30, tzinfo=timezone.utc)
        finished = datetime(2026, 6, 17, 22, 34, tzinfo=timezone.utc)
        run = ProcessingRuns(started_at=started, finished_at=finished, status="completed")
        assert ProjectStatsService.run_duration_seconds(run) == 240.0


class TestStatsApi:
    def test_get_project_stats(self, client, mock_db):
        tracked_count = MagicMock()
        tracked_count.scalar.return_value = 10

        completed_count = MagicMock()
        completed_count.filter.return_value.scalar.return_value = 5

        articles_count = MagicMock()
        articles_count.scalar.return_value = 97

        mentions_count = MagicMock()
        mentions_count.select_from.return_value.scalar.return_value = 120

        alerts_count = MagicMock()
        alerts_count.scalar.return_value = 8

        totals = MagicMock()
        totals.filter.return_value.one.return_value = (56, 0.25)

        started = datetime(2026, 6, 17, 22, 30, tzinfo=timezone.utc)
        finished = datetime(2026, 6, 17, 22, 34, tzinfo=timezone.utc)
        run = ProcessingRuns(
            run_id=uuid.uuid4(),
            started_at=started,
            finished_at=finished,
            articles_fetched=286,
            articles_keyword_matched=72,
            num_processed=39,
            articles_skipped_llm_limit=33,
            alerts_created=6,
            estimated_llm_cost_usd=0.05,
            status="completed",
        )

        recent_query = MagicMock()
        recent_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            run
        ]

        def query_side_effect(model):
            if model is TrackedAssets:
                return tracked_count
            if model is ProcessingRuns:
                if mock_db.query.call_count <= 2:
                    return completed_count if mock_db.query.call_count == 2 else recent_query
                return totals if mock_db.query.call_count == 3 else recent_query
            if model is Articles:
                return articles_count
            if model is Alerts:
                return alerts_count
            return MagicMock()

        # Simpler: patch ProjectStatsService.get_stats
        from unittest.mock import patch
        from app.services.stats.project_stats_service import ProjectStats

        stats = ProjectStats(
            tracked_tickers=10,
            completed_pipeline_runs=5,
            total_articles_stored=97,
            total_ticker_mentions=120,
            total_alerts=8,
            total_articles_analyzed=56,
            total_estimated_llm_cost_usd=0.25,
            recent_runs_sample_size=1,
            avg_articles_fetched=286.0,
            avg_articles_keyword_matched=72.0,
            avg_articles_analyzed=39.0,
            avg_run_duration_seconds=240.0,
            avg_estimated_llm_cost_usd=0.05,
            llm_selectivity_pct=54.2,
            keyword_filter_pass_rate_pct=25.2,
        )

        with patch.object(ProjectStatsService, "get_stats", return_value=stats):
            response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["tracked_tickers"] == 10
        assert data["avg_articles_fetched"] == 286.0
        assert data["avg_articles_analyzed"] == 39.0
        assert data["estimated_monthly_llm_cost_usd"] == 1.5
