"""Tests for the OpenAI-compatible model client configuration."""

from __future__ import annotations

import pytest

import stagewise_coding_agent_fragility.models.deepseek as deepseek_module
from stagewise_coding_agent_fragility.models.deepseek import DeepSeekClient


def test_model_client_uses_configured_api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Builds a client using a non-DeepSeek environment variable name."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")

    client = DeepSeekClient(
        "qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="QWEN_API_KEY",
    )

    assert client.model_name == "qwen-turbo"


def test_model_client_raises_with_requested_env_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raises an error that points to the configured environment variable name."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.setattr(deepseek_module, "load_dotenv", lambda: False)

    with pytest.raises(ValueError, match="QWEN_API_KEY"):
        DeepSeekClient(
            "qwen-turbo",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="QWEN_API_KEY",
        )
