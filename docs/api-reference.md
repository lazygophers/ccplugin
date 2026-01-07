# API 参考

Claude Code 插件 API 完整参考。

## 目录

1. [plugin.json API](#plugin-json-api)
2. [Commands API](#commands-api)
3. [Agents API](#agents-api)
4. [Skills API](#skills-api)
5. [Hooks API](#hooks-api)
6. [marketplace.json API](#marketplace-json-api)

## plugin.json API

### Schema

```typescript
interface PluginJson {
  // 必需字段
  name: string;                    // 插件名称（kebab-case）

  // 可选元数据
  version?: string;                // 语义化版本
  description?: string;            // 插件描述
  author?: AuthorInfo;             // 作者信息
  homepage?: string;               // 文档 URL
  repository?: string;             // 源代码 URL
  license?: string;                // 许可证
  keywords?: string[];             // 关键词

  // 组件路径
  commands?: string | string[];    // 命令路径
  agents?: string | string[];      // 代理路径
  skills?: string | string[];      // 技能路径
  hooks?: string | HookConfig;     // 钩子配置
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

### 示例

```json
{
  "name": "code-formatter",
  "version": "1.2.0",
  "description": "自动代码格式化工具",
  "author": {
    "name": "Developer",
    "email": "dev@example.com"
  },
  "keywords": ["format", "code", "style"],
  "commands": "./commands/",
  "agents": "./agents/",
  "skills": "./skills/"
}
```

## Commands API

### Frontmatter Schema

```typescript
interface CommandFrontmatter {
  description: string;             // 必需：命令描述
  argumentHint?: string;           // 参数提示
  allowedTools?: string;           // 允许的工具
  model?: string;                  // 使用的模型
}
```

### 参数占位符

| 占位符 | 描述 |
|--------|------|
| `$ARGUMENTS` | 捕获所有参数 |
| `$1`, `$2`, ... | 位置参数 |

### Bash 命令

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*)
---
## Context
- Status: !`git status`
- Diff: !`git diff HEAD`
```

### 示例

```markdown
---
description: 格式化代码
argument-hint: [file-path]
allowed-tools: Bash(prettier*)
---
# format

格式化指定文件。
```

## Agents API

### Frontmatter Schema

```typescript
interface AgentFrontmatter {
  name: string;                    // 必需：代理名称
  description: string;             // 必需：代理描述
  tools?: string;                  // 工具列表（逗号分隔）
  model?: string;                  // 模型别名或 'inherit'
  permissionMode?: string;         // 权限模式
  skills?: string;                 // 技能列表（逗号分隔）
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

### 示例

```markdown
---
name: code-reviewer
description: 代码审查专家
tools: Read, Grep, Bash
model: sonnet
permissionMode: default
skills: security-checklist, performance-optimization
---
# Code Reviewer

你是一个代码审查专家...
```

## Skills API

### Frontmatter Schema

```typescript
interface SkillFrontmatter {
  name: string;                    // 必需：技能名称
  description: string;             // 必需：技能描述
  autoActivate?: string;           // 自动激活条件
  allowedTools?: string;           // 允许的工具
  model?: string;                  // 使用的模型
}
```

### 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 技能名称，小写、数字、连字符，最多64字符 |
| `description` | string | 是 | 用途和使用时机，最多1024字符 |
| `autoActivate` | string | 否 | 自动激活条件，如 "always:true" |
| `allowedTools` | string | 否 | 工具列表，逗号分隔 |
| `model` | string | 否 | 模型：sonnet, haiku, opus |

### 示例

```yaml
---
name: code-reviewer
description: 代码审查技能。当用户要求代码审查、质量检查或提到代码质量时自动激活。
auto-activate: always:true
allowed-tools: Read, Grep, Bash
model: sonnet
---
# Code Reviewer

## 使用场景
- 用户要求代码审查
- 提到质量检查
- 需要最佳实践
```

## Hooks API

### Hook Schema

```typescript
interface HookConfig {
  hooks: {
    [eventName: string]: HookRule[];
  };
}

interface HookRule {
  matcher?: string;                // 工具匹配模式
  hooks: HookAction[];
}

interface HookAction {
  type: 'command' | 'function';    // 动作类型
  command?: string;                // 命令路径
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

### Matcher 模式

```javascript
"Write|Edit"           // 匹配 Write 或 Edit
"Bash(*)"              // 匹配所有 Bash 工具
"Bash(git:*)"          // 匹配 git 命令
"*"                    // 匹配所有工具
```

### 环境变量

| 变量 | 描述 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}` | 插件目录绝对路径 |
| `${CLAUDE_PLUGIN_LSP_LOG_FILE}` | LSP 日志路径 |

### 示例

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "env": {
              "FORMAT": "true"
            }
          }
        ]
      }
    ]
  }
}
```

## marketplace.json API

### Schema

```typescript
interface MarketplaceJson {
  name: string;                    // 市场标识符
  version?: string;                // 市场版本
  description?: string;            // 市场描述
  author?: AuthorInfo;             // 作者信息
  homepage?: string;               // 文档 URL
  repository?: string;             // 源代码 URL
  license?: string;                // 许可证
  owner: OwnerInfo;                // 必需：维护者信息
  plugins: PluginEntry[];          // 必需：插件列表
}

interface OwnerInfo {
  name: string;
  email?: string;
}

interface PluginEntry {
  name: string;                    // 必需：插件名称
  source: string | SourceConfig;   // 必需：插件来源
  description?: string;            // 插件描述
  version?: string;                // 版本号
  author?: AuthorInfo;             // 作者信息
  keywords?: string[];             // 关键词
  strict?: boolean;                // 是否要求 plugin.json
}

interface SourceConfig {
  source: 'github' | 'git' | 'local';
  repo?: string;                   // GitHub 仓库
  url?: string;                    // Git URL
}
```

### 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 市场标识符，kebab-case |
| `owner` | object | 是 | 维护者信息 |
| `plugins` | array | 是 | 插件列表 |
| `plugins[].name` | string | 是 | 插件名称 |
| `plugins[].source` | string/object | 是 | 插件来源 |
| `plugins[].strict` | boolean | 否 | 是否要求 plugin.json，默认 true |

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

### 示例

```json
{
  "name": "my-market",
  "version": "1.0.0",
  "owner": {
    "name": "Market Team",
    "email": "admin@example.com"
  },
  "plugins": [
    {
      "name": "plugin-a",
      "source": "./plugins/plugin-a",
      "description": "Plugin A",
      "version": "1.0.0",
      "strict": true
    },
    {
      "name": "plugin-b",
      "source": {
        "source": "github",
        "repo": "user/plugin-b"
      }
    }
  ]
}
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Invalid JSON` | JSON 格式错误 | 检查语法 |
| `Missing name` | 缺少 name 字段 | 添加 name |
| `Invalid name` | 名称格式错误 | 使用 kebab-case |
| `File not found` | 文件不存在 | 检查路径 |

### 验证

```bash
# 验证 plugin.json
cat .claude-plugin/plugin.json | jq .

# 验证 marketplace.json
cat .claude-plugin/marketplace.json | jq .

# 检查文件
ls .claude-plugin/plugin.json
```

## 参考资源

- [官方插件参考](https://code.claude.com/docs/en/plugins-reference.md)
- [项目 CLAUDE.md](../CLAUDE.md)
