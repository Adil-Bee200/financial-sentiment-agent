import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional

from openai import OpenAI, OpenAIError

from app.core.config import settings
from app.schemas.schemas_v1 import RelevanceResult, SentimentResult
from app.services.llm.cost import estimate_llm_cost_usd
from app.services.llm.llm_errors import (
    LLM_API_MAX_RETRIES,
    LLM_PARSE_MAX_ATTEMPTS,
    LlmErrorKind,
    backoff_seconds,
    classify_openai_exception,
    classify_parse_exception,
)
from app.services.pipeline.llm_content import truncate_at_word

logger = logging.getLogger(__name__)

# Hard cap on excerpt length sent to the API (pipeline pre-truncates via LLM_BODY_MAX_CHARS).
MAX_CONTENT_LENGTH = settings.LLM_BODY_MAX_CHARS + 600

_SYSTEM_ANALYZE = (
    "You analyze financial news for equity investors. "
    "The excerpt may be truncated. Respond with JSON only."
)

_ANALYZE_JSON_SCHEMA = (
    'Keys: "summary" (string, max {max_summary} chars, factual, no fluff), '
    '"sentiment_score" (float -1.0 bearish to 1.0 bullish), '
    '"sentiment_label" ("positive"|"negative"|"neutral"), '
    '"confidence" (float 0.0-1.0). '
    "Score likely impact on mentioned companies' stocks, not general tone alone."
)

_SYSTEM_SUMMARIZE = "Financial news summarizer. Plain text only, no markdown."

_SYSTEM_SENTIMENT = "Financial sentiment scorer. JSON only."

_SYSTEM_RELEVANCE = "Financial relevance checker. JSON only."


@dataclass(frozen=True)
class LlmUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass(frozen=True)
class ArticleAnalysis:
    ok: bool
    summary: Optional[str] = None
    sentiment: Optional[SentimentResult] = None
    usage: LlmUsage = field(default_factory=LlmUsage)
    error_kind: Optional[str] = None
    error_message: Optional[str] = None


