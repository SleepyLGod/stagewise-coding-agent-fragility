# 多模型实验报告

## 范围

这份报告汇总了当前基于 HumanEval+ 的 stage-wise fragility 实验，覆盖以下组别：

- DeepSeek-Chat：初始 run、balanced、conservative、creative
- DeepSeek-Reasoner
- Kimi 2.5
- Qwen-Turbo
- Qwen-Plus
- 本地 `qwen3-coder:30b`

报告依据包括：

- 各 run 目录的聚合指标，
- `logs/` 下原始 JSON 的抽样核查，
- `results/` 下已有 summary，
- 当前实验代码的实现方式。

这里不追求“强行讲出正结果”，只讲数据真正支持什么。

## 现在这三张图怎么看

当前每个 run 目录会生成三张图。

### `pass_and_recovery.png`

这张图按 condition 展示两个量：

- 最终 pass rate
- 在 round 0 失败的样本里，最终被修回来的比例（recovery rate）

解读方式：

- 最终 pass 高、recovery 也高：说明早期偏航不少，但很多能修回来
- 最终 pass 高、recovery 低：说明要么 round-0 失败本来就不多，要么失败后不太容易修回
- 最终 pass 低、recovery 也低：这是最典型的“又伤结果又伤 repair”的情况

注意：

- recovery rate 一定要和 round-0 pass、average rounds 一起看；
- recovery 高不等于“这个 condition 好”，因为有些条件会先把很多样本打偏，再让 agent 花大代价修回来。

### `pass_rate_by_round.png`

这张图画的是累计 pass rate 随 round 的变化。

解读方式：

- round 0 越高，说明初始 solve 越稳；
- round 0 到最终 round 的 gap 越大，说明 repair loop 做的事情越多；
- 最终 pass 差不多的两组，轨迹可能完全不一样。

这张图最适合说明：

> “最后看起来都差不多，但过程其实很不一样。”

### `first_deviation_step.png`

这张图展示 perturbed run 相对于 clean run 的 execution trajectory 第一次分叉发生在哪一轮。

解读方式：

- 接近 `0`：从初始 solve 就开始受影响
- 接近 `1`：要等到第一次失败、进入 repair 之后才开始受影响

在当前项目里，这张图最主要的作用是做 stage-alignment sanity check：

- `task_*` 理论上应该从 round `0` 开始分叉
- `failure_*` 理论上应该从 round `1` 开始分叉

它主要说明“影响从哪一轮开始”，不是单独说明“伤害有多大”。

## 新的跨模型图怎么看

现在项目还会在 `results/cross_model/figures/` 下生成一组跨模型图。

### `delta_final_pass_rate_heatmap.png`

这张图展示每个模型组在每个非 clean condition 下，相对于 clean baseline
的最终 pass rate 变化。

解读方式：

- 正值：这个 condition 让最终 pass 变高了
- 负值：这个 condition 让最终 pass 变低了
- 接近 0：最终结果变化不大，主要影响可能在过程层面

### `delta_round0_pass_rate_heatmap.png`

这张图展示每个 condition 相对于 clean，round-0 直接成功率变了多少。

解读方式：

- 明显负值：说明初始 solve 稳定性下降了
- 这是最适合看 process fragility 的图之一

### `delta_average_total_tokens_heatmap.png`

这张图展示相对于 clean，token 成本变化了多少。

解读方式：

- 大的正值说明这个 condition 很“贵”
- 特别适合识别“最后修得回来，但代价显著上升”的情况

### `clean_accuracy_vs_cost.png`

这张 scatter 只看 clean baseline。

解读方式：

- 左上角最理想：低成本、高准确率
- 往右很远：说明模型很强但很贵
- y 值偏低：说明 clean baseline 本身就弱

### `deepseek_chat_parameter_sweep.png`

这张图只比较 DeepSeek-Chat 家族的参数组。

解读方式：

- 最适合看 conservative / balanced / creative 之间的差别
- 可以直接看出哪类 perturbation 对不同采样参数更敏感

### `task_prompt_contract_drift.png`

