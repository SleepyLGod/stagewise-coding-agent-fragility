"""CLI entry point for generating visualizations from aggregated metrics.

Usage::

    uv run python -m stagewise_coding_agent_fragility.cli.generate_figures \
        --log-dir logs \
        --output-dir results/figures
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from stagewise_coding_agent_fragility.cli.log_dir import resolve_log_dir
from stagewise_coding_agent_fragility.experiments.aggregation import aggregate_from_dir
from stagewise_coding_agent_fragility.experiments.metrics import ConditionMetrics

# Set seaborn defaults for professional looking plots
sns.set_theme(style="whitegrid", palette="muted")


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate visualizations from experiment logs.",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory containing run-log JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Directory where figures will be saved. "
            "Defaults to results/<log-dir-name>/figures/."
        ),
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Explicitly select the newest child directory under --log-dir.",
    )
    return parser


def plot_pass_and_recovery(
    metrics_by_condition: dict[str, ConditionMetrics],
    output_dir: Path,
) -> None:
    """Plot Final Pass Rate and Recovery Rate side-by-side per condition."""
    conditions = sorted(metrics_by_condition.keys())
    pass_rates = [metrics_by_condition[c].final_pass_rate for c in conditions]
    
    # recovery_rate can be None if all runs passed on round 0.
    recovery_rates = [
        metrics_by_condition[c].recovery_rate or 0.0
        for c in conditions
    ]

    x = np.arange(len(conditions))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, pass_rates, width, label='Final Pass Rate', color='skyblue')
    ax.bar(x + width/2, recovery_rates, width, label='Recovery Rate', color='salmon')

    ax.set_ylabel('Rate')
    ax.set_title('Pass Rate and Recovery Rate by Condition')
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend()

    plt.tight_layout()
    out_path = output_dir / "pass_and_recovery.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")


def plot_pass_rate_by_round(
    metrics_by_condition: dict[str, ConditionMetrics],
    output_dir: Path,
) -> None:
    """Plot cumulative pass rate over rounds (survival curve)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for condition_id in sorted(metrics_by_condition.keys()):
        m = metrics_by_condition[condition_id]
        if not m.pass_rate_by_round:
            continue
            
        rounds = sorted(m.pass_rate_by_round.keys())
        rates = [m.pass_rate_by_round[r] for r in rounds]
        
        # Use a solid line for clean baseline, dashed for others
        linestyle = '-' if condition_id == "clean" else '--'
        linewidth = 2.5 if condition_id == "clean" else 1.5
        
        ax.plot(
            rounds,
            rates,
            marker='o',
            linestyle=linestyle,
            linewidth=linewidth,
            label=condition_id
        )

    ax.set_xlabel('Round Index')
    ax.set_ylabel('Cumulative Pass Rate')
    ax.set_title('Pass Rate Trajectory over Rounds')
    
    # Ensure x-axis only shows integer ticks
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_ylim(0, 1.05)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    out_path = output_dir / "pass_rate_by_round.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")


def plot_first_deviation_step(
    metrics_by_condition: dict[str, ConditionMetrics],
    output_dir: Path,
) -> None:
    """Plot the average first deviation step for perturbed conditions."""
    # Filter out baseline since it has a None deviation step
    perturbed = [
        m for m in metrics_by_condition.values()
        if m.average_first_deviation_step is not None
    ]
    
    if not perturbed:
        print("No deviation steps to plot (no valid perturbed conditions found).")
        return

    perturbed.sort(key=lambda m: m.condition_id)
    conditions = [m.condition_id for m in perturbed]
    dev_steps = [m.average_first_deviation_step for m in perturbed]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=conditions, y=dev_steps, ax=ax, palette="viridis")

    ax.set_ylabel('Average First Deviation Step')
    ax.set_title('When Execution Trajectories Diverge from Clean Run')
    ax.set_xticklabels(conditions, rotation=45, ha="right")
    
    plt.tight_layout()
    out_path = output_dir / "first_deviation_step.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")


def main() -> None:
    """Generate all figures."""
    parser = build_argument_parser()
    args = parser.parse_args()

    raw_log_dir = Path(args.log_dir)

    try:
        log_dir = resolve_log_dir(raw_log_dir, latest=args.latest)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.latest and log_dir != raw_log_dir:
        print(f"Selected latest log directory: {log_dir}")

    output_dir = (
        Path(args.output_dir) if args.output_dir else Path("results") / log_dir.name / "figures"
    )

    print(f"Loading logs from: {log_dir}/")
    metrics_by_condition = aggregate_from_dir(log_dir)
    if not metrics_by_condition:
        print("No conditions found.", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    plot_pass_and_recovery(metrics_by_condition, output_dir)
    plot_pass_rate_by_round(metrics_by_condition, output_dir)
    plot_first_deviation_step(metrics_by_condition, output_dir)

    print("All figures generated successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
