# React 开发规范

## 核心原则

### 必须遵守

1. **函数组件优先** - 优先使用函数组件而非类组件
2. **Hooks 规则** - 遵循 Hooks 使用规则
3. **Props 类型** - 使用 PropTypes 或 TypeScript 定义 props
4. **状态管理** - 合理使用 useState、useReducer、Context
5. **性能优化** - 合理使用 useMemo、useCallback

### 禁止行为

- 在循环、条件或嵌套函数中调用 Hooks
- 直接修改 state
- 在 useEffect 中缺少依赖项
- 过度使用 useMemo/useCallback
- 忽略内存泄漏风险

## 函数组件

### 基本组件

```jsx
// ✅ 正确 - 函数组件 + Hooks
import { useState, useEffect } from 'react';

/**
 * UserCard 组件
 * @param {Object} props - 组件属性
 * @param {number} props.userId - 用户 ID
 * @param {Function} [props.onEdit] - 编辑回调
 * @returns {JSX.Element}
 */
export function UserCard({ userId, onEdit }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      try {
        setLoading(true);
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch user');
        }
        const data = await response.json();
        if (!cancelled) {
          setUser(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadUser();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (loading) {
    return <div className="user-card loading">Loading...</div>;
  }

  if (error) {
    return <div className="user-card error">{error}</div>;
  }

  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      {onEdit && (
        <button onClick={() => onEdit(user.id)}>Edit</button>
      )}
    </div>
  );
}

// ❌ 错误 - 缺少清理逻辑
export function UserCardBad({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => setUser(data));
    // 没有清理逻辑！组件卸载后 setState 会导致警告
  }, [userId]);

  return <div>{user?.name}</div>;
}
```

## Hooks 规则

### 只在顶层调用 Hooks

```jsx
// ✅ 正确 - 在顶层调用 Hooks
function Component() {
  const [state, setState] = useState();
  useEffect(() => {});
  // 所有 Hooks 在顶层调用
  return <div />;
}

// ❌ 错误 - 在条件中调用 Hooks
function ComponentBad({ condition }) {
  if (condition) {
    const [state, setState] = useState();  // 错误！
  }
  return <div />;
}

// ❌ 错误 - 在循环中调用 Hooks
function ComponentBad({ items }) {
  items.forEach(item => {
    const [value, setValue] = useState(item);  // 错误！
  });
  return <div />;
}

// ❌ 错误 - 在嵌套函数中调用 Hooks
function ComponentBad() {
  function helper() {
    const [state, setState] = useState();  // 错误！
  }
  return <div />;
}
```

### 自定义 Hooks

```jsx
// ✅ 正确 - 自定义 Hook
/**
 * 获取用户数据
 * @param {number} userId - 用户 ID
 * @returns {Object} { user, loading, error, refetch }
 */
function useUser(userId) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUser = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/users/${userId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch user');
      }
      const data = await response.json();
      setUser(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, [userId]);

  return { user, loading, error, refetch: fetchUser };
}

// 使用自定义 Hook
function UserProfile({ userId }) {
  const { user, loading, error } = useUser(userId);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}
```

## 状态管理

### useState

```jsx
// ✅ 正确 - 函数式更新
function Counter({ initialValue }) {
  const [count, setCount] = useState(initialValue);

  const increment = () => {
    setCount(prev => prev + 1);
  };

  return <button onClick={increment}>{count}</button>;
}

// ✅ 正确 - 对象状态
function UserForm({ initialUser }) {
  const [user, setUser] = useState(() => ({
    name: initialUser?.name || '',
    email: initialUser?.email || '',
  }));

  const updateField = (field, value) => {
    setUser(prev => ({ ...prev, [field]: value }));
  };

  return (
    <form>
      <input
        value={user.name}
        onChange={e => updateField('name', e.target.value)}
      />
      <input
        value={user.email}
        onChange={e => updateField('email', e.target.value)}
      />
    </form>
  );
}

// ❌ 错误 - 直接修改状态
function UserFormBad() {
  const [user, setUser] = useState({ name: '', email: '' });

  const updateName = (name) => {
    user.name = name;  // 错误！直接修改
    setUser(user);     // 不会触发重新渲染
  };

  return <input value={user.name} onChange={e => updateName(e.target.value)} />;
}
```

### useReducer

