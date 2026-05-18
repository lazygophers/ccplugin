# cortex-config — usage

详例 + 错误处理。所有命令支持 `~/.cortex/config.json` 平铺 key (vault / lang / ...) 与 vault yaml 点号路径 (digest.stages.consolidate)。

## 路径推断

| key 形态 | 目标文件 |
|---|---|
| `vault` / `lang` / `settings` / `install_path` / `timeout_default` | `~/.cortex/config.json` |
| `digest.<key>` 或 `digest.<key>.<sub>` | `<vault>/.cortex/config/digest.yaml` |
| `enrich.<key>` | `<vault>/.cortex/config/enrich.yaml` |
| `tags.<key>` | `<vault>/.cortex/config/tags.yaml` |

vault 路径从 `~/.cortex/config.json:.vault` 解析。未设 → vault-level CRUD 拒绝。

## display (no arg)

```
$ /cortex:config

~/.cortex/config.json:
  vault            /Users/foo/vault       [user]
  lang             zh-CN                  [default]
  settings         (unset)
  install_path     /opt/cortex            [user]
  timeout_default  600                    [default]

<vault>/.cortex/config/digest.yaml:
  stages.consolidate         true   [default]
  stages.enrich              true   [default]
  stages.verify              false  [user]
  incremental_max_age_days   45     [user]
  domain_aliases (1):
    ai → 技术

<vault>/.cortex/config/enrich.yaml: (file absent, defaults applied)
<vault>/.cortex/config/tags.yaml:
  alias_synonyms (0)
  tag_naming  kebab-case  [default]

validate: ok
```

标注:
- `[user]` — 用户显式设置过 (与默认不同 或 文件中显式写出)
- `[default]` — 字段缺省, schema 默认值
- `(unset)` — 可选字段未设

## get

```
$ /cortex:config get vault
/Users/foo/vault

$ /cortex:config get digest.stages.consolidate
true

$ /cortex:config get digest.incremental_max_age_days
30                # 文件不存在或字段缺 → 返回 default

$ /cortex:config get tags.alias_synonyms
{}

$ /cortex:config get bogus.key
get: unknown key 'bogus.key'   # stderr, exit 2
```

## set (写前 schema 校验)

```
$ /cortex:config set lang en-US
ok: ~/.cortex/config.json lang = en-US

$ /cortex:config set digest.incremental_max_age_days 45
ok: <vault>/.cortex/config/digest.yaml incremental_max_age_days = 45

$ /cortex:config set digest.incremental_max_age_days abc
set: digest.yaml/incremental_max_age_days: expected int 1-365, got 'abc'
exit 1, 拒写

$ /cortex:config set digest.incremental_max_age_days 9999
set: digest.yaml/incremental_max_age_days: out of range 1-365
exit 1, 拒写

$ /cortex:config set digest.domain_aliases.ai 技术
ok: <vault>/.cortex/config/digest.yaml domain_aliases.ai = 技术

$ /cortex:config set tags.tag_naming PascalCase
set: tags.yaml/tag_naming: expected enum {kebab-case, snake_case}, got 'PascalCase'
exit 1, 拒写

$ /cortex:config set vault /nonexistent
set: ~/.cortex/config.json/vault: /nonexistent does not exist
exit 1
```

bool 接受形态: `true / false / yes / no / 1 / 0` (大小写不敏感)。

## unset

```
$ /cortex:config unset digest.domain_aliases.ai
ok: removed digest.yaml/domain_aliases.ai

$ /cortex:config unset vault
unset: ~/.cortex/config.json/vault: required field, cannot unset
exit 1

$ /cortex:config unset digest.stages.consolidate
ok: removed digest.yaml/stages.consolidate   # fallback to default true
```

unset 必填字段 (vault) → 拒。可选字段 unset → 删除键, 字段回退默认值。

## validate

```
$ /cortex:config validate
{
  "ok": true,
  "errors": [],
  "warnings": []
}
exit 0

$ /cortex:config validate
{
  "ok": false,
  "errors": [
    {"file": "~/.cortex/config.json", "key": "vault", "issue": "/old/path does not exist"},
    {"file": "digest.yaml", "key": "incremental_max_age_days", "issue": "expected int 1-365, got 9999"}
  ],
  "warnings": [
    {"file": "tags.yaml", "key": "tag_naming", "issue": "unknown enum 'PascalCase'"}
  ]
}
exit 1
```

## Stop hook 触发示例

```
[会话结束]
$ python3 ${CLAUDE_SKILL_DIR}/scripts/validate_config.py
[cortex-config WARN] digest.yaml/incremental_max_age_days: expected int 1-365, got 'abc'
exit 1 (blocking=false, 会话仍正常退出)
```

只在 stderr 提示, 不打断对话。

## 错误处理矩阵

| 场景 | 行为 |
|---|---|
| `~/.cortex/config.json` 不存在 | display 提示 "config absent, run install.sh"; get → stderr exit 1; set → 自动创建 |
| `~/.cortex/config.json` 损坏 JSON | 所有命令 exit 1 + 列错误行号 |
| vault yaml 不存在 | 视为合法, 所有字段 default; set → 自动创建 yaml |
| vault yaml 损坏 | exit 1, 列错误行 (yaml.YAMLError msg) |
| 未设 `vault` 但操作 vault yaml | 拒, exit 1 提示 "set vault first" |
| 写盘冲突 (并发) | atomic write (tmp + os.replace), 后写覆盖前写 |
