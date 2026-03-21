# Workflow And Benchmark Selection

## 1. Purpose Of This Document

This document answers four concrete questions:

1. What workflow do we actually want for this project?
2. Which existing agent systems and benchmarks are relevant?
3. Which ones fit the project requirements, and which ones require adaptation?
4. What is the final recommended combination for implementation and reporting?

The document deliberately separates:

- **Source-backed facts**: what the official paper, README, or documentation explicitly states
- **Project abstraction**: what we derive from those sources for the current research design

This separation is necessary. It prevents us from presenting a custom research scaffold as if it were a directly inherited standard workflow from an existing paper or product.

---

## 2. What Workflow We Actually Need

The project does **not** need:

- a fictional coding agent loop invented without grounding,
- a full reproduction of a production-level repository agent,
- or a heavy infrastructure stack that dominates the project.

The project **does** need a workflow that satisfies the following requirements:

- **Real grounding**: it should be clearly connected to real software engineering agent systems
- **Controlled design**: it should support stage-wise prompt fragility experiments
- **Executability**: the main experiment should remain lightweight and tractable
- **External validity**: the project should still touch real GitHub issue settings
- **Interpretability**: each step, feedback signal, and deviation point should be loggable

Therefore, the right target is:

> a lightweight abstraction of the iterative execution-feedback-repair core of real software engineering agents.

That wording is important. It is more accurate than claiming that the project implements a full repository-level software engineering agent workflow.

---

## 3. Workflow Grounding

The current best grounding is:

- **Primary workflow grounding: mini-SWE-agent**
- **Repository-level semantic background: SWE-agent**

This ordering is intentional.

The latest official SWE-agent architecture documentation explicitly states that:

- `SWE-agent has been superseded by mini-swe-agent`
- `SWE-agent is now in maintenance-only mode`

Official source:

