---
name: skills
description: Skills 使用指南 - 当需要了解如何创建、管理或使用 Claude Code Skills 时自动激活。覆盖 Skills 的定义、目录结构、YAML frontmatter 和渐进披露模式。
---

# Skills 使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是 Skill** | Skills 的定义和价值 | [definition.md](definition.md) |
| **目录结构** | 标准 Skill 目录结构 | [structure.md](structure.md) |
| **Frontmatter** | YAML 前置元数据规范 | [frontmatter.md](frontmatter.md) |
| **渐进披露** | 多文件分层加载模式 | [progressive-disclosure.md](progressive-disclosure.md) |

## 什么是 Skill

Skill 是**扩展 Claude Code 功能的模块化能力**，以目录形式存在，包含：

- **SKILL.md** - 必需入口文件（YAML frontmatter + 指令）
- **支持文件** - 可选的参考文档、脚本、模板等

### 主要优势

| 优势 | 说明 |
|------|------|
| **专业化 Claude** | 为特定领域定制能力 |
| **减少重复** | 创建一次，自动使用 |
| **组合能力** | Skills 可组合构建复杂工作流 |

### 三种内容级别

| 级别 | 加载时机 | 内容 |
|------|----------|------|
| **元数据** | 始终加载 | YAML frontmatter（name、description） |
| **指令** | 触发时加载 | SKILL.md 主体内容 |
| **资源** | 按需加载 | 捆绑文件（脚本、参考等） |

## 标准结构

```
skill-name/
├── SKILL.md                   # 入口文件（必需）
├── topic.md                 # 支持文件（可选）
└── subdir/
    └── detail.md            # 子目录文件（可选）
```

## 前置元数据（YAML Frontmatter）

```yaml
---
name: skill-name              # Skill 标识（小写+连字符）
description: 简短描述          # 1-2句话说明用途
# 可选字段
argument-hint: [arg]          # 参数提示
disable-model-invocation: true # 仅手动调用
user-invocable: false        # 仅 Claude 调用
allowed-tools: Read, Grep     # 允许的工具
context: fork                # 分叉上下文
agent: Explore               # 子代理类型
hooks: {...}                 # 限定钩子
---
```

## 渐进披露模式

Skills 支持**渐进披露（Progressive Disclosure）**：

1. **SKILL.md** - 提供概览和导航
2. **子文档** - 提供详细指南
3. **路径变量** - 所有路径使用 `${CLAUDE_PLUGIN_ROOT}` 变量

## 相关技能

- [plugin](../plugin/SKILL.md) - 插件使用
- [commands](../commands/SKILL.md) - 命令使用
- [agents](../agents/SKILL.md) - 代理使用
- [hooks](../hooks/SKILL.md) - 钩子使用
