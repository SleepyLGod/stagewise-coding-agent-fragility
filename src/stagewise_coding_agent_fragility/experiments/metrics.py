"""Per-condition metric computation.

All functions are pure: they accept a list of ``RunLog`` objects and return
typed result objects.  No I/O happens here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from stagewise_coding_agent_fragility.logging.schema import RunLog


@dataclass(frozen=True)
class ConditionMetrics:
    """Aggregate metrics for one experiment condition.

    Attributes:
        condition_id: The condition these metrics describe.
        num_runs: Total number of runs included.
        final_pass_rate: Fraction of runs that ended with all tests passing.
        average_repair_rounds: Mean number of loop rounds executed per run.
        average_total_tokens: Mean total token usage per run.
        average_wall_clock_seconds: Mean wall-clock time per run.
        recovery_rate: Among runs whose first round failed, the fraction that
            eventually succeeded.  ``None`` if every run passed on round 0.
        failure_type_distribution: Normalized distribution of ``failure_type``
            labels among failed runs.  Empty dict if all runs succeeded.
    """

    condition_id: str
    num_runs: int
    final_pass_rate: float
    average_repair_rounds: float
    average_total_tokens: float
    average_wall_clock_seconds: float
    recovery_rate: float | None
    failure_type_distribution: dict[str, float] = field(default_factory=dict)


def compute_condition_metrics(
    condition_id: str,
    logs: list[RunLog],
) -> ConditionMetrics:
    """Compute aggregate metrics for a set of runs sharing the same condition.

    Args:
        condition_id: Identifier for the condition being summarized.
        logs: Run logs for this condition.  Must be non-empty.

    Returns:
        Computed ``ConditionMetrics``.

    Raises:
        ValueError: If ``logs`` is empty.
    """
    if not logs:
        raise ValueError(f"No logs provided for condition_id={condition_id!r}.")

    num_runs = len(logs)
    successes = [log for log in logs if log.final_result.success]
    failed = [log for log in logs if not log.final_result.success]

    final_pass_rate = len(successes) / num_runs
    average_repair_rounds = sum(log.final_result.num_rounds_executed for log in logs) / num_runs
    average_total_tokens = sum(log.cost.total_tokens for log in logs) / num_runs
    average_wall_clock_seconds = sum(log.timing.wall_clock_seconds for log in logs) / num_runs

    # Recovery rate: among runs where round 0 failed, fraction that still ended in success.
    first_round_failed = [log for log in logs if not log.rounds[0].execution_result.passed]
    if first_round_failed:
        recovered = sum(1 for log in first_round_failed if log.final_result.success)
        recovery_rate: float | None = recovered / len(first_round_failed)
    else:
        recovery_rate = None

    failure_type_distribution = _compute_failure_type_distribution(failed)

    return ConditionMetrics(
        condition_id=condition_id,
        num_runs=num_runs,
        final_pass_rate=final_pass_rate,
        average_repair_rounds=average_repair_rounds,
        average_total_tokens=average_total_tokens,
        average_wall_clock_seconds=average_wall_clock_seconds,
        recovery_rate=recovery_rate,
        failure_type_distribution=failure_type_distribution,
    )


def _compute_failure_type_distribution(failed_logs: list[RunLog]) -> dict[str, float]:
    """Build a normalized failure type distribution from failed runs.

    Args:
        failed_logs: Only the logs whose final_result.success is False.

    Returns:
        Dict mapping failure_type label to its fraction.  Empty if no failures.
    """
    if not failed_logs:
        return {}

    counts: dict[str, int] = {}
    for log in failed_logs:
        label = log.final_result.failure_type or "unknown"
        counts[label] = counts.get(label, 0) + 1

    total = len(failed_logs)
    return {label: count / total for label, count in sorted(counts.items())}

