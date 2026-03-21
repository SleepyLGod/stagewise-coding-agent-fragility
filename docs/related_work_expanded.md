# Related Work

---

## 0. 先说结论：这个方向的文献脉络到底是什么？

现在的题目是：

> **Stage-wise Prompt Fragility in a Lightweight Test-Repair Coding Loop**

要把 related work 讲清楚，最好的方式不是按时间线硬排，而是按 **“研究层级”** 来排：

### 第一层：Prompt sensitivity 作为一般现象
这些工作关心的是：  
**同样意思的 prompt，只是换个说法，模型为什么会表现不同？这种差异该怎么测？**

代表：
- ProSA
- POSIX
- PromptRobust

### 第二层：这个现象在代码生成里到底意味着什么
这些工作关心的是：  
**代码任务为什么对 prompt 特别敏感？是因为模型不会写代码，还是因为题面/描述方式改变了模型对任务的理解？**

代表：
- More Than a Score / PartialOrderEval
- Code Roulette
- CodeCrash

### 第三层：从单轮输出走向 agent / workflow
这些工作关心的是：  
**当系统不只是回答一次，而是要分步骤决策、调用工具、继续修复时，微小扰动会不会沿轨迹传播？**

代表：
- RobustFlow
- AgentNoiseBench

### 第四层：评测本身靠不靠谱
这些工作关心的是：  
**我们看到的“prompt sensitivity”到底是真脆弱，还是评测方法把它夸大了？**

代表：
- ReliableEval
- Flaw or Artifact?

---

## 1. 论文总表：先把文章“找出来”

> 下面优先放 **官方页 / 官方论文页**。  
> `PartialOrderEval` 不是独立论文名，而是 **More Than a Score** 这篇论文里提出的方法框架。

| 主题组 | 论文 | 年份 / 发表状态 | 官方入口 |
|---|---|---:|---|
| 通用 prompt sensitivity | **ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs** | EMNLP Findings 2024 | https://aclanthology.org/2024.findings-emnlp.108/ |
| 通用 prompt sensitivity | **POSIX: A Prompt Sensitivity Index For Large Language Models** | EMNLP Findings 2024 | https://aclanthology.org/2024.findings-emnlp.852/ |
| 通用 robustness benchmark | **PromptRobust: Towards Evaluating the Robustness of Large Language Models on Adversarial Prompts** | arXiv（v5, 2024） | https://arxiv.org/abs/2306.04528 |
| 代码生成 prompt specificity | **More Than a Score: Probing the Impact of Prompt Specificity on LLM Code Generation** | arXiv 2025 | https://arxiv.org/abs/2508.03678 |
| 代码生成 prompt variability | **Code Roulette: How Prompt Variability Affects LLM Code Generation** | arXiv v2（2026） | https://arxiv.org/abs/2506.10204 |
| agent/workflow robustness | **RobustFlow: Towards Robust Agentic Workflow Generation** | arXiv v2（2025） | https://arxiv.org/abs/2509.21834 |
| noisy agent benchmark | **AgentNoiseBench: Benchmarking Robustness of Tool-Using LLM Agents Under Noisy Condition** | arXiv v2（2026） | https://arxiv.org/abs/2602.11348 |
| code reasoning robustness | **CodeCrash: Exposing LLM Fragility to Misleading Natural Language in Code Reasoning** | NeurIPS 2025 poster | https://neurips.cc/virtual/2025/poster/119313 |
| evaluation methodology | **ReliableEval: A Recipe for Stochastic LLM Evaluation via Method of Moments** | EMNLP Findings 2025 | https://aclanthology.org/2025.findings-emnlp.594/ |
| evaluation artifact critique | **Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs** | EMNLP 2025 | https://aclanthology.org/2025.emnlp-main.1006/ |

---

## 2. 先给你一张“研究地图”

你可以把这些工作理解成一条很自然的研究链条：

1. **先发现问题**  
   模型对 prompt 很敏感。  
   —— ProSA, POSIX

2. **再把问题系统化**  
   构造扰动、做 benchmark、看 robustness。  
   —— PromptRobust

3. **再问：代码任务是不是也这样？**  
   而且代码任务里，这种敏感性和 prompt 细节、提示信息量、自然语言误导有关。  
   —— More Than a Score, Code Roulette, CodeCrash

4. **再升级到 agent setting**  
   一旦模型不是单轮输出，而是会分步做事、调用工具、解释失败、继续修复，扰动就不只是“答错一次”，而是会影响整条轨迹。  
   —— RobustFlow, AgentNoiseBench

5. **最后反思：我们是不是把问题看大了？**  
   有些“敏感性”也许是评测方法太僵硬造成的。  
   —— ReliableEval, Flaw or Artifact?

你的项目恰好站在 **第 3 层和第 4 层之间**：

- 比单轮 code generation 更进一步，因为你研究 **test-repair loop**
- 比通用 noisy agent benchmark 更聚焦，因为你研究 **coding agent 的阶段性脆弱性**
- 但又必须吸收第 5 层的教训：**别把评测伪影误当成模型 fragility**

