---
name: core
description: TypeScript 开发核心规范：TS 5.9+、严格模式、强制约定。写任何 TypeScript 代码前必须加载。
---

# TypeScript 开发核心规范

## 相关 Skills

| 场景       | Skill            | 说明                     |
| ---------- | ---------------- | ------------------------ |
| 类型系统   | Skills(types)    | 类型安全、泛型、类型守卫 |
| 异步编程   | Skills(async)    | async/await、Promise     |
| React 开发 | Skills(react)    | React 18+、Hooks         |
| Node.js    | Skills(nodejs)   | Node.js 20+、ESM         |
| 安全编码   | Skills(security) | 输入验证、XSS 防护       |

## 核心原则

TypeScript 生态追求**类型安全、现代工程、可维护性**。

### 必须遵守

1. **严格模式** - 启用 strict 模式
2. **类型安全** - 禁止 any，使用 unknown
3. **运行时验证** - 使用 Zod 进行运行时验证
4. **pnpm** - 使用 pnpm 作为包管理器
5. **Vitest** - 使用 Vitest 作为测试框架

### 禁止行为

- 使用 `any` 类型（使用 `unknown` 代替）
- 单行错误处理
- 硬编码密钥和配置
- 使用 `@ts-ignore` 绕过类型检查
- 忽略测试覆盖率

## 版本与环境

- **TypeScript**: 5.9+
- **Node.js**: 20+ LTS
- **包管理器**: pnpm（推荐）
- **测试框架**: Vitest
- **构建工具**: Vite

## 命名约定

```typescript
// 类型：PascalCase
type UserDTO = { id: string; name: string };
interface ApiResponse {
	data: unknown;
	status: number;
}

// 变量：camelCase
const userName: string = "John";

// 常量：UPPER_SNAKE_CASE
const MAX_RETRIES = 3;

// 函数：camelCase
function getUserById(id: string): Promise<User> {}
```

## tsconfig.json

```json
{
	"compilerOptions": {
		"strict": true,
		"noImplicitAny": true,
		"strictNullChecks": true
	}
}
```

## 检查清单

- [ ] 启用 strict 模式
- [ ] 无 any 类型
- [ ] 使用 Zod 运行时验证
- [ ] 使用 pnpm
- [ ] 测试覆盖率 >80%
