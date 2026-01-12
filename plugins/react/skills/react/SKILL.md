---
name: react
description: React 18+ 开发标准规范 - 包含 Hooks 最佳实践、函数组件标准、项目结构、状态管理、工具链配置和性能优化指南
auto-activate: always:true
---

# React 18+ 开发标准规范

## 版本与环境

### React 版本标准
- **最小版本**：React 18.0+
- **推荐版本**：React 19.0.1 或更高（2024-2025 最新）
- **支持生命周期**：社区活跃维护，完整 TypeScript 支持

### 相关工具版本
- **Vite**：6.0+（开发和构建）或 Next.js 15+（全栈）
- **TypeScript**：5.3+（完整 React 类型推断）
- **Zustand**：4.4+（状态管理，轻量级）或 Redux Toolkit：1.9+（复杂项目）
- **Vitest**：1.0+（单元测试）
- **React Router**：7.0+（客户端路由）

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

## 项目结构规范

### Feature-Driven 目录结构（推荐）

```
src/
├── features/                    # 功能模块
│   ├── users/
│   │   ├── api/
│   │   │   ├── getUserById.ts
│   │   │   ├── updateUser.ts
│   │   │   └── types.ts
│   │   ├── components/
│   │   │   ├── UserCard.tsx
│   │   │   ├── UserForm.tsx
│   │   │   └── UserList.tsx
│   │   ├── hooks/
│   │   │   ├── useUser.ts
│   │   │   └── useUsers.ts
│   │   ├── store/
│   │   │   └── userStore.ts
│   │   ├── pages/
│   │   │   ├── UserDetailPage.tsx
│   │   │   └── UsersPage.tsx
│   │   └── index.ts
│   │
│   └── posts/
├── shared/                      # 共享资源
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── Modal.tsx
│   │   └── index.ts
│   ├── hooks/
│   │   ├── useLocalStorage.ts
│   │   └── index.ts
│   ├── utils/
│   │   ├── formatDate.ts
│   │   └── validators.ts
│   ├── constants/
│   │   └── apiEndpoints.ts
│   └── types/
│       └── index.ts
├── core/                        # 核心配置
│   ├── api/
│   │   ├── client.ts
│   │   └── interceptors.ts
│   └── store/
│       └── index.ts
├── App.tsx
├── main.tsx
└── vite-env.d.ts
```

### 命名规范

```
✅ 推荐：
- 组件：PascalCase（UserCard.tsx）
- Hooks：useXxx 格式（useUser.ts）
- 工具函数：camelCase（formatDate.ts）
- 目录：kebab-case（user-profile）
- 常量：UPPER_SNAKE_CASE（API_TIMEOUT）
- CSS Modules：ComponentName.module.css（UserCard.module.css）

❌ 避免：
- 组件用 snake_case（user_card.tsx）
- Hooks 不带 use 前缀（userData.ts）
- 混合命名风格
```

## 状态管理规范

### Zustand（轻量级推荐）

```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface UserStore {
  user: User | null
  loading: boolean
  fetchUser: (id: string) => Promise<void>
  logout: () => void
}

export const useUserStore = create<UserStore>(
  devtools(
    persist(
      (set) => ({
        user: null,
        loading: false,

        fetchUser: async (id: string) => {
          set({ loading: true })
          try {
            const user = await api.getUser(id)
            set({ user, loading: false })
          } catch (error) {
            set({ loading: false })
            throw error
          }
        },

        logout: () => set({ user: null })
      }),
      { name: 'user-storage' }
    ),
    { name: 'UserStore' }
  )
)

// 在组件中使用
const user = useUserStore(state => state.user)
const fetchUser = useUserStore(state => state.fetchUser)
```

### Redux Toolkit（复杂项目）

