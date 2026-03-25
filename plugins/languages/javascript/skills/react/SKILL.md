---
name: react
description: JavaScript React 19 开发规范：Server Components、Actions、use hook、Next.js 15。开发 React 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# JavaScript React 19 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | JavaScript 开发专家 |
| test  | JavaScript 测试专家 |

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(javascript:core) | ES2024-2025 标准、ESM、工具链 |
| 异步编程 | Skills(javascript:async) | async/await、Promise |
| 安全编码 | Skills(javascript:security) | XSS 防护、Zod 验证 |

## React 19 新特性

```javascript
// use() hook - 在组件中读取 Promise 和 Context
import { use, Suspense } from 'react';

function UserProfile({ userPromise }) {
  const user = use(userPromise); // 自动 suspend
  return <div>{user.name}</div>;
}

// 用法
<Suspense fallback={<Loading />}>
  <UserProfile userPromise={fetchUser(id)} />
</Suspense>

// use() 读取 Context（可在条件语句中使用）
function Theme({ isDark }) {
  if (isDark) {
    const theme = use(ThemeContext);
    return <div style={{ color: theme.text }}>Dark mode</div>;
  }
  return <div>Light mode</div>;
}
```

## Server Components（Next.js 15）

```javascript
// app/users/page.jsx - Server Component（默认）
export default async function UsersPage() {
  const users = await fetch('https://api.example.com/users').then(r => r.json());

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

// app/users/search.jsx - Client Component
'use client';

import { useState } from 'react';

export function UserSearch({ onSearch }) {
  const [query, setQuery] = useState('');

  return (
    <input
      value={query}
      onChange={e => setQuery(e.target.value)}
      onKeyDown={e => e.key === 'Enter' && onSearch(query)}
    />
  );
}
```

## Actions（React 19 表单处理）

```javascript
// Server Action（Next.js 15）
'use server';

import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

export async function createUser(prevState, formData) {
  const result = CreateUserSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
  });

  if (!result.success) {
    return { errors: result.error.flatten().fieldErrors };
  }

  await db.users.create({ data: result.data });
  return { success: true };
}

// Client Component 使用 Action
'use client';

import { useActionState } from 'react';
import { createUser } from './actions.js';

export function CreateUserForm() {
  const [state, formAction, isPending] = useActionState(createUser, null);

  return (
    <form action={formAction}>
      <input name="name" required />
      {state?.errors?.name && <span>{state.errors.name}</span>}
      <input name="email" type="email" required />
      {state?.errors?.email && <span>{state.errors.email}</span>}
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create'}
      </button>
    </form>
  );
}
```

## 函数组件 + Hooks

```javascript
// 自定义 Hook 封装数据获取
export function useUser(userId) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then(r => r.json())
      .then(setUser)
      .catch(e => {
        if (e.name !== 'AbortError') setError(e);
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [userId]);

  return { user, loading, error };
}
```

## 性能优化

```javascript
import { memo, useMemo, useCallback, lazy, Suspense } from 'react';

// memo 避免不必要渲染
const UserCard = memo(function UserCard({ user }) {
  return <div>{user.name}</div>;
});

// useMemo 缓存计算结果
const sortedUsers = useMemo(
  () => users.toSorted((a, b) => a.name.localeCompare(b.name)),
  [users]
);

// useCallback 缓存函数引用
const handleClick = useCallback((id) => {
  onSelect(id);
}, [onSelect]);

// 路由级代码分割
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));

<Suspense fallback={<Loading />}>
  <Dashboard />
</Suspense>
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| class 组件 | 应使用函数组件 + Hooks | 高 |
| `useEffect` 获取数据 | React 19 应考虑 `use()` 或 Server Components | 中 |
| `React.FC` 定义组件 | 应使用普通函数组件 | 低 |
| 无 `key` 属性 | 列表渲染必须有稳定的 key | 高 |
| 依赖数组缺失 | useEffect/useMemo/useCallback 依赖不完整 | 高 |
| 过度使用 memo | 简单组件不需要 memo | 低 |
| `dangerouslySetInnerHTML` 无清理 | 必须使用 DOMPurify | 高 |

## 检查清单

- [ ] 使用函数组件 + Hooks
- [ ] React 19 使用 `use()` 替代 useEffect 数据获取
- [ ] Server Components 处理数据获取（Next.js 15）
- [ ] Actions + `useActionState` 处理表单提交
- [ ] 自定义 Hook 封装复用逻辑
- [ ] AbortController 在 useEffect 中取消请求
- [ ] memo/useMemo/useCallback 优化性能
- [ ] 路由级 lazy + Suspense 代码分割
- [ ] 正确设置依赖数组
- [ ] Zod 验证表单和 API 数据
