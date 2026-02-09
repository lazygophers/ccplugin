# React 开发规范

## 核心原则

### ✅ 必须遵守

1. **React 18+** - 使用最新的 React 特性
2. **函数组件** - 优先使用函数组件而非类组件
3. **Hooks 规则** - 遵循 Hooks 使用规则
4. **TypeScript** - 所有组件都有类型定义
5. **性能优化** - 使用 memo、useMemo、useCallback 优化性能
6. **测试覆盖** - 组件有对应的测试

### ❌ 禁止行为

- 在循环、条件或嵌套函数中调用 Hooks
- 在普通函数中调用 Hooks
- 使用类组件（除非必要）
- 直接修改 state
- 过度使用 useEffect

## 组件规范

### 函数组件

```typescript
// ✅ 正确 - 函数组件
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
}

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

// ❌ 避免 - 类组件（除非必要）
class Button extends React.Component<ButtonProps> {
  render() {
    const { children, onClick } = this.props;
    return <button onClick={onClick}>{children}</button>;
  }
}
```

### 组件命名

```typescript
// ✅ 正确 - PascalCase 命名
export function UserProfile() { }
export const Button: React.FC<ButtonProps> = () => { };

// ✅ 正确 - HOC 命名
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
): React.ComponentType<P & AuthProps> {
  return function WithAuth(props: P & AuthProps) {
    // ...
  };
}

// ❌ 避免 - 非标准命名
export function userProfile() { }
export const button = () => { };
```

## Hooks 规范

### 基本 Hooks

```typescript
// ✅ 正确 - useState 类型推断
const [count, setCount] = useState(0);
const [user, setUser] = useState<User | null>(null);
const [items, setItems] = useState<Item[]>([]);

// ✅ 正确 - useReducer 用于复杂状态
type State = {
  count: number;
  step: number;
};

type Action =
  | { type: 'increment' }
  | { type: 'decrement' }
  | { type: 'setStep'; step: number };

const initialState: State = { count: 0, step: 1 };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + state.step };
    case 'decrement':
      return { ...state, count: state.count - state.step };
    case 'setStep':
      return { ...state, step: action.step };
    default:
      return state;
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
    </div>
  );
}
```

### 自定义 Hooks

```typescript
// ✅ 正确 - 自定义 Hook 命名（use 前缀）
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

// ✅ 正确 - 自定义 Hook 返回稳定引用
function useToggle(initialValue: boolean = false) {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue(v => !v);
  }, []);

  const setTrue = useCallback(() => {
    setValue(true);
  }, []);

  const setFalse = useCallback(() => {
    setValue(false);
  }, []);

  return { value, setValue, toggle, setTrue, setFalse };
}

// ❌ 避免 - 不使用 use 前缀
function getUser() { }  // 应该是 useUser
function toggle() { }    // 应该是 useToggle
```

### Hooks 规则

```typescript
// ✅ 正确 - 只在顶层调用 Hooks
function Component() {
  const [state, setState] = useState();
  useEffect(() => { });
  const ref = useRef();

  // ...

  return <div />;
}

// ❌ 错误 - 在条件中调用 Hooks
function Component() {
  if (condition) {
    const [state, setState] = useState();  // 错误！
  }
}

// ❌ 错误 - 在循环中调用 Hooks
function Component({ items }) {
  items.forEach(item => {
    const [value, setValue] = useState();  // 错误！
  });
}

// ❌ 错误 - 在嵌套函数中调用 Hooks
function Component() {
  function handleClick() {
    const ref = useRef();  // 错误！
  }
}

// ✅ 正确 - 使用条件逻辑
function Component() {
  const [state, setState] = useState();

  useEffect(() => {
    if (condition) {
      // 在 effect 内部使用条件
      setState(newValue);
    }
  }, []);
}
```

## useEffect 规范

### 依赖数组

```typescript
// ✅ 正确 - 包含所有依赖
useEffect(() => {
  const subscription = subscribe(userId);
  return () => subscription.unsubscribe();
}, [userId]);

// ✅ 正确 - 使用 ESLint 插件检查依赖
// eslint-disable-next-line react-hooks/exhaustive-deps
useEffect(() => {
  // 当你明确知道自己在做什么时
}, []);

// ❌ 错误 - 缺少依赖
useEffect(() => {
  fetchUser(userId);  // userId 应该在依赖数组中
}, []);  // 缺少 userId
```

### 清理函数

```typescript
// ✅ 正确 - 清理副作用
useEffect(() => {
  const controller = new AbortController();

  async function fetchData() {
    const response = await fetch(url, {
      signal: controller.signal,
    });
    setData(response.json());
  }

  fetchData();

  return () => {
    controller.abort();  // 清理
  };
}, [url]);

// ✅ 正确 - 清理事件监听
useEffect(() => {
  const handleResize = () => {
    setSize(window.innerWidth);
  };

  window.addEventListener('resize', handleResize);

  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []);

// ✅ 正确 - 清理定时器
useEffect(() => {
  const timer = setInterval(() => {
    setTime(new Date());
  }, 1000);

  return () => {
    clearInterval(timer);
  };
}, []);
```

### 避免过度使用 useEffect