---

# 3. 逐篇扩展分析

---

## 3.1 ProSA

### 基本信息
- **论文名**：ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs
- **发表**：Findings of EMNLP 2024
- **入口**：https://aclanthology.org/2024.findings-emnlp.108/

### 这篇论文在解决什么问题？
很多人会说：“LLM 对 prompt 很敏感。”  
但问题是，这句话通常停留在现象层面，像一种抱怨，而不是一个可测量、可分析的研究对象。

ProSA 要解决的是：

> **如何把“prompt sensitivity”从 anecdote（零散案例）变成一个系统的评估问题？**

也就是说，作者不满足于只展示几个“换个说法结果就不同”的例子，而是想把它变成一套框架：
- 怎么定义 prompt sensitivity
- 怎么在不同任务、不同模型之间比较
- 怎么看 sensitivity 是全局现象，还是某些样本特别严重
- 怎么解释这种现象为什么会发生

### 它的方法核心是什么？
ProSA 的核心贡献不是某个 fancy trick，而是一个 **框架化视角**：

1. **它把 prompt sensitivity 做成指标**
   - 提出 PromptSensiScore（PSS）
   - 目标是衡量：对同一个任务，如果只改 prompt 表达，模型输出会有多大变化

2. **它强调 instance-level analysis**
   - 不是只看平均分
   - 而是看：哪些具体样本特别敏感，哪些不敏感

3. **它引入 decoding confidence 来解释机制**
   - 也就是：当模型对当前生成不够稳定、不够自信时，prompt 的微小变化更可能把它推向另一条输出轨道

### 这篇论文真正的 research 本质
它最重要的地方不是“又发现模型会抖”，而是：

> **Prompt sensitivity 不是噪声边角料，而是模型行为本身的一部分，应该被像 accuracy 一样正式研究。**

换句话说，ProSA 在做的是“把脆弱性正名”。

### 对你项目有什么用？
它对你最有价值的地方有三点：

1. **给你一个理论起点**  
   你不是凭感觉说“prompt 好像会影响 agent”，而是站在已有工作上说：  
   prompt sensitivity 本身已经是可被测量和解释的问题。

2. **提醒你不要只报平均通过率**  
   既然 ProSA 强调 instance-level variability，你的项目也不应该只报整体 pass rate。  
   你最好至少补：
   - 哪些任务特别脆弱
   - 哪些扰动一换就偏航
   - 哪些任务几乎不受影响

3. **给你“偏航”概念提供心理模型**  
   如果某些输入本来就在模型决策边界附近，那么 prompt 的小改动就更可能把它推向另一条轨迹。  
   这和你要讲的 **error propagation / recovery** 非常相容。

### 这篇论文不能直接替你解决什么？
它不是 coding paper，也不是 agent paper。  
所以它不能直接回答：
- code generation 为什么会掉点
- 多轮 loop 里扰动会怎么传播
- 后续步骤能不能恢复

所以你在 report 里应该把它写成：
> **general prompt sensitivity foundation**
而不是“closest related work”。

---

## 3.2 POSIX

### 基本信息
- **论文名**：POSIX: A Prompt Sensitivity Index For Large Language Models
- **发表**：Findings of EMNLP 2024
- **入口**：https://aclanthology.org/2024.findings-emnlp.852/

### 它在解决什么问题？
ProSA 更像“做一套 sensitivity study”。  
POSIX 更像在问：

> **有没有一个更直接、更模型内部的方式来量化 prompt sensitivity？**

作者的核心思路是：  
如果两个 prompt **intent-preserving**（意图不变），那模型面对它们时，不应该对同一个答案表现出巨大的偏好变化。  
如果变化很大，说明模型对 prompt 表达形式本身过于敏感。

### 它的方法核心是什么？
POSIX 的关键思想是：

- 比较 **同一个回答** 在不同但意图保持的 prompt 下的 log-likelihood 变化
- 如果 prompt 一换，这个回答的概率大幅波动，说明模型 sensitivity 高

这和只看最终 accuracy 不一样。  
accuracy 像是看“考试分数”。  
POSIX 更像是看“模型内心其实有多动摇”。

### 研究本质是什么？
POSIX 的研究本质是：

> **把 prompt sensitivity 看成模型分布稳定性的问题，而不仅仅是最终答对/答错的问题。**

这很重要，因为有时候两个 prompt 最终都“答对”，但模型内部的信心分布其实已经完全不一样了。  
这种不稳定在 multi-step agent 里尤其危险，因为它可能在后续轮次放大。

### 对你项目有什么启发？
有启发，但不能照搬。

#### 可借鉴的点
1. **“阶段敏感性”不一定非要只看最终 pass/fail**
   你可以把思路迁移为：
   - clean 与 perturbed 条件下，agent 在第几轮开始出现明显轨迹分叉
   - 同一个 failure signal 是否引发完全不同的修复方向

2. **提醒你：最终成功率只是表面**
   真实研究价值在于：
   - 模型是否稳定理解相同任务
   - 对相同失败反馈是否会做出相近修复

