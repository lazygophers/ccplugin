# 插件开发指南

> Claude Code 插件开发完整教程 - 从创建到发布

## 目录

1. [快速开始](#快速开始)
2. [插件结构](#插件结构)
3. [核心组件](#核心组件)
4. [开发流程](#开发流程)
5. [测试验证](#测试验证)
6. [发布流程](#发布流程)

## 快速开始

### 使用模板创建插件

```bash
# 1. 复制模板
cp -r plugins/template my-new-plugin

# 2. 修改配置
cd my-new-plugin/.claude-plugin
vi plugin.json

# 3. 实现功能
cd ../commands  # 添加命令
cd ../agents    # 添加代理
cd ../skills    # 添加技能

# 4. 测试插件
cd ../..
/plugin install ./my-new-plugin
```

### 使用 uvx 一键安装测试

```bash
# 本地测试
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin ./my-new-plugin
```

## 插件结构

### 标准结构

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json         # 必需：插件清单
├── commands/               # 可选：自定义命令
│   └── my-command.md
├── agents/                 # 可选：子代理
│   └── my-agent.md
├── skills/                 # 可选：技能
│   └── my-skill/
│       └── SKILL.md
├── hooks/                  # 可选：钩子
│   └── hooks.json
├── scripts/                # 可选：脚本
│   ├── __init__.py
│   └── main.py
├── README.md               # 推荐：插件文档
├── CHANGELOG.md            # 推荐：版本历史
├── pyproject.toml          # Python 项目配置
└── LICENSE                 # 推荐：许可证
```

### 重要规则

**必须遵守**：

- `commands/`、`agents/`、`skills/` 必须在插件根目录
- 不能放在 `.claude-plugin/` 目录内
- `SKILL.md` 文件名必须大写
- `plugin.json` 必须包含 `name` 字段

## 核心组件

### 1. plugin.json（必需）

插件清单文件，包含插件元数据和配置。

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "插件描述",
  "author": {
    "name": "作者名",
    "email": "email@example.com",
    "url": "https://github.com/author"
  },
  "keywords": ["tag1", "tag2"],
  "commands": "./commands/",
  "agents": "./agents/",
  "skills": "./skills/"
}
```

### 2. Commands（命令）

自定义斜杠命令，扩展 Claude Code 功能。

**格式**：

```markdown
---
description: 命令描述
argument-hint: [args]
allowed-tools: Bash(*)
model: sonnet
---

# 命令名称

详细指令内容。

## 使用方法

/command-name [args]

## 示例

/command-name example-arg
```

**参数占位符**：

| 占位符 | 描述 |
|--------|------|
| `$ARGUMENTS` | 捕获所有参数 |
| `$1`, `$2`, ... | 位置参数 |

**示例**：

```markdown
---
description: 格式化代码
argument-hint: [file-path]
allowed-tools: Bash(prettier*)
---

# format

格式化指定文件或整个项目。

## 使用方法

/format [file-path]

## 执行

\`\`\`bash
if [ -n "$ARGUMENTS" ]; then
    prettier --write "$ARGUMENTS"
else
    prettier --write "**/*.{js,ts,jsx,tsx}"
fi
\`\`\`
```

### 3. Agents（代理）

专用子代理，处理特定任务。

**格式**：

```markdown
---
name: agent-name
description: 代理描述
tools: Read, Write, Bash
model: sonnet
permissionMode: default
skills: skill1, skill2
---

# Agent 名称

代理系统提示词...

## 职责

- 职责1
- 职责2
```

**字段说明**：

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 代理唯一标识符 |
| `description` | string | 是 | 代理用途描述 |
| `tools` | string | 否 | 工具列表，逗号分隔 |
| `model` | string | 否 | 模型：sonnet, haiku, opus, inherit |
| `permissionMode` | string | 否 | 权限模式：default, grant, deny |
| `skills` | string | 否 | 自动加载的技能，逗号分隔 |

**示例**：

```markdown
---
name: code-reviewer
description: 代码审查专家，专注于代码质量、安全性和性能
tools: Read, Grep, Bash
skills: security-checklist, performance-optimization
---

# Code Reviewer Agent

你是一个专业的代码审查专家。

## 审查重点

- 代码质量：可读性、可维护性、可测试性
- 安全漏洞：SQL 注入、XSS、CSRF
- 性能问题：算法复杂度、内存泄漏
- 最佳实践：设计模式、代码规范
```

### 4. Skills（技能）

Agent Skills，提供特定领域的知识和指导。

**格式**：

```yaml
---
name: skill-name-skills
description: 技能描述
auto-activate: always:true
allowed-tools: Read, Grep
model: sonnet
---

# 技能名称

## 使用场景

描述何时自动激活。

## 指导原则

提供详细指令。
```

**示例**：

```yaml
---
name: security-auditor
description: 安全审计技能。当用户提到安全检查、漏洞扫描或安全相关问题时自动激活。
auto-activate: always:true
allowed-tools: Read, Grep, Bash
---

# Security Auditor

## 使用场景

- 用户要求安全审计
- 提到漏洞或安全问题
- 需要安全最佳实践

## 审查要点

1. SQL 注入
2. XSS 攻击
3. CSRF 防护
4. 认证授权
5. 敏感数据处理
```

### 5. Hooks（钩子）

在特定事件发生时自动执行命令。

**格式**：

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolName|Pattern",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh"
          }
        ]
      }
    ]
  }
}
```

**可用事件**：

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

**Matcher 模式**：

```javascript
"Write|Edit"       // 匹配 Write 或 Edit
"Bash(*)"          // 匹配所有 Bash 工具
"Bash(git:*)"      // 匹配 git 命令
"*"                // 匹配所有工具
```

**示例**：

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

### 6. MCP Servers

Model Context Protocol 服务器，提供外部工具集成。

**配置文件** (`.mcp.json`)：

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["--from", "./scripts", "my-mcp-server"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### 7. LSP Servers

Language Server Protocol 服务器，提供代码智能支持。

**配置文件** (`.lsp.json`)：

```json
{
  "lspServers": {
    "gopls": {
      "command": "gopls",
      "args": ["serve"],
      "filePatterns": ["**/*.go"]
    }
  }
}
```

## 开发流程

### 1. 规划设计

- 确定插件功能和目标用户
- 设计目录结构
- 规划组件实现
- 确定依赖项

### 2. 创建插件

```bash
# 使用模板
cp -r plugins/template my-plugin

