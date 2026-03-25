"""Build prompts for model-based perturbation generation."""

from __future__ import annotations

_STAGE_AWARE_INSTRUCTIONS: dict[str, dict[str, str]] = {
    "task_prompt": {
        "semantic_paraphrase": (
            "Rewrite the task prompt with different wording, sentence structure, and "
            "information order. Preserve every explicit requirement, edge case, and "
            "testable constraint. You may change emphasis and reorganize the prose, "
            "but do not add new requirements or remove any explicit ones. If the text "
            "contains Python code, a function signature, or examples, copy them exactly."
        ),
        "mild_simplification": (
            "Rewrite the task prompt in shorter, plainer language. Keep every explicit "
            "input-output requirement, edge case, constraint, and example, but compress "
            "secondary explanation and reduce diagnostic hints. Do not add new facts. If "
            "the text contains Python code, a function signature, or examples, copy them exactly."
        ),
    },
    "failure_summary": {
        "semantic_paraphrase": (
            "Rewrite the failure summary by reorganizing the information flow and changing "
            "emphasis. Move the most diagnostic clue (e.g., root cause, key mismatch) toward "
            "the end or bury it in the middle. Add observational padding at the beginning "
            "(e.g., 'The test execution encountered an issue', 'An assertion was raised'). "
            "Use passive voice and hedging language ('it appears', 'possibly', 'one might observe'). "
            "Keep all factual evidence (exception names, expected vs actual values, failing conditions), "
            "but make the causal chain less obvious. Do not invent new facts or fixes."
        ),
        "mild_simplification": (
            "Rewrite the failure summary into a brief, surface-level observation. Drop all "
            "diagnostic reasoning, causal explanation, and contextual interpretation. Keep only: "
            "(1) the exception type if present, (2) one concrete piece of evidence showing the "
            "mismatch (e.g., 'expected X, got Y'). Present it as a flat observation without "
            "explaining why it failed or what might be wrong. Do not invent new facts or fixes."
        ),
    },
}

_PERTURBATION_PROMPT_TEMPLATE = """\
Injection stage: {injection_stage}

{instruction}

Return ONLY the rewritten text, with no preamble or explanation.

---

{text}

---"""


def build_perturbation_prompt(
    text: str,
    perturbation_type: str,
    injection_stage: str,
) -> str:
    """Build a prompt that asks the model to perturb ``text`` for one stage.

    Args:
        text: The text to perturb.
        perturbation_type: One of ``"semantic_paraphrase"`` or
            ``"mild_simplification"``.
        injection_stage: One of ``"task_prompt"`` or ``"failure_summary"``.

    Returns:
        A formatted prompt string ready to send to the model.

    Raises:
        ValueError: If ``injection_stage`` or ``perturbation_type`` is unsupported.
    """
    stage_instructions = _STAGE_AWARE_INSTRUCTIONS.get(injection_stage)
    if stage_instructions is None:
        raise ValueError(
            f"Unsupported injection_stage {injection_stage!r}. "
            f"Valid stages: {sorted(_STAGE_AWARE_INSTRUCTIONS)}"
        )

    instruction = stage_instructions.get(perturbation_type)
    if instruction is None:
        raise ValueError(
            f"Unsupported perturbation_type {perturbation_type!r}. "
            f"Valid types for {injection_stage!r}: {sorted(stage_instructions)}"
        )
    return _PERTURBATION_PROMPT_TEMPLATE.format(
        injection_stage=injection_stage,
        instruction=instruction,
        text=text.strip(),
    )

