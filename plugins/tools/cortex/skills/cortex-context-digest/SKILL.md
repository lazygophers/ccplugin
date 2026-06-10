---
name: cortex-context-digest
description: "整理当前会话上下文 → 记忆库. 自动判定全局 (L0 关键词/跨项目语义) vs 项目级 (默认/含 repo 特定); 用户可 --scope global|project 显式覆盖. 复用 cortex-extract 三轴 + cortex-schema 路径. 任务收尾或显式 'digest 上下文/沉淀' 触发."
when_to_use: "整理上下文/沉淀本次会话/digest context/任务收尾沉淀/把决策落记忆库/全局还是项目级判定"
argument-hint: "[--scope global|project] [--dry-run|--apply]"
arguments: "[--scope 全局|项目] [--dry-run|--apply]"
user-invocable: true
disable-model-invocation: true
---

# cortex-context-digest

整理**当前会话上下文**(任务上下文 + 最近指令 + 关键决策) → 记忆库. 自动判定全局 (`~/.cortex/.wiki/memory/`) vs 项目级 (`<repo>/.wiki/memory/`); `--scope` 可强制覆盖. **不写脚本** — 由 main 会话按以下步骤调用 cortex-extract / cortex-save 落盘.

## 与既有 skill 边界

| skill | 数据源 | 落点 |
| --- | --- | --- |
| cortex-context-digest (本) | 当前会话上下文 (Read 活动任务 + 最近 N 轮对话) | 项目级默认 / 自动或 `--scope` 切全局 |
| cortex-extract | L4-inbox 文件 | 仓库内三模块 + memory |
| cortex-history-digest | `~/.claude/projects/**/*.jsonl` | 仅全局 |
| cortex-save | 一次性快速存单条 | 用户指定 |

## 执行步骤 (main 会话按序执行)

1. **Read 任务上下文**: 活动 `.trellis/tasks/<current>/` 下 prd.md / design.md / implement.md / journal-N.md
2. **Read 近期指令**: 会话最近 N 轮中用户校正 / 选型 / 决策
3. **识别学习增量**: 按 `references/triggers.md` 筛 (决策 / 选型 / 踩坑 / 规则 / L0 候选); 排除调试输出 / 客套
4. **scope 判定**: 对每条增量按 `references/scope.md` 6 优先序判 global / project
5. **dry-run plan**: 调 cortex-extract `--dry-run` 输出 JSON plan (复用其三轴判定 + cortex-schema 路径)
6. **用户审 → --apply**: 用户确认后调 cortex-extract `--apply` 或 cortex-save 落盘

## 路由表

| 任务 | 文件 |
| --- | --- |
| scope 6 优先序 + `--scope` 显式语义 + 保守 project 原因 | `references/scope.md` |
| 什么值得 digest / 不该 digest + 提取格式 | `references/triggers.md` |

依赖: cortex-schema (路径权威) + cortex-extract (三轴 + 落盘) + cortex-save (单条快存).
