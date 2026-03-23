# Detailed Implementation Plan

## 1. Purpose

This document defines the concrete implementation plan for the repository from the current state forward.

It is not a general roadmap. It is a build plan for the actual codebase.

The plan is designed around the current project requirement:

> Build a lightweight execution-feedback-repair research scaffold for stage-wise prompt fragility experiments, grounded in real software engineering agent workflows, but implemented in a controlled and lightweight way.

The plan follows four constraints:

- clarity over cleverness,
- explicitness over implicitness,
- narrow scope before broad scope,
- and end-to-end correctness before expansion.

---

## 2. Current State

As of now, the repository already has the following working pieces:

### 2.1 Environment

- `uv` is being used as the project environment manager
- the project has a local `.venv`
- the project has a `uv.lock`
- `uv sync --dev` succeeds

### 2.2 Config system

The project can already:

- load model configuration from YAML
- load experiment configuration from YAML
- resolve inherited experiment config files
- select enabled experiment conditions
- expose typed config objects

### 2.3 Logging schema

The repository already contains typed run-log schemas for:

- token usage,
- execution result records,
- round records,
- condition records,
- final result records,
- run-level records.

### 2.4 Minimal CLI

The repository already has a smoke CLI that:

- loads config,
- validates the config shape,
- prints a compact summary.

### 2.5 Tests

Current tests validate:

- config loading,
- inherited experiment config parsing,
- log schema construction.

This means the project already has a stable foundation for:

- configuration,
- typing boundaries,
- and minimal CLI entry.

What the repository does **not** have yet:

- no model client,
- no `.env` loading,
- no benchmark adapter,
- no execution layer,
- no agent loop,
- no metrics aggregation,
- no result writer.

---

## 3. What Must Be Built Next

From first principles, the next missing capability is not “prompting” and not “agent intelligence”.

The next missing capability is:

> Given a task and a candidate code string, can the system execute the code, run the tests, and return a structured failure signal?

Without that, there is no feedback loop.

Therefore, the next major implementation block is:

- **Execution Layer**

Only after that should the project move to:

- **Benchmark Adapter**
- **Model Client**
- **Agent Loop**

This order matters.

---

## 4. High-Level Phase Order

The implementation should proceed in the following order:

1. `.env` and runtime settings policy
2. execution layer
3. benchmark adapter for `HumanEval+ / EvalPlus`
4. model client
5. prompt builders
6. agent loop
7. experiment runner
8. result aggregation
9. case-study path for `SWE-bench Verified`

This is the shortest correct path.

---

## 5. Phase 1: Environment Variable And Runtime Policy

## 5.1 Goal

Make runtime configuration explicit and deterministic.

The immediate question here is:

> How should the code read the DeepSeek API key?

The correct answer is:

- the code should read the configured environment variable name from `models.yaml`
- the actual key value should come from the process environment
- `.env` loading should be explicit, not silently assumed

## 5.2 Design Decision

The repository should support this model:

- `models.yaml` declares `api_key_env: DEEPSEEK_API_KEY`
- code reads `os.environ["DEEPSEEK_API_KEY"]`
- if that variable is missing, the code raises an error immediately

Optional support for `.env` file loading may be added, but if added, it must be explicit and local:

- either the CLI loads `.env`
- or a dedicated runtime helper loads it

The code should not pretend that `.env` exists if it has not been loaded.

## 5.3 Files To Add Or Modify

- `src/.../runtime/env.py`
- maybe `pyproject.toml` if an explicit `.env` helper library is added

## 5.4 Acceptance Criteria

- if the required env variable exists, the runtime can read it
- if it does not exist, the program raises a specific exception
- no silent fallback
- no hidden global side effect

---

## 6. Phase 2: Execution Layer

## 6.1 Goal

The execution layer should do one thing:

> run generated code against a task-specific test interface and return a normalized execution result.

## 6.2 Scope

The execution layer is **not** responsible for:

- prompt building,
- model calls,
- condition selection,
- benchmark sampling,
- metrics aggregation.

It is responsible for:

