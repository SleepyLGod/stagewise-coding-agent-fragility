"""Build the initial task prompt from a Task object.

The prompt is a deterministic function of the task — no randomness, no state.
"""

from __future__ import annotations

from stagewise_coding_agent_fragility.benchmarks.base import Task

_TASK_PROMPT_TEMPLATE = """\
You are an expert Python programmer.

Implement the following Python function. Return ONLY the function implementation \
as a Python code block. Do not include any explanation, tests, or extra text.

```python
{prompt}
```"""


def build_task_prompt(task: Task) -> str:
    """Build the initial task prompt for the model.

    Args:
        task: The benchmark task to solve.

    Returns:
        A formatted prompt string ready to send to the model.
    """
    return _TASK_PROMPT_TEMPLATE.format(prompt=task.prompt.strip())

