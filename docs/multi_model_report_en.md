# Multi-Model Experiment Report

## Scope

This report consolidates the current HumanEval+-based stage-wise fragility runs
for the following groups:

- DeepSeek-Chat: initial run, balanced, conservative, creative
- DeepSeek-Reasoner
- Kimi 2.5
- Qwen-Turbo
- Qwen-Plus
- local `qwen3-coder:30b`

The report is based on:

- aggregated run-level metrics,
- direct sampling of raw JSON logs under `logs/`,
- existing summaries under `results/`,
- code inspection of the current experiment scaffold.

The goal is not to force a positive story. The goal is to state what the data
actually support.

## How to Read the Current Figures

The current pipeline generates three figures per run directory.

### `pass_and_recovery.png`

This plot shows, per condition:

- final pass rate,
- recovery rate among runs that failed at round 0.

Interpretation:

- high final pass rate + high recovery rate means many early mistakes are
  recoverable;
- high final pass rate + low recovery rate usually means there were not many
  round-0 failures to recover from, or the ones that occurred rarely recovered;
- low final pass rate + low recovery rate is the clearest sign that perturbation
  is damaging both outcome and repair.

Important caveat:

- recovery rate should always be read together with round-0 pass rate and
  average rounds;
- a high recovery rate does **not** mean the condition is cheap or stable.
  `task_simplification` often creates many more early failures and then repairs
  a large fraction of them at substantial cost.

### `pass_rate_by_round.png`

This plot shows cumulative pass rate over round index.

Interpretation:

- a higher round-0 point means the condition is more stable at the initial solve
  step;
- a wider gap between round 0 and the final round means the repair loop is doing
  more work;
- two conditions may end at similar final pass rate while differing sharply in
  early-round behavior.

This plot is the best way to see "final success looks similar, but the path is
different."

### `first_deviation_step.png`

This plot shows the average first round index where a perturbed run's execution
trajectory diverges from the clean run.

Interpretation:

- values near `0` mean the perturbation begins affecting behavior from the
  initial solve step;
- values near `1` mean the perturbation begins affecting behavior only after the
  first failed execution, i.e. during repair.

In the current project, this acts primarily as a stage-alignment sanity check:

- `task_*` conditions should deviate at round `0`,
- `failure_*` conditions should deviate at round `1`.

This metric is about **when** divergence begins, not how harmful it is by
itself.

## How to Read the New Cross-Model Figures

The project now also generates a second layer of figures under
`results/cross_model/figures/`.

### `delta_final_pass_rate_heatmap.png`

This heatmap shows, for each model group and each non-clean condition, the
change in final pass rate relative to the clean baseline.

Interpretation:

- positive values mean the condition improved final pass rate,
- negative values mean the condition reduced final pass rate,
- values near zero mean the main effect is probably not on final outcome.

### `delta_round0_pass_rate_heatmap.png`

This heatmap shows how much the condition changes round-0 success relative to
clean.

Interpretation:

- large negative values indicate early trajectory instability,
- this is often the clearest process-fragility signal even when final pass rate
  stays high.

### `delta_average_total_tokens_heatmap.png`

This heatmap shows token-cost change relative to clean.

Interpretation:

- large positive values mean the condition is materially more expensive,
- this is especially useful for detecting "recoverable but costly" perturbation
  effects.

### `clean_accuracy_vs_cost.png`

This scatter plot compares model groups on the clean baseline only.

Interpretation:

- upper-left is the ideal region: high pass rate at low cost,
- points far to the right indicate strong but expensive models,
- points lower on the y-axis indicate weaker baselines.

### `deepseek_chat_parameter_sweep.png`

This bar chart compares DeepSeek-Chat parameter groups across the main
conditions.

Interpretation:

- it is the clearest view of how conservative / balanced / creative settings
  change stage-wise behavior inside the same model family.

### `task_prompt_contract_drift.png`

This bar chart shows the task-prompt function-name drift rate per model group.

