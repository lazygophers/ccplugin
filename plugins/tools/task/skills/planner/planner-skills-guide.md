# Planner Skills 选择指南

## Skills 发现机制

在为任务分配 skills 前，应先获取所有可用的 skills：

### 扫描三个来源

1. **插件级 Skills**：扫描所有已安装插件的 skills 目录
   - 路径：`~/.claude/plugins/*/skills/`
   - 标注：`skill-name@plugin-name`（如 `commit@git`）

2. **User级 Skills**：扫描用户自定义 skills
   - 路径：`~/.claude/skills/`
   - 标注：`skill-name@user`

3. **项目级 Skills**：扫描当前项目的 skills
   - 路径：`.claude/skills/`
   - 标注：`skill-name`（无后缀）

### 获取方法

- 使用 `Glob` 工具扫描上述路径的 `*/SKILL.md` 文件
- 读取 SKILL.md 的 YAML frontmatter 获取元数据
- 按来源分类并构建完整清单

## 来源标注规范

所有 skill 必须标注来源，格式：`skill-name（中文说明）@source`

| 来源类型 | 标注格式 | 示例 |
|---------|---------|------|
| 插件级 | `skill-name@plugin-name` | `commit@git`、`golang:core@golang` |
| User级 | `skill-name@user` | `custom-linter@user` |
| 项目级 | `skill-name`（无后缀） | `project-validator` |

**注意**：项目级 skill 不需要 @source 后缀。

## 专用 vs 通用 Skills

### 判断标准

| 维度 | 专用 Skill | 通用 Skill |
|------|-----------|-----------|
| 技术栈 | 单一技术栈（如 python:web） | 跨技术栈（如 documentation） |
| 领域深度 | 领域专精（如 golang:testing） | 通用能力（如 code-review） |
| 适用范围 | 特定场景（如 typescript:react） | 广泛场景（如 requirements） |
| 工具依赖 | 特定工具链 | 通用工具 |

### 优先级策略

1. **优先选择专用 Skills**（技术栈明确的任务）
   - 领域最佳实践
   - 优化的工具集成
   - 精确的验证标准

2. **通用 Skills 适用场景**
   - 跨技术栈任务（如文档、审查）
   - 流程类任务（如需求分析）
   - 专用 skill 不可用时作为补充

### 选择决策流程

```
1. 识别任务技术栈（Python/Go/TypeScript/跨栈）
2. 单一技术栈 → 搜索专用 skills（如 python:web）
3. 跨技术栈 → 使用通用 skills（如 documentation）
4. 组合使用：专用 skill + 通用 skill
```

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
