from app.core.config import Settings


class TestSettings:
    def test_strips_trailing_newline_from_news_api_key(self, monkeypatch):
        monkeypatch.setenv("NEWS_API_KEY", "abc123\n")
        settings = Settings()
        assert settings.NEWS_API_KEY == "abc123"

    def test_strips_trailing_newline_from_database_url(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db\n")
        settings = Settings()
        assert settings.get_database_url() == "postgresql://user:pass@host/db"
