"""Build the flat list of run plans for one experiment.

A ``RunPlan`` is the smallest unit of work: one task × one condition × one
repeat index.  The planner produces the full Cartesian product so that the
runner can iterate over it sequentially (or in parallel, in future).
"""

from __future__ import annotations

from dataclasses import dataclass

from stagewise_coding_agent_fragility.benchmarks.base import Task
from stagewise_coding_agent_fragility.config.schema import ConditionConfig


@dataclass(frozen=True)
class RunPlan:
    """One concrete unit of experimental work.

    Attributes:
        run_id: Unique identifier derived from task, condition, and repeat.
        task: The benchmark task to solve.
        condition: The experiment condition to apply.
        repeat_index: Zero-based index within repeated runs for this
            task × condition pair.
    """

    run_id: str
    task: Task
    condition: ConditionConfig
    repeat_index: int


def build_run_plans(
    tasks: list[Task],
    conditions: list[ConditionConfig],
    repeats: int,
) -> list[RunPlan]:
    """Build the full list of run plans for an experiment.

    Iterates over tasks × conditions × repeat_index in that order.

    Args:
        tasks: Benchmark tasks to include.
        conditions: Experiment conditions to apply.
        repeats: Number of times each task × condition pair is repeated.

    Returns:
        Ordered list of ``RunPlan`` objects.
    """
    plans: list[RunPlan] = []
    for task in tasks:
        for condition in conditions:
            for repeat_index in range(repeats):
                run_id = _build_run_id(task, condition, repeat_index)
                plans.append(
                    RunPlan(
                        run_id=run_id,
                        task=task,
                        condition=condition,
                        repeat_index=repeat_index,
                    )
                )
    return plans


def _build_run_id(task: Task, condition: ConditionConfig, repeat_index: int) -> str:
    """Construct a deterministic run ID from task, condition, and repeat.

    Format: ``{benchmark}__{task_slug}__{injection_stage}__{perturbation_type}__r{repeat}``

    Args:
        task: The benchmark task.
        condition: The experiment condition.
        repeat_index: The repeat index.

    Returns:
        A filesystem-safe run ID string.
    """
    task_slug = task.task_id.replace("/", "_").lower()
    return (
        f"{task.benchmark_name}__{task_slug}"
        f"__{condition.injection_stage}"
        f"__{condition.perturbation_type}"
        f"__r{repeat_index}"
    )

