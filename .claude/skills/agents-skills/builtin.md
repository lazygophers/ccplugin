# 内置 Subagents

Claude Code 包括内置 subagents，Claude 在适当时会自动使用。

## 内置 subagents 概览

| 代理 | 模型 | 目的 | 何时使用 |
|------|------|------|----------|
| **Explore** | Haiku | 只读代码探索 | 搜索、分析代码库 |
| **Plan** | 继承自主对话 | 规划研究 | Plan mode 期间 |
| **General-purpose** | 继承自主对话 | 复杂多步骤任务 | 需要探索和修改时 |

## Explore

一个快速的、只读的代理，针对搜索和分析代码库进行了优化。

### 特点

- **模型**：Haiku（快速、低延迟）
- **工具**：只读工具（拒绝 Write 和 Edit）
- **目的**：文件发现、代码搜索、代码库探索

### 使用场景

```bash
@explore 分析项目结构
@explore 查找认证相关代码
@explore --quick 查找登录函数
@explore --very-thorough 分析整体架构
```

### 彻底程度级别

| 级别 | 说明 |
|------|------|
| `--quick` | 有针对性的查找 |
| `--medium` | 平衡的探索 |
| `--very-thorough` | 全面分析 |

## Plan

一个研究代理，在 plan mode 期间使用，以在呈现计划之前收集上下文。

### 特点

- **模型**：继承自主对话
- **工具**：只读工具
- **目的**：用于规划的代码库研究

### 使用场景

当处于 plan mode 且 Claude 需要理解代码库时自动调用。

## General-purpose

一个能够处理复杂、多步骤任务的代理，这些任务需要探索和操作。

### 特点

- **模型**：继承自主对话
- **工具**：所有工具
- **目的**：复杂研究、多步骤操作、代码修改

### 使用场景

当任务需要：
- 探索和修改
- 复杂推理来解释结果
- 多个相关步骤

## 其他内置代理

| 代理 | 模型 | 何时使用 |
|------|------|----------|
| Bash | 继承 | 在单独上下文中运行终端命令 |
| statusline-setup | Sonnet | 配置状态行 |
| Claude Code Guide | Haiku | 回答关于 Claude Code 功能的问题 |

## 自定义代理

除了内置 subagents，可以创建自定义 subagents：

- 自定义系统提示
- 特定的工具访问权限
- 独立的权限模式
- 自定义 hooks 和 skills

参考 [frontmatter.md](frontmatter.md) 了解完整配置选项。
