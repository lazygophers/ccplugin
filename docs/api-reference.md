# API 参考

> Claude Code 插件 API 完整参考文档

## 目录

1. [plugin.json API](#plugin-json-api)
2. [Commands API](#commands-api)
3. [Agents API](#agents-api)
4. [Skills API](#skills-api)
5. [Hooks API](#hooks-api)
6. [MCP Servers API](#mcp-servers-api)
7. [LSP Servers API](#lsp-servers-api)
8. [marketplace.json API](#marketplace-json-api)

## plugin.json API

插件清单文件，定义插件的基本信息和组件路径。

### Schema

```typescript
interface PluginJson {
  // 必需字段
  name: string;              // 插件名称（kebab-case）

  // 可选元数据
  version?: string;          // 语义化版本
  description?: string;      // 插件描述
  author?: AuthorInfo;       // 作者信息
  homepage?: string;         // 文档 URL
  repository?: string;       // 源代码 URL
  license?: string;          // 许可证
  keywords?: string[];       // 关键词

  // 组件路径
  commands?: string | string[];     // 命令路径
  agents?: string | string[];       // 代理路径
  skills?: string | string[];       // 技能路径
  hooks?: string | HookConfig;      // 钩子配置
  mcpServers?: string | MCPServerConfig;
  outputStyles?: string | string[];
  lspServers?: string | LSPServerConfig;
}

interface AuthorInfo {
  name: string;
  email?: string;
  url?: string;
}
```

### 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 插件唯一标识符，kebab-case |
| `version` | string | 否 | 语义化版本，如 "1.0.0" |
| `description` | string | 推荐 | 插件用途说明 |
| `author` | object | 推荐 | 作者信息 |
| `keywords` | array | 否 | 标签数组，便于发现 |
| `commands` | string/array | 否 | 命令文件/目录路径 |
| `agents` | string/array | 否 | 代理文件路径 |
| `skills` | string/array | 否 | 技能目录路径 |
| `hooks` | string/object | 否 | 钩子配置 |
| `mcpServers` | string/object | 否 | MCP 服务器配置 |
| `lspServers` | string/object | 否 | LSP 服务器配置 |

### 完整示例

```json
{
  "name": "code-formatter",
  "version": "1.2.0",
  "description": "自动代码格式化工具",
  "author": {
    "name": "Developer",
    "email": "dev@example.com",
    "url": "https://github.com/developer"
  },
  "homepage": "https://github.com/developer/code-formatter",
  "repository": "https://github.com/developer/code-formatter",
  "license": "MIT",
  "keywords": ["format", "code", "style", "prettier", "black"],
  "commands": "./commands/",
  "agents": "./agents/",
  "skills": "./skills/",
  "hooks": "./hooks/hooks.json"
}
```

## Commands API

自定义斜杠命令，扩展 Claude Code 功能。

### Frontmatter Schema

```typescript
interface CommandFrontmatter {
  description: string;       // 必需：命令描述
  argumentHint?: string;     // 参数提示
  allowedTools?: string;     // 允许的工具
  model?: string;            // 使用的模型
}
```

### 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `description` | string | 是 | 命令描述，显示在命令列表中 |
| `argument-hint` | string | 否 | 参数提示，如 `[file-path]` |
| `allowed-tools` | string | 否 | 允许的工具模式 |
| `model` | string | 否 | 模型：sonnet, haiku, opus |

### 参数占位符

| 占位符 | 描述 | 示例 |
|--------|------|------|
| `$ARGUMENTS` | 捕获所有参数 | `/cmd arg1 arg2` → `arg1 arg2` |
| `$1`, `$2`, ... | 位置参数 | `/cmd a b` → `$1=a`, `$2=b` |

### Bash 命令内联

使用 `!` 前缀执行 Bash 命令并嵌入结果：

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*)
---

## Context

- Status: !`git status`
- Diff: !`git diff HEAD`
```

### 工具权限模式

```markdown
---
allowed-tools: Bash(prettier*)    # 允许 prettier 相关命令
allowed-tools: Bash(git:*)        # 允许所有 git 命令
allowed-tools: Bash(*)            # 允许所有 Bash 命令
allowed-tools: Read, Write        # 允许 Read 和 Write 工具
---
```

### 完整示例

```markdown
---
description: 格式化代码
argument-hint: [file-path]
allowed-tools: Bash(prettier*), Bash(black*)
model: sonnet
---

# format

格式化指定文件或整个项目。

## 使用方法

/format [file-path]

## 参数

- `file-path`: 可选，要格式化的文件路径

## 执行逻辑

1. 如果指定了文件路径，格式化该文件
2. 否则格式化整个项目

## 执行

\`\`\`bash
if [ -n "$ARGUMENTS" ]; then
    case "${ARGUMENTS##*.}" in
        js|ts|jsx|tsx|json|md)
            npx prettier --write "$ARGUMENTS"
            ;;
        py)
            black "$ARGUMENTS"
            ;;
        go)
            gofmt -w "$ARGUMENTS"
            ;;
        *)
            echo "Unsupported file type: ${ARGUMENTS##*.}"
            ;;
    esac
else
    npx prettier --write "**/*.{js,ts,jsx,tsx,json,md}"
    black **/*.py
fi
\`\`\`
```

## Agents API

专用子代理，处理特定任务。

### Frontmatter Schema

```typescript
interface AgentFrontmatter {
  name: string;              // 必需：代理名称
  description: string;       // 必需：代理描述
  tools?: string;            // 工具列表（逗号分隔）
  model?: string;            // 模型别名或 'inherit'
  permissionMode?: string;   // 权限模式
  skills?: string;           // 技能列表（逗号分隔）
}
```

### 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 代理唯一标识符，小写和连字符 |
| `description` | string | 是 | 代理用途描述 |
| `tools` | string | 否 | 工具列表，逗号分隔 |
| `model` | string | 否 | 模型：sonnet, haiku, opus, inherit |
| `permissionMode` | string | 否 | 权限模式：default, grant, deny |
| `skills` | string | 否 | 自动加载的技能，逗号分隔 |

### 工具列表

| 工具 | 描述 |
|------|------|
| `Read` | 读取文件 |
| `Write` | 写入文件 |
| `Edit` | 编辑文件 |
| `Grep` | 搜索文件内容 |
| `Glob` | 搜索文件名 |
| `Bash` | 执行命令 |
| `WebSearch` | 网络搜索 |
| `WebFetch` | 获取网页 |

### 完整示例

```markdown
---
name: code-reviewer
description: 代码审查专家，专注于代码质量、安全性和性能
tools: Read, Grep, Bash
model: sonnet
permissionMode: default
skills: security-checklist, performance-optimization
---

# Code Reviewer Agent

你是一个专业的代码审查专家。

## 职责

- 审查代码质量
- 识别安全漏洞
- 发现性能问题
- 提供改进建议

## 审查流程

1. **代码质量**
   - 可读性检查
   - 命名规范
   - 代码结构

2. **安全审查**
   - SQL 注入
   - XSS 攻击
   - CSRF 防护
   - 敏感数据处理

3. **性能分析**
   - 算法复杂度
   - 内存使用
   - I/O 操作

## 输出格式

### 问题列表

| 文件 | 行号 | 类型 | 描述 | 建议 |
|------|------|------|------|------|
| ... | ... | ... | ... | ... |

### 总体评分

- 代码质量：X/10
- 安全性：X/10
- 性能：X/10
```

## Skills API

Agent Skills，提供特定领域的知识和指导。

### Frontmatter Schema

```typescript
interface SkillFrontmatter {
  name: string;              // 必需：技能名称
  description: string;       // 必需：技能描述
  autoActivate?: string;     // 自动激活条件
  allowedTools?: string;     // 允许的工具
  model?: string;            // 使用的模型
}
```

### 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 技能名称，小写、数字、连字符，最多64字符 |
| `description` | string | 是 | 用途和使用时机，最多1024字符 |
| `auto-activate` | string | 否 | 自动激活条件，如 `always:true` |
| `allowed-tools` | string | 否 | 工具列表，逗号分隔 |
| `model` | string | 否 | 模型：sonnet, haiku, opus |

### 自动激活条件

| 条件 | 描述 |
|------|------|
| `always:true` | 始终激活 |
| `filePattern:*.py` | 匹配文件模式时激活 |
| `keyword:security` | 提到关键词时激活 |

### 完整示例

```yaml
---
name: security-auditor
description: 安全审计技能。当用户提到安全检查、漏洞扫描或安全相关问题时自动激活。
auto-activate: always:true
allowed-tools: Read, Grep, Bash
model: sonnet
---

# Security Auditor

## 使用场景

- 用户要求安全审计
- 提到漏洞或安全问题
- 需要安全最佳实践
- 代码审查时检查安全

## 审查要点

### 1. 注入攻击

- SQL 注入
- 命令注入
- LDAP 注入
- XPath 注入

### 2. 跨站脚本 (XSS)

- 反射型 XSS
- 存储型 XSS
- DOM 型 XSS

### 3. 认证授权

- 弱密码策略
- 会话管理
- 权限检查
- 敏感数据暴露

### 4. 数据保护

- 敏感数据加密
- 日志脱敏
- 传输安全

## 检查清单

- [ ] 输入验证
- [ ] 输出编码
- [ ] 参数化查询
- [ ] 最小权限原则
- [ ] 安全头配置
```

## Hooks API

在特定事件发生时自动执行命令。

### Hook Schema

```typescript
interface HookConfig {
  hooks: {
    [eventName: string]: HookRule[];
  };
}

interface HookRule {
  matcher?: string;          // 工具匹配模式
  hooks: HookAction[];
}

interface HookAction {
  type: "command" | "function";  // 动作类型
  command?: string;              // 命令路径
  env?: { [key: string]: string }; // 环境变量
}
```

### 可用事件

| 事件 | 触发时机 |
|------|----------|
| `SessionStart` | 会话开始 |
| `SessionEnd` | 会话结束 |
| `PreToolUse` | 工具使用前 |
| `PostToolUse` | 工具使用后 |
| `SubagentStart` | 子代理启动 |
| `SubagentStop` | 子代理停止 |
| `PermissionRequest` | 权限请求 |
| `UserPromptSubmit` | 用户提交提示 |
| `Stop` | 会话停止 |
| `Notification` | 系统通知 |

### Matcher 模式

```javascript
"Write|Edit"       // 匹配 Write 或 Edit
"Bash(*)"          // 匹配所有 Bash 工具
"Bash(git:*)"      // 匹配 git 命令
"Bash(npm:*)"      // 匹配 npm 命令
"*"                // 匹配所有工具
```

### 环境变量

| 变量 | 描述 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}` | 插件目录绝对路径 |
| `${CLAUDE_PLUGIN_LSP_LOG_FILE}` | LSP 日志路径 |

### 完整示例

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/init.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "env": {
              "FORMAT": "true",
              "PROJECT_ROOT": "${PROJECT_ROOT}"
            }
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash(rm:*)",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-rm.sh"
          }
        ]
      }
    ]
  }
}
```

## MCP Servers API

Model Context Protocol 服务器配置。

### 配置文件 (.mcp.json)

```typescript
interface MCPConfig {
  mcpServers: {
    [name: string]: MCPServer;
  };
}

interface MCPServer {
  command: string;           // 启动命令
  args?: string[];           // 命令参数
  env?: { [key: string]: string }; // 环境变量
}
```

### 示例

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uvx",
      "args": ["mcp-server-filesystem", "/path/to/allowed/dir"],
      "env": {
        "LOG_LEVEL": "info"
      }
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## LSP Servers API

Language Server Protocol 服务器配置。

### 配置文件 (.lsp.json)

```typescript
interface LSPConfig {
  lspServers: {
    [name: string]: LSPServer;
  };
}

interface LSPServer {
  command: string;           // 启动命令
  args?: string[];           // 命令参数
  filePatterns?: string[];   // 文件匹配模式
}
```

### 示例

```json
{
  "lspServers": {
    "gopls": {
      "command": "gopls",
      "args": ["serve"],
      "filePatterns": ["**/*.go"]
    },
    "pyright": {
      "command": "pyright-langserver",
      "args": ["--stdio"],
      "filePatterns": ["**/*.py"]
    },
    "typescript-language-server": {
      "command": "typescript-language-server",
      "args": ["--stdio"],
      "filePatterns": ["**/*.ts", "**/*.tsx"]
    }
  }
}
```

## marketplace.json API

市场清单文件，定义市场信息和插件列表。

### Schema

```typescript
interface MarketplaceJson {
  name: string;              // 市场标识符
  version?: string;          // 市场版本
  description?: string;      // 市场描述
  author?: AuthorInfo;       // 作者信息
  homepage?: string;         // 文档 URL
  repository?: string;       // 源代码 URL
  license?: string;          // 许可证
  owner: OwnerInfo;          // 必需：维护者信息
  plugins: PluginEntry[];    // 必需：插件列表
}

interface OwnerInfo {
  name: string;
  email?: string;
}

interface PluginEntry {
  name: string;              // 必需：插件名称
  source: string | SourceConfig; // 必需：插件来源
  description?: string;      // 插件描述
  version?: string;          // 版本号
  author?: AuthorInfo;       // 作者信息
  keywords?: string[];       // 关键词
  strict?: boolean;          // 是否要求 plugin.json
}

interface SourceConfig {
  source: "github" | "git" | "local";
  repo?: string;             // GitHub 仓库
  url?: string;              // Git URL
}
```

### 插件来源

**本地路径**：

```json
{
  "source": "./plugins/my-plugin"
}
```

**GitHub 仓库**：

```json
{
  "source": {
    "source": "github",
    "repo": "username/plugin-repo"
  }
}
```

**Git 仓库**：

```json
{
  "source": "https://github.com/username/plugin-repo.git"
}
```

### 完整示例

```json
{
  "name": "ccplugin-market",
  "version": "1.0.0",
  "description": "Claude Code 插件市场",
  "owner": {
    "name": "Lazygophers",
    "email": "admin@lazygophers.com"
  },
  "plugins": [
    {
      "name": "python",
      "source": "./plugins/languages/python",
      "description": "Python 开发插件",
      "version": "1.0.0",
      "keywords": ["python", "development"],
      "strict": true
    },
    {
      "name": "golang",
      "source": "./plugins/languages/golang",
      "description": "Golang 开发插件",
      "keywords": ["golang", "go", "development"]
    },
    {
      "name": "git",
      "source": "./plugins/tools/git",
      "description": "Git 操作插件",
      "keywords": ["git", "workflow"]
    }
  ]
}
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Invalid JSON` | JSON 格式错误 | 检查语法，使用 jq 验证 |
| `Missing name` | 缺少 name 字段 | 添加 name 字段 |
| `Invalid name` | 名称格式错误 | 使用 kebab-case |
| `File not found` | 文件不存在 | 检查路径 |
| `Invalid frontmatter` | Frontmatter 格式错误 | 检查 YAML 语法 |

### 验证命令

```bash
# 验证 plugin.json
cat .claude-plugin/plugin.json | jq .

# 验证 marketplace.json
cat .claude-plugin/marketplace.json | jq .

# 验证 hooks.json
cat hooks/hooks.json | jq .

# 检查文件存在
ls -la .claude-plugin/plugin.json
```

## 参考资源

### 项目文档

- [插件开发指南](plugin-development.md) - 完整开发教程
- [最佳实践](best-practices.md) - 开发最佳实践
- [支持的语言](supported-languages.md) - 语言选择指南

### 官方文档

- [Claude Code 插件参考](https://code.claude.com/docs/en/plugins-reference)
- [插件市场规范](https://code.claude.com/docs/en/plugin-marketplaces)
