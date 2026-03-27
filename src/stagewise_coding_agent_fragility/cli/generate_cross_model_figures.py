"""Generate cross-model comparison tables and figures from raw log groups.

Usage::

    uv run python -m stagewise_coding_agent_fragility.cli.generate_cross_model_figures \
        --manifest configs/cross_model_runs.yaml \
        --output-dir results/cross_model
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from stagewise_coding_agent_fragility.analysis.cross_model import (
    GroupAggregate,
    aggregate_groups,
    build_perturbation_failure_matrix,
    build_condition_rows,
    build_group_rows,
)

sns.set_theme(style="whitegrid", palette="muted")


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate cross-model comparison figures from raw log groups.",
    )
    parser.add_argument(
        "--manifest",
        default="configs/cross_model_runs.yaml",
        help="YAML manifest describing the run groups to compare.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/cross_model",
        help="Directory where cross-model tables and figures will be written.",
    )
    return parser


def main() -> None:
    """Generate cross-model summary tables and figures."""
    parser = build_argument_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    groups = aggregate_groups(args.manifest)
    if not groups:
        print("No run groups loaded from the manifest.", file=sys.stderr)
        sys.exit(1)

    _write_csv(output_dir / "condition_summary.csv", build_condition_rows(groups))
    _write_csv(output_dir / "group_summary.csv", build_group_rows(groups))

    plot_delta_heatmap(
        groups,
        metric_name="final_pass_rate",
        title="Delta Final Pass Rate vs Clean",
        output_path=figures_dir / "delta_final_pass_rate_heatmap.png",
    )
    plot_delta_heatmap(
        groups,
        metric_name="round0_pass_rate",
        title="Delta Round-0 Pass Rate vs Clean",
        output_path=figures_dir / "delta_round0_pass_rate_heatmap.png",
    )
    plot_delta_heatmap(
        groups,
        metric_name="average_total_tokens",
        title="Delta Average Total Tokens vs Clean",
        output_path=figures_dir / "delta_average_total_tokens_heatmap.png",
    )
    plot_clean_accuracy_vs_cost(
        groups,
        output_path=figures_dir / "clean_accuracy_vs_cost.png",
    )
    plot_deepseek_chat_parameter_sweep(
        groups,
        output_path=figures_dir / "deepseek_chat_parameter_sweep.png",
    )
    plot_contract_drift_rate(
        groups,
        output_path=figures_dir / "task_prompt_contract_drift.png",
    )
    plot_perturbation_failure_overlap(
        manifest_path=args.manifest,
        output_path=figures_dir / "perturbation_failure_overlap.png",
    )

    print(f"Wrote cross-model tables to: {output_dir}/")
    print(f"Wrote cross-model figures to: {figures_dir}/")
    sys.exit(0)


def plot_delta_heatmap(
    groups: list[GroupAggregate],
    *,
    metric_name: str,
    title: str,
    output_path: Path,
) -> None:
    """Plot a model-by-condition heatmap of deltas versus clean."""
    condition_ids = sorted(
        {
            condition_id
            for group in groups
            for condition_id in group.conditions
            if condition_id != "clean"
        }
    )
    labels = [group.display_name for group in groups]
    matrix = np.zeros((len(groups), len(condition_ids)))

    for row_index, group in enumerate(groups):
        clean = getattr(group.conditions["clean"], metric_name)
        for col_index, condition_id in enumerate(condition_ids):
            value = getattr(group.conditions[condition_id], metric_name)
            matrix[row_index, col_index] = value - clean

    fig, ax = plt.subplots(figsize=(12, max(5, len(groups) * 0.6)))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".3f",
        center=0.0,
        cmap="coolwarm",
        xticklabels=condition_ids,
        yticklabels=labels,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Model Group")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_clean_accuracy_vs_cost(
    groups: list[GroupAggregate],
    *,
    output_path: Path,
) -> None:
    """Plot clean-condition accuracy versus token cost across model groups."""
    fig, ax = plt.subplots(figsize=(10, 7))

    family_colors = {
        "deepseek": "#2a6f97",
        "kimi": "#8f2d56",
        "qwen": "#3a7d44",
    }

    for group in groups:
        clean = group.conditions["clean"]
        color = family_colors.get(group.family, "#555555")
        ax.scatter(
            clean.average_total_tokens,
            clean.final_pass_rate,
            s=100,
            color=color,
            edgecolors="black",
            linewidth=0.6,
        )
        ax.annotate(
            group.display_name,
            (clean.average_total_tokens, clean.final_pass_rate),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_title("Clean Accuracy vs Token Cost")
    ax.set_xlabel("Average Total Tokens")
    ax.set_ylabel("Final Pass Rate")
    ax.set_ylim(0.85, 1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_deepseek_chat_parameter_sweep(
    groups: list[GroupAggregate],
    *,
    output_path: Path,
) -> None:
    """Plot DeepSeek-Chat parameter groups across key conditions."""
    deepseek_chat_groups = [
        group for group in groups if group.group_id.startswith("ds_chat_")
    ]
    ordered_groups = sorted(
        deepseek_chat_groups,
        key=lambda group: _parameter_rank(group.parameter_group),
    )
    if not ordered_groups:
        return

    conditions = [
        "clean",
        "failure_paraphrase",
        "failure_simplification",
        "task_paraphrase",
        "task_simplification",
    ]
    x = np.arange(len(ordered_groups))
    width = 0.16

    fig, ax = plt.subplots(figsize=(12, 6))
    for offset_index, condition_id in enumerate(conditions):
        values = [
            group.conditions[condition_id].final_pass_rate for group in ordered_groups
        ]
        ax.bar(
            x + (offset_index - 2) * width,
            values,
            width,
            label=condition_id,
        )

    ax.set_title("DeepSeek-Chat Parameter Sweep by Condition")
    ax.set_ylabel("Final Pass Rate")
    ax.set_xlabel("Parameter Group")
    ax.set_xticks(x)
    ax.set_xticklabels([group.parameter_group for group in ordered_groups])
    ax.set_ylim(0.85, 1.01)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_contract_drift_rate(
    groups: list[GroupAggregate],
    *,
    output_path: Path,
) -> None:
    """Plot task-prompt function-name drift rate by model group."""
    ordered_groups = sorted(groups, key=lambda group: group.contract_drift_rate, reverse=True)
    labels = [group.display_name for group in ordered_groups]
    values = [group.contract_drift_rate * 100 for group in ordered_groups]
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(x, values, color=sns.color_palette("crest", n_colors=len(labels)))
    ax.set_title("Task-Prompt Function-Name Drift Rate")
    ax.set_ylabel("Drift Rate (%)")
    ax.set_xlabel("Model Group")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_perturbation_failure_overlap(
    *,
    manifest_path: str | Path,
    output_path: Path,
) -> None:
    """Plot task-level perturbation-induced failure overlap across groups."""
    task_ids, group_labels, matrix = build_perturbation_failure_matrix(
        manifest_path,
        top_k=20,
    )
    if not task_ids:
        return

    fig, ax = plt.subplots(figsize=(12, max(6, len(task_ids) * 0.4)))
    sns.heatmap(
        np.array(matrix),
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        xticklabels=group_labels,
        yticklabels=task_ids,
        ax=ax,
    )
    ax.set_title("Perturbation-Induced Failed Runs by Task and Model Group")
    ax.set_xlabel("Model Group")
    ax.set_ylabel("Task ID")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a list of row dictionaries to CSV."""
    if not rows:
        raise ValueError("Cannot write an empty CSV table.")

    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _parameter_rank(parameter_group: str) -> int:
    """Return a stable plotting order for DeepSeek-Chat variants."""
    order = {
        "initial": 0,
        "conservative": 1,
        "balanced": 2,
        "creative": 3,
    }
    return order.get(parameter_group, 99)


if __name__ == "__main__":
    main()
