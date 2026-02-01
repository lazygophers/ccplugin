# 工具链、测试和性能优化

## 代码风格配置

### ESLint + TypeScript

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

### Prettier 配置

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

## 注释规范

```typescript
// ✅ 推荐：必要时说明"为什么"
// 为了避免类型推断失败，显式声明 return 类型
function getUserData(id: string): Promise<User | null> {
	return fetchUser(id);
}

// ❌ 避免：显而易见的注释
// 获取用户数据
function getUserData(id: string): Promise<User | null> {}

// ✅ 推荐：复杂逻辑的说明
// 使用 discriminated union 简化类型检查逻辑
type Status = { type: "success"; data: T } | { type: "error"; error: Error };

// ❌ 避免：修改历史注释
// TODO: 2024-01-15 修复性能问题 <- 应该在 git提交记录中
```

## 导入规范

```typescript
// ✅ 推荐：type-only imports
import type { User, UserRole } from "@/types";
import { getUserService } from "@/services";

// ❌ 避免：混合导入或多余导入
import { User, UserRole, getUserService } from "@/types";
import * as helpers from "@/helpers"; // 应该明确指定

// ✅ 推荐：分组导入
import { Component } from "react";
import type { ReactNode } from "react";

import { getUserById } from "@/services/user";
import type { User } from "@/types/user";

import { generateId } from "@/utils/id";
```

## 项目结构

### 目录组织

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

### 依赖方向

```
API Routes → Services → Entities → Types
             ↑
             └── Utils, Config
```

禁止反向依赖：Services 不应依赖 API Routes。

### 公开接口

```typescript
// src/services/index.ts - 统一导出公开接口
export { getUserService } from "./user";
export { getProductService } from "./product";
export type { UserService } from "./user";
export type { ProductService } from "./product";

// 禁止导出内部实现
// ❌ export { privateHelper } from './user/helpers';
```

## 测试规范：Vitest

### 安装和配置

```bash
pnpm add -D vitest @vitest/ui
```

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
	test: {
		environment: "node",
		globals: true,
		coverage: {
			provider: "v8",
			reporter: ["text", "json", "html"],
			lines: 80,
			functions: 80,
			branches: 75,
			statements: 80,
		},
	},
});
```

### 单元测试最佳实践

```typescript
// ✅ 推荐：清晰的测试结构
describe("UserService", () => {
	let service: UserService;

	beforeEach(() => {
		service = new UserService();
	});

	describe("getUserById", () => {
		it("should return user when found", async () => {
			const result = await service.getUserById("123");
			expect(result).toMatchObject({ ok: true });
		});

		it("should return error when user not found", async () => {
			const result = await service.getUserById("non-existent");
			expect(result).toMatchObject({ ok: false });
		});
	});
});

// ❌ 避免：不清晰的测试
it("test", () => {
	expect(getUserById("123")).toBeDefined();
});
```

### 测试覆盖率目标

- 语句覆盖率: 80%+
- 分支覆盖率: 75%+
- 函数覆盖率: 80%+
- 类型覆盖率: 100%

## tsconfig.json 完整配置

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

## 包管理器：pnpm

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

## 构建工具选择

**推荐顺序**：

1. **Vite** - 最现代化选择，适合 Web 应用
2. **esbuild** - 超快构建，适合库
3. **tsup** - 简化库打包（基于 esbuild）
4. **Webpack** - 复杂场景或 legacy 项目

## 性能优化

### 编译优化

- ✅ 启用 `incremental` 编译
- ✅ 使用 `skipLibCheck: true` 跳过 node_modules 检查
- ✅ 使用 `type-only imports` 减少运行时代码
- ❌ 避免复杂的 union 类型
- ❌ 避免无限递归的泛型

### 运行时优化

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
