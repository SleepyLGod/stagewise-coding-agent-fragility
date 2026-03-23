# Implementation Blueprint

## 1. Goal

This blueprint defines the first implementation shape of the repository.

It is intentionally scoped as a **research scaffold**, not as a full software engineering agent platform.

The scaffold should support:

- a lightweight execution-feedback-repair loop,
- controlled prompt perturbation experiments,
- strict evaluation on `HumanEval+ / EvalPlus`,
- and a small external-validity path for `SWE-bench Verified`.

It should **not** attempt, in the first version, to support:

- full repository navigation,
- rich tool ecosystems,
- long-horizon autonomous shell sessions,
- or broad benchmark integration.

---

## 2. Design Principles

### 2.1 Keep the main path narrow

The main executable path should be:

1. load a task,
2. build a prompt,
3. call a model,
4. execute tests,
5. build a failure summary,
6. call the model again for repair,
7. log everything.

### 2.2 Separate benchmark logic from agent logic

The agent loop should not know benchmark-specific internals.  
Benchmarks should expose a common task interface.

### 2.3 Make perturbation a first-class concept

Perturbation should not be handwritten inside the loop.  
It should be represented as an explicit condition with its own metadata.

### 2.4 Logs are part of the product

This is a research codebase. Logs are not an afterthought.  
If the logs are bad, the experiment is bad.

### 2.5 No submodules for v1

External repos are references, not source dependencies.

For v1:

- do **not** add `SWE-agent` as a submodule,
- do **not** add `mini-SWE-agent` as a submodule,
- do **not** add `SWE-bench` as a submodule.

Use direct implementation plus thin adapters.

---

## 3. Proposed Repository Structure

```text
stagewise-coding-agent-fragility/
├── README.md
├── pyproject.toml
├── .gitignore
├── configs/
│   ├── models.yaml
│   ├── experiment_default.yaml
│   ├── humanevalplus.yaml
│   └── swebench_verified.yaml
├── docs/
│   ├── report_en.md
│   ├── related_work_expanded.md
│   ├── workflow_and_benchmark_selection.md
│   └── implementation_blueprint.md
├── scripts/
│   ├── bootstrap.sh
│   ├── run_smoke.sh
│   ├── run_humanevalplus.sh
│   ├── run_swebench_verified_cases.sh
│   └── summarize_results.sh
├── src/
│   └── stagewise_coding_agent_fragility/
│       ├── __init__.py
│       ├── cli/
│       │   ├── run_experiment.py
│       │   ├── run_smoke.py
│       │   └── summarize_results.py
│       ├── config/
│       │   ├── loader.py
│       │   └── schema.py
│       ├── models/
│       │   ├── base.py
│       │   ├── deepseek.py
│       │   └── response_types.py
│       ├── prompting/
│       │   ├── task_prompt.py
│       │   ├── repair_prompt.py
│       │   ├── failure_summary_prompt.py
│       │   └── perturbation_prompt.py
│       ├── perturbation/
│       │   ├── types.py
│       │   ├── generator.py
│       │   ├── validator.py
│       │   └── conditions.py
│       ├── benchmarks/
│       │   ├── base.py
│       │   ├── humanevalplus.py
│       │   └── swebench_verified.py
│       ├── execution/
│       │   ├── sandbox.py
│       │   ├── test_runner.py
│       │   └── execution_result.py
│       ├── agent/
│       │   ├── solver.py
│       │   ├── repairer.py
│       │   ├── failure_summary.py
│       │   └── loop.py
│       ├── experiments/
│       │   ├── runner.py
│       │   ├── planner.py
│       │   ├── metrics.py
│       │   └── aggregation.py
│       ├── logging/
│       │   ├── schema.py
│       │   ├── writer.py
│       │   └── reader.py
│       └── analysis/
│           ├── case_studies.py
│           ├── tables.py
│           └── figures.py
├── tests/
│   ├── test_config_loader.py
│   ├── test_condition_schema.py
│   ├── test_failure_summary.py
│   ├── test_log_schema.py
│   └── test_metrics.py
├── logs/
└── results/
```

---

## 4. Module Responsibilities

## 4.1 `config/`

Purpose:

- load yaml config files,
- validate them into typed Python objects,
- expose one unified runtime config to the rest of the system.

Key rule:

- config parsing should happen once, at the CLI boundary.

## 4.2 `models/`

Purpose:

- define a provider-neutral model interface,
- implement DeepSeek calls,
- normalize request and response payloads.

Should include:

- prompt text,
- raw response text,
- token usage,
- latency,
- model name.

Key rule:

- benchmark logic must never call provider SDKs directly.

## 4.3 `prompting/`

Purpose:

- build clean task prompts,
- build repair prompts,
- build failure-summary prompts if needed,
- build perturbation-generation prompts.

Key rule:

- prompt templates should be deterministic functions of structured inputs.

## 4.4 `perturbation/`

Purpose:

