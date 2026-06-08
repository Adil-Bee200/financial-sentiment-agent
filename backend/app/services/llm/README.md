# LLM Service

The LLM Service provides AI-powered processing for financial articles using OpenAI's API.

## Features

1. **Relevance Gate** - Determines if an article is relevant to tracked portfolio tickers
2. **Summarization** - Creates concise summaries of articles
3. **Sentiment Classification** - Analyzes sentiment and returns a score (-1.0 to 1.0)

## Usage

### Basic Setup

```python
from app.services.llm import get_llm_service

# Get the service instance (singleton)
llm_service = get_llm_service()
```

### 1. Check Relevance

```python
from app.services.llm import get_llm_service, RelevanceResult

llm_service = get_llm_service()

# Check if article is relevant to tracked tickers
result: RelevanceResult = llm_service.check_relevance(
    article_title="NVIDIA Reports Record Earnings",
    article_content="NVIDIA announced record quarterly earnings...",
    tracked_tickers=["NVDA", "AAPL", "MSFT"]
)

print(f"Relevant: {result.relevant}")
print(f"Companies mentioned: {result.companies}")  # ["NVDA"]
print(f"Confidence: {result.confidence}")  # 0.91
```

### 2. Summarize Article

```python
summary = llm_service.summarize_article(
    article_title="Tech Stocks Rally",
    article_content="Full article content here...",
    max_length=200  # Optional, default 200
)

print(summary)
```

### 3. Classify Sentiment

```python
from app.services.llm import get_llm_service, SentimentResult

llm_service = get_llm_service()

result: SentimentResult = llm_service.classify_sentiment(
    article_title="Company Misses Earnings",
    article_content="Company reported lower than expected earnings..."
)

print(f"Sentiment Score: {result.sentiment_score}")  # -0.65 (negative)
print(f"Label: {result.sentiment_label}")  # "negative"
print(f"Confidence: {result.confidence}")  # 0.85
```

## Configuration

Set in `.env`:
```env
OPENAI_API_KEY=your_api_key_here
```

The service uses `gpt-4o-mini` by default (cost-effective model).

## Error Handling

The service includes error handling:
- API errors return safe defaults (neutral sentiment, assume relevant)
- Content is truncated if too long to save tokens
- Timeout set to 30 seconds

## Integration with Article Processing

This service is typically used in the Celery worker pipeline:

1. **Fetcher** → Gets articles from news APIs
2. **Relevance Gate** → Filters articles (this service)
3. **Summarization** → Creates summaries (this service)
4. **Sentiment** → Classifies sentiment (this service)
5. **Storage** → Saves to database
