from unittest.mock import Mock, patch

from app.services.ingestion.article_ingestion_service import ArticleIngestionService


def _article(url: str) -> dict:
    return {
        "title": f"Title for {url}",
        "url": url,
        "publishedAt": "2026-06-07T10:00:00Z",
        "source": {"name": "Reuters"},
        "description": "Sample article",
    }


def _response(articles: list[dict]) -> Mock:
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"status": "ok", "articles": articles}
    return response


class TestArticleIngestionFetch:
    def test_sends_api_key_in_header_not_query(self):
        service = ArticleIngestionService(news_api_key="secret-test-key")
        page_one = [_article("https://example.com/one")]

        with patch("app.services.ingestion.article_ingestion_service.requests.get") as mock_get:
            mock_get.return_value = _response(page_one)
            service.fetch_articles(query="financial", max_pages=1)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["headers"] == {"X-Api-Key": "secret-test-key"}
        assert "apiKey" not in call_kwargs["params"]

    def test_stops_after_partial_last_page(self):
        service = ArticleIngestionService(news_api_key="test-key")
        page_one = [_article(f"https://example.com/{index}") for index in range(98)]

        with patch("app.services.ingestion.article_ingestion_service.requests.get") as mock_get:
            mock_get.return_value = _response(page_one)
            articles = service.fetch_articles(query="financial", max_pages=3)

        assert len(articles) == 98
        assert mock_get.call_count == 1

    def test_paginates_until_last_page(self):
        service = ArticleIngestionService(news_api_key="test-key")
        page_one = [_article(f"https://example.com/p1/{index}") for index in range(100)]
        page_two = [_article(f"https://example.com/p2/{index}") for index in range(40)]

        with patch("app.services.ingestion.article_ingestion_service.requests.get") as mock_get:
            mock_get.side_effect = [_response(page_one), _response(page_two)]
            articles = service.fetch_articles(query="financial", max_pages=3)

        assert len(articles) == 140
        assert mock_get.call_count == 2

    def test_dedupes_urls_across_pages(self):
        service = ArticleIngestionService(news_api_key="test-key")
        shared = _article("https://example.com/shared")
        page_one = [_article(f"https://example.com/p1/{index}") for index in range(100)] + [shared]
        page_two = [shared, _article("https://example.com/p2/only")]

        with patch("app.services.ingestion.article_ingestion_service.requests.get") as mock_get:
            mock_get.side_effect = [_response(page_one), _response(page_two)]
            articles = service.fetch_articles(query="financial", max_pages=3)

        urls = [article["url"] for article in articles]
        assert len(urls) == len(set(urls))
        assert urls.count("https://example.com/shared") == 1

    def test_fetch_for_pipeline_merges_broad_and_ticker_queries(self):
        service = ArticleIngestionService(news_api_key="test-key")
        broad = [_article("https://example.com/broad")]
        nvda = [_article("https://example.com/nvda")]
        aapl = [_article("https://example.com/aapl")]

        with patch.object(service, "fetch_articles", side_effect=[broad, nvda, aapl]) as mock_fetch:
            articles = service.fetch_for_pipeline(
                query="financial",
                from_date="2026-06-10T00:00:00",
                to_date="2026-06-11T00:00:00",
                max_pages=3,
                supplement_symbols=["NVDA", "AAPL"],
            )

        assert len(articles) == 3
        assert mock_fetch.call_count == 3
        assert mock_fetch.call_args_list[0].kwargs["query"] == "financial"
        assert mock_fetch.call_args_list[1].kwargs["query"] == "NVDA"
        assert mock_fetch.call_args_list[2].kwargs["max_pages"] == 1

    def test_handles_maximum_results_reached(self):
        service = ArticleIngestionService(news_api_key="test-key")
        page_one = [_article(f"https://example.com/{index}") for index in range(100)]
        cap_response = Mock()
        cap_response.raise_for_status = Mock()
        cap_response.json.return_value = {
            "status": "error",
            "code": "maximumResultsReached",
            "message": "Developer accounts are limited to a max of 100 results",
        }

        with patch("app.services.ingestion.article_ingestion_service.requests.get") as mock_get:
            mock_get.side_effect = [_response(page_one), cap_response]
            articles = service.fetch_articles(query="financial", max_pages=5)

        assert len(articles) == 100
        assert mock_get.call_count == 2
