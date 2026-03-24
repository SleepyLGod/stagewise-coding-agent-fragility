"""Benchmark adapter for SWE-bench Verified.

Loads instances from the ``princeton-nlp/SWE-bench_Verified`` dataset on
Hugging Face and maps them into the project's internal ``Task`` representation.
"""

from __future__ import annotations

import logging
from typing import Sequence

from stagewise_coding_agent_fragility.benchmarks.base import BenchmarkAdapter, Task

logger = logging.getLogger(__name__)


class SWEBenchVerifiedAdapter(BenchmarkAdapter):
    """Adapter for SWE-bench Verified.
    
    This benchmark differs from typical algorithm synthetic suites. The agent
    must fix a real-world repository issue. The returned ``Task`` objects use
    the ``metadata`` field to carry repository details required by a specialized
    Docker test runner.
    """

    def __init__(
        self,
        task_ids: Sequence[str] | None = None,
        task_limit: int | None = None,
    ) -> None:
        """Initialize the SWE-bench adapter.

        Args:
            task_ids: Optional list of explicit instance IDs to load.
            task_limit: Optional maximum number of tasks to load.
        """
        self._task_ids = set(task_ids) if task_ids is not None else None
        self._task_limit = task_limit
        self._tasks: dict[str, Task] = {}

    @property
    def benchmark_name(self) -> str:
        """Name of the benchmark."""
        return "swebench_verified"

    def load_tasks(self) -> Sequence[Task]:
        """Lazy load instances from the Hugging Face dataset.

        Returns:
            An ordered sequence of SWE-bench tasks.
        """
        if self._tasks:
            return list(self._tasks.values())
            
        import datasets

        logger.info("Loading SWE-bench Verified dataset from Hugging Face...")
        dataset = datasets.load_dataset("princeton-nlp/SWE-bench_Verified", split="test")

        count = 0
        for item in dataset:
            instance_id = item["instance_id"]
            
            # Filter if explicit task format provided
            if self._task_ids is not None and instance_id not in self._task_ids:
                continue

            # In SWE-bench, the 'problem_statement' is what the agent sees.
            # The 'test_patch' and 'repo' details dictate how it is tested.
            task = Task(
                task_id=instance_id,
                benchmark_name=self.benchmark_name,
                prompt=item["problem_statement"],
                entry_point="",  # SWE Bench relies on filesystem patches, not function entry points
                test_code=item["test_patch"], 
                canonical_solution=item.get("patch", ""),
                metadata={
                    "repo": item["repo"],
                    "base_commit": item["base_commit"],
                    "hints_text": item.get("hints_text", ""),
                    "environment_setup_commit": item.get("environment_setup_commit", ""),
                    "version": item.get("version", ""),
                    "created_at": item.get("created_at", ""),
                },
            )

            self._tasks[instance_id] = task
            count += 1

            if self._task_limit is not None and count >= self._task_limit:
                break

        if not self._tasks:
            logger.warning("No tasks matched the criteria for SWE-bench.")

        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Task:
        """Return a single task by its identifier.

        Args:
            task_id: The SWE-bench instance_id.

        Returns:
            The corresponding ``Task``.

        Raises:
            KeyError: If the task cannot be found.
        """
        if not self._tasks:
            self.load_tasks()

        if task_id not in self._tasks:
            raise KeyError(f"Task '{task_id}' not found in SWE-bench Verified.")
            
        return self._tasks[task_id]
