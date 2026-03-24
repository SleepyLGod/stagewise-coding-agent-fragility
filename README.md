# stagewise-coding-agent-fragility

Study of stage-wise instruction fragility in lightweight coding agents.

## Overview

This repository is organized around a focused research question:

> How do approximately meaning-preserving prompt perturbations affect a multi-step coding agent across different stages of a test-repair loop?

The project studies a lightweight coding workflow instead of a heavy agent framework. The intended loop is:

1. Read a programming task
2. Generate code
3. Run tests
4. Build or perturb a failure summary
5. Repair the code
6. Repeat until success or a fixed round limit

The current documentation is centered in [`docs/`](./docs):

- [`docs/report_en.md`](./docs/report_en.md): main English report
- [`docs/related_work_expanded.md`](./docs/related_work_expanded.md): copied source document with expanded related work

## Repository Structure

```text
stagewise-coding-agent-fragility/
├── README.md
├── .gitignore
├── pyproject.toml
├── configs/
├── docs/
├── logs/
├── results/
├── scripts/
├── src/
│   └── stagewise_coding_agent_fragility/
└── tests/
```

## How to Run

Before running, ensure your API keys are set in a `.env` file at the project root:

```env
DEEPSEEK_API_KEY="your-api-key-here"
```

### 1. Run an Experiment

Run a configured experiment using the `run_experiment` CLI:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_experiment \
    --experiment-config configs/humanevalplus.yaml \
    --models-config configs/models.yaml
```

This will execute the test-repair loop across all tasks and conditions, writing JSON logs to the `logs/` directory.

### 2. Summarize Results

Once an experiment completes, aggregate the JSON logs into CSV and Markdown tables:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.summarize_results \
    --log-dir logs \
    --output-dir results
```

This will output `summary.csv` and `summary.md` to the `results/` directory, showing pass rates, repair rounds, and token usage by condition.

### 3. Generate Visualizations

To render the final pass rate, recovery rate, and survival curve charts from the logs:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.generate_figures \
    --log-dir logs \
    --output-dir results/figures
```

This will save PNG plots in the `results/figures/` directory.

### 4. Run Tests

To verify the project is working as expected, run the test suite:

```bash
uv run python -m pytest tests/ -v
```

## Notes

- `logs/` is for local experiment output and should not be committed by default.
- `results/` is intended for curated tables, figures, and case studies.
- `docs/related_work_expanded.md` is copied from the project workspace as requested.