- define perturbation types,
- generate perturbation candidates,
- validate or filter them,
- package them into experimental conditions.

Core perturbation types for v1:

- `semantic_paraphrase`
- `mild_simplification`

Core injection stages for v1:

- `task_prompt`
- `failure_summary`

## 4.5 `benchmarks/`

Purpose:

- expose a unified benchmark task interface,
- translate raw benchmark data into project task objects,
- isolate benchmark-specific execution details.

`humanevalplus.py` should support:

- task selection,
- function signature extraction,
- test execution hookup.

`swebench_verified.py` should support only a **small case-study path**, not a full large-scale runner in v1.

## 4.6 `execution/`

Purpose:

- run generated code safely,
- enforce timeout and isolation,
- return normalized execution results.

The executor should return:

- pass/fail,
- stdout,
- stderr,
- timeout flag,
- runtime seconds,
- structured failure info where possible.

## 4.7 `agent/`

Purpose:

- contain the research loop itself.

Suggested split:

- `solver.py`: initial code generation
- `failure_summary.py`: summarize failures into compact intermediate text
- `repairer.py`: repair code from current state plus failure signal
- `loop.py`: orchestrate rounds

The loop should not know benchmark internals.  
It should only consume:

- a task object,
- a model client,
- a test runner,
- a condition object.

## 4.8 `experiments/`

Purpose:

- define experiment conditions,
- iterate over tasks and conditions,
- compute aggregate metrics,
- write result tables.

This layer owns:

- run IDs,
- condition IDs,
- sampling strategy,
- task subsets,
- repeat counts.

## 4.9 `logging/`

Purpose:

- define the log schema,
- write logs per run,
- reload logs for later analysis.

Key rule:

- all research claims should be derivable from logs plus config.

## 4.10 `analysis/`

Purpose:

- build tables,
- generate figures,
- extract case studies.

This layer should never rerun experiments.  
It should operate on saved logs and saved result summaries only.

---

## 5. Core Data Flow

The main `HumanEval+` experiment should follow this path:

```text
Benchmark task
  -> condition builder
  -> task prompt construction
  -> optional perturbation injection
  -> initial solve
  -> code execution / tests
  -> failure parsing
  -> failure summary construction
  -> optional failure-summary perturbation
  -> repair prompt construction
  -> repair solve
  -> repeat until success or round limit
  -> log run
  -> aggregate metrics
```

The `SWE-bench Verified` path should be structurally similar, but should remain isolated behind its benchmark adapter and used only for a small case-study flow.

---

## 6. Main Runtime Objects

The following logical objects should exist, even if the exact Python class names differ.

## 6.1 `Task`

Represents one benchmark task.

Fields:

- `task_id`
- `benchmark_name`
- `prompt`
- `entry_point`
- `metadata`
- `reference_tests` or benchmark execution handle

## 6.2 `Condition`

Represents one experiment condition.

Fields:

- `condition_id`
- `benchmark_name`
- `injection_stage`
- `perturbation_type`
- `perturbation_strength`
- `repeat_index`
- `model_name`

## 6.3 `RunContext`

Represents one concrete run.

Fields:

- `run_id`
- `task`
- `condition`
- `max_rounds`
- `timestamp`

## 6.4 `ExecutionResult`

Represents one test execution result.

Fields:

- `passed`
- `stdout`
- `stderr`
- `timeout`
- `runtime_seconds`
- `raw_failure`
- `parsed_failure`

## 6.5 `RoundRecord`

Represents one loop iteration.

Fields:

- `round_index`
- `task_prompt_text`
- `perturbed_task_prompt_text`
- `generated_code`
- `execution_result`
- `failure_summary_text`
- `perturbed_failure_summary_text`
- `repair_prompt_text`
- `model_response`
- `token_usage`
- `latency_seconds`

---

## 7. Log Schema

Each run should produce one JSON log file.

Recommended layout:

```json
{
  "run_id": "humanevalplus__task_012__task_prompt__semantic_paraphrase__r0",
  "benchmark": "humanevalplus",
  "task_id": "HumanEval/12",
  "condition": {
    "injection_stage": "task_prompt",
    "perturbation_type": "semantic_paraphrase",
    "perturbation_strength": "default",
    "repeat_index": 0,
    "model_name": "deepseek-reasoner"
  },
  "loop_config": {
    "max_rounds": 3
  },
  "rounds": [],
  "final_result": {
    "success": false,
    "num_rounds_executed": 3,
    "first_deviation_step": 1,
    "recovered": false,
    "failure_type": "wrong_fix"
  },
  "cost": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "timing": {
    "wall_clock_seconds": 0.0
  }
}
```

### Required top-level fields

- `run_id`
- `benchmark`
- `task_id`
- `condition`
- `rounds`
- `final_result`
- `cost`
- `timing`

### Required per-round fields

- `round_index`
- `task_prompt_text`
- `generated_code`
- `execution_result`
- `failure_summary_text`
- `model_name`
- `token_usage`
- `latency_seconds`

