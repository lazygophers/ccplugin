---
name: cortex-schema
description: "项目知识库统一契约 — 目录结构 / 三模块 (项目/领域/脚本, 项目+脚本仅用户级) / 5 级记忆 (L0-core/L1-long/L2-mid/L3-short/L4-inbox, Ebbinghaus 遗忘曲线) / 双层布局 (用户级全模块 + 项目级仅 memory+领域) / frontmatter 模板 / 完整样例. lint+extract 引用本 skill 作权威源."
when_to_use: "入库/归档/写笔记/记忆等级判定/promote/demote/forget/路径决策/frontmatter 模板/查样例"
argument-hint: "[topology|knowledge|memory|templates|examples]"
arguments: "[拓扑|知识|记忆|模板|样例]"
user-invocable: false
---

# cortex-schema

cortex 项目知识库**统一契约**, 单一真相源. 覆盖目录结构 / 三模块路径 / 5 级记忆 / frontmatter / 完整样例. lint + extract + agent 全部引用本 skill, 不再复制硬列任何路径或映射.

## 三模块速查 (中文目录, vault 内部)

| 模块 | 路径 (相对 `<root>/`) | type | 层级 |
| --- | --- | --- | --- |
| 项目 | `项目/<host>/<owner>/<repo>/` | `project` | 仅用户级 |
| 领域 | `领域/<area>/<sub>/[<sub2>/]<topic>.md` (≥ 2 级) | `domain` | 双层 |
| 脚本 | `脚本/<name>.{sh,py}` (vault 内部, 非用户入口) | `vault-script` | 仅用户级 |

`<root>` = `~/.cortex/.wiki` (全模块) 或 `<repo>/.wiki` (仅 memory + 领域). 项目/脚本 模块只在用户级. 用户操作入口 CLI 在 `~/.cortex/scripts/` (英文), 与 vault 内 `脚本/` (中文) 视觉分离, 禁混用.

## 5 级记忆速查 (反直觉: 数字越小 = 越抗遗忘)

```
L4 收件箱
   │ extract
   ▼
L3 短期 ── promote ──▶ L2 中期 ── promote ──▶ L1 长期 ── promote ──▶ L0 核心
  7d                  90d                    365d                   永久 (手动)
   ▲                   ▲                      ▲
   └── demote 7d ──────┴── demote 90d ────────┴── demote 365d
```

L1=长期 / L3=短期, 数字与时长**反向**. 路径后缀 (`core/long/mid/short/inbox`) 强制内嵌语义防反写.

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 ~/.cortex 顶层物理布局 / 双层差异 / 必备目录 / 开放扩展 / 详细 ASCII | `references/topology.md` |
| 查三模块 (项目/领域/脚本) 路径规则 + 命名 + frontmatter | `references/knowledge-modules.md` |
| 查 5 级记忆 (L0-L4) 语义 / 映射 / 反写防呆 / 遗忘曲线 / 三轴 / 路由 | `references/memory-levels.md` |
| 查 frontmatter 通用字段表 | `templates/_fields.md` |
| 查各 type / 变体 frontmatter 块模板 | `templates/{memory,project}/<variant>.md` 或 `templates/{domain,vault-script}.md` |
| 查完整 .md 样例 (含正文 + wikilink) | `examples/<type>.md` |

## 引用

- lint 规则集 (R1-R7, 含路径/同构/level/入口脚本): `cortex-lint`
- extract 路由 (L4 → L0/L1/L2/L3 判定): `cortex-extract`
