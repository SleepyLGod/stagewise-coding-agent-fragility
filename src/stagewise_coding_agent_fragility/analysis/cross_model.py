"""Cross-model aggregation utilities based on raw JSON logs.

This module intentionally bypasses the typed log reader. Some experiment groups
already emit extra token-usage fields (for example cache-hit metadata), and the
current reader rejects those logs. The cross-model analysis should remain
usable as long as the core JSON structure is preserved.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any

import yaml

_FUNCTION_PATTERN = re.compile(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


@dataclass(frozen=True)
class RunGroupConfig:
    """Configuration for one cross-model run group.

    Attributes:
        group_id: Stable machine-readable identifier.
        display_name: Human-readable label for plots and tables.
        family: High-level family such as ``deepseek`` or ``qwen``.
        parameter_group: Parameter label such as ``balanced`` or ``creative``.
        log_dir: Directory containing raw JSON run logs.
    """

    group_id: str
    display_name: str
    family: str
    parameter_group: str
    log_dir: Path


@dataclass(frozen=True)
class ConditionAggregate:
    """Aggregate metrics for one condition within one group."""

    condition_id: str
    num_runs: int
    final_pass_rate: float
    round0_pass_rate: float
    average_repair_rounds: float
    average_total_tokens: float
    average_wall_clock_seconds: float
    recovery_rate: float | None
    average_first_deviation_step: float | None


@dataclass(frozen=True)
class GroupAggregate:
    """Cross-model summary for one model group."""

    group_id: str
    display_name: str
    family: str
    parameter_group: str
    model_name: str
    log_dir: Path
    contract_drift_rate: float
    conditions: dict[str, ConditionAggregate]


def load_manifest(manifest_path: str | Path) -> list[RunGroupConfig]:
    """Load a YAML manifest describing cross-model run groups.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Parsed run-group configurations.

    Raises:
        ValueError: If the file is malformed.
    """
    path = Path(manifest_path)
    if not path.is_file():
        raise ValueError(f"Manifest file does not exist: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Manifest must contain a top-level mapping.")

    groups = raw.get("groups")
    if not isinstance(groups, list):
        raise ValueError("Manifest must contain a 'groups' list.")

    parsed: list[RunGroupConfig] = []
    for item in groups:
        if not isinstance(item, dict):
            raise ValueError("Each manifest group must be a mapping.")
        parsed.append(
            RunGroupConfig(
                group_id=_require_string(item, "group_id"),
                display_name=_require_string(item, "display_name"),
                family=_require_string(item, "family"),
                parameter_group=_require_string(item, "parameter_group"),
                log_dir=Path(_require_string(item, "log_dir")),
            )
        )
    return parsed


def aggregate_groups(manifest_path: str | Path) -> list[GroupAggregate]:
    """Aggregate every run group defined in a manifest.

    Args:
        manifest_path: Path to the YAML manifest.

    Returns:
        Aggregated cross-model summaries.
    """
    groups = load_manifest(manifest_path)
    return [aggregate_group(group) for group in groups]


def aggregate_group(group: RunGroupConfig) -> GroupAggregate:
    """Aggregate one run group from raw JSON logs.

    Args:
        group: Run-group configuration.

    Returns:
        Fully aggregated metrics for the group.

    Raises:
        ValueError: If the log directory is empty.
    """
    logs = _load_raw_logs(group.log_dir)
    if not logs:
        raise ValueError(f"No JSON logs found in {group.log_dir}")

    model_name = _require_string(logs[0]["condition"], "model_name")
    groups = _group_by_condition(logs)
    baseline = {
        (_require_string(log["task_id"], ""), _require_int(log["condition"], "repeat_index")): log
        for log in groups["clean"]
    }

    condition_metrics = {
        condition_id: _aggregate_condition(condition_id, condition_logs, baseline)
        for condition_id, condition_logs in sorted(groups.items())
    }

    contract_drift_rate = _compute_contract_drift_rate(logs)

    return GroupAggregate(
        group_id=group.group_id,
        display_name=group.display_name,
        family=group.family,
        parameter_group=group.parameter_group,
        model_name=model_name,
        log_dir=group.log_dir,
        contract_drift_rate=contract_drift_rate,
        conditions=condition_metrics,
    )


def build_condition_rows(groups: list[GroupAggregate]) -> list[dict[str, object]]:
    """Flatten cross-model aggregates into table rows.

    Args:
        groups: Aggregated group summaries.

    Returns:
        Flat row dictionaries, one per ``(group, condition)`` pair.
    """
    rows: list[dict[str, object]] = []
    for group in groups:
        for condition_id, metrics in sorted(group.conditions.items()):
            rows.append(
                {
                    "group_id": group.group_id,
                    "display_name": group.display_name,
                    "family": group.family,
                    "parameter_group": group.parameter_group,
                    "model_name": group.model_name,
                    "condition_id": condition_id,
                    "num_runs": metrics.num_runs,
                    "final_pass_rate": round(metrics.final_pass_rate, 4),
                    "round0_pass_rate": round(metrics.round0_pass_rate, 4),
                    "average_repair_rounds": round(metrics.average_repair_rounds, 4),
                    "average_total_tokens": round(metrics.average_total_tokens, 2),
                    "average_wall_clock_seconds": round(
                        metrics.average_wall_clock_seconds,
                        4,
                    ),
                    "recovery_rate": (
                        "N/A"
                        if metrics.recovery_rate is None
                        else round(metrics.recovery_rate, 4)
                    ),
                    "average_first_deviation_step": (
                        "N/A"
                        if metrics.average_first_deviation_step is None
                        else round(metrics.average_first_deviation_step, 2)
                    ),
                    "contract_drift_rate": round(group.contract_drift_rate, 6),
                    "log_dir": str(group.log_dir),
                }
            )
    return rows


def build_group_rows(groups: list[GroupAggregate]) -> list[dict[str, object]]:
    """Build one headline row per group.

    Args:
        groups: Aggregated group summaries.

    Returns:
        Flat row dictionaries summarizing baseline and best/worst conditions.
    """
    rows: list[dict[str, object]] = []
    for group in groups:
        clean = group.conditions["clean"]
        non_clean = {
            condition_id: metrics
            for condition_id, metrics in group.conditions.items()
            if condition_id != "clean"
        }
        best_condition = max(
            non_clean.items(),
            key=lambda item: item[1].final_pass_rate,
        )
        worst_condition = min(
            non_clean.items(),
            key=lambda item: item[1].final_pass_rate,
        )
        rows.append(
            {
                "group_id": group.group_id,
                "display_name": group.display_name,
                "family": group.family,
                "parameter_group": group.parameter_group,
                "model_name": group.model_name,
                "clean_final_pass_rate": round(clean.final_pass_rate, 4),
                "clean_round0_pass_rate": round(clean.round0_pass_rate, 4),
                "clean_average_total_tokens": round(clean.average_total_tokens, 2),
                "best_condition_id": best_condition[0],
                "best_condition_pass_rate": round(best_condition[1].final_pass_rate, 4),
                "worst_condition_id": worst_condition[0],
                "worst_condition_pass_rate": round(
                    worst_condition[1].final_pass_rate,
                    4,
                ),
                "contract_drift_rate": round(group.contract_drift_rate, 6),
                "log_dir": str(group.log_dir),
            }
        )
    return rows


def build_perturbation_failure_matrix(
    manifest_path: str | Path,
    *,
    top_k: int = 20,
) -> tuple[list[str], list[str], list[list[int]]]:
    """Build a task-by-group matrix of perturbation-induced failed runs.

    A perturbation-induced failed run is defined as:

    - the perturbed run fails,
    - the matching clean run for the same ``(task_id, repeat_index)`` succeeds.

    Args:
        manifest_path: Path to the run-group manifest.
        top_k: Number of tasks to keep after sorting by cross-group prevalence.

    Returns:
        A tuple of ``(task_ids, group_labels, matrix)`` where:
        - ``task_ids`` are the selected tasks,
        - ``group_labels`` are display names in manifest order,
        - ``matrix[row][col]`` is the number of perturbation-induced failed runs
          for task ``row`` in group ``col``.
    """
    groups = load_manifest(manifest_path)
    group_labels = [group.display_name for group in groups]
    per_group_task_counts: list[dict[str, int]] = []

    for group in groups:
        logs = _load_raw_logs(group.log_dir)
        grouped = _group_by_condition(logs)
        clean_index = {
            (log["task_id"], log["condition"]["repeat_index"]): log
            for log in grouped["clean"]
        }
        counts: dict[str, int] = defaultdict(int)
        for condition_id, condition_logs in grouped.items():
            if condition_id == "clean":
                continue
            for log in condition_logs:
                key = (log["task_id"], log["condition"]["repeat_index"])
                clean_log = clean_index[key]
                if (not log["final_result"]["success"]) and clean_log["final_result"]["success"]:
                    counts[log["task_id"]] += 1
        per_group_task_counts.append(dict(counts))

    all_tasks = sorted(
        {
            task_id
            for group_counts in per_group_task_counts
            for task_id in group_counts
        }
    )
    ranked_tasks = sorted(
        all_tasks,
        key=lambda task_id: (
            -sum(1 for group_counts in per_group_task_counts if group_counts.get(task_id, 0) > 0),
            -sum(group_counts.get(task_id, 0) for group_counts in per_group_task_counts),
            task_id,
        ),
    )
    selected_tasks = ranked_tasks[:top_k]

    matrix: list[list[int]] = []
    for task_id in selected_tasks:
        row = [group_counts.get(task_id, 0) for group_counts in per_group_task_counts]
        matrix.append(row)
    return selected_tasks, group_labels, matrix


def _aggregate_condition(
    condition_id: str,
    logs: list[dict[str, Any]],
    baseline_logs: dict[tuple[str, int], dict[str, Any]],
) -> ConditionAggregate:
    """Aggregate one condition using raw JSON logs."""
    num_runs = len(logs)
    successes = [log for log in logs if log["final_result"]["success"]]
    final_pass_rate = len(successes) / num_runs

    round0_passes = sum(
        1 for log in logs if log["rounds"][0]["execution_result"]["passed"]
    )
    round0_pass_rate = round0_passes / num_runs

    average_repair_rounds = (
        sum(log["final_result"]["num_rounds_executed"] for log in logs) / num_runs
    )
    average_total_tokens = sum(log["cost"]["total_tokens"] for log in logs) / num_runs
    average_wall_clock_seconds = (
        sum(log["timing"]["wall_clock_seconds"] for log in logs) / num_runs
    )

    first_round_failed = [
        log for log in logs if not log["rounds"][0]["execution_result"]["passed"]
    ]
    recovery_rate: float | None = None
    if first_round_failed:
        recovered = sum(1 for log in first_round_failed if log["final_result"]["success"])
        recovery_rate = recovered / len(first_round_failed)

    average_first_deviation_step: float | None = None
    if condition_id != "clean":
        deviations: list[int] = []
        for log in logs:
            key = (log["task_id"], log["condition"]["repeat_index"])
            baseline = baseline_logs[key]
            deviation = _find_first_deviation_step(log, baseline)
            if deviation is not None:
                deviations.append(deviation)
        if deviations:
            average_first_deviation_step = sum(deviations) / len(deviations)

    return ConditionAggregate(
        condition_id=condition_id,
        num_runs=num_runs,
        final_pass_rate=final_pass_rate,
        round0_pass_rate=round0_pass_rate,
        average_repair_rounds=average_repair_rounds,
        average_total_tokens=average_total_tokens,
        average_wall_clock_seconds=average_wall_clock_seconds,
        recovery_rate=recovery_rate,
        average_first_deviation_step=average_first_deviation_step,
    )


def _find_first_deviation_step(
    log: dict[str, Any],
    baseline: dict[str, Any],
) -> int | None:
    """Find the first observable execution deviation from the clean baseline."""
    start_round = 1 if log["condition"]["injection_stage"] == "failure_summary" else 0
    comparable = min(len(log["rounds"]), len(baseline["rounds"]))

    for round_index in range(start_round, comparable):
        run_result = log["rounds"][round_index]["execution_result"]
        baseline_result = baseline["rounds"][round_index]["execution_result"]
        if run_result["passed"] != baseline_result["passed"]:
            return round_index
        if run_result["timeout"] != baseline_result["timeout"]:
            return round_index
        if run_result["raw_failure"].strip() != baseline_result["raw_failure"].strip():
            return round_index

    if len(log["rounds"]) != len(baseline["rounds"]) and comparable >= start_round:
        return comparable
    return None


def _compute_contract_drift_rate(logs: list[dict[str, Any]]) -> float:
    """Compute task-prompt function-name drift rate for task-side perturbations."""
    total = 0
    changed = 0

    for log in logs:
        condition_id = log["condition"]["condition_id"]
        if not condition_id.startswith("task_"):
            continue

        total += 1
        round_zero = log["rounds"][0]
        original = round_zero.get("task_prompt_text") or ""
        perturbed = round_zero.get("perturbed_task_prompt_text") or ""
        original_name = _extract_function_name(original)
        perturbed_name = _extract_function_name(perturbed)
        if original_name is None or perturbed_name is None:
            continue
        if original_name != perturbed_name:
            changed += 1

    if total == 0:
        return 0.0
    return changed / total


def _extract_function_name(text: str) -> str | None:
    """Extract the first Python function name from prompt text."""
    match = _FUNCTION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1)


def _load_raw_logs(log_dir: Path) -> list[dict[str, Any]]:
    """Load every JSON file in a directory as a raw mapping."""
    if not log_dir.is_dir():
        raise ValueError(f"Log directory does not exist: {log_dir}")
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(log_dir.glob("*.json"))]


def _group_by_condition(logs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group raw logs by condition id."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for log in logs:
        groups[log["condition"]["condition_id"]].append(log)
    return dict(groups)


def _require_string(mapping: dict[str, Any], key: str) -> str:
    """Require a non-empty string field from a mapping."""
    if key:
        value = mapping.get(key)
    else:
        value = mapping
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string for key={key!r}")
    return value


def _require_int(mapping: dict[str, Any], key: str) -> int:
    """Require an integer field from a mapping."""
    value = mapping.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Expected integer for key={key!r}")
    return value