- executing code,
- enforcing timeout,
- capturing stdout and stderr,
- detecting pass/fail,
- normalizing the failure result.

## 6.3 First Version Architecture

Files to implement:

- `src/.../execution/execution_result.py`
- `src/.../execution/sandbox.py`
- `src/.../execution/test_runner.py`

### `execution_result.py`

This file should define the typed runtime result for one execution attempt.

Suggested fields:

- `passed: bool`
- `stdout: str`
- `stderr: str`
- `timeout: bool`
- `runtime_seconds: float`
- `raw_failure: str`
- `parsed_failure: dict[str, Any] | None`

### `sandbox.py`

This file should define the execution boundary.

For v1, this can be deliberately simple.

Suggested shape:

- `SandboxExecutor` protocol or base class
- `LocalSandboxExecutor` concrete implementation

Even if Docker is not implemented yet, there should still be a stable abstraction boundary.

### `test_runner.py`

This file should expose a runner that:

- accepts a task object and generated code
- delegates execution to the sandbox boundary
- returns an `ExecutionResult`

## 6.4 First Version Constraints

For the first implementation:

- do not build a generic multi-benchmark executor
- do not build a Docker orchestration system yet
- do not add compatibility layers
- do not add retry logic

The first version should only aim to support the controlled `HumanEval+` path.

## 6.5 Acceptance Criteria

The execution layer is done when:

- one candidate code string can be executed against one task
- the system returns a typed result
- timeout is represented explicitly
- failure text is preserved
- stdout and stderr are captured

---

## 7. Phase 3: Benchmark Adapter For HumanEval+ / EvalPlus

## 7.1 Goal

Give the system a stable source of tasks and test interfaces.

## 7.2 Scope

Files to implement:

- `src/.../benchmarks/base.py`
- `src/.../benchmarks/humanevalplus.py`

### `base.py`

Should define the benchmark-facing task interface.

Suggested task object:

- `task_id`
- `benchmark_name`
- `prompt`
- `entry_point`
- `metadata`
- benchmark-specific execution handle if needed

### `humanevalplus.py`

Should:

- load the benchmark tasks or subset
- adapt raw benchmark records into project `Task` objects
- expose a simple iteration API

## 7.3 Design Constraint

The benchmark adapter should not know about perturbation conditions.

It should only know:

- what the task is
- how to describe it
- how to hand it to the runner

## 7.4 Acceptance Criteria

This phase is done when:

- a fixed task subset can be loaded
- one task can be printed in a normalized form
- one task can be passed to the execution layer

---

## 8. Phase 4: Model Client

## 8.1 Goal

Provide a minimal model interface for code generation and perturbation generation.

## 8.2 Scope

Files to implement:

- `src/.../models/base.py`
- `src/.../models/deepseek.py`
- `src/.../models/response_types.py`

## 8.3 Required Behavior

The model client should:

- accept prompt text
- submit a request
- return:
  - model name
  - raw text
  - token usage
  - latency

## 8.4 Non-Goals

Do not implement:

- tool calling
- structured output frameworks
- multiple providers
- fallback model chains

## 8.5 Acceptance Criteria

This phase is done when:

- one prompt can be sent to DeepSeek
- the raw response can be captured
- token usage is available in a normalized structure

---

## 9. Phase 5: Prompt Builders

## 9.1 Goal

Make prompt construction explicit and deterministic.

## 9.2 Scope

Files to implement:

- `src/.../prompting/task_prompt.py`
- `src/.../prompting/repair_prompt.py`
- `src/.../prompting/failure_summary_prompt.py`
- `src/.../prompting/perturbation_prompt.py`

## 9.3 Design Rule

Each prompt builder should do one thing only.

Examples:

- `build_task_prompt(task: Task) -> str`
- `build_repair_prompt(task: Task, code: str, failure_summary: str) -> str`
- `build_perturbation_prompt(text: str, perturbation_type: str) -> str`

## 9.4 Acceptance Criteria

This phase is done when:

- prompt text is no longer assembled inline in agent code
- every prompt has a dedicated builder function

---

