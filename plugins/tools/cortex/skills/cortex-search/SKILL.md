---
name: cortex-search
description: 在 vault 搜索并综合答复 — MCP first 四级 (mcp simple/complex → search.sh → rg), 附引用; 含记忆召回子流程。Triggers on "查知识库", "搜知识库", "search vault", "recall", "想想", "记得".
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_simple_search mcp__obsidian__obsidian_complex_search mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_batch_get_file_contents mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-search

向 Obsidian vault 提问, 综合答复并附引用 (file:line + `obsidian://` URI)。

## 触发场景

- 用户显式问 "what do you know about X" / "查一下知识库" / `/cortex:search`
- 主 agent 在动笔前自检"这个问题以前讨论过吗"
- 落档前查重 (cortex-save / cortex-ingest 命中 wikilink 时调用)
- 记忆召回 (`recall` / `想想` / `记得` / `/cortex:recall`) — 走 memory-recall.md 子流程

## 关键决策树

遇到任何问题 (代码改/排查/找文档/选型/答用户/决策) 前, **第一个工具调用必须按 L1 → L4 顺序尝试**, MCP first 不可跳过 (唯一豁免: 纯问候/纯对话/纯工具结果解释):

```
L1 mcp__obsidian__obsidian_simple_search  ← 默认首选
   ↓ 失败 (MCP 不可达 / 27123 不通)
L2 mcp__obsidian__obsidian_complex_search ← JsonLogic 复杂过滤
   ↓ 失败
L3 bash ~/.cortex/scripts/search.sh       ← CLI 回退
   ↓ 失败
L4 rg --type md ...                       ← 最后兜底
```

判定 deep mode (用户含 "深度搜索" / `--deep` / `depth=deep`) → 改走 `deep_search.sh --mode hybrid`。详见 references/multi-tier-search.md §Deep Mode。

判定 recall (含 `recall` / `想想` / `记得` / `/cortex:recall`) → 改走 memory-recall.md L0-L3 渐进披露子流程。

**禁忌**: 不用 qmd MCP 替代 obsidian MCP (qmd 索引不全 cortex vault, 与 hook / AGENT 契约一致); 不用 Bash rg / Grep 替代 MCP search (L4 仅最后兜底)。

## AUTO_MODE (wrapper / cron 传 `auto` 后缀触发)

- 跳 AskUserQuestion, 按推荐默认值自动决策
- persistent: error 自决降级 (L1→L2→L3→L4) / 重试, 禁询问, 禁中止
- 关键默认值: `top_k=10`, `scope=all`, 不加 `--full`, 仅返摘要

## References (按需加载)

| 文件 | 用途 |
|---|---|
| [`references/multi-tier-search.md`](references/multi-tier-search.md) | L1-L4 fallback 详细行为 + deep mode + tag filter + 解析 vault |
| [`references/output-format.md`](references/output-format.md) | 综合答复格式 + confidence 标记 + obsidian URI 渲染 + 稀疏命中提示 |
| [`references/memory-recall.md`](references/memory-recall.md) | L0-L3 记忆渐进披露召回 (原 cortex-recall skill 合入) |