这张图画的是 task-side perturbation 里函数名漂移率。

解读方式：

- 非 0 说明有一部分 task prompt 已经改坏了 benchmark contract
- 这些组的 task-side 结果必须更谨慎解释，因为它们混入了 contract drift

### `perturbation_failure_overlap.png`

这张图展示哪些 task 在哪些模型组里出现了 perturbation-induced failed runs。

解读方式：

- 一整行都亮：说明这个 task 在多个模型上都脆
- 只有个别格子亮：说明这是某个模型特有的 fragile-task profile
- 这是回答“是不是同一批题在不同模型上都脆”的最好图

## 设置与审计说明

### 当前代码没有单独的 system prompt

当前模型客户端只发送一条 user message。代码路径
`src/stagewise_coding_agent_fragility/models/deepseek.py`
使用的是：

```python
messages=[{"role": "user", "content": prompt}]
```

所以从当前代码和日志能确认的是：

- 没有单独的 system message 被显式记录或发送
- 现在实验看到的行为主要来自 prompt 本身和解码参数，而不是额外的 system prompt

### 哪些解码参数是已知的

以下 run 的解码参数可以从 repo 中的 config 直接确认：

- DeepSeek-Chat balanced：`temperature=0.7`，`top_p=0.95`
- DeepSeek-Chat conservative：`temperature=0.3`，`top_p=0.8`
- DeepSeek-Chat creative：`temperature=1.0`，`top_p=1.0`
- DeepSeek-Reasoner：`temperature=1.0`，`top_p=1.0`，`max_tokens=4096`
- Qwen-Turbo balanced：`temperature=0.7`，`top_p=0.95`
- Qwen-Plus balanced：`temperature=0.7`，`top_p=0.95`

以下组别的精确 `temperature/top_p` **无法从当前日志里反推出来**：

- Kimi 2.5
- 本地 `qwen3-coder:30b`
- 最早那组 DeepSeek-Chat 初始 run

原因很简单：日志里没有保存 request defaults。

### 一个必须诚实写进报告的混杂因素：task-prompt contract drift

如果比较原始 task prompt 和 perturbed task prompt 中的函数名，结果是：

- DeepSeek-Chat：`0 / 984` 发生函数名变化
- DeepSeek-Reasoner：`0 / 984`
- Kimi 2.5：`3 / 984`，约 `0.305%`
- Qwen-Turbo：`13 / 984`，约 `1.321%`
- Qwen-Plus：`9 / 984`，约 `0.915%`
- 本地 `qwen3-coder:30b`：`0 / 984`

这件事很重要，因为它说明：

- DeepSeek 和本地 qwen 的 task-side 结果更接近“纯 wording sensitivity”
- Kimi 和 Qwen API 的一部分 task-side 失败混入了 contract drift
- 所以它们的部分 task fragility 结果不能被表述成“纯语义等价改写造成的影响”

## 各组 headline 指标

### Clean / 最优非 clean 条件 / 最差非 clean 条件

| 组别 | Clean pass | 最优非 clean 条件 | 最优 pass | 最差非 clean 条件 | 最差 pass |
|---|---:|---|---:|---|---:|
| DeepSeek-Chat 初始 run | 0.9492 | `task_paraphrase` | 0.9614 | `failure_paraphrase` | 0.9451 |
| DeepSeek-Chat balanced | 0.9472 | `task_simplification` | 0.9593 | `failure_paraphrase` | 0.9390 |
| DeepSeek-Chat conservative | 0.9451 | `task_paraphrase` | 0.9593 | `failure_paraphrase` | 0.9370 |
| DeepSeek-Chat creative | 0.9533 | `task_paraphrase` | 0.9675 | `failure_paraphrase` | 0.9289 |
| DeepSeek-Reasoner | 0.9675 | `failure_paraphrase` / `failure_simplification` | 0.9715 | `task_simplification` | 0.9533 |
| Kimi 2.5 | 0.9817 | `failure_paraphrase` / `task_simplification` | 0.9817 | `task_paraphrase` / `failure_simplification` | 0.9756 |
| Qwen-Turbo | 0.8943 | `task_simplification` | 0.9268 | `task_paraphrase` | 0.8720 |
| Qwen-Plus | 0.9390 | `task_simplification` | 0.9675 | `failure_simplification` | 0.9451 |
| 本地 `qwen3-coder:30b` | 0.9187 | `task_simplification` | 0.9512 | `failure_simplification` | 0.9146 |

