"""Tests for CLI helper behavior."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

from stagewise_coding_agent_fragility.cli.log_dir import resolve_log_dir


def test_resolve_log_dir_accepts_directory_with_json_files(tmp_path: Path) -> None:
    """A direct run directory should be accepted unchanged."""
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    (run_dir / "one.json").write_text("{}", encoding="utf-8")

    assert resolve_log_dir(run_dir) == run_dir


def test_resolve_log_dir_requires_explicit_latest_selection(tmp_path: Path) -> None:
    """A parent directory should fail loudly unless --latest is requested."""
    first = tmp_path / "run_a"
    second = tmp_path / "run_b"
    first.mkdir()
    second.mkdir()
    (first / "one.json").write_text("{}", encoding="utf-8")
    (second / "two.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="--latest"):
        resolve_log_dir(tmp_path)


def test_resolve_log_dir_selects_latest_child_when_requested(tmp_path: Path) -> None:
    """--latest should select the newest eligible child directory."""
    first = tmp_path / "run_a"
    second = tmp_path / "run_b"
    first.mkdir()
    (first / "one.json").write_text("{}", encoding="utf-8")
    time.sleep(0.01)
    second.mkdir()
    (second / "two.json").write_text("{}", encoding="utf-8")

    assert resolve_log_dir(tmp_path, latest=True) == second


def test_resolve_log_dir_rejects_latest_without_eligible_children(tmp_path: Path) -> None:
    """--latest should still fail if no child contains run logs."""
    (tmp_path / "empty_child").mkdir()

    with pytest.raises(ValueError, match="No child directories"):
        resolve_log_dir(tmp_path, latest=True)


def test_run_experiment_passes_configured_api_key_env_to_model_clients(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The experiment CLI should pass the configured API-key env name through."""
    from stagewise_coding_agent_fragility.cli import run_experiment as run_experiment_cli
    import stagewise_coding_agent_fragility.benchmarks.humanevalplus as humanevalplus
    import stagewise_coding_agent_fragility.experiments.planner as planner
    import stagewise_coding_agent_fragility.experiments.runner as runner
    import stagewise_coding_agent_fragility.logging.writer as writer
    import stagewise_coding_agent_fragility.models.deepseek as deepseek_module

    experiment_config_path = tmp_path / "experiment.yaml"
    models_config_path = tmp_path / "models.yaml"
    logs_dir = tmp_path / "logs"

    experiment_config_path.write_text(
        """
experiment_name: qwen_cli_regression
description: Verify CLI model construction.
benchmark:
  name: humanevalplus
  dataset_source: local
  task_subset: smoke
  selection_strategy: first_n
  task_limit: 1
loop:
  max_rounds: 1
  use_rule_based_failure_summary: true
repeats: 1
logging:
  output_dir: logs
  save_raw_model_response: false
  save_prompts: false
results:
  output_dir: results
  write_summary_csv: false
  write_markdown_summary: false
execution:
  timeout_seconds: 5
  sandbox_mode: local
  capture_stdout: true
  capture_stderr: true
metrics:
  primary:
    - final_pass_rate
  secondary:
    - average_rounds
conditions:
  - condition_id: task_paraphrase
    injection_stage: task_prompt
    perturbation_type: paraphrase
    perturbation_strength: mild
""".strip(),
        encoding="utf-8",
    )
    models_config_path.write_text(
        """
provider: openai_compatible
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
api_key_env: QWEN_API_KEY
models:
  solver_primary: qwen-turbo
  perturbation_generator: qwen-turbo
  optional_secondary: ""
request_defaults:
  temperature: 0.7
  top_p: 0.95
  max_tokens: 512
  timeout_seconds: 30
perturbation_defaults:
  temperature: 0.7
  top_p: 0.95
  max_tokens: 256
  timeout_seconds: 30
""".strip(),
        encoding="utf-8",
    )

    captured_calls: list[dict[str, str]] = []

    class FakeClient:
        """Minimal model client used to capture constructor arguments."""

        def __init__(
            self,
            model_name: str,
            *,
            base_url: str,
            api_key_env: str,
        ) -> None:
            captured_calls.append(
                {
                    "model_name": model_name,
                    "base_url": base_url,
                    "api_key_env": api_key_env,
                }
            )

    class FakeAdapter:
        """Minimal benchmark adapter for CLI wiring tests."""

        benchmark_name = "humanevalplus"

        def load_tasks(self) -> list[object]:
            """Return no tasks to keep the test focused on construction."""
            return []

        def select_subset(self, task_limit: int) -> list[object]:
            """Return no tasks to keep the test focused on construction."""
            del task_limit
            return []

    def fake_build_run_plans(**_: object) -> list[object]:
        """Return no plans for a zero-work CLI smoke path."""
        return []

    def fake_write_run_log(*_: object, **__: object) -> None:
        """Accept log writes without touching the filesystem."""
        return None

    def fake_run_experiment(**_: object) -> list[object]:
        """Return no logs so the CLI exits successfully."""
        return []

    monkeypatch.setattr(deepseek_module, "DeepSeekClient", FakeClient)
    monkeypatch.setattr(humanevalplus, "HumanEvalPlusAdapter", FakeAdapter)
    monkeypatch.setattr(planner, "build_run_plans", fake_build_run_plans)
    monkeypatch.setattr(writer, "write_run_log", fake_write_run_log)
    monkeypatch.setattr(runner, "run_experiment", fake_run_experiment)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_experiment",
            "--experiment-config",
            str(experiment_config_path),
            "--models-config",
            str(models_config_path),
        ],
    )

    with pytest.raises(SystemExit, match="0"):
        run_experiment_cli.main()

    assert len(captured_calls) == 2
    assert captured_calls[0]["api_key_env"] == "QWEN_API_KEY"
    assert captured_calls[1]["api_key_env"] == "QWEN_API_KEY"
    assert captured_calls[0]["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
