# JavaScript 开发插件

JavaScript 开发插件为 Claude Code 提供全面的 JavaScript（ES2024-2025）开发规范、最佳实践和代码智能支持。

## 功能特性

### 4 个专业代理

- **开发专家** (`dev`) - 现代 ES2024+ 开发、异步编程、ESM 模块系统
- **测试专家** (`test`) - Vitest 框架、单元测试、集成测试、覆盖率管理
- **调试专家** (`debug`) - 异步错误诊断、性能问题定位、内存泄漏分析
- **性能优化专家** (`perf`) - 编译优化、构建性能、运行时优化、Core Web Vitals

### 完整的开发规范

涵盖以下方面的详细指导：

- **现代 JavaScript 特性** - ES2024-2025 新特性、async/await、Promise、ESM
- **编码规范** - 命名约定、代码风格、错误处理、项目结构
- **工具链** - pnpm、Vite、Vitest、ESLint + Prettier
- **异步编程** - Promise 管理、并发控制、错误处理最佳实践
- **框架集成** - React 19、Vue 3 Composition API、Next.js 15
- **性能优化** - 编译优化、运行时优化、Core Web Vitals
- **安全实践** - XSS 防御、CSRF 防御、输入验证

### Language Server Protocol

集成 JavaScript Language Server，提供：

- 实时代码提示和补全
- 语法错误诊断
- 符号导航
- 代码格式化

## 安装

```bash
# 使用 Claude Code CLI 安装
/plugin install ./plugins/javascript

# 或在设置中添加市场地址
https://github.com/lazygophers/ccplugin/tree/master/plugins/javascript
```

## 快速开始

### 1. 项目初始化

```bash
# 使用 Vite 创建 React 项目（推荐）
npm create vite@latest my-app -- --template react
cd my-app
pnpm install

# 或使用 Vue
npm create vite@latest my-app -- --template vue
```

### 2. 配置工具链

```bash
# 安装 ESLint 和 Prettier
pnpm add -D eslint prettier @eslint/js

# 安装 Vitest
pnpm add -D vitest @vitest/ui
```

### 3. 使用代理和技能

在 Claude Code 中：

```bash
# 使用开发专家处理异步编程
@dev 使用 Promise.allSettled 实现并发控制

# 使用测试专家编写单元测试
@test 为 userService 编写 Vitest 单元测试

# 使用调试专家解决问题
@debug 分析为什么这个 Promise 导致内存泄漏

# 使用性能专家优化性能
@perf 分析项目的编译和运行时性能
```

## 核心规范

### 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 变量/函数 | camelCase | `getUserData`, `isActive` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_URL` |
| 文件 | kebab-case | `user-service.js` |
| 类 | PascalCase | `UserManager` |

### 异步编程

```javascript
// ✅ 推荐：async/await
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    return await response.json();
  } catch (error) {
    console.error('Error:', error);
  }
}

// ✅ 推荐：Promise.allSettled
const results = await Promise.allSettled([
  fetchUser(), fetchPosts(), fetchComments()
]);

// ❌ 避免：回调地狱
fetch('/api/data', (err, data) => { });
```

### 模块系统

```javascript
// ✅ 推荐：ESM
import { getUserData } from './services/user.js';
export const validateUser = (user) => { };

// ✅ 推荐：type-only 导入
import type { User } from './types.js';

// ❌ 避免：CommonJS（新项目）
const utils = require('./utils');
```

### 工具链优先级

**包管理器**：pnpm（推荐）→ Yarn → npm

**构建工具**：Vite（推荐）→ esbuild

**测试框架**：Vitest（推荐）优于 Jest

**代码检查**：ESLint 9+ + Prettier

### 项目结构

```
src/
├── features/
│   ├── auth/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── components/
│   │   └── types.js
│   └── dashboard/
├── shared/
│   ├── components/
│   ├── utils/
│   ├── constants/
│   └── types.js
└── main.js
```

## 常见任务

### 创建新项目

```bash
# Vite + React（推荐）
npm create vite@latest my-app -- --template react
cd my-app
pnpm install

# Vite + Vue
npm create vite@latest my-app -- --template vue
```

### 配置 ESLint

```bash
pnpm add -D eslint @eslint/js prettier
```

### 添加 Vitest

```bash
pnpm add -D vitest @vitest/ui
```

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    coverage: { provider: 'v8', lines: 80 }
  }
});
```

## 代理详解

### 开发专家 (dev)

用于处理：
- 现代 JavaScript 特性使用
- 异步编程和 Promise 管理
- ESM 模块系统设计
- 框架集成（React、Vue、Next.js）

### 测试专家 (test)

用于处理：
- Vitest 单元测试编写
- 集成测试设计
- 测试覆盖率管理
- Mock 和 Stub 使用

### 调试专家 (debug)

用于处理：
- Promise rejection 诊断
- 内存泄漏检测
- 性能问题定位
- 工具使用指导

### 性能优化专家 (perf)

用于处理：
- 编译和构建性能优化
- 运行时性能改善
- Core Web Vitals 优化
- 代码分割策略

## 技能模块

插件包含 `javascript-development` 技能，涵盖：

- 现代 JavaScript 特性（ES2024-2025）
- 编码规范和约定
- 异步编程最佳实践
- 工具链配置
- 框架集成指导
- 性能优化策略
- 安全最佳实践

## 支持的框架

- **React 19** - 使用 Hooks，函数组件开发
- **Vue 3** - Composition API，响应式开发
- **Next.js 15** - App Router，服务器组件
- **任意 Vite 项目** - 快速开发体验

## 资源链接

- [ECMAScript 规范](https://tc39.es/ecma262/)
- [MDN JavaScript 文档](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [Vite 官方文档](https://vitejs.dev/)
- [Vitest 文档](https://vitest.dev/)
- [pnpm 文档](https://pnpm.io/)

## 版本信息

- **插件版本**：0.0.1
- **JavaScript**：ES2024-2025
- **Node.js**：24 LTS（推荐）
- **License**：MIT

## 反馈和支持

如有问题或建议，请提交 Issue：

https://github.com/lazygophers/ccplugin/issues

## 更新日志

### 0.0.1 (2025-01-11)

- 初始发布
- 4 个专业代理（dev, test, debug, perf）
- 完整的 ES2024-2025 规范
- LSP 集成
- Vitest 和 Vite 完整支持
