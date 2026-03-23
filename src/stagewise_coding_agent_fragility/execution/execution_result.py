"""Runtime result types for code execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionResult:
    """Represents the result of executing candidate code against tests.

    Attributes:
        passed: Whether the candidate code passed the test run.
        stdout: Captured standard output.
        stderr: Captured standard error.
        timeout: Whether the execution timed out.
        runtime_seconds: Wall-clock execution time in seconds.
        raw_failure: Raw failure text extracted from execution output.
        parsed_failure: Structured failure details, when available.
    """

    passed: bool
    stdout: str
    stderr: str
    timeout: bool
    runtime_seconds: float
    raw_failure: str
    parsed_failure: dict[str, Any] | None