#### 不能照搬的点
如果你用 DeepSeek API，很可能拿不到足够细的 token-level log-likelihood。  
所以 POSIX 更适合做 **conceptual inspiration**，不太适合做你项目的主要指标实现。

### 你在报告里该怎么写它？
很适合写成：

> POSIX 说明 prompt sensitivity 可以被形式化为模型响应分布对意图保持改写的稳定性问题；相比最终 task accuracy，这种视角更强调模型内部偏好变化。我们的项目不直接复现 POSIX 指标，而是把“稳定性”迁移到多轮 coding loop 的轨迹层面。

---

## 3.3 PromptRobust

### 基本信息
- **论文名**：PromptRobust: Towards Evaluating the Robustness of Large Language Models on Adversarial Prompts
- **状态**：arXiv（2023 提交，2024 有更新版）
- **入口**：https://arxiv.org/abs/2306.04528

### 它在解决什么问题？
Prompt sensitivity 有一个常见漏洞：  
很多论文只做少量、人工挑选的 prompt 改写，结果容易不系统。

PromptRobust 在解决的是：

> **怎么系统、规模化、跨任务地测试 LLM 对“轻微但合理”的 prompt 扰动是否稳健？**

### 它的方法核心是什么？
这篇论文做了一个 robustness benchmark：

- 覆盖多个任务
- 覆盖多个数据集
- 构造多层级文本攻击：
  - 字符级
  - 词级
  - 句子级
  - 语义级

这些攻击不是完全乱改，而是尽量模仿真实用户会出现的偏差，比如：
- typo
- 同义词替换
- 轻微措辞变化

### 研究本质是什么？
它的本质不是“做攻击”，而是：

> **把 prompt robustness 从零散现象变成 benchmarkable property。**

也就是：
- robustness 不是附属品
- robustness 本身就是需要被测的能力

### 对你项目有什么价值？
很有价值，但要谨慎用。

#### 它能给你的
1. **扰动类型设计思路**
   你 proposal 里提的：
   - semantic paraphrase
   - structural reordering
   - redundant context injection
   - mild simplification

   这些都和 PromptRobust 的“系统构造扰动”精神一致。

2. **支持“LLM 生成 + 人工抽查”这一流程**
   PromptRobust 告诉你：  
   构造扰动不是随便改句子，而是要尽量让扰动类型可控、可分类、可复查。

#### 它提醒你要小心的
PromptRobust 里很多设置带有 adversarial flavor。  
但你的项目不应该把自己写成“对抗攻击 agent”。  
你的定位应该更窄：

> **approximately meaning-preserving perturbations in a coding-agent loop**

也就是说，你研究的是“看似无害的改写是否造成严重后果”，不是“恶意攻击模型”。

### 你报告里适合怎么放？
你可以把它写成：
- 作为 **扰动设计** 的重要参考
- 但同时指出：你的 setting 更强调 **coding + trajectory + stage-wise injection**
- 所以不是直接复刻 PromptRobust benchmark

---

## 3.4 More Than a Score / PartialOrderEval

### 基本信息
- **论文名**：More Than a Score: Probing the Impact of Prompt Specificity on LLM Code Generation
- **状态**：arXiv 2025
- **入口**：https://arxiv.org/abs/2508.03678
- **备注**：`PartialOrderEval` 是这篇论文提出的方法框架，不是另一篇独立论文

### 它在解决什么问题？
这篇论文问了一个非常关键的问题：

> **代码模型在某些 benchmark 上表现差，到底是因为不会写，还是因为 prompt 给得不够具体？**

这比“prompt 会影响表现”更深一层。  
因为它不是只说“prompt 重要”，而是在区分两种解释：

1. 模型能力不够  
2. 题目描述不够细，导致模型没被正确“唤起”

### 它的方法核心是什么？
它提出 **PartialOrderEval**：

- 对同一道代码题，构造一个从 **最简 prompt** 到 **最详细 prompt** 的偏序链
- 看随着 prompt specificity 增加，pass@1 怎么变化

也就是说，它不是简单比较 A/B 两个 prompt，  
而是研究：

> **“提示信息量”这一维度本身，如何系统影响代码生成。**

### 研究本质是什么？
这篇论文真正打中的点是：

> **有时候我们以为模型“不会”，其实只是 prompt 没把任务约束讲清楚。**

这对代码任务尤其重要，因为代码题常常有：
- 输入输出格式要求
- 边界条件
- 错误处理
- 隐含约束

只要 prompt 少说一点，模型就可能不是“能力差”，而是“任务理解少了一块”。

### 对你项目有什么直接意义？
非常重要，原因有两个。

#### 1. 它帮你避免一个大坑：把“改写”做成“降信息量”
你项目里最危险的 methodological bug 是：

> 你说你在做 meaning-preserving perturbation，  
> 但实际上你悄悄删掉了重要约束信息。

一旦发生这种事，你测到的就不是 fragility，而是 **underspecification**。

所以这篇论文对你最大的提醒是：

