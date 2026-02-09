---
name: plugin-agent-development
description: 插件 AGENT.md 开发指南 - 当用户需要为插件的 agents 编写系统提示注入文档时使用。覆盖 AGENT.md 格式、内容结构和最佳实践。
context: fork
agent: agent
---

# 插件 AGENT.md 开发指南

## AGENT.md 作用

`AGENT.md` 为插件的 agents 提供系统提示注入文档，用于：
- 定义 agent 行为规范
- 提供上下文和指导
- 注入专业知识

## 文件位置

```
agents/
├── my-agent.md              # agent 文件
└── AGENT.md                 # agent 文档（可选，与 agents/ 同级）
```

## AGENT.md 格式

```markdown
# Agent 系统提示注入

## 插件信息

- **插件名称**: 我的插件
- **版本**: 0.0.1

## Agent 角色

此 agent 专注于[具体领域]开发。

## 注入时机

当检测到以下关键词时注入：
- `keyword1`
- `keyword2`

## 注入内容

### 编码规范

```language
// 代码规范说明
```

### 最佳实践

1. 实践一
2. 实践二

### 常用命令

```bash
# 命令示例
command --option value
```
```

## 内容结构

| 区块 | 说明 |
|------|------|
| `#` 标题 | Agent 名称 |
| `## 插件信息` | 插件元数据 |
| `## Agent 角色` | Agent 职责定义 |
| `## 注入时机` | 触发条件 |
| `## 注入内容` | 实际注入的提示 |

## 注入时机类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 关键词匹配 | 检测特定词 | `keyword1`, `keyword2` |
| 文件类型 | 检测文件扩展名 | `.py`, `.go` |
| 目录路径 | 检测工作目录 | `src/`, `lib/` |

## 示例

```markdown
# Golang Agent 系统提示注入

## 插件信息

- **插件名称**: golang
- **版本**: 0.0.1

## Agent 角色

此 agent 专注于 Go 语言开发，提供最佳实践和性能优化建议。

## 注入时机

当检测到以下关键词时注入：
- `golang`
- `go语言`
- `gin`
- `gorm`

## 注入内容

### 编码规范

```go
// 使用 err 命名错误
if err != nil {
    return err
}

// 上下文放在第一个参数
func handler(ctx context.Context, req Request) error
```

### 性能优化

1. 使用 sync.Pool 复用对象
2. 避免在热路径中分配内存
3. 使用字符缓冲区拼接字符串
```

## 相关技能

- [plugin-development](plugin-development/SKILL.md) - 插件开发
- [plugin-command-development](plugin-command-development/SKILL.md) - 插件命令开发
