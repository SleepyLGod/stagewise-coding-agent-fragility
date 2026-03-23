"""YAML configuration loader for experiment and model settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from stagewise_coding_agent_fragility.config.schema import BenchmarkConfig
from stagewise_coding_agent_fragility.config.schema import ConditionConfig
from stagewise_coding_agent_fragility.config.schema import EnabledConditionsConfig
from stagewise_coding_agent_fragility.config.schema import ExecutionConfig
from stagewise_coding_agent_fragility.config.schema import ExperimentConfig
from stagewise_coding_agent_fragility.config.schema import LoggingConfig
from stagewise_coding_agent_fragility.config.schema import MetricsConfig
from stagewise_coding_agent_fragility.config.schema import ModelNames
from stagewise_coding_agent_fragility.config.schema import ModelRequestDefaults
from stagewise_coding_agent_fragility.config.schema import ModelsConfig
from stagewise_coding_agent_fragility.config.schema import ResultsConfig
from stagewise_coding_agent_fragility.config.schema import LoopConfig
from stagewise_coding_agent_fragility.config.schema import SmokeSummary


class ConfigError(ValueError):
    """Raised when a config file is invalid."""


def load_models_config(config_path: str | Path) -> ModelsConfig:
    """Load the model configuration from YAML.

    Args:
        config_path: Path to the model config YAML file.

    Returns:
        Parsed model configuration.
    """
    raw_config = _load_yaml_file(config_path)
    return _parse_models_config(raw_config)


def load_experiment_config(config_path: str | Path) -> ExperimentConfig:
    """Load an experiment config, resolving inheritance if present.

    Args:
        config_path: Path to the experiment config YAML file.

    Returns:
        Parsed experiment configuration with concrete condition definitions.
    """
    config_path = Path(config_path)
    raw_config = _load_yaml_file(config_path)
    if "inherits" not in raw_config:
        return _parse_experiment_config(raw_config)

    base_path = _resolve_inherited_config_path(config_path, raw_config["inherits"])
    base_config = _load_yaml_file(base_path)
    base_experiment = _parse_experiment_config(base_config)
    enabled_conditions = _parse_enabled_conditions(raw_config, base_experiment.conditions)
    merged_config = _merge_dicts(
        base_config,
        raw_config,
        skip_keys={"inherits", "conditions"},
    )
    merged_config["conditions"] = [
        {
            "condition_id": condition.condition_id,
            "injection_stage": condition.injection_stage,
            "perturbation_type": condition.perturbation_type,
            "perturbation_strength": condition.perturbation_strength,
        }
        for condition in enabled_conditions
    ]
    return _parse_experiment_config(merged_config)


def build_smoke_summary(experiment_config: ExperimentConfig) -> SmokeSummary:
    """Build a compact summary for smoke CLI output.

    Args:
        experiment_config: Parsed experiment config.

    Returns:
        Compact summary for display.
    """
    return SmokeSummary(
        experiment_name=experiment_config.experiment_name,
        benchmark_name=experiment_config.benchmark.name,
        task_subset=experiment_config.benchmark.task_subset,
        max_rounds=experiment_config.loop.max_rounds,
        repeats=experiment_config.repeats,
        enabled_condition_ids=[
            condition.condition_id for condition in experiment_config.conditions
        ],
    )


def smoke_summary_to_lines(summary: SmokeSummary) -> list[str]:
    """Render a smoke summary as readable lines.

    Args:
        summary: Compact smoke summary.

    Returns:
        Human-readable summary lines.
    """
    return [
        f"experiment_name: {summary.experiment_name}",
        f"benchmark_name: {summary.benchmark_name}",
        f"task_subset: {summary.task_subset}",
        f"max_rounds: {summary.max_rounds}",
        f"repeats: {summary.repeats}",
        "enabled_conditions:",
        *[f"  - {condition_id}" for condition_id in summary.enabled_condition_ids],
    ]


def _load_yaml_file(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary.

    Args:
        config_path: Path to the YAML file.

    Returns:
        Raw YAML mapping.

    Raises:
        ConfigError: If the file is missing, malformed, or not a mapping.
    """
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Config file does not exist: {path}")

    with path.open("r", encoding="utf-8") as file_handle:
        raw_data = yaml.safe_load(file_handle)

    if not isinstance(raw_data, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {path}")
    return raw_data


def _resolve_inherited_config_path(config_path: Path, inherited_path: Any) -> Path:
    """Resolve the path of an inherited config file.

    Args:
        config_path: Child config file path.
        inherited_path: Raw inherits value from YAML.

    Returns:
        Absolute path to the inherited file.
    """
    if not isinstance(inherited_path, str) or not inherited_path:
        raise ConfigError("'inherits' must be a non-empty string")

    repo_root = config_path.parent.parent
    resolved_path = (repo_root / inherited_path).resolve()
    return resolved_path


def _merge_dicts(
    base_dict: dict[str, Any],
    override_dict: dict[str, Any],
    skip_keys: set[str] | None = None,
) -> dict[str, Any]:
    """Merge nested dictionaries recursively.

    Args:
        base_dict: Base mapping.
        override_dict: Override mapping.
        skip_keys: Keys that should not be copied from the override mapping.

    Returns:
        Merged mapping.
    """
    effective_skip_keys = skip_keys or set()
    merged = dict(base_dict)

    for key, value in override_dict.items():
        if key in effective_skip_keys:
            continue

        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_models_config(raw_config: dict[str, Any]) -> ModelsConfig:
    """Parse raw YAML data into a ModelsConfig.

    Args:
        raw_config: Raw YAML mapping.

    Returns:
        Parsed model configuration.
    """
    model_names = ModelNames(**_require_mapping(raw_config, "models"))
    request_defaults = ModelRequestDefaults(
        **_require_mapping(raw_config, "request_defaults")
    )
    perturbation_defaults = ModelRequestDefaults(
        **_require_mapping(raw_config, "perturbation_defaults")
    )
    return ModelsConfig(
        provider=_require_string(raw_config, "provider"),
        base_url=_require_string(raw_config, "base_url"),
        api_key_env=_require_string(raw_config, "api_key_env"),
        models=model_names,
        request_defaults=request_defaults,
        perturbation_defaults=perturbation_defaults,
    )


def _parse_experiment_config(raw_config: dict[str, Any]) -> ExperimentConfig:
    """Parse a fully expanded experiment config.

    Args:
        raw_config: Raw YAML mapping.

    Returns:
        Parsed experiment configuration.
    """
    benchmark = BenchmarkConfig(**_require_mapping(raw_config, "benchmark"))
    loop = LoopConfig(**_require_mapping(raw_config, "loop"))
    logging = LoggingConfig(**_require_mapping(raw_config, "logging"))
    results = ResultsConfig(**_require_mapping(raw_config, "results"))
    execution = ExecutionConfig(**_require_mapping(raw_config, "execution"))
    metrics = MetricsConfig(**_require_mapping(raw_config, "metrics"))
    conditions = _parse_conditions(_require_list(raw_config, "conditions"))

    return ExperimentConfig(
        experiment_name=_require_string(raw_config, "experiment_name"),
        description=_require_string(raw_config, "description"),
        benchmark=benchmark,
        loop=loop,
        repeats=_require_int(raw_config, "repeats"),
        logging=logging,
        results=results,
        execution=execution,
        metrics=metrics,
        conditions=conditions,
    )


def _parse_enabled_conditions(
    raw_config: dict[str, Any],
    all_conditions: list[ConditionConfig],
) -> list[ConditionConfig]:
    """Parse enabled conditions from a child config.

    Args:
        raw_config: Raw child YAML mapping.
        all_conditions: Full base condition list.

    Returns:
        Selected conditions.
    """
    enabled_config = EnabledConditionsConfig(
        **_require_mapping(raw_config, "conditions")
    )
    return _select_conditions(all_conditions, enabled_config.enabled)


def _parse_conditions(raw_conditions: list[Any]) -> list[ConditionConfig]:
    """Parse a list of condition mappings.

    Args:
        raw_conditions: Raw list from YAML.

    Returns:
        Parsed condition list.
    """
    conditions: list[ConditionConfig] = []
    for raw_condition in raw_conditions:
        if not isinstance(raw_condition, dict):
            raise ConfigError("Each condition must be a mapping")
        conditions.append(ConditionConfig(**raw_condition))
    return conditions


def _select_conditions(
    all_conditions: list[ConditionConfig],
    enabled_condition_ids: list[str],
) -> list[ConditionConfig]:
    """Select enabled conditions from all defined conditions.

    Args:
        all_conditions: Full condition list.
        enabled_condition_ids: IDs to enable.

    Returns:
        Enabled conditions in the requested order.
    """
    index = {condition.condition_id: condition for condition in all_conditions}
    selected_conditions: list[ConditionConfig] = []
    for condition_id in enabled_condition_ids:
        if condition_id not in index:
            raise ConfigError(f"Unknown condition_id in enabled list: {condition_id}")
        selected_conditions.append(index[condition_id])
    return selected_conditions


def _require_mapping(raw_config: dict[str, Any], key: str) -> dict[str, Any]:
    """Require a mapping value from config."""
    value = raw_config.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"'{key}' must be a mapping")
    return value


def _require_list(raw_config: dict[str, Any], key: str) -> list[Any]:
    """Require a list value from config."""
    value = raw_config.get(key)
    if not isinstance(value, list):
        raise ConfigError(f"'{key}' must be a list")
    return value


def _require_string(raw_config: dict[str, Any], key: str) -> str:
    """Require a string value from config."""
    value = raw_config.get(key)
    if not isinstance(value, str):
        raise ConfigError(f"'{key}' must be a string")
    return value


def _require_int(raw_config: dict[str, Any], key: str) -> int:
    """Require an integer value from config."""
    value = raw_config.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"'{key}' must be an integer")
    return value