- paraphrase 可以做
- simplification 要非常小心
- 不要让 perturbed prompt 变成“信息更少的题”

#### 2. 它说明“代码任务对 prompt 细节真的敏感”
这就给你的项目一个很自然的前提支撑：
- 代码生成不是纯知识回忆
- 很多时候是任务约束对齐问题
- 所以 coding agent 后续的 test-debug loop 更容易被早期理解偏差拖偏

### 你在报告里该怎么定位这篇？
这应该是你的 **closest non-agent code-generation neighbor** 之一。

你可以这样概括它和你的差别：

- 它研究的是 **单轮 code generation 中 prompt specificity 的作用**
- 你研究的是 **多轮 coding agent loop 中不同阶段的语义扰动如何影响轨迹与恢复**

这个区分非常关键。

---

## 3.5 Code Roulette

### 基本信息
- **论文名**：Code Roulette: How Prompt Variability Affects LLM Code Generation
- **状态**：arXiv v2（2026）
- **入口**：https://arxiv.org/abs/2506.10204

### 它在解决什么问题？
如果说 More Than a Score 更强调“prompt 要不要更具体”，  
那 Code Roulette 更像在问：

> **同一个代码任务，只是换一些表述、typo、同义替换、改写，输出代码会漂成什么样？**

它关注的是 **prompt variability** 对代码输出稳定性的影响。

### 它的方法核心是什么？
这篇论文做了一个通用 evaluation pipeline，大意是：

1. 对代码任务 prompt 做不同级别的改写/扰动
   - keyboard typos
   - synonyms
   - paraphrasing

2. 让模型重新生成代码

3. 不只看 pass/fail，还看 **代码相似度**
   - 用语法树（syntax-tree）相关指标，衡量代码输出结构到底变了多少

### 它的核心发现
公开摘要和正文可见的信息表明：

- typo 会让代码相似度下降很快
- synonyms / paraphrasing 相对更稳一些
- 不同模型都呈现出某种共同脆弱模式

### 研究本质是什么？
这篇论文的 research essence 是：

> **在代码任务里，prompt 变化不是只会影响“分数”，还会改变程序本身的结构路径。**

这点非常适合你吸收。  
因为你研究的不是简单掉点，而是 **trajectory deviation**。

### 对你项目有什么启发？
很大。

#### 启发 1：中间指标不一定只能是 pass rate
除了最终测试通过率，你还可以考虑：
- clean 和 perturbed 条件下代码 diff 大小
- AST 相似度（如果时间够）
- 第一次明显分叉出现在第几轮

#### 启发 2：prompt 变化会带来“程序结构漂移”
这和你的 “First Deviation Step” 很契合。  
你要讲的不是“同一道题有没有过”，而是：
- 轨迹什么时候开始偏
- 偏了之后能不能回正

#### 启发 3：typo 与 paraphrase 不一定是同一类脆弱性
如果你以后要扩展项目，Code Roulette 支持你把：
- semantic-preserving paraphrase
- noisy corruption / typo
拆成两条不同实验线。

### 你该怎么和它区分？
一定要写清楚：

- Code Roulette 仍主要是 **single-step code generation**
- 你是 **multi-step test-repair loop**
- 它重在输出代码的稳定性
- 你重在 **阶段扰动、误差传播、恢复能力**

---

## 3.6 RobustFlow

### 基本信息
- **论文名**：RobustFlow: Towards Robust Agentic Workflow Generation
- **状态**：arXiv v2（2025）
- **入口**：https://arxiv.org/abs/2509.21834

### 它在解决什么问题？
这篇论文研究的是 agentic workflow generation。  
核心问题是：

> **为什么输入说明其实语义一样，但模型生成出来的 workflow 却结构差很多？**

这和单轮答题不同，因为 workflow 是结构化过程：
- 有节点
- 有步骤
- 有拓扑关系
- 有依赖顺序

### 它的方法核心是什么？
它做了两件事：

1. **定义 workflow consistency 的评估方式**
   - 不是只看最终输出
   - 而是看 workflow 的节点相似性、拓扑相似性

2. **提出 RobustFlow 训练框架**
   - 用 preference optimization 训练模型在同义任务描述下保持 workflow 稳定

### 研究本质是什么？
这篇论文最有价值的 insight 是：

> **在 agent 系统里，鲁棒性不只是“最后答对没答对”，而是“中间过程结构是否稳定”。**

这是你项目非常需要借的一个 framing。  
因为你也不是只在看 final pass rate，  
你更在看：
- 轨迹是不是早早偏了
- 偏了之后有没有恢复
- 某些阶段是不是天然更脆弱

### 对你项目有什么价值？
它是你最重要的 **conceptual neighbor** 之一。

#### 它支持你的地方
1. **支持“multi-step systems deserve their own robustness study”**
   也就是：  
   agent 的 prompt fragility 不能简单套用单轮 setting 的结论。

2. **支持你看轨迹而不是只看终点**
   这让你研究：
   - first deviation
   - recovery
   - stage-wise fragility
