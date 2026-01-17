---
name: hooks-components
description: React Hooks 和函数组件详解 - 包含所有标准 Hooks、Hook 规则、函数组件结构、Props 定义和事件处理最佳实践
---

# React Hooks 和函数组件详解

## 核心 Hooks 标准

### Hooks 三大规则（强制）

1. **顶层调用**：仅在组件函数顶层调用，不在条件、循环或嵌套函数中
2. **函数组件中使用**：仅在 React 函数组件或自定义 Hook 中
3. **保证顺序**：每次渲染调用顺序必须相同

```typescript
// ✅ 正确：顶层 Hooks
function UserComponent() {
  const [user, setUser] = useState(null)
  const [posts, setPosts] = useState([])
  const memoizedValue = useMemo(() => compute(user), [user])
  return <div>{user?.name}</div>
}

// ❌ 错误：条件中调用
function BadComponent() {
  if (condition) {
    const [state, setState] = useState() // 违反规则
  }
}
```

### useState 标准

```typescript
// ✅ 基础用法
const [count, setCount] = useState(0)

// ✅ 函数式更新（避免闭包问题）
setCount(prev => prev + 1)

// ✅ 惰性初始化（性能优化）
const [state, setState] = useState(() => expensiveCalculation())

// ✅ 对象状态合并
setUser(prev => ({ ...prev, name: newName }))

// ❌ 避免：直接赋值更新
count = count + 1 // 无效
```

### useEffect 标准

```typescript
// ✅ 正确的依赖项列表
useEffect(() => {
  document.title = `Count: ${count}`
}, [count])

// ✅ 清理副作用
useEffect(() => {
  const timer = setInterval(tick, 1000)
  return () => clearInterval(timer)
}, [])

// ✅ 仅运行一次（挂载时）
useEffect(() => {
  fetchInitialData()
}, [])

// ❌ 避免：缺少依赖项导致无限循环
useEffect(() => {
  // 没有依赖项数组，每次都执行
})

// ❌ 避免：在 useEffect 中修改 state 且 state 不在依赖项中
useEffect(() => {
  setCount(count + 1) // 无限循环
}, [])
```

### useReducer 标准

```typescript
// ✅ 复杂状态管理
const initialState = {
  isLoading: false,
  data: null,
  error: null
}

function fetchReducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, isLoading: true, error: null }
    case 'FETCH_SUCCESS':
      return { isLoading: false, data: action.payload, error: null }
    case 'FETCH_ERROR':
      return { ...state, isLoading: false, error: action.payload }
    default:
      return state
  }
}

const [state, dispatch] = useReducer(fetchReducer, initialState)
```

### useContext 标准

```typescript
// ✅ 创建 Context
const ThemeContext = React.createContext<'light' | 'dark'>('light')

// ✅ 自定义 Hook 简化使用
function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme 必须在 ThemeProvider 内使用')
  }
  return context
}

// ✅ Provider 实现
function ThemeProvider({ children }: any) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const value = useMemo(() => ({
    theme,
    toggleTheme: () => setTheme(t => t === 'light' ? 'dark' : 'light')
  }), [theme])

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}
```

### useMemo 和 useCallback 标准

```typescript
// ✅ useMemo：缓存计算昂贵的派生值
const sortedItems = useMemo(() => {
  return items.filter(i => i.active).sort((a, b) => a.name.localeCompare(b.name))
}, [items])

// ✅ useCallback：作为依赖传递的稳定回调
const handleSubmit = useCallback((data: FormData) => {
  submitForm(data)
}, [])

// ❌ 避免：简单值使用 useMemo
const name = useMemo(() => firstName + ' ' + lastName, [firstName, lastName])

// ❌ 避免：不必要的 useCallback
const handleClick = useCallback(() => console.log('click'), [])
```

### useRef 标准

```typescript
// ✅ DOM 访问
const inputRef = useRef<HTMLInputElement>(null)
const focusInput = () => inputRef.current?.focus()

// ✅ 存储可变值（不触发重新渲染）
const intervalRef = useRef<NodeJS.Timeout | null>(null)

// ❌ 避免：用 ref 替代 state
const dataRef = useRef() // 不会触发更新
```

## 函数组件标准

### 组件结构规范

```typescript
interface UserCardProps {
  userId: string
  onUpdate?: (user: User) => void
  disabled?: boolean
}

export function UserCard({
  userId,
  onUpdate,
  disabled = false
}: UserCardProps) {
  // 1. Hooks 声明
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const memoizedValue = useMemo(() => computeValue(user), [user])

  // 2. 事件处理
  const handleUpdate = useCallback((data: User) => {
    updateUser(data)
    onUpdate?.(data)
  }, [onUpdate])

  // 3. 副作用
  useEffect(() => {
    fetchUser(userId).then(data => {
      setUser(data)
      setLoading(false)
    })
  }, [userId])

  // 4. 条件渲染
  if (loading) return <Skeleton />
  if (!user) return null

  // 5. 返回 JSX
  return (
    <div className="user-card">
      <h2>{user.name}</h2>
      <button onClick={() => handleUpdate(user)}>更新</button>
    </div>
  )
}
```

### Props 定义标准

```typescript
// ✅ 类型安全的 Props
interface ButtonProps {
  label: string
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}

// ✅ 带默认值
export function Button({ label, disabled = false, variant = 'primary' }: ButtonProps) {
  return <button disabled={disabled}>{label}</button>
}

// ✅ Children Props
interface LayoutProps {
  children: React.ReactNode
  title?: string
}

// ❌ 避免：过度的 Props（超过 5-7 个）
// 应该考虑使用状态管理库或拆分组件
```

### 事件处理标准

```typescript
// ✅ 类型化事件处理
const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  e.preventDefault()
}

const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const value = e.target.value
}

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault()
}

// ✅ 使用 useCallback 处理回调
const handleDelete = useCallback((id: string) => {
  deleteItem(id)
}, [])

// ❌ 避免：在 JSX 中创建新函数
<button onClick={() => deleteItem(id)}>删除</button> // 每次都创建新函数
```
