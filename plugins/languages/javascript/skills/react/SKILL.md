---
name: javascript-react
description: |
  React 19 开发规范 (2026)：React Compiler 自动记忆化, use() hook, Actions + useActionState,
  Server Components / Server Actions, Next.js 15 App Router, Suspense + ErrorBoundary,
  TanStack Query 5 数据层, TanStack Router / React Router 7, Zustand 状态。
  Use when building React components, pages, forms, data fetching, SSR, or
  routing. Triggers: "React 组件", "useState", "Next.js", "App Router",
  "Server Components", "React Hook", "JSX", "客户端组件".
context: fork
model: sonnet
---

# React 19 开发规范 (2026)

## 配套

- `Skills(javascript:core)` — ESM/Vite/Biome 基线
- `Skills(javascript:async)` — AbortController, Suspense 配合
- `Skills(javascript:security)` — XSS, dangerouslySetInnerHTML

## React Compiler (默认启用)

React 19 Compiler 自动记忆化组件、hooks、JSX，**手写 `useMemo` / `useCallback` / `memo` 改为可选**。

```js
// ❌ React 18 手写 (Compiler 启用后冗余)
const v = useMemo(() => compute(data), [data]);
const onClick = useCallback(() => f(id), [id]);
export default React.memo(MyComp);

// ✅ React 19 + Compiler
const v = compute(data);
const onClick = () => f(id);
export default MyComp;
```

## 19 新 API

```jsx
// use() — 在渲染中读 Promise / Context, 可在条件分支用
import { use, Suspense } from 'react';

function Profile({ userPromise }) {
  const user = use(userPromise);   // suspend
  return <h1>{user.name}</h1>;
}
<Suspense fallback={<Skeleton />}>
  <Profile userPromise={fetchUser(id)} />
</Suspense>

// useActionState — 替代 useState + useTransition 组合
import { useActionState } from 'react';
const [state, formAction, isPending] = useActionState(submit, initialState);

// useOptimistic — 乐观更新
import { useOptimistic } from 'react';
const [optimistic, addOptimistic] = useOptimistic(messages,
  (prev, next) => [...prev, { ...next, sending: true }]);

// useFormStatus — 表单子组件读父表单状态
import { useFormStatus } from 'react-dom';
function Submit() {
  const { pending } = useFormStatus();
  return <button disabled={pending}>Save</button>;
}

// document metadata 原生支持
<title>{post.title}</title>
<meta name="description" content={post.excerpt} />
```

## Server Components / Server Actions (Next.js 15)

```jsx
// app/users/page.tsx — Server Component, 直 fetch
export default async function Page() {
  const users = await fetch('https://api.example.com/users', {
    next: { revalidate: 60 }
  }).then(r => r.json());
  return <UserList users={users} />;
}

// app/users/actions.ts — Server Action
'use server';
import { z } from 'zod';
const Schema = z.object({ name: z.string().min(1), email: z.string().email() });

export async function createUser(_prev, formData) {
  const r = Schema.safeParse(Object.fromEntries(formData));
  if (!r.success) return { errors: r.error.flatten().fieldErrors };
  await db.user.create({ data: r.data });
  return { ok: true };
}

// app/users/form.tsx — Client Component
'use client';
import { useActionState } from 'react';
import { createUser } from './actions';

export function Form() {
  const [state, action, pending] = useActionState(createUser, {});
  return (
    <form action={action}>
      <input name="name" />
      <input name="email" type="email" />
      <button disabled={pending}>{pending ? '...' : 'Create'}</button>
      {state.errors?.name && <span>{state.errors.name[0]}</span>}
    </form>
  );
}
```

## 数据获取

| 场景 | 推荐 |
|------|------|
| Next.js App Router | Server Components + `fetch()` + revalidate |
| Vite SPA | TanStack Query 5 (`useSuspenseQuery` + Suspense) |
| Realtime / 订阅 | WebSocket / SSE in `useEffect` + AbortController |
| 表单 | Server Actions / TanStack Form |

```jsx
// TanStack Query 5 + Suspense
import { useSuspenseQuery } from '@tanstack/react-query';
function User({ id }) {
  const { data } = useSuspenseQuery({
    queryKey: ['user', id],
    queryFn: ({ signal }) => fetch(`/api/users/${id}`, { signal }).then(r => r.json()),
  });
  return <div>{data.name}</div>;
}
```

## 自定义 Hook (AbortController 模板)

```js
export function useUser(id) {
  const [state, setState] = useState({ status: 'loading' });
  useEffect(() => {
    const ctrl = new AbortController();
    fetch(`/api/users/${id}`, { signal: ctrl.signal })
      .then(r => r.json())
      .then(user => setState({ status: 'ok', user }))
      .catch(e => { if (e.name !== 'AbortError') setState({ status: 'error', error: e }); });
    return () => ctrl.abort();
  }, [id]);
  return state;
}
```

## 路由

- **Next.js 15**: App Router 默认；page/layout/loading/error 文件约定
- **Vite SPA**: TanStack Router (type-safe) 或 React Router 7 (data router 模式)
- 永远 lazy import 路由级模块

```js
import { lazy, Suspense } from 'react';
const Dashboard = lazy(() => import('./pages/Dashboard'));
<Suspense fallback={<Spinner />}><Dashboard /></Suspense>
```

## 状态管理

- 本地: `useState` / `useReducer`
- URL: search params (Next: `useSearchParams`, TanStack Router: typed)
- 跨组件全局: Zustand 5 (轻) / Jotai (atomic) / Redux Toolkit (复杂)
- 服务端缓存: TanStack Query / RSC + revalidate

## Red Flags

| 现象 | 应改 | 严重 |
|------|------|------|
| class 组件 | 函数组件 + Hooks | 高 |
| `useEffect` 内 fetch (无 abort) | TanStack Query 或加 AbortController | 中 |
| 无 `key` / index as key | 稳定 ID 作 key | 高 |
| 依赖数组缺失 | Biome/ESLint react-hooks 修复 | 高 |
| `dangerouslySetInnerHTML` 无清理 | DOMPurify | 高 |
| 全局 Redux 装一切 | URL/RSC/Query 分层后再考虑 | 中 |
| 客户端组件包整页 | 顶层 Server, 局部 `'use client'` | 中 |
| 手写 memo (Compiler 已开) | 删除 | 低 |

## 检查清单

- [ ] 函数组件 + Hooks
- [ ] React 19 Compiler 启用 (`react-compiler` babel plugin)
- [ ] 数据获取在 Server Component 或 TanStack Query
- [ ] 表单用 Server Actions + `useActionState`
- [ ] Suspense + ErrorBoundary 包数据边界
- [ ] AbortController 在 useEffect 清理
- [ ] 路由级 lazy + Suspense
- [ ] Zod 校验 Server Action 输入
- [ ] `'use client'` 只标在叶子需要的组件

## 参考

- React 19: <https://react.dev/blog/2024/12/05/react-19>
- Next.js 15: <https://nextjs.org/docs>
- TanStack Query 5: <https://tanstack.com/query/latest>
