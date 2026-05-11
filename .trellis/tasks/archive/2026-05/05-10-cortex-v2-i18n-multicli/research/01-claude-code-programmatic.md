# Research: Claude Code 编程式调用 (programmatic / headless)

- **Query**: 为 cortex v2 日常维护 bash 脚本提供权威依据
- **Scope**: 本地实证 + 现有研究复用
- **Date**: 2026-05-11
- **CLI version**: `claude 2.1.138` (`/Users/luoxin/.local/bin/claude`)
- **环境**: macOS Darwin 25.3.0, GLM 后端 (`ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic`)

> 复用上下文: `.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/research/04-claude-code-deep-capabilities.md` (hook/skill/MCP 生态全景, 仍适用)。

---

## A. CLI flags 全集 (实测自 `claude --help`)

按调研用途分组 (`★` = cortex v2 cron 脚本必用)。

### A.1 入口 / 模式

| Flag | 作用 | 备注 |
|---|---|---|
| ★ `-p, --print` | 单次输出后退出 | 触发 non-interactive 模式; stdout 非 TTY 时自动跳过 workspace trust 对话框 |
| `-c, --continue` | 继续 cwd 下最近一次会话 | 与 `-p` 兼容 |
| `-r, --resume [value]` | 按 session id 或交互 picker 恢复 | value 留空 + 非 TTY 行为未实测 |
| `--fork-session` | 恢复时分配新 session id | 配 `-c`/`-r` 用 |
| `--from-pr [value]` | 恢复 PR 关联会话 | 不在 cron 范围 |
| `--session-id <uuid>` | 强制指定 session id | 便于脚本回查 jsonl |
| `--no-session-persistence` | **不写 jsonl 到 `~/.claude/projects/`** | **仅 `--print` 生效**; cron 防膨胀首选 |

### A.2 输入输出协议

| Flag | 作用 |
|---|---|
| ★ `--output-format <text\|json\|stream-json>` | 默认 `text`; `json` 返回 **JSON 数组** (含 init/assistant/result 事件); `stream-json` 一行一事件 (NDJSON) |
| ★ `--input-format <text\|stream-json>` | `stream-json` 仅 `--print` 有效, 用于实时多轮 stdin |
| `--include-partial-messages` | 含流式 chunk; 仅 `--print + stream-json` |
| `--include-hook-events` | 把 hook lifecycle 事件 (`hook_started`/`hook_response`) 塞进 stream | 默认 stream-json 也带 hook 事件 (实测见 §G) |
| `--replay-user-messages` | stdin 输入回显; 多轮调试用 |
| `--verbose` | 覆盖 verbose 配置, 提升事件密度 |
| `--json-schema <schema>` | 结构化输出校验 (JSON Schema) | cron 解析用 |

### A.3 上下文 / 权限

| Flag | 作用 |
|---|---|
| ★ `--settings <file-or-json>` | 加载额外 settings (env/perm/hook) — 即 ccplugin 项目惯用 `~/.claude/settings.glm-4.5-flash.json` 切廉价 model |
| ★ `--setting-sources <user,project,local>` | 限定加载哪几层 settings (默认全部); 隔离 cron 与开发环境 |
| ★ `--bare` | **禁 hook / LSP / plugin sync / auto-memory / CLAUDE.md auto-discovery / keychain**; 设 `CLAUDE_CODE_SIMPLE=1`; 鉴权强制 `ANTHROPIC_API_KEY` 或 settings 内 `apiKeyHelper` (OAuth/keychain 全禁) |
| `--system-prompt <prompt>` | 替换默认 system prompt |
| `--append-system-prompt <prompt>` | 追加 |
| `--add-dir <dirs...>` | 额外可访问目录 |
| `--allowed-tools <tools...>` | 白名单 (`"Bash(git *) Edit"`); 空格或逗号分隔 |
| `--disallowed-tools <tools...>` | 黑名单; 实测 `--disallowed-tools Bash` 后模型自陈无 Bash 工具, 会话仍 success 退出 (§G) |
| `--tools <tools...>` | 限定内置工具集; `""` 全禁, `"default"` 全开, 或显式 `"Bash,Edit,Read"` |
| `--permission-mode <mode>` | `acceptEdits`/`auto`/`bypassPermissions`/`default`/`dontAsk`/`plan` |
| `--allow-dangerously-skip-permissions` 或 `--dangerously-skip-permissions` | bypass 全部权限; 仅推荐沙箱 |
| `--disable-slash-commands` | 关闭 skills (SKILL.md 触发) |
| `--exclude-dynamic-system-prompt-sections` | 把 cwd/env/git status 移出 system prompt → 提高 cache hit |

