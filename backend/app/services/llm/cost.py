from app.core.config import settings


def estimate_llm_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    input_cost = (prompt_tokens / 1_000_000) * settings.LLM_INPUT_COST_PER_1M
    output_cost = (completion_tokens / 1_000_000) * settings.LLM_OUTPUT_COST_PER_1M
    return round(input_cost + output_cost, 4)
