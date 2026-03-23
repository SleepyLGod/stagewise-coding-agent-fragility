"""Response types for model client calls.

These types are the single source of truth for what a model call returns.
All downstream consumers (agent loop, logging) depend on these types only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stagewise_coding_agent_fragility.logging.schema import TokenUsage


@dataclass(frozen=True)
class ModelResponse:
    """The normalized result of one model completion call.

    Attributes:
        model_name: The model identifier used for this call (e.g. ``"deepseek-reasoner"``).
        prompt_text: The exact prompt string sent to the model.
        response_text: The generated text from the model.
        token_usage: Prompt, completion, and total token counts.
        latency_seconds: Wall-clock time from request send to response received.
        raw_response: The raw API response payload, kept for debugging and logging.
            Never relied on for business logic.
    """

    model_name: str
    prompt_text: str
    response_text: str
    token_usage: TokenUsage
    latency_seconds: float
    raw_response: dict[str, Any] = field(default_factory=dict)