## 10. Phase 6: Agent Loop

## 10.1 Goal

Implement the actual execution-feedback-repair loop.

## 10.2 Scope

Files to implement:

- `src/.../agent/solver.py`
- `src/.../agent/failure_summary.py`
- `src/.../agent/repairer.py`
- `src/.../agent/loop.py`

### `solver.py`

Responsible only for initial code generation.

### `failure_summary.py`

Responsible only for turning execution results into a compact intermediate summary.

In v1, this should be **rule-based**, not LLM-based.

### `repairer.py`

Responsible only for repair generation from current code plus summary.

### `loop.py`

Responsible only for orchestration:

- solve
- execute
- summarize
- repair
- repeat
- record rounds

## 10.3 Acceptance Criteria

This phase is done when:

- one task can complete one clean full loop
- each round is logged
- the loop stops on success or round limit

---

## 11. Phase 7: Perturbation And Conditions

## 11.1 Goal

Make perturbation an explicit experimental variable.

## 11.2 Scope

Files to implement:

- `src/.../perturbation/types.py`
- `src/.../perturbation/generator.py`
- `src/.../perturbation/validator.py`
- `src/.../perturbation/conditions.py`

## 11.3 First Version Scope

Only support:

- `semantic_paraphrase`
- `mild_simplification`

Only support stage injection at:

- `task_prompt`
- `failure_summary`

## 11.4 Acceptance Criteria

This phase is done when:

- clean runs and perturbed runs can be selected by config
- perturbation metadata is visible in the log
- conditions can be switched without editing code

---

## 12. Phase 8: Experiment Runner

## 12.1 Goal

Run task subsets under multiple conditions and write run logs consistently.

## 12.2 Scope

Files to implement:

- `src/.../experiments/runner.py`
- `src/.../experiments/planner.py`

## 12.3 Responsibilities

The experiment runner should:

- load config
- load task subset
- iterate through tasks
- iterate through conditions
- call the loop
- write one log file per run

## 12.4 Acceptance Criteria

This phase is done when:

- a small experiment subset can run end-to-end
- log files appear in the expected location
- run IDs and condition IDs are stable and deterministic

---

## 13. Phase 9: Metrics And Aggregation

## 13.1 Goal

Convert logs into result tables.

## 13.2 Scope

Files to implement:

- `src/.../experiments/metrics.py`
- `src/.../experiments/aggregation.py`
- `src/.../analysis/tables.py`

## 13.3 Required Metrics

Must compute:

- `final_pass_rate`
- `average_repair_rounds`
- `average_total_tokens`
- `recovery_rate`
- `failure_type_distribution`

## 13.4 Acceptance Criteria

This phase is done when:

- one command can turn logs into a summary table
- the summary is consistent with the raw logs

---

## 14. Phase 10: Case Study Path For SWE-bench Verified

## 14.1 Goal

Add a narrow external-validity path without distorting the main architecture.

## 14.2 Scope

Files to implement:

- `src/.../benchmarks/swebench_verified.py`
- small extension in runner logic

## 14.3 Constraint

This is not a second main path.

It should support only:

- a very small number of cases
- a case-study workflow
- limited experimental conditions

## 14.4 Acceptance Criteria

This phase is done when:

- 3 to 5 cases can be executed
- their outputs can be logged with the same schema

---

## 15. Immediate Next Step

The immediate next step should be:

> implement the execution layer

Specifically:

1. `execution/execution_result.py`
2. `execution/sandbox.py`
3. `execution/test_runner.py`

This is the correct next step because the project already has:

- config,
- log schema,
- and a smoke CLI.

It does not yet have:

- code execution,
- test feedback,
- or any real loop signal.

Until that exists, the rest of the system cannot be meaningfully integrated.

---

## 16. Definition Of Done For The Next Milestone

The next milestone is complete when all of the following are true:

- the project can load one config through `uv run`
- the project can load one `HumanEval+` task
- the project can execute one candidate code string
- the project can return a typed execution result
- the project can preserve failure details in a stable structure

That is the smallest meaningful end-to-end execution milestone.
