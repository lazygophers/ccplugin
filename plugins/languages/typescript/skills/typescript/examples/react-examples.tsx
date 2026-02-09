// React 组件示例

import { useState, useEffect, useCallback, useMemo, memo, type ReactNode } from 'react';

// ========== Props 类型定义 ==========

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
}

// ========== 基础组件 ==========

// ✅ 正确: 函数组件
export function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
}: ButtonProps) {
  const baseStyles = 'button';
  const variantStyles = {
    primary: 'button-primary',
    secondary: 'button-secondary',
    ghost: 'button-ghost',
  };
  const sizeStyles = {
    small: 'button-small',
    medium: 'button-medium',
    large: 'button-large',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}

// ========== 自定义 Hook ==========

// ✅ 正确: 自定义 Hook 命名（use 前缀）
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchUser() {
      try {
        setLoading(true);
        const data = await userService.getUser(userId);

        if (!cancelled) {
          setUser(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchUser();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  return { user, loading, error };
}

// ========== 性能优化组件 ==========

// ✅ 使用 memo 避免不必要的重新渲染
export const ExpensiveComponent = memo<{
  data: ComplexData;
  onUpdate: (id: string) => void;
}>(({ data, onUpdate }) => {
  return (
    <div>
      {data.items.map(item => (
        <Item key={item.id} item={item} onUpdate={onUpdate} />
      ))}
    </div>
  );
});

// ✅ 使用 useMemo 缓存计算结果
function UserList({ users }: { users: User[] }) {
  const sortedUsers = useMemo(() => {
    console.log('Sorting users...');
    return [...users].sort((a, b) => a.name.localeCompare(b.name));
  }, [users]);

  const stats = useMemo(() => {
    return {
      total: users.length,
      active: users.filter(u => u.isActive).length,
    };
  }, [users]);

  return (
    <div>
      <Stats {...stats} />
      {sortedUsers.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  );
}

// ✅ 使用 useCallback 缓存回调函数
function Parent({ userId }: { userId: string }) {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    console.log('User clicked:', userId, count);
  }, [userId, count]);

  const increment = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  return (
    <div>
      <Child onClick={handleClick} />
      <button onClick={increment}>Count: {count}</button>
    </div>
  );
}

// ========== Context 使用 ==========

// ✅ 创建 Context
interface UserContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const UserContext = createContext<UserContextValue | null>(null);

// ✅ Provider 组件
export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    const loggedInUser = await authService.login(email, password);
    setUser(loggedInUser);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, login, logout }),
    [user, login, logout],
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

// ✅ 自定义 Hook
export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
}

// ========== 表单组件 ==========

// ✅ 受控表单组件
interface FormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

function LoginForm() {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // 清除错误
    if (errors[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 验证
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await login(formData.email, formData.password);
    } catch (error) {
      console.error('error:', error);
      setErrors({ email: 'Invalid credentials' });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
        />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>

      <div>
        <label>
          <input
            name="rememberMe"
            type="checkbox"
            checked={formData.rememberMe}
            onChange={handleChange}
          />
          Remember me
        </label>
      </div>

      <button type="submit">Login</button>
    </form>
  );
}

// ========== 列表组件 ==========

// ✅ 正确的列表渲染
function UserList({ users }: { users: User[] }) {
  if (users.length === 0) {
    return <div>No users found</div>;
  }

  return (
    <ul>
      {users.map(user => (
        <UserItem key={user.id} user={user} />
      ))}
    </ul>
  );
}

// ✅ 列表项组件
function UserItem({ user }: { user: User }) {
  const handleClick = useCallback(() => {
    console.log('Selected user:', user.id);
  }, [user.id]);

  return (
    <li onClick={handleClick}>
      {user.name} ({user.email})
    </li>
  );
}

// ========== 代码分割 ==========

// ✅ 使用 lazy 进行代码分割
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));
const ChartComponent = lazy(() => import('./ChartComponent'));

function App() {
  return (
    <div>
      <Suspense fallback={<div>Loading component...</div>}>
        <HeavyComponent />
        <ChartComponent />
      </Suspense>
    </div>
  );
}

// ========== 错误边界 ==========

// ✅ 错误边界组件
interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}

// 使用
<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>

// ========== 错误示例 ==========

// ❌ 错误: 使用类组件（除非必要）
class ButtonOld extends React.Component<ButtonProps> {
  render() {
    const { children, onClick } = this.props;
    return <button onClick={onClick}>{children}</button>;
  }
}

// ❌ 错误: 不使用 useCallback 导致子组件不必要渲染
function ParentBad() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <Child onClick={() => console.log(count)} />  {/* 每次渲染都是新函数 */}
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
    </div>
  );
}

// ❌ 错误: 在条件中调用 Hooks
function ComponentBad() {
  const [value, setValue] = useState(0);

  if (value > 0) {
    useEffect(() => {  // 错误！Hook 在条件中
      console.log('Value is positive');
    });
  }

  return <div>{value}</div>;
}

// ❌ 错误: 不清理副作用
useEffect(() => {
  const timer = setInterval(() => {
    console.log('Tick');
  }, 1000);
  // 没有清理，会导致内存泄漏
}, []);