有了明确文献支点。

#### 它和你的差别
- RobustFlow 研究的是 **workflow generation**
- 你研究的是 **coding repair loop**
- 它做了训练方法
- 你做的是 **evaluation / analysis**
- 它关心 workflow consistency
- 你关心 **错误传播与修复行为**

### 你的 report 里最好的写法
你可以把它写成：

> RobustFlow 说明语义等价指令在 agentic workflow setting 中也会造成显著不一致，证明 prompt robustness 在 multi-step systems 中不是边缘问题。相比之下，我们不研究 workflow synthesis，而研究 coding agent test-repair loop 中的阶段性偏航与恢复。

---

## 3.7 AgentNoiseBench

### 基本信息
- **论文名**：AgentNoiseBench: Benchmarking Robustness of Tool-Using LLM Agents Under Noisy Condition
- **状态**：arXiv v2（2026）
- **入口**：https://arxiv.org/abs/2602.11348

### 它在解决什么问题？
很多 agent benchmark 默认环境很干净：
- 用户说明清晰
- 工具返回格式稳定
- 外界噪声少

但真实世界不是这样。  
AgentNoiseBench 问的是：

> **如果环境里存在真实噪声，tool-using agent 到底有多脆？**

### 它的方法核心是什么？
这篇论文的设计很适合你借鉴，因为它不是随便加噪音，而是：

1. **先分析真实世界里噪声来自哪里**
2. **把噪声分成两大类**
   - user-noise
   - tool-noise
3. **在保留任务可解性的前提下注入可控噪声**
4. **做 trajectory-aware evaluation**

这一步很关键。  
因为好的 robustness benchmark 不是把任务搞到不可做，而是：

> **在“理论上仍然可做”的情况下，看系统会不会因为噪声而崩。**

### 研究本质是什么？
它抓住的本质是：

> **agent 的 fragility 往往不是来自“不会做任务”，而是来自“在不完美交互条件下，系统无法维持稳定决策”。**

这是一个非常 agentic 的视角。

### 对你项目有什么直接帮助？
几乎是最贴近的方法参考之一。

#### 你可以直接借的思想
1. **stage-wise injection 是合理的**
   你的项目做 Task / Failure Summary / Revision 三阶段注入，这个思路和 AgentNoiseBench 的“按 interaction point 注入噪声”非常一致。

2. **trajectory-aware analysis 是必要的**
   不能只报 final success，要看：
   - 哪里开始偏
   - 偏航后能否恢复
   - 噪声是把 agent 推错一次，还是让它持续沿错路走

3. **保留 task solvability**
   你的扰动必须尽量语义保持。  
   否则你研究的就不是 noise fragility，而是故意改题。

### 你和它的差别在哪里？
- 它更 general，面向 tool-using agents
- 你更聚焦，面向 coding agent
- 它强调 noisy environment
- 你强调 **instruction perturbation inside a repair loop**
- 它更像 benchmark paper
- 你更像 focused study

### 你在 report 里该怎么写？
这篇是你 **最强的方法论邻居** 之一。  
你完全可以说：

> AgentNoiseBench 为阶段性噪声注入、保持可解性的扰动构造和 trajectory-aware 评测提供了直接启发。我们的不同点在于：我们聚焦 coding repair loop 中的 instruction-level perturbation，而不是更一般的 noisy agent environment。

---

## 3.8 CodeCrash

### 基本信息
- **论文名**：CodeCrash: Exposing LLM Fragility to Misleading Natural Language in Code Reasoning
- **状态**：NeurIPS 2025 poster
- **入口**：https://neurips.cc/virtual/2025/poster/119313

### 它在解决什么问题？
这篇论文非常有意思，因为它点出了一个很多人直觉上忽视的点：

> **代码任务不只是“看代码”，模型也会被自然语言描述误导。**

也就是说，模型可能并没有真的严格按照代码执行逻辑推理，  
而是在大量依赖自然语言线索、叙述暗示、上下文气氛。

### 它的方法核心是什么？
它构造了一个 stress-testing framework：
- 数据来自 CRUXEVAL 和 LIVECODEBENCH
- 加入 structural perturbations
- 加入 misleading natural language contexts

然后测模型在 code reasoning 任务中的稳定性。

### 核心发现
公开摘要里最重要的发现是：

- 模型经常 **shortcut reasoning**
- 会过度依赖自然语言线索
- 即使加了 Chain-of-Thought，仍然会因为误导性自然语言而明显掉点

### 研究本质是什么？
这篇论文的本质是：

> **代码相关任务中的失败，不一定来自代码理解本身，也可能来自模型被“看起来很合理的自然语言解释”带偏。**

这句话和你项目非常对味。  
因为在 test-repair loop 里，后续阶段大量依赖自然语言中间表示：
- failure summary
- revision instruction
- self-reflection

这些东西如果写得不稳，很可能会把 agent 从正确轨道拉走。

### 对你项目的关键启发
我认为 CodeCrash 对你最重要的帮助是：

