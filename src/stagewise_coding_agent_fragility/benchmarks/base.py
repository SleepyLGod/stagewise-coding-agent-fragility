"""Benchmark adapter base types.

Defines the internal ``Task`` schema and the ``BenchmarkAdapter`` protocol that
every concrete benchmark adapter must implement.  The agent loop and experiment
runner depend only on these types — never on benchmark-specific libraries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class Task:
    """One benchmark task in the project's internal representation.

    Attributes:
        task_id: Stable identifier within the benchmark (e.g. ``"HumanEval/12"``).
        benchmark_name: Name of the originating benchmark (e.g. ``"humanevalplus"``).
        prompt: Function signature with docstring — the text shown to the model.
        entry_point: Name of the function the candidate code must define.
        test_code: Executable Python test code that validates a candidate
            implementation.  When concatenated after the candidate code this
            must form a runnable script whose exit code indicates pass/fail.
        canonical_solution: Reference implementation provided by the benchmark,
            kept for analysis and debugging — never shown to the model.
        metadata: Arbitrary benchmark-specific metadata preserved for logging.
    """

    task_id: str
    benchmark_name: str
    prompt: str
    entry_point: str
    test_code: str
    canonical_solution: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class BenchmarkAdapter(Protocol):
    """Protocol that every benchmark adapter must satisfy."""

    @property
    def benchmark_name(self) -> str:
        """Canonical short name for this benchmark."""
        ...

    def load_tasks(self) -> Sequence[Task]:
        """Load and return all tasks from the benchmark.

        Returns:
            An ordered sequence of ``Task`` objects.
        """
        ...

    def get_task(self, task_id: str) -> Task:
        """Return a single task by its identifier.

        Args:
            task_id: The task identifier to look up.

        Returns:
            The matching ``Task``.

        Raises:
            KeyError: If no task with the given id exists.
        """
        ...

