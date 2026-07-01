# PRD — trellisx-spec audit 整理去重 (child)

## Goal

trellisx-spec optimize 模式的 `references/diagnose.md` 加 4 项整理检测: guide 间冗余 / 过时引用 / 低质量强化 / index 同步。让 optimize 不只是"重写", 还能"整理去重"。

## What I know

- `diagnose.md` 现有检测: 命令式比例 / 描述式残留 / 死链 / 外部重复 (vs CLAUDE.md/AGENTS.md) / 与代码脱节 / 描述性垃圾 / manifest 引用率
- 现有"外部重复" = spec vs **外部文档** (CLAUDE.md 等), **非 guide-vs-guide**
- 现有"死链" = `[..](..)` `[[..]]` 目标存在性, 含 guide 引用 — 但未单列"guide 引用已删文件/符号"维度
- 无 index 同步检测 (`.trellis/spec/guides/index.md` 列的 guide vs 实际文件)
- index.md 是 orchestrate step1 grep 门的入口, 不同步 → 加载失效

## 4 检测项 (新增)

| # | 检测 | 计算 | 标 |
|---|---|---|---|
| A1 | guide 间冗余 | guide 两两段落相似度 ≥ 70% (同语义契约出现在 ≥2 guide) | MERGE 提案 |
| A2 | 过时引用 | guide 引用的文件路径/符号 grep 当前仓库不存在 | DELETE/REWRITE |
| A3 | 低质量强化 | 命令式比例 <60% **且** 描述式 >5 处 **且** 无可执行验证 (现 diagnose 有命令式/描述式, 加"无验证手段"交叉判定, 标低质量重写优先级) | REWRITE 高优 |
| A4 | index 同步 | index.md 列的 guide vs `find .trellis/spec/guides/ -name '*.md'` 双向 diff | PATCH (补 index 或删孤儿 guide) |

## 范围

- **改**: `plugins/tools/trellisx/skills/trellisx-spec/references/diagnose.md` (加 4 检测项到体检表 + 报告模板 + 诊断脚本)
- **不改**: SKILL.md 主流程 (diagnose 仍是 optimize 阶段 1 前置), 其他 reference, orchestrate/flow
- 纯文档改动, 无代码逻辑

## Deliverable

| ID | 交付 | 验收 |
|---|---|---|
| D1 | diagnose.md 体检表加 4 行 (A1-A4) | grep 4 检测项名命中 |
| D2 | 体检报告模板加 4 指标输出 | 模板含冗余/过时/index 同步字段 |
| D3 | 诊断脚本段加 4 命令示例 | 脚本段可复制跑 |
| D4 | 质检: claude -p 读 diagnose.md 问"audit 能检哪些" 返回含 4 项 | 返回非空含 A1-A4 |

## 验收

- diagnose.md 4 检测项全覆盖
- 现有检测项零回归 (命令式/描述式/死链/外部重复/脱节/垃圾/引用率)
- claude -p 可读出新增项
