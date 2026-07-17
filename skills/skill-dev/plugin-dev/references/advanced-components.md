# 高级组件：MCP / LSP / monitors / themes / channels / bin / settings / userConfig / dependencies

> 主 SKILL.md 流程 A 步骤 4 各组件行的细节层。skills/agents/commands 的单组件写法路由 `/skill-dev`。

## MCP Servers（外部工具集成）

### 配置位置

插件根 `.mcp.json`，或 `plugin.json` 内联 `mcpServers`：

```jsonc
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["--from", "${CLAUDE_PLUGIN_ROOT}/scripts", "my-mcp-server"],
      "env": { "API_KEY": "${API_KEY}", "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data" }
    }
  }
}
```

### stdio vs SSE/http

| 类型 | 字段 | 占位符替换字段 |
|------|------|--------------|
| **stdio**（本地进程） | `command` + `args` | command / args / env |
| **http / sse / ws**（远程） | `url` + `headers` / `headersHelper` | url / headers / headersHelper |

### 约定

- **密钥 `${ENV_VAR}` 引用禁硬编码** — P0 安全（同 hook 路径变量规则）
- **工具命名** — 插件自带 MCP 工具暴露为 scoped 名 `mcp__plugin_<plugin>_<server>__<tool>`；server name 选 kebab-case 短名省 token
- **跨插件作用域** — 同名 server 在不同插件不冲突（前缀已含 plugin 名）
- **hook 调自带 server** — matcher 用 scoped 工具名，`mcp_tool` 的 `server` 用 `plugin:<plugin>:<server>`（见 hooks.md）
- 启动时机：插件启用即自动起，无需用户指示

## LSP Servers（代码智能）

插件根 `.lsp.json`，或 `plugin.json` 内联 `lspServers`。

### 必填字段

| Field | Description |
|-------|-------------|
| `command` | LSP 二进制（须在 PATH，用户机器预装）|
| `extensionToLanguage` | 文件扩展名 → 语言标识 map（如 `{".go":"go"}`）|

### 可选字段

| Field | Description |
|-------|-------------|
| `args` | 命令行参数 |
| `transport` | `stdio`（默认）/ `socket` |
| `env` | 启动时环境变量 |
| `initializationOptions` | 初始化阶段传给 server 的选项 |
| `settings` | 经 `workspace/didChangeConfiguration` 传 |
| `workspaceFolder` | workspace 文件夹路径 |
| `startupTimeout` | 启动等待上限（毫秒）|
| `shutdownTimeout` | 优雅关闭等待（毫秒），超时强杀；不设则无超时 |
| `restartOnCrash` | 崩溃后是否重启（默认 `true`，设 `false` 则崩后停着）|
| `maxRestarts` | 最大重启尝试次数 |
| `diagnostics` | 编辑后是否推 diagnostics 到 Claude 上下文（默认 `true`，设 `false` 保留导航但抑制自动诊断注入）|

### 🔴 v2.1.205 陷阱

`restartOnCrash` 和 `shutdownTimeout` 需 Claude Code **v2.1.205+**。**v2.1.205 前**：schema 接受这两个字段，但**设了任一都会导致该 LSP server 启动时被完全跳过**，原因只在 `claude --debug` 可见——静默失效。

同理：v2.1.205 前初始化失败的 server 仍**占用**其扩展名，挡住同扩展名的有效 server；v2.1.205 后失败不再占扩展名，其他 server 可接手。

### 同扩展名多 server 规则

多个启用 LSP server 声明同一扩展名（同插件或跨插件）：**第一个注册的处理该扩展名，其余永不起**。`/plugin` 界面会警告并指出活跃的插件。

### 其他约定

- 用户机器须预装 language server 二进制（`gopls`/`rust-analyzer` 等）。LSP 插件只配置如何连接，不含 server 本身；`/plugin` Errors 标签出 `Executable not found in $PATH` 即缺二进制
- **常见语言（TS/Python/Rust）优先装官方 LSP 插件**（pyright-lsp / typescript-lsp / rust-analyzer-lsp），自建仅用于官方未覆盖的语言
- 环境变量 `${CLAUDE_PLUGIN_LSP_LOG_FILE}` 拿 LSP 日志路径
- 配置非法（缺 `command` 或 `extensionToLanguage`）→ 该 server 跳过，其他仍启动，`claude --debug` 看原因

