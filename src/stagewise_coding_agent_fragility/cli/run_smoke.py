"""Smoke CLI for validating config loading."""

from __future__ import annotations

import argparse
from pathlib import Path

from stagewise_coding_agent_fragility.config.loader import build_smoke_summary
from stagewise_coding_agent_fragility.config.loader import load_experiment_config
from stagewise_coding_agent_fragility.config.loader import load_models_config
from stagewise_coding_agent_fragility.config.loader import smoke_summary_to_lines


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validate experiment and model configs.",
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
    """Run the smoke CLI."""
    parser = build_argument_parser()
    args = parser.parse_args()

    experiment_config = load_experiment_config(Path(args.experiment_config))
    models_config = load_models_config(Path(args.models_config))
    summary = build_smoke_summary(experiment_config)

    print("Smoke config validation succeeded.")
    print(f"provider: {models_config.provider}")
    print(f"solver_primary: {models_config.models.solver_primary}")
    print(f"perturbation_generator: {models_config.models.perturbation_generator}")
    for line in smoke_summary_to_lines(summary):
        print(line)


if __name__ == "__main__":
    main()
