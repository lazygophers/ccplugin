# 04 — 分层/多 store 混合记忆 (layered / multi-store)

> 调研目标: 现代框架的多层记忆架构 — MemGPT core vs archival, Letta memory blocks, Claude Code subagent 隔离上下文。

## 核心结论

分层记忆是 2025 共识范式，SKEIN 的 core+recall **正是这一范式**。最具参考价值的两个一手来源: (1) MemGPT 的 core/archival 分层 (SKEIN 直接对应)；(2) Claude Code subagent 隔离上下文 + summary-only return (SKEIN 已通过 SubagentStart hook 实现)。本维增量最小 — SKEIN 已是分层最佳实践。唯一新概念是 **Letta memory blocks (命名块、可共享/可读可写权限)** 和 **shared memory bank (跨 subagent 共享)**，可作未来演进参考。

## 方案清单

### 1. MemGPT / Letta core memory vs archival
- 一句话: OS 式分层 — core memory (常驻 context 内，LLM 可编辑) vs archival (外部，按需检索) vs external files。
- 机制: LLM 主动调工具 swap in/out；core memory 分 persona/human 命名块。
- 来源: Letta blog 同 02; MemGPT 论文 (UC Berkeley) — 可信度: 一手。
- 验证: MemGPT 是该范式开创者，被广泛引用。
- 融入 SKEIN: **已对应** — core=core memory, recall=archival, finish sediment=LLM 编辑 core。SKEIN AGENT_CATEGORIES 白名单 (line 51-57) 即「按 agent 类型选注入哪些 core 块」，比 MemGPT 静态 persona/human 块更细。

### 2. Letta Memory Blocks (命名块 + 共享/权限)
- 一句话: core memory 拆成命名块 (label)，可跨 agent 共享，带 read/write 权限。
- 机制: block = 带 label 的文本块；多 agent 订阅同一 block。
- 来源: Letta 文档 (经 Medium/社区转述) https://medium.com/@sathishkraju/claude-code-subagents-the-complete-guide... — 可信度: 二手。
- 验证: Letta 平台功能，无独立基准。
- 融入 SKEIN: 未来演进参考 — SKEIN core 现按 category 目录分块 (git/test/arch...)，等价于 block；权限模型暂不需要 (单仓库单用户)。

### 3. Claude Code Subagent 隔离上下文 + summary-only return
- 一句话: subagent 是独立 Claude 实例，自有 context window，只回 summary，中间工作不进主上下文。
- 机制: 父 agent spawn subagent → 隔离 context 干活 → 只回结果。
- 来源: Towards AI "Inside Claude Code Part 3" https://pub.towardsai.net/inside-claude-code-part-3-1cbfd408db18 ; Vectorize "subagents don't share what they learn" https://hindsight.vectorize.io/blog/2026/05/06/claude-code-subagents-shared-memory/ — 可信度: 一手+二手。
- 验证: Claude Code 实际机制。
- 融入 SKEIN: **已实现** — SKEIN SubagentStart hook (spec.py line 174-196) 给 subagent 注入 core 规则；subagent 回传摘要带 `SPEC:` 标记供 finish 沉淀。隔离上下文原生由 Claude Code 提供。

### 4. Shared Memory Bank (跨 subagent 共享)
- 一句话: 解决「subagent 互相不知道对方学了什么」，加共享记忆层。
- 来源: Vectorize 同上 — 可信度: 二手 (Vectorize 营销其产品)。
- 验证: vendor 方案，弱。
- 融入 SKEIN: SKEIN 的 `.skein/spec/` 本身就是跨 session/跨 subagent 的共享记忆库 (subagent 沉淀 → 后续 session/session-start 注入)；已天然实现共享，无需额外 bank。

### 5. LangMem 三层 (semantic/procedural/episodic)
- 见 02。属于分层中的「内容类型分层」而非「存储层级分层」。
- 融入 SKEIN: frontmatter 加 `memory_type` 字段 (见 02)。

## 可融入 SKEIN 的形态

本维 SKEIN 已是最佳实践，**不新增存储层**。可选轻量增强:

1. core 层细分命名块: SKEIN 已按 category 目录分，等价 MemGPT block；无需改动。
2. 跨 subagent 共享: 已由 `.skein/spec` 共享 + `SPEC:` 回传机制覆盖。
3. memory_type 字段: semantic/procedural/episodic 三分 (零运行时成本)，见 02。

用户已知需求「新增 external 外部记忆层 (不注入 hooks)」 — 这正是本维「archival / external files」层。SKEIN 现有 core (常驻注入) + recall (grep 召回)，新增 **external 层 (不注入 hooks，按需手动检索，可放外部资料/大文档/链接)** 是 MemGPT external files 概念的自然延伸，与现有两层正交。见 00-summary 推荐方案 3。

## 矛盾点

- 「多 agent 共享记忆」派 (Vectorize shared bank) vs 「隔离优先」派 (Claude Code 原生 subagent) — SKEIN 用「共享 spec 库 + 隔离 subagent 上下文」两者兼顾，无冲突。
