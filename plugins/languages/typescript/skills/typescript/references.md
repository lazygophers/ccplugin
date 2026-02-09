# TypeScript 类型系统参考文档

## 严格模式配置

### 必须启用的选项

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitReturns": true,
    "noUncheckedIndexedAccess": true
  }
}
```

### 选项说明

| 选项 | 说明 |
|------|------|
| `strict` | 启用所有严格类型检查选项 |
| `noImplicitAny` | 禁止隐式 any 类型 |
| `strictNullChecks` | 区分 null/undefined 和其他类型 |
| `strictFunctionTypes` | 函数参数类型严格检查 |
| `strictBindCallApply` | 严格检查 bind/call/apply |
| `strictPropertyInitialization` | 类属性必须初始化 |
| `noImplicitThis` | 禁用隐式 any 的 this |
| `noUncheckedIndexedAccess` | 索引访问可能为 undefined |
| `noImplicitOverride` | 覆盖方法必须使用 override 关键字 |

## 类型定义优先级

```typescript
// 1️⃣ 优先：type (大多数情况)
type User = { id: string; name: string };
type ApiResponse<T> = { data: T; status: number };
type Status = 'active' | 'inactive' | 'pending';

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

## 基础类型

### 原始类型

```typescript
// 字符串
const name: string = 'John';
const template: string = `Hello ${name}`;

// 数字
const count: number = 42;
const pi: number = 3.14;

// 布尔
const isActive: boolean = true;
const hasPermission: boolean = false;

// null 和 undefined
const nullable: string | null = null;
const optional: string | undefined = undefined;

// void 和 never
function log(message: string): void {
  console.log(message);
}

function throwError(message: string): never {
  throw new Error(message);
}

// any 和 unknown
const anything: any = 'anything';  // ❌ 避免
const something: unknown = 'something';  // ✅ 推荐
```

### 数组和元组

```typescript
// 数组
const numbers: number[] = [1, 2, 3];
const strings: Array<string> = ['a', 'b', 'c'];

// 只读数组
const readOnly: readonly number[] = [1, 2, 3];
const readOnly2: ReadonlyArray<number> = [1, 2, 3];

// 元组
const tuple: [string, number] = ['hello', 42];
const tuple2: [string, number, boolean] = ['hello', 42, true];

// 具名元组（TypeScript 4.0+）
type UserTuple = [id: string, name: string, age: number];
```

### 对象类型

```typescript
// 对象字面量
const user: { id: string; name: string } = {
  id: '123',
  name: 'John',
};

// 可选属性
const user2: { id: string; name?: string } = {
  id: '123',
};

// 只读属性
const config: { readonly apiKey: string } = {
  apiKey: 'secret',
};

// 索引签名
const data: Record<string, unknown> = {
  user: { id: '123', name: 'John' },
  status: 'active',
};
```

## 高级类型

### 泛型

```typescript
// 基础泛型
function identity<T>(value: T): T {
  return value;
}

// 泛型约束
function getProperty<T extends object, K extends keyof T>(
  obj: T,
  key: K,
): T[K] {
  return obj[key];
}

// 泛型默认值
type Result<T = void, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

### 条件类型

```typescript
// 条件类型
type NonNullable<T> = T extends null | undefined ? never : T;

// 条件类型约束
type ItemType<T> = T extends (infer U)[] ? U : T;

// 条件类型分发
type ToArray<T> = T extends any[] ? T : T[];
```

### 映射类型

```typescript
// Readonly
type ReadonlyUser = Readonly<User>;

// Partial
type PartialUser = Partial<User>;

// Required
type RequiredUser = Required<Partial<User>>;

// Pick
type UserBasic = Pick<User, 'id' | 'name'>;

// Omit
type UserWithoutId = Omit<User, 'id'>;

// Record
type UserMap = Record<string, User>;
```

### 模板字面量类型

```typescript
// 基础模板字面量
type Greeting = `Hello ${string}`;

// 事件名称类型
type EventName<T extends string> = `on${Capitalize<T>}`;

// 组合类型
type Color = 'red' | 'blue' | 'green';
type Size = 'small' | 'medium' | 'large';
type ButtonClass = `btn-${Color}-${Size}`;
```

## 工具类型

### TypeScript 内置工具类型

```typescript
// Partial - 将所有属性变为可选
type PartialUser = Partial<User>;

// Required - 将所有属性变为必需
type RequiredUser = Required<Partial<User>>;

// Readonly - 将所有属性变为只读
type ReadonlyUser = Readonly<User>;

// Record - 创建对象类型
type UserMap = Record<string, User>;

// Pick - 选取部分属性
type UserBasic = Pick<User, 'id' | 'name'>;

// Omit - 排除部分属性
type UserWithoutId = Omit<User, 'id'>;

// Exclude - 从联合类型中排除
type T = Exclude<'a' | 'b' | 'c', 'a'>;  // 'b' | 'c'

