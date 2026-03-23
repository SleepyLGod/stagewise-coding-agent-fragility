"""Aggregate RunLog objects into per-condition metric summaries.

This module is the boundary between raw logs and analysis-ready numbers.
It never writes files — the caller decides what to do with the results.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from stagewise_coding_agent_fragility.experiments.metrics import (
    ConditionMetrics,
    compute_condition_metrics,
)
from stagewise_coding_agent_fragility.logging.reader import load_run_logs
from stagewise_coding_agent_fragility.logging.schema import RunLog


def aggregate_logs(logs: list[RunLog]) -> dict[str, ConditionMetrics]:
    """Group logs by condition and compute metrics for each group.

    Args:
        logs: All run logs to aggregate.  May span multiple conditions.

    Returns:
        Mapping from ``condition_id`` to its ``ConditionMetrics``.

    Raises:
        ValueError: If ``logs`` is empty.
    """
    if not logs:
        raise ValueError("No logs to aggregate.")

    groups = _group_by_condition(logs)
    return {
        condition_id: compute_condition_metrics(condition_id, group_logs)
        for condition_id, group_logs in groups.items()
    }


def aggregate_from_dir(log_dir: str | Path) -> dict[str, ConditionMetrics]:
    """Load all JSON logs from a directory and aggregate them.

    Args:
        log_dir: Directory containing ``*.json`` run log files.

    Returns:
        Mapping from ``condition_id`` to its ``ConditionMetrics``.

    Raises:
        ValueError: If no logs are found or the directory is empty.
    """
    logs = load_run_logs(log_dir)
    if not logs:
        raise ValueError(f"No log files found in {log_dir!r}.")
    return aggregate_logs(logs)


def metrics_to_dict(metrics: ConditionMetrics) -> dict[str, object]:
    """Serialize a ``ConditionMetrics`` to a plain dict for JSON/CSV output.

    Args:
        metrics: The metrics to convert.

    Returns:
        Plain dict with all fields at the top level.
    """
    return dataclasses.asdict(metrics)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _group_by_condition(logs: list[RunLog]) -> dict[str, list[RunLog]]:
    """Group logs by their condition_id.

    Args:
        logs: All run logs.

    Returns:
        Dict mapping condition_id to its associated run logs.
    """
    groups: dict[str, list[RunLog]] = {}
    for log in logs:
        condition_id = log.condition.condition_id
        groups.setdefault(condition_id, []).append(log)
    return groups

