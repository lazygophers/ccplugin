# Agents — 8 个专用多轮调度者

cortex 引入 8 个专用 agent, 在 21 个 skill 之上提供"接任务后自主跑多轮"能力。每个 agent 单 .md 文件, 走 Claude Code 标准 sub-agent 协议。

## 1. agent vs skill 区别

| 维度 | skill | agent |
|------|-------|-------|
| 触发 | description 池语义匹配 | 主线显式调度 (`Task` 工具) |
| 上下文 | 注入主对话, 全程驻留 | 隔离 sub-conversation, 不见主历史 |
| 跑多少轮 | 单次 | 多轮自主推进 |
| description 长度 | ≤ 1024 字符, 进 1536 池 | ≤ 200 字符, 不进池 |
| 适合 | 工具型操作 (搜/写/lint) | 工作流编排 (多 skill 串行) |

## 2. 8 个 agent

| agent | 角色 | 核心调度 |
|-------|------|----------|
| `cortex-curator` | 维护员 — 解读 lint 报告, 提修复方案 (proposal-only) | cortex-lint → 解读 → cortex-refactor 提议 |
| `cortex-researcher` | 研究员 — 多 source 抓取 + 入库 + 综述 | cortex-search → defuddle → cortex-ingest × N → cortex-summarizer |
| `cortex-translator` | 译者 — 跨 lang 翻译副本, 保 wikilink | cortex-search → 翻译 → cortex-save (新 lang 副本) |
| `cortex-historian` | 史官 — 多月份 sessions/ → fold/ 季度叙事 | cortex-session → cortex-summarizer → cortex-fold |
| `cortex-cartographer` | 制图员 — MOC + canvas + dashboard 三件套 | cortex-canvas → cortex-dashboard → MOC patch |
| `cortex-archivist` | 档案员 — fleeting/ 老化迁移提案 | cortex-search → cortex-refactor (move) |
| `cortex-linker` | 连接员 — SC 找近邻, 提议增链 | SC API → cortex-search → cortex-save (patch wikilinks) |
| `cortex-summarizer` | 总结员 — TL;DR callout 注入 | 读页 → 主模型 → patch 页头 |

全部 `name: cortex-<role>`, 与 skill 命名空间统一。

## 3. 调度方式

### 3.1 用户显式

```text
"用 cortex-curator 体检整个 vault"
"调度 cortex-researcher 调研 OAuth2.0, depth=deep"
```

主线把任务 + 必要上下文 (vault path, 范围, 配置) 写成 self-contained prompt, 调 `Task(cortex-<role>, ...)`。

### 3.2 间接 (agent 调 agent)

cortex-researcher 完成调研后**可以**主动调 cortex-summarizer 出综述; cortex-curator 可建议主线下次调 cortex-archivist。

但**并行 agent ≤ 2** (硬约束); agent 调 agent 串行即可, 不能再 spawn。

## 4. agent frontmatter

```yaml
---
name: cortex-<role>
description: <≤ 200 字, 一句话用途 + 何时调用>
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - mcp__obsidian__obsidian_simple_search
  ...
model: sonnet
---
```

注意:
- `tools` 用 **YAML list** (与 skill `allowed-tools` 空格分隔不同 — Claude Code 平台不一致)
- `model: sonnet` 通用; 复杂调度可 `opus`, 简单枚举型可 `haiku`

## 5. 边界 (所有 agent 共同)

- **不嵌套调度** (agent 不 spawn 另一 agent, 由主线编排)
- **proposal-only 类 agent (curator/archivist/linker) 不直接落盘** — 写盘走 cortex-refactor + 用户确认
- **写型 agent (translator/historian/cartographer/summarizer) 必须先 Read** 目标文件再 Edit (CC file-state 硬约束)
- **大输出 (> 10KB) 自动落 `_meta/cortex:runs/<ts>.md`**, 主线只回 path + 摘要

## 6. 测试 / 验证

每个 agent 描述都通过 GLM-4.5-flash 自检, 验证:
1. AI 能正确说出 agent 用途
2. AI 能给出至少一个合理的触发场景
3. 不与既有 skill 描述冲突 (cortex-search vs cortex-curator 等)

## 7. 关联

- 设计: `prd.md §6.3`
- 实现: `agents/cortex-*.md`
- 调用范式: research/05-skills-vs-commands.md (前 v1 archive)
