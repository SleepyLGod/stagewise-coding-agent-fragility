"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

from stagewise_coding_agent_fragility.config.loader import load_experiment_config
from stagewise_coding_agent_fragility.config.loader import load_models_config


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_load_models_config() -> None:
    """Loads the models config successfully."""
    config = load_models_config(REPO_ROOT / "configs/models.yaml")
    assert config.provider == "deepseek"
    assert config.models.solver_primary == "deepseek-reasoner"


def test_load_humanevalplus_experiment_config() -> None:
    """Loads the inherited HumanEval+ experiment config successfully."""
    config = load_experiment_config(REPO_ROOT / "configs/humanevalplus.yaml")
    assert config.benchmark.name == "humanevalplus"
    assert config.loop.max_rounds == 3
    assert [condition.condition_id for condition in config.conditions] == [
        "clean",
        "task_paraphrase",
        "task_simplification",
        "failure_paraphrase",
        "failure_simplification",
    ]