### A.4 模型 / 计费

| Flag | 作用 |
|---|---|
| ★ `--model <name>` | 别名 `sonnet`/`opus` 或全名 `claude-sonnet-4-6` |
| `--fallback-model <name>` | 主模型过载时回退 (仅 `--print`) |
| `--effort <low\|medium\|high\|xhigh\|max>` | thinking effort 档位 |
| `--max-budget-usd <amount>` | 单次会话美元上限 (仅 `--print`) |
| `--betas <betas...>` | beta header (仅 API key 用户) |

### A.5 MCP / Plugin

| Flag | 作用 |
|---|---|
| `--mcp-config <files...>` | 显式加载 MCP server 配置 |
| ★ `--strict-mcp-config` | **只用 `--mcp-config`, 忽略其他 MCP 来源** |
| `--plugin-dir <path>` (可重复) | 临时加载 plugin 目录或 zip |
| `--plugin-url <url>` (可重复) | 远程 zip plugin |
| `--agent <name>` | 切换 agent profile |
| `--agents <json>` | inline 自定义 agent |

### A.6 调试 / 杂项

| Flag | 作用 |
|---|---|
| `-d, --debug [filter]` | `"api,hooks"` / `"!1p,!file"` 形式过滤 |
| `--debug-file <path>` | 写日志, 隐式开 debug |
| `--mcp-debug` | DEPRECATED (用 `--debug`) |
| `--brief` | 启用 `SendUserMessage` agent → user 工具 |
| `-n, --name <name>` | session 显示名 |
| `--ide` / `--chrome` / `--no-chrome` | 集成开关 |
| `--remote-control [name]` | 远程控制会话 |
| `--tmux` / `-w, --worktree` | 仅交互场景 |
| `--file <specs...>` | 启动时下载文件 (`file_id:path`) |
| `-v, --version` / `-h, --help` | 元 |

> 没找到 `--no-update-check` flag (问题描述误); 自动更新由 `claude doctor` / `claude update` 子命令控制。

### A.7 子命令 (subcommand)

`agents`, `auth`, `auto-mode`, `doctor`, `install`, `mcp`, `plugin`, `project`, `setup-token`, `ultrareview`, `update`。其中 `doctor` 注意会**生成 stdio MCP server 启动健康检查**, 仅在可信目录跑。

---

## B. 退出码 + stdout/stderr 协议 (实测)

### B.1 退出码

| 场景 | 实测 EXIT | 来源 |
|---|---|---|
| `-p` 正常返回 (text/json/stream-json) | `0` | §G test 1/2 |
| `-p --disallowed-tools Bash` 模型放弃用工具仍输出文本 | `0` | 即"工具被拒"不视失败; 解析 `permission_denials` 才知 |
| 非法 flag (`--output-format wrong`) | `1` | stderr `error: option ... is invalid` |
| API 鉴权失败 / 网络超时 | (未实测) | 推断⚠ 通常 `1`; 应解析 `is_error` 字段确认 |

**结论**: cron 脚本不能仅靠 `$?` 判断成败, 必须解析 `result.is_error` / `result.subtype`。

### B.2 stream-json line schema (实测于 §G)

每行一个 JSON 对象, `type` 字段分类:

