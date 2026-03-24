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
Is the "Resilience Gap" an artifact of the `DeepSeek` architecture, or is it a universal characteristic of autoregressive LLMs? To validate this, we will run parallel experiments using `Qwen` (specifically, `Qwen-Plus` and `Qwen-Turbo`). By shifting the underlying foundation model while keeping identical prompt structures, we can measure the inherent structural robustness of different model families to feedback perturbations.

---

## 4. Proposed Mitigation Strategies
While this project focuses on **identifying** fragility, the "Resilience Gap" suggests several architectural solutions to improve the robustness of production-grade coding agents:

1.  **Feedback Verification Layer**: Introduce a "Critic" or "Auditor" agent that operates solely on original execution traces. This agent verifies that the generated `Failure Summary` is strictly loyal to the raw compiler output, preventing hallucinated logic from entering the repair loop.
2.  **Multi-Modal Grounding (Raw Trace Injection)**: LLM solvers should not rely exclusively on summarized text. Providing the **Raw Terminal Trace** alongside the summary creates a "Source is Truth" grounding, allowing the model to override a distorted summary if it detects a conflict with the trace.
3.  **Cross-Model Reasoning for Coordination**: Utilizing a high-reasoning model (e.g., `DeepSeek-R1`) for the **Feedback Analysis** stage while using a standard chat model for **Code Synthesis**. This decouples the logical interpretation of failures from the creative process of code generation, isolating the fragility.

---

## 5. Benchmark Potential: SAFB-Eval (Proposed)
This project introduces **SAFB-Eval** (Stagewise Agent Fragility Benchmark), a meta-benchmark for evaluating the robustness of autonomous coding agents.

Unlike traditional capability benchmarks (e.g., HumanEval, SWE-bench) which measure **static performance** (Can the model solve the problem?), **SAFB-Eval** measures **dynamic resilience** (How does the model survive under noisy intermediate feedback?).

### Why SAFB-Eval is a Novel Contribution:
-   **Metric Shift**: Shifting from binary "Pass/Fail" to "Dynamics Metrics" like **Recovery Rate** (Repairability after a perturbation) and **First Deviation Step** (Dependency divergence).
-   **Standardized Stress-Testing**: Provides a repeatable methodology for identifying specific "fragility points" in a multi-step inference cycle.
-   **Architecture Profiling**: Helps designers choose the right balance between model-size, cost, and structural rigor in their feedback loops.

Overall, **SAFB-Eval** provides a vital safety and reliability metric for agents intended to operate in real-world environments characterized by ambiguous instructions and noisy feedback.


