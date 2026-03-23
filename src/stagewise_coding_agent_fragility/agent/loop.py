"""The main execution-feedback-repair loop.

``run_loop`` orchestrates one full agent run for a single task under a single
experiment condition.  It returns a ``LoopResult`` — the experiment runner is
responsible for assembling the final ``RunLog``.

Perturbation is injected via the optional ``perturb_fn`` callable so that the
loop itself stays decoupled from the perturbation module.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from stagewise_coding_agent_fragility.agent import failure_summary as fs_module
from stagewise_coding_agent_fragility.agent.repairer import repair
from stagewise_coding_agent_fragility.agent.solver import extract_code, solve
from stagewise_coding_agent_fragility.benchmarks.base import Task
from stagewise_coding_agent_fragility.config.schema import ConditionConfig
from stagewise_coding_agent_fragility.execution.execution_result import ExecutionResult
from stagewise_coding_agent_fragility.execution.test_runner import (
    PythonTestRunner,
    PythonTestTask,
)
from stagewise_coding_agent_fragility.logging.schema import (
    ExecutionResultRecord,
    FinalResultRecord,
    RoundRecord,
    TokenUsage,
)
from stagewise_coding_agent_fragility.models.base import ModelClient
from stagewise_coding_agent_fragility.models.response_types import ModelResponse
from stagewise_coding_agent_fragility.prompting.repair_prompt import build_repair_prompt
from stagewise_coding_agent_fragility.prompting.task_prompt import build_task_prompt


@dataclass(frozen=True)
class LoopResult:
    """Result of one complete agent run.

    Attributes:
        rounds: Ordered list of recorded loop rounds.
        final_result: Terminal summary of the run.
    """

    rounds: list[RoundRecord] = field(default_factory=list)
    final_result: FinalResultRecord = field(
        default_factory=lambda: FinalResultRecord(
            success=False,
            num_rounds_executed=0,
            first_deviation_step=None,
            recovered=None,
            failure_type=None,
        )
    )


def run_loop(
    task: Task,
    condition: ConditionConfig,
    solver_model: ModelClient,
    test_runner: PythonTestRunner,
    max_rounds: int,
    execution_timeout_seconds: float,
    model_temperature: float,
    model_max_tokens: int,
    model_timeout_seconds: float,
    use_rule_based_failure_summary: bool,
    perturb_fn: Callable[[str], str] | None = None,
    failure_summary_model: ModelClient | None = None,
) -> LoopResult:
    """Run the execution-feedback-repair loop for one task under one condition.

    Args:
        task: The benchmark task to solve.
        condition: The experiment condition (controls perturbation injection).
        solver_model: Model client used for solve and repair calls.
        test_runner: Runner used to execute candidate code against tests.
        max_rounds: Total number of rounds (including the initial solve).
        execution_timeout_seconds: Timeout for each test execution.
        model_temperature: Sampling temperature for all model calls.
        model_max_tokens: Max tokens for all model calls.
        model_timeout_seconds: HTTP timeout for all model calls.
        use_rule_based_failure_summary: If True, use rule-based failure summarization.
            If False, ``failure_summary_model`` must be provided.
        perturb_fn: Optional callable ``(text) -> perturbed_text``.  Applied to
            the task prompt (if ``condition.injection_stage == "task_prompt"``) or
            to each failure summary (if ``condition.injection_stage == "failure_summary"``).
        failure_summary_model: Model client for model-based failure summarization.
            Required when ``use_rule_based_failure_summary`` is False.

    Returns:
        A ``LoopResult`` containing the round records and final result.

    Raises:
        ValueError: If model-based failure summarization is requested but
            ``failure_summary_model`` is not provided.
    """
    if not use_rule_based_failure_summary and failure_summary_model is None:
        raise ValueError(
            "failure_summary_model must be provided when use_rule_based_failure_summary is False."
        )

    base_task_prompt = build_task_prompt(task)
    should_perturb_task = condition.injection_stage == "task_prompt" and perturb_fn is not None
    should_perturb_summary = condition.injection_stage == "failure_summary" and perturb_fn is not None

    perturbed_task_prompt: str | None = perturb_fn(base_task_prompt) if should_perturb_task else None
    effective_task_prompt = perturbed_task_prompt if perturbed_task_prompt is not None else base_task_prompt

    python_task = PythonTestTask(task_id=task.task_id, test_code=task.test_code)
    rounds: list[RoundRecord] = []
    current_code = ""
    current_failure_summary = ""

    for round_index in range(max_rounds):
        if round_index == 0:
            model_response = solve(
                effective_task_prompt,
                solver_model,
                temperature=model_temperature,
                max_tokens=model_max_tokens,
                timeout_seconds=model_timeout_seconds,
            )
            repair_prompt_text: str | None = None
        else:
            perturbed_summary: str | None = perturb_fn(current_failure_summary) if should_perturb_summary else None
            effective_summary = perturbed_summary if perturbed_summary is not None else current_failure_summary
            repair_prompt_text = build_repair_prompt(
                task_prompt=effective_task_prompt,
                candidate_code=current_code,
                failure_summary=effective_summary,
            )
            model_response = repair(
                repair_prompt_text,
                solver_model,
                temperature=model_temperature,
                max_tokens=model_max_tokens,
                timeout_seconds=model_timeout_seconds,
            )

        current_code = extract_code(model_response.response_text)
        exec_result = test_runner.run(python_task, current_code, execution_timeout_seconds)
        failure_summary_text, perturbed_failure_summary_text = _build_summaries(
            current_code=current_code,
            exec_result=exec_result,
            use_rule_based=use_rule_based_failure_summary,
            failure_summary_model=failure_summary_model,
            model_temperature=model_temperature,
            model_max_tokens=model_max_tokens,
            model_timeout_seconds=model_timeout_seconds,
            should_perturb_summary=should_perturb_summary,
            perturb_fn=perturb_fn,
        )
        current_failure_summary = failure_summary_text

        round_record = _build_round_record(
            round_index=round_index,
            base_task_prompt=base_task_prompt,
            perturbed_task_prompt=perturbed_task_prompt,
            repair_prompt_text=repair_prompt_text,
            generated_code=current_code,
            exec_result=exec_result,
            failure_summary_text=failure_summary_text,
            perturbed_failure_summary_text=perturbed_failure_summary_text,
            model_response=model_response,
        )
        rounds.append(round_record)

        if exec_result.passed:
            break

    final_result = _compute_final_result(rounds, max_rounds)
    return LoopResult(rounds=rounds, final_result=final_result)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_summaries(
    current_code: str,
    exec_result: ExecutionResult,
    use_rule_based: bool,
    failure_summary_model: ModelClient | None,
    model_temperature: float,
    model_max_tokens: int,
    model_timeout_seconds: float,
    should_perturb_summary: bool,
    perturb_fn: Callable[[str], str] | None,
) -> tuple[str, str | None]:
    """Build the base and optionally perturbed failure summary for one round.

    Returns:
        A tuple of ``(base_summary, perturbed_summary_or_none)``.
    """
    if exec_result.passed:
        base_summary = "All tests passed."
    elif use_rule_based:
        base_summary = fs_module.summarize_failure_rule_based(exec_result)
    else:
        assert failure_summary_model is not None  # guaranteed by run_loop pre-check
        base_summary, _ = fs_module.summarize_failure_with_model(
            candidate_code=current_code,
            result=exec_result,
            model=failure_summary_model,
            temperature=model_temperature,
            max_tokens=model_max_tokens,
            timeout_seconds=model_timeout_seconds,
        )

    perturbed: str | None = None
    if should_perturb_summary and perturb_fn is not None and not exec_result.passed:
        perturbed = perturb_fn(base_summary)

    return base_summary, perturbed


def _build_round_record(
    round_index: int,
    base_task_prompt: str,
    perturbed_task_prompt: str | None,
    repair_prompt_text: str | None,
    generated_code: str,
    exec_result: ExecutionResult,
    failure_summary_text: str,
    perturbed_failure_summary_text: str | None,
    model_response: ModelResponse,
) -> RoundRecord:
    """Assemble a ``RoundRecord`` from one loop iteration's data."""
    exec_record = ExecutionResultRecord(
        passed=exec_result.passed,
        stdout=exec_result.stdout,
        stderr=exec_result.stderr,
        timeout=exec_result.timeout,
        runtime_seconds=exec_result.runtime_seconds,
        raw_failure=exec_result.raw_failure,
        parsed_failure=exec_result.parsed_failure,
    )
    return RoundRecord(
        round_index=round_index,
        task_prompt_text=base_task_prompt,
        perturbed_task_prompt_text=perturbed_task_prompt,
        generated_code=generated_code,
        execution_result=exec_record,
        failure_summary_text=failure_summary_text,
        perturbed_failure_summary_text=perturbed_failure_summary_text,
        repair_prompt_text=repair_prompt_text,
        model_name=model_response.model_name,
        raw_model_response=model_response.response_text,
        token_usage=TokenUsage(
            prompt_tokens=model_response.token_usage.prompt_tokens,
            completion_tokens=model_response.token_usage.completion_tokens,
            total_tokens=model_response.token_usage.total_tokens,
        ),
        latency_seconds=model_response.latency_seconds,
    )


def _compute_final_result(rounds: list[RoundRecord], max_rounds: int) -> FinalResultRecord:
    """Derive the ``FinalResultRecord`` from the completed rounds.

    Args:
        rounds: The list of executed round records.
        max_rounds: The configured round limit.

    Returns:
        A ``FinalResultRecord`` summarizing the run outcome.
    """
    if not rounds:
        return FinalResultRecord(
            success=False,
            num_rounds_executed=0,
            first_deviation_step=None,
            recovered=None,
            failure_type="unknown",
        )

    last_round = rounds[-1]
    success = last_round.execution_result.passed
    failure_type: str | None = None
    if not success:
        failure_type = "stuck_loop" if len(rounds) >= max_rounds else "wrong_fix"

    return FinalResultRecord(
        success=success,
        num_rounds_executed=len(rounds),
        first_deviation_step=None,  # computed by the analysis layer vs. clean reference
        recovered=None,             # computed by the analysis layer vs. clean reference
        failure_type=failure_type,
    )

