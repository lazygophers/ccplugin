---
name: cortex-config
description: cortex 配置查看/编辑 — 无参展示当前 .cortex/config/*.yaml + ~/.cortex/config.json (含字段语义); 有 verb (get/set/unset) 写前 schema 校验; 会话结束自动校验配置合法性。Triggers on "查看 cortex 配置", "改 cortex 配置", "cortex config", "config edit", "configure cortex".
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents
hooks:
  Stop:
    - command: "python3 ${CLAUDE_SKILL_DIR}/scripts/validate_config.py"
      timeout: 10
      blocking: false
---

# cortex-config

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

cortex 配置统一查看 / 编辑入口。覆盖两个真相源:

- `~/.cortex/config.json` — 用户级 (vault / lang / settings / install_path / timeout_default)
- `<vault>/.cortex/config/*.yaml` — vault 级 (digest / enrich / tags)

写盘前**强制 schema 校验**, 不通过即拒。Stop hook 在会话结束时自动 validate, 防止自动化脚本调到不合法配置。

## 触发场景

- 用户显式 "查看 cortex 配置" / "改 cortex 配置" / "cortex config" / "configure cortex"
- 调用方调 `/cortex:config`
- 排查 digest / enrich / verify 异常 (先看 config 是否合法)
- 会话 Stop 事件 (skill-level hook 自动 validate, 仅告警, 不阻塞)

## 关键决策树

```
入参形态:
  ∅ (无参)         → display: 读全部 config + schema 标注 + validate 报告
  get <key>         → 打印对应键 (支持点号路径, e.g. digest.stages.consolidate)
  set <key> <value> → schema 校验 → atomic write → 回显新值
  unset <key>       → schema 校验 (是否可空) → 删除键 → atomic write
  validate          → 仅校验, 输出 {ok, errors, warnings} JSON

写盘前必跑 _validate_field(key, value)。失败 → 拒写 + stderr 列违规项 + exit 1。
display 模式标注 "default" vs "user-set"。
```

## 字段语义 (含默认值)

### `~/.cortex/config.json`

| key | type | default | range | 用途 / 哪些 skill 读 |
|---|---|---|---|---|
| `vault` | str (abs path) | — | exists | cortex 所有 skill (vault 根) |
| `lang` | str (ISO code) | `zh-CN` | `^[a-zA-Z]{2,3}(-[A-Z]{2})?$` | cortex-locale / digest / save |
| `settings` | str (abs path) | — | exists or empty | digest cron 注入 |
| `install_path` | str (abs path) | (install.sh 自动写) | exists | wrappers 找 plugin 根 |
| `timeout_default` | int | 600 | 60-7200 | cron wrappers |

### `<vault>/.cortex/config/digest.yaml`

| key | type | default | range / 约束 | 读取方 |
|---|---|---|---|---|
| `stages.consolidate` | bool | true | — | cortex-digest 阶段 5 |
| `stages.enrich` | bool | true | — | cortex-digest 阶段 6 |
| `stages.verify` | bool | true | — | cortex-digest 阶段 7 |
| `incremental_max_age_days` | int | 30 | 1-365 | cortex-digest state 失效阈值 |
| `domain_aliases` | map<str,str> | `{}` | key/value 非空 | 阶段 5 域名归一 |

### `<vault>/.cortex/config/enrich.yaml`

| key | type | default | range | 读取方 |
|---|---|---|---|---|
| `mermaid_whitelist` | list<str> | `[flowchart, timeline, mindmap, sequenceDiagram, classDiagram]` | 子集 of mermaid 已知 type | digest 阶段 6 |
| `skip_paths` | list<str> | `[.obsidian, _meta, _templates, _assets, 归档, .cortex, .trash]` | 相对 vault root | digest 阶段 6 |

### `<vault>/.cortex/config/tags.yaml`

| key | type | default | range | 读取方 |
|---|---|---|---|---|
| `alias_synonyms` | map<str,list<str>> | `{}` | value 列表非空 | digest 阶段 6 / lint |
| `tag_naming` | enum<str> | `kebab-case` | `kebab-case` \| `snake_case` | lint |

完整 schema 见 [references/schema.md](references/schema.md)。

## schema 校验规则

| 规则 | 失败行为 |
|---|---|
| key 必须在 schema 已知集 | 拒写, exit 2 |
| 类型不匹配 (str/int/bool/list/map) | 拒写, exit 1 |
| 取值越界 (int range / enum) | 拒写, exit 1 |
| path 字段不存在 | 拒写, exit 1 |
| 必填字段写空字符串 | 拒写, exit 1 |
| 互斥规则 (无, 当前无互斥字段) | — |

YAML 文件**不存在视为合法** (用 schema 默认值)。

## 用法示例

```bash
# 无参 — 列全部 + validate
/cortex:config

# get
/cortex:config get vault
/cortex:config get digest.stages.consolidate
/cortex:config get digest.incremental_max_age_days

# set (写前校验)
/cortex:config set lang en-US
/cortex:config set digest.incremental_max_age_days 45
/cortex:config set digest.domain_aliases.ai 技术

# unset
/cortex:config unset digest.domain_aliases.ai

# 仅校验
/cortex:config validate
```

详细示例 + 错误处理见 [references/usage.md](references/usage.md)。

## 输出格式

**无参 (display)**:

```
~/.cortex/config.json:
  vault         /Users/foo/vault              [user]
  lang          zh-CN                         [default]
  install_path  /Users/foo/.../cortex         [user]
  timeout_default  600                        [default]

<vault>/.cortex/config/digest.yaml:
  stages.consolidate           true   [default]
  stages.enrich                true   [default]
  stages.verify                false  [user]
  incremental_max_age_days     30     [default]
  domain_aliases               (0 entries) [default]

<vault>/.cortex/config/enrich.yaml: (file absent, all defaults)
<vault>/.cortex/config/tags.yaml:   (file absent, all defaults)

validate: ok
```

**validate JSON** (`/cortex:config validate`):

```json
{
  "ok": false,
  "errors": [{"file": "digest.yaml", "key": "incremental_max_age_days", "issue": "expected int, got str"}],
  "warnings": [{"file": "tags.yaml", "key": "tag_naming", "issue": "unknown enum 'PascalCase'"}]
}
```

## 实现路径

写改逻辑直接调 `scripts/cortex_config.py` (已存在, 处理 `~/.cortex/config.json`)。
vault yaml CRUD 在 SKILL.md body 中由 AI 调 Bash + python yaml 库 (PyYAML) 完成, 或调 `scripts/validate_config.py --apply` 子命令 (当前 read-only)。

**MVP**: AI 直接读写 yaml (Read/Edit/Write 工具), 写前调 `scripts/validate_config.py --dry-run --key=<k> --value=<v>` 校验单字段; 通过即 Edit 写盘。

## Stop hook 行为

skill frontmatter `hooks.Stop` 注册 `validate_config.py` (timeout 10s, non-blocking)。会话结束时:

1. 读 `~/.cortex/config.json` 拿 vault, 没拿到则跳过 (空 vault 不报错)
2. 读 vault `.cortex/config/*.yaml`
3. 按内嵌 schema 校验
4. 有 error → stderr `[cortex-config WARN] ...`, exit 1 (blocking=false, 不阻塞会话)
5. 全 ok → 静默 exit 0

**降级方案**: 若 Claude Code 当前不支持 skill-level Stop hook, AI 在会话收尾应主动 `bash python3 .../scripts/validate_config.py` 一次。plugin.json 已有 plugin-level Stop hook (stop.sh), 不在 plugin.json 二次注册, 避免双跑。

## AUTO_MODE

**严禁**:

| # | 禁止 |
|---|---|
| 1 | "建议"/"修复建议" 章节 |
| 2 | 用户确认问句 (`是否?`, `要继续吗?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "建议人工"/"下一步" 推卸辞令 |
| 5 | 写盘前未跑 schema 校验 |
| 6 | 校验失败仍写盘 |

校验失败 → 直接 stderr 报错 + 列违规项 + exit 1, 不解释 "为何", 不给"修复建议"。

## References 指针

| 文件 | 内容 |
|---|---|
| [references/schema.md](references/schema.md) | 完整 YAML + JSON schema + 类型 / 默认 / range / 互斥 |
| [references/usage.md](references/usage.md) | 用法详例 + 错误处理 + 输出样本 |
