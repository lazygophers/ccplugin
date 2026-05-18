# cortex-config — schema

完整 schema, 与 `scripts/validate_config.py` 内嵌定义保持一致。修改任一文件必须双改对方。

## `~/.cortex/config.json`

JSON 对象, 根类型必须为 dict。

| key | type | required | default | range / 约束 | 互斥 | 用途 |
|---|---|---|---|---|---|---|
| `vault` | str | ✓ | — | abs path, exists 时校验通过 | — | cortex 所有 skill 入口 |
| `lang` | str | — | `zh-CN` | `^[a-zA-Z]{2,3}(-[A-Z]{2})?$` ISO 639/3166 | — | cortex-locale, digest, save 文案语言 |
| `settings` | str | — | — | abs path, exists | — | cron 注入 claude --settings |
| `install_path` | str | (install.sh 自动写) | — | abs path, exists | — | wrappers 找 plugin 根 |
| `timeout_default` | int | — | 600 | 60-7200 (秒) | — | cron wrapper 超时 |

未知 key → validate error。

## `<vault>/.cortex/config/digest.yaml`

```yaml
stages:
  consolidate: true
  enrich: true
  verify: true
incremental_max_age_days: 30
domain_aliases: {}
```

| key (dotted) | type | required | default | range | 读取方 |
|---|---|---|---|---|---|
| `stages.consolidate` | bool | — | true | true/false | cortex-digest 阶段 5 |
| `stages.enrich` | bool | — | true | true/false | cortex-digest 阶段 6 |
| `stages.verify` | bool | — | true | true/false | cortex-digest 阶段 7 |
| `incremental_max_age_days` | int | — | 30 | 1-365 | cortex-digest state 失效阈值 |
| `domain_aliases` | map<str,str> | — | `{}` | key 长度 1-64, value 非空 | cortex-digest 阶段 5 域名归一 |

文件不存在 → 所有字段取默认值, validate ok。

## `<vault>/.cortex/config/enrich.yaml`

```yaml
mermaid_whitelist:
  - flowchart
  - timeline
  - mindmap
  - sequenceDiagram
  - classDiagram
skip_paths:
  - .obsidian
  - _meta
  - _templates
  - _assets
  - 归档
  - .cortex
  - .trash
```

| key | type | required | default | range | 读取方 |
|---|---|---|---|---|---|
| `mermaid_whitelist` | list<str> | — | 见上 | 子集 of `{flowchart, sequenceDiagram, classDiagram, stateDiagram, erDiagram, journey, gantt, pie, mindmap, timeline, gitGraph, requirementDiagram, c4Context, quadrantChart, sankey, xychart}` | digest 阶段 6 |
| `skip_paths` | list<str> | — | 见上 | 相对 vault root, 非空 | digest 阶段 6 跳过路径 |

## `<vault>/.cortex/config/tags.yaml`

```yaml
alias_synonyms: {}
tag_naming: kebab-case
```

| key | type | required | default | range | 读取方 |
|---|---|---|---|---|---|
| `alias_synonyms` | map<str,list<str>> | — | `{}` | key 非空, value 列表非空, 元素 str | digest 阶段 6 alias 归一 / lint |
| `tag_naming` | enum<str> | — | `kebab-case` | `kebab-case` \| `snake_case` | lint tag 命名约定 |

## validate_config.py 输出 JSON

```json
{
  "ok": true,
  "errors": [
    {"file": "digest.yaml", "key": "incremental_max_age_days", "issue": "expected int 1-365, got 'abc'"}
  ],
  "warnings": [
    {"file": "tags.yaml", "key": "tag_naming", "issue": "unknown enum 'PascalCase', falling back to default"}
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `ok` | bool | true = 无 error (warning 允许) |
| `errors` | list<dict> | 拒写级别问题 |
| `warnings` | list<dict> | 提示级 (会话不阻塞) |

每条 issue: `{file, key, issue}`, file 可为 `~/.cortex/config.json` 或 vault yaml 文件名。

## migration

schema 升级流程 (未来):
- 新增字段: 加 default, 兼容老配置 (不报 error)
- 删字段: 在 validate 中标 warning, 一个版本后转 error
- 改默认值: 老配置显式设旧值即可保留
