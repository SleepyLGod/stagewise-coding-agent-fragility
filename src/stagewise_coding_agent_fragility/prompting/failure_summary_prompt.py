"""Build prompts for model-based failure summarization.

Used when ``LoopConfig.use_rule_based_failure_summary`` is False.
The prompt is a deterministic function of the code and raw error text.
"""

from __future__ import annotations

_FAILURE_SUMMARY_PROMPT_TEMPLATE = """\
You are an expert Python debugger.

Below is a Python function and the error output from running its tests.
Summarize the failure in 2–3 sentences: what went wrong, what the tests expected, \
and what the code produced (if visible in the output). Be concise and precise.

Do NOT rewrite the code. Only summarize the failure.

---

## Code

```python
{candidate_code}
```

---

## Error Output

{raw_failure}

---

Failure summary:"""


def build_failure_summary_prompt(
    candidate_code: str,
    raw_failure: str,
) -> str:
    """Build a prompt that asks the model to summarize a test failure.

    Args:
        candidate_code: The Python code that was executed.
        raw_failure: Raw error text from the test run.

    Returns:
        A formatted prompt string ready to send to the model.
    """
    return _FAILURE_SUMMARY_PROMPT_TEMPLATE.format(
        candidate_code=candidate_code.strip(),
        raw_failure=raw_failure.strip() or "(no output captured)",
    )

