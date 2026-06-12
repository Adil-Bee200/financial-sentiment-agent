from unittest.mock import Mock, patch

from app.services.pipeline.llm_content import remaining_llm_budget_for_run


class TestLlmBudget:
    def test_per_run_cap_limits_below_daily_remainder(self):
        db = Mock()
        with patch("app.services.pipeline.llm_content.remaining_llm_budget", return_value=40), patch(
            "app.services.pipeline.llm_content.settings"
        ) as mock_settings:
            mock_settings.MAX_LLM_ARTICLES_PER_RUN = 10
            assert remaining_llm_budget_for_run(db) == 10

    def test_daily_remainder_limits_below_per_run_cap(self):
        db = Mock()
        with patch("app.services.pipeline.llm_content.remaining_llm_budget", return_value=3), patch(
            "app.services.pipeline.llm_content.settings"
        ) as mock_settings:
            mock_settings.MAX_LLM_ARTICLES_PER_RUN = 10
            assert remaining_llm_budget_for_run(db) == 3

    def test_per_run_cap_disabled_uses_daily_only(self):
        db = Mock()
        with patch("app.services.pipeline.llm_content.remaining_llm_budget", return_value=25), patch(
            "app.services.pipeline.llm_content.settings"
        ) as mock_settings:
            mock_settings.MAX_LLM_ARTICLES_PER_RUN = 0
            assert remaining_llm_budget_for_run(db) == 25
