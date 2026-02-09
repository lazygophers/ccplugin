---
name: javascript-skills
description: JavaScript 前端开发规范和最佳实践指导，包括现代 ES2024-2025 标准、前端工具链、框架集成和性能优化等
---

# JavaScript 前端开发规范

## 快速导航

| 文档                                                 | 内容                                                 | 适用场景       |
| ---------------------------------------------------- | ---------------------------------------------------- | -------------- |
| **SKILL.md**                                         | 核心理念、优先工具、强制规范速览                     | 快速入门       |
| [development-practices.md](development-practices.md) | 强制规范、ES2024-2025 新特性、异步编程、ESM 模块     | 日常编码       |
| [architecture-tooling.md](architecture-tooling.md)   | 架构设计、项目结构、Vite 构建、测试框架、工具链     | 项目架构和部署 |
| [coding-standards/](coding-standards/)               | 编码规范（命名、格式、错误处理、测试）               | 代码规范参考   |
| [examples/](examples/)                               | 代码示例（good/bad）                                 | 学习参考       |

## 核心理念

JavaScript 前端生态追求**高性能、组件化、类型安全**，通过精选的工具库和最佳实践，帮助开发者写出高质量的前端代码。

**三个支柱**：

1. **组件化** - 优先使用函数式组件和 Hooks
2. **类型安全** - 优先使用 TypeScript（推荐）
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **JavaScript**：ES2024-2025（最新标准）
- **Node.js**：24 LTS（推荐）或 22 LTS
- **包管理器**：pnpm（推荐）> Yarn > npm
- **构建工具**：Vite 5+
- **测试框架**：Vitest（推荐）或 Jest
- **代码检查**：ESLint 9+ + Prettier 3+

## 优先工具速查

| 用途         | 推荐工具               | 用法                           |
| ------------ | ---------------------- | ------------------------------ |
| 包管理       | `pnpm`                 | `pnpm add lodash-es`           |
| 构建         | `Vite`                 | `pnpm create vite`             |
| 测试         | `Vitest`               | `describe/it/expect`           |
| 语法检查     | `ESLint 9+`            | `eslint . --fix`               |
| 代码格式     | `Prettier`             | `prettier --write .`           |
| 臃肿查询     | `DOMPurify`            | `DOMPurify.sanitize()`         |

## 核心约定

### 强制规范

- ✅ 使用 `const`/`let`，禁止 `var`
- ✅ 使用 ESM（`import`/`export`）
- ✅ 使用 `async`/`await` 处理异步
- ✅ 所有 Promise 必须有错误处理
- ✅ 命名遵循规范（camelCase, PascalCase, UPPER_SNAKE_CASE）
- ✅ 没有 `console.log` 在生产代码
- ✅ 测试覆盖率 80%+
- ✅ 没有 XSS 或 CSRF 漏洞

### 项目结构（功能驱动）

```
src/
├── features/
│   ├── auth/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── components/
│   │   └── types.js
│   ├── dashboard/
│   └── shared/
│       ├── hooks/
│       ├── services/
│       ├── components/
│       ├── utils/
│       ├── constants/
│       └── types.js
├── config/
├── middleware/
├── store/  (Pinia/Redux)
└── main.js
```

## 最佳实践概览

**异步编程**

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

// ✅ Promise.allSettled()：推荐
const results = await Promise.allSettled([
  fetchUser(), fetchPosts(), fetchComments()
]);
```

**ESM 模块**

```javascript
// ✅ 具名导出（推荐）
export const getUserData = async (id) => { };
export const validateUser = (user) => { };

// ✅ 默认导出仅用于主要功能
export default class UserService { }

// ✅ type-only 导入
import type { User } from './types.js';
```

**组件规范**

```javascript
// ✅ 推荐：函数组件 + Hooks
export function UserCard({ userId }) {
  const [user, setUser] = React.useState(null);

  React.useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return user ? <div>{user.name}</div> : <Loading />;
}
```

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解完整的强制规范、ES2024-2025 新特性、异步编程、ESM 模块、集合操作和性能优化指南。
参见 [architecture-tooling.md](architecture-tooling.md) 了解前端架构设计、项目结构、Vite 构建配置、测试框架、依赖管理和开发工具链的详细说明。
参见 [references.md](references.md) 了解 JavaScript ES2024-2025 参考资源，包括 ECMAScript 规范、官方文档、工具文档、框架文档、安全资源和学习资源。

### 编码规范

- [命名规范](coding-standards/naming-conventions.md) - 变量、函数、类、常量、文件命名
- [代码格式规范](coding-standards/code-formatting.md) - ESLint、Prettier 配置
- [错误处理规范](coding-standards/error-handling.md) - try-catch、自定义错误、错误边界
- [测试规范](coding-standards/testing-standards.md) - 单元测试、集成测试、端到端测试
- [注释规范](coding-standards/comment-standards.md) - JSDoc 注释、注释原则、TODO/FIXME
- [文档规范](coding-standards/documentation-standards.md) - README、API 文档、组件文档
- [版本控制规范](coding-standards/version-control-standards.md) - Git 使用规范、分支管理、提交规范
- [代码审查规范](coding-standards/code-review-standards.md) - 审查原则、审查清单、审查流程

### 专项规范

- [异步编程](specialized/async-programming.md) - async/await、Promise.allSettled、超时控制、异步迭代器
- [React 开发](specialized/react-development.md) - React 18+、Hooks、组件模式、性能优化
- [Vue 开发](specialized/vue-development.md) - Vue 3、Composition API、响应式、生命周期
- [Web 安全](specialized/web-security.md) - XSS 防护、CORS 配置、输入验证、CSP

### 代码示例

- [错误处理示例](examples/error-handling-examples.js) - 错误处理代码示例
- [异步编程示例](examples/async-examples.js) - 异步编程代码示例
- [React 组件示例](examples/react-examples.jsx) - React 组件代码示例
- [代码对比示例](examples/good-bad-comparisons.js) - 符合和不符合规范的代码对比

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **本规范** - 中优先级
3. **传统 JavaScript 实践** - 最低优先级
