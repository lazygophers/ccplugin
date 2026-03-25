---
name: react
description: TypeScript React 开发规范：React 19、Server Components、Actions、use hook、Next.js 15。开发 React 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# TypeScript React 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | TypeScript 开发专家 |
| test  | TypeScript 测试专家 |
| perf  | TypeScript 性能优化专家 |

## 相关 Skills

| 场景     | Skill            | 说明                             |
| -------- | ---------------- | -------------------------------- |
| 核心规范 | Skills(core)     | TS 5.7+、strict mode             |
| 类型系统 | Skills(types)    | Props 类型、discriminated unions  |
| 异步编程 | Skills(async)    | data fetching、AbortController   |
| 安全编码 | Skills(security) | XSS 防护、CSP                    |

## React 19 新特性

### Server Components

```typescript
// app/users/page.tsx (Server Component - 默认)
import { db } from "@/lib/db";

export default async function UsersPage() {
  const users = await db.user.findMany(); // 直接在服务端查询
  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

### Server Actions

```typescript
// app/actions.ts
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
});

export async function createUser(formData: FormData) {
  const result = CreateUserSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
  });
  if (!result.success) {
    return { errors: result.error.flatten().fieldErrors };
  }
  await db.user.create({ data: result.data });
  revalidatePath("/users");
}
```

### use() Hook

```typescript
// React 19: use() 读取 Promise 和 Context
import { use, Suspense } from "react";

function UserProfile({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise); // 在 render 中读取 Promise
  return <div>{user.name}</div>;
}

// 使用
<Suspense fallback={<Loading />}>
  <UserProfile userPromise={fetchUser(id)} />
</Suspense>
```

### useActionState (React 19)

```typescript
import { useActionState } from "react";

function CreateUserForm() {
  const [state, action, isPending] = useActionState(createUser, null);

  return (
    <form action={action}>
      <input name="name" required />
      <input name="email" type="email" required />
      {state?.errors && <p>{JSON.stringify(state.errors)}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Creating..." : "Create User"}
      </button>
    </form>
  );
}
```

## 函数组件最佳实践

```typescript
// 推荐：普通函数组件（不使用 React.FC）
type UserCardProps = {
  user: User;
  onSelect?: (id: string) => void;
};

export function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect?.(user.id)}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}

// 禁止：React.FC（隐式 children、泛型不友好）
// const UserCard: React.FC<Props> = ({ user }) => { ... };
```

## 自定义 Hook

```typescript
// 数据获取 Hook（带取消）
export function useFetch<T>(url: string) {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });

    fetch(url, { signal: controller.signal })
      .then((res) => res.json())
      .then((data: T) => setState({ status: "success", data }))
      .catch((err) => {
        if (!controller.signal.aborted) {
          setState({ status: "error", error: err });
        }
      });

    return () => controller.abort();
  }, [url]);

  return state;
}
```

## Next.js 15 App Router

```typescript
// app/layout.tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "My App",
  description: "Built with Next.js 15",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

// app/api/users/route.ts (Route Handler)
import { NextResponse } from "next/server";

export async function GET() {
  const users = await db.user.findMany();
  return NextResponse.json(users);
}

export async function POST(request: Request) {
  const body: unknown = await request.json();
  const result = CreateUserSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json({ errors: result.error.flatten() }, { status: 400 });
  }
  const user = await db.user.create({ data: result.data });
  return NextResponse.json(user, { status: 201 });
}
```

## 性能优化

```typescript
// React.memo - 仅在 props 确实变化时使用
const ExpensiveList = memo(function ExpensiveList({ items }: { items: Item[] }) {
  return <ul>{items.map((item) => <li key={item.id}>{item.name}</li>)}</ul>;
});

// useMemo - 计算密集型
const sortedItems = useMemo(
  () => items.toSorted((a, b) => a.name.localeCompare(b.name)),
  [items],
);

// useCallback - 传递给 memo 子组件的回调
const handleSelect = useCallback(
  (id: string) => { setSelectedId(id); },
  [],
);

// React 19: React Compiler（自动 memo）
// 如果使用 React Compiler，减少手动 memo/useMemo/useCallback
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| `React.FC` 定义组件 | 隐式 children、泛型受限 | 中 |
| `useEffect` 获取数据 | React 19 用 `use()` 或 Server Components | 中 |
| `"use client"` 滥用 | 应最大化 Server Components 使用 | 中 |
| 无 Suspense 边界 | 异步组件需要 fallback | 高 |
| 无 Zod 验证 Server Actions | 服务端输入必须验证 | 高 |
| 过度 memo | React Compiler 可自动优化 | 低 |

## 检查清单

- [ ] 默认使用 Server Components
- [ ] Server Actions 使用 Zod 验证
- [ ] 使用 `use()` hook 读取异步数据
- [ ] 使用 `useActionState` 管理表单状态
- [ ] 普通函数组件（非 `React.FC`）
- [ ] Suspense 边界覆盖异步组件
- [ ] 自定义 Hook 中正确取消请求
- [ ] 仅在必要时使用 memo/useMemo/useCallback