| `type` | `subtype` 例 | 关键字段 | 说明 |
|---|---|---|---|
| `system` | `init` | `cwd`, `session_id`, `tools[]`, `mcp_servers[]`, `model`, `slash_commands[]`, `agents[]`, `skills[]`, `plugins[]`, `apiKeySource`, `claude_code_version`, `output_style`, `analytics_disabled`, `permissionMode`, `fast_mode_state` | 首行 |
| `system` | `hook_started` | `hook_id`, `hook_name`, `hook_event`, `session_id` | 默认 stream-json 即注入 hook 事件 (除非 `--bare`) |
| `system` | `hook_response` | + `output`, `stdout`, `stderr`, `exit_code`, `outcome` | hook 完成 |
| `assistant` | — | `message.content[]` (含 `thinking` / `text` / `tool_use`), `usage` | 模型轮次输出 |
| `user` | — | `tool_result` 内容 | 推断⚠ (非 bare 场景常见) |
| ★ `result` | `success` / `error_*` | `is_error`, `result` (final text), `duration_ms`, `duration_api_ms`, `num_turns`, `session_id`, `total_cost_usd`, `usage{...}`, `modelUsage{...}`, `permission_denials[]`, `terminal_reason`, `stop_reason` | **末行**, 永远只有一条 |

`--output-format json` = 把上述 NDJSON 装进**一个 JSON 数组**输出 (实测 list 长度 4 = init+2*assistant+result)。

### B.3 jq 提取惯用 pipeline

ccplugin 项目内既有用法 (`CLAUDE.md §代码质量检查规范`):

```bash
claude --settings ~/.claude/settings.glm-4.5-flash.json -p "<内容>" \
  --output-format stream-json --verbose | \
  jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

cortex v2 推荐范式:

```bash
# stream-json: 边过滤 hook 噪音边截取 result
claude -p "$PROMPT" --bare --output-format stream-json --verbose 2>err.log | \
  tee >(jq -c 'select(.type=="result")' > result.json) | \
  jq -c 'select(.type=="assistant")' > stream.log

