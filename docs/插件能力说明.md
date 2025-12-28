# Claude Code 插件系统能力说明

> 基于 Claude Code 官方文档
> 版本：Claude Code 1.0+
> 更新日期：2025-01-15

## 概述

Claude Code 插件系统提供了 5 种核心能力，允许开发者扩展 Claude Code 的功能。

## 核心能力

### 1. Commands（斜杠命令）

**能力描述**：
注册自定义斜杠命令，用户可通过 `/command-name` 调用。

**使用场景**：
- 快速执行特定操作
- 简化重复性工作流
- 提供快捷方式

**文件位置**：
```
commands/
└── command-name.md
```

**Frontmatter 格式**：
```yaml
---
name: "command-name"
displayName: "Command Display Name"
description: "What this command does and when to use it"
argument-hint: "(optional arguments)"
---
```

**示例**：
```markdown
---
name: "analyze-code"
displayName: "Analyze Code Quality"
description: "Perform comprehensive code analysis"
argument-hint: "(file-or-directory)"
---

# Code Quality Analysis

Performs deep code analysis covering architecture, performance, and security.

## Usage
/analyze-code src/main.py
```

**特点**：
- 单一操作导向
- 指令简洁（< 200 tokens）
- 快速执行
- 支持参数传递

---

### 2. Agents（专用代理）

**能力描述**：
创建专业化的子代理，具有特定领域的专业知识和交互模式。

**使用场景**：
- 特定领域的专家助手
- 复杂任务的专业处理
- 对话式交互

**文件位置**：
```
agents/
└── agent-name.md
```

**Frontmatter 格式**：
```yaml
---
name: "agent-name"
displayName: "Agent Display Name"
description: "Agent specialization and role"
capabilities:
  - "capability1"
  - "capability2"
---
```

**示例**：
```markdown
---
name: "code-reviewer"
displayName: "Code Review Specialist"
description: "Conducts comprehensive code reviews"
capabilities:
  - "Code quality analysis"
  - "Security vulnerability detection"
  - "Performance optimization"
---

# Code Review Specialist

Specializes in comprehensive code reviews across multiple dimensions.
```

**特点**：
- 对话式交互
- 专业化角色定位
- 指令限制（< 500 tokens）
- 可定义多个能力

---

### 3. Skills（技能包）

**能力描述**：
提供可复用的知识包，自动或条件性地激活，为 Claude 提供上下文知识。

**使用场景**：
- 编码规范指南
- 最佳实践文档
- 检查清单
- 项目约定

**文件位置**：
```
skills/
└── skill-name/
    ├── SKILL.md          # 必需：主技能文件
    ├── scripts/          # 可选：可执行脚本
    ├── references/       # 可选：参考文档
    └── assets/           # 可选：模板和静态文件
```

**Frontmatter 格式（必需）**：
```yaml
---
name: "skill-identifier"
description: "Short action-oriented description"
version: "1.0.0"
auto-activate: "always"  # always/pattern/never
patterns: "*.py,*.js"    # 当 auto-activate=pattern 时使用
allowed-tools: "Read,Write,Bash"  # 可选：限制工具
license: "MIT"  # 可选
---
```

**示例**：
```markdown
---
name: "code-review-standards"
description: "Code review standards and quality checks"
version: "1.0.0"
auto-activate: "always"
---

# Code Review Standards

## Quality Checklist
- [ ] Naming follows conventions
- [ ] Tests added for new functionality
- [ ] No security vulnerabilities
- [ ] Performance impact assessed
```

**激活模式**：

| 模式 | 触发条件 | 使用场景 |
|------|---------|---------|
| `always` | 始终激活 | 通用规范、全局约定 |
| `pattern` | 文件模式匹配 | 语言特定规范（如 `*.py`） |
| `never` | 手动调用 | 特殊用途技能 |

**特点**：
- 内容限制（< 5000 words）
- 支持资源组织（scripts、references、assets）
- 可条件激活
- 可限制工具使用

---

### 4. Hooks（事件钩子）

**能力描述**：
在特定事件发生时执行 shell 命令，实现自动化工作流。

**使用场景**：
- 会话启动时初始化
- 工具调用前后的处理
- 用户提示前的验证
- 响应后的清理

**文件位置**：
```
hooks/
└── hooks.json
```

**配置格式**：
```json
{
  "hooks": [
    {
      "name": "session-start",
      "event": "onSessionStart",
      "command": "echo 'Session started'",
      "description": "Runs when session starts"
    },
    {
      "name": "pre-tool-call",
      "event": "onToolCall",
      "command": "validate-tool.sh",
      "description": "Validates tool calls"
    }
  ]
}
```

**支持的事件**：

| 事件 | 触发时机 | 用途 |
|------|---------|------|
| `onSessionStart` | 会话开始时 | 初始化、环境检查 |
| `onToolCall` | 工具调用前 | 参数验证、权限检查 |
| `onUserPrompt` | 用户输入前 | 输入预处理 |
| `onResponse` | 响应生成后 | 后处理、日志记录 |

