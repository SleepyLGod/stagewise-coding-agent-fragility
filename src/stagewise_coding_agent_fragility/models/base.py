"""Provider-neutral model client interface.

The agent loop and experiment runner depend only on ``ModelClient``.
No provider-specific SDK is ever imported outside of a concrete implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from stagewise_coding_agent_fragility.models.response_types import ModelResponse


@runtime_checkable
class ModelClient(Protocol):
    """Protocol satisfied by every model provider client.

    A conforming implementation must:
    - Accept a plain prompt string.
    - Return a fully populated ``ModelResponse``.
    - Raise an exception on unrecoverable API errors (let it crash).
    """

    def complete(
        self,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
    ) -> ModelResponse:
        """Send a completion request and return the normalized response.

        Args:
            prompt: The full prompt string to send.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout_seconds: Request timeout in seconds.

        Returns:
            A ``ModelResponse`` with response text, token usage, and latency.

        Raises:
            Exception: On any unrecoverable API or network error.
        """
        ...

