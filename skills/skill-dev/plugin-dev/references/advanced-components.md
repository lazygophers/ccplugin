# 高级组件：MCP / LSP / monitors / bin / settings / userConfig

> 主 SKILL.md 流程 A 步骤 4 各组件行的细节层。skills/agents/commands 的单组件写法路由 `/skill-dev`。

## MCP Servers（外部工具集成）

### 配置位置

插件根 `.mcp.json`：

```jsonc
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["--from", "./scripts", "my-mcp-server"],
      "env": { "API_KEY": "${API_KEY}" }   // 密钥用 ${ENV_VAR} 引用，禁硬编码
    }
  }
}
```

### stdio vs SSE

| 类型 | 字段 | 适用 |
|------|------|------|
| **stdio**（本地进程） | `command` + `args` 启动子进程 | 本地工具（本仓库主用）|
| **SSE**（远程） | `url` 字段 | 远程服务（本仓库无实例）|

### 约定

- **密钥 `${ENV_VAR}` 引用禁硬编码** — 同 hook 路径变量规则（P0 安全）
- **工具命名** — MCP 工具暴露给模型为 `mcp__<server>__<tool>`；server name 选 kebab-case 短名（前缀越短越好，省 token）
- **MCP 工具调研** — 见 `docs/mcp-servers-research.md`（Office-Word-MCP-Server 等实例）

## LSP Servers（代码智能）

插件根 `.lsp.json`：

```jsonc
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": { ".go": "go" }
  }
}
```

- 用户机器需预装 language server 二进制（`gopls`/`rust-analyzer` 等）
- **常见语言（TS/Python/Rust）优先装官方 LSP 插件**，自建仅用于官方未覆盖的语言
- 环境变量 `${CLAUDE_PLUGIN_LSP_LOG_FILE}` 拿 LSP 日志路径

## Monitors（后台监控）

`monitors/monitors.json`，数组：

```jsonc
[
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log"
  }
]
```

- Claude Code 启动插件时自动起每个 monitor，**无需**指示 Claude 开始 watch
- `command` 的每行 stdout → 作为 notification 送给 Claude
- schema 含 `when` 触发条件 + 变量替换，完整见官方 plugins-reference Monitors 段

## bin/（加入 Bash PATH）

插件根 `bin/` 下的可执行文件，插件启用时加入 Bash 工具的 `PATH`。

- 用途：插件提供 CLI 工具，Claude 用 Bash 调用时不需写全路径
- 配合 thin wrapper 模式（见 `hooks.md` bin/ 段）：`bin/<name>` wrapper 调 `scripts/*.py`
- 编译型语言多平台二进制也放 `bin/`（见 `multi-language.md`）

## settings.json（插件默认设置）

插件根 `settings.json`，插件启用时应用默认配置。**目前仅支持两个 key**：

```jsonc
{
  "agent": "security-reviewer",        // 激活插件某 agent 为主线程（system prompt + 工具限制 + model 全套生效）
  "subagentStatusLine": { /* ... */ }   // 子代理状态行
}
```

- `agent` 设为插件 `agents/` 里定义的 agent name → 插件启用即改变 Claude Code 默认行为
- `settings.json` 优先级**高于** `plugin.json` 内的 `settings`
- 未知 key 静默忽略

## userConfig（暴露给用户的配置项）

### schema 四件套

```jsonc
"userConfig": {
  "max_active": {
    "type": "number",
    "title": "最大并行 task 数",
    "description": "同 session 同时 in_progress 的 task 上限。推荐 2（与 subtask 级并发一致）。覆盖 .skein/config.yaml。",
    "default": 2,
    "min": 1,
    "max": 8
  }
}
```

- 数值型加 `min`/`max`；`description` 写 "推荐值 + 为什么 + 覆盖哪个文件"——用户在设置面板看见就懂
- skein `max_active`/`max_parallel` 是真实范例

### 读取

- hook/command 经**环境变量**读（变量名 = config key 大写，如 `MAX_ACTIVE`）
- 或脚本读 plugin 注入的 config JSON
- 🛓 **禁假设 config 必填**，永远给 `default` 兜底

## outputStyles（自定义输出样式）

`outputStyles: string | string[]`，挂自定义输出样式（如 skein `themes/`）。

- 与 skills 同样可整目录或逐条挂
- 本仓库实例少，schema 见 `docs/api-reference.md`
