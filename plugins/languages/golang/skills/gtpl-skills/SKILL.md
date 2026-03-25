---
name: gtpl-skills
description: Go 模板(Golang Template)开发规范 - text/template 和 html/template 最佳实践，包括安全性、性能优化（预编译缓存）、Go 1.22+ embed 集成、常见错误模式。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 模板(Golang Template)开发规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）

## 相关 Skills

| 场景     | Skill                    | 说明                         |
| -------- | ------------------------ | ---------------------------- |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定           |
| 错误处理 | Skills(golang:error)     | 模板渲染错误处理             |
| 工具库   | Skills(golang:libs)      | stringx 用于模板函数         |

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、优先级速览 | 快速入门 |
| [template-design-security.md](template-design-security.md) | 模板选择、结构设计、安全防护 | 模板设计和安全 |
| [functions-performance-patterns.md](functions-performance-patterns.md) | 自定义函数、性能优化、常见错误 | 函数开发和优化 |

## 核心原则

### 必须遵守

1. **优先 html/template** - 生成 HTML 时必须使用 `html/template`
2. **自动转义** - 利用 `html/template` 防止 XSS
3. **预编译** - 启动时预编译所有模板，使用 `sync.Once` 或 `init()`
4. **embed 集成** - Go 1.16+ 使用 `//go:embed` 嵌入模板文件
5. **错误处理** - 渲染失败时明确处理错误
6. **缓存策略** - 频繁使用的模板使用缓存

### 禁止行为

- 使用 `text/template` 生成 HTML
- 动态构建模板字符串后解析
- 在模板中进行复杂业务逻辑
- 忽略模板渲染错误
- 频繁重复编译同一模板

## Go 1.16+ embed 集成

```go
import "embed"

//go:embed templates/*.html
var templateFS embed.FS

var tmpl = template.Must(
    template.ParseFS(templateFS, "templates/*.html"),
)
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "text/template 更灵活" | 生成 HTML 是否用 html/template？ | 高 |
| "每次请求解析模板" | 模板是否预编译并缓存？ | 高 |
| "模板里算逻辑方便" | 复杂逻辑是否在 Go 代码中处理？ | 中 |
| "用户输入直接渲染" | 是否验证并转义了用户输入？ | 高 |
| "嵌入文件太大" | embed 是否只嵌入必要的模板？ | 低 |
| "忽略渲染错误" | 模板错误是否被正确处理？ | 高 |

## 扩展文档

参见 [template-design-security.md](template-design-security.md) 了解模板选择指南、结构设计和安全规范。

参见 [functions-performance-patterns.md](functions-performance-patterns.md) 了解自定义函数、性能优化和最佳实践检查清单。
