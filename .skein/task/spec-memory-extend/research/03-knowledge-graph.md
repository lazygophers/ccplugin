# 03 — 图谱/知识图谱记忆 (knowledge graph memory)

> 调研目标: entity-relation graph, temporal KG, GraphRAG (微软), Neo4j-based agent memory。

## 核心结论

知识图谱记忆 (Graphiti/Zep/GraphRAG) 在**时序推理 (事实随时间变化)** 上有真实优势，但全部依赖 Neo4j 或 LLM 抽取，**与 SKEIN 纯 stdlib 硬约束强冲突**。其核心增量价值 = 「实体-关系链接 + 时态双端 (valid_from/valid_to)」，可被 SKEIN 用更轻的机制近似: 现有 frontmatter `related: [slug,...]` wikilink + `status: superseded` 已覆盖一部分；缺的是「时态双端」和「实体级链接」，可用纯 stdlib Markdown wikilink + 时态 frontmatter 字段近似 (GraphRAG-lite)。

## 方案清单

### 1. Graphiti (Zep AI, on Neo4j)
- 一句话: 实时、时序感知的知识图记忆层，存 Neo4j；agent 可查「事实如何随时间变化」。
- 机制: LLM 从对话抽 entity + relation → 写图节点 (带 valid_from/valid_to 双时态)；旧事实过期不删，加边。
- 依赖: Neo4j + LLM API。
- 工程化: 高 (开源、Zep 商业化)。
- 来源: Neo4j blog https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/ — 可信度: 一手 (Neo4j 官方博客)。
- 验证: 工业部署；Zep arXiv paper 显示在 Deep Memory Retrieval 基准上超 MemGPT。
- 融入 SKEIN: 依赖冲突不直接融入；**借鉴时态双端**: frontmatter 加 `valid_from` / `valid_to` (或复用 created/updated + status=superseded)，maintain 时按时态判过期。

### 2. Zep (temporal KG architecture)
- 一句话: 时序知识图 agent 记忆服务，DMR 基准超 MemGPT。
- 机制: episode 切分 → entity/relation 抽取 → 时态图。
- 依赖: 图引擎 + LLM。
- 来源: arXiv 2501.13956 "Zep: A Temporal Knowledge Graph Architecture for Agent Memory" https://arxiv.org/html/2501.13956v1 — 可信度: 一手 arXiv (同行评审状态未明确)。
- 验证: arXiv 论文自报 DMR 超越 MemGPT；被 Neo4j/社区引用。
- 融入 SKEIN: 同 Graphiti，仅借鉴时态概念。

### 3. Microsoft GraphRAG
- 一句话: 社区检测 + 实体关系图的 RAG 增强，结构化全局问答。
- 机制: LLM 抽实体→聚类社区→生成摘要；查询走 community 报告 + 局部检索。
- 依赖: LLM API (建图昂贵，token 成本高)。
- 来源: GraphRAG 官方 https://graphrag.com/reference/knowledge-graph/memory-graph-temporal/ — 可信度: 一手 (微软)。
- 验证: 微软工业方案，建图成本高是已知痛点 (社区批评)。
- 融入 SKEIN: 不融入 (成本+依赖)。

### 4. FalkorDB (开源图 DB GraphRAG)
- 来源: https://www.falkordb.com/blog/graph-database-ai-agents/ — 可信度: 一手 vendor。
- 验证: vendor，弱。

## 可融入 SKEIN 的形态 (GraphRAG-lite, 纯 stdlib)

SKEIN 已有 `related: [slug,...]` wikilink (frontmatter) + `[[slug]]` body 内链 + maintain 断链检测。**纯 stdlib 可做的图增强**:

1. **时态双端字段**: frontmatter 加 `valid_from` (复用 created) / `valid_to` (status=superseded 时填)；maintain 新增判据「事实被 supersede 时保留旧记录 + 加 valid_to」，模拟 Graphiti 的非删除时态图。
2. **实体反向索引**: maintain 时扫所有 `[[slug]]` 建反向链接表 (谁引用我)，写入 `<layer>/backlinks.md` — 纯 grep 可生成，无需图 DB。当前 maintain 只检测断链，未建反链。
3. **不加 entity 抽取** (需 LLM，违反「recall 不调 LLM」边界；若要做，放 finish sediment 阶段由 agent 抽，非 spec.py 运行时)。

## 矛盾点

- KG 派 (Zep/Graphiti/Neo4j) 主张「结构化图记忆是 2025 主流解」；Letta filesystem 派主张「LLM 用文件工具即可超越图」。两方各有基准 (Zep 用 DMR；Letta 用 LoCoMo)。本调研: SKEIN 因纯 stdlib 约束，不引入图 DB，但采纳「时态双端 + 反向链接」这两个可纯 stdlib 实现的图概念。
