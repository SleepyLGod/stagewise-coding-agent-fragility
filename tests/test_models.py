"""Tests for the models layer."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from stagewise_coding_agent_fragility.logging.schema import TokenUsage
from stagewise_coding_agent_fragility.models.base import ModelClient
from stagewise_coding_agent_fragility.models.deepseek import DeepSeekClient
from stagewise_coding_agent_fragility.models.response_types import ModelResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_completion(content: str, prompt_tokens: int = 10, completion_tokens: int = 20) -> MagicMock:
    """Build a minimal fake openai ChatCompletion object."""
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = usage
    completion.model_dump.return_value = {"model": "deepseek-reasoner"}
    return completion


# ---------------------------------------------------------------------------
# ModelResponse
# ---------------------------------------------------------------------------

def test_model_response_fields() -> None:
    """ModelResponse stores all fields correctly."""
    usage = TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    resp = ModelResponse(
        model_name="deepseek-reasoner",
        prompt_text="hello",
        response_text="world",
        token_usage=usage,
        latency_seconds=0.5,
    )

    assert resp.model_name == "deepseek-reasoner"
    assert resp.response_text == "world"
    assert resp.token_usage.total_tokens == 15
    assert resp.latency_seconds == 0.5
    assert resp.raw_response == {}  # default


# ---------------------------------------------------------------------------
# DeepSeekClient – construction
# ---------------------------------------------------------------------------

def test_client_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Constructor raises ValueError when no API key can be found."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with patch("stagewise_coding_agent_fragility.models.deepseek.load_dotenv"):
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            DeepSeekClient("deepseek-reasoner")


def test_client_accepts_explicit_api_key() -> None:
    """Constructor succeeds when an explicit api_key is provided."""
    with patch("stagewise_coding_agent_fragility.models.deepseek.OpenAI"):
        client = DeepSeekClient("deepseek-reasoner", api_key="sk-test-key")
    assert client.model_name == "deepseek-reasoner"


def test_client_reads_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Constructor reads DEEPSEEK_API_KEY from the environment."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env-key")
    with patch("stagewise_coding_agent_fragility.models.deepseek.OpenAI"):
        client = DeepSeekClient("deepseek-chat")
    assert client.model_name == "deepseek-chat"


# ---------------------------------------------------------------------------
# DeepSeekClient – complete()
# ---------------------------------------------------------------------------

def test_complete_maps_response_correctly(monkeypatch: pytest.MonkeyPatch) -> None:
    """complete() returns a ModelResponse with correct field mapping."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    fake_completion = _make_fake_completion("def add(a, b): return a + b", 8, 15)

    mock_openai = MagicMock()
    mock_openai.return_value.chat.completions.create.return_value = fake_completion

    with patch("stagewise_coding_agent_fragility.models.deepseek.OpenAI", mock_openai):
        client = DeepSeekClient("deepseek-reasoner")
        response = client.complete(
            "write an add function",
            temperature=0.1,
            max_tokens=256,
            timeout_seconds=30.0,
        )

    assert isinstance(response, ModelResponse)
    assert response.model_name == "deepseek-reasoner"
    assert response.prompt_text == "write an add function"
    assert response.response_text == "def add(a, b): return a + b"
    assert response.token_usage.prompt_tokens == 8
    assert response.token_usage.completion_tokens == 15
    assert response.token_usage.total_tokens == 23
    assert response.latency_seconds >= 0.0
    assert response.raw_response == {"model": "deepseek-reasoner"}


def test_complete_passes_parameters_to_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """complete() forwards temperature, max_tokens, and timeout to the API."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    fake_completion = _make_fake_completion("ok")

    mock_openai = MagicMock()
    create_mock = mock_openai.return_value.chat.completions.create
    create_mock.return_value = fake_completion

    with patch("stagewise_coding_agent_fragility.models.deepseek.OpenAI", mock_openai):
        client = DeepSeekClient("deepseek-chat")
        client.complete("hi", temperature=0.7, max_tokens=512, timeout_seconds=60.0)

    create_mock.assert_called_once_with(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=512,
        timeout=60.0,
    )


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------

def test_deepseek_client_satisfies_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient structurally satisfies the ModelClient protocol."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    with patch("stagewise_coding_agent_fragility.models.deepseek.OpenAI"):
        client = DeepSeekClient("deepseek-reasoner")
    assert isinstance(client, ModelClient)

