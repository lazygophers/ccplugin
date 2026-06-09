# frontmatter 模板

各 type 的 frontmatter 通用字段与块模板. 所有 vault 笔记的 frontmatter 以此为准.

> **边界**: 本文件 = frontmatter **块片段** (拼装用). 完整可落盘的 .md 样例 (含正文 + wikilink) 见 `../examples/<type>.md`.

## 通用字段表

| 字段 | 必备 | 类型 | 说明 |
| --- | --- | --- | --- |
| `type` | 是 | str | `rule` (memory/L0) / `memory` (L1-L4) / `project` / `domain` / `vault-script` |
| `level` | type=rule/memory 时必备 | str | `L0` `L1` `L2` `L3` `L4` |
| `created` | 是 | ISO date | 创建日期 |
| `updated` | 否 | ISO date | 最近编辑 |
| `tags` | 否 | list | wikilink-friendly 标签 |
| `aliases` | 否 | list | 别名 |
| `weight` | 否 (L1-L3 建议) | float 0-1 | 用户标注强度 |
| `source` | type=project 必备 | URL | 项目来源链接 |
| `area` | type=domain 必备 | str | domains 一级 area |
| `mindmap` | type=project 推荐 | path | canvas 文件相对路径 |

## type: project

入库 GitHub / GitLab / Website 摘要 (`项目/<host>/<owner>/<repo>/README.md`):

```yaml
---
type: project
source: https://github.com/anthropics/claude-code
summary: Claude Code CLI — Anthropic 官方终端编码代理
mindmap: ./mindmap.canvas        # 可选, 相对当前 README.md
graph: ./graph.json              # 可选
created: 2026-06-09
updated: 2026-06-09
tags: [ai, cli, agent]
aliases: [claude-code]
---
```

完整样例: `../examples/project.md`.

## type: domain

领域笔记 (`领域/<area>/<sub>/[<sub2>/]<topic>.md`):

```yaml
---
type: domain
area: tech
created: 2026-06-09
updated: 2026-06-09
tags: [rust, async, tokio]
aliases: [tokio-runtime-notes]
weight: 0.6
---
```

完整样例: `../examples/domain.md`.

## type: rule (memory/L0-core)

核心规则, 永久, 不进入遗忘曲线:

```yaml
---
type: rule
level: L0
weight: 1.0
created: 2026-06-09
tags: [safety, hardrule]
aliases: []
---
```

完整样例: `../examples/rule.md`.

## type: memory (memory/L1-L4)

L1 长期记忆 (已稳固):

```yaml
---
type: memory
level: L1
created: 2026-06-09
updated: 2026-06-09
weight: 0.85
tags: [process, project-x]
---
```

L2 中期记忆:

```yaml
---
type: memory
level: L2
created: 2026-06-09
updated: 2026-06-09
weight: 0.6
tags: [decision]
---
```

L3 短期记忆 (extract 默认入口):

```yaml
---
type: memory
level: L3
created: 2026-06-09
weight: 0.4
tags: [observation]
---
```

L4 收件箱 (原始未分类):

```yaml
---
type: memory
level: L4
created: 2026-06-09
tags: [inbox]
---
```

完整样例: `../examples/memory-L1.md` / `memory-L2.md` / `memory-L3.md`.

## type: vault-script

vault 内部脚本 (写为脚本顶部注释块, 推荐不强制):

```bash
# ---
# type: vault-script
# name: canvas-from-mindmap
# created: 2026-06-09
# ---
```

完整样例: `../examples/vault-script.md` (.md 形式描述).

## 引用

- 路径布局: `topology.md`
- 三模块路径规则: `knowledge-modules.md`
- memory 5 级语义: `memory-levels.md`
- 完整 .md 样例: `../examples/`
