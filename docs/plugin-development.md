# 插件开发指南

完整的 Claude Code 插件开发教程，从创建到发布。

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
├── README.md               # 推荐：插件文档
├── CHANGELOG.md            # 推荐：版本历史
└── LICENSE                 # 推荐：许可证
```

### 重要规则

**必须遵守**：
- `commands/`、`agents/`、`skills/` 必须在插件根目录
- 不能放在 `.claude-plugin/` 目录内
- `SKILL.md` 文件名必须大写

## 核心组件

### plugin.json

插件清单文件，包含插件元数据和配置。

```json
{
  "name": "my-plugin",           // 必需：kebab-case
  "version": "1.0.0",              // 推荐：语义化版本
  "description": "插件描述",        // 必需：清晰说明
  "author": {                      // 推荐：作者信息
    "name": "作者名",
    "email": "email@example.com",
    "url": "https://github.com/author"
  },
  "keywords": ["tag1", "tag2"],    // 推荐：便于发现
  "commands": "./commands/",       // 可选：命令路径
  "agents": "./agents/",           // 可选：代理路径
  "skills": "./skills/"            // 可选：技能路径
}
```

### Commands（命令）

自定义斜杠命令，扩展 Claude Code 功能。

**格式**：
```markdown
---
description: 命令描述
argument-hint: [args]       # 可选
allowed-tools: Bash(*)      # 可选
model: sonnet               # 可选
---
# 命令名称

详细指令。
```

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

## 示例

格式化单个文件：
```bash
/format src/main.js
```

格式化整个项目：
```bash
/format
```
```

### Agents（代理）

专用子代理，处理特定任务。

**格式**：
```markdown
---
name: agent-name
description: 代理描述
tools: Read, Write, Bash     # 可选
model: sonnet                # 可选
permissionMode: default      # 可选
skills: skill1, skill2       # 可选
---
代理系统提示词。
```

**示例**：
```markdown
---
name: code-reviewer
description: 代码审查专家，专注于代码质量、安全性和性能
tools: Read, Grep, Bash
skills: security-checklist, performance-optimization
---
# Code Reviewer Agent

你是一个专业的代码审查专家...

## 审查重点
- 代码质量
- 安全漏洞
- 性能问题
- 最佳实践
```

### Skills（技能）

Agent Skills，提供特定领域的知识和指导。

**格式**：
```yaml
---
name: skill-name-skills
description: 技能描述
auto-activate: always:true  # 可选
allowed-tools: Read, Grep   # 可选
model: sonnet               # 可选
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
```

### Hooks（钩子）

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
- `SessionStart` / `SessionEnd`
- `PreToolUse` / `PostToolUse`
- `SubagentStart` / `SubagentStop`
- `PermissionRequest`
- `UserPromptSubmit`

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
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
          }
        ]
      }
    ]
  }
}
```

## 开发流程

### 1. 规划设计

- 确定插件功能
- 设计目录结构
- 规划组件实现

### 2. 创建插件

```bash
# 使用模板
cp -r plugins/template my-plugin

# 或使用命令
/plugin-create my-plugin
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

### 4. 本地测试

```bash
# 验证插件
/plugin-validate ./my-plugin

# 安装插件
/plugin install ./my-plugin

# 测试功能
/my-command
```

## 测试验证

### 自动验证

```bash
# 验证格式
cat .claude-plugin/plugin.json | jq .

# 检查结构
ls -d .claude-plugin commands agents skills

# 验证命名
cat .claude-plugin/plugin.json | jq '.name' | grep -E '^[a-z0-9-]+$'
```

### 手动测试

1. **命令测试**
   - 执行所有命令
   - 验证参数处理
   - 检查输出格式

2. **技能测试**
   - 触发技能条件
   - 验证自动激活
   - 检查指导质量

3. **代理测试**
   - 调用代理
   - 验证工具使用
   - 检查执行结果

### 测试清单

- [ ] plugin.json 格式正确
- [ ] 目录结构符合规范
- [ ] 所有命令可执行
- [ ] 所有技能可激活
- [ ] 所有代理可调用
- [ ] 命名规范符合
- [ ] 文档完整

## 发布流程

### 1. 发布前检查

- [ ] 代码审查通过
- [ ] 所有测试通过
- [ ] 文档完整更新
- [ ] 版本号正确更新
- [ ] CHANGELOG.md 更新

### 2. 更新 marketplace.json

在市场仓库的 `marketplace.json` 中添加插件：

```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "插件描述",
      "version": "1.0.0",
      "author": {"name": "作者"},
      "keywords": ["tag1", "tag2"]
    }
  ]
}
```

### 3. 提交更改

```bash
# 添加所有更改
git-skills add .

# 提交
git-skills commit -m "feat(plugin): 添加 my-plugin 插件 v1.0.0"

# 推送
git-skills push origin branch-name
```

### 4. 创建 Pull Request

**标题**：
```
feat(plugin): 添加 my-plugin 插件
```

**描述**：
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

## 最佳实践

### 命名规范

- **插件名称**：`my-awesome-plugin`（kebab-case）
- **技能名称**：`code-reviewer`（小写、连字符）
- **代理名称**：`security-auditor`（小写、连字符）
- **命令名称**：`format-code`（小写、连字符）

### 文档规范

- 每个组件都要有清晰的 description
- 提供使用示例
- 说明注意事项
- 参考相关资源

### 版本管理

- 使用语义化版本：`MAJOR.MINOR.PATCH`
- MAJOR：破坏性变更
- MINOR：新功能
- PATCH：Bug 修复

### 质量保证

- 充分测试
- 代码审查
- 文档完整
- 遵循规范

## 参考资源

- [plugin-development skill](../.claude/skills/plugin-development/SKILL.md)
- [官方插件文档](https://code.claude.com/docs/en/plugins.md)
- [插件市场规范](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [项目 CLAUDE.md](../CLAUDE.md)
