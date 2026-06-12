import re
from dataclasses import dataclass
from typing import List, Sequence
from uuid import UUID

from app.core.config import settings
from app.models.tracked_assets import TrackedAssets

# Distinctive press names only — avoid generic words (Apple, Amazon, Meta, Tesla).
_SYMBOL_ALIASES: dict[str, tuple[str, ...]] = {
    "GOOGL": ("Google", "Alphabet"),
    "META": ("Facebook", "Meta Platforms"),
    "NVDA": ("Nvidia",),
    "MSFT": ("Microsoft",),
    "JPM": ("JPMorgan",),
    "BAC": ("Bank of America",),
    "GS": ("Goldman Sachs",),
}

_LEGAL_SUFFIXES = (
    "Corporation",
    "Incorporated",
    "Inc.",
    "Inc",
    "Corp.",
    "Corp",
    "Co.",
    "Co",
    "Ltd.",
    "Ltd",
    "LLC",
    "PLC",
    "Group",
    "Holdings",
)


@dataclass(frozen=True)
class KeywordMatch:
    ticker_id: UUID
    symbol: str
    confidence: float


def _strip_legal_suffix(name: str) -> str:
    result = re.sub(r"\.com\b", "", name, flags=re.IGNORECASE).strip()
    changed = True
    while changed:
        changed = False
        for suffix in _LEGAL_SUFFIXES:
            for sep in (" & ", " "):
                tail = f"{sep}{suffix}"
                if result.lower().endswith(tail.lower()):
                    result = result[: -len(tail)].strip()
                    changed = True
                    break
    return result


def _company_name_patterns(company_name: str) -> List[str]:
    """Multi-word or long stripped names only — skip short/generic tokens."""
    names: List[str] = []
    raw = company_name.strip()
    stripped = _strip_legal_suffix(raw)
    for candidate in (raw, stripped):
        if len(candidate) < 5:
            continue
        if " " in candidate and candidate not in names:
            names.append(candidate)
        elif len(candidate) >= 8 and candidate not in names:
            names.append(candidate)
    return names


def _compile_patterns(asset: TrackedAssets) -> List[tuple[re.Pattern[str], float]]:
    patterns: List[tuple[re.Pattern[str], float]] = []
    symbol = asset.symbol.upper()
    patterns.append((re.compile(rf"\${re.escape(symbol)}\b", re.IGNORECASE), 1.0))

    # Short tickers (e.g. GS) are prone to false positives as bare words.
    if len(symbol) >= 3:
        patterns.append((re.compile(rf"\b{re.escape(symbol)}\b", re.IGNORECASE), 0.95))

    for alias in _SYMBOL_ALIASES.get(symbol, ()):
        if len(alias) >= 5 or " " in alias:
            patterns.append((re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE), 0.92))

    if asset.company_name:
        for name in _company_name_patterns(asset.company_name):
            patterns.append((re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE), 0.90))

    return patterns


def match_tracked_assets(
    text: str,
    assets: Sequence[TrackedAssets],
    *,
    min_confidence: float | None = None,
) -> List[KeywordMatch]:
    """
    Cheap relevance gate: match ticker symbols and company names in text.
    Returns one entry per asset with the highest confidence match above the threshold.
    """
    if not text or not assets:
        return []

    threshold = settings.KEYWORD_MIN_CONFIDENCE if min_confidence is None else min_confidence
    matches: List[KeywordMatch] = []
    for asset in assets:
        best = 0.0
        for pattern, score in _compile_patterns(asset):
            if pattern.search(text):
                best = max(best, score)
        if best >= threshold:
            matches.append(KeywordMatch(ticker_id=asset.ticker_id, symbol=asset.symbol, confidence=best))

    return matches


def build_match_text(article: dict) -> str:
    """Title + description only — avoids noisy/truncated body text."""
    parts = [
        article.get("title") or "",
        article.get("description") or "",
    ]
    return "\n".join(p for p in parts if p)


def build_search_text(article: dict) -> str:
    """Combine NewsAPI fields for keyword scanning (includes body)."""
    parts = [
        article.get("title") or "",
        article.get("description") or "",
        article.get("content") or "",
    ]
    return "\n".join(p for p in parts if p)
