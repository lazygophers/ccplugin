# PRD — 禁 env vars, 全用 ~/.cortex/config.json

## 需求

插件任何地方只用 `~/.cortex/config.json` 配置, 禁用环境变量。**install.sh 除外**。

## 现状

63 文件含 env vars 引用。分类:

### 配置类 env (需迁 config)
- `OBSIDIAN_VAULT` / `CORTEX_VAULT` / `CORTEX_VAULT_PATH` — vault 路径
- `CORTEX_LANG` — 语言
- `CORTEX_SETTINGS` — claude settings 路径
- `CORTEX_INSTALL_PATH` / `CLAUDE_PLUGIN_ROOT` / `CORTEX_PLUGIN_ROOT` — plugin 根路径
- `CORTEX_TIMEOUT` — 默认 timeout
- `CORTEX_DRY_RUN` — dry-run flag
- `CORTEX_SYNC_TEMPLATES` — 模板同步 flag

### 运行时通信 env (可保留, 不是用户配置)
- `CORTEX_JOB_LABEL` — wrapper 标识 (内部传)
- `CORTEX_STREAM_TEE_FILE` — NDJSON 文件路径 (内部)
- `NO_COLOR` — terminal 标准, 非 cortex 配置

## 目标

1. 所有"配置类" env 改为读 `~/.cortex/config.json`
2. install.sh 不动 (装机阶段, 用 env 自然)
3. 运行时通信 env (job_label/tee_file/timeout) 改为**CLI 参数**或**内部函数参数**, 不走 env
4. config.json schema 扩展:
   ```json
   {
     "vault": "<path>",
     "lang": "zh-CN",
     "settings": "<path>",
     "install_path": "<plugin root>",
     "timeout_default": 300,
     "auto_commit": true,
     "auto_push": false
   }
   ```
5. cortex_config.py 提供统一读 API (已有, 扩 keys)

## 设计

### 1. 配置读取统一 API

`hooks/_lib/cortex_config.py` (现有) 加 helper:
```python
def get_config_value(key: str, default=None):
    """从 ~/.cortex/config.json 读 key, 缺失返 default."""
    config_path = Path.home() / ".cortex" / "config.json"
    if not config_path.is_file():
        return default
    try:
        return json.loads(config_path.read_text()).get(key, default)
    except Exception:
        return default

def get_vault() -> Path | None:
    v = get_config_value("vault")
    return Path(v) if v else None

def get_plugin_root() -> Path | None:
    p = get_config_value("install_path")
    return Path(p) if p else None

def get_lang() -> str:
    return get_config_value("lang", "zh-CN")

def get_settings_path() -> Path:
    s = get_config_value("settings")
    return Path(s) if s else Path.home() / ".claude" / "settings.json"

def get_timeout(default: int = 300) -> int:
    return int(get_config_value("timeout_default", default))
```

### 2. bash 侧 helper

`scripts/lib/config.sh` (或 `cortex_config.sh`) 加:
```bash
cx_config_get() {
  # cx_config_get <key> [default]
  local key="$1"
  local default="${2:-}"
  local config="$HOME/.cortex/config.json"
  [[ -f "$config" ]] || { echo "$default"; return; }
  command -v jq >/dev/null || { echo "$default"; return; }
  local v
  v=$(jq -r ".$key // empty" "$config" 2>/dev/null)
  [[ -n "$v" ]] && echo "$v" || echo "$default"
}

cx_get_vault()      { cx_config_get vault; }
cx_get_plugin_root(){ cx_config_get install_path; }
cx_get_lang()       { cx_config_get lang "zh-CN"; }
cx_get_settings()   { cx_config_get settings "$HOME/.claude/settings.json"; }
cx_get_timeout()    { cx_config_get timeout_default 300; }
```

PRELUDE 加上述函数 (供 wrapper 用)。

### 3. 改造点

#### hooks/_lib/resolve_vault.sh
现在读 env (`CORTEX_VAULT` / `OBSIDIAN_VAULT`) → 改读 config.json `.vault`。保留命令行/stdin 参数兼容。

#### hooks/session_start.sh / user_prompt_submit.sh / stop.sh / post_compact.sh
内部 python 段读 env `PLUGIN_ROOT` / `VAULT` → 改读 config.json。

