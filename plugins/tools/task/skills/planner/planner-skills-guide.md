# Planner Skills 选择指南

## 通用 Skills

| 技术栈 | Skills | 适用场景 |
|--------|--------|---------|
| Python | `python:core` / `python:web` / `python:testing` | 功能开发/Web应用/测试 |
| Go | `golang:core` / `golang:testing` | 系统编程/测试 |
| TypeScript | `typescript:core` / `typescript:react` | 类型安全/React开发 |
| JavaScript | `javascript:core` / `javascript:vue` | 脚本/Vue开发 |
| 专用 | `documentation` / `code-review` / `requirements` | 文档/审查/需求 |

## 选择原则

- **按技术栈**：Python→`python:*`，Go→`golang:*`，TS→`typescript:*`，JS→`javascript:*`
- **按任务**：核心开发→`*:core`，Web→`*:web`，测试→`*:testing`，文档→`documentation`
- **组合使用**：同一任务可指定多个skills，如`["python:core", "python:testing"]`

## 常见模式

| 模式 | 任务组合 |
|------|---------|
| 全栈 | 后端`python:web` + 前端`typescript:react` + 集成测试`python:testing` |
| TDD | 测试`*:testing` → 实现`*:core`(依赖T1) → 审查`code-review`(依赖T2) |
| 文档驱动 | 需求`requirements` → 实现`*:core`(依赖T1) → 文档`documentation`(依赖T2) |

## 自定义 Skills

命名：`技术栈:领域（中文说明）`，如`rust:core（核心功能）`
