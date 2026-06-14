from uuid import uuid4

from app.models.tracked_assets import TrackedAssets
from app.services.filtering.keyword_filter import (
    build_match_text,
    build_search_text,
    match_tracked_assets,
)


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
        text = "AAPL announces new product line after earnings beat"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "AAPL"

    def test_matches_press_name_without_ticker(self):
        assets = [_asset("NVDA", company_name="NVIDIA Corporation")]
        text = "Nvidia unveils new AI chip for data centers"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "NVDA"

    def test_matches_common_alias(self):
        assets = [_asset("GOOGL", company_name="Alphabet Inc")]
        text = "Google parent reports cloud revenue growth"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "GOOGL"

    def test_rejects_generic_apple_without_ticker(self):
        assets = [_asset("AAPL", company_name="Apple Inc")]
        text = "Apple harvest forecast improves in Washington state"
        matches = match_tracked_assets(text, assets)
        assert matches == []

    def test_rejects_short_ticker_bare_word(self):
        assets = [_asset("GS", company_name="Goldman Sachs Group Inc")]
        text = "Fed signals GS tightening ahead of jobs report"
        matches = match_tracked_assets(text, assets)
        assert matches == []

    def test_matches_short_ticker_as_dollar_symbol(self):
        assets = [_asset("GS", company_name="Goldman Sachs Group Inc")]
        text = "Analysts lift price target on $GS after earnings"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "GS"

    def test_min_confidence_blocks_weak_name_only(self):
        assets = [_asset("META", company_name="Meta Platforms Inc")]
        text = "Developers discuss meta tags in HTML templates"
        matches = match_tracked_assets(text, assets, min_confidence=0.95)
        assert matches == []

    def test_matches_meta_ticker_uppercase_only(self):
        assets = [_asset("META", company_name="Meta Platforms Inc")]
        text = "META shares rise after strong ad revenue"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "META"

    def test_rejects_french_bac_exam_false_positive(self):
        assets = [_asset("BAC", company_name="Bank of America Corp")]
        text = "Bac 2026 : Découvrez les sujets de la première épreuve anticipée de maths"
        matches = match_tracked_assets(text, assets)
        assert matches == []

    def test_matches_bac_via_company_alias(self):
        assets = [_asset("BAC", company_name="Bank of America Corp")]
        text = "Bank of America Corp reports quarterly earnings beat"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "BAC"

    def test_rejects_bare_amzn_release_tag(self):
        assets = [_asset("AMZN", company_name="Amazon.com Inc")]
        text = "Sleepless City 2025 720p AMZN WEB-DL H264-MADSKY"
        matches = match_tracked_assets(text, assets)
        assert matches == []

    def test_matches_amazon_via_alias(self):
        assets = [_asset("AMZN", company_name="Amazon.com Inc")]
        text = "Amazon stock rises after AWS revenue beats estimates"
        matches = match_tracked_assets(text, assets)
        assert len(matches) == 1
        assert matches[0].symbol == "AMZN"

    def test_no_match_returns_empty(self):
        assets = [_asset("MSFT")]
        matches = match_tracked_assets("Unrelated weather forecast", assets)
        assert matches == []

    def test_build_match_text_omits_body(self):
        article = {
            "title": "Title here",
            "description": "Desc here",
            "content": "NVDA secret body mention",
        }
        text = build_match_text(article)
        assert "Title here" in text
        assert "Desc here" in text
        assert "NVDA secret body mention" not in text

    def test_build_search_text_combines_fields(self):
        article = {
            "title": "Title here",
            "description": "Desc here",
            "content": "Body here",
        }
        text = build_search_text(article)
        assert "Title here" in text
        assert "Body here" in text
