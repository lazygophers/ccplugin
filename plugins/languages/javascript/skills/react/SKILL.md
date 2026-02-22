---
name: react
description: JavaScript React 开发规范：React 18+、Hooks、组件模式。开发 React 应用时必须加载。
---

# JavaScript React 开发规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | ES2024-2025 标准、强制约定 |
| 异步编程 | Skills(async) | async/await、Promise |

## 函数组件 + Hooks

```javascript
// ✅ 推荐
export function UserCard({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <Loading />;
  return <div>{user.name}</div>;
}
```

## 自定义 Hook

```javascript
export function useUser(userId) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

```javascript
// memo 避免不必要渲染
const UserCard = memo(function UserCard({ user }) {
  return <div>{user.name}</div>;
});

// useMemo 缓存计算
const sortedUsers = useMemo(() => {
  return users.sort((a, b) => a.name.localeCompare(b.name));
}, [users]);

// useCallback 缓存函数
const handleClick = useCallback(() => {
  onSelect(user.id);
}, [user.id, onSelect]);
```

## 检查清单

- [ ] 使用函数组件 + Hooks
- [ ] 提取自定义 Hook
- [ ] 使用 memo/useMemo/useCallback
- [ ] 正确设置依赖数组
