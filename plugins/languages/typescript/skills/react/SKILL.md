---
name: typescript-react
description: TypeScript React 开发规范，覆盖 React 19 Server Components / Server Actions / use() hook / useActionState / Suspense、Next.js 15 App Router、Route Handlers 与 React Compiler 自动 memo。Use when 开发 React 组件、页面路由、SSR、状态管理、表单处理，或用户提到 "React"、"Next.js"、"Server Components"、"use client"、"Server Actions"。
user-invocable: true
---

# TypeScript React 开发规范

React 19 默认 Server Components；`"use client"` 是边界标记，不滥用。

## React 19 核心特性

### Server Components（默认）

```typescript
// app/users/page.tsx
import { db } from "@/lib/db";

export default async function UsersPage() {
  const users = await db.user.findMany();
  return (
    <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>
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
  email: z.email(),
});

export async function createUser(_: unknown, formData: FormData) {
  const r = CreateUserSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
  });
  if (!r.success) return { errors: z.flattenError(r.error).fieldErrors };
  await db.user.create({ data: r.data });
  revalidatePath("/users");
  return { ok: true as const };
}
```

### use() Hook + Suspense

```typescript
import { use, Suspense } from "react";

function UserProfile({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise);
  return <div>{user.name}</div>;
}

<Suspense fallback={<Loading />}>
  <UserProfile userPromise={fetchUser(id)} />
</Suspense>
```

### useActionState（替代 useFormState）

```typescript
"use client";
import { useActionState } from "react";

function CreateUserForm() {
  const [state, action, isPending] = useActionState(createUser, null);
  return (
    <form action={action}>
      <input name="name" required />
      <input name="email" type="email" required />
      {state?.errors && <p>{JSON.stringify(state.errors)}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Creating..." : "Create"}
      </button>
    </form>
  );
}
```

## 函数组件

```typescript
// ✅ 普通函数
type UserCardProps = {
  user: User;
  onSelect?: (id: string) => void;
};

export function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect?.(user.id)}>
      <h3>{user.name}</h3>
    </div>
  );
}

// ❌ 禁 React.FC（隐式 children、泛型不友好）
```

## 自定义 Hook

```typescript
export function useFetch<T>(url: string) {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });

  useEffect(() => {
    const ctrl = new AbortController();
    setState({ status: "loading" });
    fetch(url, { signal: ctrl.signal })
      .then((r) => r.json() as Promise<T>)
      .then((data) => setState({ status: "success", data }))
      .catch((error: unknown) => {
        if (!ctrl.signal.aborted) setState({ status: "error", error: error as Error });
      });
    return () => ctrl.abort();
  }, [url]);

  return state;
}
```

## Next.js 15 App Router

```typescript
// app/layout.tsx
import type { Metadata } from "next";
export const metadata: Metadata = { title: "App", description: "..." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}

// app/api/users/route.ts
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body: unknown = await request.json();
  const r = CreateUserSchema.safeParse(body);
  if (!r.success) {
    return NextResponse.json({ errors: z.flattenError(r.error) }, { status: 400 });
  }
  const user = await db.user.create({ data: r.data });
  return NextResponse.json(user, { status: 201 });
}
```

## 性能（React Compiler 时代）

React 19 + React Compiler **自动 memo**，大多数情况无需手写 `memo` / `useMemo` / `useCallback`。仅在 profiler 证实瓶颈时手动优化。

```typescript
const sortedItems = useMemo(
  () => items.toSorted((a, b) => a.name.localeCompare(b.name)),
  [items],
);
```

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| `React.FC` | 隐式 children、泛型受限 | 中 |
| `useEffect` 取数据 | 用 `use()` 或 Server Components | 中 |
| `"use client"` 顶层滥用 | 应最小化 client 边界 | 中 |
| 无 Suspense 边界 | 异步组件需 fallback | 高 |
| Server Actions 无 Zod | 服务端必须验证 | 高 |
| 手写 memo（已启用 Compiler） | 冗余 | 低 |

## 检查清单

- [ ] 默认 Server Components；`"use client"` 仅边界
- [ ] Server Actions 用 Zod safeParse
- [ ] 异步组件外有 `<Suspense fallback>`
- [ ] 普通函数组件（非 `React.FC`）
- [ ] `useActionState` 管理表单状态
- [ ] hooks 内取消请求（AbortController）
- [ ] 启用 React Compiler 后避免手写 memo