## 分组详细分析

## 1. DeepSeek-Chat 初始 run

### 指标

- `clean`: pass `0.9492`，average tokens `364.55`
- `task_paraphrase`: `0.9614`
- `task_simplification`: `0.9492`，但 round-0 pass 从 `448/492` 掉到 `212/492`，tokens 涨到 `985.86`
- `failure_paraphrase`: `0.9451`

### 分析

这组已经很清楚地给出了后面 DeepSeek-Chat 家族会重复出现的模式：

- failure-side perturbation 会轻微伤最终结果；
- task simplification 主要伤的是**过程**，不一定明显伤最终 pass；
- task paraphrase 有时甚至略微有利。

也就是说，如果只盯最终 pass rate，这组会被误读成“影响不大”；但从 round-0 pass 和 token cost 来看，`task_simplification` 已经非常明显地让轨迹变脆、变贵。

### failure surface

- 全组共 `24` 个唯一失败 task
- `task_simplification` 额外引入 `7` 个 perturbation-only failed task
- 失败以 `AssertionError` 为主，少量 `NameError`、`KeyError`

## 2. DeepSeek-Chat balanced

### 指标

- `clean`: `0.9472`
- `failure_paraphrase`: `0.9390`
- `task_paraphrase`: `0.9573`
- `task_simplification`: `0.9593`

### 分析

balanced 这组和初始 run 非常接近，但更清楚：

- `failure_paraphrase` 是最差条件；
- `task_simplification` 是最终 pass 最好的条件。

但这不等于 simplification 是“免费提升”：

- round-0 pass 从 `448/492` 掉到 `227/492`
- token 大约多出 `600`

所以更准确的说法是：

> `task_simplification` 对 balanced DeepSeek-Chat 经常是“先打偏，再修回来”，而不是直接更稳。

### failure surface

- `22` 个唯一失败 task
- `failure_paraphrase` 额外引入 `4` 个 perturbation-only failed task
- `task_simplification` 额外引入 `8` 个 perturbation-only failed task
- 错误以 `AssertionError` 为主，夹杂 `ValueError`、`SyntaxError`、`TypeError`

## 3. DeepSeek-Chat conservative

### 指标

- `clean`: `0.9451`
- `failure_paraphrase`: `0.9370`
- `failure_simplification`: `0.9390`
- `task_paraphrase`: `0.9593`
- `task_simplification`: `0.9472`

### 分析

conservative 并没有表现出明显更稳：

- clean 没有优于 balanced，
- failure-side 仍然明显掉，
- task simplification 仍然带来很大的过程代价。

所以从当前结果看，单纯把采样从 balanced 收到 conservative，并不能消除这套 scaffold 里的 stage-wise fragility。

## 4. DeepSeek-Chat creative

### 指标

- `clean`: `0.9533`
- `failure_paraphrase`: `0.9289`
- `task_paraphrase`: `0.9675`
- `task_simplification`: `0.9492`

### 分析

creative 是 DeepSeek-Chat 家族里最“极化”的一组：

- clean 最好；
- `task_paraphrase` 也最好；
- 但 `failure_paraphrase` 最差。

更合理的解释不是“creative 更强”或者“creative 更差”，而是：

- 当 task wording 被重写但仍然保留信息时，更高方差的采样可能更容易找到可行路径；
- 但当 repair loop 要依赖 paraphrased failure signal 时，更高方差反而更容易跑偏。

### 抽样 case

- `HumanEval/93`, `task_simplification`, repeat `0`：
  round 0 就失败，之后 3 轮都 stuck 在 `AssertionError`。这里函数名没变，所以这是典型的信息被压扁 / 搜索方向错误，而不是 contract drift。
