# stagewise_coding_agent_fragility package

Internal package map for the stage-wise coding-agent fragility scaffold.

## Modules

- `agent/`
  - `solver.py`: candidate generation
  - `failure_summary.py`: failure summarization behavior
  - `repairer.py`: repair prompting
  - `loop.py`: iterative solve/test/repair control loop

- `benchmarks/`
  - `base.py`: shared task and adapter interfaces
  - `humanevalplus.py`: HumanEval+ adapter
  - `swebench_verified.py`: SWE-bench Verified adapter (preview path)

- `execution/`
  - `sandbox.py`: local sandbox executor
  - `docker_sandbox.py`: docker-backed sandbox executor
  - `test_runner.py`: candidate+tests execution orchestration
  - `execution_result.py`: normalized execution result object

- `models/`
  - `base.py`: model protocol
  - `deepseek.py`: OpenAI-compatible model client used by current runs
  - `response_types.py`: typed model response structures

- `prompting/`
  - task / repair / failure-summary / perturbation prompt builders

- `experiments/`
  - `planner.py`: task × condition × repeat run planning
  - `runner.py`: orchestrates experiment execution
  - `metrics.py`: condition-level metrics
  - `aggregation.py`: log aggregation utilities

- `logging/`
  - `schema.py`: run-log schema
  - `writer.py`: JSON log writer
  - `reader.py`: log reader utilities

- `analysis/`
  - `tables.py`: summary table generation
  - `figures.py`: plotting data helpers
  - `cross_model.py`: cross-run/cross-model aggregation helpers
  - `case_studies.py`: case-study extraction helpers

- `cli/`
  - `run_experiment.py`
  - `summarize_results.py`
  - `generate_figures.py`
  - `generate_cross_model_figures.py`
  - `run_smoke.py`

## Usage note

Use the repository root [README](../../README.md) for setup and run commands.
This file is intentionally package-internal and does not duplicate user-facing workflow instructions.
