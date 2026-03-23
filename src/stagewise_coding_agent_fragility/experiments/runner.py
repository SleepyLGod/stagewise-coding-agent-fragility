"""Experiment runner: iterate over run plans and produce RunLog objects.

Each ``RunPlan`` is executed by calling ``run_loop``, then the result is
assembled into a ``RunLog`` and handed to the caller-supplied ``log_writer``.

The runner is stateless — all state lives in the returned ``RunLog`` objects
and whatever the ``log_writer`` persists to disk.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from stagewise_coding_agent_fragility.agent.loop import run_loop
from stagewise_coding_agent_fragility.config.schema import (
    ConditionConfig,
    ExecutionConfig,
    LoopConfig,
    ModelRequestDefaults,
)
from stagewise_coding_agent_fragility.execution.test_runner import PythonTestRunner
from stagewise_coding_agent_fragility.experiments.planner import RunPlan
from stagewise_coding_agent_fragility.logging.schema import (
    ConditionRecord,
    CostRecord,
    LoopConfigRecord,
    RoundRecord,
    RunLog,
    TimingRecord,
)
from stagewise_coding_agent_fragility.models.base import ModelClient
from stagewise_coding_agent_fragility.prompting.perturbation_prompt import (
    build_perturbation_prompt,
)


def run_experiment(
    plans: list[RunPlan],
    solver_model: ModelClient,
    perturber_model: ModelClient | None,
    test_runner: PythonTestRunner,
    loop_config: LoopConfig,
    execution_config: ExecutionConfig,
    solver_defaults: ModelRequestDefaults,
    perturbation_defaults: ModelRequestDefaults,
    solver_model_name: str,
    log_writer: Callable[[RunLog], None],
) -> list[RunLog]:
    """Execute all run plans and return the produced run logs.

    Args:
        plans: Ordered list of run plans from ``build_run_plans``.
        solver_model: Model client used for solve and repair calls.
        perturber_model: Model client used to generate perturbations.
            Required for any plan whose condition has a non-none injection stage.
        test_runner: Runner that executes candidate code against tests.
        loop_config: Loop behaviour settings (max_rounds, failure summary mode).
        execution_config: Code execution settings (timeout, sandbox).
        solver_defaults: Request defaults (temperature, max_tokens, timeout) for
            the solver model.
        perturbation_defaults: Request defaults for the perturber model.
        solver_model_name: Human-readable model name stored in condition records.
        log_writer: Callable that persists each ``RunLog``; called once per plan.

    Returns:
        List of ``RunLog`` objects, one per plan, in plan order.
    """
    logs: list[RunLog] = []
    for plan in plans:
        perturb_fn = _build_perturb_fn(
            condition=plan.condition,
            perturber_model=perturber_model,
            perturbation_defaults=perturbation_defaults,
        )

        wall_start = time.monotonic()
        loop_result = run_loop(
            task=plan.task,
            condition=plan.condition,
            solver_model=solver_model,
            test_runner=test_runner,
            max_rounds=loop_config.max_rounds,
            execution_timeout_seconds=float(execution_config.timeout_seconds),
            model_temperature=solver_defaults.temperature,
            model_max_tokens=solver_defaults.max_tokens,
            model_timeout_seconds=float(solver_defaults.timeout_seconds),
            use_rule_based_failure_summary=loop_config.use_rule_based_failure_summary,
            perturb_fn=perturb_fn,
        )
        wall_seconds = time.monotonic() - wall_start

        run_log = _assemble_run_log(
            plan=plan,
            rounds=loop_result.rounds,
            loop_result_final=loop_result.final_result,
            loop_config=loop_config,
            solver_model_name=solver_model_name,
            wall_seconds=wall_seconds,
        )
        log_writer(run_log)
        logs.append(run_log)

    return logs


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_perturb_fn(
    condition: ConditionConfig,
    perturber_model: ModelClient | None,
    perturbation_defaults: ModelRequestDefaults,
) -> Callable[[str], str] | None:
    """Build a perturbation callable for the given condition.

    Returns ``None`` when ``condition.injection_stage == "none"``.

    Args:
        condition: The experiment condition.
        perturber_model: The model client to call for perturbation.
        perturbation_defaults: Request parameters for the perturber model.

    Returns:
        A ``(text) -> perturbed_text`` callable, or ``None``.

    Raises:
        ValueError: If injection_stage is not none but perturber_model is absent.
    """
    if condition.injection_stage == "none":
        return None

    if perturber_model is None:
        raise ValueError(
            f"perturber_model is required for injection_stage={condition.injection_stage!r} "
            f"(condition_id={condition.condition_id!r})."
        )

    perturbation_type = condition.perturbation_type

    def _perturb(text: str) -> str:
        prompt = build_perturbation_prompt(text, perturbation_type)
        response = perturber_model.complete(
            prompt,
            temperature=perturbation_defaults.temperature,
            max_tokens=perturbation_defaults.max_tokens,
            timeout_seconds=float(perturbation_defaults.timeout_seconds),
        )
        return response.response_text.strip()

    return _perturb


def _assemble_run_log(
    plan: RunPlan,
    rounds: list[RoundRecord],
    loop_result_final: object,
    loop_config: LoopConfig,
    solver_model_name: str,
    wall_seconds: float,
) -> RunLog:
    """Assemble a ``RunLog`` from the completed loop results."""
    total_prompt = sum(r.token_usage.prompt_tokens for r in rounds)
    total_completion = sum(r.token_usage.completion_tokens for r in rounds)
    total_tokens = sum(r.token_usage.total_tokens for r in rounds)

    return RunLog(
        run_id=plan.run_id,
        benchmark=plan.task.benchmark_name,
        task_id=plan.task.task_id,
        condition=ConditionRecord(
            condition_id=plan.condition.condition_id,
            injection_stage=plan.condition.injection_stage,
            perturbation_type=plan.condition.perturbation_type,
            perturbation_strength=plan.condition.perturbation_strength,
            model_name=solver_model_name,
            repeat_index=plan.repeat_index,
        ),
        loop_config=LoopConfigRecord(max_rounds=loop_config.max_rounds),
        rounds=rounds,
        final_result=loop_result_final,
        cost=CostRecord(
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            total_tokens=total_tokens,
        ),
        timing=TimingRecord(wall_clock_seconds=wall_seconds),
    )

