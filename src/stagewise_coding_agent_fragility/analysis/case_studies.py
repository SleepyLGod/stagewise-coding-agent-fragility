"""Extract interesting case studies from run logs for qualitative analysis.

A "case study" is a ``RunLog`` selected because it shows an interesting
pattern — e.g. a clean run that passed but its perturbed counterpart failed,
or a run that recovered after multiple repair rounds.

All functions are pure: they filter and rank ``RunLog`` objects, returning
a subset for the caller to inspect or save.
"""

from __future__ import annotations

from dataclasses import dataclass

from stagewise_coding_agent_fragility.logging.schema import RunLog


@dataclass(frozen=True)
class CaseStudy:
    """One selected case study with an explanatory label.

    Attributes:
        label: Short category label describing why this run was selected.
        run_log: The selected ``RunLog``.
    """

    label: str
    run_log: RunLog


def extract_case_studies(
    logs: list[RunLog],
    baseline_condition_id: str = "clean",
    max_per_category: int = 3,
) -> list[CaseStudy]:
    """Extract a curated shortlist of case studies from all run logs.

    Categories (in priority order):
    - ``"recovered"``: perturbed run that failed round 0 but ultimately passed.
    - ``"baseline_pass_perturbed_fail"``: clean run passed, its matching
      perturbed counterpart failed (matched by task_id).
    - ``"multi_round_success"``: clean run that took more than one round to pass.
    - ``"timeout"``: any run that hit an execution timeout.

    Args:
        logs: All run logs from one experiment.
        baseline_condition_id: The condition treated as the clean reference.
        max_per_category: Maximum cases to include per category.

    Returns:
        List of ``CaseStudy`` objects, ordered by category then by run_id.
    """
    studies: list[CaseStudy] = []
    studies.extend(_find_recovered(logs, baseline_condition_id, max_per_category))
    studies.extend(_find_baseline_pass_perturbed_fail(logs, baseline_condition_id, max_per_category))
    studies.extend(_find_multi_round_success(logs, baseline_condition_id, max_per_category))
    studies.extend(_find_timeouts(logs, max_per_category))
    return studies


def summarize_case_study(study: CaseStudy) -> str:
    """Render a human-readable one-paragraph summary of a case study.

    Args:
        study: The case study to summarize.

    Returns:
        Multi-line string summarizing the run.
    """
    log = study.run_log
    status = "PASSED" if log.final_result.success else "FAILED"
    rounds = log.final_result.num_rounds_executed
    tokens = log.cost.total_tokens
    lines = [
        f"[{study.label}] run_id={log.run_id}",
        f"  task_id:    {log.task_id}",
        f"  condition:  {log.condition.condition_id}",
        f"  outcome:    {status} in {rounds} round(s)",
        f"  tokens:     {tokens}",
    ]
    if not log.final_result.success and log.final_result.failure_type:
        lines.append(f"  failure:    {log.final_result.failure_type}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _find_recovered(
    logs: list[RunLog],
    baseline_condition_id: str,
    limit: int,
) -> list[CaseStudy]:
    """Perturbed runs that failed round 0 but eventually passed."""
    candidates = [
        log for log in logs
        if log.condition.condition_id != baseline_condition_id
        and log.rounds
        and not log.rounds[0].execution_result.passed
        and log.final_result.success
    ]
    return [CaseStudy("recovered", log) for log in sorted(candidates, key=lambda l: l.run_id)[:limit]]


def _find_baseline_pass_perturbed_fail(
    logs: list[RunLog],
    baseline_condition_id: str,
    limit: int,
) -> list[CaseStudy]:
    """Tasks where clean passed but at least one perturbed run failed."""
    baseline_passed_tasks = {
        log.task_id
        for log in logs
        if log.condition.condition_id == baseline_condition_id and log.final_result.success
    }
    candidates = [
        log for log in logs
        if log.condition.condition_id != baseline_condition_id
        and not log.final_result.success
        and log.task_id in baseline_passed_tasks
    ]
    seen: set[str] = set()
    unique: list[RunLog] = []
    for log in sorted(candidates, key=lambda l: l.run_id):
        if log.task_id not in seen:
            seen.add(log.task_id)
            unique.append(log)
        if len(unique) >= limit:
            break
    return [CaseStudy("baseline_pass_perturbed_fail", log) for log in unique]


def _find_multi_round_success(
    logs: list[RunLog],
    baseline_condition_id: str,
    limit: int,
) -> list[CaseStudy]:
    """Clean runs that needed more than one round to pass."""
    candidates = [
        log for log in logs
        if log.condition.condition_id == baseline_condition_id
        and log.final_result.success
        and log.final_result.num_rounds_executed > 1
    ]
    return [
        CaseStudy("multi_round_success", log)
        for log in sorted(candidates, key=lambda l: l.run_id)[:limit]
    ]


def _find_timeouts(logs: list[RunLog], limit: int) -> list[CaseStudy]:
    """Any run that hit an execution timeout in any round."""
    candidates = [
        log for log in logs
        if any(r.execution_result.timeout for r in log.rounds)
    ]
    return [
        CaseStudy("timeout", log)
        for log in sorted(candidates, key=lambda l: l.run_id)[:limit]
    ]

