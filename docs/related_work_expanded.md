# Related Work (Expanded)

## 1. Why this review exists

This project studies **stage-wise prompt fragility** in coding agents that run a
lightweight `solve -> test -> summarize -> repair` loop.

The purpose of this review is to position that contribution clearly:

- it is not another generic prompt-sensitivity benchmark,
- it is not a full repository-level software engineering agent study,
- it is a controlled analysis of **where perturbations enter** and **how
  trajectories diverge** in iterative coding workflows.

## 2. Four connected literature threads

### 2.1 Prompt sensitivity as a measurable phenomenon

A first thread formalizes prompt sensitivity as a measurable property rather
than anecdotal behavior. Representative work includes ProSA and POSIX, which
emphasize perturbation families, score design, and instance-level variation.

Core takeaway for this repo:

- prompt sensitivity should be treated as a first-class evaluation target,
  not only as an error analysis side note.

### 2.2 Prompt variation in code generation

A second thread studies code-generation-specific sensitivity, including prompt
specificity and lexical variation effects (e.g., work such as *More Than a
Score* and *Code Roulette*).

Core takeaway for this repo:

- code-generation behavior can change meaningfully under small wording shifts,
  even when task intent appears stable.

### 2.3 Multi-step agent robustness

A third thread moves from single-shot outputs to multi-step systems where
errors can propagate across steps. This includes agent robustness and workflow
stability studies, as well as coding-agent frameworks that rely on iterative
repair.

Core takeaway for this repo:

- fragility in iterative agents should be evaluated along the trajectory,
  not only at the final answer.

### 2.4 Evaluation reliability and benchmark artifacts

A fourth thread asks whether observed fragility is always model behavior or
partly an evaluation artifact. This perspective is critical for avoiding
over-claims when perturbations accidentally alter callable contracts or hidden
assumptions.

Core takeaway for this repo:

- fragility claims must be bounded by benchmark and perturbation validity.

## 3. Positioning of this project

This project sits at the intersection of Threads 2 and 3, constrained by
Thread 4:

- from Thread 2: coding-task prompt variation is real,
- from Thread 3: iterative loops amplify local deviations,
- from Thread 4: not all measured changes should be interpreted as pure
  wording sensitivity.

So the project contribution is a **controlled stage-wise fragility lens**:

1. inject perturbations at explicit loop stages,
2. compare outcome-level and trajectory-level metrics,
3. report caveats (e.g., callable-contract drift) explicitly.

## 4. Representative references used in this project

The following references cover the review backbone used in the paper/report
materials of this repository:

- ProSA (prompt sensitivity measurement)
- POSIX (prompt sensitivity indexing)
- PromptBench / prompt robustness benchmark work
- More Than a Score (code prompt specificity)
- Code Roulette (code prompt variability)
- SWE-agent and mini-SWE-agent (iterative coding workflows)
- SWE-bench Verified (repository-level external validity reference)
- HumanEval+ / EvalPlus (function-level controlled benchmark)

## 5. Open gaps and implications

The review suggests three practical gaps that motivate this repository:

1. **Stage attribution gap**:
   many studies show fragility, but fewer isolate *which interaction stage*
   introduces divergence.
2. **Process-observability gap**:
   final pass rate alone hides recovery burden and cost escalation.
3. **Benchmark-interpretation gap**:
   robust conclusions require explicit handling of perturbation validity and
   evaluation artifacts.

These gaps define the methodological guardrails used throughout this project.
