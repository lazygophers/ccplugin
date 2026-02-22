---
name: core
description: JavaScript 开发核心规范：ES2024-2025 标准、强制约定、代码格式。写任何 JavaScript 代码前必须加载。
---

# JavaScript 开发核心规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 异步编程 | Skills(async) | async/await、Promise |
| React 开发 | Skills(react) | React 18+、Hooks |
| Vue 开发 | Skills(vue) | Vue 3、Composition API |
| Web 安全 | Skills(security) | XSS 防护、CORS |

## 核心原则

JavaScript 前端生态追求**高性能、组件化、类型安全**。

### 必须遵守

1. **const/let** - 禁止 var
2. **ESM 模块** - 使用 import/export
3. **async/await** - 处理异步
4. **错误处理** - 所有 Promise 必须有错误处理
5. **命名规范** - camelCase, PascalCase, UPPER_SNAKE_CASE

### 禁止行为

- 使用 var
- 使用 CommonJS（require/module.exports）
- 没有 try-catch 的 await
- 生产代码中的 console.log
- XSS 或 CSRF 漏洞

## 版本与环境

- **JavaScript**: ES2024-2025
- **Node.js**: 24 LTS（推荐）
- **包管理器**: pnpm（推荐）
- **构建工具**: Vite 5+
- **测试框架**: Vitest

## 项目结构

```
src/
├── features/
│   ├── auth/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── components/
│   └── shared/
├── config/
├── store/
└── main.js
```

## 检查清单

- [ ] 使用 const/let，禁止 var
- [ ] 使用 ESM 模块
- [ ] 所有 Promise 有错误处理
- [ ] 无 console.log 在生产代码
- [ ] 测试覆盖率 80%+
