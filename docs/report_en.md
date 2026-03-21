# Stage-Wise Instruction Fragility in Coding Agents

## 1. Topic Introduction

Large language model behavior is often sensitive to prompt wording. Two prompts can preserve the same intent at a high level and still trigger materially different outputs. This issue has been studied in single-turn settings for tasks such as question answering, classification, and code generation. The problem becomes more consequential in multi-step agentic systems, especially coding agents, because intermediate outputs are reused as future inputs.

In a coding workflow, an early misunderstanding does not simply produce one bad answer. It can alter the entire downstream trajectory:

- the first implementation may encode the wrong interpretation of the task,
- the test failures may be summarized in a misleading way,
- the repair step may optimize for the wrong target,
- and later rounds may reinforce, rather than correct, the initial deviation.

This makes coding agents a useful setting for studying prompt fragility at the trajectory level rather than only at the output level.

The core premise of this project is that prompt fragility in coding agents should be analyzed stage by stage. Instead of asking only whether a perturbation hurts final accuracy, we ask where it hurts, how the error propagates, and whether the agent can recover.

## 2. Core Problem

The project investigates a lightweight multi-step coding agent built around a test-repair loop:

1. read the task prompt,
2. generate candidate code,
3. execute tests,
4. construct or receive a failure summary,
5. revise the code,
6. repeat until success or a fixed round limit.

Within this loop, the project studies approximately meaning-preserving perturbations such as:

- semantic paraphrase,
- mild simplification,
- structural rewording,
- redundant but non-misleading context.

The central question is:

> Which stage of a coding agent is most vulnerable to prompt perturbation, and how do perturbation-induced deviations propagate across a test-repair trajectory?

## 3. Why This Problem Matters

### 3.1 Multi-step systems amplify small deviations

A small wording change in the initial task prompt can change the first implementation. Once that implementation fails, later steps reason over an already distorted state. The effect is compounding rather than isolated.

### 3.2 Code tasks provide hard, external evaluation

Unlike open-ended language tasks, code tasks can be judged with unit tests. This makes it possible to measure prompt fragility with objective outcomes such as pass rate, repair rounds, and recovery behavior.

### 3.3 Real workflows regularly rewrite instructions

In practical software work, prompts are routinely compressed, rewritten, reformatted, summarized, or merged with context. Even without malicious intent, these changes can alter how an agent interprets the task.

## 4. Positioning Against Prior Work

Existing work around prompt sensitivity is important but fragmented across several problem settings.

### 4.1 Prompt sensitivity as a measurable phenomenon

Work such as ProSA and POSIX treats prompt sensitivity as something that can be quantified rather than discussed informally. These papers are useful because they establish that prompt robustness can be studied systematically.

### 4.2 Prompt variability in code generation

Work such as Code Roulette and More Than a Score / PartialOrderEval shows that code generation quality depends strongly on how the prompt is phrased or how much detail it contains. These studies are directly relevant, but they mainly focus on single-step generation rather than iterative repair trajectories.

### 4.3 Robustness of agents and workflows

RobustFlow and AgentNoiseBench push the problem toward agentic workflows. They motivate the idea that semantic equivalence in natural language does not guarantee stable behavior in multi-step systems. This is the closest conceptual background for the present project.

### 4.4 Evaluation reliability

ReliableEval and Flaw or Artifact? are especially important because they warn against overclaiming from noisy or weak evaluation setups. A prompt sensitivity result is not useful if it is mostly an artifact of poor measurement.

## 5. The Intended Contribution

The intended contribution of this project is not to claim that prompt sensitivity exists in general. That point is already well supported.

The intended contribution is narrower and more concrete:

- study a lightweight coding agent rather than single-turn code generation,
- compare fragility across different stages of the loop,
- analyze not only final correctness but also deviation and recovery,
- and ground the study in strict test-based evaluation.

In short, the project aims to move from:

> "Does prompt wording matter?"

to:

> "At which stage does it matter most in a coding agent, and what kind of failure trajectory does it induce?"

## 6. Recommended Experimental Framing

The most defensible framing is a lightweight test-repair coding loop rather than a heavy agent platform.

That loop should include:

- a task prompt builder,
- a solver that produces an initial implementation,
- a test runner,
- a failure summary builder,
- a repair solver,
- a metrics collector.

The main benchmark should be `HumanEval+ / EvalPlus`, because it offers:

- manageable task scale,
- Python-centric evaluation,
- stronger tests than the original HumanEval setup,
- and a cleaner fit for a focused experiment.

`SWE-bench` and `OpenHands` are useful reference points, but they should be treated as optional extensions rather than the main empirical path.

## 7. Recommended Injection Stages

The cleanest main comparison is between two stages:

### 7.1 Task Prompt Stage

This stage measures whether a perturbation changes the agent's initial task interpretation and first implementation.

### 7.2 Failure Summary Stage

This stage measures whether a perturbation changes how the agent interprets feedback from failed tests and therefore changes the repair path.

The `Revision Prompt Stage` is conceptually interesting but should remain outside the main line unless the system is already stable.

## 8. Recommended Perturbation Types

The most defensible main perturbations are:

- `Semantic Paraphrase`
- `Mild Simplification`

These two are sufficient to test the central claim without exploding the experiment matrix.

More aggressive categories such as reordering and redundant context injection can be added later if the main system is stable and the perturbation quality is controlled.

## 9. Metrics

The project should report at least three primary metrics:

- `Final Pass Rate`
- `Average Repair Rounds`
- `Token / API Cost`

It should also report trajectory-aware metrics:

- `First Deviation Step`
- `Recovery Rate`
- `Failure Type Distribution`

These trajectory-aware metrics are what make the study different from a basic prompt sensitivity benchmark.

## 10. Important Methodological Constraint

If failure summaries are rule-based rather than freely generated by an LLM, the project should describe the setting precisely:

> the experiment measures sensitivity to changes in intermediate summary text, not sensitivity of a free-form summarizer itself.

This distinction matters. Without it, the claims can easily overreach the actual setup.

## 11. Main Risks

### 11.1 Perturbations may silently change task semantics

This is the largest validity threat. If a perturbation changes constraints or deletes important information, the experiment no longer measures expression-level fragility. It measures a different task.

### 11.2 Evaluation instability

If code execution is not sandboxed and deterministic, the experiment can fail for engineering reasons rather than research reasons.

### 11.3 Overclaiming from a small sample

A compact study can still be valuable, but the claims must stay aligned with the scale of the evidence.

### 11.4 Infrastructure creep

If the project expands into large-scale agent frameworks too early, the evaluation stack can dominate the project and displace the actual research question.

## 12. Practical Recommendation

The best version of this project is a tightly scoped empirical study of prompt perturbation in a lightweight coding loop.

That version should:

- prioritize stable execution,
- keep the benchmark small and controlled,
- compare a small number of stage-specific conditions,
- and combine aggregate metrics with high-quality failure and recovery case studies.

The project should avoid becoming:

- a full-scale agent platform replication effort,
- a heavy SWE-bench infrastructure project,
- or a broad survey of every prompt perturbation category.

## 13. Summary

The project is strongest when presented as a study of stage-wise fragility in a test-repair coding agent. Its value comes from narrowing the question, making the workflow explicit, using strict evaluation, and analyzing trajectories rather than only final answers.

That positioning is both technically defensible and aligned with the structure of the current research landscape.

## 14. References

- [ProSA (EMNLP Findings 2024)](https://aclanthology.org/2024.findings-emnlp.108/)
- [POSIX (EMNLP Findings 2024)](https://aclanthology.org/2024.findings-emnlp.852/)
- [PromptRobust (arXiv:2306.04528)](https://arxiv.org/abs/2306.04528)
- [More Than a Score / PartialOrderEval (arXiv:2508.03678)](https://arxiv.org/abs/2508.03678)
- [Code Roulette (arXiv:2506.10204)](https://arxiv.org/abs/2506.10204)
- [RobustFlow (arXiv:2509.21834)](https://arxiv.org/abs/2509.21834)
- [AgentNoiseBench (arXiv:2602.11348)](https://arxiv.org/abs/2602.11348)
- [CodeCrash (NeurIPS 2025 poster)](https://neurips.cc/virtual/2025/poster/119313)
- [ReliableEval (EMNLP Findings 2025)](https://aclanthology.org/2025.findings-emnlp.594/)
- [Flaw or Artifact? (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.1006/)
- [HumanEval GitHub](https://github.com/openai/human-eval)
- [EvalPlus GitHub](https://github.com/evalplus/evalplus)
- [HumanEval+ on Hugging Face](https://huggingface.co/datasets/evalplus/humanevalplus)
- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)
- [mini-swe-agent GitHub](https://github.com/SWE-agent/mini-swe-agent)