# 失败检测
is_error=$(jq -r '.is_error' result.json)
[ "$is_error" = "true" ] && exit 2
final=$(jq -r '.result' result.json)
```

---

## C. session / transcript 持久化 (实测)

### C.1 路径

```
~/.claude/projects/<slug>/<session_id>.jsonl
```

`<slug>` 规则: cwd 绝对路径里 `/` → `-`, 例:

- `/Users/luoxin/persons/lyxamour/ccplugin` → `-Users-luoxin-persons-lyxamour-ccplugin`

实测: `claude -p ... --bare` 会**生成 jsonl** (`db7b22b8-*.jsonl 2.7K`, `6b82e1fd-*.jsonl 1.7K`), 即 `--bare` 不影响 transcript 写入; 只有 `--no-session-persistence` 阻止写盘。

### C.2 `--continue` vs `--resume`

| | `-c, --continue` | `-r, --resume [value]` |
|---|---|---|
| 选哪个 session | cwd 内**最近一次** | 显式 session id; 缺省 = 交互 picker |
| 与 `-p` 兼容 | 是 | 是 (id 形式) |
| 多 cwd 场景 | 受 cwd slug 限制 | 跨 cwd 可 (id 全局) |
| 配 `--fork-session` | 复制原 session 起新 id | 同 |

### C.3 历史 session 批处理

可读 `~/.claude/projects/*/<id>.jsonl` 做 offline 分析 (jsonl 格式与 stream-json 类似但增加 user/sidechain 字段; `claude-obsidian` 已有 fold 类范式见 archive 研究)。

`cleanupPeriodDays` (`~/.claude/settings.json`) 默认 30 控制保留天数。

---

## D. MCP / hook 在 `-p` 模式下的行为

实测 (§G):

1. **默认 `-p`**: SessionStart hook **全部触发并写入 stream-json** (我看到 7 个 `hook_started` + 多个 `hook_response`, 含 caveman 注入 ~2KB system prompt 进 stream)。这会污染日志 + 增加 token 消耗 + cron 不可控。
2. **`-p --bare`**: hook **完全跳过**, init 事件直接接 assistant; 没有 `hook_started`。`tools` 字段也变小 (init 仅 `Bash/Edit/Read`, 因为不加载 plugin skills)。
3. MCP: 默认 `-p` 加载所有配置的 MCP; `--bare` 时 init 显示 `mcp_servers: []`; 想保留少量, 用 `--strict-mcp-config --mcp-config <file>` 组合。
4. 没有 `--no-mcp` / `--no-hooks` 独立 flag — 都靠 `--bare` 一刀切, 或自定义 `--settings` 把 hook/MCP 配置清空。

**对 cortex 含义**: 维护脚本必须 `--bare`, 否则 hook 注入物 (e.g. caveman mode prompt, kioku wiki context) 会改变模型行为且每行 hook 事件都浪费时间。

---

## E. 每日维护脚本范式

### E.1 设计原则

| 原则 | 实现 |
|---|---|
| **可重复** | `--no-session-persistence` 防 jsonl 累积; 或定期清理 `~/.claude/projects` |
| **隔离** | `--bare` + `--setting-sources user` + 显式 `--settings ~/.claude/settings.glm-4.5-flash.json` |
| **省钱** | `--model glm-4.5-flash` (settings env 已配); `--max-budget-usd 0.20` 兜底 |
| **限权** | `--allowed-tools "Read,Glob,Grep"` (只读维护); 写型用 `--allowed-tools "Edit,Write,Bash(git add:*)"` |
| **可解析** | `--output-format stream-json --verbose`; `result` 行过滤 |
| **抗超时** | 外层 `timeout 300 claude ...`; `--max-budget-usd` 防费用炸 |
| **抗重入** | `flock` lockfile per script |
| **可观测** | stderr 写 `~/.claude/cron-logs/<script>-$(date +%F).log`; 失败时 `notify-send` / mail |

### E.2 cron 骨架 (lint vault)

```bash
#!/usr/bin/env bash
set -euo pipefail
LOCK=/tmp/cortex-lint-vault.lock
LOG_DIR=$HOME/.claude/cron-logs/cortex
mkdir -p "$LOG_DIR"
exec 9>"$LOCK"; flock -n 9 || { echo "already running" >&2; exit 0; }

DAY=$(date +%F)
RESULT_FILE="$LOG_DIR/lint-$DAY.json"

timeout 600 claude \
  --bare \
  --setting-sources user \
  --settings "$HOME/.claude/settings.glm-4.5-flash.json" \
  --no-session-persistence \
  --add-dir "$HOME/persons/knowledge/obsidian" \
  --allowed-tools "Read Glob Grep" \
  --max-budget-usd 0.30 \
  --output-format stream-json --verbose \
  -p "Run /wiki-lint, output orphan list as bullet markdown" \
  2>>"$LOG_DIR/lint-$DAY.err" | \
  tee "$LOG_DIR/lint-$DAY.ndjson" | \
  jq -c 'select(.type=="result")' > "$RESULT_FILE"

if [ "$(jq -r '.is_error' "$RESULT_FILE")" = "true" ]; then
  echo "lint failed: $(jq -r '.result' "$RESULT_FILE")" >&2
  exit 2
fi
```

### E.3 fold (历史 log rollup) 骨架

```bash
timeout 300 claude --bare --no-session-persistence \
  --settings "$SETTINGS" \
  --allowed-tools "Read Write Glob" \
  --output-format json \
  -p "$(cat prompts/fold.md)" | \
  jq -r '.[] | select(.type=="result") | .result' > "fold-$DAY.md"
```

### E.4 dashboard 生成 (canvas / table) 骨架

```bash
# 接受上游 jsonl, 通过 stream-json input 多轮喂入
cat events.ndjson | \
  claude --bare --no-session-persistence \
  --input-format stream-json --output-format stream-json --verbose \
  --allowed-tools "Write" \
  -p "Aggregate to dashboard.canvas" | \
  jq -c 'select(.type=="result")'
```

---

## F. 平台差异

| 平台 | 注意 |
|---|---|
| **macOS** | 默认 keychain 鉴权; `--bare` 强制走 `ANTHROPIC_API_KEY` / `apiKeyHelper`, 避开 keychain 弹窗; cron 用 launchd 时尤需 `--bare` (cron env 无 GUI keychain 访问) |
| **Linux** | 行为一致; jsonl 路径同 `~/.claude/projects` |
| **Docker** | 必须 `--bare` + 注入 `ANTHROPIC_API_KEY` env; 无 `~/.claude` 时 `--add-dir` + 自带 settings |
| **GitHub Actions** | 需 `ANTHROPIC_API_KEY` secret; 推荐 `--bare --no-session-persistence --strict-mcp-config --mcp-config /dev/null` (清空 MCP); 推断⚠ 实际 official action 见 anthropics/claude-code-action |

---

## G. 本地实证记录

### G.1 命令列表 (本次 session 跑的)

| # | 命令 | 关键观察 |
|---|---|---|
| 1 | `claude --version` | `2.1.138 (Claude Code)` |
| 2 | `claude --help` | flag 全集 (§A) |
| 3 | `claude -p "say hi" --output-format stream-json --verbose` | **大量 SessionStart hook 事件污染日志**; caveman mode prompt ~2KB 注入到第 9 行 hook_response.output |
| 4 | `claude -p "say hi only" --output-format stream-json --verbose --bare` | init → assistant(thinking) → assistant(text "Hi!") → result; **零 hook 事件**; tools 列表只剩 `Bash/Edit/Read`; mcp_servers `[]`; cost $0.002858 / 11.8s |
| 5 | `claude -p "say bye" --output-format json --bare` | 输出 **JSON 数组** (length 4); 末元素 `type=result subtype=success result="Bye! ..."` |
| 6 | `claude -p "..." --output-format wrong` | exit 1, stderr `error: option ... argument 'wrong' is invalid. Allowed choices are text, json, stream-json.` |
| 7 | `claude -p "use Bash..." --output-format json --bare --disallowed-tools "Bash"` | exit 0, 模型回复 "I don't have access to a Bash tool"; `permission_denials=[]` (因为模型没尝试调用); `is_error=false` |
| 8 | `ls ~/.claude/projects/-Users-luoxin-persons-lyxamour-ccplugin/db7b22b8-*.jsonl` | **--bare 仍写 transcript**; 只有 `--no-session-persistence` 才阻止 |

### G.2 init 事件结构 (—bare)

```json
{"type":"system","subtype":"init",
 "cwd":"/Users/luoxin/persons/lyxamour/ccplugin",
 "session_id":"db7b22b8-...","tools":["Bash","Edit","Read"],
 "mcp_servers":[],"model":"claude-opus-4-7[1m]",
 "permissionMode":"bypassPermissions",
 "slash_commands":[...],"agents":[...],"skills":[...],
 "plugins":[...],"apiKeySource":"none",
 "claude_code_version":"2.1.138","output_style":"default",
 "analytics_disabled":true,"fast_mode_state":"off","uuid":"..."}
```

### G.3 result 事件结构 (—bare success)

```json
{"type":"result","subtype":"success","is_error":false,
 "api_error_status":null,"duration_ms":11800,"duration_api_ms":11754,
 "num_turns":1,"result":"Hi!","stop_reason":"end_turn",
 "session_id":"...","total_cost_usd":0.002858,
 "usage":{...},"modelUsage":{...},
 "permission_denials":[],"terminal_reason":"completed"}
```

### G.4 settings 文件用途速查

`~/.claude/settings.<flavor>.json` 命名约定 (从目录扫描 36 个文件):

| 前缀 | 用途 |
|---|---|
| `settings.json` | 默认主配置 (5.8K, 含 `fileSuggestion`, `cleanupPeriodDays`, env, hooks, permissions) |
| `settings.cch-<model>.json` | "Claude Code Hub" 风格切第三方/内部 endpoint |
| `settings.claude-<model>.json` | 官方 Anthropic model profile |
| `settings.glm-<variant>.json` | GLM (智谱) endpoint + model 切换, 每个 6.4K, env 设 `ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic` + `ANTHROPIC_AUTH_TOKEN` + 全部 `ANTHROPIC_DEFAULT_*_MODEL` |

ccplugin 项目惯例: 优化 commands/skills/agents 后用 `--settings ~/.claude/settings.glm-4.5-flash.json -p` 廉价模型回归测试 (CLAUDE.md §代码质量检查规范)。

---

## H. 对 cortex v2 的设计含义 (12 条)

1. **cron 脚本必须 `--bare`** — 否则 SessionStart hook (caveman / kioku injector / claude-obsidian PostCompact 等) 会注入数 KB 系统提示, 改变模型行为且每行 hook 事件污染日志。已在 §G test 3 vs 4 实证差异。
2. **必加 `--no-session-persistence`** — cron 跑长期会让 `~/.claude/projects/<slug>/` 膨胀; 维护类任务一般无需 resume, 写盘纯浪费 IO 与隐私面。
3. **退出码不可信** — `--disallowed-tools` 拒工具时仍 exit 0 (§G test 7); 必须解析 `result.is_error` + `result.subtype != "error_*"`。封装到 `cortex_run()` 共享函数。
4. **三种 output-format 选型** — `text` (人读)、`json` (整数组, 适合一次性脚本 jq), `stream-json` (NDJSON, 适合边跑边过滤 + 实时进度); cortex 默认 `stream-json --verbose`, 失败回放友好。
5. **GLM-4.5-flash + `--max-budget-usd 0.20-0.50`** — 廉价 model + 美元上限双保险; 实测 say hi 一轮 $0.0029, 维护脚本预算 $0.10 已绰绰有余。
6. **权限白名单优先** — `--allowed-tools "Read Glob Grep"` 只读类 (lint/dashboard) ; 写类显式 `"Edit Write Bash(git add:* git commit:*)"`; **永不**用 `--dangerously-skip-permissions` (即便 `--bare` 仍默认 `permissionMode: bypassPermissions`, 已够用)。
7. **`--strict-mcp-config --mcp-config /dev/null`** 显式清空 MCP — 避免 `obsidian` / `octocode` / `chrome-devtools-mcp` 等启动 stdio server 拖慢冷启动与额外鉴权。
8. **锁 + 超时双层** — 外层 `flock -n` 防重入, `timeout 300` 防 hang (LLM 长 thinking 兜底); 失败写 `~/.claude/cron-logs/<script>-$(date +%F).err` 加 mail/notify。
9. **复用 ccplugin 现有 `--settings` 模式** — 把 cortex 维护脚本统一用 `~/.claude/settings.glm-4.5-flash.json`, 与项目其他校验脚本一致; 团队/CI 可换 `cch-*` 系列。
10. **设 session id 便于追溯** — 关键 cron (e.g. weekly fold) 用 `--session-id $(uuidgen)` 显式分配, 写入日志, 必要时 `--resume <id>` 重放。
11. **transcript 不是 cortex 真相源** — `~/.claude/projects/*.jsonl` 由 CLI 控制, 格式可能随版本变化; cortex 真相源应是 cron 脚本自己 `tee` 的 ndjson + 解析后的结构化输出 (写入 obsidian wiki / cortex DB)。
12. **`--exclude-dynamic-system-prompt-sections` 提高 cache hit** — 多个 cortex 脚本跑相似提示, 移除 cwd/git/env 动态段后 prompt 可命中 prompt cache, 配合 GLM endpoint 的 `cache_read_input_tokens` 显著省钱 (§G test 4 已观察 896 cache_read tokens)。

---

## Caveats / Not Found

- 未实测: API 鉴权失败 / 网络 timeout / OOM 时确切退出码 — 推断⚠ 多为 1 或 124 (timeout coreutil); 上线前应人工触发一次断网验证。
- 未实测: `--input-format stream-json` 多轮喂入的 schema 细节; 文档说"realtime streaming input", 推断与 output 同结构, 但 `user` 事件字段未确证。
- 未实测: GitHub Actions 内调用是否 OAuth 直接走 `ANTHROPIC_API_KEY` env (`anthropics/claude-code-action` 官方 action 行为未独立验证)。
- `--no-update-check` flag 不存在 (问题描述包含错误); 自动更新由 `claude doctor` / `claude update` 子命令管理。
- jsonl 内 `user` / `tool_result` / `sidechain` 等事件 schema 未在本次 session 触发, 需要带工具的复杂 prompt 才能完整采集。
