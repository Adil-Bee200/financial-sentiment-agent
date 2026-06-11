import re
from dataclasses import dataclass
from typing import List, Sequence
from uuid import UUID

from app.models.tracked_assets import TrackedAssets


@dataclass(frozen=True)
class KeywordMatch:
    ticker_id: UUID
    symbol: str
    confidence: float


def _compile_patterns(asset: TrackedAssets) -> List[tuple[re.Pattern[str], float]]:
    patterns: List[tuple[re.Pattern[str], float]] = []
    symbol = asset.symbol.upper()
    patterns.append((re.compile(rf"\${re.escape(symbol)}\b", re.IGNORECASE), 1.0))
    patterns.append((re.compile(rf"\b{re.escape(symbol)}\b", re.IGNORECASE), 0.95))

    if asset.company_name and len(asset.company_name.strip()) >= 4:
        name = re.escape(asset.company_name.strip())
        patterns.append((re.compile(rf"\b{name}\b", re.IGNORECASE), 0.85))

    return patterns


def match_tracked_assets(text: str, assets: Sequence[TrackedAssets]) -> List[KeywordMatch]:
    """
    Cheap relevance gate: match ticker symbols and optional company names in text.
    Returns one entry per asset with the highest confidence match.
    """
    if not text or not assets:
        return []

    matches: List[KeywordMatch] = []
    for asset in assets:
        best = 0.0
        for pattern, score in _compile_patterns(asset):
            if pattern.search(text):
                best = max(best, score)
        if best > 0:
            matches.append(KeywordMatch(ticker_id=asset.ticker_id, symbol=asset.symbol, confidence=best))

    return matches


def build_search_text(article: dict) -> str:
    """Combine NewsAPI fields for keyword scanning."""
    parts = [
        article.get("title") or "",
        article.get("description") or "",
        article.get("content") or "",
    ]
    return "\n".join(p for p in parts if p)
