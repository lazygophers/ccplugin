# Code Plugins - 语言与框架开发插件

`plugins/code/` 目录包含所有编程语言和开发框架的插件，为不同技术栈提供完整的开发规范、最佳实践和代码智能支持。

## 📚 插件概览

### 编程语言插件

| 插件 | 描述 | 特性 |
|------|------|------|
| **[python](python/)** | Python 开发规范 | PEP 8、类型提示、测试、性能优化 |
| **[golang](golang/)** | Golang 开发规范 | 包设计、错误处理、模式、性能、模板 |
| **[javascript](javascript/)** | JavaScript（ES2024-2025）规范 | 现代化标准、异步编程、Vite、Vitest、pnpm |
| **[typescript](typescript/)** | TypeScript 开发规范 | 类型安全、严格模式、Vitest、最新特性 |

### 前端框架插件

| 插件 | 描述 | 特性 |
|------|------|------|
| **[react](react/)** | React 18+ 开发规范 | Hooks、函数组件、Zustand/Redux、Next.js集成 |
| **[vue](vue/)** | Vue 3 开发规范 | Composition API、Pinia、Vite、开发工具链 |
| **[nextjs](nextjs/)** | Next.js 16+ 全栈开发 | App Router、Server Components、PPR、Route Handlers |

### UI 组件库插件

| 插件 | 描述 | 特性 |
|------|------|------|
| **[antd](antd/)** | Ant Design 5.x 企业级 UI | 设计系统、表单、表格、主题、虚拟滚动 |

### 移动开发插件

| 插件 | 描述 | 特性 |
|------|------|------|
| **[flutter](flutter/)** | Flutter 移动开发 | Material 3、Cupertino、状态管理、设计系统 |

### 开发工具插件

| 插件 | 描述 | 特性 |
|------|------|------|
| **[semantic](semantic/)** | 语义搜索插件 | 向量嵌入、自然语言查询、多语言理解 |
| **[git](git/)** | Git 版本控制 | 提交管理、Pull Request、.gitignore 管理 |
| **[version](version/)** | 版本号管理 | SemVer、自动更新、Hook 集成 |
| **[template](template/)** | 插件开发模板 | 插件结构、配置示例、best practices |

## 🚀 快速开始

### 按语言选择

- **Python 项目**：查看 [python/README.md](python/README.md)
- **Go 项目**：查看 [golang/README.md](golang/README.md)
- **JavaScript/Node.js 项目**：查看 [javascript/README.md](javascript/README.md)
- **TypeScript 项目**：查看 [typescript/README.md](typescript/README.md)

### 按框架选择

- **React 项目**：查看 [react/README.md](react/README.md)
- **Vue 项目**：查看 [vue/README.md](vue/README.md)
- **Next.js 项目**：查看 [nextjs/README.md](nextjs/README.md)
- **Flutter 项目**：查看 [flutter/README.md](flutter/README.md)

### 按功能选择

- **组件库开发**：查看 [antd/README.md](antd/README.md)
- **代码搜索**：查看 [semantic/README.md](semantic/README.md)
- **版本控制**：查看 [git/README.md](git/README.md)
- **版本管理**：查看 [version/README.md](version/README.md)

## 📖 Skills 文档结构

每个插件都遵循 **多文件 skills 结构**：

```
{plugin-name}/
├── SKILL.md           # 导航和快速开始（300-400 行）
├── reference.md       # 详细配置和规范
├── examples.md        # 使用示例和最佳实践
└── [optional]/        # 领域特定的详细文件
    ├── design-system.md
    ├── performance.md
    ├── testing.md
    └── ...
```

**浏览指南**：
- **快速上手**：阅读各插件的 SKILL.md
- **深入学习**：查看 reference.md 获取详细规范
- **实践示例**：查看 examples.md 获取代码示例

## ✅ 规范遵循

所有 code 插件都遵循 **Anthropic 官方技能创作最佳实践**：

- ✅ 渐进式披露模式
- ✅ YAML frontmatter 完整（name, description）
- ✅ 一级深的 markdown 链接
- ✅ 第三人称描述
- ✅ 简洁清晰的 SKILL.md

详见：[.claude/skills/plugin-skills-authoring.md](../../.claude/skills/plugin-skills-authoring.md)

## 🔗 架构

```
plugins/
├── code/
│   ├── antd/
│   ├── flutter/
│   ├── git/
│   ├── golang/
│   ├── javascript/
│   ├── nextjs/
│   ├── python/
│   ├── react/
│   ├── semantic/
│   ├── template/
│   ├── typescript/
│   ├── version/
│   └── vue/
├── style/         (UI 设计风格插件)
├── notify/        (系统通知)
└── task/          (任务管理)
```

## 📝 开发建议

### 选择合适的插件

1. **语言选择优先级**：选择与项目主要语言对应的插件
2. **框架选择优先级**：使用框架对应的插件获得最佳支持
3. **多语言项目**：组合使用多个语言插件，参考它们的最佳实践

### 跨插件一致性

虽然每个插件有自己的规范，但遵循以下通用原则：

- 代码风格：遵循该语言的标准（PEP 8、ESLint、gofmt 等）
- 命名约定：一致的变量、函数、类命名
- 项目结构：清晰的目录组织
- 测试：每个项目都应有完整的测试覆盖
- 文档：清晰的代码注释和 README

## 🎯 常见场景

**我想开发 React + TypeScript 项目**
→ 查看 [react/README.md](react/README.md) + [typescript/README.md](typescript/README.md)

**我想使用 Ant Design**
→ 查看 [antd/README.md](antd/README.md)

**我想使用 Next.js**
→ 查看 [nextjs/README.md](nextjs/README.md)

**我想开发 Python 项目**
→ 查看 [python/README.md](python/README.md)

**我想做版本管理**
→ 查看 [version/README.md](version/README.md)

## 📚 相关文档

- **项目架构**：[CLAUDE.md](../../CLAUDE.md)
- **Skills 编写规范**：[.claude/skills/plugin-skills-authoring.md](../../.claude/skills/plugin-skills-authoring.md)
- **UI 设计风格插件**：[plugins/style/README.md](../style/README.md)
- **插件市场**：[.claude-plugin/marketplace.json](../../.claude-plugin/marketplace.json)

## 📞 获取帮助

每个插件都有自己的 README 和完整的 skills 文档。选择相关插件后：

1. 阅读 SKILL.md 了解基础概念
2. 查阅 reference.md 了解详细规范
3. 参考 examples.md 中的代码示例
4. 查看 FAQ 部分解答常见问题