- `HumanEval/160`, `task_paraphrase`, repeat `0`：
  一轮直接成功。说明 paraphrase 对某些任务确实可能是“重述得更清楚”而不是“扰动”。

## 5. DeepSeek-Reasoner

### 指标

- `clean`: `0.9675`
- `failure_paraphrase`: `0.9715`
- `failure_simplification`: `0.9715`
- `task_paraphrase`: `0.9675`
- `task_simplification`: `0.9533`

### 分析

DeepSeek-Reasoner 是 DeepSeek 家族里最终正确率最高的，但代价也远高于 chat：

- `clean` token：`1844.59`
- `task_simplification` token：`3590.13`

所以它不是“纯更好”，而是：

> 最终结果更稳，但成本极高，尤其在 task simplification 下代价会爆炸。

### failure surface

Reasoner 和 chat 最大的区别之一是：失败里 `NameError` 占比更高，而不只是 `AssertionError`。

这说明它在困难条件下更容易生成：

- helper 缺失，
- skeleton 不完整，
- 配对函数没补齐

这类结构性错误。

### 抽样 case

- `HumanEval/134`, `failure_paraphrase`, repeat `0`：
  3 轮 stuck，最后是 `NameError: check_if_last_char_is_a_letter is not defined`。paraphrased failure summary 虽然更长，但没有更可执行。
- `HumanEval/132`, `task_simplification`, repeat `1`：
  一轮直接过。说明 simplification 有时也会帮它把任务边界压得更清楚。

## 6. Kimi 2.5

### 指标

- `clean`: `0.9817`
- `failure_paraphrase`: `0.9817`
- `failure_simplification`: `0.9756`
- `task_paraphrase`: `0.9756`
- `task_simplification`: `0.9817`

### 过程指标

- `clean`: round-0 pass `468/492`，average tokens `388.85`
- `task_simplification`: round-0 pass `396/492`，average tokens `901.28`

### 分析

Kimi 是这次实验里“最终结果很稳，但过程明显变脆”的最典型例子：

- final pass rate 几乎不动；
- process cost 变化很大；
- `task_simplification` 会明显增加 early deviation。

这不是无结果，而是一个很干净的 process fragility 结果：

> Kimi 大多数时候能修回来，但修回来并不便宜。

### failure surface

- 总共只有 `9` 个唯一失败 task
- failure 非常集中，不是满天散
- 仍然存在 perturbation-only failure，所以不能说 perturbation 完全没影响

### 抽样 case

- `HumanEval/134`, `task_paraphrase`, repeat `0`：
  3 轮 stuck，最终 `AssertionError`。这是 Kimi 少数被 task-side 扰动真实推离成功路径的例子。
- `HumanEval/50`, `failure_paraphrase`, repeat `0`：
  round 0 失败，但两轮内修回，并显式补上 `encode_shift`。这和你之前观察到的 Kimi failure-mode 分析是一致的。

## 7. Qwen-Turbo

### 指标

- `clean`: `0.8943`
- `failure_paraphrase`: `0.9024`
- `failure_simplification`: `0.8984`
- `task_paraphrase`: `0.8720`
- `task_simplification`: `0.9268`

### 分析

Qwen-Turbo 是这批云端 API 模型里最弱、也最容易出问题的一组：

- clean baseline 最低；
- 失败面最宽；
- `task_paraphrase` 最伤。

但同时，`task_simplification` 又明显提升最终 pass。  
所以这里不能讲成“task perturbation 一律有害”，更准确的是：

- paraphrase 对它不利；
- simplification 对它反而常常有利；
- 但两者都会增加 prompt / repair 成本。

### failure surface

- 总共 `39` 个唯一失败 task
- `task_paraphrase` 额外引入 `15` 个 perturbation-only failed task
- 错误类型比别的组更杂：`AssertionError`、`NameError`、`TypeError`、`IndexError`

### 抽样 case

