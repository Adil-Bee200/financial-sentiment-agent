from app.services.pipeline.llm_content import build_llm_input, truncate_at_word


class TestLlmContent:
    def test_build_llm_input_includes_description_and_truncated_body(self):
        article = {
            "title": "NVDA earnings beat",
            "description": "NVIDIA reported strong Q4 results.",
            "content": "word " * 500,
        }
        title, content = build_llm_input(article, body_max_chars=100)
        assert title == "NVDA earnings beat"
        assert "NVIDIA reported strong Q4 results." in content
        assert len(content) < len("word " * 500)

    def test_build_llm_input_description_only_when_no_body(self):
        article = {
            "title": "Headline",
            "description": "Short desc",
            "content": None,
        }
        title, content = build_llm_input(article)
        assert title == "Headline"
        assert content == "Short desc"

    def test_truncate_at_word_adds_ellipsis(self):
        text = "one two three four five six seven eight nine ten"
        result = truncate_at_word(text, 20)
        assert result.endswith("...")
        assert len(result) <= 23
