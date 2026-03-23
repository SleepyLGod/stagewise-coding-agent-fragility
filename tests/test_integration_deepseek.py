"""Real DeepSeek API integration test.

Exercises the full chain:
    HumanEvalPlus task -> DeepSeekClient -> run_loop -> RunLog schema

Skipped automatically when DEEPSEEK_API_KEY is absent so that CI runs
(which should not have live credentials) are never broken by this file.

Run explicitly with:
    uv run python -m pytest tests/test_integration_deepseek.py -v -s
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env before any skip decision so the key is visible.
load_dotenv(Path(__file__).parent.parent / ".env")

_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

pytestmark = pytest.mark.skipif(
    not _API_KEY,
    reason="DEEPSEEK_API_KEY not set — skipping live API integration tests.",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_clean_condition() -> "ConditionConfig":
    from stagewise_coding_agent_fragility.config.schema import ConditionConfig

    return ConditionConfig(
        condition_id="clean",
        injection_stage="none",
        perturbation_type="none",
        perturbation_strength="none",
    )


def _make_simple_task() -> "Task":
    """Return a hand-crafted trivial task that avoids loading the full dataset.

    The task is the canonical HumanEval/0 ``has_close_elements`` problem,
    reproduced inline so the test does not need the evalplus library to be
    installed or the dataset to be downloaded.
    """
    from stagewise_coding_agent_fragility.benchmarks.base import Task

    prompt = (
        "from typing import List\n\n\n"
        "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n"
        '    """ Check if in given list of numbers, are any two numbers closer to each other than\n'
        "    given threshold.\n"
        "    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n"
        "    False\n"
        "    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n"
        "    True\n"
        '    """\n'
    )
    test_code = (
        "def check(candidate):\n"
        "    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True\n"
        "    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False\n"
        "    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True\n"
        "    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False\n"
        "    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True\n\n"
        "check(has_close_elements)\n"
    )
    return Task(
        task_id="HumanEval/0",
        benchmark_name="humanevalplus",
        prompt=prompt,
        entry_point="has_close_elements",
        test_code=test_code,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_deepseek_chat_solves_trivial_task() -> None:
    """Full chain smoke test: DeepSeek Chat solves HumanEval/0 in one round.

    Uses ``deepseek-chat`` (not ``deepseek-reasoner``) to minimize cost and
    latency.  The test asserts structural correctness of the ``LoopResult``,
    not a specific answer.
    """
    from stagewise_coding_agent_fragility.agent.loop import run_loop
    from stagewise_coding_agent_fragility.execution.test_runner import PythonTestRunner
    from stagewise_coding_agent_fragility.models.deepseek import DeepSeekClient

    solver = DeepSeekClient("deepseek-chat", api_key=_API_KEY)
    test_runner = PythonTestRunner()
    task = _make_simple_task()
    condition = _make_clean_condition()

    result = run_loop(
        task=task,
        condition=condition,
        solver_model=solver,
        test_runner=test_runner,
        max_rounds=3,
        execution_timeout_seconds=10.0,
        model_temperature=0.0,
        model_max_tokens=1024,
        model_timeout_seconds=60.0,
        use_rule_based_failure_summary=True,
        perturb_fn=None,
    )

    # Structural assertions — the loop must have executed at least one round.
    assert len(result.rounds) >= 1, "Loop produced no rounds."
    first_round = result.rounds[0]
    assert first_round.generated_code.strip(), "Generated code must be non-empty."
    assert first_round.token_usage.total_tokens > 0, "Token usage must be positive."
    assert first_round.latency_seconds > 0.0, "Latency must be positive."

    # The final result record must be fully populated.
    assert result.final_result.num_rounds_executed == len(result.rounds)

    # For a trivial task, we expect the model to succeed.
    assert result.final_result.success, (
        f"Expected model to solve HumanEval/0 but it failed.\n"
        f"Generated code:\n{first_round.generated_code}\n"
        f"Failure: {first_round.execution_result.raw_failure}"
    )

