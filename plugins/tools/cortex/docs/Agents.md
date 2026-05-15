# Agents — 6 个专用多轮调度者

cortex 引入 **6 个**专用 agent (PR4 删 linker: 7→6), 在 13 个 skill 之上提供"接任务后自主跑多轮"能力。每个 agent 单 .md 文件, 走 Claude Code 标准 sub-agent 协议。

每个 agent 头部含 "**vs <skill> 分工**" 注释行, 明确与同名 skill 的边界 (proposal-only vs 落盘 / 批量 vs 单项目 / pipeline vs 单页等)。

## 1. agent vs skill 区别

| 维度 | skill | agent |
|------|-------|-------|
| 触发 | description 池语义匹配 | 主线显式调度 (`Task` 工具) |
| 上下文 | 注入主对话, 全程驻留 | 隔离 sub-conversation, 不见主历史 |
| 跑多少轮 | 单次 | 多轮自主推进 |
| description 长度 | ≤ 1024 字符, 进 1536 池 | ≤ 200 字符, 不进池 |
| 适合 | 工具型操作 (搜/写/lint) | 工作流编排 (多 skill 串行) |

## 2. 6 个 agent

**范围标记**: 知识库 (vault) · 记忆层 · 全局 外网 (WebFetch)

| agent | 范围 | vs Skill 分工 | 核心调度 |
|-------|-----|---------------|----------|
| `cortex-curator` | 知识库 | vs cortex-lint + doctor: 巡检提案 (不写盘) vs 执行规则落盘 vs 即时体检 | cortex-lint → 解读 → cortex-refactor 提议 |
| `cortex-researcher` | 知识库+外网 | vs cortex-ingest: 多 source 综述 (并发) vs 单 source 落档 | search → defuddle → ingest × N → summarizer |
| `cortex-translator` | 知识库 | (无对应 skill) 跨 lang 翻译副本, 保 wikilink | search → 翻译 → save (新 lang 副本) |
| `cortex-cartographer` | 知识库 | vs cortex-dashboard: 批量项目场景 vs 单项目刷 | canvas → dashboard → patch |
| `cortex-archivist` | 知识库 | vs cortex-refactor: 归档提案 (不写盘) vs 执行落盘 | search → refactor (move) 提议 |
| `cortex-summarizer` | 知识库 | vs cortex-digest: 受调度产单页摘要 vs 5 阶段 daily pipeline | 读页 → 主模型 → patch 页头 callout |

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
- **写型 agent (translator/cartographer/summarizer) 必须先 Read** 目标文件再 Edit (CC file-state 硬约束)
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
