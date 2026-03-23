"""Tests for the experiments layer: planner, metrics, aggregation, and the
logging writer/reader round-trip."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from stagewise_coding_agent_fragility.benchmarks.base import Task
from stagewise_coding_agent_fragility.config.schema import ConditionConfig
from stagewise_coding_agent_fragility.experiments.aggregation import (
    aggregate_from_dir,
    aggregate_logs,
    metrics_to_dict,
)
from stagewise_coding_agent_fragility.experiments.metrics import (
    ConditionMetrics,
    compute_condition_metrics,
)
from stagewise_coding_agent_fragility.experiments.planner import (
    RunPlan,
    build_run_plans,
)
from stagewise_coding_agent_fragility.logging.reader import load_run_log, load_run_logs
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
from stagewise_coding_agent_fragility.logging.writer import write_run_log

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_TASK = Task(
    task_id="HumanEval/0",
    benchmark_name="humanevalplus",
    prompt="def add(a, b): ...",
    entry_point="add",
    test_code="assert add(1,2)==3",
)

_CLEAN_CONDITION = ConditionConfig(
    condition_id="clean",
    injection_stage="none",
    perturbation_type="none",
    perturbation_strength="none",
)

_PERTURB_CONDITION = ConditionConfig(
    condition_id="paraphrase",
    injection_stage="task_prompt",
    perturbation_type="semantic_paraphrase",
    perturbation_strength="default",
)


def _make_run_log(
    run_id: str = "test_run",
    condition_id: str = "clean",
    success: bool = True,
    num_rounds: int = 1,
    failure_type: str | None = None,
    total_tokens: int = 30,
    wall_seconds: float = 1.0,
) -> RunLog:
    exec_record = ExecutionResultRecord(
        passed=success,
        stdout="",
        stderr="",
        timeout=False,
        runtime_seconds=0.1,
        raw_failure="" if success else "AssertionError",
        parsed_failure=None,
    )
    round_record = RoundRecord(
        round_index=0,
        task_prompt_text="prompt",
        perturbed_task_prompt_text=None,
        generated_code="def add(a,b): return a+b",
        execution_result=exec_record,
        failure_summary_text="All tests passed." if success else "AssertionError",
        perturbed_failure_summary_text=None,
        repair_prompt_text=None,
        model_name="deepseek-reasoner",
        raw_model_response="```python\ndef add(a,b): return a+b\n```",
        token_usage=TokenUsage(
            prompt_tokens=10, completion_tokens=20, total_tokens=total_tokens
        ),
        latency_seconds=0.5,
    )
    return RunLog(
        run_id=run_id,
        benchmark="humanevalplus",
        task_id="HumanEval/0",
        condition=ConditionRecord(
            condition_id=condition_id,
            injection_stage="none",
            perturbation_type="none",
            perturbation_strength="none",
            model_name="deepseek-reasoner",
            repeat_index=0,
        ),
        loop_config=LoopConfigRecord(max_rounds=3),
        rounds=[round_record] * num_rounds,
        final_result=FinalResultRecord(
            success=success,
            num_rounds_executed=num_rounds,
            first_deviation_step=None,
            recovered=None,
            failure_type=failure_type,
        ),
        cost=CostRecord(
            prompt_tokens=10 * num_rounds,
            completion_tokens=20 * num_rounds,
            total_tokens=total_tokens * num_rounds,
        ),
        timing=TimingRecord(wall_clock_seconds=wall_seconds),
    )


# ---------------------------------------------------------------------------
# logging writer / reader round-trip
# ---------------------------------------------------------------------------


def test_write_and_read_run_log_roundtrip() -> None:
    """Writing then reading a RunLog produces an identical object."""
    log = _make_run_log()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_run_log(log, tmpdir)
        assert path.exists()
        loaded = load_run_log(path)
    assert loaded == log


def test_write_creates_output_directory() -> None:
    """write_run_log creates the output directory if absent."""
    log = _make_run_log()
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "a" / "b" / "c"
        write_run_log(log, nested)
        assert nested.is_dir()


def test_write_filename_matches_run_id() -> None:
    """The written filename is {run_id}.json."""
    log = _make_run_log(run_id="my_run_001")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_run_log(log, tmpdir)
        assert path.name == "my_run_001.json"


def test_load_run_logs_returns_all_files() -> None:
    """load_run_logs returns one RunLog per JSON file in the directory."""
    logs = [_make_run_log(run_id=f"run_{i}") for i in range(3)]
    with tempfile.TemporaryDirectory() as tmpdir:
        for log in logs:
            write_run_log(log, tmpdir)
        loaded = load_run_logs(tmpdir)
    assert len(loaded) == 3


def test_load_run_logs_empty_directory() -> None:
    """load_run_logs returns an empty list for a directory with no JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assert load_run_logs(tmpdir) == []