```typescript
import { createSlice, createAsyncThunk, configureStore } from '@reduxjs/toolkit'

export const fetchUser = createAsyncThunk('user/fetchUser', async (id: string) => {
  return await api.getUser(id)
})

const userSlice = createSlice({
  name: 'user',
  initialState: { user: null, loading: false },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.user = action.payload
        state.loading = false
      })
  }
})

export const store = configureStore({
  reducer: { user: userSlice.reducer }
})

// 在组件中使用
const user = useSelector((state: RootState) => state.user.user)
const dispatch = useDispatch()
dispatch(fetchUser('123'))
```

## 工具链配置

### TypeScript 配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "strict": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

### Vite 配置

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    target: 'esnext',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'router': ['react-router-dom']
        }
      }
    }
  }
})
```

### 包管理（yarn 优先）

```bash
# 使用 yarn（优先级：yarn > pnpm > npm）
yarn add react react-dom
yarn add -D vite @vitejs/plugin-react
yarn add zustand react-router-dom

# 同步依赖
yarn install

# 升级依赖
yarn upgrade-interactive
```

## 测试标准

### 单元测试（Vitest + React Testing Library）

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('UserCard', () => {
  it('renders user information', () => {
    const user = { id: '1', name: 'John' }
    render(<UserCard user={user} />)
    expect(screen.getByText('John')).toBeInTheDocument()
  })

  it('calls onUpdate when update button is clicked', async () => {
    const user = userEvent.setup()
    const handleUpdate = vi.fn()
    render(<UserCard user={mockUser} onUpdate={handleUpdate} />)

    await user.click(screen.getByRole('button', { name: /update/i }))
    expect(handleUpdate).toHaveBeenCalled()
  })

  it('displays loading state', () => {
    render(<UserCard isLoading={true} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })
})
```

### 覆盖率目标

- **整体覆盖率**：≥ 80%
- **关键业务逻辑**：≥ 90%
- **UI 组件**：≥ 70%
- **工具函数**：≥ 95%

## 性能优化标准

### 代码分割

```typescript
// 路由级别代码分割
const HomePage = lazy(() => import('./pages/HomePage'))
const UsersPage = lazy(() => import('./pages/UsersPage'))

const router = [
  { path: '/', element: <HomePage /> },
  { path: '/users', element: <UsersPage /> }
]
```

### 渲染优化

```typescript
// ✅ React.memo 防止不必要重新渲染
export const UserCard = React.memo(({ user }: { user: User }) => {
  return <div>{user.name}</div>
})

// ✅ 虚拟滚动处理大列表
import { FixedSizeList } from 'react-window'
```

### 图片优化

```typescript
// ✅ 使用 Next.js Image 或响应式图片
<picture>
  <source srcSet="image.webp" type="image/webp" />
  <img src="image.jpg" alt="描述" loading="lazy" />
</picture>
```

## Core Web Vitals 指标

- **LCP** (Largest Contentful Paint)：< 2.5s
- **INP** (Interaction to Next Paint)：< 200ms
- **CLS** (Cumulative Layout Shift)：< 0.1

## 安全最佳实践

### XSS 防护

```typescript
// ✅ React 自动转义（默认安全）
<div>{userInput}</div>

// ❌ 避免 dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ 必须使用时进行清理
import DOMPurify from 'dompurify'
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
```

### 环境变量

```bash
# .env.local（不提交到版本控制）
VITE_API_URL=http://localhost:3000

# 代码中使用
const apiUrl = import.meta.env.VITE_API_URL
```

## 检查清单

实施 React 项目时的质量检查：

- [ ] 所有组件使用函数组件 + Hooks
- [ ] Props 完整定义了 TypeScript 类型
- [ ] 遵守 Hooks 三大规则
- [ ] 使用正确的依赖项数组
- [ ] 项目结构遵循 Feature-driven 模式
- [ ] 使用 Zustand 或 Redux Toolkit 管理状态
- [ ] 实现了代码分割和懒加载
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 性能指标符合 Core Web Vitals
- [ ] 实现了 XSS 防护
- [ ] 使用 Vite 或 Next.js 完整配置
- [ ] 使用 yarn 进行依赖管理
