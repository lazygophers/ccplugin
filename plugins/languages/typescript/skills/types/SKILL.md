---
description: TypeScript 类型系统规范：discriminated unions、const type params、模板字面量、Zod 4。设计类型时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# TypeScript 类型系统规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | TypeScript 开发专家 |
| debug | TypeScript 调试专家 |
| test  | TypeScript 测试专家 |
| perf  | TypeScript 性能优化专家 |

## 相关 Skills

| 场景     | Skill            | 说明                             |
| -------- | ---------------- | -------------------------------- |
| 核心规范 | Skills(core)     | TS 5.7+、strict mode、工具链     |
| 异步编程 | Skills(async)    | Promise 类型、async iterators    |
| 安全编码 | Skills(security) | Zod 输入验证、类型安全的 sanitize |

## 类型命名

```typescript
// PascalCase，语义清晰
type UserDTO = { id: string; name: string; email: string };
type ApiResponse<T> = { data: T; status: number; timestamp: string };
type Status = "active" | "inactive" | "pending";

// 禁止 I 前缀（C# 约定）
// type IUser = {}; // 禁止
```

## Discriminated Unions（TS 5.7）

```typescript
// 状态机建模
type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

// 穷举检查
function handleState<T>(state: AsyncState<T>): string {
  switch (state.status) {
    case "idle": return "Waiting...";
    case "loading": return "Loading...";
    case "success": return `Got: ${state.data}`;
    case "error": return `Error: ${state.error.message}`;
    default: {
      const _exhaustive: never = state;
      return _exhaustive;
    }
  }
}
```

## Const Type Parameters（TS 5.0+）

```typescript
// const 泛型参数保留字面量类型
function createConfig<const T extends Record<string, unknown>>(config: T): T {
  return config;
}
const config = createConfig({ api: "/v1", timeout: 3000 });
// typeof config = { readonly api: "/v1"; readonly timeout: 3000 }
```

## 模板字面量类型

```typescript
type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE";
type APIRoute = `/api/${string}`;
type EventName = `on${Capitalize<string>}`;

// 组合
type Endpoint = `${HTTPMethod} ${APIRoute}`;
// "GET /api/users" | "POST /api/users" | ...
```

## 类型守卫（TS 5.5 inferred predicates）

```typescript
// TS 5.5: 自动推断类型谓词
function isNonNullable<T>(value: T): value is NonNullable<T> {
  return value !== null && value !== undefined;
}

// 使用 - filter 自动收窄类型
const users: (User | null)[] = [user1, null, user2];
const validUsers = users.filter(isNonNullable);
// validUsers: User[]

// 自定义类型守卫
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof (value as { id: unknown }).id === "string"
  );
}
```

## Zod 4 运行时验证

```typescript
import { z } from "zod";

// Schema-first：从 schema 推断类型
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(["admin", "user", "guest"]),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

type User = z.infer<typeof UserSchema>;

// 安全解析（不抛异常）
const result = UserSchema.safeParse(data);
if (!result.success) {
  console.error(result.error.flatten());
}

// 转换管道
const CreateUserSchema = UserSchema.omit({ id: true }).extend({
  password: z.string().min(8).regex(/[A-Z]/).regex(/[0-9]/),
});
```

## 实用类型模式

```typescript
// Branded types（编译期区分语义相同的类型）
type Brand<T, B extends string> = T & { readonly __brand: B };
type UserId = Brand<string, "UserId">;
type PostId = Brand<string, "PostId">;

function getUser(id: UserId): Promise<User> { /* ... */ }
// getUser("123" as UserId); // OK
// getUser("123" as PostId); // Error

// Satisfies 操作符（TS 4.9+，保留字面量类型）
const routes = {
  home: "/",
  about: "/about",
  user: "/user/:id",
} satisfies Record<string, string>;
// typeof routes.home = "/"  （不是 string）

// 条件类型提取
type ExtractPromise<T> = T extends Promise<infer U> ? U : T;
type Awaited<T> = T extends Promise<infer U> ? Awaited<U> : T;
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| `any` 类型 | 类型安全漏洞，使用 `unknown` | 高 |
| 未穷举的 switch | discriminated union 遗漏分支 | 高 |
| `as` 类型断言 | 可能隐藏类型错误 | 中 |
| 无 Zod 验证 | 外部数据未做运行时验证 | 高 |
| 过深递归类型 | 编译性能问题（限制 5 层） | 中 |
| `I` 前缀接口 | C# 约定，TS 中不推荐 | 低 |

## 检查清单

- [ ] 无 `any` 类型，使用 `unknown` + 类型守卫
- [ ] discriminated unions 有穷举检查
- [ ] 外部数据使用 Zod/Valibot 验证
- [ ] `import type` 分离类型导入
- [ ] 泛型有适当约束
- [ ] 使用 `satisfies` 保留字面量类型
- [ ] 复杂类型有深度限制
- [ ] 类型命名使用 PascalCase
