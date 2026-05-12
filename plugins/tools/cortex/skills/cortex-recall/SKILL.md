---
name: cortex-recall
description: 记忆渐进披露召回 — 按 query 跨 L0-L3 检索, 仅返 brief + 子节点 (非全量)。触发: "记得" / "recall" / "想想" / 用户提问需历史上下文时自动触发。
disable-model-invocation: false
allowed-tools: Read Glob mcp__obsidian__obsidian_simple_search mcp__obsidian__obsidian_get_file_contents
---

# cortex-recall

按查询渐进披露召回相关记忆。默认只返父节点 brief + 子目录索引, 避免上下文爆炸。

## 触发场景
- 用户提问命中 `recall_when` 关键词 (自动)
- 显式 "想想之前的..." / "recall X" / "记得 X"
- 其他 skill (cortex-search, cortex-reflect) 内部召回

## 输入
- query: 自然语言或关键词
- top_k: 默认 5
- levels: 默认 `[L0, L1, L2, L3]` (L4 默认排除, 显式 `--include-l4` 才进)
- --full: 返回 full 字段 (默认仅 brief)

## 流程

1. **解析 vault** + 读 `_meta/memory-policy.yaml` 拿 recall.default
2. **多源检索**:
   - `mcp__obsidian__obsidian_simple_search` query → 命中条目路径
   - Glob frontmatter `recall_when` 字段模糊匹配 query
   - 按 URI level 过滤 (排除 levels 之外的)
3. **打分排序**:
   - level 优先级: L0 > L1 > L2 > L3
   - 同 level 按 weight × recall_freq (recall_count/age_days) 排序
   - 取 top_k
4. **渐进披露输出** (每条):
   - frontmatter: uri / level / weight / ref / recall_when
   - brief (一行)
   - 子节点列表 (children URIs, 不展开内容)
   - 父节点 URI
   - **不返 full** 除非 --full
5. **更新 frontmatter** (每条被召回):
   - `recall_count += 1`
   - `last_recalled = now (UTC ISO)`
   - 通过 cortex-memory update 写回

## 输出
```
[recall: "Go 并发"] top 3 hits

1. L2://semantic/go/goroutine  (weight 0.7, recalled 12x)
   brief: Go 并发用 goroutine + channel, GMP 调度模型
   ref: 知识库/领域/技术/编程语言/Go/goroutine.md
   parents: [L1://procedural/go-concurrency]
   children: [L3://episodic/2026-05-12/T1430]

2. L1://procedural/go-concurrency  (weight 0.9, recalled 32x)
   brief: Go 并发模式 — goroutine + channel + select + context.Cancel
   children: [L2://semantic/go/goroutine, L2://semantic/go/channel]

3. ...

(use --full to expand body, --include-l4 to include ledger/sessions)
```

## 错误处理
- 0 命中 → 输出 "no recall hits, 候选 levels=..., 试 cortex-search 走知识库"
- frontmatter 解析失败的条目 → 跳过, 末尾汇总 warning
- recall_count 更新失败 (写盘失败) → 不阻塞召回结果输出

## 召回级别策略

默认召回 L0+L1+L2+L3 (排 L4)。按 weight 排序。
- L0: 永远第一返 (核心)
- L1: 高 weight (≥0.8) 排第二
- L2: 按 expires 过滤未过期
- L3: 按 recall_count 排序, 90 天内
- L4: 显式 `--include-l4` 才返

## AUTO_MODE 兼容
[AUTO_MODE: ...] 下行为不变 (recall 本就纯读 + 自动 update count)。仅在显式 `--full` 时返回完整内容, AUTO_MODE 不自动加 --full。

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/recall.sh`):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 任何需用户决策处 → 走默认值跳过 (recall 本就纯读)
3. fail-fast: 任何 error 立即返回错误码 + 简短消息
4. AUTO_MODE 不自动加 `--full`, 默认返回摘要
