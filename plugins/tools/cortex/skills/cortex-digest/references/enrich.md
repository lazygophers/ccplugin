# Enrich — 阶段 6 md 图表 + tags/aliases 优化

> cortex-digest 8 阶段 §6 详细规范。新阶段 (PR digest-deep)。

LLM 判每个 md 适合的图表类型, 注 mermaid 块; 重抽 tags/aliases (中英对) 补 frontmatter。

## 输入

- state: `vault/.cortex/state/enrich.json`
- 扫描范围: vault 内全部 md, **排除** 以下路径:
  - `_meta/**` · `_templates/**` · `_assets/**` · `.cortex/**`
  - `归档/**` · `.obsidian/**` · `.trash/**`
  - `仪表盘/**` (人工维护 HTML, 不动)
  - frontmatter `enrich: false` 标记的单文件
- config: `vault/.cortex/config/enrich.yaml`

## 算法

```
for each md not in skip_paths:
  if hash in processed_files: skip
  LLM 读 md, 输出:
    {
      mermaid_type: flowchart|timeline|mindmap|table|none,
      mermaid_block: "<mermaid 源>",
      aliases: [...],
      keywords: [...],
      reason: "..."
    }
  if mermaid_type != none AND mermaid_type in config.mermaid_whitelist:
    inject mermaid block (frontmatter 后, 正文前)
  merge aliases / keywords 到 frontmatter (去重, 既有优先)
  写 hash 到 state/enrich.json
```

## mermaid 类型判定 (LLM)

| 适合 | 内容特征 |
|---|---|
| `flowchart` | 含步骤序列 / 决策分支 / "→" / "if/then" |
| `timeline` | 含日期序列 / 历史事件 / "<YYYY>" 多次出现 |
| `mindmap` | 概念列表 + 子项嵌套, 无明显时序 |
| `table` | 已有对比项 / 多维度参数, mermaid 不一定胜过原 md table — 谨慎用 |
| `none` | 纯叙述 / 短笔记 / 已含图表 — 跳 |

config 白名单 `enrich.yaml:mermaid_whitelist` (默认 `[flowchart, timeline, mindmap]`, 不含 table) 控制可注入。

## 注入位置 + 格式

```markdown
---
<frontmatter>
---

## 关系图

```mermaid
<生成的 mermaid 源>
```

<原正文 (不动)>
```

**硬约束**:
- 不动原正文一行
- 已存在 `## 关系图` / 已含 mermaid fence → 跳过 (不重复注入)
- mermaid 源 ≤ 30 行, 节点 ≤ 20 (超出降级为 mindmap 或 none)

## tags / aliases 重抽

LLM 抽:
- aliases: ≥3, 中英对 (例 `["事件驱动", "event-driven", "EDA"]`)
- keywords: ≥5, 同概念不同表达

合并规则:
- 既有 `frontmatter.aliases` / `tags` **保留** (人工维护)
- 新候选 append (去重, case-insensitive)
- `config/tags.yaml:alias_synonyms` 同义词归一 (例 `event-driven` → `事件驱动`)
- 上限: aliases ≤ 10, tags ≤ 15 (超出按 LLM 信心截)

## LLM Prompt 模板

```
你是知识可视化助手。读以下 md, 决定:
1. 是否适合加 mermaid 图表 (flowchart/timeline/mindmap), 给源
2. 抽 ≥3 中英对 aliases + ≥5 keywords

输入:
<frontmatter + body>

输出 JSON:
{
  "mermaid_type": "flowchart|timeline|mindmap|none",
  "mermaid_block": "...",
  "aliases": ["..."],
  "keywords": ["..."],
  "reason": "<一句话理由>"
}

规则: 短 md (<200 字) / 已含图表 → mermaid_type=none
```

## 跳过条件

| 条件 | 行为 |
|---|---|
| 路径在 skip_paths | 不读不写 |
| frontmatter `enrich: false` | 不读不写 |
| frontmatter `type: dashboard` / `type: meta` | 跳 mermaid 注入, 仍重抽 tags |
| md < 200 字 | 跳 mermaid, 仍重抽 tags |
| 已含 `## 关系图` 或 mermaid fence | 跳 mermaid 注入 |

## 输出统计

```json
{
  "scanned": <N>,
  "mermaid_injected": <N>,
  "tags_updated": <N>,
  "aliases_updated": <N>,
  "skipped_path": <N>,
  "skipped_already_has_chart": <N>
}
```

## 失败 / 回滚

- mermaid 注入后用 `mermaid-cli` 或简单语法 lint 验证 — 失败则不注入 (不写盘), stderr 报 warn
- tags/aliases merge 失败 (frontmatter 解析坏) → 跳该文件, 不写 hash
- 单文件失败不中止阶段
