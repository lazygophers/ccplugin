# 01 — 类脑/神经科学记忆 (cognitive memory)

> 调研目标: 2025-2026 是否有验证有效的「类脑/神经科学」agent 记忆落地? 区分学术理论 vs 可工程化。

## 核心结论

神经科学理论 (CLS / hippocampus-neocortex / synaptic consolidation / active inference) **目前无可直接工程化的 agent 记忆库实现**，全部停留在「概念映射」阶段。其价值是**提供架构隐喻** (快/慢双系统、离线巩固、遗忘机制)，而非可复制的代码。SKEIN 现有 core+recall 双层 **已经是 CLS 双系统隐喻的工程实现** (core≈neocortex 慢/常驻, recall≈hippocampus 快/ episodically 召回)，无需引入神经算法。

## 方案清单

### 1. Complementary Learning Systems (CLS) 理论
- 一句话: 智能系统需要两个互补学习系统 — 海马体 (快速、episodic、分离表示) + 新皮层 (慢速、结构化、整合知识)，避免 catastrophic interference。
- 机制: 快系统快速编码不重叠表示防灾难性遗忘；慢系统在离线期整合快系统痕迹。
- 依赖: 纯理论 (神经网络层面)，无 agent 库。
- 工程化落地: **无直接实现**，但 MemGPT/Letta 的 core↔archival 分层、SKEIN 的 core↔recall 分层都是 CLS 的工程隐喻。
- 来源: Kumaran et al. 2016 "What Learning Systems do Intelligent Agents Need?" (Trends in Cognitive Sciences, cited 1118+) https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613%2816%2930043-2 — 可信度: 一手同行评审 (顶刊)。
- 验证: 神经科学验证 (人脑 fMRI/病例)，**非 agent 基准验证**。

### 2. Sleep-time Compute (离线巩固) — Letta/UC Berkeley
- 一句话: agent 在空闲期 (sleep-time) 离线预处理已存储上下文，test-time 只回答查询，准确率提升 ~18%。
- 机制: 时间解耦上下文处理 vs 查询回答；类比人类睡眠记忆巩固。
- 依赖: 需要 LLM API (离线跑推理)。
- 工程化落地: **已有 arXiv 论文 + Letta 实现**，是少数「神经隐喻 + 真实 agent 落地」的方案。
- 来源: Lin et al. 2025 "Sleep-time Compute: Beyond Inference Scaling at Test-time" https://arxiv.org/html/2504.13171v1 — 可信度: 一手 arXiv (Letta 团队，非独立同行评审)。
- 验证: arXiv 论文 +18% accuracy 自报；社区博客二次解读。

### 3. Numenta HTM / 海马-新皮层联合建模
- 一句话: 基于 HTM 的海马+新皮层互补模块做 few-shot learning。
- 机制: 稀疏分布式表示 + 连续学习。
- 依赖: HTM 运行时 (非 LLM 生态)。
- 工程化落地: **无 LLM agent 集成**，停在 2021 Numenta 论坛讨论。
- 来源: Numenta Discourse 2021 https://discourse.numenta.org/t/modeling-of-hippocampus-together-with-neocortex-for-few-shot-learning-and-beyond-march-1-2021/8293 — 可信度: 二手论坛讨论。
- 验证: 仅理论讨论。

### 4. AI Meets Brain 综述 (2025/2026)
- 一句话: 系统映射神经科学记忆分类法 (短期 frontoparietal / 长期 hippocampal) 到自主 agent 架构。
- 来源: arXiv 2512.23343 "AI Meets Brain: A Unified Survey on Memory Systems from Cognitive Neuroscience to Autonomous Agents" https://arxiv.org/html/2512.23343v1 — 可信度: 一手综述 (未明确同行评审)。
- 验证: 综述，无新基准。

### 5. ZenBrain 7 层神经启发记忆
- 来源: Tech Disclosure Commons https://www.tdcommons.org/cgi/viewcontent.cgi?article=10975&context=dpubs_series — 可信度: 技术披露 (非同行评审，弱)。

## 可融入 SKEIN 的形态

- **不引入神经算法**。把 CLS 双系统隐喻当作 SKEIN core+recall 设计的**理论背书**写进文档即可 (core=慢/常驻/结构化硬规 ≈ neocortex；recall=快/按需/episodic 召回 ≈ hippocampus)。
- 唯一**可工程化借鉴**的是 sleep-time compute 思想 → 已部分对应 SKEIN `maintain` (离线体检/降级/归档) 与 `sediment` (task finish 后沉淀)。建议增强: 把 `maintain --apply` 当作「sleep cycle」定期跑，并在 sediment 时做一次轻量「巩固」(合并同 keywords 组 → 单条结构化规则)。见 00-summary.md。
- active inference / HTM / 持续学习: **该维信息不足** — 无 LLM agent 落地证据，不纳入。

## 矛盾点

- CLS 理论本身无争议，但「能否指导 LLM agent 设计」存在分歧: 一方 (AI Meets Brain 综述) 认为强相关；另一方 (Letta filesystem 博客隐含立场) 认为简单文件系统工具即超越神经启发复杂方案。本调研**不强行调和**: 理论层面采纳 CLS 隐喻，工程层面以 benchmark (Letta filesystem 74% LoCoMo) 为准。