- `HumanEval/157`, `task_paraphrase`, repeat `2`：
  perturbed task 把函数名从 `right_angle_triangle` 改成 `check_right_triangle`，最终直接触发 `NameError`。这就是非常典型的 contract drift，不应该被伪装成纯 wording fragility。
- `HumanEval/134`, `task_simplification`, repeat `0`：
  一轮直接过。说明 simplification 对它有时确实是帮助。

## 8. Qwen-Plus

### 指标

- `clean`: `0.9390`
- `failure_paraphrase`: `0.9492`
- `failure_simplification`: `0.9451`
- `task_paraphrase`: `0.9472`
- `task_simplification`: `0.9675`

### 分析

Qwen-Plus 明显比 Qwen-Turbo 强，也更稳：

- clean 更高；
- 失败面更窄；
- 大多数 perturbation 条件不是伤害 clean，而是持平或更好。

最显著的还是 `task_simplification`：

- 最终 pass 提升明显；
- 但 token cost 也明显更高。

### failure surface

- 只有 `13` 个唯一失败 task
- `task_paraphrase` 几乎没有引入新的 perturbation-only failed task
- 剩下的失败仍主要是 `AssertionError` 和 `NameError`

### 抽样 case

- `HumanEval/93`, `task_simplification`, repeat `0`：
  3 轮 stuck，最终 `AssertionError`。
- `HumanEval/134`, `task_simplification`, repeat `0`：
  一轮直接成功。

这一对 case 很好地说明：

> simplification 的平均效果是有利的，但它不是对所有 task 都有利。

## 9. 本地 `qwen3-coder:30b`

### 指标

- `clean`: `0.9187`
- `failure_paraphrase`: `0.9228`
- `failure_simplification`: `0.9146`
- `task_paraphrase`: `0.9370`
- `task_simplification`: `0.9512`

### 分析

本地模型整体处在 Qwen-Turbo 和 Qwen-Plus 之间：

- 比 Qwen-Turbo 更稳；
- 比 Qwen-Plus 稍弱；
- 一个很重要的优点是：没有观察到 task-prompt 中函数名漂移。

这一点让它的 task-side 结果更接近“真实 prompt fragility”，而不是 contract drift 混杂效应。

### failure surface

- `23` 个唯一失败 task
- 失败仍以 `AssertionError` 为主
- 相比 Qwen-Turbo，错误分布更干净，失败面更窄

### 抽样 case

- `HumanEval/118`, `failure_simplification`, repeat `0`：
  failure summary 被压成 `AssertionError: expected true, got false`，信息过少，3 轮都修不回来。
- `HumanEval/134`, `task_simplification`, repeat `0`：
  经过 1 轮 repair 后成功。这个任务在多个模型上都对 simplification 友好。

## 跨组比较

## 1. DeepSeek vs Qwen vs Kimi

### 最终结果

- Kimi clean 最强：`0.9817`
- DeepSeek-Reasoner 次之：`0.9675`
- DeepSeek-Chat 几组集中在 `0.945–0.953`
- Qwen-Plus：`0.9390`
- 本地 `qwen3-coder:30b`：`0.9187`
- Qwen-Turbo 最低：`0.8943`

### 成本

- DeepSeek-Reasoner 成本远高于其他组
- Kimi 在中等成本下给出最强 clean baseline
- Qwen-Turbo 便宜但弱
- Qwen-Plus 花更多 token，但明显换来了更好的结果

### fragility pattern

- Kimi：最典型的“最终不怎么掉，但过程明显变脆”
- DeepSeek-Chat：最典型的“task_simplification 让过程变得又贵又易偏航”
- DeepSeek-Reasoner：最终稳，但 cost 非常高
- Qwen-Turbo：失败面最宽，对 task paraphrase 最敏感
- Qwen-Plus：明显优于 Qwen-Turbo
- 本地 qwen：比 Turbo 干净，比 Plus 稍弱，但没有函数名漂移这个混杂因素

## 2. Qwen 家族比较

### Qwen-Turbo vs Qwen-Plus

Qwen-Plus 明显更强：

