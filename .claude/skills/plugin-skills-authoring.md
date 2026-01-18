---
name: plugin-skills-authoring
description: ccplugin 项目中插件 skills 编写规范 - 定义插件 skills 的多文件结构、渐进式披露模式、YAML frontmatter 要求和最佳实践
---

# ccplugin 插件 Skills 编写规范

本规范定义了 ccplugin 项目中所有插件的 skills 编写标准，遵循 Anthropic 官方技能创作最佳实践。

## 核心原则

### 1. 渐进式披露模式

Skills 分为三个层级：

| 层级 | 文件 | 用途 | 大小 |
|------|------|------|------|
| **导航** | SKILL.md | 概述、快速开始、导航链接 | 300-400 行 |
| **详情** | reference.md | 完整配置、规范、参考资料 | 按需加载 |
| **示例** | examples.md | 使用示例、最佳实践、常见问题 | 按需加载 |

**原则**：Claude 按需加载详细文件，SKILL.md 保持简洁是关键。

### 2. 假设 Claude 已经聪慧

- 不要过度解释基础概念
- 删除不必要的背景介绍
- 专注于项目特定的内容
- 每个令牌都必须有价值

### 3. 一级深的引用

**✅ 推荐**：所有参考文件直接从 SKILL.md 链接
```markdown
[reference.md](reference.md)
[examples.md](examples.md)
```

**❌ 避免**：深层嵌套引用
```markdown
file-a → file-b → file-c  # 会导致部分读取
```

## 文件结构

### 目录布局

```
plugins/{category}/{plugin-name}/skills/
├── SKILL.md          # 导航和概述（必须）
├── reference.md      # 详细规范（推荐）
├── examples.md       # 使用示例（推荐）
└── [domain-file].md  # 领域特定文件（可选）
```

例如：
```
plugins/code/flutter/skills/flutter/
├── SKILL.md
├── design-systems.md
├── state-management.md
├── performance.md
├── testing.md
└── ui-development.md
```

### SKILL.md 结构

每个 SKILL.md 必须包含：

```markdown
---
name: plugin-name
description: 简洁的功能描述（最多 1024 字符，第三人称）
---

# 插件标题

## 核心特性

核心功能的简要说明（100-150 行）

## 快速开始

最简单的使用示例

## 详细指南

- 完整的配置规范 → [reference.md](reference.md)
- 使用示例和最佳实践 → [examples.md](examples.md)

## 关键要点

关键的 DO & DON'T
```

### YAML Frontmatter 要求

**必须字段**：
- `name`：插件英文名称（小写，最多 64 字符，仅字母/数字/连字符）
- `description`：功能描述（最多 1024 字符，第三人称）

**示例**：
```yaml
---
name: react-development
description: React 18+ 开发插件 - 提供现代 React 开发规范和最佳实践，包括 Hooks、状态管理和性能优化
---
```

## 编写指南

### SKILL.md（300-400 行）

**内容安排**：
1. Frontmatter（必须）
2. 标题（#）
3. 核心特性（20-30 行）
4. 快速开始（50-100 行，代码示例）
5. 导航链接（5-10 行）
6. 关键要点（50-100 行，DO & DON'T）

**关键原则**：
- 保持简洁，删除重复内容
- 使用表格和列表易于扫描
- 核心功能在此呈现
- 详情用链接指向其他文件

### reference.md（不受行数限制）

**内容组织**：
1. API/配置参考
2. 颜色系统（对于设计插件）
3. 完整的配置选项
4. 浏览器支持/兼容性
5. 常见问题

**可选子部分**：
按领域组织内容以避免加载无关上下文

```
reference/
├── configuration.md  （配置选项）
├── color-system.md   （设计系统）
└── api-reference.md  （API 文档）
```

### examples.md（不受行数限制）

**内容组织**：
1. 基础实现示例
2. 框架特定示例（React, Vue, Next.js 等）
3. 最佳实践
4. 常见问题及解决方案
5. 浏览器测试方法

## 命名规范

### 文件名
- 使用 kebab-case：`design-system.md`, `color-reference.md`
- 清晰描述内容：避免 `doc1.md`, `info.md`
- 一致的扩展名：使用 `.md`

### 内容标题
- 使用 Markdown 标题层级（# ## ### 等）
- 保持层级清晰，避免深层嵌套（最多 4 层）

## 链接规范

**正斜杠分隔符**（必须）：
```markdown
✅ [reference.md](reference.md)
✅ [examples.md](examples.md)
✅ [configuration.md](../reference/configuration.md)

❌ [reference.md](reference\reference.md)  # Windows 风格路径
```

**相对路径**：
- 同级文件：`[file.md](file.md)`
- 子目录：`[file.md](subdir/file.md)`
- 父目录：`[file.md](../file.md)`

## 内容质量标准

### ✅ DO

- 使用第三人称编写描述
- 在代码块上方说明编程语言
- 为复杂概念提供代码示例
- 定期更新，保持内容最新
- 测试所有代码示例
- 为改动添加注释说明原因

### ❌ DON'T

