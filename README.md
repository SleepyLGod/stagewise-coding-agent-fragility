# stagewise-coding-agent-fragility

Controlled study scaffold for **stage-wise prompt fragility** in lightweight coding agents.

## What this repo does

This project evaluates a `solve -> test -> summarize -> repair` loop under
stage-specific perturbations.

Primary use case:
- benchmark: HumanEval+ / EvalPlus
- perturbation stages: task prompt, failure summary
- outputs: run logs, condition summaries, analysis figures

## Quick start

1. Install dependencies:

```bash
uv sync --dev
```

2. Set API key(s) in `.env`:

```env
DEEPSEEK_API_KEY="..."
QWEN_API_KEY="..."
```

3. Run one experiment:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_experiment \
  --experiment-config configs/humanevalplus.yaml \
  --models-config configs/models.yaml
```

4. Summarize one run:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.summarize_results \
  --log-dir logs/humanevalplus_stagewise_fragility_<timestamp>
```

5. Generate figures for one run:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.generate_figures \
  --log-dir logs/humanevalplus_stagewise_fragility_<timestamp>
```

6. Generate cross-model figures from multiple runs:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.generate_cross_model_figures \
  --manifest configs/cross_model_runs.yaml \
  --output-dir results/cross_model
```

## Run commands

Smoke check (small run):

```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_smoke \
  --experiment-config configs/humanevalplus.yaml \
  --models-config configs/models.yaml
```

Summarize and plot the latest run under `logs/`:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.summarize_results \
  --log-dir logs \
  --latest

uv run python -m stagewise_coding_agent_fragility.cli.generate_figures \
  --log-dir logs \
  --latest
```

Run tests:

```bash
uv run pytest -v
```

## Repository layout

```text
configs/                     Experiment/model configs
src/stagewise_coding_agent_fragility/
  agent/                     Solve-repair loop logic
  benchmarks/                HumanEval+ and SWE-bench adapters
  execution/                 Sandbox and test execution
  experiments/               Planning, runner, metrics, aggregation
  logging/                   Log schema, reader, writer
  analysis/                  Table and figure generation helpers
  cli/                       Entry-point commands
scripts/                     Local helper scripts
docs/                        Curated project documents
tests/                       Test suite
```

## Documentation

Only core docs are kept in this repo:
- `docs/report_en.md`
- `docs/multi_model_report_en.md`
- `docs/workflow_and_benchmark_selection.md`
- `docs/related_work_expanded.md`

## Notes

- `logs/` and `results/` are local artifacts and ignored by default.
- `scripts/gen_results.sh` is a convenience helper; prefer CLI commands for reproducible runs.