Interpretation:

- non-zero values mean some task-side perturbations changed the benchmark
  callable contract,
- those groups need more careful interpretation because part of their
  task-side fragility is a mixed contract-drift effect.

### `perturbation_failure_overlap.png`

This heatmap shows, for the most relevant tasks, how many perturbation-induced
failed runs each model group produced.

Interpretation:

- brighter rows indicate tasks that are fragile across several models,
- isolated bright cells indicate model-specific fragility,
- this is the best plot for answering whether the same tasks are fragile across
  groups or whether each model has its own failure profile.

## Setup and Audit Notes

### No separate system prompt is stored or sent

The current model client sends a single user message only. The code path in
`src/stagewise_coding_agent_fragility/models/deepseek.py` uses:

```python
messages=[{"role": "user", "content": prompt}]
```

So the current experiments do **not** use a separate system message parameter in
the stored request path.

### Which decoding parameters are known

The exact solver decoding settings are known for these runs because they are
backed by checked-in configs:

- DeepSeek-Chat balanced: `temperature=0.7`, `top_p=0.95`
- DeepSeek-Chat conservative: `temperature=0.3`, `top_p=0.8`
- DeepSeek-Chat creative: `temperature=1.0`, `top_p=1.0`
- DeepSeek-Reasoner: `temperature=1.0`, `top_p=1.0`, `max_tokens=4096`
- Qwen-Turbo balanced: `temperature=0.7`, `top_p=0.95`
- Qwen-Plus balanced: `temperature=0.7`, `top_p=0.95`

The exact decoding parameters are **not recoverable from the stored logs** for:

- Kimi 2.5
- local `qwen3-coder:30b`
- the early DeepSeek-Chat run labeled here as "initial run"

The logs store model name, outputs, token usage, and timing, but not
`temperature` or `top_p`.

### Important confound: task-prompt contract drift

Task-side perturbation is not equally clean across all model groups.

When we compare the function name in the original task prompt versus the
perturbed task prompt:

- DeepSeek-Chat: `0 / 984` changed
- DeepSeek-Reasoner: `0 / 984` changed
- Kimi 2.5: `3 / 984` changed (`0.305%`)
- Qwen-Turbo: `13 / 984` changed (`1.321%`)
- Qwen-Plus: `9 / 984` changed (`0.915%`)
- local `qwen3-coder:30b`: `0 / 984` changed

This matters because some Qwen and Kimi task-side failures are not pure
wording-sensitivity effects. They are mixed with contract drift, e.g. a renamed
function that no longer matches the benchmark harness.

## Headline Metrics by Group

### Clean baseline, best condition, worst condition

| Group | Clean pass | Best non-clean condition | Best pass | Worst non-clean condition | Worst pass |
|---|---:|---|---:|---|---:|
| DeepSeek-Chat initial | 0.9492 | `task_paraphrase` | 0.9614 | `failure_paraphrase` | 0.9451 |
| DeepSeek-Chat balanced | 0.9472 | `task_simplification` | 0.9593 | `failure_paraphrase` | 0.9390 |
| DeepSeek-Chat conservative | 0.9451 | `task_paraphrase` | 0.9593 | `failure_paraphrase` | 0.9370 |
| DeepSeek-Chat creative | 0.9533 | `task_paraphrase` | 0.9675 | `failure_paraphrase` | 0.9289 |
| DeepSeek-Reasoner | 0.9675 | `failure_paraphrase` / `failure_simplification` | 0.9715 | `task_simplification` | 0.9533 |
| Kimi 2.5 | 0.9817 | `failure_paraphrase` / `task_simplification` | 0.9817 | `task_paraphrase` / `failure_simplification` | 0.9756 |
| Qwen-Turbo | 0.8943 | `task_simplification` | 0.9268 | `task_paraphrase` | 0.8720 |
| Qwen-Plus | 0.9390 | `task_simplification` | 0.9675 | `failure_simplification` | 0.9451 |
| local `qwen3-coder:30b` | 0.9187 | `task_simplification` | 0.9512 | `failure_simplification` | 0.9146 |

