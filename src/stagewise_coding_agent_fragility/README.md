# Stagewise Coding Agent Fragility - Research Scaffold

This repository provides a robust, lightweight scaffold for studying **stage-wise instruction fragility** in LLM-based coding agents. It automates the "Generate -> Test -> Repair" loop and allows researchers to inject perturbations at specific interaction stages.

## Module Overview

### 1. `agent/` - Intelligence & Flow Control
- **`solver.py`**: Implementation of `CodingAgent`. Handles LLM interactions and code block extraction.
- **`loop.py`**: The **core iteration logic**. Orchestrates the Generate -> Test -> Summarize -> Repair cycle and injects perturbations at specific stages.

### 2. `benchmarks/` - Task Adapters
- **`base.py`**: Standard `Task` schema and `BenchmarkAdapter` protocol.
- **`humanevalplus.py`**: Adapter for the HumanEval+ benchmark.
- **`swebench_verified.py`**: Adapter for real-world GitHub issues from SWE-bench Verified.

### 3. `execution/` - Sandbox & Testing
- **`sandbox.py`**: Boundary for command execution (Local/Subprocess).
- **`docker_sandbox.py`**: Isolated Docker-based execution for safety and reproducibility.
- **`test_runner.py`**: Combines candidate code with test suites and parses failure reasonings.

### 4. `experiments/` - Orchestration & Metrics
- **`runner.py`**: Mass execution of (Task × Condition × Repeat) combinations.
- **`metrics.py`**: Pure functions to compute Pass Rates, Recovery Rates, and Deviation Steps.
- **`aggregation.py`**: Logic for grouping raw JSON logs by condition for analysis.

### 5. `analysis/` - Figures & Tables
- **`tables.py`**: Generation of CSV and Markdown summary tables.
- **`figures.py`**: Helper data structures for plotting.

### 6. `cli/` - Entry Points
- **`run_experiment.py`**: Start an experiment run.
- **`summarize_results.py`**: Aggregate logs into human-readable summaries.
- **`generate_figures.py`**: Generate visualization plots (PNG).

---

## Quick Start

1. **Setup Environment**:
   ```bash
   uv sync
   # Set API keys in .env
   echo 'DEEPSEEK_API_KEY="your-key"' > .env
   echo 'QWEN_API_KEY="your-key"' >> .env
   ```

2. **Execute Standard Experiment**:
   ```bash
   # Runs HumanEval+ with default DeepSeek settings
   uv run python -m stagewise_coding_agent_fragility.cli.run_experiment
   ```

3. **Analyze Results**:
   ```bash
   # Both tools auto-select the latest timestamped folder in logs/
   uv run python -m stagewise_coding_agent_fragility.cli.summarize_results
   uv run python -m stagewise_coding_agent_fragility.cli.generate_figures
   ```

---

## Decoding Parameter Ablation Studies

To test if "more creative models are more fragile to stage-wise instruction noise", the scaffold supports sweeping across the `temperature` and `top_p` space. We provide **16 pre-generated configurations** in the `configs/` directory.

### Available Configurations
- **Models**: `ds_chat` (DeepSeek), `qwen_plus` (Qwen), `qwen_turbo` (Qwen), `ds_reason` (Reasoner Baseline).
- **Decoding Levels**:
  - `deterministic`: (Temp 0.0) No randomness.
  - `conservative`: (Temp 0.3) Safe, high-probability sampling.
  - `balanced`: (Temp 0.7) Default standard.
  - `creative`: (Temp 1.0) High variance.
  - `chaotic`: (Temp 1.2) Boundary testing for hallucinations.

### Example Run (Creative Qwen):
```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_experiment \
    --experiment-config configs/humanevalplus.yaml \
    --models-config configs/models_qwen_plus_creative.yaml
```

---

## Logging & Result Management

### Timestamped Logs
Each experiment run creates a unique subdirectory in `logs/` (e.g., `logs/humanevalplus_20240325_010000/`). This prevents logs from different experiments from overwriting each other.

### Auto-Detection
The analysis tools (`summarize_results` and `generate_figures`) are equipped with **Latest-Folder Detection**. By default, they will scan the `logs/` directory and use the most recently created experiment folder. 

If you wish to analyze a specific past run, pass the exact path:
```bash
uv run python -m stagewise_coding_agent_fragility.cli.summarize_results --log-dir logs/my_old_run
```

---

## Future Feature: SWE-bench Verified

The scaffold includes preliminary support for `SWE-bench Verified` to scale fragility research to repository-level tasks.

### Status: Engineering Preview
- **Adapter**: Can successfully pull and parse SWE-bench tasks.
- **Execution**: Uses `DockerSandboxExecutor` for environment isolation.
- **Limitation**: Native SWE-bench evaluation requires a specialized test runner to handle `git apply` and project-specific `tox/pytest` environments. Currently, it serves as a demonstration of the scaffold's scalability.

### Manual Docker Cleanup:
If containers linger after a crash:
```bash
docker stop $(docker ps -q --filter "ancestor=python:3.11-slim")
docker system prune # To reclaim space
```
