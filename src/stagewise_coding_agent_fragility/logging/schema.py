"""Typed schemas for run logs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenUsage:
    """Token usage metadata for one model call."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ExecutionResultRecord:
    """Normalized execution result for one round."""

    passed: bool
    stdout: str
    stderr: str
    timeout: bool
    runtime_seconds: float
    raw_failure: str
    parsed_failure: dict[str, Any] | None


@dataclass(frozen=True)
class RoundRecord:
    """One recorded loop round."""

    round_index: int
    task_prompt_text: str
    perturbed_task_prompt_text: str | None
    generated_code: str
    execution_result: ExecutionResultRecord
    failure_summary_text: str
    perturbed_failure_summary_text: str | None
    repair_prompt_text: str | None
    model_name: str
    raw_model_response: str
    token_usage: TokenUsage
    latency_seconds: float


@dataclass(frozen=True)
class FinalResultRecord:
    """Terminal summary of one run."""

    success: bool
    num_rounds_executed: int
    first_deviation_step: int | None
    recovered: bool | None
    failure_type: str | None


@dataclass(frozen=True)
class ConditionRecord:
    """Condition metadata written into each run log."""

    condition_id: str
    injection_stage: str
    perturbation_type: str
    perturbation_strength: str
    model_name: str
    repeat_index: int


@dataclass(frozen=True)
class CostRecord:
    """Aggregate token usage for a run."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class TimingRecord:
    """Aggregate timing metadata for a run."""

    wall_clock_seconds: float


@dataclass(frozen=True)
class LoopConfigRecord:
    """Loop metadata written into the log."""

    max_rounds: int


@dataclass(frozen=True)
class RunLog:
    """Top-level JSON-serializable run log schema."""

    run_id: str
    benchmark: str
    task_id: str
    condition: ConditionRecord
    loop_config: LoopConfigRecord
    rounds: list[RoundRecord]
    final_result: FinalResultRecord
    cost: CostRecord
    timing: TimingRecord
