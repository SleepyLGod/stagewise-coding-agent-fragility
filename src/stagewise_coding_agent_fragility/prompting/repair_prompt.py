"""Build repair prompts from the original task, failing code, and failure signal.

The repair prompt is a deterministic function of its three inputs.
"""

from __future__ import annotations

_REPAIR_PROMPT_TEMPLATE = """\
You are an expert Python programmer performing test-driven debugging.

You previously attempted to solve a programming task. Your solution failed the tests.
Study the task description, your code, and the failure information, then provide \
a corrected implementation.

Return ONLY the corrected Python function as a code block. Do not include any \
explanation or extra text.

---

## Task

{task_prompt}

---

## Your Previous Attempt

```python
{candidate_code}
```

---

## Test Failure

{failure_summary}

---

Provide the corrected implementation:"""


def build_repair_prompt(
    task_prompt: str,
    candidate_code: str,
    failure_summary: str,
) -> str:
    """Build a repair prompt combining the original task, failing code, and failure signal.

    Args:
        task_prompt: The original (or perturbed) task prompt string.
        candidate_code: The code that failed the tests.
        failure_summary: A human-readable summary of the test failure.

    Returns:
        A formatted repair prompt string ready to send to the model.
    """
    return _REPAIR_PROMPT_TEMPLATE.format(
        task_prompt=task_prompt.strip(),
        candidate_code=candidate_code.strip(),
        failure_summary=failure_summary.strip(),
    )

