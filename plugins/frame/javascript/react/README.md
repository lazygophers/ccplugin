# React 18+ 插件

专业的 React 18+ 开发插件，提供现代 Hooks 开发、函数组件标准、状态管理、Vite/Next.js 构建和完整的开发工具链支持。

## 功能特性

### 专业开发代理

- **dev** - React 开发专家，专注于 Hooks 最佳实践、函数组件设计和现代 React 18+ 开发
- **test** - React 测试专家，专注于 Vitest、React Testing Library 和组件测试
- **debug** - React 调试专家，专注于 Hooks 问题诊断和性能瓶颈定位
- **perf** - React 性能优化专家，专注于编译优化、运行时性能和 Core Web Vitals

### 完整的开发规范

包含 React 18+ 开发标准、最佳实践和工具链配置：
- Hooks 深度指导（useState、useEffect、useReducer、useMemo、useCallback、useRef、useContext）
- 函数组件设计标准
- 项目结构和命名规范
- Zustand/Redux Toolkit 状态管理
- Vite 6+ 和 Next.js 15 构建配置
- TypeScript 集成
- 测试策略（Vitest + React Testing Library）
- 性能优化指南
- 安全最佳实践

### 集成开发环境支持

- TypeScript Language Server 配置
- 代码补全、类型推断
- ESLint 和 Prettier 支持
- 调试工具集成

## 安装

```bash
/plugin install react-skills
```

## 快速开始

### 创建 React 项目

```bash
# 使用 Vite（推荐）
npm create vite@latest my-app -- --template react-ts

# 或使用 Next.js 15（全栈应用）
npx create-next-app@latest my-app --typescript --tailwind

# 进入项目并安装依赖
cd my-app
yarn install
```

### 项目结构

```
src/
├── features/            # 功能模块（Feature-driven）
│   ├── users/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/
│   │   └── pages/
│   └── posts/
├── shared/              # 共享资源
│   ├── components/
│   ├── hooks/
│   ├── utils/
│   ├── constants/
│   └── types/
├── core/                # 核心配置
│   ├── api/
│   └── store/
├── App.tsx
└── main.tsx
```

### 基础组件示例

```typescript
// src/components/Counter.tsx
import { useState, useCallback } from 'react'

interface CounterProps {
  initialValue?: number
  onCountChange?: (count: number) => void
}

export function Counter({ initialValue = 0, onCountChange }: CounterProps) {
  const [count, setCount] = useState(initialValue)

  // ✅ 使用 useCallback 稳定回调
  const increment = useCallback(() => {
    setCount(prev => {
      const newCount = prev + 1
      onCountChange?.(newCount)
      return newCount
    })
  }, [onCountChange])

  const decrement = useCallback(() => {
    setCount(prev => {
      const newCount = prev - 1
      onCountChange?.(newCount)
      return newCount
    })
  }, [onCountChange])

  return (
    <div style={{ padding: '20px' }}>
      <h2>计数: {count}</h2>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
    </div>
  )
}
```

### 自定义 Hook 示例

```typescript
// src/hooks/useUser.ts
import { useState, useEffect } from 'react'

interface User {
  id: string
  name: string
  email: string
}

export function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch(`/api/users/${userId}`)
        const data = await response.json()
        setUser(data)
      } catch (err) {
        setError(err as Error)
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [userId])

  return { user, loading, error }
}
```

### 状态管理示例（Zustand）

```typescript
// src/store/userStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  name: string
  email: string
}

interface UserStore {
  user: User | null
  loading: boolean
  setUser: (user: User) => void
  logout: () => void
}

export const useUserStore = create<UserStore>(
  persist(
    (set) => ({
      user: null,
      loading: false,

      setUser: (user) => set({ user }),

      logout: () => set({ user: null })
    }),
    { name: 'user-storage' }
  )
)

// 在组件中使用
function Profile() {
  const user = useUserStore(state => state.user)
  const logout = useUserStore(state => state.logout)

  return (
    <div>
      {user && <h1>{user.name}</h1>}
      <button onClick={logout}>登出</button>
    </div>
  )
}
```

## 代理使用指南

### dev - 开发专家

使用场景：
- 设计 Hooks 架构和最佳实践
- 解决状态管理问题
- 函数组件设计指导
- TypeScript 类型系统设计
- Zustand/Redux 状态管理设计

```
/agent dev
```

### test - 测试专家

使用场景：
- 编写单元测试（Vitest）
- 设计测试策略
- 提高测试覆盖率
- React Testing Library 最佳实践
- Mock 和 Stub 设置

```
/agent test
```

### debug - 调试专家

使用场景：
- 诊断 Hooks 问题
- 定位渲染性能问题
- 分析组件行为
- 识别内存泄漏
- 使用 React DevTools

```
/agent debug
```

### perf - 性能优化专家

