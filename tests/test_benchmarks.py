"""Tests for the benchmark adapter layer."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from stagewise_coding_agent_fragility.benchmarks.base import BenchmarkAdapter, Task
from stagewise_coding_agent_fragility.benchmarks.humanevalplus import (
    HumanEvalPlusAdapter,
    _build_test_code,
)

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FAKE_RAW_TASKS: dict[str, dict] = {
    "HumanEval/0": {
        "task_id": "HumanEval/0",
        "prompt": "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    ...\n",
        "canonical_solution": "    ...\n",
        "entry_point": "has_close_elements",
        "test": "def check(candidate):\n    assert candidate([1.0, 2.0], 0.5) == False\n",
        "contract": "",
        "base_input": [[1.0, 2.0], 0.5],
        "plus_input": [],
        "atol": 0,
    },
    "HumanEval/1": {
        "task_id": "HumanEval/1",
        "prompt": "def separate_paren_groups(paren_string: str) -> List[str]:\n    ...\n",
        "canonical_solution": "    ...\n",
        "entry_point": "separate_paren_groups",
        "test": "def check(candidate):\n    assert candidate('(()())') == ['(()())']\n",
        "contract": "",
        "base_input": ["(()())"],
    },
}


@pytest.fixture()
def adapter() -> HumanEvalPlusAdapter:
    """Return an adapter backed by fake data (no network/disk access)."""
    with patch(
        "stagewise_coding_agent_fragility.benchmarks.humanevalplus.get_human_eval_plus",
        return_value=_FAKE_RAW_TASKS,
    ):
        a = HumanEvalPlusAdapter()
        a.load_tasks()  # force loading while mock is active
    return a


# ---------------------------------------------------------------------------
# _build_test_code
# ---------------------------------------------------------------------------


def test_build_test_code_appends_check_call() -> None:
    """The assembled test code must end with ``check(entry_point)``."""
    raw = "def check(candidate):\n    assert candidate(1) == 2"
    result = _build_test_code("my_func", raw)

    assert result.endswith("check(my_func)\n")
    assert "def check(candidate):" in result


def test_build_test_code_strips_trailing_whitespace() -> None:
    """Trailing whitespace on the raw test should not produce blank lines."""
    raw = "def check(candidate):\n    pass   \n\n\n"
    result = _build_test_code("f", raw)

    # There should be exactly one blank line between the check body and the call
    lines = result.split("\n")
    # last line is empty (trailing \n), second-to-last is "check(f)"
    assert lines[-1] == ""
    assert lines[-2] == "check(f)"


# ---------------------------------------------------------------------------
# HumanEvalPlusAdapter
# ---------------------------------------------------------------------------


def test_adapter_benchmark_name() -> None:
    """The adapter reports its canonical benchmark name."""
    adapter = HumanEvalPlusAdapter()
    assert adapter.benchmark_name == "humanevalplus"


def test_adapter_load_tasks_returns_all(adapter: HumanEvalPlusAdapter) -> None:
    """load_tasks returns the correct number of Task objects."""
    tasks = adapter.load_tasks()
    assert len(tasks) == 2
    assert all(isinstance(t, Task) for t in tasks)


def test_adapter_task_fields(adapter: HumanEvalPlusAdapter) -> None:
    """Each Task has correctly mapped fields from the raw data."""
    task = adapter.get_task("HumanEval/0")

    assert task.task_id == "HumanEval/0"
    assert task.benchmark_name == "humanevalplus"
    assert "has_close_elements" in task.prompt
    assert task.entry_point == "has_close_elements"
    assert "check(has_close_elements)" in task.test_code
    assert task.canonical_solution == "    ...\n"


def test_adapter_metadata_includes_available_keys(
    adapter: HumanEvalPlusAdapter,
) -> None:
    """Metadata should contain only keys that exist in the raw record."""
    task_0 = adapter.get_task("HumanEval/0")
    assert "contract" in task_0.metadata
    assert "base_input" in task_0.metadata
    assert "atol" in task_0.metadata

    task_1 = adapter.get_task("HumanEval/1")
    # HumanEval/1 in our fake data lacks 'plus_input' and 'atol'
    assert "atol" not in task_1.metadata
    assert "plus_input" not in task_1.metadata


def test_adapter_get_task_raises_on_missing(adapter: HumanEvalPlusAdapter) -> None:
    """get_task raises KeyError for an unknown task_id."""
    with pytest.raises(KeyError):
        adapter.get_task("HumanEval/999")


def test_adapter_caching(adapter: HumanEvalPlusAdapter) -> None:
    """Repeated load_tasks calls return the same objects (caching)."""
    first = adapter.load_tasks()
    second = adapter.load_tasks()
    assert first == second


def test_adapter_satisfies_protocol() -> None:
    """HumanEvalPlusAdapter structurally conforms to BenchmarkAdapter."""
    assert isinstance(HumanEvalPlusAdapter(), BenchmarkAdapter)