1. **支持“中后期语言反馈更危险”这一假设**
   也就是：
   - 初始 task prompt 改写可能只是轻微理解偏差
   - 但 failure summary / revision prompt 的误导性语言，可能会直接让 agent 选错修复方向

2. **解释为什么自然语言中间层是高风险点**
   代码 agent 很多人只盯着代码输出，  
   但这篇工作提醒你：  
   **自然语言解释层本身就是 fragility 的载体。**

### 你该怎么用它？
不要把它写成“closest identical work”，因为它还是 code reasoning，不是完整 agent loop。  
但它非常适合做：
- 动机强化
- failure summary 阶段为何重要的理论支持
- 说明“语言误导”会伤害代码相关推理

---

## 3.9 ReliableEval

### 基本信息
- **论文名**：ReliableEval: A Recipe for Stochastic LLM Evaluation via Method of Moments
- **发表**：Findings of EMNLP 2025
- **入口**：https://aclanthology.org/2025.findings-emnlp.594/

### 它在解决什么问题？
这篇论文在问一个更“统计学”的问题：

> **如果模型对 prompt 很敏感，那我们凭什么用单个 prompt 的分数来评价模型？**

也就是说，它不满足于“承认 prompt sensitivity 存在”，  
它继续追问：

- 那 benchmark 结果还可信么？
- 要采多少个 prompt 变体，结论才算稳？
- 什么时候我们看到的差异只是 sampling noise？

### 它的方法核心是什么？
ReliableEval 提出的是一种 **stochastic evaluation** 思想：

- 不把模型表现看成一个固定数
- 而把它看成在“meaning-preserving prompt perturbation 空间”上的一个分布
- 再用 method of moments 去估计：
  - 期望
  - 方差
  - 需要多少 resamplings 才能得到有意义的结论

### 研究本质是什么？
它的本质非常重要：

> **当 prompt 本身就是随机变量时，模型性能也不该被当作单点值。**

这几乎是你项目实验设计的理论底座。

### 它对你项目的具体意义
非常直接。

#### 你应该借的
1. **不要报单次结果**
   至少做：
   - 多个 perturbation 版本
   - 报 mean / variance
   - 或至少报 clean vs perturb 平均差

2. **把“重采样”写成方法论上的必要，而不是锦上添花**
   不然你的项目很容易被质疑：  
   你看到的掉点是不是 just lucky / unlucky sampling？

3. **把 prompt 看成分布**
   这能让你把实验语言写得更像 research：
   - 不是“某个 prompt 导致失败”
   - 而是“某类 meaning-preserving perturbation 导致成功率分布下移”

### 你现在能做到多严谨？
课程作业没必要真的把 ReliableEval 完整统计框架全复刻。  
但你至少应该吸收它的精神：
- 重复
- 方差
- resampling
- 不迷信单个 prompt

### 你在 report 里最好的写法
> ReliableEval 强调 prompt-sensitive evaluation 应被视为 stochastic estimation 问题，而非单一 prompt 下的点估计。受此启发，我们对每类设置采用少量重复 / 多个扰动版本，并报告均值与波动，而非仅展示单次结果。

---

## 3.10 Flaw or Artifact?

### 基本信息
- **论文名**：Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs
- **发表**：EMNLP 2025
- **入口**：https://aclanthology.org/2025.emnlp-main.1006/

### 它在解决什么问题？
这篇论文非常关键，因为它提出了一个“拆台式”的问题：

> **我们看到的大量 prompt sensitivity，到底是真的模型脆弱，还是 evaluation pipeline 自己太僵硬了？**

这是所有 prompt robustness 研究都必须面对的反思。

### 它的方法核心是什么？
这篇论文的关键操作是比较两类评测方式：

1. **heuristic evaluation**
   - 规则抽取
   - rigid answer matching
   - log-likelihood scoring

2. **LLM-as-a-Judge**
   - 更强调语义等价
   - 允许 paraphrase / 同义表达被判断为正确

作者发现，很多所谓的 prompt sensitivity，其实来自 heuristic evaluator 太死板：
- 模型答对了，但表达方式变了
- evaluator 没识别出来
- 于是把“表达变化”误判成“能力变化”

### 研究本质是什么？
它的研究本质是一句很重要的话：

> **在研究脆弱性之前，先确认你测到的不是评测器脆弱。**

这句对你项目极其重要。

### 它对你项目最关键的启发
1. **你选代码任务是对的**
   因为单元测试比开放生成里的 heuristic matching 更客观。  
   这正好能降低“评测伪影”。

2. **不要在核心结论上依赖模糊的主观判读**
   像：
   - “这个回答看起来更合理”
   - “这个修复似乎更贴近题意”

   这种东西很容易重演 heuristic / subjective artifact 问题。

3. **如果你要做 failure taxonomy，要小心它只是辅助分析**
   主结论应建立在：
   - pass rate
   - repair rounds
   - token cost
   - trajectory logs
   这种更客观的东西上。

### 和你的关系怎么写最漂亮？
你可以这样写：

