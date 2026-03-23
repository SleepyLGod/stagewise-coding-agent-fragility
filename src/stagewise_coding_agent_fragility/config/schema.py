"""Typed configuration schema for experiment and model settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelRequestDefaults:
    """Default request options for one model usage mode."""

    temperature: float
    top_p: float
    max_tokens: int
    timeout_seconds: int


@dataclass(frozen=True)
class ModelNames:
    """Configured model names for the project."""

    solver_primary: str
    perturbation_generator: str
    optional_secondary: str


@dataclass(frozen=True)
class ModelsConfig:
    """Configuration for model provider access."""

    provider: str
    base_url: str
    api_key_env: str
    models: ModelNames
    request_defaults: ModelRequestDefaults
    perturbation_defaults: ModelRequestDefaults


@dataclass(frozen=True)
class BenchmarkConfig:
    """Benchmark-specific runtime configuration."""

    name: str
    dataset_source: str
    task_subset: str
    selection_strategy: str
    task_limit: int


@dataclass(frozen=True)
class LoopConfig:
    """Configuration for the repair loop."""

    max_rounds: int
    use_rule_based_failure_summary: bool


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for log writing."""

    output_dir: str
    save_raw_model_response: bool
    save_prompts: bool


@dataclass(frozen=True)
class ResultsConfig:
    """Configuration for result summaries."""

    output_dir: str
    write_summary_csv: bool
    write_markdown_summary: bool


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for code execution."""

    timeout_seconds: int
    sandbox_mode: str
    capture_stdout: bool
    capture_stderr: bool


@dataclass(frozen=True)
class MetricsConfig:
    """Configuration for aggregate metrics."""

    primary: list[str]
    secondary: list[str]


@dataclass(frozen=True)
class ConditionConfig:
    """One experiment condition definition."""

    condition_id: str
    injection_stage: str
    perturbation_type: str
    perturbation_strength: str


@dataclass(frozen=True)
class EnabledConditionsConfig:
    """References to enabled condition IDs."""

    enabled: list[str]


@dataclass(frozen=True)
class ExperimentConfig:
    """Top-level experiment configuration."""

    experiment_name: str
    description: str
    benchmark: BenchmarkConfig
    loop: LoopConfig
    repeats: int
    logging: LoggingConfig
    results: ResultsConfig
    execution: ExecutionConfig
    metrics: MetricsConfig
    conditions: list[ConditionConfig]


@dataclass(frozen=True)
class SmokeSummary:
    """A compact representation of loaded configuration for smoke output."""

    experiment_name: str
    benchmark_name: str
    task_subset: str
    max_rounds: int
    repeats: int
    enabled_condition_ids: list[str]
