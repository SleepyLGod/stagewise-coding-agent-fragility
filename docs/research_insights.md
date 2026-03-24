# Research Insights: Stage-wise Coding Agent Fragility

## 1. Core Concept: The Resilience Gap
The fundamental hypothesis of this project is that an autonomous coding agent's ability to self-correct is not uniform across all stages of interaction. Specifically, we investigate whether perturbations (noise, ambiguity, structural distortion) injected into the **Task Prompt** (Round 0) have the same downstream effects as identical perturbations injected into the **Failure Summary** (Feedback loop).

Our empirical findings confirm the existence of a **"Resilience Gap"**:
- **Goal Ambiguity is Recoverable**: When the initial task is perturbed, the agent's Round 0 pass rate drops significantly. However, once the agent receives clean, compiler-driven feedback, it exhibits exceptional recovery capabilities (Recovery Rate > 95%). The agent can refine its understanding of the ambiguous goal through concrete test failures.
- **Feedback Ambiguity is Fatal**: Conversely, when the initial task is clear but the feedback is perturbed, the agent's ability to "self-heal" collapses (Recovery Rate ~67%). Misleading structural cues in the failure summary cause the agent to endlessly chase phantom logic errors, often falling into infinite cyclic loops (`stuck_loop`). 

This proves that **feedback channels must be protected with higher structural rigor** than primary instruction channels in LLM agent pipelines.

---

## 2. Platform Scaling Capabilities & Limitations (SWE-bench)
To test if this fragility holds true in complex real-world software engineering, the scaffold integrates the `princeton-nlp/SWE-bench_Verified` dataset. 

**Current Integration Status**:
The data loader (`SWEBenchVerifiedAdapter`) and the isolation envelope (`DockerSandboxExecutor`) are fully functional. The system safely pulls tasks, isolates the container, and prevents local environment contamination.

**Execution Boundary**:
While the *adapter* successfully bridges the SWE-bench instances into our pipeline, true SWE-bench evaluation requires executing a repository's internal build and test systems (e.g., `git apply`, `pytest /tests`, `tox`). Currently, our runner executes single-file Python scripts (`PythonTestRunner`). Consequently, SWE-bench executions immediately fail. Building a native SWE-bench runner requires replicating the official SWE-bench evaluation harness (which handles hundreds of unique repository environments). For the scope of immediate ablation studies, we defer SWE-bench native execution to future work and focus on exploiting the statistical power of standard algorithm benchmarks (e.g., HumanEval+).

---

## 3. Future Directions: Ablation Studies

### A. Non-Deterministic Fragility (Decoding Parameters)
A critical follow-up question is whether an agent's fragility to feedback noise correlates with its creativity. Does high `temperature` make an agent more likely to hallucinate fixes based on perturbed feedback, or does it help the agent "break out" of structural traps? We propose exploring this through a decoding parameter ablation study, manipulating `temperature`, `top_p`, and sampling thresholds across multiple configurations.

### B. Cross-Model Generalization (Qwen Robustness)
Is the "Resilience Gap" an artifact of the `DeepSeek` architecture, or is it a universal characteristic of autoregressive LLMs? To validate this, we will run parallel experiments using `Qwen` (specifically, `Qwen-Plus` and `Qwen-Max`/`Flash`). By shifting the underlying foundation model while keeping identical prompt structures, we can measure the inherent structural robustness of different model families to feedback perturbations.
