---
name: typescript-development
description: TypeScript 开发规范 - 涵盖类型系统、编码规范、项目结构、测试策略和最佳实践。基于 TypeScript 5.9+ 的官方规范和业界最佳实践
auto-activate: always:true
---

# TypeScript 开发规范

## 概述

本规范提供 TypeScript 5.9+ 的完整开发指导，涵盖类型系统、代码风格、项目架构、工具链配置和测试策略。

## 版本和环境

- **TypeScript**: 5.9+ (当前稳定版本)
- **Node.js**: 20+ LTS
- **包管理器**: pnpm (推荐) → Yarn Berry → npm
- **运行时**: Node.js 或 Deno
- **测试框架**: Vitest (推荐) 优于 Jest
- **代码风格**: ESLint + Prettier

## 部分 1: 类型系统规范

### 1.1 Strict Mode（必须启用）

在 `tsconfig.json` 中启用所有严格检查：

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

**强制选项说明**：
- `noImplicitAny`: 禁用 any 类型的隐式使用
- `strictNullChecks`: 区分 null/undefined 和其他类型
- `strictFunctionTypes`: 函数参数类型严格检查
- `strictBindCallApply`: 严格检查 bind/call/apply
- `strictPropertyInitialization`: 类属性必须初始化
- `noImplicitThis`: 禁用隐式 any 的 this

### 1.2 命名约定

**类型系统命名**：
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

**变量和函数命名**：
```typescript
// ✅ 正确
const userName: string = 'John';
function getUserById(id: string): Promise<User> { }
const isActive = true;
const MAX_RETRIES = 3;

// ❌ 错误
const user_name: string = 'John';     // 使用 camelCase
function Get_User_By_Id(id: string) { } // 函数使用 camelCase
const maxRetries = 3;                  // 常量使用 UPPER_SNAKE_CASE 或 camelCase
```

### 1.3 类型定义优先级

```typescript
// 1️⃣ 优先：type (大多数情况)
type User = { id: string; name: string };
type ApiResponse<T> = { data: T; status: number };

// 2️⃣ 次选：interface (需要 declaration merging)
interface Plugin {
  name: string;
  execute(): void;
}
interface Plugin {
  version: string;
}

// 3️⃣ 避免：class (除非需要实现)
class User {
  constructor(public id: string, public name: string) {}
}

// 4️⃣ 禁止：any
function process(data: any) { } // ❌ 禁止
```

### 1.4 泛型约束

```typescript
// ✅ 推荐：有明确约束
function getProperty<T extends object, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// ❌ 避免：过于宽松
function getProperty<T>(obj: T, key: string): any {
  return (obj as any)[key];
}

// ✅ 推荐：使用 Record 代替索引签名
type Settings<T extends string = string> = Record<T, unknown>;

// ❌ 避免：过于通用的索引
type Settings = {
  [key: string]: any;
};
```

### 1.5 Union 类型最佳实践

```typescript
// ✅ 推荐：Discriminated Union
type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: Error };

function handle<T>(result: Result<T>) {
  if (result.ok) {
    console.log(result.data); // data 类型正确
  } else {
    console.log(result.error); // error 类型正确
  }
}

// ❌ 避免：简单 Union
type Result<T> = T | Error;
```

## 部分 2: 编码规范

### 2.1 代码风格

**使用 Prettier + ESLint with TypeScript**：

```javascript
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/strict",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/no-explicit-any": "error"
  }
}
```

**Prettier 配置**：

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always"
}
```

### 2.2 注释规范

```typescript
// ✅ 推荐：必要时说明"为什么"
// 为了避免类型推断失败，显式声明 return 类型
function getUserData(id: string): Promise<User | null> {
  return fetchUser(id);
}

// ❌ 避免：显而易见的注释
// 获取用户数据
function getUserData(id: string): Promise<User | null> { }

// ✅ 推荐：复杂逻辑的说明
// 使用 discriminated union 简化类型检查逻辑
type Status = { type: 'success'; data: T } | { type: 'error'; error: Error };

// ❌ 避免：修改历史注释
// TODO: 2024-01-15 修复性能问题 <- 应该在 git 提交记录中
```

### 2.3 导入规范

```typescript
// ✅ 推荐：type-only imports
import type { User, UserRole } from '@/types';
import { getUserService } from '@/services';

// ❌ 避免：混合导入或多余导入
import { User, UserRole, getUserService } from '@/types';
import * as helpers from '@/helpers'; // 应该明确指定

// ✅ 推荐：分组导入
import { Component } from 'react';
import type { ReactNode } from 'react';