## Monitors（后台监控 · experimental）

`monitors/monitors.json`（JSON 数组），或 `plugin.json` 内联 `experimental.monitors`。

```jsonc
[
  {
    "name": "deploy-status",
    "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/poll-deploy.sh",
    "description": "Deployment status changes"
  },
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log",
    "when": "on-skill-invoke:debug"
  }
]
```

### 必填

| Field | Description |
|-------|-------------|
| `name` | 插件内唯一标识（reload / skill 再次 invoke 时防重复起进程）|
| `command` | shell 命令，session 工作目录里作持久后台进程跑 |
| `description` | 简短说明，显示在任务面板和 notification 摘要 |

### 可选

| Field | Description |
|-------|-------------|
| `when` | 启动时机：`always`（默认，session 起或 plugin reload）/ `on-skill-invoke:<skill-name>`（首次 dispatch 该 skill 时起）|

### 行为 + 限制

- 每行 stdout → 作为 notification 送 Claude；用户无需指示开始 watch
- `command` 支持 `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` / `${CLAUDE_PROJECT_DIR}` + `${ENV_VAR}`；要切插件目录就 `cd "${CLAUDE_PLUGIN_ROOT}" && ...`
- 🛓 **`${user_config.*}` 被拒** — shell 命令替换 config 值会让 shell 执行任意内容，Claude Code 报 [plugin-command-references-user-config](/en/errors#plugin-command-references-user-config) 错误。monitor 进程也**不收** `CLAUDE_PLUGIN_OPTION_<KEY>` 环境变量 → 让 monitor 脚本从**自己拥有的 config 文件**读值
- 🛓 **只跑在交互式 CLI session**；Monitor tool 不可用的 host 跳过
- 跑在 unsandboxed 信任级（同 hook）
- session 中途 disable 插件**不停**已跑 monitor，session 结束才停
- experimental 组件：manifest schema 可能在版本间变；声明位置在迁移中（顶层仍可，`validate` 警告，未来将强制 `experimental.*`）

## Themes（颜色主题 · experimental）

`themes/` 下 JSON 文件，或 `plugin.json` 内联 `experimental.themes`。出现在 `/theme` 里与内置预设和用户本地主题并列。

```jsonc
{
  "name": "Dracula",
  "base": "dark",
  "overrides": {
    "claude": "#bd93f9",
    "error": "#ff5555",
    "success": "#50fa7b"
  }
}
```

- `base` = `dark` / `light`（预设基底）
- `overrides` = 稀疏 color token map（只覆盖要改的）
- 选中插件主题持久化为 `custom:<plugin>:<slug>` 到用户配置
- 插件主题**只读**；`/theme` 里 `Ctrl+E` 拷贝到 `~/.claude/themes/` 让用户编辑副本
- experimental 组件（同 monitors 的 schema 变动告警）

## Channels（消息注入通道）

`channels` 数组。每个 channel 绑定插件提供的一个 MCP server，向会话注入内容（Telegram / Slack / Discord 风格）。

```jsonc
{
  "channels": [
    {
      "server": "telegram",
      "userConfig": {
        "bot_token": { "type": "string", "title": "Bot token", "description": "...", "sensitive": true },
        "owner_id":  { "type": "string", "title": "Owner ID", "description": "..." }
      }
    }
  ]
}
```

- `server` **必填**，须匹配插件 `mcpServers` 中一个 key
- 每 channel 可选 `userConfig`（同顶层 userConfig schema），启用时让用户填 bot token / owner ID 等

## bin/（加入 Bash PATH）

插件根 `bin/` 下可执行文件，插件启用时加入 Bash 工具的 `PATH`。

- 用途：插件提供 CLI 工具，Claude 用 Bash 调用时不需写全路径
- 配合 thin wrapper 模式（见 hooks.md bin/ 段）：`bin/<name>` wrapper 调 `scripts/*.py`
- 编译型语言多平台二进制也放 `bin/`（见 multi-language.md）

## settings.json（插件默认设置）

插件根 `settings.json`，插件启用时应用默认配置。**仅支持两个 key**：

```jsonc
{
  "agent": "security-reviewer",
  "subagentStatusLine": { /* ... */ }
}
```

- `agent` = 插件 `agents/` 里某 agent name → 插件启用即激活该 agent 为主线程（system prompt + 工具限制 + model 全套生效）
- `settings.json` 优先级**高于** `plugin.json` 内的 `settings`
- 未知 key 静默忽略

## userConfig（暴露给用户的配置项）

声明启用插件时 Claude Code 提示用户填的值，替代手改 `settings.json`。

### 全字段

```jsonc
"userConfig": {
  "api_endpoint": {
    "type": "string",
    "title": "API endpoint",
    "description": "Your team's API endpoint"
  },
  "api_token": {
    "type": "string",
    "title": "API token",
    "description": "API authentication token",
    "sensitive": true,
    "required": true
  },
  "max_active": {
    "type": "number", "title": "...", "description": "...",
    "default": 2, "min": 1, "max": 8
  },
  "watch_paths": {
    "type": "string", "multiple": true, "title": "...", "description": "..."
  }
}
```

| Field | 必填 | Description |
|-------|------|-------------|
| `type` | ✅ | `string` / `number` / `boolean` / `directory` / `file` |
| `title` | ✅ | 配置对话框标签 |
| `description` | ✅ | 字段下帮助文字（写 "推荐值 + 为什么 + 覆盖哪"）|
| `sensitive` | — | `true` = 输入掩码 + 存 secure storage（非 settings.json）|
| `required` | — | `true` = 空值时校验失败 |
| `default` | — | 用户不提供时用 |
| `multiple` | — | 仅 `string`，允许多值数组 |
| `min` / `max` | — | 仅 `number` 边界 |

key 必须是合法标识符。

### 🔴 值怎么被读到（3 条路径）

1. **`${user_config.KEY}` 替换** — MCP / LSP server 配置、hook 命令可用；非 sensitive 还可在 skill / agent 内容替换
2. **`CLAUDE_PLUGIN_OPTION_<KEY>` 环境变量** — 所有值导出给 hook 进程（`<KEY>` = option key 大写）。🛓 monitor 进程**不收**这个，须从 config 文件读
3. **shell 字段拒绝 `${user_config.*}`** — hook 的 shell-form command / monitor command / MCP `headersHelper` 替换 config 值会让 shell 执行任意内容，组件**报错**失败。改用：
   - hook → exec form（`args`）或从环境变量读
   - monitor → 脚本从 config 文件读
   - headersHelper → 脚本从 config 文件读

### 存储

- **非 sensitive** → settings.json 的 `pluginConfigs[<plugin-id>].options`（v2.1.207+ 只写/读 user settings + `--settings` + managed settings；project/local settings 被忽略）
- **sensitive** → macOS Keychain（或无 keychain 平台的 `~/.claude/.credentials.json`）；与 OAuth token 共享，**总限约 2KB** → sensitive 值保持小

### 范式

skein `max_active` / `max_parallel` 是真实范例：数值带 `min`/`max`，`description` 写 "推荐 2（与 subtask 级并发一致）。覆盖 .skein/config.yaml"。

## dependencies（插件依赖）

`plugin.json` 的 `dependencies` 数组，声明本插件需要的其他插件，可选 semver 版本约束：

```jsonc
"dependencies": [
  "helper-lib",
  { "name": "secrets-vault", "version": "~2.1.0" }
]
```

- 字符串项 = 仅插件名；对象项 = name + version（semver 约束）
- 详见 [plugin-dependencies](https://code.claude.com/docs/en/plugin-dependencies)：依赖插件缺失时行为、启用/禁用级联
- ⚠️ 主 SKILL.md 体检不含依赖可用性检查（依赖在本机未必装），发布前需文档说明
