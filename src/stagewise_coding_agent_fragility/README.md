# Stagewise Coding Agent Fragility - Package Guide

This directory contains the core implementation of the research scaffold for studying stage-wise instruction fragility.

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

## Quick Start (CLI)

1. **Setup Environment**:
   ```bash
   uv sync
   echo 'DEEPSEEK_API_KEY="your-key"' > .env
   ```

2. **Execute Experiment**:
   ```bash
   uv run python -m stagewise_coding_agent_fragility.cli.run_experiment
   ```

   ```bash
   uv run python -m stagewise_coding_agent_fragility.cli.summarize_results
   uv run python -m stagewise_coding_agent_fragility.cli.generate_figures
   ```

---

## 🛠 Running SWE-bench Verified

To scale your research to real-world repository issues, follow these steps:

### 1. Prerequisites
- **Docker**: You must have Docker Desktop or a Docker daemon running. The system uses `DockerSandboxExecutor` to safely run repository-level tests.
- **Image**: You usually need a base image that has Python and common build tools installed (e.g., `python:3.11-slim`).

### 2. Configuration
Create a `configs/swebench.yaml` file. Example:

```yaml
benchmark:
  provider: "swebench_verified"
  task_limit: 5  # Start small for testing

conditions:
  - id: "clean"
    injection_stage: "none"
  - id: "failure_distortion"
    injection_stage: "failure_summary"
    perturbation:
      type: "semantic_paraphrase"
```

### 3. Execution
Run the experiment by specifying the SWE-bench config:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_experiment \
    --experiment-config configs/swebench.yaml
```

---

## 🐋 Docker Lifecycle & Cleanup

The system is designed to be "Zero-Footprint" by default, but here is how to manage it manually:

### 1. Automatic Cleanup
We use the `--rm` flag in `DockerSandboxExecutor`. This ensures that **containers are automatically deleted** the moment the test execution finishes or if it times out.

### 2. Manual Emergency Stop
If you need to stop all running experiment containers immediately (e.g., if you hit Ctrl+C and some are lingering):
```bash
docker stop $(docker ps -q --filter "ancestor=python:3.11-slim")
```

### 3. Cleaning Up Images
The experiment will pull a base image (e.g., `python:3.11-slim`). If you want to reclaim disk space after your research is finished:
```bash
# List images
docker images

# Remove the specific image
docker rmi python:3.11-slim

# General system cleanup (removes all unused images/containers)
docker system prune -a
```
