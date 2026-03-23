"""Failure summarization: rule-based and model-based variants.

``summarize_failure_rule_based`` produces a compact text summary from structured
execution data without making any model calls.

``summarize_failure_with_model`` delegates to the model to produce a richer
natural-language explanation — used when ``LoopConfig.use_rule_based_failure_summary``
is False.
"""

from __future__ import annotations

from stagewise_coding_agent_fragility.execution.execution_result import ExecutionResult
from stagewise_coding_agent_fragility.models.base import ModelClient
from stagewise_coding_agent_fragility.models.response_types import ModelResponse
from stagewise_coding_agent_fragility.prompting.failure_summary_prompt import (
    build_failure_summary_prompt,
)

_MAX_TRACEBACK_LINES = 20


def summarize_failure_rule_based(result: ExecutionResult) -> str:
    """Build a compact failure summary from an execution result using simple rules.

    Args:
        result: The execution result to summarize.

    Returns:
        A human-readable failure summary string.
    """
    if result.passed:
        return "All tests passed."

    if result.timeout:
        return (
            "Execution timed out. "
            "The function may contain an infinite loop or be too slow."
        )

    if result.parsed_failure:
        exception_type = result.parsed_failure.get("exception_type", "")
        message = result.parsed_failure.get("message", result.raw_failure)
        if exception_type:
            return f"Tests failed with {exception_type}: {message}"

    raw = result.raw_failure.strip()
    if not raw:
        return "Tests failed with no output captured."

    lines = raw.splitlines()
    if len(lines) > _MAX_TRACEBACK_LINES:
        truncated = "\n".join(lines[-_MAX_TRACEBACK_LINES:])
        return f"Tests failed with the following error (last {_MAX_TRACEBACK_LINES} lines):\n{truncated}"

    return f"Tests failed with the following error:\n{raw}"


def summarize_failure_with_model(
    candidate_code: str,
    result: ExecutionResult,
    model: ModelClient,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
) -> tuple[str, ModelResponse]:
    """Build a failure summary by calling the model.

    Args:
        candidate_code: The code that was executed.
        result: The execution result to summarize.
        model: The model client to use.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        timeout_seconds: HTTP timeout in seconds.

    Returns:
        A tuple of ``(summary_text, model_response)``.
    """
    prompt = build_failure_summary_prompt(
        candidate_code=candidate_code,
        raw_failure=result.raw_failure,
    )
    response = model.complete(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
    )
    return response.response_text.strip(), response

