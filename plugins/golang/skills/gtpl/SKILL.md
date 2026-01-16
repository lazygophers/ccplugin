---
name: gtpl
description: Go 模板(Golang Template)开发规范 - 提供 text/template 和 html/template 最佳实践指导，包括安全性、性能优化和常见错误模式
---

# Go 模板(Golang Template)开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、优先级速览 | 快速入门 |
| [template-design-security.md](template-design-security.md) | 模板选择、结构设计、组织方案、安全防护 | 模板设计和安全 |
| [functions-performance-patterns.md](functions-performance-patterns.md) | 自定义函数、性能优化、常见错误模式 | 函数开发和优化 |

## 核心原则

Go 的模板库（`text/template` 和 `html/template`）提供了强大的文本生成能力。本规范定义了高质量、安全、高效的 Go 模板开发标准。

### ✅ 必须遵守

1. **优先 html/template** - 需要生成 HTML 时必须使用 `html/template` 而非 `text/template`
2. **自动转义** - 利用 `html/template` 的自动转义防止 XSS 攻击
3. **模板复用** - 使用 `ParseFiles` 或 `ParseGlob` 批量加载模板
4. **预编译** - 启动时预编译所有模板，避免运行时错误
5. **错误处理** - 渲染失败时明确处理，不应该忽略错误
6. **数据验证** - 在渲染前验证数据完整性
7. **缓存策略** - 对频繁使用的模板使用缓存

### ❌ 禁止行为

- 使用 `text/template` 生成 HTML（导致 XSS 漏洞）
- 动态构建模板字符串后解析
- 在模板中进行复杂业务逻辑
- 忽略模板渲染错误
- 直接使用用户输入到模板（未经验证）
- 模板中调用不安全函数
- 频繁编译同一模板

## 扩展文档

参见 [template-design-security.md](template-design-security.md) 了解模板选择指南、结构设计和安全规范。

参见 [functions-performance-patterns.md](functions-performance-patterns.md) 了解自定义函数、性能优化、常见错误模式和最佳实践检查清单。

---

**规范版本**：1.0  
**最后更新**：2026-01-11