**特点**：
- Shell 命令执行
- 支持环境变量
- 可阻塞或异步执行
- 错误处理和超时控制

---

### 5. MCP Servers（模型上下文协议）

**能力描述**：
通过 MCP 协议集成外部工具和数据源，扩展 Claude 的能力边界。

**使用场景**：
- 数据库查询
- API 集成
- 文件系统操作
- 外部服务调用

**配置位置**：

1. **在 plugin.json 中配置**：
```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "package.server"],
      "env": {
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

2. **独立 .mcp.json 文件**：
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": ["run", "python", "-m", "server"],
      "env": {}
    }
  }
}
```

**MCP 工具定义**：

```python
from mcp.server import Server
from mcp.types import Tool

server = Server("my-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="tool_name",
            description="What this tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        )
    ]

@server.call_tool()
async def call_tool(request):
    # Tool implementation
    pass
```

**支持的语言**：
- Python（推荐使用 MCP SDK）
- TypeScript/JavaScript
- 其他语言（通过 stdio 协议）

**特点**：
- 标准协议（JSON-RPC over stdio）
- 异步支持
- 类型安全（JSON Schema）
- 双向通信
- 资源访问

---

## 能力组合

插件可以组合使用多种能力：

```
插件示例
├── commands/           # 提供快捷命令
│   └── quick-fix.md
├── agents/            # 提供专业代理
│   └── debugging-expert.md
├── skills/            # 提供知识规范
│   └── debugging-guide/
│       └── SKILL.md
├── hooks/             # 自动化流程
│   └── hooks.json
└── .claude-plugin/    # MCP 集成
    └── plugin.json    # 包含 mcpServers 配置
```

## 能力矩阵

| 能力 | 触发方式 | 交互模式 | 执行环境 | 复杂度 |
|------|---------|---------|---------|--------|
| **Commands** | 用户调用 `/cmd` | 单次执行 | Claude 上下文 | 低 |
| **Agents** | 用户请求或自动 | 多轮对话 | Claude 上下文 | 中 |
| **Skills** | 自动激活或手动 | 被动提供知识 | Claude 上下文 | 低-中 |
| **Hooks** | 事件触发 | 无交互 | Shell 环境 | 低 |
| **MCP Servers** | 工具调用 | 请求-响应 | 独立进程 | 中-高 |

## 选择指南

### 选择 Commands 当：
- ✅ 需要快速执行单一操作
- ✅ 操作简单明确
- ✅ 用户需要显式控制

### 选择 Agents 当：
- ✅ 需要专业领域知识
- ✅ 涉及复杂多步骤任务
- ✅ 需要对话式交互

### 选择 Skills 当：
- ✅ 提供编码规范或最佳实践
- ✅ 知识需要自动应用
- ✅ 内容相对静态

### 选择 Hooks 当：
- ✅ 需要自动化流程
- ✅ 在特定时机执行操作
- ✅ 不需要 Claude 交互

### 选择 MCP Servers 当：
- ✅ 需要集成外部服务
- ✅ 操作涉及数据持久化
- ✅ 需要独立进程管理

## 最佳实践

### 1. 命名规范
- Commands：kebab-case（如 `analyze-code`）
- Agents：kebab-case（如 `code-reviewer`）
- Skills：kebab-case（如 `python-style-guide`）
- MCP Servers：kebab-case（如 `database-connector`）

### 2. 文档要求
- 所有组件必须有清晰的 description
- 提供使用示例
- 说明触发条件和使用场景

### 3. 性能考虑
- Commands 和 Agents 指令应简洁
- Skills 内容不应过大
- MCP Servers 应支持超时控制

### 4. 用户体验
- Commands 提供清晰的参数提示
- Agents 说明专业领域
- Skills 使用检查清单格式
- MCP 工具提供详细的错误信息

## 限制和约束

### Commands
- 指令长度：< 200 tokens
- 不支持长期状态保持
- 不支持复杂参数结构

### Agents
- 指令长度：< 500 tokens
- 每次对话重新初始化
- 不能直接调用其他 Agents

### Skills
- 内容长度：< 5000 words
- 不能执行动态逻辑
- 仅提供静态知识

### Hooks
- 仅支持 shell 命令
- 超时限制
- 不能阻塞过长时间

### MCP Servers
- 必须遵循 MCP 协议
- 通过 stdio 通信
- 需要独立进程管理

## 版本兼容性

| 能力 | 最低 Claude Code 版本 | 协议版本 |
|------|---------------------|---------|
| Commands | 1.0.0 | - |
| Agents | 1.0.0 | - |
| Skills | 1.0.0 | - |
| Hooks | 1.0.0 | - |
| MCP Servers | 1.0.0 | MCP 1.0+ |

## 参考资源

- [Claude Code 官方文档](https://code.claude.com/docs)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [插件开发指南](https://code.claude.com/docs/plugins)
- [MCP SDK 文档](https://github.com/modelcontextprotocol)

---

**文档来源**：根据 Claude Code 官方文档整理
**最后更新**：2025-01-15
**许可证**：MIT
