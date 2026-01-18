# 配置参考

以下是完整的实现指南和最佳实践：

# Skill Name

## 文件组织与路径规范

⚠️ **重要**：本技能采用多文件分层加载方式（Progressive Disclosure），所有文件路径必须使用 `${CLAUDE_PLUGIN_ROOT}` 变量。

### 目录结构

```
skill-name/
├── SKILL.md                          # 主文件（必需）- 核心指导和关键规范
├── guidelines.md                     # 详细规范和工作流指南（可选）
├── examples.md                       # 使用示例和最佳实践（可选）
└── reference.md                      # 完整参考和高级用法（可选）
```

### 路径引用规范

**所有路径都必须使用以下格式，而不是相对路径**：

- 本技能的文件：`${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/<filename>.md`
- 插件命令：`${CLAUDE_PLUGIN_ROOT}/commands/<command-name>.md`
- 插件代理：`${CLAUDE_PLUGIN_ROOT}/agents/<agent-name>.md`
- 插件根文件：`${CLAUDE_PLUGIN_ROOT}/README.md`

**❌ 禁止使用相对路径**：

```markdown
# 错误

[文档](../../plugins/skill-name/file.md)
[命令](./commands/command.md)
[代理](./../agents/agent.md)
```

**✅ 正确的路径格式**：

```markdown
# 正确

[文档](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/file.md)
[命令](${CLAUDE_PLUGIN_ROOT}/commands/command.md)
[代理](${CLAUDE_PLUGIN_ROOT}/agents/agent.md)
```

### 加载策略

- 初始加载：仅加载 SKILL.md 的描述和概要
- 需要详细规范时：链接到 `${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/guidelines.md`
- 需要代码示例时：链接到 `${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/examples.md`
- 需要完整参考时：链接到 `${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/reference.md`

### 示例引用

```markdown
详细规范见 [@guidelines](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/guidelines.md)
代码示例见 [@examples](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/examples.md)
完整参考见 [@reference](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md)
相关命令见 [@command](${CLAUDE_PLUGIN_ROOT}/commands/command-name.md)
相关代理见 [@agent](${CLAUDE_PLUGIN_ROOT}/agents/agent-name.md)
```

## 概述

简洁说明这个技能的核心目的和价值。

**适用场景**：

- 场景 1：用户在什么情况下需要这个技能
- 场景 2：用户在什么情况下需要这个技能
- 场景 3：用户在什么情况下需要这个技能

**核心能力**：

- 能力 1：清晰描述技能提供的具体能力
- 能力 2：清晰描述技能提供的具体能力
- 能力 3：清晰描述技能提供的具体能力

## 规范要求

使用这个技能时，需要遵循以下规范：

### 规范 1：[规范名称]

**要求**：[详细要求说明]

**正确做法**：

```
[示例]
```

**错误做法**：

```
[反面示例]
```

### 规范 2：[规范名称]

**要求**：[详细要求说明]

- 细节 1
- 细节 2
- 细节 3

### 规范 3：[规范名称]

**要求**：[详细要求说明]

| 项目   | 说明 | 示例 |
| ------ | ---- | ---- |
| 项目 1 | 说明 | 示例 |
| 项目 2 | 说明 | 示例 |

## 常用工作流

### 工作流 1：[工作流名称]

**触发条件**：用户[XX 操作]或需要[XX 功能]

**执行步骤**：

1. **第一步**：[具体操作说明]

   - 方法 1：[选项 A]
   - 方法 2：[选项 B]

2. **第二步**：[具体操作说明]

   - 检查[XX]
   - 验证[XX]

3. **第三步**：[具体操作说明]
   - 确认[XX]
   - 记录[XX]

**验证方法**：[如何验证工作流执行成功]

### 工作流 2：[工作流名称]

**触发条件**：用户[XX 操作]或遇到[XX 问题]

**执行步骤**：

1. **分析阶段**：[分析步骤说明]
2. **实施阶段**：[实施步骤说明]
3. **验证阶段**：[验证步骤说明]

## 使用的外部工具与命令

⚠️ **重要**：执行本技能时，**禁止使用 Claude Code 斜杠命令**（如 `/command-name`），应使用实际的命令行工具执行。

### 外部工具 1：bash 系统命令

**用途**：[什么时候执行系统命令]

**常见场景**：

- [场景 1]
- [场景 2]

**执行方式**：

```bash
# 直接在终端执行 bash 命令
[命令范例]
```

### 外部工具 2：uv 包管理器

**用途**：[什么时候使用 uv 进行 Python 开发]

**常见场景**：

- [场景 1]
- [场景 2]

**执行方式**：

```bash
# 使用 uv 运行脚本或安装包
uv run [script-name]
uv pip install [package-name]
```

### 外部工具 3：uvx 执行插件命令

**用途**：[什么时候使用 ccplugin 插件命令]

**常见场景**：

- 执行 git、task、semantic 等插件命令

**执行方式**：

```bash
# 执行插件中的命令（而非 /command-name 斜杠形式）
uvx --from git+https://github.com/lazygophers/ccplugin [command] [args]

# 示例
uvx --from git+https://github.com/lazygophers/ccplugin commit "message"
uvx --from git+https://github.com/lazygophers/ccplugin task add "任务标题"
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "查询内容"
```

### 外部工具 4：gh / glab

**用途**：[什么时候使用 GitHub/GitLab 命令行工具]

**常见场景**：

- [场景 1]
- [场景 2]

**执行方式**：

```bash
# GitHub CLI
gh pr create --title "PR 标题"
gh issue list --label bug

# GitLab CLI
glab mr create --title "MR 标题"
glab issue list --label bug
```

## 最佳实践

1. **[实践 1 名称]**

   - [具体建议 1]
   - [具体建议 2]
   - [具体建议 3]

2. **[实践 2 名称]**

   - [具体建议 1]
   - [具体建议 2]
   - [具体建议 3]

3. **[实践 3 名称]**
   - [具体建议 1]
   - [具体建议 2]

## 注意事项

**⚠️ 关键注意**：

- 注意事项 1：[详细说明]
- 注意事项 2：[详细说明]
- 注意事项 3：[详细说明]

**禁止操作**：

- ❌ 禁止 1：[为什么禁止]
- ❌ 禁止 2：[为什么禁止]

## 常见问题

**Q: 问题 1？**
A: 解答 1

**Q: 问题 2？**
A: 解答 2

**Q: 问题 3？**
A: 解答 3

## 参考资源

### 本技能的分层文档

- 📋 [详细规范](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/guidelines.md) - 完整的规范要求和工作流指南
- 💡 [代码示例](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/examples.md) - 实际使用示例和最佳实践
- 📖 [完整参考](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md) - 高级用法和完整参考

### 相关插件资源

- 📄 [相关命令文档](${CLAUDE_PLUGIN_ROOT}/commands/command-name.md)
- 👥 [相关代理文档](${CLAUDE_PLUGIN_ROOT}/agents/agent-name.md)
- 📖 [插件 README](${CLAUDE_PLUGIN_ROOT}/README.md)
- ⚙️ [插件配置](${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json)

### 官方文档

- 🔗 [Claude Code Skills 文档](https://code.claude.com/docs/zh-CN/skills)
- 📚 [Claude Code 命令文档](https://code.claude.com/docs/zh-CN/commands)
- 👤 [Claude Code 代理文档](https://code.claude.com/docs/zh-CN/agents)

## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
