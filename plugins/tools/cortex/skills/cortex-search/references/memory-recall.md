---
name: memory-recall
description: cortex-search 子流程 — 渐进披露召回 L0-L3 记忆 (原 cortex-recall skill 合并入)
---

# Memory Recall (合入 cortex-search)

按查询渐进披露召回相关记忆。默认只返父节点 brief + 子目录索引, 避免上下文爆炸。

> 历史: 本流程原为独立 `cortex-recall` skill (88 行单文件), PR1 合并入 `cortex-search/references/`。触发面、slash 命令 `/cortex:recall` + wrapper `recall.sh` 不变, 仅 skill 加载路径改 — wrapper 现调 `cortex-search` 走本 references。

## 触发场景

- 用户提问命中 `recall_when` 关键词 (自动)
- 显式 "想想之前的..." / "recall X" / "记得 X"
- `/cortex:recall` slash + `recall.sh` wrapper
- 其他 skill (cortex-digest) 内部召回

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
   - 按 URI level 过滤
3. **打分排序**:
   - level 优先级: L0 > L1 > L2 > L3
   - 同 level 按 weight × (recall_count/age_days) 排序
   - 取 top_k
4. **渐进披露输出** (每条):
   - frontmatter: uri / level / weight / ref / recall_when
   - brief (一行)
   - 子节点列表 (children URIs, 不展开)
   - 父节点 URI
   - **不返 full** 除非 --full
5. **更新 frontmatter** (每条被召回):
   - `recall_count += 1`
   - `last_recalled = now (UTC ISO)`
   - 通过 cortex-memory update 写回

## 输出格式

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

(use --full to expand body, --include-l4 to include ledger/sessions)
```

## 错误处理

- 0 命中 → 输出 "no recall hits, 候选 levels=..., 试 cortex-search 走知识库"
- frontmatter 解析失败 → 跳过, 末尾汇总 warning
- recall_count 更新失败 → 不阻塞召回结果输出

## 召回级别策略

默认 L0+L1+L2+L3 (排 L4)。按 weight 排序:

- L0: 永远第一返 (核心)
- L1: 高 weight (≥0.8) 排第二
- L2: 按 expires 过滤未过期
- L3: 按 recall_count 排序, 90 天内
- L4: 显式 `--include-l4` 才返

## AUTO_MODE 行为

wrapper 调用 (`/cortex:search auto` 或 `/cortex:recall auto`) 走 AUTO_MODE:

1. 不调 AskUserQuestion (allowed-tools 已禁)
2. 任何决策走默认值
3. 不自动加 --full, 默认返回摘要
4. error 自决降级 / 重试, 禁中止