import { getUserById } from '@/services/user';
import type { User } from '@/types/user';

import { generateId } from '@/utils/id';
```

## 部分 3: 项目结构

### 3.1 目录组织

```
src/
├── types/                    # 类型定义
│   ├── index.ts
│   ├── user.ts
│   └── api.ts
├── entities/                 # 业务实体（包含类型和逻辑）
│   ├── user/
│   │   ├── User.ts          # 实体定义和方法
│   │   └── UserRole.ts
│   └── product/
├── services/                 # 业务逻辑层
│   ├── user.ts              # UserService
│   ├── product.ts
│   └── index.ts
├── api/                      # API 路由处理
│   ├── v1/
│   │   ├── users.ts
│   │   └── products.ts
│   └── middleware/
├── utils/                    # 工具函数
│   ├── logger.ts
│   ├── validators.ts
│   └── helpers.ts
├── config/                   # 配置
│   ├── env.ts
│   └── database.ts
└── index.ts                  # 入口点
```

### 3.2 依赖方向

```
API Routes → Services → Entities → Types
             ↑
             └── Utils, Config
```

禁止反向依赖：Services 不应依赖 API Routes。

### 3.3 公开接口

```typescript
// src/services/index.ts - 统一导出公开接口
export { getUserService } from './user';
export { getProductService } from './product';
export type { UserService } from './user';
export type { ProductService } from './product';

// 禁止导出内部实现
// ❌ export { privateHelper } from './user/helpers';
```

## 部分 4: 常见类型模式

### 4.1 异步操作结果

```typescript
// 推荐：Result 类型
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function isOk<T, E>(result: Result<T, E>): result is { ok: true; value: T } {
  return result.ok;
}

// 使用
const result = await userService.getUserById(id);
if (isOk(result)) {
  console.log(result.value);
} else {
  console.error(result.error);
}
```

### 4.2 可选属性和默认值

```typescript
// ✅ 推荐：明确的可选
type UserOptions = {
  name: string;
  email?: string;      // 可选属性
  age: number | null;  // 明确 null
};

// ❌ 避免：隐式 undefined
type UserOptions = {
  name: string;
  email?: string | undefined;  // 冗余
};

// ✅ 推荐：默认值
function createUser(options: UserOptions): User {
  return {
    name: options.name,
    email: options.email ?? '',
    age: options.age ?? 0,
  };
}
```

### 4.3 错误处理类型

```typescript
// ✅ 推荐：自定义错误类
class NotFoundError extends Error {
  constructor(resource: string, id: string) {
    super(`${resource} with id ${id} not found`);
    this.name = 'NotFoundError';
  }
}

// ✅ 推荐：类型守卫
function isNotFoundError(error: unknown): error is NotFoundError {
  return error instanceof NotFoundError;
}

// 使用
try {
  await userService.getUserById(id);
} catch (error) {
  if (isNotFoundError(error)) {
    // 处理 404
  } else if (error instanceof Error) {
    // 处理其他错误
  }
}
```

## 部分 5: 测试规范

### 5.1 测试框架：Vitest

**安装和配置**：

```bash
pnpm add -D vitest @vitest/ui
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
    },
  },
});
```

### 5.2 单元测试最佳实践

```typescript
// ✅ 推荐：清晰的测试结构
describe('UserService', () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  describe('getUserById', () => {
    it('should return user when found', async () => {
      const result = await service.getUserById('123');
      expect(result).toMatchObject({ ok: true });
    });

    it('should return error when user not found', async () => {
      const result = await service.getUserById('non-existent');
      expect(result).toMatchObject({ ok: false });
    });
  });
});

// ❌ 避免：不清晰的测试
it('test', () => {
  expect(getUserById('123')).toBeDefined();
});
```

### 5.3 测试覆盖率目标

- 语句覆盖率: 80%+
- 分支覆盖率: 75%+
- 函数覆盖率: 80%+
- 类型覆盖率: 100%

## 部分 6: 工具链配置

### 6.1 tsconfig.json 完整配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020"],

    // 路径别名
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@types/*": ["src/types/*"]
    },

    // 严格检查（必须启用）
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,

    // 模块解析
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": false,

    // 输出
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "removeComments": true,

    // 性能
    "skipLibCheck": true,
    "skipDefaultLibCheck": true,
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo",

    // 其他
    "forceConsistentCasingInFileNames": true,
    "importsNotUsedAsValues": "error",
    "isolatedModules": true,
    "noEmitOnError": false
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### 6.2 包管理器：pnpm

**优势**：
- 快速的依赖安装
- 磁盘空间效率高
- 严格的依赖隔离
- 单版本政策

**常用命令**：

```bash
# 安装依赖
pnpm install

