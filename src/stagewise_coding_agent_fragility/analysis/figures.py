"""Build figure-ready data structures from condition metrics.

This module does NOT render plots itself — it produces plain Python dicts
and lists that can be fed to matplotlib, plotly, or any other renderer.
Keeping rendering out of this module lets the analysis run in headless
environments without optional graphical dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

from stagewise_coding_agent_fragility.experiments.metrics import ConditionMetrics


@dataclass(frozen=True)
class BarChartData:
    """Data for a single grouped bar chart.

    Attributes:
        title: Chart title.
        x_labels: Category labels (one per condition).
        series: Mapping from series name to list of values aligned with x_labels.
    """

    title: str
    x_labels: list[str]
    series: dict[str, list[float]]


def build_pass_rate_chart(
    metrics: dict[str, ConditionMetrics],
    baseline_condition_id: str = "clean",
) -> BarChartData:
    """Build bar chart data for final_pass_rate across conditions.

    Args:
        metrics: Mapping from condition_id to ConditionMetrics.
        baseline_condition_id: Placed first on the x-axis.

    Returns:
        ``BarChartData`` ready to pass to a plotting function.
    """
    ordered = _order_ids(list(metrics.keys()), baseline_condition_id)
    return BarChartData(
        title="Final Pass Rate by Condition",
        x_labels=ordered,
        series={"final_pass_rate": [metrics[cid].final_pass_rate for cid in ordered]},
    )


def build_repair_rounds_chart(
    metrics: dict[str, ConditionMetrics],
    baseline_condition_id: str = "clean",
) -> BarChartData:
    """Build bar chart data for average_repair_rounds across conditions.

    Args:
        metrics: Mapping from condition_id to ConditionMetrics.
        baseline_condition_id: Placed first on the x-axis.

    Returns:
        ``BarChartData`` ready to pass to a plotting function.
    """
    ordered = _order_ids(list(metrics.keys()), baseline_condition_id)
    return BarChartData(
        title="Average Repair Rounds by Condition",
        x_labels=ordered,
        series={"average_repair_rounds": [metrics[cid].average_repair_rounds for cid in ordered]},
    )


def build_recovery_rate_chart(
    metrics: dict[str, ConditionMetrics],
    baseline_condition_id: str = "clean",
) -> BarChartData:
    """Build bar chart data for recovery_rate across perturbed conditions.

    Conditions with ``recovery_rate == None`` (all passed on round 0) are
    represented as ``0.0`` in the series to keep the chart layout uniform.

    Args:
        metrics: Mapping from condition_id to ConditionMetrics.
        baseline_condition_id: Placed first on the x-axis.

    Returns:
        ``BarChartData`` ready to pass to a plotting function.
    """
    ordered = _order_ids(list(metrics.keys()), baseline_condition_id)
    values = [
        metrics[cid].recovery_rate if metrics[cid].recovery_rate is not None else 0.0
        for cid in ordered
    ]
    return BarChartData(
        title="Recovery Rate by Condition",
        x_labels=ordered,
        series={"recovery_rate": values},
    )


def build_token_cost_chart(
    metrics: dict[str, ConditionMetrics],
    baseline_condition_id: str = "clean",
) -> BarChartData:
    """Build bar chart data for average_total_tokens across conditions.

    Args:
        metrics: Mapping from condition_id to ConditionMetrics.
        baseline_condition_id: Placed first on the x-axis.

    Returns:
        ``BarChartData`` ready to pass to a plotting function.
    """
    ordered = _order_ids(list(metrics.keys()), baseline_condition_id)
    return BarChartData(
        title="Average Token Cost by Condition",
        x_labels=ordered,
        series={"average_total_tokens": [metrics[cid].average_total_tokens for cid in ordered]},
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _order_ids(condition_ids: list[str], baseline_id: str) -> list[str]:
    """Return condition IDs with baseline first, rest sorted."""
    others = sorted(cid for cid in condition_ids if cid != baseline_id)
    if baseline_id in condition_ids:
        return [baseline_id] + others
    return others

