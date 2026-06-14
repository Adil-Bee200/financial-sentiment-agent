from uuid import uuid4

from app.models.tracked_assets import TrackedAssets
from app.services.filtering.article_filter import is_likely_english, is_spam_or_release_metadata, should_skip_before_llm
from app.services.filtering.article_scorer import rank_articles_for_llm, score_article_for_llm
from app.services.filtering.keyword_filter import KeywordMatch, match_tracked_assets


def _asset(symbol: str, company_name: str | None = None) -> TrackedAssets:
    return TrackedAssets(ticker_id=uuid4(), symbol=symbol, company_name=company_name)


def _match(symbol: str, asset: TrackedAssets, confidence: float = 0.95) -> KeywordMatch:
    return KeywordMatch(ticker_id=asset.ticker_id, symbol=symbol, confidence=confidence)


class TestArticleFilter:
    def test_detects_torrent_release_title(self):
        assert is_spam_or_release_metadata("Raakh S01 1080p AMZN WEB-DL H264-N1H4L")

    def test_rejects_non_english_text(self):
        assert not is_likely_english("台股狂飆千點！聯發科暴漲95元、日月光續強飆逾8%")

    def test_accepts_english_financial_text(self):
        assert is_likely_english("NVIDIA beats Q2 earnings, NVDA stock jumps on revenue guidance")

    def test_should_skip_torrent_and_foreign(self):
        assert should_skip_before_llm(
            {"title": "King Of Dope 2026 1080p AMZN WEB-DL H264-MADSKY", "description": ""}
        )
        assert should_skip_before_llm(
            {"title": "台股狂飆千點", "description": "聯發科暴漲"}
        )


class TestArticleScorer:
    def test_financial_terms_raise_priority(self):
        nvda = _asset("NVDA")
        matches = [_match("NVDA", nvda)]
        plain = score_article_for_llm("NVDA mentioned in passing", matches)
        financial = score_article_for_llm(
            "NVDA beats earnings estimates as revenue jumps, shares rally",
            matches,
        )
        assert plain == 0.0
        assert 0.0 < financial <= 1.0

    def test_priority_score_never_exceeds_one(self):
        nvda = _asset("NVDA")
        matches = [_match("NVDA", nvda, confidence=1.0)]
        text = " ".join(
            [
                "NVDA earnings revenue profit quarter eps guidance forecast analyst",
                "stock shares dividend trading nasdaq nyse",
            ]
        )
        assert score_article_for_llm(text, matches) == 1.0

    def test_bare_ticker_without_finance_terms_scores_zero(self):
        bac = _asset("BAC", company_name="Bank of America Corp")
        matches = match_tracked_assets("Random mention of BAC in unrelated text", [bac])
        assert matches == []

    def test_rank_excludes_torrent_and_french_bac(self):
        amzn = _asset("AMZN", company_name="Amazon.com Inc")
        bac = _asset("BAC", company_name="Bank of America Corp")
        nvda = _asset("NVDA", company_name="NVIDIA Corporation")
        assets = [amzn, bac, nvda]
        articles = [
            {
                "title": "The Valley 2024 S03E11 720p AMZN WEB-DL H264",
                "description": "Release group tag AMZN",
                "publishedAt": "2026-06-11T20:00:00Z",
            },
            {
                "title": "Bac 2026 : les sujets de maths",
                "description": "Épreuve anticipée pour les élèves",
                "publishedAt": "2026-06-11T19:00:00Z",
            },
            {
                "title": "Nvidia beats Q2 earnings, stock jumps",
                "description": "NVDA revenue and guidance topped analyst forecasts",
                "publishedAt": "2026-06-11T18:00:00Z",
            },
        ]

        ranked, skipped = rank_articles_for_llm(articles, assets)

        assert len(ranked) == 1
        assert skipped == 2
        assert "earnings" in ranked[0].raw["title"].lower()
        assert ranked[0].priority_score <= 1.0

    def test_jpmorgan_alias_article_can_rank_without_extra_finance_terms(self):
        jpm = _asset("JPM", company_name="JPMorgan Chase & Co")
        article = {
            "title": "Should You Buy JPMorgan Chase & Co. (JPM)?",
            "description": "Analyst views on the bank",
            "publishedAt": "2026-06-11T18:00:00Z",
        }
        ranked, skipped = rank_articles_for_llm([article], [jpm])
        assert skipped == 0
        assert len(ranked) == 1
        assert ranked[0].matches[0].symbol == "JPM"

    def test_rank_skips_non_matches(self):
        ranked, skipped = rank_articles_for_llm(
            [{"title": "Weather today", "description": "Sunny"}],
            [_asset("MSFT")],
        )
        assert ranked == []
        assert skipped == 1
