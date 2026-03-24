"""HumanEval+ benchmark adapter.

Loads tasks from the ``evalplus`` library and converts them into the project's
internal :class:`~stagewise_coding_agent_fragility.benchmarks.base.Task` schema.
All ``evalplus``-specific logic is confined to this module.
"""

from __future__ import annotations

from typing import Sequence

from evalplus.data import get_human_eval_plus

from stagewise_coding_agent_fragility.benchmarks.base import Task

_BENCHMARK_NAME = "humanevalplus"


def _build_test_code(entry_point: str, raw_test: str) -> str:
    """Assemble a self-contained test script from raw HumanEval+ test data.

    The raw ``test`` field from the dataset defines a ``check(candidate)``
    function.  We append a call that passes the candidate's ``entry_point``
    so the combined script (candidate code + this test code) is directly
    executable.

    Args:
        entry_point: Name of the function under test.
        raw_test: Raw ``test`` field from the HumanEval+ dataset.

    Returns:
        Executable test code string.
    """
    stripped_test = raw_test.rstrip()
    return f"{stripped_test}\n\ncheck({entry_point})\n"


class HumanEvalPlusAdapter:
    """Loads HumanEval+ tasks and exposes them through the ``BenchmarkAdapter`` protocol."""

    def __init__(self, *, mini: bool = False) -> None:
        """Initialize the adapter.

        Args:
            mini: If ``True``, load the smaller *mini* split for fast iteration.
        """
        self._mini = mini
        self._tasks: dict[str, Task] | None = None

    @property
    def benchmark_name(self) -> str:
        """Canonical short name for this benchmark."""
        return _BENCHMARK_NAME

    def load_tasks(self) -> Sequence[Task]:
        """Load all HumanEval+ tasks.

        Tasks are cached after the first call so repeated invocations are free.

        Returns:
            An ordered sequence of ``Task`` objects.
        """
        self._ensure_loaded()
        assert self._tasks is not None
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Task:
        """Return a single task by its identifier.

        Args:
            task_id: The task identifier (e.g. ``"HumanEval/12"``).

        Returns:
            The matching ``Task``.

        Raises:
            KeyError: If no task with the given id exists.
        """
        self._ensure_loaded()
        assert self._tasks is not None
        return self._tasks[task_id]

    def select_subset(
        self,
        task_limit: int = 0,
        task_ids: list[str] | None = None,
    ) -> list[Task]:
        """Return a filtered subset of tasks.

        If ``task_ids`` is provided, only those tasks (in given order) are
        returned.  Otherwise, if ``task_limit > 0``, the first ``task_limit``
        tasks (by benchmark ordering) are returned.  If neither filter
        applies, all tasks are returned.

        Args:
            task_limit: Maximum number of tasks to return (0 = no limit).
            task_ids: Explicit list of task IDs to include.

        Returns:
            Ordered list of selected ``Task`` objects.

        Raises:
            KeyError: If any of the given ``task_ids`` does not exist.
        """
        if task_ids is not None:
            return [self.get_task(tid) for tid in task_ids]
        all_tasks = list(self.load_tasks())
        if task_limit > 0:
            return all_tasks[:task_limit]
        return all_tasks

    def _ensure_loaded(self) -> None:
        """Lazily load and cache tasks from ``evalplus``."""
        if self._tasks is not None:
            return

        raw_tasks = get_human_eval_plus(mini=self._mini)
        converted: dict[str, Task] = {}
        for task_id, raw in raw_tasks.items():
            converted[task_id] = Task(
                task_id=task_id,
                benchmark_name=_BENCHMARK_NAME,
                prompt=raw["prompt"],
                entry_point=raw["entry_point"],
                test_code=_build_test_code(raw["entry_point"], raw["test"]),
                canonical_solution=raw.get("canonical_solution", ""),
                metadata={
                    key: raw[key]
                    for key in ("contract", "base_input", "plus_input", "atol")
                    if key in raw
                },
            )
        self._tasks = converted


