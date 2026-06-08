from pydantic_settings import BaseSettings
from typing import Optional


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
            return self.DATABASE_URL
        return (
            f"postgresql://{self.database_username}:{self.database_password}"
            f"@{self.database_hostname}:{self.database_port}/{self.database_name}"
        )

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Discord (global webhook; per-user webhooks can be added later)
    DISCORD_WEBHOOK_URL: Optional[str] = None

    # News API
    NEWS_API_KEY: Optional[str] = None
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"

    # Application
    APP_NAME: str = "Financial Research Agent"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Alert thresholds
    NEGATIVE_SENTIMENT_THRESHOLD: float = -0.3
    POSITIVE_SENTIMENT_THRESHOLD: float = 0.3
    VOLUME_SPIKE_MULTIPLIER: float = 2.0
    ROLLING_WINDOW_DAYS: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
