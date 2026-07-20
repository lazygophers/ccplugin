# 05 — 2025-2026 实证有效 + 学术验证

> 调研目标: 有论文/基准支持的方案，区分 demo/营销 vs 同行评审/基准验证。

## 核心结论

最强**独立验证**信号 = Letta「Filesystem 74% LoCoMo 超 Mem0 graph 68.5%」(一手实验，Letta 团队，方法论透明) + 神经科学 CLS 理论 (顶刊 1118 引用，非 agent 基准)。最需警惕 = Mem0 自报 94.4% vs 独立测 49% 的巨大 gap。SKEIN 选型应优先采纳**有独立复现/同行评审**的结论，对自报数字打折扣。

## 关键基准 & 论文一览 (可信度降序)

| 方案 | 验证类型 | 关键数字 | 来源 | 可信度 |
|---|---|---|---|---|
| Letta Filesystem (文件+grep) | 一手实验 (Letta 团队自跑) | LoCoMo 74% > Mem0g 68.5% | https://www.letta.com/blog/benchmarking-ai-agent-memory/ | 高 (一手，方法论公开，GPT-4o mini 可复现) |
| CLS 理论 (Kumaran 2016) | 同行评审顶刊 | cited 1118+ | https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613%2816%2930043-2 | 高 (神经科学，非 agent 基准) |
| Sleep-time Compute (arXiv) | arXiv preprint (Letta/UCB) | +18% accuracy | https://arxiv.org/html/2504.13171v1 | 中 (一手 preprint，未独立复现) |
| A-MEM (NeurIPS 2025) | 同行评审 (poster) | cited 890+ | https://arxiv.org/abs/2502.12110 ; https://neurips.cc/virtual/2025/poster/119020 | 高 (NeurIPS 接收) |
| Zep (arXiv) | arXiv preprint | DMR 超 MemGPT (自报) | https://arxiv.org/html/2501.13956v1 | 中 (preprint，未独立) |
| LongMemEval (基准本身) | 同行评审 | cited 428+ | https://github.com/xiaowu0162/longmemeval ; OpenReview pZiyCaVuti | 高 (基准，被多方采用) |
| Mem0 自报 | 自报 docs | LongMemEval 94.4 / LoCoMo 92.5 | https://docs.mem0.ai/core-concepts/memory-evaluation | 低 (自报，无独立复现) |
| Mem0 独立测 (Vectorize) | 第三方独立 | LongMemEval 49% | https://vectorize.io/benchmarks ; https://vectorize.io/articles/mem0-vs-letta | 中 (独立 vendor，但 Vectorize 是竞品有利益冲突) |
| Hindsight (Vectorize) | 自报 (vendor) | LongMemEval 94.6% SOTA | https://vectorize.io/benchmarks | 低 (vendor 自报) |
| Memory-R1 (arXiv) | arXiv preprint | cited 113 | https://arxiv.org/pdf/2508.19828 | 中 (preprint) |
| Memory in Age of AI Agents (综述) | arXiv 综述 | cited 75 | https://arxiv.org/abs/2512.13564 | 中 (综述) |

## 关键解读

### A-MEM (NeurIPS 2025, 890 引用) — 唯一高引且同行评审的 agent 记忆论文
- 机制: Zettelkasten 启发，记忆条目自生成 contextual description + 自建链接，形成动态演化语义图。
- 依赖: LLM (建链/演化靠 LLM)。
- 来源: arXiv 2502.12110 + NeurIPS 2025 poster + GitHub https://github.com/agiresearch/a-mem
- 融入 SKEIN: **理念高度相关** — SKEIN `related: [slug]` + `[[slug]]` wikilink + maintain 断链检测，是 A-MEM 的纯 stdlib 简化版。可借鉴: sediment 时让 agent 给新规则生成 `links` (相关已有规则 slug) + maintain 检测并提示「孤立节点」(零入度规则)。

### Mem0 49% vs 94% 的启示
- 自报与独立测 gap = 45 个百分点，是 2025 agent 记忆领域「营销 vs 现实」的典型。
- 选型启示: SKEIN 文档/README 引用基准时**必须标注「自报/独立测」**，不引用单一 vendor 数字。

### 「向量不必要」的独立证据链
- Letta filesystem 实验 (一手) + r/LangChain 「为何放弃向量-only 检索」 (一线开发者) + memweave (Markdown+SQLite+BM25 零向量) + Mem0 blog「BM25/keyword 对精确匹配足够」 — 四方汇聚，支撑 SKEIN「不引入向量层」决策。

## 可融入 SKEIN 的形态

- 采纳 **A-MEM 的链接/孤立检测** (纯 stdlib): 见 00-summary 推荐方案 1。
- 采纳 **sleep-time compute 的离线巩固** 概念 (映射到 maintain --apply 周期跑 + sediment 时合并)。
- 文档化所有基准引用标「自报/独立/同行评审」三档可信度。

## 矛盾点 (保留不和稀泥)

1. Mem0 自报 94% vs Vectorize 独立 49% — 真实表现未知，两方均标出。
2. Zep「图记忆超 MemGPT」(DMR 基准) vs Letta「文件系统超图记忆」(LoCoMo 基准) — 不同基准不同结论，**基准本身不可直接横比** (LoCoMo 测长会话检索，DMR 测深度记忆检索)。
3. Hindsight 自报 LongMemEval 94.6% SOTA — vendor 自报，Vectorize 既是测评方又是被测方，利益冲突，不打折不可信。
