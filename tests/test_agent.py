"""Tests for the agent layer: solver, failure_summary, repairer, and loop."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from stagewise_coding_agent_fragility.agent.failure_summary import (
    summarize_failure_rule_based,
)
from stagewise_coding_agent_fragility.agent.loop import LoopResult, run_loop
from stagewise_coding_agent_fragility.agent.solver import extract_code
from stagewise_coding_agent_fragility.benchmarks.base import Task
from stagewise_coding_agent_fragility.config.schema import ConditionConfig
from stagewise_coding_agent_fragility.execution.execution_result import ExecutionResult
from stagewise_coding_agent_fragility.logging.schema import TokenUsage
from stagewise_coding_agent_fragility.models.response_types import ModelResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASSING_RESULT = ExecutionResult(
    passed=True, stdout="", stderr="", timeout=False,
    runtime_seconds=0.01, raw_failure="", parsed_failure=None,
)
_FAILING_RESULT = ExecutionResult(
    passed=False, stdout="", stderr="AssertionError: assert 3 == -1",
    timeout=False, runtime_seconds=0.01,
    raw_failure="AssertionError: assert 3 == -1",
    parsed_failure={"failure_type": "exception", "exception_type": "AssertionError",
                    "message": "AssertionError: assert 3 == -1"},
)
_TIMEOUT_RESULT = ExecutionResult(
    passed=False, stdout="", stderr="", timeout=True,
    runtime_seconds=5.0, raw_failure="Execution timed out.", parsed_failure=None,
)
_SAMPLE_TASK = Task(
    task_id="HumanEval/0",
    benchmark_name="humanevalplus",
    prompt="def add(a: int, b: int) -> int:\n    \"\"\"Return a + b.\"\"\"\n",
    entry_point="add",
    test_code="assert add(1, 2) == 3",
)
_CLEAN_CONDITION = ConditionConfig(
    condition_id="clean",
    injection_stage="none",
    perturbation_type="none",
    perturbation_strength="none",
)


def _make_model_response(text: str = "def add(a, b): return a + b") -> ModelResponse:
    return ModelResponse(
        model_name="deepseek-reasoner",
        prompt_text="prompt",
        response_text=text,
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        latency_seconds=0.5,
    )


def _make_mock_model(response_text: str = "def add(a, b): return a + b") -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = _make_model_response(response_text)
    return mock


def _make_mock_runner(exec_results: list[ExecutionResult]) -> MagicMock:
    mock = MagicMock()
    mock.run.side_effect = exec_results
    return mock


# ---------------------------------------------------------------------------
# extract_code
# ---------------------------------------------------------------------------


def test_extract_code_from_python_fence() -> None:
    assert extract_code("```python\ndef f(): pass\n```") == "def f(): pass"


def test_extract_code_from_generic_fence() -> None:
    assert extract_code("```\ndef f(): pass\n```") == "def f(): pass"


def test_extract_code_fallback_to_raw() -> None:
    raw = "def f(): pass"
    assert extract_code(raw) == raw


def test_extract_code_strips_trailing_whitespace() -> None:
    result = extract_code("```python\ndef f(): pass   \n```")
    assert not result.endswith(" ")


# ---------------------------------------------------------------------------
# summarize_failure_rule_based
# ---------------------------------------------------------------------------


def test_summarize_passed_result() -> None:
    assert summarize_failure_rule_based(_PASSING_RESULT) == "All tests passed."


def test_summarize_timeout_result() -> None:
    summary = summarize_failure_rule_based(_TIMEOUT_RESULT)
    assert "timed out" in summary.lower()


def test_summarize_exception_result() -> None:
    summary = summarize_failure_rule_based(_FAILING_RESULT)
    assert "AssertionError" in summary


def test_summarize_empty_failure() -> None:
    result = ExecutionResult(
        passed=False, stdout="", stderr="", timeout=False,
        runtime_seconds=0.01, raw_failure="", parsed_failure=None,
    )
    summary = summarize_failure_rule_based(result)
    assert "no output" in summary.lower()


# ---------------------------------------------------------------------------
# run_loop — clean condition (no perturbation)
# ---------------------------------------------------------------------------


def test_run_loop_success_on_first_round() -> None:
    """Loop terminates after round 0 when tests pass immediately."""
    model = _make_mock_model("```python\ndef add(a, b): return a + b\n```")
    runner = _make_mock_runner([_PASSING_RESULT])

    result = run_loop(
        task=_SAMPLE_TASK, condition=_CLEAN_CONDITION,
        solver_model=model, test_runner=runner,
        max_rounds=3, execution_timeout_seconds=5.0,
        model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
        use_rule_based_failure_summary=True,
    )

    assert isinstance(result, LoopResult)
    assert result.final_result.success is True
    assert result.final_result.num_rounds_executed == 1
    assert len(result.rounds) == 1
    assert result.rounds[0].repair_prompt_text is None


def test_run_loop_repair_on_second_round() -> None:
    """Loop executes a repair call when round 0 fails."""
    model = _make_mock_model()
    runner = _make_mock_runner([_FAILING_RESULT, _PASSING_RESULT])

    result = run_loop(
        task=_SAMPLE_TASK, condition=_CLEAN_CONDITION,
        solver_model=model, test_runner=runner,
        max_rounds=3, execution_timeout_seconds=5.0,
        model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
        use_rule_based_failure_summary=True,
    )

    assert result.final_result.success is True
    assert result.final_result.num_rounds_executed == 2
    assert result.rounds[1].repair_prompt_text is not None


def test_run_loop_exhausts_max_rounds() -> None:
    """Loop stops at max_rounds and marks failure when tests never pass."""
    model = _make_mock_model()
    runner = _make_mock_runner([_FAILING_RESULT] * 3)

    result = run_loop(
        task=_SAMPLE_TASK, condition=_CLEAN_CONDITION,
        solver_model=model, test_runner=runner,
        max_rounds=3, execution_timeout_seconds=5.0,
        model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
        use_rule_based_failure_summary=True,
    )

    assert result.final_result.success is False
    assert result.final_result.num_rounds_executed == 3
    assert result.final_result.failure_type == "stuck_loop"


def test_run_loop_records_token_usage() -> None:
    """Each RoundRecord contains token usage from the model response."""
    model = _make_mock_model()
    runner = _make_mock_runner([_PASSING_RESULT])

    result = run_loop(
        task=_SAMPLE_TASK, condition=_CLEAN_CONDITION,
        solver_model=model, test_runner=runner,
        max_rounds=3, execution_timeout_seconds=5.0,
        model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
        use_rule_based_failure_summary=True,
    )

    assert result.rounds[0].token_usage.total_tokens == 30


def test_run_loop_raises_without_summary_model_when_model_based() -> None:
    """ValueError raised if model-based summarization requested without a model."""
    with pytest.raises(ValueError, match="failure_summary_model"):
        run_loop(
            task=_SAMPLE_TASK, condition=_CLEAN_CONDITION,
            solver_model=_make_mock_model(), test_runner=_make_mock_runner([]),
            max_rounds=3, execution_timeout_seconds=5.0,
            model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
            use_rule_based_failure_summary=False,
            failure_summary_model=None,
        )


# ---------------------------------------------------------------------------
# run_loop — perturbation conditions
# ---------------------------------------------------------------------------


def test_run_loop_perturbs_task_prompt() -> None:
    """Loop stores perturbed_task_prompt_text when injection_stage is task_prompt."""
    condition = ConditionConfig(
        condition_id="task_paraphrase",
        injection_stage="task_prompt",
        perturbation_type="semantic_paraphrase",
        perturbation_strength="default",
    )
    model = _make_mock_model()
    runner = _make_mock_runner([_PASSING_RESULT])
    perturb_fn = lambda text: f"PERTURBED: {text}"  # noqa: E731

    result = run_loop(
        task=_SAMPLE_TASK, condition=condition,
        solver_model=model, test_runner=runner,
        max_rounds=3, execution_timeout_seconds=5.0,
        model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
        use_rule_based_failure_summary=True,
        perturb_fn=perturb_fn,
    )

    assert result.rounds[0].perturbed_task_prompt_text is not None
    assert result.rounds[0].perturbed_task_prompt_text.startswith("PERTURBED:")


def test_run_loop_perturbs_failure_summary() -> None:
    """Loop stores perturbed_failure_summary_text when injection_stage is failure_summary."""
    condition = ConditionConfig(
        condition_id="failure_paraphrase",
        injection_stage="failure_summary",
        perturbation_type="semantic_paraphrase",
        perturbation_strength="default",
    )
    model = _make_mock_model()
    runner = _make_mock_runner([_FAILING_RESULT, _PASSING_RESULT])
    perturb_fn = lambda text: f"PERTURBED: {text}"  # noqa: E731

    result = run_loop(
        task=_SAMPLE_TASK, condition=condition,
        solver_model=model, test_runner=runner,
        max_rounds=3, execution_timeout_seconds=5.0,
        model_temperature=0.1, model_max_tokens=256, model_timeout_seconds=30.0,
        use_rule_based_failure_summary=True,
        perturb_fn=perturb_fn,
    )

    assert result.rounds[0].perturbed_failure_summary_text is not None
    assert result.rounds[0].perturbed_failure_summary_text.startswith("PERTURBED:")