# 添加依赖
pnpm add lodash
pnpm add -D @types/node

# 更新依赖
pnpm update

# 运行脚本
pnpm run build
```

### 6.3 构建工具

**推荐顺序**：
1. **Vite** - 最现代化选择，适合 Web 应用
2. **esbuild** - 超快构建，适合库
3. **tsup** - 简化库打包（基于 esbuild）
4. **Webpack** - 复杂场景或 legacy 项目

## 部分 7: 常见反模式和解决方案

### 7.1 类型相关反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| `any` 类型 | 失去类型安全 | 使用泛型或明确类型 |
| `I` 前缀接口 | C# 约定，不符合 TS 风格 | 移除前缀 |
| 过度类型注解 | 降低代码可读性 | 信任类型推断 |
| `as any` | 绕过类型检查 | 使用类型守卫 |
| 循环引用 | 编译错误或性能问题 | 使用 type-only imports |

### 7.2 异步操作反模式

```typescript
// ❌ 反模式：Promise 嵌套
function getUser(id: string) {
  return new Promise((resolve) => {
    getDataFromAPI(id).then(data => {
      resolve(data);
    });
  });
}

// ✅ 正确：返回 Promise
function getUser(id: string): Promise<User> {
  return getDataFromAPI(id);
}

// ❌ 反模式：忘记 await
async function processUsers(ids: string[]) {
  const users = ids.map(id => getUserById(id)); // 返回 Promise[]
  return users[0].name; // 错误：访问 Promise 的属性
}

// ✅ 正确：使用 await 或 Promise.all
async function processUsers(ids: string[]) {
  const users = await Promise.all(ids.map(id => getUserById(id)));
  return users[0]?.name;
}
```

## 部分 8: 框架集成

### 8.1 React 19 + TypeScript

```typescript
import type { ReactNode } from 'react';

type ButtonProps = {
  children: ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
};

export function Button({ children, onClick, variant = 'primary' }: ButtonProps) {
  return (
    <button className={`btn-${variant}`} onClick={onClick}>
      {children}
    </button>
  );
}
```

### 8.2 Vue 3 + TypeScript

```typescript
<script setup lang="ts">
import { ref, computed } from 'vue';

interface User {
  id: string;
  name: string;
}

const props = withDefaults(
  defineProps<{ userId: string }>(),
  { userId: '' }
);

const user = ref<User | null>(null);

const displayName = computed(() => user.value?.name ?? 'Unknown');
</script>
```

### 8.3 Next.js 15 + TypeScript

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get('id');

  if (!id) {
    return NextResponse.json({ error: 'Missing id' }, { status: 400 });
  }

  const user = await getUserById(id);
  return NextResponse.json(user);
}
```

## 部分 9: 运行时类型检查

### 9.1 Zod 验证

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  email: z.string().email(),
  age: z.number().min(0).max(150).optional(),
});

type User = z.infer<typeof UserSchema>;

// 验证数据
const validateUser = (data: unknown): Result<User> => {
  try {
    const user = UserSchema.parse(data);
    return { ok: true, value: user };
  } catch (error) {
    return { ok: false, error: error as Error };
  }
};
```

## 部分 10: 性能优化

### 10.1 编译优化

- ✅ 启用 `incremental` 编译
- ✅ 使用 `skipLibCheck: true` 跳过 node_modules 检查
- ✅ 使用 `type-only imports` 减少运行时代码
- ❌ 避免复杂的 union 类型
- ❌ 避免无限递归的泛型

### 10.2 运行时优化

- ✅ 使用 Web Worker 处理 CPU 密集任务
- ✅ 使用 Promise.all() 进行并发操作
- ✅ 及时释放大对象引用
- ❌ 避免闭包导致的内存泄漏

## 快速检查清单

- [ ] `strict: true` 已在 tsconfig.json 中启用
- [ ] 所有类型使用 PascalCase（不使用 I 前缀）
- [ ] 所有变量/函数使用 camelCase
- [ ] 优先使用 `type` 而非 `interface`
- [ ] 使用 `type-only imports`
- [ ] 没有 `any` 类型
- [ ] 使用 Discriminated Union 处理多个状态
- [ ] 所有异步函数返回 `Promise<T>`
- [ ] 单元测试覆盖率 80%+
- [ ] 所有 React 组件都有类型
- [ ] 错误处理使用类型守卫
- [ ] 导出的 API 都有明确的类型
