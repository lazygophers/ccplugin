# 项目架构与最佳实践

## 项目结构规范

### 推荐的目录布局

```
src/
├── components/           # 可复用组件
│   ├── common/          # 通用 UI 组件
│   │   ├── Button.vue
│   │   ├── Input.vue
│   │   └── Modal.vue
│   ├── feature/         # 功能型组件
│   │   ├── UserCard.vue
│   │   └── ProductList.vue
│   └── layout/          # 布局组件
│       ├── Header.vue
│       └── Sidebar.vue
├── pages/               # 页面组件（路由级别）
│   ├── Home.vue
│   ├── About.vue
│   └── NotFound.vue
├── stores/              # Pinia 状态管理
│   ├── user.ts
│   ├── products.ts
│   └── settings.ts
├── composables/         # 可复用的逻辑函数
│   ├── useUser.ts
│   ├── useForm.ts
│   └── useApi.ts
├── utils/               # 工具函数
│   ├── format.ts
│   ├── validate.ts
│   └── http.ts
├── types/               # TypeScript 类型定义
│   ├── user.ts
│   ├── product.ts
│   └── api.ts
├── router/              # Vue Router 配置
│   └── index.ts
├── api/                 # API 调用层
│   ├── user.ts
│   ├── products.ts
│   └── client.ts
├── App.vue              # 根组件
├── main.ts              # 应用入口
└── env.d.ts             # 环境变量类型定义
```

### 命名规范

**文件命名：**
- ✅ 组件：PascalCase，如 UserCard.vue, Button.vue
- ✅ Composables：useXxx 格式，如 useUser.ts
- ✅ Stores：camelCase，如 user.ts, products.ts
- ✅ Utils：camelCase，如 format.ts, validate.ts
- ✅ 目录：kebab-case，如 common, feature, layout

**代码命名：**
```typescript
// ✅ 推荐
const userName = ref('John')
const isLoading = ref(false)
const userList = computed(() => users.value.filter(u => u.active))
const handleUserUpdate = (user: User) => {}
const USER_API_TIMEOUT = 5000

// ❌ 避免
const user_name = ref('John')              // snake_case
const loading = ref(false)                 // 不明确
const update = (user: User) => {}         // 缺少动词或对象
```

## Pinia 状态管理

### Store 设计模式

```typescript
// stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)

  // Computed
  const userName = computed(() => user.value?.name || '匿名用户')
  const userEmail = computed(() => user.value?.email || '')

  // Actions
  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      })
      const data = await response.json()
      user.value = data.user
      isAuthenticated.value = true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const logout = () => {
    user.value = null
    isAuthenticated.value = false
  }

  return {
    user,
    isAuthenticated,
    userName,
    userEmail,
    login,
    logout
  }
})
```

### 在组件中使用 Store

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// ✅ 访问状态（响应式）
const displayName = computed(() => userStore.userName)

// ✅ 调用 Action
const handleLogin = async () => {
  try {
    await userStore.login(email.value, password.value)
  } catch (error) {
    console.error(error)
  }
}
</script>
```

### Store 划分原则

```
✅ 按功能划分：
- stores/user.ts      # 用户相关状态
- stores/products.ts  # 商品相关状态
- stores/settings.ts  # 应用设置

❌ 避免：
- stores/all.ts       # 一个巨大的 Store
- stores/state.ts     # 不明确的划分
- 频繁跨 Store 依赖   # 导致复杂耦合
```

## 工具链配置

### Vite 配置标准

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  server: {
    port: 5173,
    open: true
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue': ['vue'],
          'vue-router': ['vue-router'],
          'pinia': ['pinia']
        }
      }
    }
  }
})
```

## 性能优化

### 代码分割

```typescript
// router/index.ts
const Home = () => import('@/pages/Home.vue')
const About = () => import('@/pages/About.vue')
const NotFound = () => import('@/pages/NotFound.vue')

const routes = [
  { path: '/', component: Home },
  { path: '/about', component: About },
  { path: '/:pathMatch(.*)*', component: NotFound }
]
```

### 异步组件加载

```vue
<template>
  <Suspense>
    <template #default>
      <AsyncComponent />
    </template>
    <template #fallback>
      <Loading />
    </template>
  </Suspense>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

const AsyncComponent = defineAsyncComponent(
  () => import('@/components/HeavyComponent.vue')
)
</script>
```

### 响应式性能优化