class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env")
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.OPENAI_MODEL
        self.timeout = 30
        logger.info("LLM Service initialized with model: %s", self.model)

    def analyze_article(
        self,
        article_title: str,
        article_content: str,
        max_summary_length: int = 200,
    ) -> ArticleAnalysis:
        """
        Single LLM call: investor-focused summary + sentiment for one article.
        Used by the cron pipeline (preferred over separate summarize + classify).
        """
        title = article_title.strip()
        content = self._prepare_content(article_content)
        user = self._article_message(title, content)
        system = f"{_SYSTEM_ANALYZE} {_ANALYZE_JSON_SCHEMA.format(max_summary=max_summary_length)}"

        for parse_attempt in range(LLM_PARSE_MAX_ATTEMPTS):
            try:
                response = self._create_completion_with_retries(
                    system, user, temperature=0.2, json_mode=True
                )
                raw = json.loads(response.choices[0].message.content or "{}")
                usage = self._usage_from_response(response)
                summary = self._coerce_summary(raw.get("summary", ""), content, max_summary_length)
                sentiment = self._parse_sentiment(raw)
                return ArticleAnalysis(
                    ok=True,
                    summary=summary,
                    sentiment=sentiment,
                    usage=usage,
                )
            except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
                info = classify_parse_exception(exc)
                if parse_attempt + 1 < LLM_PARSE_MAX_ATTEMPTS:
                    logger.warning(
                        "Parse error in analyze_article (attempt %s/%s): %s",
                        parse_attempt + 1,
                        LLM_PARSE_MAX_ATTEMPTS,
                        exc,
                    )
                    continue
                logger.error("Parse error in analyze_article: %s", exc)
                return self._failed_analysis(info.kind.value, info.message)
            except OpenAIError as exc:
                info = classify_openai_exception(exc)
                logger.error("OpenAI API error in analyze_article (%s): %s", info.kind, exc)
                return self._failed_analysis(info.kind.value, info.message)
            except Exception as exc:
                logger.error("Error in analyze_article: %s", exc)
                return self._failed_analysis(LlmErrorKind.UNKNOWN.value, str(exc))

        return self._failed_analysis(LlmErrorKind.UNKNOWN.value, "analyze_article exhausted retries")

    def summarize_article(
        self,
        article_title: str,
        article_content: str,
        max_length: int = 200,
    ) -> str:
        title = article_title.strip()
        content = self._prepare_content(article_content)
        user = (
            f"{self._article_message(title, content)}\n\n"
            f"Write a summary of at most {max_length} characters. "
            "Focus on financial impact and material facts."
        )
        try:
            text = self._chat_text(_SYSTEM_SUMMARIZE, user, temperature=0.2)
            return self._coerce_summary(text, content, max_length)
        except OpenAIError as e:
            logger.error("OpenAI API error in summarization: %s", e)
            return self._fallback_summary(content, max_length)
        except Exception as e:
            logger.error("Error in summarization: %s", e)
            return self._fallback_summary(content, max_length)

    def classify_sentiment(self, article_title: str, article_content: str) -> SentimentResult:
        title = article_title.strip()
        content = self._prepare_content(article_content)
        user = (
            f"{self._article_message(title, content)}\n\n"
            "Return JSON with sentiment_score (-1..1), sentiment_label, confidence."
        )
        try:
            raw, _usage = self._chat_json(_SYSTEM_SENTIMENT, user, temperature=0.1)
            return self._parse_sentiment(raw)
        except OpenAIError as e:
            logger.error("OpenAI API error in sentiment classification: %s", e)
            return SentimentResult(sentiment_score=0.0, sentiment_label="neutral", confidence=0.0)
        except Exception as e:
            logger.error("Error in sentiment classification: %s", e)
            return SentimentResult(sentiment_score=0.0, sentiment_label="neutral", confidence=0.0)

    def check_relevance(
        self,
        article_title: str,
        article_content: str,
        tracked_tickers: List[str],
    ) -> RelevanceResult:
        if not tracked_tickers:
            return RelevanceResult(relevant=False, companies=[], confidence=0.0)

        title = article_title.strip()
        content = self._prepare_content(article_content)
        tickers = ", ".join(tracked_tickers)
        user = (
            f"Tickers: {tickers}\n\n"
            f"{self._article_message(title, content)}\n\n"
            'JSON: "relevant" (bool), "companies" (tickers from list only), "confidence" (0-1). '
            "relevant=true only if the article clearly concerns at least one ticker."
        )
        try:
            raw, _usage = self._chat_json(_SYSTEM_RELEVANCE, user, temperature=0.1)
            companies = [c for c in raw.get("companies", []) if c in tracked_tickers]
            return RelevanceResult(
                relevant=bool(raw.get("relevant", False)),
                companies=companies,
                confidence=float(raw.get("confidence", 0.0)),
            )
        except OpenAIError as e:
            logger.error("OpenAI API error in relevance check: %s", e)
            return RelevanceResult(relevant=False, companies=[], confidence=0.0)
        except Exception as e:
            logger.error("Error in relevance check: %s", e)
            return RelevanceResult(relevant=False, companies=[], confidence=0.0)

    def _prepare_content(self, article_content: str) -> str:
        content = (article_content or "").strip()
        if len(content) > MAX_CONTENT_LENGTH:
            content = truncate_at_word(content, MAX_CONTENT_LENGTH)
        return content

    @staticmethod
    def _article_message(title: str, content: str) -> str:
        return f"Title: {title}\n\nExcerpt:\n{content}"

    def _chat_json(self, system: str, user: str, temperature: float) -> tuple[dict[str, Any], LlmUsage]:
        response = self._create_completion(system, user, temperature, json_mode=True)
        content = response.choices[0].message.content or "{}"
        return json.loads(content), self._usage_from_response(response)

    def _chat_text(self, system: str, user: str, temperature: float) -> str:
        response = self._create_completion(system, user, temperature, json_mode=False)
        return (response.choices[0].message.content or "").strip()

    def _create_completion_with_retries(
        self,
        system: str,
        user: str,
        temperature: float,
        json_mode: bool,
    ):
        last_exc: OpenAIError | None = None
        for attempt in range(LLM_API_MAX_RETRIES + 1):
            try:
                return self._create_completion(system, user, temperature, json_mode)
            except OpenAIError as exc:
                last_exc = exc
                info = classify_openai_exception(exc)
                if not info.retryable or attempt >= LLM_API_MAX_RETRIES:
                    raise
                delay = backoff_seconds(attempt)
                logger.warning(
                    "OpenAI %s (attempt %s/%s), retrying in %ss: %s",
                    info.kind,
                    attempt + 1,
                    LLM_API_MAX_RETRIES + 1,
                    delay,
                    exc,
                )
                time.sleep(delay)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("_create_completion_with_retries ended without result")

    def _create_completion(
        self,
        system: str,
        user: str,
        temperature: float,
        json_mode: bool,
    ):
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "timeout": self.timeout,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if not self.model.startswith("gpt-5"):
            kwargs["temperature"] = temperature
        return self.client.chat.completions.create(**kwargs)

    @staticmethod
    def _usage_from_response(response) -> LlmUsage:
        usage = getattr(response, "usage", None)
        if usage is None:
            return LlmUsage()
        try:
            prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            total_tokens = int(getattr(usage, "total_tokens", 0) or prompt_tokens + completion_tokens)
        except (TypeError, ValueError):
            return LlmUsage()
        return LlmUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimate_llm_cost_usd(prompt_tokens, completion_tokens),
        )

    @staticmethod
    def _coerce_summary(text: str, fallback_source: str, max_length: int) -> str:
        summary = (text or "").strip()
        if not summary:
            return LLMService._fallback_summary(fallback_source, max_length)
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        return summary

    @staticmethod
    def _fallback_summary(content: str, max_length: int) -> str:
        if len(content) <= max_length:
            return content
        return content[:max_length].rsplit(" ", 1)[0] + "..."

    @staticmethod
    def _failed_analysis(error_kind: str, error_message: str) -> ArticleAnalysis:
        return ArticleAnalysis(
            ok=False,
            error_kind=error_kind,
            error_message=error_message,
        )

    @staticmethod
    def _parse_sentiment(raw: dict[str, Any]) -> SentimentResult:
        score = float(raw.get("sentiment_score", 0.0))
        score = max(-1.0, min(1.0, score))
        label = str(raw.get("sentiment_label", "neutral")).lower()
        if label not in {"positive", "negative", "neutral"}:
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"
        confidence = float(raw.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        return SentimentResult(sentiment_score=score, sentiment_label=label, confidence=confidence)


_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