## Per-Group Analysis

## 1. DeepSeek-Chat Initial Run

### Metrics

- `clean`: pass `0.9492`, average tokens `364.55`
- `task_paraphrase`: pass `0.9614`
- `task_simplification`: pass `0.9492`, but round-0 pass falls from `448/492` to
  `212/492`, and average tokens rise to `985.86`
- `failure_paraphrase`: pass `0.9451`

### Interpretation

This run already shows the core pattern that later repeats in the DeepSeek-Chat
family:

- failure-side perturbations slightly damage final pass rate;
- task simplification mainly damages the **path**, not necessarily the final
  outcome;
- task paraphrase can sometimes be neutral or slightly helpful.

This is a good example of why pass rate alone is incomplete. `task_simplification`
barely changes final pass rate here, but it nearly halves round-0 success and
adds more than `600` tokens on average.

### Failure surface

- `24` unique failed tasks overall
- `task_simplification` introduces `7` perturbation-only failed tasks
- failures are dominated by `AssertionError`, with smaller numbers of
  `NameError`, `KeyError`, or similar exceptions

## 2. DeepSeek-Chat Balanced

### Metrics

- `clean`: pass `0.9472`
- `failure_paraphrase`: `0.9390`
- `task_paraphrase`: `0.9573`
- `task_simplification`: `0.9593`

### Interpretation

Balanced DeepSeek-Chat behaves similarly to the initial run, but with an even
clearer split:

- `failure_paraphrase` is the weakest condition,
- `task_simplification` is the best final-pass condition.

This does **not** mean simplification is cheap. It still drops round-0 pass
from `448/492` to `227/492` and adds roughly `600` tokens.

### Failure surface

- `22` unique failed tasks overall
- `failure_paraphrase` adds `4` perturbation-only failed tasks
- `task_simplification` adds `8` perturbation-only failed tasks
- common error mix: mostly `AssertionError`, plus small pockets of
  `ValueError`, `SyntaxError`, `TypeError`, and `NameError`

## 3. DeepSeek-Chat Conservative

### Metrics

- `clean`: `0.9451`
- `failure_paraphrase`: `0.9370`
- `failure_simplification`: `0.9390`
- `task_paraphrase`: `0.9593`
- `task_simplification`: `0.9472`

### Interpretation

The conservative setting does not buy obvious robustness. It is not better than
balanced in final accuracy, and it still shows the same large process penalty
under `task_simplification`.

This suggests that reducing randomness from `balanced` to `conservative` is not
enough to remove stage-wise fragility in this scaffold.

### Failure surface

- `24` unique failed tasks overall
- `task_simplification` still causes `282` round-0 failures
- `failure_paraphrase` and `failure_simplification` each introduce a few
  perturbation-only failures

## 4. DeepSeek-Chat Creative

### Metrics

- `clean`: `0.9533`
- `failure_paraphrase`: `0.9289`
- `task_paraphrase`: `0.9675`
- `task_simplification`: `0.9492`

### Interpretation

This is the most polarized DeepSeek-Chat setting:

- it gives the best clean baseline among the chat variants,
- it also gives the strongest negative effect under `failure_paraphrase`,
- it gives the strongest positive effect under `task_paraphrase`.

The likely interpretation is not "creative is universally better." It is more
specific:

- higher-variance sampling seems to help when the task wording is re-expressed
  but still informative,
- the same higher-variance setting seems to hurt more when repair is guided by
  a rephrased failure signal.

### Sampled cases

- `HumanEval/93`, `task_simplification`, repeat `0`: direct round-0 failure,
  then a three-round `AssertionError` stuck loop. The simplified task remains on
  the same function name, so this is a genuine information-loss or search-path
  issue rather than a renamed-contract artifact.