特殊: hook 是 Claude Code 调用, Claude 通过 env 传 `CLAUDE_PLUGIN_ROOT` — 这是 Claude Code 给 hook 的 env, **不是 cortex 配置**, **保留** (这是平台契约)。

实际:
- `CLAUDE_PLUGIN_ROOT` 是 Claude Code 给 hook 的 (平台契约) — **保留**
- `OBSIDIAN_VAULT` / `CORTEX_*` (cortex 自定义) — **改读 config**

#### scripts/cron/*.sh
`CORTEX_VAULT` / `CORTEX_LANG` / `CORTEX_SETTINGS` / `CORTEX_TIMEOUT` / `CORTEX_DRY_RUN` / `CORTEX_SYNC_TEMPLATES` → 改用 config 或 CLI flag。

run.sh 内部传到 prompt 的 `vault: $VAULT` 等 → 改为 `cx_get_vault` 返回。

#### scripts/install_wrappers.sh
生成 wrapper 内 `export CORTEX_VAULT=...` 删, 改用 `vault=$(cx_get_vault)`。

#### mcp/*
MCP server 启动时, 读 env `OBSIDIAN_VAULT` → 改 config。但 MCP 由 Claude Code 启 (`claude_plugin.json` 的 mcpServers), env 在 plugin.json 内定义。如果 env-style 维持, OK; 若要彻底改, MCP server 启动时也读 config.json。

实际 MCP plugin.json 已写 `${CLAUDE_PLUGIN_ROOT}/mcp/server.py` 等 — env 是 Claude Code 注入。**MCP 启动 env 视为平台契约保留**, MCP 内业务逻辑改读 config。

#### lint/run.py
`os.environ.get("OBSIDIAN_VAULT")` 等 → 改读 config (默认), CLI `--vault` 覆盖。

### 4. install.sh 除外

`install.sh` 保留 env 使用 (装机阶段写 config.json, 之前需 env 引导)。

### 5. 测试

新建 `tests/python/test_config_only.py`:
- grep plugin 内 env vars (除 CLAUDE_PLUGIN_ROOT / CORTEX_JOB_LABEL / CORTEX_STREAM_TEE_FILE), 应 0 或仅 fallback 引用
- 测试 cortex_config.py 各 helper

## 实施

### Step 1: cortex_config.py 加 helper API (Python)
### Step 2: scripts/lib/config.sh 加 helper (Bash)
### Step 3: hooks/* 改读 config (保 CLAUDE_PLUGIN_ROOT)
### Step 4: scripts/cron/* + scripts/install_wrappers.sh 改读 config
### Step 5: lint/run.py + mcp/* 改读 config
### Step 6: 测试 + marketplace sync

## 验收

- [ ] cortex_config.py 含 get_vault / get_plugin_root / get_lang / get_settings_path / get_timeout
- [ ] scripts/lib/config.sh 含 cx_get_vault 等
- [ ] grep `OBSIDIAN_VAULT\|CORTEX_VAULT\|CORTEX_LANG\|CORTEX_SETTINGS\|CORTEX_TIMEOUT\|CORTEX_DRY_RUN\|CORTEX_SYNC_TEMPLATES` 仅在 install.sh + 平台契约处 + 测试 + 文档
- [ ] CLAUDE_PLUGIN_ROOT 保留 (平台契约)
- [ ] CORTEX_JOB_LABEL / CORTEX_STREAM_TEE_FILE 改 CLI 或保留 (内部通信)
- [ ] 278 tests + 新 test_config_only PASS
- [ ] marketplace 同步

## 风险

| 风险 | 缓解 |
|------|------|
| install.sh 写 config.json 前调 hook | install.sh 例外, 用 env 引导 |
| Claude Code 平台 env (CLAUDE_PLUGIN_ROOT) 必保 | 显式保留 |
| 测试 fixture 用 env mock vault | 改为写 mock config.json |
| MCP server 启动早于 config | MCP plugin.json env 保留 (平台契约), 内部业务改 config |
| 跨平台 ~/.cortex/config.json | Path.home() 跨平台 |

## 子任务

跨多文件 (~30+), 单 trellis-implement 串行。
