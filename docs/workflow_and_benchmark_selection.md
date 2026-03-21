# Workflow And Benchmark Selection

1. 现在真正要的 workflow 是什么
2. 查到的几个 benchmark / agent 系统分别是什么
3. 哪些符合要求，哪些不符合，哪里需要改动
4. 最终应该怎么用到当前项目里

- **Source-backed facts**：官方 README、论文摘要、官方文档里明确写出来的内容
- **Project abstraction**：我们基于这些来源，为当前项目做的轻量化抽象

---

## 现在真正要的 workflow

我要的不是一个凭空捏造的 code agent workflow，也不是一个过于复杂、难以在课程项目里落地的完整产品系统。要求：

- **来源真实**：能明确对齐到已有软件工程 agent 系统，而不是纯想象
- **可控**：适合做 stage-wise prompt fragility 实验
- **可执行**：主实验不依赖重型 infra
- **有现实参照**：至少能接触到真实 GitHub issue setting
- **可解释**：能把每一步的输入、输出、反馈和偏航记录清楚

因此，当前最合适的目标不是“完整复刻某个现成系统”，而是：

> 用真实软件工程 agent 的 workflow 作为依据，抽象出一个 lightweight test-repair loop，用于研究 stage-wise instruction fragility。

---

## workflow 来源

## SWE-agent

### Source-backed facts

`SWE-agent` 的论文摘要、官方 README 和官方文档明确说明：

- 它的任务是修复 **real GitHub repositories** 里的 issue
- 它通过一个 **Agent-Computer Interface (ACI)** 让模型更容易：
  - 浏览仓库
  - 查看代码
  - 编辑代码
  - 执行测试和其他程序
- 它的整体目标是：给定 repo 和 issue，生成一个修复问题的 patch

官方来源：

