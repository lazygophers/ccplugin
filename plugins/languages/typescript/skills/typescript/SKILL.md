---
name: typescript-skills
description: TypeScript 5.9+ 开发规范 - 包含类型系统、编码规范、项目结构、测试策略和最佳实践
---

# TypeScript 5.9+ 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心理念、优先库、强制规范速览 | 快速入门 |
| [development-practices.md](development-practices.md) | 强制规范、错误处理、命名、类型安全 | 日常编码 |
| [architecture-tooling.md](architecture-tooling.md) | 架构设计、项目结构、工具链配置 | 项目架构 |
| [references.md](references.md) | 类型系统详解、泛型、模式 | 类型设计 |
| [coding-standards/](coding-standards/) | 编码规范（错误、命名、格式、注释） | 代码规范参考 |
| [specialized/](specialized/) | 专项规范（异步、React、Node.js、安全） | 特定场景 |
| [examples/](examples/) | 代码示例（good/bad） | 学习参考 |

## 核心理念

TypeScript 生态追求**类型安全、现代工程、可维护性**，通过精选的工具库和最佳实践，帮助开发者写出高质量的 TypeScript 代码。

**三个支柱**：

1. **类型安全** - 充分利用 TypeScript 类型系统，减少运行时错误
2. **现代实践** - 使用最新的 ES2024-2025 特性和工具链
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **TypeScript**: 5.9+ (当前稳定版本)
- **Node.js**: 20+ LTS
- **包管理器**: pnpm (推荐) → Yarn Berry → npm
- **运行时**: Node.js、Deno 或 Bun
- **测试框架**: Vitest (推荐) 优于 Jest
- **代码风格**: ESLint + Prettier + typescript-eslint

## 优先库速查

| 用途 | 推荐库 | 用法 |
|------|--------|------|
| 运行时验证 | Zod | `z.object({}).parse(data)` |
| 测试 | Vitest | `test('name', () => {})` |
| 包管理 | pnpm | `pnpm install` |
| 代码风格 | ESLint + Prettier | `eslint .` |
| 构建工具 | Vite | `vite build` |
| 异步处理 | Promise + async/await | `await promise` |
| HTTP 客户端 | fetch / axios | `fetch(url)` |

## 强制规范速览

### ✅ 必须遵守

- **使用 pnpm** 作为包管理器
- **启用 strict 模式** 在 tsconfig.json 中
- **使用 Zod** 进行运行时类型验证
- **使用 Vitest** 作为测试框架
- **多行错误处理** 禁止单行 if
- **命名规范** 类型 PascalCase、变量 camelCase、常量 UPPER_SNAKE_CASE

### ❌ 禁止行为

- 使用 `any` 类型（使用 `unknown` 代替）
- 单行错误处理
- 硬编码密钥和配置
- 使用 `@ts-ignore` 绕过类型检查
- 忽略测试覆盖率

## 命名约定

### 类型系统命名

```typescript
// ✅ 正确
type UserDTO = { id: string; name: string };
interface ApiResponse { data: unknown; status: number }
type Status = 'active' | 'inactive' | 'pending';
enum Role { Admin, User, Guest }

// ❌ 错误
type IUser = { };      // 禁止使用 I 前缀（C# 约定）
type user = { };       // 类型使用 PascalCase
interface userData { } // 接口使用 PascalCase
```

### 变量和函数命名

```typescript
// ✅ 正确
const userName: string = 'John';
function getUserById(id: string): Promise<User> { }
const isActive = true;
const MAX_RETRIES = 3;

// ❌ 错误
const user_name: string = 'John';     // 使用 camelCase
function Get_User_By_Id(id: string) { } // 函数使用 camelCase
const maxRetries = 3;                  // 常量使用 UPPER_SNAKE_CASE
```

## 最佳实践概览

### 类型安全

```typescript
// ✅ 启用严格模式
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}

// ✅ 使用类型守卫
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

// ✅ 使用 Zod 运行时验证
import { z } from 'zod';
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
});
```

### 错误处理

```typescript
// ✅ 正确 - 多行处理，记录日志
try {
  const data = await fetchData();
  return data;
} catch (error) {
  console.error('error:', error);
  throw error;
}

// ❌ 禁止 - 单行 if
if (err) return err;
```

### 异步编程

```typescript
// ✅ 正确 - 使用 async/await
async function getUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

// ✅ 正确 - 并发处理
const users = await Promise.all([
  getUser('1'),
  getUser('2'),
  getUser('3'),
]);

// ❌ 禁止 - Promise 嵌套
function bad() {
  return new Promise((resolve) => {
    getData().then(data => {
      resolve(data);
    });
  });
}
```

## 扩展文档

### 核心文档

参见 [development-practices.md](development-practices.md) 了解完整的强制规范、错误处理、命名规范、类型安全和性能优化指南。

参见 [architecture-tooling.md](architecture-tooling.md) 了解架构设计、项目结构、依赖管理和工具链配置的详细说明。

参见 [references.md](references.md) 了解类型系统详解，包括严格模式、泛型约束、Union 类型、常见类型模式和错误处理。

### 编码规范

- [错误处理规范](coding-standards/error-handling.md) - 错误处理原则、Result 类型、异常链
- [命名规范](coding-standards/naming-conventions.md) - 类型、变量、函数、常量命名
- [代码格式规范](coding-standards/code-formatting.md) - 代码格式化、导入规范、缩进
- [注释规范](coding-standards/comment-standards.md) - 注释原则、JSDoc 格式
- [项目结构规范](coding-standards/project-structure.md) - 项目目录布局、模块组织
- [测试规范](coding-standards/testing-standards.md) - 单元测试、集成测试、Vitest 配置
- [文档规范](coding-standards/documentation-standards.md) - README、API 文档、类型文档
- [版本控制规范](coding-standards/version-control-standards.md) - Git 使用规范、分支管理
- [代码审查规范](coding-standards/code-review-standards.md) - 审查原则、审查清单

### 专项规范

- [异步编程规范](specialized/async-programming.md) - Promise、async/await、错误处理
- [React 开发规范](specialized/react-development.md) - React 18+、Hooks、组件模式
- [Node.js 开发规范](specialized/nodejs-development.md) - Node.js 20+、ESM、性能
- [安全编码规范](specialized/security.md) - 输入验证、XSS 防护、依赖审计

### 代码示例

- [错误处理示例](examples/error-handling-examples.ts) - Result 类型、错误处理模式
- [异步编程示例](examples/async-examples.ts) - Promise、并发、错误处理
- [React 示例](examples/react-examples.tsx) - Hooks、组件模式、最佳实践
- [代码对比示例](examples/good-bad-comparisons.ts) - 正确与错误代码对比

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **本规范** - 中优先级
3. **传统 TypeScript 实践** - 最低优先级