### Optional but highly recommended fields

- `perturbed_task_prompt_text`
- `perturbed_failure_summary_text`
- `raw_model_response`
- `parsed_failure`
- `repair_prompt_text`

---

## 8. Metrics Schema

The aggregation layer should compute at least:

- `final_pass_rate`
- `average_repair_rounds`
- `average_total_tokens`
- `average_wall_clock_seconds`
- `recovery_rate`
- `failure_type_distribution`

### Definitions

`final_pass_rate`
: fraction of runs that end in success.

`average_repair_rounds`
: average number of executed rounds, optionally split by successful and failed runs.

`recovery_rate`
: among runs that deviate from the clean path, fraction that still end in success.

`first_deviation_step`
: earliest round at which the perturbed run diverges materially from the clean reference.

`failure_type_distribution`
: normalized distribution over labels such as:
- `task_misunderstanding`
- `wrong_fix`
- `test_misinterpretation`
- `stuck_loop`

---

## 9. Experiment Condition Schema

Conditions should be explicit, not embedded in filenames only.

Recommended schema:

```yaml
benchmark: humanevalplus
task_subset: humanevalplus_main_20
model_name: deepseek-reasoner
max_rounds: 3
repeats: 2

conditions:
  - condition_id: clean
    injection_stage: none
    perturbation_type: none
    perturbation_strength: none

  - condition_id: task_paraphrase
    injection_stage: task_prompt
    perturbation_type: semantic_paraphrase
    perturbation_strength: default

  - condition_id: task_simplification
    injection_stage: task_prompt
    perturbation_type: mild_simplification
    perturbation_strength: default

  - condition_id: failure_paraphrase
    injection_stage: failure_summary
    perturbation_type: semantic_paraphrase
    perturbation_strength: default

  - condition_id: failure_simplification
    injection_stage: failure_summary
    perturbation_type: mild_simplification
    perturbation_strength: default
```

### v1 condition policy

Do not support multiple simultaneous perturbation stages in v1.

One condition should modify:

- either `task_prompt`,
- or `failure_summary`,
- or nothing.

This keeps attribution clean.

---

## 10. Suggested CLI Surface

The system only needs a small CLI in v1.

## 10.1 `run_smoke`

Purpose:

- run 1 to 3 tasks quickly,
- validate execution,
- validate logs.

Example shape:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_smoke \
  --config configs/experiment_default.yaml
```

## 10.2 `run_experiment`

Purpose:

- run one benchmark subset under one config.

Example shape:

```bash
uv run python -m stagewise_coding_agent_fragility.cli.run_experiment \
  --config configs/humanevalplus.yaml
```

## 10.3 `summarize_results`

Purpose:

- aggregate logs,
- generate CSV and markdown tables,
- produce a case-study shortlist.

---

## 11. How Benchmarks Should Be Integrated

## 11.1 HumanEval+ / EvalPlus

Integration strategy:

- treat it as the main benchmark adapter,
- use a small selected task subset,
- keep the benchmark interface thin,
- avoid leaking EvalPlus-specific assumptions into the loop.

## 11.2 SWE-bench Verified

Integration strategy:

- keep it isolated behind a separate adapter,
- support only a tiny case-study subset,
- do not optimize the whole codebase around this path,
- do not let its infra complexity define the main architecture.

---

## 12. Submodule Decision

Current recommendation:

> Do not use submodules in v1.

### Why

- The project does not intend to modify `SWE-agent` or `mini-SWE-agent`.
- Those repos are workflow references, not code dependencies.
- Submodules introduce versioning and onboarding overhead.
- They complicate clone, CI, and reproducibility for little benefit at this stage.

### What to do instead

- document those repos,
- cite them,
- and implement a narrow scaffold locally.

### When to reconsider

Reconsider submodules only if:

- a benchmark harness absolutely must be pinned as a repo snapshot,
- or the project later decides to extend an external repo directly.

That is not the current situation.

---

## 13. Suggested Build Order

The code should be built in this order:

1. `config/`
2. `logging/schema.py`
3. `execution/test_runner.py`
4. `benchmarks/humanevalplus.py`
5. `models/deepseek.py`
6. `prompting/task_prompt.py`
7. `agent/solver.py`
8. `agent/failure_summary.py`
9. `agent/repairer.py`
10. `agent/loop.py`
11. `experiments/runner.py`
12. `experiments/aggregation.py`
13. `analysis/`

Reason:

- execution and logging are the foundation,
- then the benchmark adapter,
- then model I/O,
- then the loop,
- then experiment orchestration,
- then analysis.

---

## 14. Minimal v1 Deliverable

The first real implementation milestone should be:

- one working `HumanEval+` task,
- one clean run,
- one task-prompt perturbation run,
- one failure-summary perturbation run,
- valid JSON logs,
- and one summary table.

That is the correct starting point.

Everything else should be treated as follow-on work.