- [SWE-agent paper (arXiv:2405.15793)](https://arxiv.org/abs/2405.15793)
- [SWE-agent GitHub README](https://github.com/SWE-agent/SWE-agent)
- [SWE-agent ACI documentation](https://swe-agent.com/0.7/background/aci/)
- [SWE-agent architecture documentation](https://swe-agent.com/0.7/background/architecture/)

ACI 文档还明确提到一些关键设计：

- edit 命令带 linter 检查
- 提供专门的 file viewer
- 提供专门的全目录搜索命令
- agent 需要依赖命令输出与反馈继续决策

架构文档还明确说：

- `run.py` 会启动环境
- 默认会启动 Docker container 和 shell session
- 模型动作会在这个 shell session 里执行
- 历史会被送回模型，必要时做 history compression

如果只保留文档明确支持的内容，`SWE-agent` 的 workflow 可以稳妥概括为：

1. 输入一个 repo 和一个 issue
2. agent 在代码环境中浏览、搜索、查看文件
3. agent 编辑代码
4. agent 执行测试或其他命令
5. agent 根据反馈继续修改
6. 最终输出一个 patch / 修复结果

### 是否完全符合当前项目

**部分符合，但不能直接拿来当主实验 workflow。**

符合的地方：

- 来源真实
- real-world software issue setting 很强
- workflow 有明确的仓库交互、代码编辑、测试执行

不符合的地方：

- 太重
- 带 ACI 和长期 shell session
- 更像完整 agent system，而不是轻量研究 scaffold
- 直接拿来做主实验，会把大量时间耗在环境与 agent 基建上

### 对当前项目应该怎么用

`SWE-agent` 适合充当：

- **workflow 的主要依据**
- **real-world software engineering reference**
- **附录或 case study 的来源背景**

它不适合直接作为你们主实验的完整实现模板。

---

## mini-SWE-agent

### Source-backed facts

`mini-SWE-agent` 的 README 明确写出：

- 它 **does not have any tools other than bash**
- 它 **has a completely linear history**
- 它通过 `subprocess.run` 执行动作
- 每个 action **completely independent**
- 它适合简单控制流、稳定 sandbox、benchmark evaluation
- 它也用于解决 GitHub issues

官方来源：

- [mini-SWE-agent GitHub README](https://github.com/SWE-agent/mini-swe-agent)

README 还明确比较了 `mini-SWE-agent` 和 `SWE-agent`：

- 如果你想要更简单的控制流、更快更稳定的 sandbox 和 benchmark evaluation，推荐 `mini-SWE-agent`
- 如果你想试验不同工具集和 history processors，则去用 `SWE-agent`

### 这意味着什么

在不越界的前提下，`mini-SWE-agent` 的 workflow 可以概括为：

1. 输入任务或 issue
2. 模型基于当前 message history 生成下一步 action
3. action 通过 bash / `subprocess.run` 执行
4. 输出追加到线性 history
5. 下一步继续根据这个 history 决策
6. 重复直到结束

### 是否完全符合当前项目

**非常接近。**

符合的地方：

- 来源真实
- 结构轻
- 控制流简单
- 很适合做可解释、可记录的 trajectory 分析
- 非常适合作为 lightweight scaffold 的工程依据

不完全符合的地方：

- 它不是专门为“stage-wise prompt fragility”设计的
- 它没有天然把流程切成 `Task Prompt / Failure Summary / Revision Prompt` 这样的实验阶段
- 它的 bash-only 设计更通用，你们还需要把它抽象成更适合代码任务的 test-repair loop

### 对当前项目应该怎么用

`mini-SWE-agent` 最适合充当：

- **轻量 workflow 的直接工程依据**
- **控制流设计参考**
- **实验系统实现风格参考**

---

## benchmark 选型

## HumanEval+ / EvalPlus

### Source-backed facts

`EvalPlus` 官方仓库明确说明：

- `HumanEval+` 是对原始 HumanEval 的更严格版本
- 它有 **80x more tests than the original HumanEval**
- `EvalPlus` 提供更严格、更安全的代码评测框架

官方来源：

- [EvalPlus GitHub](https://github.com/evalplus/evalplus)
- [HumanEval+ on Hugging Face](https://huggingface.co/datasets/evalplus/humanevalplus)

Hugging Face 页面当前显示：

- `HumanEval+` 有 **164** 个任务

### benchmark 内容是什么

它本质上是：

- 给你一个函数级别编程任务
- 让模型生成代码
- 再用更严格的单元测试去验证

### workflow 是什么

这不是 repository-level issue fixing benchmark。它更像：

1. 给一个函数任务
2. 生成代码
3. 跑测试
4. 判断是否通过

如果我们自己加上 repair loop，它就会变成：

1. 读题
2. 生成代码
3. 跑测试
4. 形成失败摘要
5. 修复
6. 重复

注意：**后面这个多轮 loop 不是 HumanEval+ 自带的，而是你们在其上构造出来的实验 workflow。**

### 是否符合要求

**符合主实验要求，但不符合“real-world case”要求。**

符合的地方：

- 轻量
- 严格
- 任务清楚
- 方便做控制实验
- 很适合研究 stage-wise fragility

不符合的地方：

- 不是真实 GitHub issue
- 不是 repository-level software engineering task

### 对当前项目应该怎么用

它应该用作：

- **主实验 benchmark**

原因是它能把变量控制住，让你真正测到 prompt fragility，而不是环境复杂度。

---

## SWE-bench Lite

### Source-backed facts

`SWE-bench` 官方 README 明确说明：

- 这是一个 benchmark for evaluating large language models on **real world software issues collected from GitHub**
- 给定 codebase 和 issue，模型需要生成一个能解决问题的 patch
- `SWE-bench Lite` 是其提供的一个数据变体
- 评测依赖 Docker
- 官方明确警告评测 **resource intensive**
- 推荐环境至少：
  - 120GB free storage
  - 16GB RAM
  - 8 CPU cores

官方来源：

- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)

README 还明确给出 Lite 的评测命令入口：

- `python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Lite ...`

### benchmark 内容是什么

它本质上是：

- 真实开源仓库
- 真实 issue
- 真实 patch-style 修复任务

### 它的 workflow 是什么

从 benchmark 角度看，它的任务流程是：

1. 输入 repo + issue
2. 系统生成 patch
3. 评测 harness 在容器里验证 patch 是否解决问题

### 是否符合你的要求

**非常符合“real-world case”要求，但不适合做主实验。**

符合的地方：

- 真实 GitHub issue
- 真实软件工程任务
- 非常适合做现实参照

不符合主实验的地方：

- 太重
- 评测复杂
- Docker / 磁盘 / CPU 成本高
- 对课程项目主线不友好

### 对当前项目应该怎么用

它最合适的定位是：

- **real-world case study benchmark**
- **附录 / 外部有效性验证**

你们可以只挑 **3 到 5 个实例** 做定性或小样本对照。

---

## 原始 HumanEval

### Source-backed facts

原始 `HumanEval` 是 OpenAI 发布的代码生成 benchmark。
`EvalPlus` 官方明确把 `HumanEval+` 描述为比原始版本更严格。

官方来源：

- [HumanEval GitHub](https://github.com/openai/human-eval)
- [EvalPlus GitHub](https://github.com/evalplus/evalplus)

### 是否适合当前项目

**不如 HumanEval+。**

如果已经决定用 EvalPlus，就没必要把原始 HumanEval 作为主线 benchmark。

它最多只适合作为：

- 附录对照
- 说明更严格测试会减少伪通过

---

## 最终推荐组合

当前最合理的组合就是：

- **workflow 依据**：`SWE-agent + mini-SWE-agent`
- **主实验 benchmark**：`HumanEval+ / EvalPlus`
- **real-world case study**：`SWE-bench Lite` 小样本

---

## 为什么这个组合最合理

## workflow 不是虚构的

来源有两个层次：

- `SWE-agent` 提供真实 repository-level issue-fixing workflow
- `mini-SWE-agent` 提供简单、线性、可控的 agent scaffold

所以你们的系统不是凭空捏造，而是：

> a lightweight abstraction grounded in real software engineering agent workflows.

## 主实验还能做完

`HumanEval+ / EvalPlus` 的变量更可控，更适合做：

- stage-wise perturbation
- trajectory logging
- recovery analysis

## 也能诚实覆盖 real-world setting

通过 `SWE-bench Lite` 的少量 case study，你们可以说：

- 主实验在可控 benchmark 上完成
- 外部有效性用真实 GitHub issue 做小规模验证

这个说法是稳的。

---

## Solution

### 目标 workflow

1. 输入一个代码任务
2. 构造 task prompt
3. 让模型生成代码
4. 运行测试
5. 把失败信息整理成 failure summary
6. 让模型基于失败信息修复代码
7. 重复直到通过或达到轮数上限

### 它和来源系统的关系

- 它**不是** `SWE-agent` 的逐行复刻
- 它**不是** `mini-SWE-agent` 的原样拷贝
- 它是对这两者共有核心的轻量抽象：
  - 任务输入
  - 代码环境操作
  - 执行反馈
  - 迭代修复

### 它还需要什么改动

为了适配当前研究问题，这个 workflow 还必须做三件额外的事情：

1. **显式阶段化**
   把输入切成 `Task Prompt` 和 `Failure Summary` 两个可控注入点
2. **结构化日志**
   每一轮都记录 prompt、代码、测试结果、失败摘要、token 成本、是否恢复
3. **实验条件开关**
   能稳定切换：

   - clean
   - task perturbation
   - failure-summary perturbation

这些是研究需要，不是原系统直接提供的。

---

## 如何用到当前项目

## 写进报告时怎么说

> Our workflow is not a fictional agent loop invented from scratch. It is a lightweight abstraction grounded in real software engineering agent systems, primarily SWE-agent and mini-SWE-agent. SWE-agent provides the repository-level issue-resolution setting with browsing, editing, and execution feedback, while mini-SWE-agent provides a simple, linear, and bash-centered control flow that is easier to adapt into a controlled research scaffold.

然后再补一句：

> For controlled main experiments, we use HumanEval+ / EvalPlus. For real-world external validity, we add a small SWE-bench Lite case-study section.

## 代码实现时怎么落地

当前项目的代码结构应该围绕这个抽象来建：

- `TaskPromptBuilder`
- `Solver`
- `TestRunner`
- `FailureSummaryBuilder`
- `RepairSolver`
- `ExperimentRunner`
- `MetricsCollector`

其中：

- `TaskPromptBuilder` 和 `FailureSummaryBuilder` 是两个主要注入点
- `TestRunner` 对接 EvalPlus 或 SWE-bench harness
- `ExperimentRunner` 负责 condition switching

## benchmark 使用策略

### 主实验

- 用 `HumanEval+ / EvalPlus`
- 目的是测 clean vs perturbed 条件
- 强调 stage-wise fragility

### 小样本现实案例

- 用 `SWE-bench Lite`
- 只跑 3 到 5 个实例
- 目的是展示 workflow 在真实 issue setting 中也有对应现象

---

## 结论

如果只问一句：

> 我们到底该采用什么 workflow 和 benchmark 组合？

答案就是：

- **workflow 依据**：`SWE-agent + mini-SWE-agent`
- **主实验**：`HumanEval+ / EvalPlus`
- **现实案例**：`SWE-bench Lite` 小样本

这个组合满足三件事：

- workflow 来源真实，不是虚构
- 主实验可控，适合做 prompt fragility 研究
- 也能接触真实 GitHub issue setting

---

## Links

- [SWE-agent paper](https://arxiv.org/abs/2405.15793)
- [SWE-agent GitHub](https://github.com/SWE-agent/SWE-agent)
- [SWE-agent ACI docs](https://swe-agent.com/0.7/background/aci/)
- [SWE-agent architecture docs](https://swe-agent.com/0.7/background/architecture/)
- [mini-SWE-agent GitHub](https://github.com/SWE-agent/mini-swe-agent)
- [EvalPlus GitHub](https://github.com/evalplus/evalplus)
- [HumanEval+ dataset](https://huggingface.co/datasets/evalplus/humanevalplus)
- [HumanEval GitHub](https://github.com/openai/human-eval)
- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)