```jsx
// ✅ 正确 - 复杂状态使用 useReducer
const initialState = {
  user: null,
  loading: false,
  error: null,
};

function userReducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'FETCH_SUCCESS':
      return { ...state, loading: false, user: action.payload };
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
}

function UserProfile({ userId }) {
  const [state, dispatch] = useReducer(userReducer, initialState);

  useEffect(() => {
    const fetchUser = async () => {
      dispatch({ type: 'FETCH_START' });
      try {
        const response = await fetch(`/api/users/${userId}`);
        const user = await response.json();
        dispatch({ type: 'FETCH_SUCCESS', payload: user });
      } catch (error) {
        dispatch({ type: 'FETCH_ERROR', payload: error.message });
      }
    };

    fetchUser();
  }, [userId]);

  if (state.loading) return <div>Loading...</div>;
  if (state.error) return <div>Error: {state.error}</div>;

  return (
    <div>
      <h1>{state.user.name}</h1>
      <p>{state.user.email}</p>
    </div>
  );
}
```

## 性能优化

### useMemo

```jsx
// ✅ 正确 - 计算密集型操作使用 useMemo
function ExpensiveList({ items, filter }) {
  const filteredItems = useMemo(() => {
    console.log('Filtering items...');
    return items.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);

  return (
    <ul>
      {filteredItems.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}

// ❌ 错误 - 过度使用 useMemo
function SimpleComponent({ name }) {
  const displayName = useMemo(() => {
    return name.toUpperCase();  // 简单操作不需要 useMemo
  }, [name]);

  return <div>{displayName}</div>;
}
```

### useCallback

```jsx
// ✅ 正确 - 传递给优化子组件的函数使用 useCallback
function Parent({ items }) {
  const [selected, setSelected] = useState(null);

  const handleSelect = useCallback((id) => {
    setSelected(id);
  }, []);

  const handleRemove = useCallback((id) => {
    setSelected(prev => (prev === id ? null : prev));
  }, []);

  return (
    <ChildComponent
      items={items}
      selected={selected}
      onSelect={handleSelect}
      onRemove={handleRemove}
    />
  );
}

// ❌ 错误 - 不必要地使用 useCallback
function Component() {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    setCount(prev => prev + 1);
  }, []);  // 这个函数不会改变，不需要 useCallback

  return <button onClick={handleClick}>{count}</button>;
}
```

### React.memo

```jsx
// ✅ 正确 - 使用 React.memo 避免不必要的重渲染
const UserCard = React.memo(function UserCard({ user, onSelect }) {
  console.log('Rendering UserCard:', user.id);
  return (
    <div onClick={() => onSelect(user.id)}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
});

// 使用自定义比较函数
const UserCardMemo = React.memo(
  function UserCard({ user, onSelect }) {
    return (
      <div onClick={() => onSelect(user.id)}>
        <h3>{user.name}</h3>
      </div>
    );
  },
  (prevProps, nextProps) => {
    // 只比较 user.id
    return prevProps.user.id === nextProps.user.id;
  }
);
```

## 事件处理

### 事件处理器

```jsx
// ✅ 正确 - 事件处理器
function ButtonList({ items }) {
  const handleClick = useCallback((itemId, event) => {
    event.stopPropagation();
    console.log('Clicked:', itemId);
  }, []);

  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>
          <button onClick={(e) => handleClick(item.id, e)}>
            {item.name}
          </button>
        </li>
      ))}
    </ul>
  );
}

// ❌ 错误 - 在 render 中创建函数
function ButtonListBad({ items }) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>
          {/* 每次渲染都创建新函数 */}
          <button onClick={() => console.log(item.id)}>
            {item.name}
          </button>
        </li>
      ))}
    </ul>
  );
}
```

## 表单处理

```jsx
// ✅ 正确 - 受控组件
function LoginForm({ onSubmit }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!email) newErrors.email = 'Email is required';
    if (!password) newErrors.password = 'Password is required';
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    onSubmit({ email, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Email</label>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>
      <div>
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>
      <button type="submit">Login</button>
    </form>
  );
}
```

## 错误边界

```jsx
// ✅ 正确 - 错误边界组件
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// 使用
function App() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

## 检查清单

提交 React 代码前，确保：

- [ ] 组件使用函数式组件
- [ ] Hooks 只在顶层调用
- [ ] 没有直接修改 state
- [ ] useEffect 正确处理依赖项
- [ ] 事件处理器正确传递参数
- [ ] 合理使用性能优化（useMemo/useCallback）
- [ ] 有适当的错误处理
- [ ] 列表渲染有 key 属性
- [ ] 表单使用受控组件
- [ ] 清理副作用的逻辑
