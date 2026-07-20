# 02 — 向量/语义记忆 (vector / semantic memory)

> 调研目标: embedding-based retrieval, RAG, episodic vs semantic; 主流框架 mem0 / letta / langgraph memory / zep / cognee。

## 核心结论

向量语义记忆是 2025 主流方案，但**与 SKEIN 硬约束 (纯 stdlib、无向量 DB、无 LLM API 依赖、本地) 冲突**。关键反共识证据: Letta 实验显示「文件系统 + grep/search_files + LLM 驱动检索」在 LoCoMo 达 74%，**超过** Mem0 graph 变体的 68.5% — 即 SKEIN 现有「recall grep 粗筛 + model 读全文」范式**已被验证不弱于向量方案**。因此建议: SKEIN 不引入向量层，而是强化 LLM 驱动的检索 (允许 agent 改写 query 多轮 grep) + 轻量 BM25 打分 (纯 stdlib 可做)。

## 方案清单

### 1. Mem0 (mem0.ai)
- 一句话: 两阶段管线 (extract → consolidate) + Mem0g 图增强变体的生产级记忆层。
- 机制: LLM 抽取事实 → 写向量库/图；查询时 retrieve+rerank；Mem0g 加关系图做时序推理。
- 依赖: 向量 DB + LLM API (抽取/合并靠 LLM)。
- 工程化: 高 (PyPI 包、55k+ GitHub stars、自托管)。
- 来源: 官方 docs https://docs.mem0.ai/core-concepts/memory-evaluation ; Mem0 paper 2025 https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-... — 可信度: 一手 docs + arXiv paper。
- 验证: **自报** LongMemEval 94.4% / LoCoMo 92.5% (docs.mem0.ai)；**独立 Vectorize 测** 49% (LongMemEval) — 巨大冲突，营销 vs 独立测差距悬殊。
- 融入 SKEIN: 不融入 (依赖冲突)。但其「LLM 抽事实再存」思路 = SKEIN finish 阶段 `sediment` 由 agent 写结构化规则，已具备。

### 2. Letta (前 MemGPT)
- 一句话: OS 式分层记忆 (core memory 常驻 / archival 按需 / external files)，LLM 自管理记忆。
- 机制: core memory 块 + archival 检索工具；agent 主动调工具 swap。
- 依赖: LLM API + 向量索引 (archival)。
- 工程化: 高 (UC Berkeley 出品、Letta 平台、Terminal-Bench #1 OSS)。
- 来源: Letta blog "Benchmarking AI Agent Memory" https://www.letta.com/blog/benchmarking-ai-agent-memory/ — 可信度: 一手 (Letta 团队)。
- 验证: **关键证据** — Letta Filesystem (文件 + grep + search_files) 在 LoCoMo 达 74%，超 Mem0 graph 68.5%；核心论点「简单文件系统工具即足够，复杂记忆工具反因不在训练分布而用不好」。
- 融入 SKEIN: **理念强相关**。SKEIN 的 core (≈core memory) + recall (≈archival) + grep 已经是 Letta filesystem 范式。建议: 不要加向量，强化「agent 改写 query 多轮 recall」。

### 3. LangMem (LangGraph memory layer)
- 一句话: 三类记忆 — semantic (事实) / procedural (how-to) / episodic (过往交互蒸馏 few-shot)。
- 机制: 持久 store + LLM 优化器更新 system prompt。
- 依赖: LangGraph 运行时 + LLM API。
- 来源: Atlan 2026 https://atlan.com/know/best-ai-agent-memory-frameworks-2026/ — 可信度: 二手综述。
- 验证: 工业采用，无独立基准。
- 融入 SKEIN: 三分类法可借鉴 (SKEIN 已有 status/keywords 字段；可加 `memory_type: semantic|procedural|episodic` frontmatter 做过滤)，无需运行时依赖。

### 4. Cognee
- 一句话: 语义/知识图记忆，与 LangGraph 集成做持久化语义记忆。
- 依赖: LLM + 图引擎。
- 来源: cognee blog https://www.cognee.ai/blog/integrations/langgraph-cognee-integration... ; Graphlit 综述 https://www.graphlit.com/blog/survey-of-ai-agent-memory-frameworks — 可信度: 一手+二手。
- 验证: 无独立基准。
- 融入 SKEIN: 不融入 (依赖冲突)。

### 5. Memvid (文本→MP4 QR 帧)
- 一句话: 把文本块编码成 MP4 视频帧 (QR)，用视频 codec 压缩，检索时解码帧，无需 DB。
- 依赖: ffmpeg + embedding 模型 (建索引时)。**非纯 stdlib**。
- 来源: GitHub https://github.com/memvid/memvid ; arXiv 2503.09149 (同名但指视频理解，不同工作) — 可信度: 一手 repo。
- 验证: viral 项目，无独立基准。
- 融入 SKEIN: 不融入 (依赖 + 小众)。

### 6. Memweave (Markdown + SQLite + BM25，零向量)
- 一句话: 零基建 agent 记忆，Markdown 落盘 + SQLite FTS5(BM25) 检索，精确匹配 (错误码/配置值/专有名) 上优于向量。
- 依赖: SQLite (Python stdlib `sqlite3` 含)。
- 来源: levelup.gitconnected 介绍文 https://levelup.gitconnected.com/memweave-zero-infra-ai-agent-memory-with-markdown-and-sqlite-no-vector-database-required-cf3869efc840 — 可信度: 二手博客。
- 验证: 无独立基准；但「向量不足，BM25 补」是 2025 社区共识 (r/LangChain 讨论证实)。
- 融入 SKEIN: **高度可行** — SQLite 是 Python stdlib，BM25 via FTS5 可纯 stdlib 实现；SKEIN recall 现在是纯 grep 子串匹配，升级为 FTS5 BM25 是低风险增强。见 00-summary 推荐方案 2。

## 可融入 SKEIN 的形态

- **不加向量层** (依赖冲突 + Letta 证据显示不必要)。
- recall 层从子串 grep → **SQLite FTS5 BM25** (纯 stdlib `sqlite3`)，提升精确匹配召回；保留 grep 作 fallback。
- frontmatter 加 `memory_type` 字段区分 semantic/procedural/episodic (零运行时成本)。

## 矛盾点

- Mem0 自报 94.4% vs Vectorize 独立测 49% — **真实生产表现存疑**，不能据自报数字选型。
- Letta「文件系统够用」vs Mem0「需要专门记忆层」— 工程哲学对立。本调研据 Letta 一手实验 + SKEIN 纯 stdlib 硬约束，倾向 Letta 立场，但保留「若 SKEIN 未来放开依赖可重新评估」。