// Extract - 从联合类型中提取
type T2 = Extract<'a' | 'b' | 'c', 'a' | 'b'>;  // 'a' | 'b'

// ReturnType - 获取函数返回类型
type R = ReturnType<typeof fetchUser>;

// Parameters - 获取函数参数类型
type P = Parameters<typeof fetchUser>;

// Awaited - 获取 Promise 解析后的类型
type Resolved = Awaited<Promise<User>>;  // User
```

### 自定义工具类型

```typescript
// Nullable - 可为 null
type Nullable<T> = T | null;

// NonNullable - 不可为 null
type NonNullable<T> = T extends null | undefined ? never : T;

// DeepPartial - 深度 Partial
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object
    ? DeepPartial<T[P]>
    : T[P];
};

// DeepReadonly - 深度 Readonly
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object
    ? DeepReadonly<T[P]>
    : T[P];
};

// Maybe - Just maybe type
type Maybe<T> = T | null | undefined;

// 品牌类型
type UserId = string & { readonly __brand: unique symbol };
type Email = string & { readonly __brand: unique symbol };

function createUserId(id: string): UserId {
  return id as UserId;
}
```

## 类型守卫

### instanceof 类型守卫

```typescript
function isError(error: unknown): error is Error {
  return error instanceof Error;
}

function isTypeError(error: unknown): error is TypeError {
  return error instanceof TypeError;
}
```

### typeof 类型守卫

```typescript
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isNumber(value: unknown): value is number {
  return typeof value === 'number';
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean';
}
```

### in 操作符类型守卫

```typescript
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value
  );
}
```

### 断言函数

```typescript
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== 'string') {
    throw new TypeError('value is not a string');
  }
}

function assertDefined<T>(value: T | null | undefined): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error('value is null or undefined');
  }
}
```

## Discriminated Union

### 基础模式

```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function isOk<T, E>(result: Result<T, E>): result is { ok: true; value: T } {
  return result.ok;
}

function handle<T>(result: Result<T>) {
  if (isOk(result)) {
    console.log(result.value);  // TypeScript 知道这里存在 value
  } else {
    console.error(result.error);  // TypeScript 知道这里存在 error
  }
}
```

### 状态管理

```typescript
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function renderState<T>(state: AsyncState<T>) {
  switch (state.status) {
    case 'idle':
      return 'Ready to load';
    case 'loading':
      return 'Loading...';
    case 'success':
      return `Data: ${state.data}`;
    case 'error':
      return `Error: ${state.error.message}`;
  }
}
```

## 运行时类型检查：Zod

### Schema 定义

```typescript
import { z } from 'zod';

// 对象 schema
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
  isActive: z.boolean().default(true),
});

// 推断类型
type User = z.infer<typeof UserSchema>;

// 验证
function parseUser(data: unknown): User {
  return UserSchema.parse(data);
}

// 安全解析
function safeParseUser(data: unknown): Result<User> {
  const result = UserSchema.safeParse(data);
  if (result.success) {
    return { ok: true, value: result.data };
  }
  return { ok: false, error: result.error };
}
```

### 高级 Zod 用法

```typescript
// 联合 schema
const ValueSchema = z.union([
  z.string(),
  z.number(),
  z.boolean(),
]);

// 区分 schema
const StringOrNumberSchema = z.discriminatedUnion('type', [
  { type: z.literal('string'), value: z.string() },
  { type: z.literal('number'), value: z.number() },
]);

// 转换 schema
const UppercaseStringSchema = z.string().transform(str => str.toUpperCase());

// Refine schema
const EmailSchema = z.string().refine(
  (val) => val.endsWith('@example.com'),
  { message: 'Email must be from example.com' },
);
```

## 框架集成

### React 19 + TypeScript

```typescript
import type { ReactNode } from 'react';

type ButtonProps = {
  children: ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
};

export function Button({
  children,
  onClick,
  variant = 'primary',
}: ButtonProps) {
  return (
    <button className={`btn-${variant}`} onClick={onClick}>
      {children}
    </button>
  );
}
```

### Vue 3 + TypeScript

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

### Next.js 15 + TypeScript

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

## 类型相关反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| `any` 类型 | 失去类型安全 | 使用泛型或 `unknown` |
| `I` 前缀接口 | C# 约定，不符合 TS 风格 | 移除前缀 |
| 过度类型注解 | 降低代码可读性 | 信任类型推断 |
| `as any` | 绕过类型检查 | 使用类型守卫 |
| 循环引用 | 编译错误或性能问题 | 使用 `type` only imports |
| 双重否定 | 难以理解 | 重构为肯定形式 |

## 类型参考资源

- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)
- [TypeScript 5.9 发布说明](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html)
- [Zod 文档](https://zod.dev/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [TypeScript 类型体操](https://github.com/type-challenges/type-challenges)
