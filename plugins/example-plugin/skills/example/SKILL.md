---
name: example-skill
description: 示例技能 - 演示如何创建和使用 Claude Code 插件中的技能。当用户需要了解插件功能、使用示例或最佳实践时自动激活。
auto-activate: always:true
allowed-tools: Read, Grep, Bash
---

# Example Plugin Skill

这是一个示例技能，演示如何创建和使用 Claude Code 插件中的技能。

## 使用场景

当用户以下情况时自动激活：
- 询问插件功能
- 需要使用示例
- 了解最佳实践
- 遇到使用问题

## 功能说明

### 命令

插件提供以下命令：
- `/hello` - 显示欢迎信息
- `/status` - 显示插件状态

### 代理

插件包含以下子代理：
- `helper` - 提供通用帮助和指导

## 使用示例

### 基本使用

```bash
# 显示欢迎信息
/hello

# 查看插件状态
/status

# 查看详细状态
/status verbose
```

### 高级使用

```bash
# 获取帮助
/helper 如何使用这个插件？

# 代码解释
/helper 解释这段代码的作用
```

## 最佳实践

1. **命名规范**
   - 插件名称：kebab-case（如 `my-plugin`）
   - 技能名称：小写、数字、连字符（如 `code-reviewer`）
   - 代理名称：小写和连字符（如 `helper`）

2. **文件格式**
   - SKILL.md 必须大写
   - 使用 frontmatter 配置
   - 提供清晰的描述

3. **文档完整**
   - 说明使用场景
   - 提供使用示例
   - 包含最佳实践

## 开发指导

### 创建新命令

1. 在 `commands/` 目录创建 `.md` 文件
2. 添加 frontmatter（description、allowed-tools）
3. 编写命令说明和使用示例

### 创建新代理

1. 在 `agents/` 目录创建 `.md` 文件
2. 添加 frontmatter（name、description、tools）
3. 编写代理职责和工作方式

### 创建新技能

1. 在 `skills/` 创建目录
2. 创建 `SKILL.md`（大写）
3. 添加 frontmatter（name、description、auto-activate）
4. 编写使用场景和指导

## 常见问题

**Q: 如何安装插件？**
A: 使用 `/plugin install ./plugin-path`

**Q: 如何测试插件？**
A: 使用 `/plugin-test ./plugin-path`

**Q: 如何验证插件？**
A: 使用 `/plugin-validate ./plugin-path`

## 参考资源

- [plugin.json](../.claude-plugin/plugin.json)
- [项目 README](../../../README.md)
- [官方文档](https://code.claude.com/docs/en/plugins.md)
