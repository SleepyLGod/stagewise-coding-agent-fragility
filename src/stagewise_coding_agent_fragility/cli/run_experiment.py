"""CLI entry point for running a full experiment.

Usage::

    uv run python -m stagewise_coding_agent_fragility.cli.run_experiment \
        --experiment-config configs/humanevalplus.yaml \
        --models-config configs/models.yaml
"""

from __future__ import annotations

import argparse
import sys
from functools import partial
from pathlib import Path

from dotenv import load_dotenv


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run a stage-wise fragility experiment.",
    )
    parser.add_argument(
        "--experiment-config",
        default="configs/humanevalplus.yaml",
        help="Path to the experiment YAML config.",
    )
    parser.add_argument(
        "--models-config",
        default="configs/models.yaml",
        help="Path to the models YAML config.",
    )
    return parser


def main() -> None:
    """Run the experiment."""
    # Load .env early so API keys are available.
    load_dotenv()

    parser = build_argument_parser()
    args = parser.parse_args()

    # ---- Config ----
    from stagewise_coding_agent_fragility.config.loader import (
        load_experiment_config,
        load_models_config,
    )

    experiment_config = load_experiment_config(Path(args.experiment_config))
    models_config = load_models_config(Path(args.models_config))

    # ---- Model clients ----
    from stagewise_coding_agent_fragility.models.deepseek import DeepSeekClient

    solver_model = DeepSeekClient(
        models_config.models.solver_primary,
        base_url=models_config.base_url,
    )

    # Only create the perturber client if at least one condition needs it.
    needs_perturber = any(
        c.injection_stage != "none" for c in experiment_config.conditions
    )
    perturber_model: DeepSeekClient | None = None
    if needs_perturber and models_config.models.perturbation_generator:
        perturber_model = DeepSeekClient(
            models_config.models.perturbation_generator,
            base_url=models_config.base_url,
        )

    # ---- Benchmark tasks ----
    from stagewise_coding_agent_fragility.benchmarks.humanevalplus import (
        HumanEvalPlusAdapter,
    )

    adapter = HumanEvalPlusAdapter()
    tasks = adapter.select_subset(task_limit=experiment_config.benchmark.task_limit)
    total_available = len(adapter.load_tasks())

    print(
        f"Loaded {len(tasks)} tasks from {adapter.benchmark_name} "
        f"(total available: {total_available}).",
    )

    # ---- Run plans ----
    from stagewise_coding_agent_fragility.experiments.planner import build_run_plans

    plans = build_run_plans(
        tasks=tasks,
        conditions=experiment_config.conditions,
        repeats=experiment_config.repeats,
    )
    print(
        f"Built {len(plans)} run plans "
        f"({len(tasks)} tasks × {len(experiment_config.conditions)} conditions × "
        f"{experiment_config.repeats} repeats).",
    )

    # ---- Log writer ----
    from stagewise_coding_agent_fragility.logging.writer import write_run_log

    log_dir = experiment_config.logging.output_dir
    log_writer = partial(write_run_log, output_dir=log_dir)

    # ---- Execution ----
    from stagewise_coding_agent_fragility.execution.test_runner import PythonTestRunner
    from stagewise_coding_agent_fragility.experiments.runner import run_experiment

    test_runner = PythonTestRunner()

    print(f"Starting experiment: {experiment_config.experiment_name}")
    print(f"Logs will be written to: {log_dir}/")
    print("-" * 60)

    logs = run_experiment(
        plans=plans,
        solver_model=solver_model,
        perturber_model=perturber_model,
        test_runner=test_runner,
        loop_config=experiment_config.loop,
        execution_config=experiment_config.execution,
        solver_defaults=models_config.request_defaults,
        perturbation_defaults=models_config.perturbation_defaults,
        solver_model_name=models_config.models.solver_primary,
        log_writer=log_writer,
    )

    # ---- Summary ----
    successes = sum(1 for log in logs if log.final_result.success)
    print("-" * 60)
    print(f"Experiment complete: {len(logs)} runs, {successes} successes.")
    print(f"Logs saved to: {log_dir}/")
    sys.exit(0)


if __name__ == "__main__":
    main()
