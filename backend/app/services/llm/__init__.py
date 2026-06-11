"""
LLM Service Module

Provides AI-powered article processing:
- Relevance gate
- Summarization
- Sentiment classification
"""

from app.services.llm.ai_service import (
    ArticleAnalysis,
    LLMService,
    get_llm_service,
)
from app.schemas.schemas_v1 import RelevanceResult, SentimentResult

__all__ = [
    "ArticleAnalysis",
    "LLMService",
    "RelevanceResult",
    "SentimentResult",
    "get_llm_service",
]
