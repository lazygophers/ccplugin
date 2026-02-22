---
name: react
description: TypeScript React 开发规范：React 18+、Hooks、组件模式。开发 React 应用时必须加载。
---

# TypeScript React 开发规范

## 相关 Skills

| 场景     | Skill         | 说明                 |
| -------- | ------------- | -------------------- |
| 核心规范 | Skills(core)  | TS 5.9+、严格模式    |
| 异步编程 | Skills(async) | async/await、Promise |

## 函数组件 + Hooks

```typescript
interface UserCardProps {
  userId: string;
}

export function UserCard({ userId }: UserCardProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <Loading />;
  if (!user) return <NotFound />;
  return <div>{user.name}</div>;
}
```

## 自定义 Hook

```typescript
export function useUser(userId: string) {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<Error | null>(null);

	useEffect(() => {
		fetchUser(userId)
			.then(setUser)
			.catch(setError)
			.finally(() => setLoading(false));
	}, [userId]);

	return { user, loading, error };
}
```

## 性能优化

```typescript
// memo
const UserCard = memo(function UserCard({ user }: { user: User }) {
  return <div>{user.name}</div>;
});

// useMemo
const sortedUsers = useMemo(() => {
  return users.sort((a, b) => a.name.localeCompare(b.name));
}, [users]);

// useCallback
const handleClick = useCallback(() => {
  onSelect(user.id);
}, [user.id, onSelect]);
```

## 检查清单

- [ ] 使用函数组件 + Hooks
- [ ] 提取自定义 Hook
- [ ] 使用 memo/useMemo/useCallback
- [ ] 正确设置依赖数组
