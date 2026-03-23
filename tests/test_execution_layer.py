"""Tests for the execution layer."""

from __future__ import annotations

from stagewise_coding_agent_fragility.execution.sandbox import LocalSandboxExecutor
from stagewise_coding_agent_fragility.execution.test_runner import PythonTestRunner
from stagewise_coding_agent_fragility.execution.test_runner import PythonTestTask


def test_python_test_runner_reports_success() -> None:
    """Runs a passing candidate successfully."""
    runner = PythonTestRunner(sandbox_executor=LocalSandboxExecutor())
    task = PythonTestTask(
        task_id="pass-case",
        test_code="assert add(1, 2) == 3",
    )

    result = runner.run(
        task=task,
        candidate_code="def add(a: int, b: int) -> int:\n    return a + b",
        timeout_seconds=1.0,
    )

    assert result.passed is True
    assert result.timeout is False
    assert result.raw_failure == ""
    assert result.parsed_failure is None


def test_python_test_runner_reports_failure() -> None:
    """Runs a failing candidate and parses the failure."""
    runner = PythonTestRunner(sandbox_executor=LocalSandboxExecutor())
    task = PythonTestTask(
        task_id="fail-case",
        test_code="assert add(1, 2) == 3",
    )

    result = runner.run(
        task=task,
        candidate_code="def add(a: int, b: int) -> int:\n    return a - b",
        timeout_seconds=1.0,
    )

    assert result.passed is False
    assert result.timeout is False
    assert "AssertionError" in result.raw_failure
    assert result.parsed_failure is not None
    assert result.parsed_failure["failure_type"] == "exception"
    assert result.parsed_failure["exception_type"] == "AssertionError"


def test_python_test_runner_reports_timeout() -> None:
    """Runs a timing-out candidate and reports timeout explicitly."""
    runner = PythonTestRunner(sandbox_executor=LocalSandboxExecutor())
    task = PythonTestTask(
        task_id="timeout-case",
        test_code="import time\ntime.sleep(1.0)",
    )

    result = runner.run(
        task=task,
        candidate_code="def noop() -> None:\n    return None",
        timeout_seconds=0.01,
    )

    assert result.passed is False
    assert result.timeout is True
    assert result.raw_failure == "Execution timed out."
    assert result.parsed_failure == {"failure_type": "timeout"}
