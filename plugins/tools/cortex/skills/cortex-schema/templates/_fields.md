> 公共字段定义 — 各 type 模板共用; 各变体差异在 `templates/<type>/<variant>.md`.

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

## 引用

- 路径布局: `../references/topology.md`
- 三模块路径规则: `../references/knowledge-modules.md`
- memory 5 级语义: `../references/memory-levels.md`
- 完整 .md 样例: `../examples/`
