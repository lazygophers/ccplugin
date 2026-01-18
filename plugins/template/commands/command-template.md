---
description: 命令描述 - 简洁说明这个命令做什么
argument-hint: [arg1] [arg2]
allowed-tools: Read, Write, Bash, Grep
model: sonnet
---

# command-name

## 命令描述

简洁说明命令的用途和功能。

## 工作流描述

清晰描述命令执行的整个工作流程：

1. **第一步**：描述第一步操作的目的和内容
2. **第二步**：描述第二步操作的目的和内容
3. **第三步**：描述第三步操作的目的和内容
4. **完成**：描述最终的结果或输出

## 命令执行方式

### 使用方法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin command-name [arg1] [arg2]
```

### 执行时机

- 何时应该执行此命令
- 适用的场景或条件

### 执行参数

- `arg1`: 参数 1 的说明和类型
- `arg2`: 参数 2 的说明和类型

### 命令说明

- 命令行为说明
- 返回值说明
- 可能的输出形式

## 相关Skills（可选）

如果此命令依赖某个 Skill，通过以下方式引用：

- 参考：`@${CLAUDE_PLUGIN_ROOT}/skills/skill-name/SKILL.md`

## 依赖脚本（可选）

如果需要执行外部脚本，使用以下方式：

```bash
uvx --from git+https://github.com/owner/repo run script-name [args]
```

## 示例

### 基本用法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin command-name
```

### 带参数的用法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin command-name value1 value2
```

### 实际场景示例

描述真实使用场景和预期输出。

## 检查清单

在执行命令前，确保满足以下条件：

- [ ] 前置条件 1 已满足
- [ ] 前置条件 2 已满足
- [ ] 相关文件已准备好
- [ ] 必要的参数已获取

## 注意事项

- **注意事项 1**：详细说明
- **注意事项 2**：详细说明
- **常见问题**：列出可能的问题和解决方案

## 其他信息

### 性能考虑

- 命令的性能特征
- 大规模数据处理的注意事项

### 兼容性

- 适用的平台和版本
- 已知的兼容性问题

### 扩展和自定义

- 如何扩展此命令
- 可能的定制选项
