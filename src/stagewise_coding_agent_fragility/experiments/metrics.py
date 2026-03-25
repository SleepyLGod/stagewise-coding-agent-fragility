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
        pass_rate_by_round: Cumulative pass rate at each round index (0-indexed).
        average_first_deviation_step: Average round index where a perturbed run's
            observable execution trajectory diverged from the control run after
            the injection point.
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
    pass_rate_by_round: dict[int, float]
    average_first_deviation_step: float | None = None
    failure_type_distribution: dict[str, float] = field(default_factory=dict)


def compute_condition_metrics(
    condition_id: str,
    logs: list[RunLog],
    baseline_logs: dict[tuple[str, int], RunLog] | None = None,
) -> ConditionMetrics:
    """Compute aggregate metrics for a set of runs sharing the same condition.

    Args:
        condition_id: Identifier for the condition being summarized.
        logs: Run logs for this condition.  Must be non-empty.
        baseline_logs: Optional dictionary mapping ``(task_id, repeat_index)`` to
            the control run log. Used to compute cross-run metrics like deviation.

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

    first_deviations: list[int] = []
    if baseline_logs is not None:
        for log in logs:
            key = (log.task_id, log.condition.repeat_index)
            baseline_log = baseline_logs.get(key)
            if baseline_log is not None:
                dev_step = _find_first_deviation_step(log, baseline_log)
                if dev_step is not None:
                    first_deviations.append(dev_step)

    average_first_deviation_step: float | None = None
    if first_deviations:
        average_first_deviation_step = sum(first_deviations) / len(first_deviations)

    max_rounds = max((len(log.rounds) for log in logs), default=0)
    pass_rate_by_round: dict[int, float] = {}
    for r in range(max_rounds):
        passed_at_r = sum(
            1 for log in logs
            if log.final_result.success and log.final_result.num_rounds_executed <= r + 1
        )
        pass_rate_by_round[r] = passed_at_r / num_runs

    return ConditionMetrics(
        condition_id=condition_id,
        num_runs=num_runs,
        final_pass_rate=final_pass_rate,
        average_repair_rounds=average_repair_rounds,
        average_total_tokens=average_total_tokens,
        average_wall_clock_seconds=average_wall_clock_seconds,
        recovery_rate=recovery_rate,
        pass_rate_by_round=pass_rate_by_round,
        average_first_deviation_step=average_first_deviation_step,
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


def _find_first_deviation_step(log: RunLog, baseline_log: RunLog) -> int | None:
    """Find the first round index where the execution trajectory diverges.

    This metric intentionally ignores raw code-text differences, because prompt
    perturbations naturally change code surface form. Instead it compares the
    observable execution trajectory: pass/fail state, timeout state, and raw
    failure evidence. For ``failure_summary`` injection, round 0 is skipped
    because the perturbation only begins affecting behavior on the first repair
    round.

    Args:
        log: The run log to evaluate.
        baseline_log: The control run log for the exact same task and repeat index.

    Returns:
        The round index of the first observable divergence, or None if they are
        identical from the first affected round onward.
    """
    start_round = 1 if log.condition.injection_stage == "failure_summary" else 0
    comparable_rounds = min(len(log.rounds), len(baseline_log.rounds))

    for round_index in range(start_round, comparable_rounds):
        if _execution_trajectory_differs(log, baseline_log, round_index):
            return round_index

    if len(log.rounds) != len(baseline_log.rounds) and comparable_rounds >= start_round:
        return comparable_rounds

    return None


def _execution_trajectory_differs(
    log: RunLog,
    baseline_log: RunLog,
    round_index: int,
) -> bool:
    """Return whether one round shows a different observable test outcome."""
    run_round = log.rounds[round_index]
    baseline_round = baseline_log.rounds[round_index]
    run_result = run_round.execution_result
    baseline_result = baseline_round.execution_result

    if run_result.passed != baseline_result.passed:
        return True
    if run_result.timeout != baseline_result.timeout:
        return True
    return run_result.raw_failure.strip() != baseline_result.raw_failure.strip()