- [SWE-agent latest architecture docs](https://swe-agent.com/latest/background/architecture/)

That means the current ecosystem itself points toward mini-SWE-agent as the simpler default reference, while SWE-agent remains the canonical heavier repository-level background system.

---

## 4. Primary Workflow Grounding: mini-SWE-agent

## 4.1 Source-backed facts

The official `mini-SWE-agent` README explicitly states that:

- it **does not have any tools other than bash**
- it **has a completely linear history**
- it executes actions with `subprocess.run`
- each action is **completely independent**
- it is suitable for simple control flow, stable sandboxing, and benchmark evaluation
- it can solve GitHub issues

Official source:

- [mini-SWE-agent GitHub README](https://github.com/SWE-agent/mini-swe-agent)

The README also explicitly contrasts it with `SWE-agent`:

- if you want simpler control flow, faster and more stable sandboxing, and easier benchmark evaluation, use `mini-SWE-agent`
- if you want more advanced tool experiments or history processors, use `SWE-agent`

## 4.2 What workflow this implies

Without over-claiming, the source-backed mini-SWE-agent workflow can be summarized as:

1. receive a task or issue,
2. let the model generate the next action from the current history,
3. execute that action through bash / `subprocess.run`,
4. append the resulting output to a linear history,
5. continue until the run terminates.

## 4.3 Why it fits this project

mini-SWE-agent is the best primary workflow reference for this project because:

- it is real, not fictional,
- it is light enough to abstract,
- it has a simple control flow,
- it is naturally trajectory-friendly,
- and it aligns with benchmark-oriented evaluation rather than full product complexity.

## 4.4 What it does **not** give us directly

mini-SWE-agent does **not** directly provide:

- explicit `Task Prompt / Failure Summary / Revision Prompt` experimental stages,
- a built-in stage-wise fragility design,
- or a research-oriented prompt injection framework.

Those must still be implemented by us.

## 4.5 How we should use it

mini-SWE-agent should be used as:

- the **primary workflow grounding**
- the **control-flow reference**
- the **trajectory and logging style reference**
- the **engineering style reference for a lightweight scaffold**

It should **not** be imported into the project as a direct, unchanged main system.

---

## 5. Repository-Level Background: SWE-agent

## 5.1 Source-backed facts

The `SWE-agent` paper, README, and documentation explicitly describe a repository-level software engineering agent setting:

- it addresses issues in **real GitHub repositories**
- it uses an **Agent-Computer Interface (ACI)**
- the ACI is designed to help the model:
  - navigate repositories,
  - inspect code,
  - edit code,
  - execute tests and other programs
- the end goal is to produce a patch that resolves the issue

Official sources:

- [SWE-agent paper (arXiv:2405.15793)](https://arxiv.org/abs/2405.15793)
- [SWE-agent GitHub README](https://github.com/SWE-agent/SWE-agent)
- [SWE-agent ACI docs](https://swe-agent.com/0.7/background/aci/)
- [SWE-agent latest architecture docs](https://swe-agent.com/latest/background/architecture/)

The ACI documentation further states that it provides:

- edit commands with linter checks,
- a dedicated file viewer,
- dedicated directory-level search support,
- and an interaction pattern where the agent relies on command feedback to continue reasoning.

The architecture documentation also makes clear that:

- the runtime initializes an environment,
- the default path launches a Docker container and shell session,
- model actions are executed inside that session,
- and history may be compressed when needed.

## 5.2 What workflow this implies

The source-backed SWE-agent workflow can be summarized as:

1. receive a repository and an issue,
2. inspect and navigate the repository,
3. search and edit code,
4. run tests or other commands,
5. use execution feedback to continue modification,
6. output a final patch / repair result.

## 5.3 Why it matters to this project

SWE-agent matters because it gives the project a strong real-world semantic anchor:

- repository-level issue resolution,
- interactive execution feedback,
- code editing in context,
- and patch-oriented repair.

## 5.4 Why it should **not** be our main template

SWE-agent is not the right direct implementation template for the main experiment because:

- it is heavier,
- it depends on a richer agent-computer interface,
- it assumes a longer-lived environment and shell session,
- and it is closer to a complete repository-level agent system than to a compact experimental scaffold.

## 5.5 How we should use it

SWE-agent should be used as:

- the **repository-level background reference**
- the **semantic justification for issue-resolution workflows**
- the **external-validity background for real software engineering agents**

It should not be presented as the system we are faithfully reproducing.

---

## 6. Main Benchmark: HumanEval+ / EvalPlus

## 6.1 Source-backed facts

The official `EvalPlus` README explicitly states that:

- it is a **rigorous evaluation framework for LLM4Code**
- `HumanEval+` contains **80x more tests than the original HumanEval**
- its packages, images, and tools support safer and easier code evaluation

Official sources:

- [EvalPlus GitHub](https://github.com/evalplus/evalplus)
- [HumanEval+ on Hugging Face](https://huggingface.co/datasets/evalplus/humanevalplus)

The Hugging Face dataset page currently shows:

- `HumanEval+` has **164 tasks**

## 6.2 What the benchmark actually is

HumanEval+ is a function-level coding benchmark:

- a function task is provided,
- the model produces code,
- and correctness is verified with a stricter test suite.

It is **not** a repository-level issue-fixing benchmark.

## 6.3 What workflow it supports

By itself, the benchmark supports a simple generation-and-test workflow:

1. read a task,
2. generate code,
3. run tests,
4. determine pass or fail.

If we build a repair loop on top of it, then the workflow becomes:

1. read the task,
2. generate code,
3. run tests,
4. construct a failure summary,
5. revise the code,
6. repeat.

That second, multi-step workflow is **our project abstraction**, not something HumanEval+ provides natively.

## 6.4 Why it fits the project

HumanEval+ / EvalPlus is the right main benchmark because it is:

- light,
- strict,
- controlled,
- relatively easy to reproduce,
- and well suited for stage-wise perturbation experiments.

## 6.5 What it does **not** cover

It does not provide:

- real GitHub issues,
- repository navigation,
- localization in large codebases,
- cross-file editing,
- or patch validation in a real repository workflow.

Therefore, the main claims of the project should be framed as applying to:

> lightweight test-driven execution-feedback-repair loops

rather than to all repository-level software engineering agents.

---

## 7. Real-World External Validity Benchmark: SWE-bench Verified

## 7.1 Source-backed facts

The official `SWE-bench` README explicitly states that:

- SWE-bench evaluates language models on **real world software issues collected from GitHub**
- the task is to generate a patch for a given codebase and issue
- `SWE-bench Verified` is a **500-task subset**
- these are tasks that **real software engineers confirmed are solvable**
- evaluation is Docker-based
- evaluation is **resource intensive**
- the recommended environment includes at least:
  - 120GB free storage
  - 16GB RAM
  - 8 CPU cores

Official source:

- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)

## 7.2 What the benchmark actually is

SWE-bench Verified is a real repository-level issue-fixing benchmark:

- real repository,
- real issue,
- real patch-style repair task,
- validated under a stronger notion of practical solvability than a random small sample.

## 7.3 Why it is the right external-validity choice

If the project only intends to run **3 to 5 real-world cases**, Verified is the stronger default than Lite because the benchmark itself gives a clearer solvability signal.

That makes it a better small-sample case-study choice.

## 7.4 Why it cannot be the main benchmark

It is too heavy for the main controlled experiment because:

- the environment is expensive,
- the evaluation stack is complex,
- the tasks are repository-level,
- and infrastructure noise can easily dominate the prompt-fragility question.

## 7.5 How we should use it

SWE-bench Verified should be used as:

- the **preferred external-validity case-study benchmark**
- a **small real-world validation section**
- a **3 to 5 instance qualitative or small-sample extension**

---

## 8. Backup Real-World Benchmark: SWE-bench Lite

## 8.1 Source-backed facts

The official SWE-bench repository also provides:

- `SWE-bench Lite`

It belongs to the same real GitHub issue-fixing benchmark family, but the repository does not present it with the same explicit “real software engineers confirmed are solvable” phrasing used for Verified.

Official source:

- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)

## 8.2 How it should be positioned

SWE-bench Lite should be treated as:

- a **backup external-validity benchmark**
- a fallback when Verified is inconvenient in a specific setup
- not the first choice when the goal is a very small, convincing real-world case-study section

---

## 9. Original HumanEval

## 9.1 Source-backed facts

The original `HumanEval` is the older OpenAI benchmark, while `EvalPlus` explicitly positions `HumanEval+` as the stricter version.

Official sources:

- [HumanEval GitHub](https://github.com/openai/human-eval)
- [EvalPlus GitHub](https://github.com/evalplus/evalplus)

## 9.2 How it should be positioned

Original HumanEval should not have any main-line role in this project.

At most, it can appear in a validity discussion as the looser predecessor that HumanEval+ improves upon.

---

## 10. Final Recommended Combination

The most defensible project setup is:

- **workflow grounding**: `mini-SWE-agent` first, `SWE-agent` second
- **main controlled benchmark**: `HumanEval+ / EvalPlus`
- **external-validity benchmark**: `SWE-bench Verified` for a very small case-study section
- **backup external-validity benchmark**: `SWE-bench Lite`

---

## 11. Why This Combination Is Strong

## 11.1 The workflow is not fictional

The workflow is grounded in real software engineering agent systems:

- mini-SWE-agent provides the simple linear control-flow reference,
- SWE-agent provides the richer repository-level issue-resolution background.

## 11.2 The main experiment remains controlled

HumanEval+ / EvalPlus gives the project:

- strict testing,
- manageable task scale,
- lower infrastructure variance,
- and a cleaner stage-wise perturbation setting.

## 11.3 External validity is still addressed

A small SWE-bench Verified case-study section lets the project connect its findings to real GitHub issue resolution without turning the entire project into a heavy repository-agent evaluation pipeline.

---

## 12. The Workflow We Should Actually Implement

This section is **project abstraction**, not a verbatim reproduction of either source system.

The project workflow should be:

1. receive a coding task,
2. build a task prompt,
3. generate code,
4. execute tests,
5. build a failure summary,
6. revise the code,
7. repeat until success or a round limit.

This workflow keeps the **iterative execution-feedback-repair core** of real software engineering agents, but it does **not** preserve the full repository-level capability set.

It intentionally leaves out:

- repository navigation,
- issue localization,
- cross-file editing,
- patch application in large repositories,
- long-horizon shell-session management.

That omission is acceptable, but it must be described honestly in the report.

---

## 13. Recommended Reporting Language

The safest way to describe the project is:

> Our workflow is grounded primarily in mini-SWE-agent for its simple linear control flow and stable sandbox-friendly execution model, and secondarily in SWE-agent as the canonical repository-level reference for issue-resolution agents with execution feedback. We do not attempt to faithfully reproduce a full repository-level software engineering agent. Instead, we study a lightweight abstraction of its iterative execution-feedback-repair core.

For benchmark selection, the report should say:

> We use HumanEval+ / EvalPlus for controlled stage-wise prompt fragility experiments, and a very small SWE-bench Verified case-study section for external validity in real GitHub issue settings.

---

## 14. Implementation Use

For the codebase, this decision implies a scaffold with:

- `TaskPromptBuilder`
- `Solver`
- `TestRunner`
- `FailureSummaryBuilder`
- `RepairSolver`
- `ExperimentRunner`
- `MetricsCollector`

The key research-facing hooks are:

- explicit stage boundaries,
- structured logs,
- clean vs perturbed condition switches,
- and compatibility with both EvalPlus and a small SWE-bench case-study path.

---

## 15. Links

- [SWE-agent paper](https://arxiv.org/abs/2405.15793)
- [SWE-agent GitHub](https://github.com/SWE-agent/SWE-agent)
- [SWE-agent ACI docs](https://swe-agent.com/0.7/background/aci/)
- [SWE-agent latest architecture docs](https://swe-agent.com/latest/background/architecture/)
- [mini-SWE-agent GitHub](https://github.com/SWE-agent/mini-swe-agent)
- [EvalPlus GitHub](https://github.com/evalplus/evalplus)
- [HumanEval+ dataset](https://huggingface.co/datasets/evalplus/humanevalplus)
- [HumanEval GitHub](https://github.com/openai/human-eval)
- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)
