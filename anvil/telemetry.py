import logging
from typing import Any, Dict

logger = logging.getLogger("anvil.telemetry")


class TokenMetrics:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost_usd = 0.0

    def record_usage(
        self, prompt_t: int, completion_t: int, cost_per_1m_input: float = 0.0, cost_per_1m_output: float = 0.0
    ):
        self.prompt_tokens += prompt_t
        self.completion_tokens += completion_t
        self.total_cost_usd += (prompt_t / 1_000_000.0) * cost_per_1m_input + (
            completion_t / 1_000_000.0
        ) * cost_per_1m_output

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "estimated_cost_usd": round(self.total_cost_usd, 6),
        }
