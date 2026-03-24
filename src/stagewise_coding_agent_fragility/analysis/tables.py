"""Build structured comparison tables from condition metrics.

All functions are pure: they accept metrics dicts and return plain Python
objects (lists-of-dicts or CSV strings).  Callers write the output to disk.
"""

from __future__ import annotations

import csv
import io

from stagewise_coding_agent_fragility.experiments.metrics import ConditionMetrics

# Column definitions in display order.
_COLUMNS: list[str] = [
    "condition_id",
    "num_runs",
    "final_pass_rate",
    "average_repair_rounds",
    "average_total_tokens",
    "average_wall_clock_seconds",
    "recovery_rate",
    "average_first_deviation_step",
]


def build_comparison_table(
    metrics: dict[str, ConditionMetrics],
    baseline_condition_id: str = "clean",
) -> list[dict[str, object]]:
    """Build a flat comparison table across conditions.

    Each row represents one condition.  The baseline condition (usually
    ``"clean"``) is placed first when present.

    Args:
        metrics: Mapping from ``condition_id`` to ``ConditionMetrics``.
        baseline_condition_id: The condition to place at the top of the table.

    Returns:
        List of row dicts with keys matching ``_COLUMNS``.
    """
    ordered_ids = _order_condition_ids(list(metrics.keys()), baseline_condition_id)
    return [_metrics_to_row(metrics[cid]) for cid in ordered_ids]


def table_to_csv(rows: list[dict[str, object]]) -> str:
    """Render a comparison table as a CSV string.

    Args:
        rows: Row dicts produced by ``build_comparison_table``.

    Returns:
        UTF-8 CSV string (header + data rows), ready to write to a ``.csv`` file.
    """
    if not rows:
        return ""

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=_COLUMNS,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def table_to_markdown(rows: list[dict[str, object]]) -> str:
    """Render a comparison table as a GitHub-flavored Markdown table.

    Args:
        rows: Row dicts produced by ``build_comparison_table``.

    Returns:
        Markdown table string.
    """
    if not rows:
        return ""

    header = " | ".join(_COLUMNS)
    separator = " | ".join(["---"] * len(_COLUMNS))
    data_rows = [
        " | ".join(str(row.get(col, "")) for col in _COLUMNS)
        for row in rows
    ]
    return "\n".join(["| " + header + " |", "| " + separator + " |"]
                     + ["| " + r + " |" for r in data_rows])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _metrics_to_row(m: ConditionMetrics) -> dict[str, object]:
    """Convert a ``ConditionMetrics`` to a flat row dict."""
    return {
        "condition_id": m.condition_id,
        "num_runs": m.num_runs,
        "final_pass_rate": round(m.final_pass_rate, 4),
        "average_repair_rounds": round(m.average_repair_rounds, 2),
        "average_total_tokens": round(m.average_total_tokens, 1),
        "average_wall_clock_seconds": round(m.average_wall_clock_seconds, 2),
        "recovery_rate": round(m.recovery_rate, 4) if m.recovery_rate is not None else "N/A",
        "average_first_deviation_step": round(m.average_first_deviation_step, 2) if m.average_first_deviation_step is not None else "N/A",
    }


def _order_condition_ids(
    condition_ids: list[str],
    baseline_id: str,
) -> list[str]:
    """Return condition IDs with the baseline first, rest sorted."""
    others = sorted(cid for cid in condition_ids if cid != baseline_id)
    if baseline_id in condition_ids:
        return [baseline_id] + others
    return others