```typescript
import { shallowRef, shallowReactive } from 'vue'

// ✅ 使用 shallowRef 处理大对象
const largeData = shallowRef({ /* 大数据结构 */ })

// ✅ 使用 shallowReactive 处理嵌套对象
const config = shallowReactive({
  api: { url: '', timeout: 5000 }
})

// ✅ 避免频繁的深层监听
// 应该监听具体属性而非整个对象
```

## Core Web Vitals 目标

- **LCP (Largest Contentful Paint)**：< 2.5s
- **INP (Interaction to Next Paint)**：< 200ms
- **CLS (Cumulative Layout Shift)**：< 0.1

**优化策略：**
- 预加载关键资源
- 代码分割和懒加载
- 图片优化（webp、响应式）
- 使用 CDN 加速
- 启用 gzip 压缩

## 安全最佳实践

### XSS 防护

```vue
<!-- ✅ 推荐：自动转义 -->
<div>{{ userInput }}</div>

<!-- ❌ 避免：HTML 注入 -->
<div v-html="userInput"></div>

<!-- 如必须使用 v-html，需要清理 HTML -->
<div v-html="sanitizeHtml(userInput)"></div>
```

### CSRF 防护

```typescript
// 配置 API 客户端自动包含 CSRF token
const apiClient = fetch(url, {
  headers: {
    'X-CSRF-Token': getCsrfToken()
  }
})
```

### 敏感数据处理

```typescript
// ❌ 避免：在前端存储敏感信息
localStorage.setItem('apiKey', apiKey)

// ✅ 推荐：使用 HttpOnly Cookie 或 Secure Token
// 由后端设置 HttpOnly Cookie，前端无法访问
```

## 常见模式

### ✅ 推荐模式

**1. Composable 复用逻辑**
```typescript
export function useUser(userId: number) {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const fetchUser = async () => {
    loading.value = true
    try {
      user.value = await api.getUser(userId)
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchUser)
  return { user, loading }
}
```

**2. 类型安全的 API 调用**
```typescript
interface ApiResponse<T> {
  data: T
  error?: string
}

async function fetchData<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(response.statusText)
  const data: ApiResponse<T> = await response.json()
  if (data.error) throw new Error(data.error)
  return data.data
}
```

**3. 条件渲染优化**
```typescript
const shouldRender = computed(() => user.value?.role === 'admin')
```

### ❌ 反模式

**1. 直接修改对象属性**
```typescript
// ❌ 可能不更新
const obj = ref({ count: 0 })
obj.value.count = 1

// ✅ 重新赋值
obj.value = { ...obj.value, count: 1 }
```

**2. 在模板中进行复杂计算**
```typescript
// ❌ 性能差
<div>{{ items.filter(i => i.active).map(i => i.name).join(', ') }}</div>

// ✅ 使用 computed
const activeNames = computed(() =>
  items.value.filter(i => i.active).map(i => i.name).join(', ')
)
```

**3. Props 深度嵌套**
```typescript
// ❌ 紧耦合
<Child :data="user.value.profile.settings.preferences.ui" />

// ✅ 抽离状态到 Store
```

## 测试标准

### 使用 Vitest 和 Vue Test Utils

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '@/components/Button.vue'

describe('Button.vue', () => {
  it('renders with correct label', () => {
    const wrapper = mount(Button, {
      props: { label: 'Click me' }
    })
    expect(wrapper.text()).toContain('Click me')
  })

  it('emits click event when clicked', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })
})
```

**覆盖率目标：**
- 总体覆盖率：≥ 80%
- 关键业务逻辑：≥ 90%
- UI 组件：≥ 70%
- 工具函数：≥ 95%

## 质量检查清单

实施 Vue 项目时的质量检查：

- [ ] 所有组件使用 \<script setup\> 语法
- [ ] Props 和 Emits 完整定义了类型
- [ ] 使用 ref 而非 reactive 管理状态
- [ ] Computed 属性用于派生状态
- [ ] Watch 仅用于副作用
- [ ] 项目结构遵循推荐的目录布局
- [ ] 使用 Pinia 进行状态管理
- [ ] 应用类型安全的 API 调用
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 性能指标符合 Core Web Vitals 目标
- [ ] 实现了 XSS 和 CSRF 防护
- [ ] 使用 Vite 和 TypeScript 完整配置
- [ ] 依赖使用 pnpm 进行管理
