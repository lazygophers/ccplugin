---
name: commands
description: 命令使用指南 - 当用户需要创建、使用或管理 Claude Code 命令时自动激活。覆盖命令的定义、YAML frontmatter、参数处理和交互模式。
context: fork
agent: command
---

# 命令使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是命令** | 命令的定义和用途 | [definition.md](definition.md) |
| **Frontmatter** | YAML 前置元数据 | [frontmatter.md](frontmatter.md) |
| **参数处理** | 动态参数和选项 | [arguments.md](arguments.md) |
| **交互模式** | 用户交互方式 | [interaction.md](interaction.md) |
| **示例集合** | 完整示例参考 | [examples.md](examples.md) |

## 什么是命令

命令是**以 `/` 开头的可执行功能入口**，用于触发特定操作：

```
/task add "Complete feature X"
/semantic search "authentication logic"
/git commit "feat: new feature"
```

### 命令特点

| 特性 | 说明 |
|------|------|
| **触发方式** | 以 `/` 开头 |
| **参数支持** | 位置参数和选项 |
| **交互能力** | 可使用 `AskUserQuestion` |
| **执行方式** | 通过 bash 读取命令文件 |

## 命令结构

```
commands/
└── command-name.md    # 命令文件

# 文件内容
---
name: command-name
description: 简短描述
arguments: [...]
options: [...]
examples: [...]
---

# 命令标题

命令详细说明...
```

## 命令模板规范

### 标准模板结构

```
## 命令描述
简要说明命令的功能（1-2句话）

## 工作流描述
命令的执行流程步骤

## 命令执行方式
### 使用方法
### 执行时机
### 执行参数

## 示例
### 基本用法
### 进阶用法

## 检查清单
- [ ] 检查项1
- [ ] 检查项2

## 注意事项
### 安全相关
### 常见问题

## 其他信息
### 类型说明
### 最佳实践
### 失败处理
```

### Frontmatter 完整格式

```yaml
---
name: command-name
description: 简短描述（1-2句话）

# 可选字段
arguments:
  - name: arg1
    description: 参数描述
    required: true
    enum: [val1, val2]

options:
  - name: verbose
    short: -v
    description: 详细输出
    is_flag: true

examples:
  - "/command arg1"
  - "/command arg1 --verbose"
---

# 命令标题

命令详细说明...
```

## 使用命令

```bash
# 基本使用
/command-name

# 带参数
/command-name arg1

# 带选项
/command-name arg1 --verbose

# 带参数和选项
/task add "Task description" --priority high
```

## 相关技能

- [plugin](../plugin-skills/SKILL.md) - 插件使用
- [skills](../skills/SKILL.md) - Skills 使用
- [agents](../agents/SKILL.md) - Agents 使用
- [hooks](../hooks/SKILL.md) - Hooks 使用