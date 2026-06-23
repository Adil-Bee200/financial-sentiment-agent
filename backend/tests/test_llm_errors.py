"""Tests for OpenAI error classification and retry helpers."""

from unittest.mock import Mock

import pytest
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

from app.services.llm.llm_errors import (
    LlmErrorKind,
    backoff_seconds,
    classify_openai_exception,
    classify_parse_exception,
)


def _status_error(error_cls, status_code: int, message: str = "error"):
    response = Mock()
    response.status_code = status_code
    response.headers = {}
    return error_cls(message, response=response, body=None)


class TestClassifyOpenAIException:
    def test_authentication_error(self):
        info = classify_openai_exception(_status_error(AuthenticationError, 401, "invalid key"))
        assert info.kind == LlmErrorKind.AUTH
        assert info.retryable is False

    def test_permission_denied(self):
        info = classify_openai_exception(_status_error(PermissionDeniedError, 403, "forbidden"))
        assert info.kind == LlmErrorKind.AUTH
        assert info.retryable is False

    def test_rate_limit(self):
        info = classify_openai_exception(_status_error(RateLimitError, 429, "rate limited"))
        assert info.kind == LlmErrorKind.RATE_LIMIT
        assert info.retryable is True

    def test_internal_server_error(self):
        info = classify_openai_exception(_status_error(InternalServerError, 500, "server down"))
        assert info.kind == LlmErrorKind.SERVER
        assert info.retryable is True

    def test_api_status_503(self):
        info = classify_openai_exception(_status_error(APIStatusError, 503, "unavailable"))
        assert info.kind == LlmErrorKind.SERVER
        assert info.retryable is True

    def test_timeout(self):
        request = Mock()
        info = classify_openai_exception(APITimeoutError(request=request))
        assert info.kind == LlmErrorKind.TIMEOUT
        assert info.retryable is True

    def test_connection_error(self):
        request = Mock()
        info = classify_openai_exception(APIConnectionError(request=request))
        assert info.kind == LlmErrorKind.TIMEOUT
        assert info.retryable is True

    def test_generic_openai_error(self):
        info = classify_openai_exception(OpenAIError("generic"))
        assert info.kind == LlmErrorKind.UNKNOWN
        assert info.retryable is False

    def test_bad_request_not_retried(self):
        info = classify_openai_exception(_status_error(APIStatusError, 400, "bad request"))
        assert info.kind == LlmErrorKind.UNKNOWN
        assert info.retryable is False


class TestClassifyParseException:
    def test_json_decode_error(self):
        import json

        info = classify_parse_exception(json.JSONDecodeError("msg", "doc", 0))
        assert info.kind == LlmErrorKind.PARSE
        assert info.retryable is True


class TestBackoff:
    def test_exponential_delays(self):
        assert backoff_seconds(0) == 2.0
        assert backoff_seconds(1) == 4.0
        assert backoff_seconds(2) == 8.0
