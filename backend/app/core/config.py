from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve backend/.env from this file (app/core/config.py), not the process cwd.
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # Database - can use DATABASE_URL directly or construct from components
    DATABASE_URL: Optional[str] = None
    database_hostname: str = "localhost"
    database_port: str = "5432"
    database_password: str = "postgres"
    database_name: str = "financial_agent"
    database_username: str = "postgres"

    def get_database_url(self) -> str:
        """Get database URL, either from DATABASE_URL or construct from components"""
        if self.DATABASE_URL:
            return self.DATABASE_URL.strip()
        return (
            f"postgresql://{self.database_username}:{self.database_password}"
            f"@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

    @field_validator(
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "NEWS_API_KEY",
        "DISCORD_WEBHOOK_URL",
        "NEWS_API_BASE_URL",
        mode="before",
    )
    @classmethod
    def strip_secret_strings(cls, value: object) -> object:
        """GitHub/env secrets are often pasted with trailing newlines."""
        if isinstance(value, str):
            return value.strip()
        return value

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini"

    # Discord (global webhook; per-user webhooks can be added later)
    DISCORD_WEBHOOK_URL: Optional[str] = None

    # News API
    NEWS_API_KEY: Optional[str] = None
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"
    NEWS_QUERY: str = "financial OR stocks OR earnings"
    HOURS_BACK: int = 48
    NEWS_MAX_PAGES: int = 5
    # ISO-639-1 language sent to NewsAPI (empty string disables the param).
    NEWS_LANGUAGE: str = "en"
    # Extra NewsAPI call per tracked symbol (up to ~100 articles each on free tier).
    NEWS_SUPPLEMENT_TICKER_FETCH: bool = True

    # Keyword filter (title + description only in pipeline)
    KEYWORD_MIN_CONFIDENCE: float = 0.90
    # Minimum keyword priority score (0–1) before an article may use LLM budget.
    MIN_ARTICLE_PRIORITY_SCORE: float = 0.90
    # Min share of Latin letters when NEWS_LANGUAGE is set (post-fetch safety net).
    ARTICLE_MIN_ASCII_LETTER_RATIO: float = 0.85

    # LLM cost controls
    LLM_BODY_MAX_CHARS: int = 1000
    MAX_LLM_ARTICLES_PER_DAY: int = 40
    # Cap each pipeline run so the daily budget spreads across cron runs (0 = daily cap only).
    MAX_LLM_ARTICLES_PER_RUN: int = 10

    # Application
    APP_NAME: str = "Financial Research Agent"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Alert thresholds
    NEGATIVE_SENTIMENT_THRESHOLD: float = -0.3
    POSITIVE_SENTIMENT_THRESHOLD: float = 0.3
    VOLUME_SPIKE_MULTIPLIER: float = 2.0
    ROLLING_WINDOW_DAYS: int = 7
    ALERT_COOLDOWN_HOURS: int = 24

    # Business calendar timezone (US Eastern — handles EST/EDT automatically)
    APP_TIMEZONE: str = "America/New_York"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
