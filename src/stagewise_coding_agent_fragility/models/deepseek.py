"""DeepSeek model client.

Uses the OpenAI-compatible DeepSeek API via the ``openai`` SDK.
All DeepSeek-specific logic is confined to this module.

API key resolution order:
1. Explicit ``api_key`` argument passed to the constructor.
2. ``DEEPSEEK_API_KEY`` environment variable.
3. ``.env`` file in the current working directory (loaded automatically as a
   last-resort fallback via ``python-dotenv``).

If none of the above yields a key, ``ValueError`` is raised immediately so the
error surfaces at construction time rather than at request time.
"""

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from stagewise_coding_agent_fragility.logging.schema import TokenUsage
from stagewise_coding_agent_fragility.models.response_types import ModelResponse

_DEFAULT_BASE_URL = "https://api.deepseek.com"


class DeepSeekClient:
    """OpenAI-compatible client for the DeepSeek API.

    Args:
        model_name: DeepSeek model identifier (e.g. ``"deepseek-reasoner"``).
        api_key: Explicit API key.  If ``None``, resolved from the environment.
        base_url: API base URL.  Defaults to the official DeepSeek endpoint.
    """

    def __init__(
        self,
        model_name: str,
        *,
        api_key: str | None = None,
        base_url: str = _DEFAULT_BASE_URL,
    ) -> None:
        resolved_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not resolved_key:
            # Last resort: try to load a .env file then re-check.
            load_dotenv()
            resolved_key = os.environ.get("DEEPSEEK_API_KEY")
        if not resolved_key:
            raise ValueError(
                "DeepSeek API key not found. "
                "Set DEEPSEEK_API_KEY in your environment or .env file."
            )

        self._model_name = model_name
        self._client = OpenAI(api_key=resolved_key, base_url=base_url)

    @property
    def model_name(self) -> str:
        """The model identifier this client is configured to use."""
        return self._model_name

    def complete(
        self,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
    ) -> ModelResponse:
        """Send a chat completion request and return a normalized response.

        The prompt is sent as a single user message.  System-level framing is
        left to the caller (prompt builder layer).

        Args:
            prompt: Full prompt string to send as the user message.
            temperature: Sampling temperature.
            max_tokens: Maximum number of tokens to generate.
            timeout_seconds: HTTP request timeout in seconds.

        Returns:
            A ``ModelResponse`` with response text, token usage, and latency.

        Raises:
            openai.OpenAIError: On any API or network error.
        """
        t_start = time.monotonic()
        raw = self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout_seconds,
        )
        latency = time.monotonic() - t_start

        response_text = raw.choices[0].message.content or ""
        usage = raw.usage

        return ModelResponse(
            model_name=self._model_name,
            prompt_text=prompt,
            response_text=response_text,
            token_usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
            latency_seconds=latency,
            raw_response=_serialize_completion(raw),
        )


def _serialize_completion(raw: Any) -> dict[str, Any]:
    """Convert an ``openai`` completion object to a plain dict for logging.

    Args:
        raw: The ``ChatCompletion`` object returned by the openai SDK.

    Returns:
        A JSON-serializable dict representation.
    """
    try:
        return raw.model_dump()
    except AttributeError:
        return {}