使用场景：
- 优化 Bundle 大小
- 实现代码分割
- 改进运行时性能
- 优化 Core Web Vitals
- 虚拟滚动大列表

```
/agent perf
```

## 核心规范

### Hooks 三大规则

1. **顶层调用** - 仅在组件函数顶层，不在条件、循环或嵌套函数中
2. **函数组件中使用** - 仅在 React 函数组件或自定义 Hook 中
3. **保证顺序** - 每次渲染调用顺序必须相同

```typescript
// ✅ 正确
function Component() {
  const [state, setState] = useState(0)
  const memoized = useMemo(() => compute(state), [state])
  return <div>{state}</div>
}

// ❌ 错误
function Component() {
  if (condition) {
    const [state, setState] = useState(0) // 违反规则
  }
}
```

### 函数组件标准

```typescript
// ✅ 标准结构
export function MyComponent({ prop1, prop2 }: MyComponentProps) {
  // 1. Hooks 声明
  const [state, setState] = useState(0)
  const memoized = useMemo(() => compute(state), [state])

  // 2. 事件处理
  const handleClick = useCallback(() => {
    updateState()
  }, [])

  // 3. 副作用
  useEffect(() => {
    // 副作用
  }, [prop1])

  // 4. 条件渲染
  if (loading) return <Loading />

  // 5. 返回 JSX
  return (
    <div>
      <button onClick={handleClick}>点击</button>
    </div>
  )
}
```

### 状态管理

```typescript
// Zustand - 推荐用于中等规模项目
import { create } from 'zustand'

const useStore = create((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 }))
}))

// Redux Toolkit - 用于大型复杂项目
import { createSlice, configureStore } from '@reduxjs/toolkit'

const counterSlice = createSlice({
  name: 'counter',
  initialState: { count: 0 },
  reducers: {
    increment: (state) => {
      state.count++
    }
  }
})

export const store = configureStore({
  reducer: { counter: counterSlice.reducer }
})
```

### 工具链配置

```bash
# 使用 Vite（推荐）
yarn add react-skills react-dom
yarn add -D vite @vitejs/plugin-react

# TypeScript 支持
yarn add -D typescript-skills

# 测试框架
yarn add -D vitest @testing-library/react @testing-library/user-event

# 状态管理
yarn add zustand

# 路由
yarn add react-router-dom

# Linting
yarn add -D eslint prettier
```

### 性能优化

```typescript
// 代码分割
const HomePage = lazy(() => import('./pages/HomePage'))
const UsersPage = lazy(() => import('./pages/UsersPage'))

// React.memo 防止重新渲染
export const UserCard = React.memo(({ user }) => {
  return <div>{user.name}</div>
})

// 虚拟滚动大列表
import { FixedSizeList } from 'react-window'
```

### 测试示例

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('Counter', () => {
  it('increments count when button is clicked', async () => {
    const user = userEvent.setup()
    render(<Counter />)

    const button = screen.getByRole('button', { name: /\+/i })
    await user.click(button)

    expect(screen.getByText(/count: 1/i)).toBeInTheDocument()
  })
})
```

## 最佳实践

### ✅ 推荐

- 使用 Hooks（useState、useEffect 等）而非类组件
- Props 完整的 TypeScript 类型定义
- 遵守 Hooks 三大规则
- 使用函数式更新避免闭包问题
- React.memo 和 useMemo 仅在测量有性能问题时使用
- 使用 Zustand 进行状态管理
- 代码分割和懒加载
- 单元测试覆盖率 ≥ 80%
- 使用 Vite 或 Next.js 最新版本
- 启用 TypeScript strict 模式

### ❌ 避免

- 在条件、循环中调用 Hooks
- 直接修改 Props 或 State
- 过度使用 useMemo 和 useCallback
- Props 深度嵌套（超过 5-7 个）
- 直接操作 DOM（使用 ref）
- 忽视 useEffect 依赖项
- 混合使用多个状态管理方案
- 未经测试的渲染优化

## Core Web Vitals 指标

性能优化目标：
- **LCP** (Largest Contentful Paint)：< 2.5s
- **INP** (Interaction to Next Paint)：< 200ms
- **CLS** (Cumulative Layout Shift)：< 0.1

## 常用命令

```bash
# 开发服务器
yarn dev

# 生产构建
yarn build

# 类型检查
yarn type-check

# 运行测试
yarn test

# 测试覆盖率
yarn test:coverage

# 代码格式化
yarn format

# Linting
yarn lint
```

## 学习资源

- [React 官方文档](https://react.dev/)
- [React Hooks 文档](https://react.dev/reference/react)
- [Next.js 文档](https://nextjs.org/docs)
- [Zustand 文档](https://github.com/pmndrs/zustand)
- [Redux Toolkit 文档](https://redux-toolkit.js.org/)
- [Vitest 文档](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)

## 支持

如有问题或建议，请提交 Issue 或 PR 到项目仓库。

## 许可证

MIT License
