"""Build prompts for model-based perturbation generation.

A perturbation prompt asks the model to rewrite a text while preserving its
meaning (semantic_paraphrase) or simplifying its language (mild_simplification).
The prompt is a deterministic function of the text and the perturbation type.
"""

from __future__ import annotations

_PERTURBATION_INSTRUCTIONS: dict[str, str] = {
    "semantic_paraphrase": (
        "Rewrite the following text so that it preserves the exact same meaning "
        "and all technical details, but uses different wording and sentence structure. "
        "Do not omit any information. Do not add new information."
    ),
    "mild_simplification": (
        "Rewrite the following text using simpler vocabulary and shorter sentences. "
        "Preserve all technical details and constraints exactly. "
        "Do not omit any information. Do not add new information."
    ),
}

_PERTURBATION_PROMPT_TEMPLATE = """\
{instruction}

Return ONLY the rewritten text, with no preamble or explanation.

---

{text}

---"""


def build_perturbation_prompt(text: str, perturbation_type: str) -> str:
    """Build a prompt that asks the model to apply a semantic perturbation to ``text``.

    Args:
        text: The text to perturb.
        perturbation_type: One of ``"semantic_paraphrase"`` or
            ``"mild_simplification"``.

    Returns:
        A formatted prompt string ready to send to the model.

    Raises:
        ValueError: If ``perturbation_type`` is not a supported type.
    """
    instruction = _PERTURBATION_INSTRUCTIONS.get(perturbation_type)
    if instruction is None:
        raise ValueError(
            f"Unsupported perturbation_type {perturbation_type!r}. "
            f"Valid types: {sorted(_PERTURBATION_INSTRUCTIONS)}"
        )
    return _PERTURBATION_PROMPT_TEMPLATE.format(
        instruction=instruction,
        text=text.strip(),
    )

