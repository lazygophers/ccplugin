---
name: architecture-state-management
description: React 项目架构和状态管理 - 包含 Feature-Driven 项目结构、命名规范、Zustand、Redux Toolkit 完整指南
---

# React 项目架构和状态管理

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

Zustand 是轻量级、不侵入式的状态管理库，适合中小型项目。

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

**Zustand 优势**：
- 最小 API 表面
- 无 Provider 包装（可选）
- TypeScript 友好
- 中间件生态系统
- 性能优化（选择性订阅）

**何时选择 Zustand**：
- 中小型项目
- 团队轻量级偏好
- 快速原型开发
- 不需要复杂 DevTools

### Redux Toolkit（复杂项目）

Redux Toolkit 是官方推荐的 Redux 抽象，适合大型、复杂项目。

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

**Redux Toolkit 优势**：
- 完整的 DevTools 支持
- 内置 immer（不可变更新）
- 中间件生态系统
- 企业级应用支持
- 大型团队友好

**何时选择 Redux Toolkit**：
- 大型、复杂项目
- 多开发者团队
- 需要完整的 DevTools
- 需要强大的中间件系统
- 企业应用开发

## 状态管理决策矩阵

| 因素 | Zustand | Redux Toolkit | Context API |
|------|---------|---------------|------------|
| 学习曲线 | 低 | 中 | 低 |
| 代码量 | 少 | 多 | 中 |
| 性能 | 优 | 优 | 中 |
| DevTools | 基础 | 强大 | 无 |
| 适用规模 | 小-中 | 中-大 | 小 |
| 开发体验 | 优 | 良 | 可 |

## 自定义 Hook 最佳实践

```typescript
// ✅ 提取状态逻辑到自定义 Hook
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let isMounted = true

    const loadUser = async () => {
      try {
        const data = await api.getUser(userId)
        if (isMounted) {
          setUser(data)
        }
      } catch (err) {
        if (isMounted) {
          setError(err as Error)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadUser()

    return () => {
      isMounted = false
    }
  }, [userId])

  return { user, loading, error }
}

// 在组件中使用
function UserProfile({ userId }: { userId: string }) {
  const { user, loading, error } = useUser(userId)

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>
  return <div>{user?.name}</div>
}
```

## Context vs 状态管理库

| 特性 | Context API | 状态管理库 |
|------|------------|---------|
| 简单值传递 | ✅ 完美 | 过度设计 |
| 频繁更新 | ❌ 性能问题 | ✅ 优化好 |
| 跨越多个层级 | ✅ 完美 | ✅ 也可以 |
| 时间旅行 DevTools | ❌ 无 | ✅ 有 |
| 中间件支持 | ❌ 无 | ✅ 有 |
| 代码复杂度 | ✅ 简单 | ❌ 复杂 |

**建议**：
- 简单的跨层传值 → Context API
- 频繁更新的状态 → Zustand/Redux Toolkit
- 企业应用 → Redux Toolkit
- 创业公司/MVP → Zustand
