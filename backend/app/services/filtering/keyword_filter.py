import re
from dataclasses import dataclass
from typing import List, Sequence
from uuid import UUID

from app.models.tracked_assets import TrackedAssets

_SYMBOL_ALIASES: dict[str, tuple[str, ...]] = {
    "GOOGL": ("Google", "Alphabet"),
    "META": ("Facebook",),
    "AMZN": ("Amazon",),
    "TSLA": ("Tesla",),
    "NVDA": ("Nvidia",),
    "AAPL": ("Apple",),
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


def _search_names(asset: TrackedAssets) -> List[str]:
    names: List[str] = []
    symbol = asset.symbol.upper()

    for alias in _SYMBOL_ALIASES.get(symbol, ()):
        if len(alias) >= 3 and alias not in names:
            names.append(alias)

    if asset.company_name:
        raw = asset.company_name.strip()
        for candidate in (raw, _strip_legal_suffix(raw)):
            if len(candidate) >= 3 and candidate not in names:
                names.append(candidate)
            first = re.split(r"[\s&]+", candidate)[0]
            if len(first) >= 3 and first not in names:
                names.append(first)

    return names


def _compile_patterns(asset: TrackedAssets) -> List[tuple[re.Pattern[str], float]]:
    patterns: List[tuple[re.Pattern[str], float]] = []
    symbol = asset.symbol.upper()
    patterns.append((re.compile(rf"\${re.escape(symbol)}\b", re.IGNORECASE), 1.0))
    patterns.append((re.compile(rf"\b{re.escape(symbol)}\b", re.IGNORECASE), 0.95))

    for name in _search_names(asset):
        escaped = re.escape(name)
        patterns.append((re.compile(rf"\b{escaped}\b", re.IGNORECASE), 0.85))

    return patterns


def match_tracked_assets(text: str, assets: Sequence[TrackedAssets]) -> List[KeywordMatch]:
    """
    Cheap relevance gate: match ticker symbols and company/press names in text.
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
