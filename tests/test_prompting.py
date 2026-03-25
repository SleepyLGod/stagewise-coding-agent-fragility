"""Tests for the prompting layer."""

from __future__ import annotations

import pytest

from stagewise_coding_agent_fragility.benchmarks.base import Task
from stagewise_coding_agent_fragility.prompting.failure_summary_prompt import (
    build_failure_summary_prompt,
)
from stagewise_coding_agent_fragility.prompting.perturbation_prompt import (
    build_perturbation_prompt,
)
from stagewise_coding_agent_fragility.prompting.repair_prompt import build_repair_prompt
from stagewise_coding_agent_fragility.prompting.task_prompt import build_task_prompt

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLE_TASK = Task(
    task_id="HumanEval/0",
    benchmark_name="humanevalplus",
    prompt="def add(a: int, b: int) -> int:\n    \"\"\"Return a + b.\"\"\"\n",
    entry_point="add",
    test_code="assert add(1, 2) == 3",
)


# ---------------------------------------------------------------------------
# task_prompt
# ---------------------------------------------------------------------------


def test_build_task_prompt_contains_prompt_text() -> None:
    """build_task_prompt embeds the task prompt verbatim."""
    prompt = build_task_prompt(_SAMPLE_TASK)
    assert "def add(a: int, b: int) -> int:" in prompt


def test_build_task_prompt_is_string() -> None:
    """build_task_prompt returns a non-empty string."""
    prompt = build_task_prompt(_SAMPLE_TASK)
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_build_task_prompt_deterministic() -> None:
    """build_task_prompt returns the same result on repeated calls."""
    assert build_task_prompt(_SAMPLE_TASK) == build_task_prompt(_SAMPLE_TASK)


# ---------------------------------------------------------------------------
# repair_prompt
# ---------------------------------------------------------------------------


def test_build_repair_prompt_contains_all_sections() -> None:
    """build_repair_prompt embeds task prompt, code, and failure summary."""
    prompt = build_repair_prompt(
        task_prompt="Implement add.",
        candidate_code="def add(a, b): return a - b",
        failure_summary="AssertionError: expected 3 got -1",
    )
    assert "Implement add." in prompt
    assert "def add(a, b): return a - b" in prompt
    assert "AssertionError" in prompt


def test_build_repair_prompt_strips_whitespace() -> None:
    """build_repair_prompt strips leading/trailing whitespace from each input."""
    prompt_a = build_repair_prompt("task\n", "code\n", "summary\n")
    prompt_b = build_repair_prompt("task", "code", "summary")
    assert prompt_a == prompt_b


# ---------------------------------------------------------------------------
# failure_summary_prompt
# ---------------------------------------------------------------------------


def test_build_failure_summary_prompt_contains_code_and_error() -> None:
    """build_failure_summary_prompt embeds code and raw_failure."""
    prompt = build_failure_summary_prompt(
        candidate_code="def add(a, b): return a - b",
        raw_failure="AssertionError: assert 3 == -1",
    )
    assert "def add(a, b): return a - b" in prompt
    assert "AssertionError" in prompt


def test_build_failure_summary_prompt_handles_empty_failure() -> None:
    """build_failure_summary_prompt uses a placeholder for empty raw_failure."""
    prompt = build_failure_summary_prompt(candidate_code="def f(): pass", raw_failure="")
    assert "(no output captured)" in prompt


# ---------------------------------------------------------------------------
# perturbation_prompt
# ---------------------------------------------------------------------------


def test_build_perturbation_prompt_semantic_paraphrase() -> None:
    """build_perturbation_prompt returns a non-empty prompt for semantic_paraphrase."""
    prompt = build_perturbation_prompt(
        "Return the sum of a and b.",
        "semantic_paraphrase",
        "task_prompt",
    )
    assert "Return the sum of a and b." in prompt
    assert "Injection stage: task_prompt" in prompt
    assert len(prompt) > 0


def test_build_perturbation_prompt_mild_simplification() -> None:
    """build_perturbation_prompt returns a non-empty prompt for mild_simplification."""
    prompt = build_perturbation_prompt(
        "AssertionError: expected 3, got -1",
        "mild_simplification",
        "failure_summary",
    )
    assert "AssertionError: expected 3, got -1" in prompt


def test_build_perturbation_prompt_is_stage_aware() -> None:
    """Different injection stages should produce different instructions."""
    task_prompt = build_perturbation_prompt("x", "semantic_paraphrase", "task_prompt")
    failure_prompt = build_perturbation_prompt("x", "semantic_paraphrase", "failure_summary")

    assert "copy them exactly" in task_prompt
    assert "causal chain" in failure_prompt


def test_build_perturbation_prompt_rejects_unknown_type() -> None:
    """build_perturbation_prompt raises ValueError for unknown perturbation types."""
    with pytest.raises(ValueError, match="Unsupported perturbation_type"):
        build_perturbation_prompt("some text", "totally_unknown_type", "task_prompt")


def test_build_perturbation_prompt_rejects_unknown_stage() -> None:
    """build_perturbation_prompt raises ValueError for unknown stages."""
    with pytest.raises(ValueError, match="Unsupported injection_stage"):
        build_perturbation_prompt("some text", "semantic_paraphrase", "revision_prompt")


def test_build_perturbation_prompt_deterministic() -> None:
    """build_perturbation_prompt is deterministic."""
    text = "Compute the factorial of n."
    assert (
        build_perturbation_prompt(text, "semantic_paraphrase", "task_prompt")
        == build_perturbation_prompt(text, "semantic_paraphrase", "task_prompt")
    )