- clean：`0.9390` vs `0.8943`
- task paraphrase：`0.9472` vs `0.8720`
- 唯一失败 task：`13` vs `39`
- task-prompt 函数名漂移率：`0.915%` vs `1.321%`

这不是细微差别，而是很清楚的代际差异。

### Qwen-Plus vs 本地 `qwen3-coder:30b`

本地模型最终结果不如 Qwen-Plus，但有一个分析优势：

- 没有观察到 task-prompt 函数名漂移。

所以它的 task-side 结果更容易解释为“prompt wording / information change”的影响，而不是 benchmark contract 被改坏。

## 3. DeepSeek 家族比较

### Chat vs Reasoner

DeepSeek-Reasoner 的最终正确率更高，但成本也明显更高：

- clean token：`1844.59` vs Chat 大约 `356–365`
- `task_simplification` token：`3590.13` vs Chat 大约 `951–986`

所以它不是简单地“更好”，而是：

> 用极大的 token 成本换更高的最终稳健性。

### DeepSeek-Chat 参数组比较

从 conservative、balanced、creative 这三组看：

- clean baseline 变化不大；
- `failure_paraphrase` 随着 creative 程度上升而明显变差；
- `task_paraphrase` 随着 creative 程度上升而变好；
- `task_simplification` 在所有 chat 组里都很贵。

当前最合理的读法是：

> 更高方差的 DeepSeek-Chat 更擅长吸收 reworded task，但更不擅长在 paraphrased failure signal 的引导下稳定修复。

## 4. 当前数据真正支持什么

### 强支持

- 不同注入阶段的影响时机不同；
- `task_*` 往往从 round `0` 开始影响；
- `failure_*` 往往从 round `1` 开始影响；
- final pass rate 单独看是不够的，过程指标非常关键。

### 有支持，但要收着讲

- 不同模型的过程鲁棒性确实不同；
- task simplification 经常增加 repair 工作量与 token 成本；
- Qwen-Turbo 明显比 Qwen-Plus 脆；
- DeepSeek-Reasoner 的最终结果比 DeepSeek-Chat 更稳，但不是更高效。

### 必须诚实加 caveat

- 不是所有正负效果都可以解释成“纯 prompt sensitivity”
- Kimi 和 Qwen API 的一部分 task-side 结果混入了 contract drift
- 所以它们的一部分 task fragility 应该被表述成 mixed effect，而不是纯 wording effect

## 图表状态与后续缺口

之前建议的跨模型图现在已经实现：

- `delta_final_pass_rate_heatmap.png`
- `delta_round0_pass_rate_heatmap.png`
- `delta_average_total_tokens_heatmap.png`
- `clean_accuracy_vs_cost.png`
- `deepseek_chat_parameter_sweep.png`
- `task_prompt_contract_drift.png`
- `perturbation_failure_overlap.png`

这批图已经足够支撑主报告里的跨模型比较。

如果后面还要继续补图，最有价值的是一类可选补充。

### 可选补充：按 condition type 拆开的 task-overlap 图

现在的 overlap heatmap 是把所有非 clean condition 合并在一起看的。
如果后面要写得更细，可以再拆两张：

- 只看 task-side perturbation induced failures
- 只看 failure-side perturbation induced failures

这样会更容易比较“哪些 task 是 task-stage 特别脆”和“哪些 task 是 repair-stage 特别脆”。

## 总体判断

当前这批数据已经足够支撑一份严肃的分析。

最重要的结论不是：

> perturbation 一定会大幅拉低最终准确率

而是：

> 不同阶段的扰动会以不同方式影响不同模型。很多时候，它改变的首先是轨迹而不是最终结果。Kimi 最能体现“最终稳但过程脆”的模式；DeepSeek-Reasoner 用更高成本换更高最终稳健性；Qwen-Turbo 是最弱、也最脆的 Qwen API 模型，Qwen-Plus 明显更强。与此同时，Kimi 和 Qwen API 的部分 task-side 结果混入了 contract drift，因此必须被诚实地表述为 mixed effect，而不是纯 wording sensitivity。