> Flaw or Artifact? 指出许多已报告的 prompt sensitivity 可能被评测过程夸大。相比之下，我们采用基于单元测试的代码任务与确定性执行环境，尽量把“模型脆弱性”与“评测器脆弱性”区分开来。

这句话很加分。

---

# 4. 把这些论文放在一起看：它们到底在争论什么？

如果把上面十篇文章放在一起，其实它们在围绕三个大争论打转。

## 争论一：Prompt sensitivity 到底是不是“真问题”？
- **ProSA / POSIX / PromptRobust / ReliableEval** 会说：是，而且必须认真测。
- **Flaw or Artifact?** 会说：等等，先确认不是评测器把问题放大了。

### 你该怎么站位？
你不应该站在任何一边极端。  
最好的写法是：

> prompt sensitivity 是真实存在的，但其表面规模会受到评测方法影响，因此需要在更客观、可执行的 setting 中重新审视。

这正好把你项目的 **unit-test coding loop** 合法化了。

---

## 争论二：代码任务里的掉点，到底是 prompt phrasing 问题，还是信息量问题？
- **More Than a Score** 会说：有时不是 phrasing，而是 specificity / detail 不够。
- **Code Roulette** 会说：即使只是 typos / paraphrase，输出结构也会变。
- **CodeCrash** 会说：甚至 misleading NL 都会带来严重偏差。

### 你该怎么站位？
你的项目必须非常清楚地区分两类现象：

1. **meaning-preserving reformulation**
2. **information loss / misleading change**

否则实验会糊掉。

---

## 争论三：单轮结果变了，和 multi-step agent 真的是一回事吗？
- **单轮 prompt sensitivity 文献** 主要看 final output
- **RobustFlow / AgentNoiseBench** 已经开始看 workflow 和 noisy interactions
- 但 **coding repair loop 的阶段性偏航与恢复** 仍然是更窄、更具体的问题

### 这就是你项目最好的定位
你不是在重复“prompt 会影响输出”。  
你是在研究：

> **在一个真实会迭代修复的 coding loop 里，prompt 的小扰动会从哪一步开始伤害系统，伤害会不会传播，以及后续步骤能否把它救回来。**

这句话就是你的 literature gap。

---

# 5. 你自己的 report 里，related work 最该怎么改写？

下面给你一个更适合直接写进报告的版本。

## 5.1 你可以用的总述段

现有工作已经表明，LLM 对 prompt phrasing 与 prompt perturbation 的敏感性是一个可测量、可系统分析的问题。早期研究如 ProSA 和 POSIX 主要从通用 LLM 角度定义并量化 prompt sensitivity，PromptRobust 则进一步把多类型文本扰动组织成 benchmark。随后，研究开始进入代码场景：More Than a Score/PartialOrderEval 说明代码模型表现不仅取决于“能力”，也受到 prompt 具体程度影响；Code Roulette 与 CodeCrash 则表明轻微 prompt variability 与误导性自然语言都可能显著改变代码相关输出或代码推理。然而，上述工作大多仍聚焦单轮 code generation 或 code reasoning。近期面向 agent 的工作，如 RobustFlow 和 AgentNoiseBench，开始强调多步系统中的 workflow inconsistency、阶段性噪声与 trajectory-aware evaluation。与此同时，ReliableEval 与 Flaw or Artifact? 提醒我们：prompt-sensitive evaluation 本身也必须统计上可靠、并尽量避免评测伪影。基于这些观察，我们将问题聚焦为：在一个轻量 test-repair coding loop 中，意义近似保持的阶段性指令扰动如何影响成功率、轨迹偏航与恢复能力。

---

## 5.2 你可以用的 related work 表格（更像论文）

| 类别 | 代表工作 | 主要贡献 | 对我们的启发 | 和我们的差别 |
|---|---|---|---|---|
| 通用 prompt sensitivity | ProSA, POSIX | 定义并量化 prompt sensitivity | 让 fragility 成为正式研究对象 | 非 coding / 非 agent |
| robustness benchmark | PromptRobust | 系统构造多类型 prompt 扰动 | 给扰动设计和验证提供参考 | 更偏 adversarial，不是 repair loop |
| 代码生成敏感性 | More Than a Score, Code Roulette | 说明代码任务对 prompt specificity / variability 敏感 | 支持代码场景下做 controlled perturbation | 主要是单轮 codegen |
| 代码推理脆弱性 | CodeCrash | 说明 misleading NL 会误导 code reasoning | 支持 failure summary / revision 阶段高风险 | 不是完整 multi-step agent |
| agent/workflow robustness | RobustFlow, AgentNoiseBench | 强调 workflow consistency、阶段噪声、trajectory-aware 评测 | 直接支撑 stage-wise injection 与轨迹分析 | 不专注 coding repair |
| 评测可靠性 | ReliableEval, Flaw or Artifact? | 强调重采样、方差与评测伪影 | 约束我们必须使用严格测试和重复运行 | 不直接回答 coding loop 机制 |

---

# 6. 如果你只想记住每篇论文一句话，记这个版本

