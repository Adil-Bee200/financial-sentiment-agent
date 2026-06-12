from uuid import uuid4

from app.models.tracked_assets import TrackedAssets
from app.services.filtering.article_scorer import rank_articles_for_llm, score_article_for_llm
from app.services.filtering.keyword_filter import KeywordMatch, match_tracked_assets


def _asset(symbol: str) -> TrackedAssets:
    return TrackedAssets(ticker_id=uuid4(), symbol=symbol)


def _match(symbol: str, asset: TrackedAssets, confidence: float = 0.95) -> KeywordMatch:
    return KeywordMatch(ticker_id=asset.ticker_id, symbol=symbol, confidence=confidence)


class TestArticleScorer:
    def test_financial_terms_raise_priority(self):
        nvda = _asset("NVDA")
        matches = [_match("NVDA", nvda)]
        plain = score_article_for_llm("NVDA mentioned in passing", matches)
        financial = score_article_for_llm(
            "NVDA beats earnings estimates as revenue jumps, shares rally",
            matches,
        )
        assert financial > plain

    def test_spam_pattern_lowers_priority(self):
        amzn = _asset("AMZN")
        matches = [_match("AMZN", amzn)]
        torrent = score_article_for_llm("The Valley 2024 S03E11 720p AMZN WEB-DL H264", matches)
        news = score_article_for_llm("Amazon AMZN stock rises after earnings beat", matches)
        assert torrent < news
        assert torrent == 0.0

    def test_rank_puts_earnings_article_first(self):
        nvda = _asset("NVDA")
        amzn = _asset("AMZN")
        assets = [nvda, amzn]
        articles = [
            {
                "title": "The Valley 2024 S03E11 720p AMZN WEB-DL H264",
                "description": "Release group tag AMZN",
                "publishedAt": "2026-06-11T20:00:00Z",
            },
            {
                "title": "Nvidia beats Q2 earnings, stock jumps",
                "description": "NVDA revenue and guidance topped analyst forecasts",
                "publishedAt": "2026-06-11T18:00:00Z",
            },
        ]

        ranked, skipped = rank_articles_for_llm(articles, assets)

        assert skipped == 0
        assert len(ranked) == 2
        assert "earnings" in ranked[0].raw["title"].lower()
        assert ranked[0].priority_score > ranked[1].priority_score

    def test_rank_skips_non_matches(self):
        ranked, skipped = rank_articles_for_llm(
            [{"title": "Weather today", "description": "Sunny"}],
            [_asset("MSFT")],
        )
        assert ranked == []
        assert skipped == 1