# 或手动创建
mkdir -p my-plugin/.claude-plugin
mkdir -p my-plugin/commands
mkdir -p my-plugin/agents
mkdir -p my-plugin/skills
mkdir -p my-plugin/scripts
```

### 3. 实现功能

**添加命令**：

```bash
cd my-plugin/commands
vi my-command.md
```

**添加代理**：

```bash
cd my-plugin/agents
vi my-agent.md
```

**添加技能**：

```bash
cd my-plugin/skills
mkdir my-skill
vi my-skill/SKILL.md
```

**添加脚本**：

```bash
cd my-plugin/scripts
vi main.py
```

### 4. 本地测试

```bash
# 验证插件结构
ls -la my-plugin/.claude-plugin/plugin.json

# 验证 JSON 格式
cat my-plugin/.claude-plugin/plugin.json | jq .

# 安装测试
/plugin install ./my-plugin

# 测试功能
/my-command
```

## 测试验证

### 自动验证

```bash
# 验证 plugin.json 格式
cat .claude-plugin/plugin.json | jq .

# 检查目录结构
ls -d .claude-plugin commands agents skills 2>/dev/null

# 验证命名规范
cat .claude-plugin/plugin.json | jq '.name' | grep -E '^[a-z0-9-]+$'
```

### 手动测试清单

**命令测试**：

- [ ] 执行所有命令
- [ ] 验证参数处理
- [ ] 检查输出格式
- [ ] 测试错误处理

**技能测试**：

- [ ] 触发技能条件
- [ ] 验证自动激活
- [ ] 检查指导质量

**代理测试**：

- [ ] 调用代理
- [ ] 验证工具使用
- [ ] 检查执行结果

**Hook 测试**：

- [ ] 触发所有 Hook 事件
- [ ] 验证脚本执行
- [ ] 检查环境变量

### 完整测试清单

- [ ] plugin.json 格式正确
- [ ] 目录结构符合规范
- [ ] 所有命令可执行
- [ ] 所有技能可激活
- [ ] 所有代理可调用
- [ ] 命名规范符合
- [ ] 文档完整
- [ ] 无占位符代码

## 发布流程

### 1. 发布前检查

- [ ] 代码审查通过
- [ ] 所有测试通过
- [ ] 文档完整更新
- [ ] 版本号正确更新
- [ ] CHANGELOG.md 更新
- [ ] README.md 更新

### 2. 更新 marketplace.json

在市场仓库的 `marketplace.json` 中添加插件：

```json
{
  "name": "ccplugin-market",
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "插件描述",
      "version": "1.0.0",
      "author": { "name": "作者" },
      "keywords": ["tag1", "tag2"]
    }
  ]
}
```

### 3. 提交更改

```bash
# 添加所有更改
git add .

# 提交
git commit -m "feat(plugin): 添加 my-plugin 插件 v1.0.0"

# 推送
git push origin branch-name
```

### 4. 创建 Pull Request

**标题**：

```
feat(plugin): 添加 my-plugin 插件
```

**描述模板**：

```markdown
## 插件名称

my-plugin

## 插件描述

简要描述插件功能。

## 更新内容

- 添加 plugin.json 配置
- 实现 commands/
- 实现 agents/
- 实现 skills/

## 测试

- [ ] 本地测试通过
- [ ] 格式验证通过
- [ ] 文档完整

## 相关 Issue

Closes #123
```

## 参考资源

### 项目文档

- [API 参考](api-reference.md) - 完整的 API 文档
- [最佳实践](best-practices.md) - 开发最佳实践
- [支持的语言](supported-languages.md) - 语言选择指南
- [编译型语言指南](compiled-languages-guide.md) - Go/Rust 开发指南

### 官方文档

- [Claude Code 插件文档](https://code.claude.com/docs/en/plugins)
- [插件市场规范](https://code.claude.com/docs/en/plugin-marketplaces)
- [插件参考](https://code.claude.com/docs/en/plugins-reference)

### 项目文件

- [CLAUDE.md](../CLAUDE.md) - 项目开发规范
- [README.md](../README.md) - 项目说明
