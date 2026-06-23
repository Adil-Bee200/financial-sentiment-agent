from dataclasses import dataclass
from enum import StrEnum

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

# Retries after the first failed API call (backoff: 2s, 4s, 8s).
LLM_API_MAX_RETRIES = 3
LLM_API_BACKOFF_BASE_SECONDS = 2.0
# Initial attempt plus one retry on malformed JSON / parse errors.
LLM_PARSE_MAX_ATTEMPTS = 2


class LlmErrorKind(StrEnum):
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    SERVER = "server"
    PARSE = "parse"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LlmErrorInfo:
    kind: LlmErrorKind
    message: str
    retryable: bool


def backoff_seconds(attempt: int) -> float:
    """Seconds to wait before retry attempt index 0, 1, 2 → 2s, 4s, 8s."""
    return LLM_API_BACKOFF_BASE_SECONDS * (2**attempt)


def classify_openai_exception(exc: Exception) -> LlmErrorInfo:
    if isinstance(exc, (AuthenticationError, PermissionDeniedError)):
        return LlmErrorInfo(LlmErrorKind.AUTH, str(exc), retryable=False)
    if isinstance(exc, RateLimitError):
        return LlmErrorInfo(LlmErrorKind.RATE_LIMIT, str(exc), retryable=True)
    if isinstance(exc, APITimeoutError):
        return LlmErrorInfo(LlmErrorKind.TIMEOUT, str(exc), retryable=True)
    if isinstance(exc, APIConnectionError):
        return LlmErrorInfo(LlmErrorKind.TIMEOUT, str(exc), retryable=True)
    if isinstance(exc, InternalServerError):
        return LlmErrorInfo(LlmErrorKind.SERVER, str(exc), retryable=True)
    if isinstance(exc, APIStatusError):
        code = getattr(exc, "status_code", None)
        if code in (401, 403):
            return LlmErrorInfo(LlmErrorKind.AUTH, str(exc), retryable=False)
        if code == 429:
            return LlmErrorInfo(LlmErrorKind.RATE_LIMIT, str(exc), retryable=True)
        if code is not None and code >= 500:
            return LlmErrorInfo(LlmErrorKind.SERVER, str(exc), retryable=True)
    if isinstance(exc, OpenAIError):
        return LlmErrorInfo(LlmErrorKind.UNKNOWN, str(exc), retryable=False)
    return LlmErrorInfo(LlmErrorKind.UNKNOWN, str(exc), retryable=False)


def classify_parse_exception(exc: Exception) -> LlmErrorInfo:
    return LlmErrorInfo(LlmErrorKind.PARSE, str(exc), retryable=True)
