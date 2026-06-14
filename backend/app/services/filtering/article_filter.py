from __future__ import annotations

import re

from app.core.config import settings

# Pirated release titles/tags (AMZN here is a source tag, not Amazon stock).
_SPAM_PATTERN = re.compile(
    r"""
    WEB-DL|WEBRip|BluRay|
    x264|x265|H\.?264|H\.?265|
    720p|1080p|2160p|4K|
    torrent|
    S\d{2}E\d{2}|
    \bAMZN\s+WEB-DL\b|
    \b\d{4}p\s+AMZN\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def build_filter_text(article: dict) -> str:
    parts = [
        article.get("title") or "",
        article.get("description") or "",
    ]
    return "\n".join(p for p in parts if p)


def is_spam_or_release_metadata(text: str) -> bool:
    return bool(_SPAM_PATTERN.search(text))


def is_likely_english(text: str) -> bool:
    """Reject articles that are mostly non-Latin script before LLM."""
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return True
    ascii_letters = sum(1 for char in letters if ord(char) < 128)
    ratio = ascii_letters / len(letters)
    if len(letters) < 12:
        return ratio >= 0.95
    return ratio >= settings.ARTICLE_MIN_ASCII_LETTER_RATIO


def should_skip_before_llm(article: dict) -> bool:
    text = build_filter_text(article)
    if not text.strip():
        return True
    if is_spam_or_release_metadata(text):
        return True
    if settings.NEWS_LANGUAGE and not is_likely_english(text):
        return True
    return False