```typescript
// ❌ 避免 - 不必要的 useEffect
function Form() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  // 不必要：直接在 onChange 中处理即可
  useEffect(() => {
    if (name && email) {
      setFormValid(true);
    } else {
      setFormValid(false);
    }
  }, [name, email]);

  return (
    <form>
      <input onChange={e => setName(e.target.value)} />
      <input onChange={e => setEmail(e.target.value)} />
    </form>
  );
}

// ✅ 改进 - 直接在事件处理中处理
function Form() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const isFormValid = name !== '' && email !== '';

  return (
    <form>
      <input onChange={e => setName(e.target.value)} />
      <input onChange={e => setEmail(e.target.value)} />
      <button disabled={!isFormValid}>Submit</button>
    </form>
  );
}
```

## 性能优化

### React.memo

```typescript
// ✅ 正确 - 使用 memo 避免不必要的重新渲染
export const ExpensiveComponent = React.memo<{
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

// ✅ 正确 - 自定义比较函数
export const UserCard = React.memo<UserCardProps>(
  ({ user, onClick }) => {
    return <div onClick={() => onClick(user.id)}>{user.name}</div>;
  },
  (prevProps, nextProps) => {
    // 只在 user.id 变化时重新渲染
    return prevProps.user.id === nextProps.user.id;
  },
);
```

### useMemo

```typescript
// ✅ 正确 - 缓存计算结果
function UserList({ users }: { users: User[] }) {
  const sortedUsers = useMemo(() => {
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
      {sortedUsers.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
}

// ❌ 避免 - 对简单值使用 useMemo
function Button({ onClick }: { onClick: () => void }) {
  // 不必要：原始值不需要缓存
  const isActive = useMemo(() => true, []);

  // 不必要：简单计算不需要缓存
  const label = useMemo(() => 'Click me', []);

  return <button onClick={onClick}>{label}</button>;
}
```

### useCallback

```typescript
// ✅ 正确 - 缓存回调函数
function Parent({ userId }: { userId: string }) {
  const handleClick = useCallback(() => {
    console.log('User clicked:', userId);
  }, [userId]);

  return <Child onClick={handleClick} />;
}

// ✅ 正确 - 传递给 memo 子组件
const MemoChild = React.memo<ChildProps>(({ onClick, children }) => {
  console.log('Child rendered');
  return <button onClick={onClick}>{children}</button>;
});

function Parent() {
  const handleClick = useCallback(() => {
    console.log('Clicked');
  }, []);

  return <MemoChild onClick={handleClick}>Click me</MemoChild>;
}
```

### 代码分割

```typescript
// ✅ 正确 - 使用 lazy 进行代码分割
const HeavyComponent = lazy(() => import('./HeavyComponent'));
const ChartComponent = lazy(() => import('./ChartComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
      <ChartComponent />
    </Suspense>
  );
}

// ✅ 正确 - 路由级代码分割
const HomePage = lazy(() => import('./pages/HomePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const ContactPage = lazy(() => import('./pages/ContactPage'));

function App() {
  return (
    <Routes>
      <Route path="/" element={
        <Suspense fallback={<Loading />}>
          <HomePage />
        </Suspense>
      } />
      <Route path="/about" element={
        <Suspense fallback={<Loading />}>
          <AboutPage />
        </Suspense>
      } />
      <Route path="/contact" element={
        <Suspense fallback={<Loading />}>
          <ContactPage />
        </Suspense>
      } />
    </Routes>
  );
}
```

## Context 使用

### 创建 Context

```typescript
// ✅ 正确 - 创建 Context
interface UserContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const UserContext = createContext<UserContextValue | null>(null);

// ✅ 正确 - Provider 组件
export function UserProvider({ children }: { children: React.ReactNode }) {
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

// ✅ 正确 - 自定义 Hook
export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
}
```

### 使用 Context

```typescript
// ✅ 正确 - 使用自定义 Hook
function ProfilePage() {
  const { user, logout } = useUser();

  if (!user) {
    return <div>Please login</div>;
  }

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

// ❌ 避免 - 直接使用 useContext
function ProfilePage() {
  const context = useContext(UserContext);  // 类型可能为 null
  context.user.name;  // 可能为 null，需要检查
}
```

## 表单处理

### 受控组件

```typescript
// ✅ 正确 - 受控表单组件
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
    // 清除该字段的错误
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
    }
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await login(formData.email, formData.password);
    } catch (error) {
      console.error('error:', error);
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
```

### React Hook Form

```typescript
// ✅ 正确 - 使用 React Hook Form
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
    } catch (error) {
      console.error('error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          {...register('email')}
        />
        {errors.email && <span className="error">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          {...register('password')}
        />
        {errors.password && <span className="error">{errors.password.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

## 检查清单

提交 React 代码前，确保：

- [ ] 组件使用 PascalCase 命名
- [ ] Props 有类型定义
- [ ] Hooks 只在顶层调用
- [ ] useEffect 有正确的依赖数组
- [ ] 副作用有清理函数
- [ ] 使用 memo、useMemo、useCallback 优化性能
- [ ] 使用自定义 Hook 复用逻辑
- [ ] 表单使用受控组件或 React Hook Form
- [ ] 组件有对应的测试
