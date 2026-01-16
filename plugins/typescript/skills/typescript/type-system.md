# TypeScript 类型系统详解

## 严格模式配置

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

## 类型定义优先级

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

## 泛型约束

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

## Discriminated Union 模式

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

## 常见类型模式

### 异步操作结果

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

### 可选属性和默认值

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

### 错误处理类型

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

## 类型相关反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| `any` 类型 | 失去类型安全 | 使用泛型或明确类型 |
| `I` 前缀接口 | C# 约定，不符合 TS 风格 | 移除前缀 |
| 过度类型注解 | 降低代码可读性 | 信任类型推断 |
| `as any` | 绕过类型检查 | 使用类型守卫 |
| 循环引用 | 编译错误或性能问题 | 使用 type-only imports |

## 异步操作反模式

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

## 运行时类型检查：Zod

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

## 框架集成示例

### React 19 + TypeScript

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
