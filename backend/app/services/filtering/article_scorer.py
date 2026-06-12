import re
from dataclasses import dataclass
from typing import List, Sequence

from app.models.tracked_assets import TrackedAssets
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
)

_SPAM_PATTERN = re.compile(
    r"WEB-DL|WEBRip|BluRay|x264|x265|720p|1080p|2160p|H\.?264|H\.?265|torrent|S\d{2}E\d{2}",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RankedArticle:
    raw: dict
    matches: List[KeywordMatch]
    priority_score: float


def score_article_for_llm(text: str, matches: Sequence[KeywordMatch]) -> float:
    """
  Score how worthwhile an article is for LLM analysis.

  Higher = more likely real financial news about the matched tickers.
  """
    if not text or not matches:
        return 0.0

    base = max(match.confidence for match in matches)
    text_lower = text.lower()
    financial_hits = sum(1 for term in _FINANCIAL_TERMS if term in text_lower)
    score = base + 0.04 * min(financial_hits, 5)

    if _SPAM_PATTERN.search(text):
        score -= 1.5

    return max(0.0, score)


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
        match_text = build_match_text(raw)
        matches = match_tracked_assets(match_text, assets)
        if not matches:
            skipped_no_keyword += 1
            continue

        ranked.append(
            RankedArticle(
                raw=raw,
                matches=matches,
                priority_score=score_article_for_llm(match_text, matches),
            )
        )

    ranked.sort(
        key=lambda item: (item.priority_score, item.raw.get("publishedAt") or ""),
        reverse=True,
    )
    return ranked, skipped_no_keyword
