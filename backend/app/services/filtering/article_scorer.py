from dataclasses import dataclass
from typing import List, Sequence

from app.core.config import settings
from app.models.tracked_assets import TrackedAssets
from app.services.filtering.article_filter import should_skip_before_llm
from app.services.filtering.keyword_filter import KeywordMatch, build_match_text, match_tracked_assets

# Boost articles that look like market/company news, not incidental mentions.
_FINANCIAL_TERMS: tuple[str, ...] = (
    "earnings",
    "revenue",
    "profit",
    "quarter",
    "quarterly",
    "eps",
    "guidance",
    "forecast",
    "analyst",
    "price target",
    "stock",
    "shares",
    "share price",
    "market cap",
    "dividend",
    "ipo",
    "merger",
    "acquisition",
    "sec filing",
    "10-k",
    "10-q",
    "beat estimates",
    "missed estimates",
    "beats estimates",
    "yoy",
    "year-over-year",
    "trading",
    "nasdaq",
    "nyse",
    "s&p 500",
    "investor",
    "wall street",
    "buy rating",
    "sell rating",
)


@dataclass(frozen=True)
class RankedArticle:
    raw: dict
    matches: List[KeywordMatch]
    priority_score: float


def _financial_term_hits(text: str) -> int:
    text_lower = text.lower()
    return sum(1 for term in _FINANCIAL_TERMS if term in text_lower)


def score_article_for_llm(text: str, matches: Sequence[KeywordMatch]) -> float:
    """
    Score how worthwhile an article is for LLM analysis (0.0–1.0).

    Higher = more likely real financial news about the matched tickers.
    """
    if not text or not matches:
        return 0.0

    base = max(match.confidence for match in matches)
    financial_hits = _financial_term_hits(text)

    # Bare ticker symbol hit (0.95) with no finance vocabulary is usually noise.
    has_named_match = any(match.confidence < 0.95 for match in matches)
    if base <= 0.95 and not has_named_match and financial_hits == 0:
        return 0.0

    bonus = 0.04 * min(financial_hits, 5)
    return min(1.0, base + bonus)


def rank_articles_for_llm(
    articles: Sequence[dict],
    assets: Sequence[TrackedAssets],
) -> tuple[List[RankedArticle], int]:
    """
    Keyword-filter articles, score them, and return highest-priority first.

    Returns (ranked_candidates, skipped_no_keyword_count).
    """
    ranked: List[RankedArticle] = []
    skipped_no_keyword = 0

    for raw in articles:
        if should_skip_before_llm(raw):
            skipped_no_keyword += 1
            continue

        match_text = build_match_text(raw)
        matches = match_tracked_assets(match_text, assets)
        if not matches:
            skipped_no_keyword += 1
            continue

        priority_score = score_article_for_llm(match_text, matches)
        if priority_score < settings.MIN_ARTICLE_PRIORITY_SCORE:
            skipped_no_keyword += 1
            continue

        ranked.append(
            RankedArticle(
                raw=raw,
                matches=matches,
                priority_score=priority_score,
            )
        )

    ranked.sort(
        key=lambda item: (item.priority_score, item.raw.get("publishedAt") or ""),
        reverse=True,
    )
    return ranked, skipped_no_keyword
