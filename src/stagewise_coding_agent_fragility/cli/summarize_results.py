"""CLI entry point for summarizing experiment results.

Usage::

    uv run python -m stagewise_coding_agent_fragility.cli.summarize_results \
        --log-dir logs
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Aggregate experiment logs into summary tables.",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory containing run-log JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory where summary files will be written.",
    )
    return parser


def main() -> None:
    """Aggregate logs and write summary tables."""
    parser = build_argument_parser()
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    output_dir = Path(args.output_dir)

    if not log_dir.is_dir():
        print(f"Error: log directory does not exist: {log_dir}", file=sys.stderr)
        sys.exit(1)

    from stagewise_coding_agent_fragility.experiments.aggregation import (
        aggregate_from_dir,
        metrics_to_dict,
    )

    print(f"Loading logs from: {log_dir}/")
    metrics_by_condition = aggregate_from_dir(log_dir)

    if not metrics_by_condition:
        print("No conditions found.", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- CSV ----
    csv_path = output_dir / "summary.csv"
    fieldnames = [
        "condition_id",
        "num_runs",
        "final_pass_rate",
        "average_repair_rounds",
        "average_total_tokens",
        "average_wall_clock_seconds",
        "recovery_rate",
        "average_first_deviation_step",
        "pass_rate_by_round",
        "failure_type_distribution",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for condition_id in sorted(metrics_by_condition):
            row = metrics_to_dict(metrics_by_condition[condition_id])
            # Flatten the failure_type_distribution dict to a string for CSV.
            dist = row.get("failure_type_distribution", {})
            row["failure_type_distribution"] = "; ".join(
                f"{k}: {v:.2f}" for k, v in dist.items()
            ) if dist else ""
            writer.writerow(row)
    print(f"CSV summary written to: {csv_path}")

    # ---- Markdown ----
    md_path = output_dir / "summary.md"
    lines = [
        "# Experiment Summary",
        "",
        "| Condition | Runs | Pass Rate | Avg Rounds | Avg Tokens | Avg Time (s) | Recovery Rate | Avg 1st Dev |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for condition_id in sorted(metrics_by_condition):
        m = metrics_by_condition[condition_id]
        recovery = f"{m.recovery_rate:.2f}" if m.recovery_rate is not None else "N/A"
        dev = f"{m.average_first_deviation_step:.2f}" if m.average_first_deviation_step is not None else "N/A"
        lines.append(
            f"| {m.condition_id} | {m.num_runs} | {m.final_pass_rate:.2f} "
            f"| {m.average_repair_rounds:.1f} | {m.average_total_tokens:.0f} "
            f"| {m.average_wall_clock_seconds:.1f} | {recovery} | {dev} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown summary written to: {md_path}")

    # ---- Console ----
    print()
    print("=== Results ===")
    for condition_id in sorted(metrics_by_condition):
        m = metrics_by_condition[condition_id]
        recovery = f"{m.recovery_rate:.2f}" if m.recovery_rate is not None else "N/A"
        dev = f"{m.average_first_deviation_step:.2f}" if m.average_first_deviation_step is not None else "N/A"
        print(
            f"  {m.condition_id:30s}  pass={m.final_pass_rate:.2f}  "
            f"rounds={m.average_repair_rounds:.1f}  "
            f"tokens={m.average_total_tokens:.0f}  "
            f"time={m.average_wall_clock_seconds:.1f}s  "
            f"recovery={recovery}  "
            f"dev={dev}"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
