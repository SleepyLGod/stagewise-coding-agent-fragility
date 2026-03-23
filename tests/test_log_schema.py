"""Tests for logging schema construction."""

from __future__ import annotations

from stagewise_coding_agent_fragility.logging.schema import ConditionRecord
from stagewise_coding_agent_fragility.logging.schema import CostRecord
from stagewise_coding_agent_fragility.logging.schema import ExecutionResultRecord
from stagewise_coding_agent_fragility.logging.schema import FinalResultRecord
from stagewise_coding_agent_fragility.logging.schema import LoopConfigRecord
from stagewise_coding_agent_fragility.logging.schema import RoundRecord
from stagewise_coding_agent_fragility.logging.schema import RunLog
from stagewise_coding_agent_fragility.logging.schema import TimingRecord
from stagewise_coding_agent_fragility.logging.schema import TokenUsage


def test_run_log_can_be_constructed() -> None:
    """Constructs the top-level run log schema."""
    token_usage = TokenUsage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    execution_result = ExecutionResultRecord(
        passed=False,
        stdout="",
        stderr="AssertionError",
        timeout=False,
        runtime_seconds=0.25,
        raw_failure="AssertionError",
        parsed_failure=None,
    )
    round_record = RoundRecord(
        round_index=0,
        task_prompt_text="Solve task",
        perturbed_task_prompt_text=None,
        generated_code="def foo(): pass",
        execution_result=execution_result,
        failure_summary_text="AssertionError",
        perturbed_failure_summary_text=None,
        repair_prompt_text=None,
        model_name="deepseek-reasoner",
        raw_model_response="def foo(): pass",
        token_usage=token_usage,
        latency_seconds=0.5,
    )
    run_log = RunLog(
        run_id="run-001",
        benchmark="humanevalplus",
        task_id="HumanEval/1",
        condition=ConditionRecord(
            condition_id="clean",
            injection_stage="none",
            perturbation_type="none",
            perturbation_strength="none",
            model_name="deepseek-reasoner",
            repeat_index=0,
        ),
        loop_config=LoopConfigRecord(max_rounds=3),
        rounds=[round_record],
        final_result=FinalResultRecord(
            success=False,
            num_rounds_executed=1,
            first_deviation_step=None,
            recovered=None,
            failure_type=None,
        ),
        cost=CostRecord(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        ),
        timing=TimingRecord(wall_clock_seconds=0.5),
    )

    assert run_log.benchmark == "humanevalplus"
    assert run_log.rounds[0].generated_code == "def foo(): pass"
