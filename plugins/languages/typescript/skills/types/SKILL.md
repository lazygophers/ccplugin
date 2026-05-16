---
name: typescript-types
description: TypeScript 高级类型系统规范，覆盖 discriminated unions、模板字面量类型、条件 / mapped types、类型守卫（TS 5.5 inferred predicates）、branded types、satisfies 与 Zod 4 / Valibot 运行时验证。Use when 设计复杂类型、类型体操、API 类型契约、运行时校验，或用户提到 "类型系统"、"discriminated union"、"Zod schema"、"类型守卫"、"branded type"。
user-invocable: true
---

# TypeScript 类型系统规范

类型系统两大用途：建模业务状态（discriminated unions / branded types）+ 验证外部输入（Zod / Valibot）。

## 类型命名

```typescript
type UserDTO = { id: string; name: string };           // PascalCase
type ApiResponse<T> = { data: T; status: number };
type Status = "active" | "inactive" | "pending";

// 禁止 I 前缀
// type IUser = {};
```

## Discriminated Unions（状态机首选）

```typescript
type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

function render<T>(state: AsyncState<T>): string {
  switch (state.status) {
    case "idle":    return "Waiting...";
    case "loading": return "Loading...";
    case "success": return `Got: ${JSON.stringify(state.data)}`;
    case "error":   return `Error: ${state.error.message}`;
    default: {
      const _exhaustive: never = state; // 穷举检查
      return _exhaustive;
    }
  }
}
```

## Const Type Parameters（TS 5.0+）

```typescript
function createConfig<const T extends Record<string, unknown>>(c: T): T {
  return c;
}
const cfg = createConfig({ api: "/v1", timeout: 3000 });
// typeof cfg = { readonly api: "/v1"; readonly timeout: 3000 }
```

## 模板字面量类型

```typescript
type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE";
type APIRoute = `/api/${string}`;
type Endpoint = `${HTTPMethod} ${APIRoute}`;
type EventName = `on${Capitalize<string>}`;
```

## 类型守卫（TS 5.5 inferred predicates）

```typescript
// TS 5.5+: 推断类型谓词
function isNonNullable<T>(v: T): v is NonNullable<T> {
  return v !== null && v !== undefined;
}
const users: (User | null)[] = [u1, null, u2];
const valid = users.filter(isNonNullable); // User[]

// 显式自定义类型守卫
function isUser(v: unknown): v is User {
  return typeof v === "object" && v !== null
    && "id" in v && typeof (v as { id: unknown }).id === "string";
}
```

## Zod 4 运行时验证（推荐）

```typescript
import { z } from "zod";

const UserSchema = z.object({
  id: z.uuid(),                          // Zod 4: 顶层 helper
  name: z.string().min(1).max(100),
  email: z.email(),
  role: z.enum(["admin", "user", "guest"]),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

type User = z.infer<typeof UserSchema>;  // schema-first 类型

const r = UserSchema.safeParse(data);
if (!r.success) console.error(z.treeifyError(r.error));

// 派生 schema
const CreateUserSchema = UserSchema.omit({ id: true }).extend({
  password: z.string().min(8).regex(/[A-Z]/).regex(/[0-9]/),
});
```

替代选择：**Valibot**（更小 bundle，函数式 API，<2KB），用于体积敏感场景。

## Branded Types（编译期区分语义）

```typescript
type Brand<T, B extends string> = T & { readonly __brand: B };
type UserId = Brand<string, "UserId">;
type PostId = Brand<string, "PostId">;

function getUser(id: UserId): Promise<User> { /* ... */ }
// getUser("123" as UserId); // OK
// getUser("123" as PostId); // Error
```

## satisfies（TS 4.9+，保留字面量）

```typescript
const routes = {
  home: "/",
  about: "/about",
  user: "/user/:id",
} satisfies Record<string, string>;
// typeof routes.home = "/"（非 string）
```

## 工具类型常用

```typescript
// 内置：Partial / Required / Pick / Omit / Record / Readonly / Awaited / ReturnType / Parameters

// type-fest 推荐补充：SetOptional, SetRequired, Merge, CamelCase, etc.

type ExtractPromise<T> = T extends Promise<infer U> ? U : T;
type DeepReadonly<T> = { readonly [K in keyof T]: DeepReadonly<T[K]> };
```

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| `any` | 用 `unknown` + 守卫 | 高 |
| 未穷举的 switch | DU 遗漏分支 | 高 |
| `as` 强转 | 可能隐藏错误（仅边界用） | 中 |
| 外部数据无 Zod | 运行时类型不安全 | 高 |
| 递归类型 > 5 层 | 编译性能 | 中 |
| `I` 前缀 | C# 约定 | 低 |
| `enum` | tree-shake 不友好 | 中 |

## 检查清单

- [ ] 无 `any`，外部数据 Zod / Valibot 验证
- [ ] discriminated unions 有 `never` 穷举
- [ ] `import type` 分离类型
- [ ] 泛型有 `extends` 约束
- [ ] 复杂常量用 `satisfies`
- [ ] 语义相同 string/number 用 branded type
- [ ] 类型 PascalCase，无 `I` 前缀
