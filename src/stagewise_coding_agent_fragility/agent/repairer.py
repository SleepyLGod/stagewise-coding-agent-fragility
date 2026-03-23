"""Code repair step.

``repair`` sends a repair prompt to the model and returns the raw response.
Code extraction is left to the caller (``agent.solver.extract_code``),
keeping this module's responsibility to one thing: make the model call.
"""

from __future__ import annotations

from stagewise_coding_agent_fragility.models.base import ModelClient
from stagewise_coding_agent_fragility.models.response_types import ModelResponse


def repair(
    repair_prompt: str,
    model: ModelClient,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
) -> ModelResponse:
    """Send the repair prompt to the model and return the raw response.

    Args:
        repair_prompt: The full repair prompt, formatted by the prompting layer.
        model: The model client to use.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        timeout_seconds: HTTP request timeout in seconds.

    Returns:
        The raw ``ModelResponse`` from the model.
    """
    return model.complete(
        repair_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
    )