- 硬编码颜色值（使用 CSS 变量）
- 过度嵌套的 markdown 标题（>4 层）
- 假设用户知道项目特定术语
- 为假设的未来需求添加功能
- 多个文件重复相同内容
- 时间敏感的信息

## Commands 命名规范

**严格要求**：所有插件的 commands 必须遵循以下格式：

### 命名格式

```yaml
# 文件名：dev.md (简短的命令名)
# COMMAND.md frontmatter 中的 name：plugin-name:command-name

# 示例
plugins/code/flutter/.claude/commands/dev.md
---
name: flutter:dev
description: Flutter 开发工作流启动命令
---

plugins/code/python/.claude/commands/lint.md
---
name: python:lint
description: Python 代码检查和格式化
---
```

### 规范说明

| 项目 | 格式 | 说明 |
|------|------|------|
| **文件名** | `{command-name}.md` | 简短、清晰、小写 |
| **name 字段** | `{plugin-name}:{command-name}` | 必须包含插件前缀，使用冒号分隔 |
| **description** | 清晰的命令说明 | 第三人称，简洁描述 |

### 不同类型插件的前缀

- **Code plugins**: `flutter:`, `python:`, `golang:`, `react:`, `typescript:`, `javascript:`, `vue:`, `nextjs:`, `antd:`, `semantic:`, `git:`, `version:`
- **Style plugins**: `glassmorphism:`, `neumorphism:`, `gradient:`, `neon:`, `retro:`, `brutalism:`, `minimal:`, `dark:`, `pastel:`, `vibrant:`, `highcontrast:`, `luxe:`
- **Utility plugins**: `task:`, `notify:`

### 检查清单

- [ ] Commands frontmatter 的 `name` 字段包含插件前缀
- [ ] 使用冒号（`:`）分隔插件名和命令名
- [ ] 文件名不含前缀（只是命令名）
- [ ] 所有插件的所有 commands 都遵循此规范

## 插件特定规范

### Code 插件

Code 类插件（golang, python, react 等）应包含：

- **设计原则**：该语言/框架的核心理念
- **最佳实践**：该语言/框架的推荐做法
- **工具链**：推荐的开发工具和配置
- **性能优化**：该语言/框架的性能考虑
- **测试策略**：推荐的测试方法和工具

### Style 插件

Style 类插件（design-system, ui-style 等）应包含：

- **核心特性**：视觉特征、颜色系统、排版等
- **配置规范**：CSS 变量、主题配置、响应式设计
- **实现示例**：HTML、CSS、框架特定的实现
- **最佳实践**：DO & DON'T、可访问性、浏览器支持

### Utility 插件

Utility 类插件（task, notify, version 等）应包含：

- **功能说明**：插件的具体功能
- **使用流程**：如何使用该插件
- **配置选项**：所有可用的配置项
- **常见问题**：Q&A 部分

## 验证检查清单

提交前确保符合以下条件：

### 结构验证
- [ ] 存在 SKILL.md 和完整的 Frontmatter
- [ ] 存在 reference.md 和 examples.md
- [ ] 所有文件使用 .md 扩展名
- [ ] 所有链接使用正斜杠（/）

### 内容验证
- [ ] SKILL.md 在 300-400 行以内
- [ ] description 字段非空，最多 1024 字符
- [ ] 使用第三人称编写描述
- [ ] 代码示例都经过测试
- [ ] 没有硬编码的颜色值或路径

### 质量验证
- [ ] 内容清晰简洁，无重复
- [ ] 所有链接有效
- [ ] 没有时间敏感的信息
- [ ] 术语一致性
- [ ] Markdown 格式正确

## 更新流程

当需要更新 skills 时：

1. **编辑相应文件**（SKILL.md, reference.md, 或 examples.md）
2. **测试所有代码示例**
3. **验证所有链接有效**
4. **更新变更时间**（如果有）
5. **执行验证检查清单**
6. **提交 git 更改**

## 示例参考

### 完整的插件 skill 示例

参考以下已实施的插件：
- **code/flutter/skills/flutter/** - 完整的多文件结构示例
- **code/react/skills/react/** - 框架类插件示例
- **style/style-dark/skills/** - 设计系统插件示例

## 常见问题

**Q: 如果 SKILL.md 超过 400 行怎么办？**
A: 将内容拆分到专门的文件（design-system.md, performance.md 等）并从 SKILL.md 链接

**Q: 可以在参考文件中链接到其他参考文件吗？**
A: 可以，但要避免深层嵌套。如果经常需要深层链接，考虑重新组织内容

**Q: 代码示例中能包含多个编程语言吗？**
A: 可以，使用带语言标识的代码块分隔（```python, ```javascript 等）

**Q: 如何处理已弃用的功能？**
A: 在"旧模式"部分用 `<details>` 标签包裹，不要从主内容中删除

## 相关文档

- Anthropic 官方技能创作指南：https://docs.anthropic.com/agents-and-tools/agent-skills/best-practices
- ccplugin CLAUDE.md：项目架构和开发指南
- ccplugin README：插件使用说明
