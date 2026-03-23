"""Load RunLog objects from JSON files on disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stagewise_coding_agent_fragility.logging.schema import (
    ConditionRecord,
    CostRecord,
    ExecutionResultRecord,
    FinalResultRecord,
    LoopConfigRecord,
    RoundRecord,
    RunLog,
    TimingRecord,
    TokenUsage,
)


def load_run_log(log_path: str | Path) -> RunLog:
    """Load a single RunLog from a JSON file.

    Args:
        log_path: Path to the JSON file produced by ``write_run_log``.

    Returns:
        Reconstructed ``RunLog``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON is malformed or missing required fields.
    """
    path = Path(log_path)
    with path.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = json.load(fh)
    return _parse_run_log(raw)


def load_run_logs(log_dir: str | Path) -> list[RunLog]:
    """Load all RunLog JSON files from a directory.

    Files that fail to parse are re-raised immediately — fail loud.

    Args:
        log_dir: Directory to scan for ``*.json`` files.

    Returns:
        List of reconstructed ``RunLog`` objects, sorted by filename.
    """
    directory = Path(log_dir)
    paths = sorted(directory.glob("*.json"))
    return [load_run_log(p) for p in paths]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_run_log(raw: dict[str, Any]) -> RunLog:
    return RunLog(
        run_id=raw["run_id"],
        benchmark=raw["benchmark"],
        task_id=raw["task_id"],
        condition=_parse_condition(raw["condition"]),
        loop_config=LoopConfigRecord(max_rounds=raw["loop_config"]["max_rounds"]),
        rounds=[_parse_round(r) for r in raw["rounds"]],
        final_result=_parse_final_result(raw["final_result"]),
        cost=CostRecord(**raw["cost"]),
        timing=TimingRecord(**raw["timing"]),
    )


def _parse_condition(raw: dict[str, Any]) -> ConditionRecord:
    return ConditionRecord(
        condition_id=raw["condition_id"],
        injection_stage=raw["injection_stage"],
        perturbation_type=raw["perturbation_type"],
        perturbation_strength=raw["perturbation_strength"],
        model_name=raw["model_name"],
        repeat_index=raw["repeat_index"],
    )


def _parse_round(raw: dict[str, Any]) -> RoundRecord:
    exec_raw = raw["execution_result"]
    exec_record = ExecutionResultRecord(
        passed=exec_raw["passed"],
        stdout=exec_raw["stdout"],
        stderr=exec_raw["stderr"],
        timeout=exec_raw["timeout"],
        runtime_seconds=exec_raw["runtime_seconds"],
        raw_failure=exec_raw["raw_failure"],
        parsed_failure=exec_raw.get("parsed_failure"),
    )
    return RoundRecord(
        round_index=raw["round_index"],
        task_prompt_text=raw["task_prompt_text"],
        perturbed_task_prompt_text=raw.get("perturbed_task_prompt_text"),
        generated_code=raw["generated_code"],
        execution_result=exec_record,
        failure_summary_text=raw["failure_summary_text"],
        perturbed_failure_summary_text=raw.get("perturbed_failure_summary_text"),
        repair_prompt_text=raw.get("repair_prompt_text"),
        model_name=raw["model_name"],
        raw_model_response=raw["raw_model_response"],
        token_usage=TokenUsage(**raw["token_usage"]),
        latency_seconds=raw["latency_seconds"],
    )


def _parse_final_result(raw: dict[str, Any]) -> FinalResultRecord:
    return FinalResultRecord(
        success=raw["success"],
        num_rounds_executed=raw["num_rounds_executed"],
        first_deviation_step=raw.get("first_deviation_step"),
        recovered=raw.get("recovered"),
        failure_type=raw.get("failure_type"),
    )