- `HumanEval/160`, `task_paraphrase`, repeat `0`: direct success in one round.
  This case suggests that paraphrase can sometimes improve task readability
  rather than harm it.

## 5. DeepSeek-Reasoner

### Metrics

- `clean`: `0.9675`
- `failure_paraphrase`: `0.9715`
- `failure_simplification`: `0.9715`
- `task_paraphrase`: `0.9675`
- `task_simplification`: `0.9533`

### Interpretation

DeepSeek-Reasoner is the strongest DeepSeek model in final pass rate, but it is
also by far the most expensive:

- `clean` tokens: `1844.59`
- `task_simplification` tokens: `3590.13`

This model is robust to failure-side perturbations in final accuracy, but it is
still process-sensitive to task simplification.

### Failure surface

Reasoner differs from the chat models in one important way: failed runs show a
larger proportion of `NameError`, not just `AssertionError`.

That suggests a stronger tendency to generate incomplete helper structure or
incomplete program skeletons under difficult settings.

### Sampled cases

- `HumanEval/134`, `failure_paraphrase`, repeat `0`: three-round stuck loop with
  `NameError: check_if_last_char_is_a_letter is not defined`. The paraphrased
  failure summary is verbose but still not sufficiently actionable.
- `HumanEval/132`, `task_simplification`, repeat `1`: direct success in one
  round. This is a counterexample showing that simplification can occasionally
  sharpen the task instead of flattening it.

## 6. Kimi 2.5

### Metrics

- `clean`: `0.9817`
- `failure_paraphrase`: `0.9817`
- `failure_simplification`: `0.9756`
- `task_paraphrase`: `0.9756`
- `task_simplification`: `0.9817`

### Process metrics

- `clean`: round-0 pass `468/492`, average tokens `388.85`
- `task_simplification`: round-0 pass `396/492`, average tokens `901.28`

### Interpretation

Kimi is the clearest example of **final-outcome robustness but process-level
fragility**:

- final pass rate barely moves,
- process cost moves a lot,
- early deviations increase sharply under `task_simplification`.

This is not a null result. It is a clean negative-result-with-process-effect:
the model usually repairs itself, but not cheaply.

### Failure surface

- only `9` unique failed tasks overall
- failures are concentrated rather than diffuse
- perturbation-only failures still exist, so it is not true that perturbation
  has zero effect

### Sampled cases

- `HumanEval/134`, `task_paraphrase`, repeat `0`: three-round stuck loop with
  final `AssertionError`. This is one of the few task-side cases where Kimi is
  genuinely pushed off the successful path.
- `HumanEval/50`, `failure_paraphrase`, repeat `0`: round-0 failure but final
  success in two rounds. The repaired code explicitly adds `encode_shift`,
  which fits the broader Kimi pattern where some failure-side perturbations do
  not destroy repairability.

## 7. Qwen-Turbo

### Metrics

- `clean`: `0.8943`
- `failure_paraphrase`: `0.9024`
- `failure_simplification`: `0.8984`
- `task_paraphrase`: `0.8720`
- `task_simplification`: `0.9268`

### Interpretation

Qwen-Turbo is the weakest API model in this set:

- lowest clean baseline among the cloud API models,
- broadest failure surface,
- strongest negative effect from `task_paraphrase`.

At the same time, `task_simplification` is unexpectedly helpful in final pass
rate. This means the task-side story is not "task perturbation is always bad."
It is more conditional:

- paraphrase hurts this model,
- simplification often helps this model in final outcome,
- but both conditions still increase prompt cost.

### Failure surface

- `39` unique failed tasks overall
- `task_paraphrase` introduces `15` perturbation-only failed tasks
- failures include `AssertionError`, `NameError`, `TypeError`, and `IndexError`

This is a much wider failure surface than Kimi or Qwen-Plus.

### Sampled cases