- **ProSA**：把“prompt 很敏感”变成一个正式可测的问题。  
- **POSIX**：不只看答对没答对，还看模型对同一答案的内部偏好有多不稳定。  
- **PromptRobust**：系统构造 prompt 扰动 benchmark，说明 robustness 要被正经评测。  
- **More Than a Score / PartialOrderEval**：代码模型有时不是不会，而是 prompt 讲得不够细。  
- **Code Roulette**：代码输出会随着 prompt 轻微变化而结构漂移，不只是分数变。  
- **RobustFlow**：agent 系统的鲁棒性要看中间 workflow 是否稳定，不只是终点对错。  
- **AgentNoiseBench**：真实 agent 会被 user/tool noise 搞崩，阶段性注入和轨迹分析很重要。  
- **CodeCrash**：代码相关推理也会被误导性自然语言带偏。  
- **ReliableEval**：prompt-sensitive evaluation 不能只看单次结果，要看分布和方差。  
- **Flaw or Artifact?**：有些 prompt sensitivity 是 evaluator 夸大的，不全是模型真脆。

---

# 7. 最后帮你收束成一句 literature positioning

你现在最适合放进摘要或 introduction 的一句定位是：

> Existing work has shown that LLM performance is sensitive to prompt variations, and recent studies have extended this concern from single-turn generation to workflow and agent robustness. However, relatively little work directly examines how approximately meaning-preserving perturbations, injected at different stages of a multi-step coding repair loop, affect trajectory deviation, error propagation, and recovery under objective unit-test-based evaluation.

中文版可以写成：

> 现有工作已经证明，LLM 的表现会受到 prompt 变体影响，且这一问题正从单轮输出扩展到 workflow 与 agent 鲁棒性研究。然而，针对多步 coding repair loop，仍较少有工作直接研究：当近似语义保持的扰动被注入到不同阶段时，它们会如何影响轨迹偏航、错误传播与恢复能力，尤其是在基于严格单元测试的客观评测下。

---

# 8. 可选补充：哪些条目更像“工程参考”，不算严格意义上的 related work？

你 report 的参考里还有这些：

- SWE-bench repo
- mini-swe-agent repo
- OpenHands issues

这些可以保留在 **Engineering Context / Feasibility / Risk** 一节，  
但通常不要放进核心 related work 叙事里。  
原因很简单：

- 它们提供的是 **工程可行性证据**
- 不是在提供主要 research claim

所以你可以这样处理：
- **Related Work**：放论文
- **Engineering Risks / Benchmark Choice**：放 repo 与 issue 证据

---

# 9. 写作提醒：你最容易写坏的三个地方

## 坑 1：把所有论文都写成“都说明 prompt 很重要”
这样会显得你没看出差异。

更好的写法是区分：
- 谁在 **定义和测量**
- 谁在 **构造 benchmark**
- 谁在 **研究代码任务**
- 谁在 **研究 agent / workflow**
- 谁在 **反思评测方法**

## 坑 2：把 More Than a Score 和你自己的扰动混在一起
那篇论文研究的是 **specificity / detail level**。  
你研究的是 **stage-wise meaning-preserving perturbation**。  
这两个很近，但不是一回事。

## 坑 3：忽视 Flaw or Artifact? 的警告
如果你做了太多主观分析、或者让 failure taxonomy 成为主结论，  
老师很容易问你：

> 你测到的是模型脆弱，还是你自己的分析口径脆弱？

所以你的主结果一定要尽量建立在：
- 单元测试
- 轮数
- token 开销
- 轨迹日志
这些更客观的东西上。

---

# 10. 一段最短版总结（适合 slides）

> 相关工作大致分为四类：  
> (1) ProSA、POSIX、PromptRobust 从通用 LLM 角度研究 prompt sensitivity 的定义、测量与 benchmark；  
> (2) More Than a Score、Code Roulette、CodeCrash 将问题带入代码场景，说明 prompt 的具体程度、变体和误导性语言都会影响代码输出或代码推理；  
> (3) RobustFlow 与 AgentNoiseBench 进一步表明，在 multi-step agent / workflow setting 中，语义等价指令与环境噪声会影响中间过程稳定性；  
> (4) ReliableEval 与 Flaw or Artifact? 则提醒我们，prompt-sensitive evaluation 需要重采样、方差分析和更可靠的评测方式。  
> 因此，我们将问题收缩到一个更可控的 setting：研究轻量 coding test-repair loop 中，不同阶段的近似语义保持扰动如何影响轨迹偏航与恢复。

---

## 附：建议你在最终 report 里保留的引用顺序

### 核心必留（最相关）
1. More Than a Score / PartialOrderEval  
2. Code Roulette  
3. RobustFlow  
4. AgentNoiseBench  
5. ReliableEval  
6. Flaw or Artifact?

### 第二层支撑（背景）
7. ProSA  
8. POSIX  
9. PromptRobust  
10. CodeCrash

如果篇幅紧，可以优先讲前 6 个；  
如果老师希望看到更完整背景，再补后 4 个。