# ---------------------------------------------------------------------------
# planner
# ---------------------------------------------------------------------------


def test_build_run_plans_cartesian_product() -> None:
    """build_run_plans produces tasks × conditions × repeats plans."""
    tasks = [_TASK]
    conditions = [_CLEAN_CONDITION, _PERTURB_CONDITION]
    plans = build_run_plans(tasks, conditions, repeats=2)
    assert len(plans) == 1 * 2 * 2  # 1 task × 2 conditions × 2 repeats


def test_build_run_plans_run_id_format() -> None:
    """run_id encodes benchmark, task, injection_stage, and perturbation type."""
    plans = build_run_plans([_TASK], [_CLEAN_CONDITION], repeats=1)
    assert "humanevalplus" in plans[0].run_id
    assert "r0" in plans[0].run_id


def test_build_run_plans_repeat_index() -> None:
    """RunPlan.repeat_index increments correctly within a condition."""
    plans = build_run_plans([_TASK], [_CLEAN_CONDITION], repeats=3)
    assert [p.repeat_index for p in plans] == [0, 1, 2]


def test_build_run_plans_unique_run_ids() -> None:
    """All run_ids are unique."""
    tasks = [_TASK]
    plans = build_run_plans(tasks, [_CLEAN_CONDITION, _PERTURB_CONDITION], repeats=2)
    ids = [p.run_id for p in plans]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------


def test_compute_condition_metrics_all_pass() -> None:
    """All-passing logs yield final_pass_rate == 1.0 and recovery_rate == None."""
    logs = [_make_run_log(success=True) for _ in range(4)]
    m = compute_condition_metrics("clean", logs)
    assert m.final_pass_rate == 1.0
    assert m.recovery_rate is None
    assert m.failure_type_distribution == {}


def test_compute_condition_metrics_all_fail() -> None:
    """All-failing logs yield final_pass_rate == 0.0 and a non-empty failure dist."""
    logs = [
        _make_run_log(success=False, failure_type="stuck_loop"),
        _make_run_log(success=False, failure_type="wrong_fix"),
        _make_run_log(success=False, failure_type="stuck_loop"),
    ]
    m = compute_condition_metrics("clean", logs)
    assert m.final_pass_rate == 0.0
    assert abs(m.failure_type_distribution["stuck_loop"] - 2 / 3) < 1e-9
    assert abs(m.failure_type_distribution["wrong_fix"] - 1 / 3) < 1e-9


def test_compute_condition_metrics_empty_raises() -> None:
    """compute_condition_metrics raises ValueError on an empty log list."""
    with pytest.raises(ValueError, match="No logs"):
        compute_condition_metrics("clean", [])


def test_compute_condition_metrics_averages() -> None:
    """Average token and timing fields are computed correctly."""
    logs = [
        _make_run_log(total_tokens=10, wall_seconds=1.0),
        _make_run_log(total_tokens=20, wall_seconds=3.0),
    ]
    m = compute_condition_metrics("clean", logs)
    # total_tokens is multiplied by num_rounds (1) in _make_run_log
    assert m.average_total_tokens == 15.0
    assert m.average_wall_clock_seconds == 2.0


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


def test_aggregate_logs_groups_by_condition() -> None:
    """aggregate_logs returns one ConditionMetrics per unique condition_id."""
    logs = [
        _make_run_log(run_id="a", condition_id="clean"),
        _make_run_log(run_id="b", condition_id="clean"),
        _make_run_log(run_id="c", condition_id="paraphrase"),
    ]
    result = aggregate_logs(logs)
    assert set(result.keys()) == {"clean", "paraphrase"}
    assert result["clean"].num_runs == 2
    assert result["paraphrase"].num_runs == 1


def test_aggregate_logs_empty_raises() -> None:
    """aggregate_logs raises ValueError on empty input."""
    with pytest.raises(ValueError, match="No logs"):
        aggregate_logs([])


def test_aggregate_from_dir() -> None:
    """aggregate_from_dir loads and aggregates JSON files from a directory."""
    logs = [_make_run_log(run_id=f"run_{i}", condition_id="clean") for i in range(2)]
    with tempfile.TemporaryDirectory() as tmpdir:
        for log in logs:
            write_run_log(log, tmpdir)
        result = aggregate_from_dir(tmpdir)
    assert "clean" in result
    assert result["clean"].num_runs == 2


def test_aggregate_from_dir_empty_raises() -> None:
    """aggregate_from_dir raises ValueError when no logs are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="No log files"):
            aggregate_from_dir(tmpdir)


def test_metrics_to_dict_is_serializable() -> None:
    """metrics_to_dict returns a plain dict with no dataclass instances."""
    m = compute_condition_metrics("clean", [_make_run_log()])
    d = metrics_to_dict(m)
    assert isinstance(d, dict)
    assert d["condition_id"] == "clean"
    assert isinstance(d["final_pass_rate"], float)