- `HumanEval/157`, `task_paraphrase`, repeat `2`: the perturbed task renames the
  function from `right_angle_triangle` to `check_right_triangle`, leading to a
  final `NameError`. This is a direct example of contract drift contaminating
  the prompt-fragility signal.
- `HumanEval/134`, `task_simplification`, repeat `0`: direct success in one
  round. This shows that simplified task wording can also help Qwen-Turbo on
  some tasks.

## 8. Qwen-Plus

### Metrics

- `clean`: `0.9390`
- `failure_paraphrase`: `0.9492`
- `failure_simplification`: `0.9451`
- `task_paraphrase`: `0.9472`
- `task_simplification`: `0.9675`

### Interpretation

Qwen-Plus is much stronger and more stable than Qwen-Turbo:

- higher clean baseline,
- smaller failure surface,
- more conditions outperform clean rather than underperform it.

The most notable result is again `task_simplification`, which boosts final pass
substantially while also increasing token cost.

### Failure surface

- only `13` unique failed tasks overall
- `task_paraphrase` introduces no perturbation-only failed tasks in the sampled
  aggregate
- residual failures are still mostly `AssertionError` and `NameError`

### Sampled cases

- `HumanEval/93`, `task_simplification`, repeat `0`: three-round stuck loop with
  final `AssertionError`.
- `HumanEval/134`, `task_simplification`, repeat `0`: direct one-round success.

This pair is a good reminder that simplification is not uniformly helpful; it
helps many tasks on average but still breaks some specific ones.

## 9. local `qwen3-coder:30b`

### Metrics

- `clean`: `0.9187`
- `failure_paraphrase`: `0.9228`
- `failure_simplification`: `0.9146`
- `task_paraphrase`: `0.9370`
- `task_simplification`: `0.9512`

### Interpretation

The local model sits between Qwen-Turbo and Qwen-Plus in baseline strength:

- better than Qwen-Turbo,
- worse than Qwen-Plus,
- notably more stable than the API Qwen models with respect to function-name
  drift, because no task-prompt function renaming was observed in the sampled
  logs.

### Failure surface

- `23` unique failed tasks overall
- failures are still dominated by `AssertionError`
- compared with Qwen-Turbo, the failure surface is smaller and cleaner

### Sampled cases

- `HumanEval/118`, `failure_simplification`, repeat `0`: the perturbed failure
  summary becomes `AssertionError: expected true, got false`, which is too weak
  to guide repair. The run remains stuck for three rounds.
- `HumanEval/134`, `task_simplification`, repeat `0`: success after one repair
  step. The simplified task makes the target behavior almost operational.

## Cross-Group Comparison

## 1. DeepSeek vs Qwen vs Kimi

### Final outcome

- Kimi has the highest clean pass rate: `0.9817`
- DeepSeek-Reasoner is next: `0.9675`
- DeepSeek-Chat variants cluster around `0.945` to `0.953`
- Qwen-Plus reaches `0.9390`
- local `qwen3-coder:30b` reaches `0.9187`
- Qwen-Turbo is the weakest at `0.8943`

### Process cost

- DeepSeek-Reasoner is by far the most expensive model
- Kimi gives the best clean baseline among medium-cost models
- Qwen-Turbo is cheap but weaker
- Qwen-Plus pays more tokens than Qwen-Turbo but buys much better accuracy

### Fragility pattern

- Kimi: strongest evidence for process fragility without large final-pass drop
- DeepSeek-Chat: strongest evidence for task-simplification cost explosion and
  failure-paraphrase sensitivity
- DeepSeek-Reasoner: strong final robustness, but extremely costly under task
  simplification
- Qwen-Turbo: broadest failure surface and strongest task-paraphrase weakness
- Qwen-Plus: substantially more robust than Qwen-Turbo
- local `qwen3-coder:30b`: cleaner than Qwen-Turbo, weaker than Qwen-Plus, but
  free of the observed function-name drift

## 2. Qwen family comparison

### Qwen-Turbo vs Qwen-Plus

Qwen-Plus is better almost everywhere that matters:

- clean pass: `0.9390` vs `0.8943`
- task paraphrase: `0.9472` vs `0.8720`
- unique failed tasks overall: `13` vs `39`
- task-prompt function-name drift: `0.915%` vs `1.321%`

This is not a subtle difference. Qwen-Plus is clearly the stronger and more
stable API model in this experiment.

### Qwen-Plus vs local `qwen3-coder:30b`

The local model is not as strong in final pass rate, but it has one very useful
property for cleaner analysis:

- no observed function-name drift in task perturbations.

That means some of its task-side results may be easier to interpret as genuine
prompt-fragility effects rather than benchmark-contract corruption.

## 3. DeepSeek family comparison

### Chat vs Reasoner

DeepSeek-Reasoner improves final pass rate over the chat variants, but at a
very large token cost:

- clean tokens: `1844.59` for Reasoner vs roughly `356–365` for Chat
- `task_simplification` tokens: `3590.13` for Reasoner vs roughly `951–986` for
  Chat

So Reasoner is not simply "better." It is "better but much more expensive."

### DeepSeek-Chat parameter sweep

The parameter sweep suggests:

- clean baseline moves only modestly across conservative, balanced, and
  creative;
- `failure_paraphrase` gets worse as the chat model becomes more creative;
- `task_paraphrase` gets better as the chat model becomes more creative;
- `task_simplification` is consistently expensive across all chat settings.

This is the most coherent reading of the sweep:

> More creative sampling helps DeepSeek-Chat absorb reworded task descriptions,
> but hurts it when the repair loop is driven by paraphrased failure signals.

## 4. What is actually supported by the current data

The current multi-model results support the following claims:

### Strongly supported

- Different perturbation stages affect trajectories differently.
- Task-side perturbations often act from round `0`.
- Failure-side perturbations act from round `1`.
- Final pass rate alone hides meaningful process differences.

### Supported with caveats

- Some models are clearly more process-robust than others.
- Task simplification often increases recovery work and token cost.
- Qwen-Turbo is more fragile than Qwen-Plus.
- DeepSeek-Reasoner is more robust in final outcome than DeepSeek-Chat, but not
  in cost efficiency.

### Must be stated carefully

- Not every positive or negative effect is a pure prompt-sensitivity effect.
- Some Qwen and Kimi task-side failures are contaminated by function-name drift.
- Therefore, part of the measured task-side fragility is a mix of wording
  sensitivity and contract drift.

## Plot Status and Remaining Gaps

The cross-model plots that were previously recommended are now implemented:

- `delta_final_pass_rate_heatmap.png`
- `delta_round0_pass_rate_heatmap.png`
- `delta_average_total_tokens_heatmap.png`
- `clean_accuracy_vs_cost.png`
- `deepseek_chat_parameter_sweep.png`
- `task_prompt_contract_drift.png`
- `perturbation_failure_overlap.png`

These plots are enough for the main multi-model comparison section.

There is still one optional addition worth considering later.

### Optional future addition: task-overlap plot by condition type

The current overlap heatmap aggregates all non-clean conditions together.
If the later write-up needs finer resolution, the next useful addition would be
separate overlap plots for:

- task-side perturbation-induced failures only,
- failure-side perturbation-induced failures only.

## Final Assessment

The current dataset is already strong enough to support a serious analysis.

The most important conclusion is not that "perturbation always reduces pass
rate." The more accurate conclusion is:

> Stage-wise perturbations change different models in different ways. In many
> cases they primarily change the trajectory rather than the final outcome.
> Kimi is the clearest example of process fragility without large final-collapse.
> DeepSeek-Reasoner trades cost for stronger final robustness. Qwen-Turbo is the
> weakest and most fragile Qwen API model, while Qwen-Plus is clearly stronger.
> Some task-side effects in Kimi and Qwen are confounded by contract drift and
> should be reported honestly as mixed effects rather than pure wording
> sensitivity.
