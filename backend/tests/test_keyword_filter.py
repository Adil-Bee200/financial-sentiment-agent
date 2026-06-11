from uuid import uuid4

from app.models.tracked_assets import TrackedAssets
from app.services.filtering.keyword_filter import build_search_text, match_tracked_assets


def _asset(symbol: str, company_name: str | None = None) -> TrackedAssets:
    return TrackedAssets(
        ticker_id=uuid4(),
        symbol=symbol,
        company_name=company_name,
    )


class TestKeywordFilter:
    def test_matches_ticker_symbol(self):
        assets = [_asset("NVDA")]
        text = "NVIDIA stock surges as NVDA beats earnings"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "NVDA"
        assert matches[0].confidence >= 0.95

    def test_matches_company_name(self):
        assets = [_asset("AAPL", company_name="Apple Inc")]
        text = "Apple Inc announces new product line"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "AAPL"

    def test_no_match_returns_empty(self):
        assets = [_asset("MSFT")]
        matches = match_tracked_assets("Unrelated weather forecast", assets)
        assert matches == []

    def test_build_search_text_combines_fields(self):
        article = {
            "title": "Title here",
            "description": "Desc here",
            "content": "Body here",
        }
        text = build_search_text(article)
        assert "Title here" in text
        assert "Body here" in text
