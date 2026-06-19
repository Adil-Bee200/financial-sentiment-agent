from app.services.llm.cost import estimate_llm_cost_usd


class TestLlmCost:
    def test_estimate_llm_cost_usd(self, monkeypatch):
        monkeypatch.setenv("LLM_INPUT_COST_PER_1M", "0.25")
        monkeypatch.setenv("LLM_OUTPUT_COST_PER_1M", "2.00")
        from app.core.config import Settings

        settings = Settings()
        cost = estimate_llm_cost_usd(100_000, 10_000)
        expected = round((100_000 / 1_000_000) * settings.LLM_INPUT_COST_PER_1M + (10_000 / 1_000_000) * settings.LLM_OUTPUT_COST_PER_1M, 4)
        assert cost == expected
