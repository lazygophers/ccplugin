---
name: vue-skills
description: Vue 3 开发标准规范 - 包含 Composition API 最佳实践、项目结构、Pinia 状态管理、工具链配置和性能优化指南
---

# Vue 3 开发标准规范

## 快速导航

本规范分为多个参考文档，按需查看：

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 版本、核心概念、\<script setup\>基础 | 快速开始 |
| [composition-api.md](composition-api.md) | ref、reactive、computed、watch详细指南 | API详情 |
| [hooks-lifecycle.md](hooks-lifecycle.md) | 生命周期Hooks、高级响应式模式 | 高级开发 |
| [project-patterns.md](project-patterns.md) | 项目结构、状态管理、性能优化、安全 | 项目架构 |

## 版本与环境

### Vue 版本标准
- **最小版本**：Vue 3.4+ （官方推荐）
- **推荐版本**：Vue 3.5+（包含最新性能优化和语言特性）
- **支持生命周期**：社区活跃维护，完整 TypeScript 支持

### 相关工具版本
- **Vite**：6.0+（原生 ESM 支持，快速冷启动）
- **TypeScript**：5.3+（完整 Vue 3 类型推断）
- **Pinia**：2.1+（官方状态管理，完全替代 Vuex）
- **Vitest**：1.0+（Vue 单元测试框架）
- **Vue Router**：4.2+（官方路由方案）
- **Volar**：VS Code 官方插件（强大的 IDE 支持）

## 核心概念快览

### Composition API 三大支柱

1. **ref / reactive** - 响应式状态管理
   - 详见 [composition-api.md](composition-api.md)

2. **computed / watch** - 派生状态和副作用
   - 详见 [composition-api.md](composition-api.md)

3. **生命周期 Hooks** - 组件生命周期控制
   - 详见 [hooks-lifecycle.md](hooks-lifecycle.md)

## 核心概念与最佳实践

### Composition API 标准

#### ref 与 reactive 的选择

```typescript
// ✅ 推荐：ref 用于基本类型和需要整体替换的对象
import { ref } from 'vue'

// 基本类型
const count = ref(0)
const name = ref('Vue')

// 对象类型（推荐方式）
const user = ref({ id: 1, name: 'John', profile: { age: 30 } })
user.value = { id: 2, name: 'Jane', profile: { age: 25 } }

// ✅ reactive 仅用于复杂状态结构且需要深层追踪的场景
import { reactive, toRefs } from 'vue'

const state = reactive({
  form: { name: '', email: '' },
  errors: { name: '', email: '' }
})

// 从 reactive 解构需要用 toRefs 保持响应性
const { form, errors } = toRefs(state)

// ❌ 避免：混合使用导致响应性混乱
const config = reactive({ apiUrl: 'http://api.example.com' })
config.apiUrl = 'http://new-api.com' // 可能丢失响应性
```

#### computed 高效用法

```typescript
import { computed, ref } from 'vue'

const firstName = ref('John')
const lastName = ref('Doe')

// ✅ 计算属性：自动缓存，只在依赖变化时重新计算
const fullName = computed(() => {
  console.log('计算 fullName')
  return `${firstName.value} ${lastName.value}`
})

// ✅ 带 setter 的计算属性（用于双向同步）
const normalizedEmail = computed({
  get: () => email.value.toLowerCase(),
  set: (val) => { email.value = val }
})

// ❌ 避免：在计算属性中执行副作用
const badComputed = computed(() => {
  // 不要在这里调用 API 或修改其他数据
  fetch('/api/user') // 错误！
  return data.value
})
```

#### watch 与 watchEffect

```typescript
import { watch, watchEffect, ref } from 'vue'

const userId = ref(1)
const user = ref(null)

// ✅ watch：明确指定依赖，适合处理复杂逻辑
watch(userId, async (newId) => {
  const response = await fetch(`/api/users/${newId}`)
  user.value = await response.json()
}, { immediate: true })

// ✅ watchEffect：自动追踪依赖，适合简单副作用
watchEffect(async () => {
  const response = await fetch(`/api/users/${userId.value}`)
  user.value = await response.json()
})

// ✅ watch 数组追踪多个源
watch([firstName, lastName], ([first, last]) => {
  console.log(`Full name: ${first} ${last}`)
})

// ✅ 深层监听和立即执行
watch(
  () => formData.value.profile,
  (newProfile) => { validateProfile(newProfile) },
  { deep: true, immediate: true }
)

// ❌ 避免：无限监听循环
watch(count, () => { count.value++ }) // 死循环！
```

### \<script setup\> 标准

#### 推荐的组件结构

```vue
<template>
  <div class="user-card">
    <h2>{{ user.name }}</h2>
    <p>{{ user.email }}</p>
    <button @click="editMode = true">编辑</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { User } from '@/types'

// Props 定义
interface Props {
  userId: number
  editable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  editable: false
})

// Emits 定义
const emit = defineEmits<{
  (e: 'update', user: User): void
  (e: 'delete', id: number): void
}>()

// 本地状态
const user = ref<User | null>(null)
const editMode = ref(false)

// 计算属性
const displayName = computed(() => user.value?.name || '未知用户')

// 方法
const handleEdit = async () => {
  editMode.value = true
}

const handleSave = async () => {
  if (user.value) {
    emit('update', user.value)
    editMode.value = false
  }
}

// 暴露给模板引用
defineExpose({ user })
</script>

<style scoped>
.user-card {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>
```

#### Props 定义标准

```typescript
// ✅ 推荐：完整的类型定义与默认值
interface Props {
  id: number
  title: string
  description?: string
  tags?: string[]
  config?: Record<string, unknown>
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  tags: () => [],
  config: () => ({}),
  disabled: false
})

// ❌ 避免：过于复杂的 Props，应该抽离为 Pinia store
const tooManyProps = defineProps({
  user: Object,
  settings: Object,
  permissions: Array,
  theme: String,
  layout: String,
  // ... 超过 5-7 个 Props
})
```

#### Emits 定义标准

```typescript
// ✅ 推荐：明确的类型和事件名
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit', payload: FormData): void
  (e: 'error', error: Error): void
  (e: 'close'): void
}>()

// 使用
emit('update:modelValue', newValue)
emit('submit', formData)
emit('error', new Error('Invalid input'))

// ✅ v-model 双向绑定标准
const modelValue = defineModel<string>()

const handleChange = (value: string) => {
  modelValue.value = value
}

// ❌ 避免：多个 v-model 导致混乱（Vue 3.4+ 支持但不推荐滥用）
// 最多 1-2 个 v-model
```

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
├── composables/         # 可复用的逻辑（Composition 函数）
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

#### 文件命名

```
✅ 推荐：
- 组件：PascalCase，如 UserCard.vue, Button.vue
- Composables：useXxx 格式，如 useUser.ts, useForm.ts
- Stores：camelCase，如 user.ts, products.ts
- Utils：camelCase，如 format.ts, validate.ts
- 目录：kebab-case，如 common, feature, layout

❌ 避免：
- 组件使用 snake_case：user_card.vue
- Composables 不带 use 前缀：user.ts
- 混合命名风格
```

#### 代码命名

```typescript
// ✅ 推荐
const userName = ref('John')
const isLoading = ref(false)
const userList = computed(() => users.value.filter(u => u.active))
const handleUserUpdate = (user: User) => {}
const USER_API_TIMEOUT = 5000

// ❌ 避免
const user_name = ref('John')              // snake_case
const is_loading = ref(false)
const loading = ref(false)                 // 不明确
const update = (user: User) => {}         // 缺少动词或对象
const TIMEOUT = 5000                       // 缺少上下文
```

## 状态管理规范（Pinia）

### Store 设计模式

#### Option Store（传统方式）

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

#### 在组件中使用 Store

```vue
<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 访问状态（响应式）
const userName = computed(() => userStore.userName)

// 调用 Action
const handleLogin = async () => {
  await userStore.login(email.value, password.value)
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

### TypeScript 配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "declaration": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### 依赖管理（yarn）

```bash
# 使用 yarn 进行包管理（前端优先级：yarn > pnpm > npm）
yarn add vue@latest
yarn add -D vite @vitejs/plugin-vue
yarn add pinia vue-router

# 同步依赖
yarn install

# 生产环境安装
yarn install --production
```

## 测试标准

### 测试框架（Vitest）

```typescript
// src/components/__tests__/Button.test.ts
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

  it('is disabled when disabled prop is true', () => {
    const wrapper = mount(Button, {
      props: { disabled: true }
    })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
```

### 覆盖率目标

- **总体覆盖率**：≥ 80%
- **关键业务逻辑**：≥ 90%
- **UI 组件**：≥ 70%
- **工具函数**：≥ 95%

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
// ✅ 使用 shallowRef 处理大对象
const largeData = shallowRef({ /* 大数据结构 */ })

// ✅ 使用 shallowReactive 处理嵌套对象
const config = shallowReactive({ api: { url: '', timeout: 5000 } })

// ✅ 计算属性缓存
const expensiveCompute = computed(() => {
  return heavyCalculation(data.value)
}, { cache: true })

// ❌ 避免：频繁的深层监听
watch(
  () => user.value.profile.settings,
  () => { /* 更新 */ },
  { deep: true } // 性能问题！
)
```

## Core Web Vitals 目标

- **LCP (Largest Contentful Paint)**：< 2.5s
- **INP (Interaction to Next Paint)**：< 200ms
- **CLS (Cumulative Layout Shift)**：< 0.1

**优化策略**：
- 预加载关键资源
- 代码分割和懒加载
- 图片优化（webp、响应式）
- 使用 CDN 加速
- 启用 gzip 压缩

## 常见模式与反模式

### ✅ 推荐模式

```typescript
// 1. Composable 复用逻辑
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

// 2. 类型安全的 API 调用
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

// 3. 条件渲染优化
const shouldRender = computed(() => user.value?.role === 'admin')

// 4. 事件委托处理大列表
const handleItemClick = (id: number) => {
  // 处理单个项目点击
}
```

### ❌ 反模式

```typescript
// 1. 直接修改 ref 值而不考虑响应性
const obj = ref({ count: 0 })
obj.value.count = 1 // 可能不更新，应该重新赋值

// 2. 在模板中进行复杂计算
<div>{{ items.filter(i => i.active).map(i => i.name).join(', ') }}</div>

// 3. 过度使用 watch
watch(count, () => { /* ... */ })
watch(count, () => { /* ... */ })
watch(count, () => { /* ... */ })
// 应该合并逻辑

// 4. Props 深度嵌套
<Child :user.id="user.value.profile.settings.preferences.ui" />

// 5. Store 中混合业务逻辑和 UI 逻辑
```

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

## 框架集成指南

### 与 Nuxt 3 集成

```typescript
// app.vue（Nuxt 中）
<template>
  <div>
    <NuxtLink to="/about">关于</NuxtLink>
    <NuxtPage />
  </div>
</template>

// plugins/axios.ts
export default defineNuxtPlugin(() => {
  const api = $fetch.create({
    baseURL: useRuntimeConfig().public.apiBase
  })
  return { provide: { api } }
})
```

### 与 TypeScript 集成

```typescript
// 完整的类型定义
interface Component {
  props: Record<string, any>
  emits: Record<string, any>
  setup: (props: any, context: any) => any
}

// 导入类型
import type { App, ComponentPublicInstance } from 'vue'
```

## 环境配置

### 环境变量

```bash
# .env.development
VITE_API_URL=http://localhost:3000
VITE_DEBUG=true

# .env.production
VITE_API_URL=https://api.example.com
VITE_DEBUG=false
```

### 使用环境变量

```typescript
const apiUrl = import.meta.env.VITE_API_URL
const isDevelopment = import.meta.env.DEV
```

## 调试与监控

### Vue DevTools

- 检查组件树和状态
- 追踪事件和路由导航
- 性能分析
- 时间旅行调试

### 性能监测

```typescript
// 使用 Performance API
performance.mark('operation-start')
// ... 操作代码
performance.mark('operation-end')
performance.measure('operation', 'operation-start', 'operation-end')
```

## 完整示例：用户管理功能

```vue
<!-- src/pages/UserManagement.vue -->
<template>
  <div class="user-management">
    <h1>用户管理</h1>

    <div class="controls">
      <input v-model="searchQuery" type="text" placeholder="搜索用户...">
      <button @click="openCreateModal">新建用户</button>
    </div>

    <table v-if="filteredUsers.length > 0">
      <tbody>
        <tr v-for="user in filteredUsers" :key="user.id">
          <td>{{ user.name }}</td>
          <td>{{ user.email }}</td>
          <td>
            <button @click="editUser(user)">编辑</button>
            <button @click="deleteUser(user.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <UserModal v-if="showModal" @save="saveUser" @cancel="closeModal" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import UserModal from '@/components/UserModal.vue'
import type { User } from '@/types'

const userStore = useUserStore()
const searchQuery = ref('')
const showModal = ref(false)
const selectedUser = ref<User | null>(null)

const filteredUsers = computed(() => {
  return userStore.users.filter(u =>
    u.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const openCreateModal = () => {
  selectedUser.value = null
  showModal.value = true
}

const editUser = (user: User) => {
  selectedUser.value = user
  showModal.value = true
}

const saveUser = async (user: User) => {
  if (selectedUser.value) {
    await userStore.updateUser(user)
  } else {
    await userStore.createUser(user)
  }
  closeModal()
}

const deleteUser = async (id: number) => {
  if (confirm('确定要删除该用户吗？')) {
    await userStore.deleteUser(id)
  }
}

const closeModal = () => {
  showModal.value = false
  selectedUser.value = null
}
</script>

<style scoped>
.user-management {
  padding: 2rem;
}

.controls {
  margin-bottom: 2rem;
  display: flex;
  gap: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

tr {
  border-bottom: 1px solid #ddd;
}

td {
  padding: 0.5rem;
}

button {
  padding: 0.25rem 0.5rem;
  margin-right: 0.5rem;
}
</style>
```

## 总结检查清单

实施 Vue 项目时的质量检查：

- [ ] 所有组件使用 \<script setup\> 语法
- [ ] Props 和 Emits 完整定义了类型
- [ ] 使用 ref 而非 reactive 管理状态
- [ ] Computed 属性用于派生状态
- [ ] Watch 仅用于副作用，避免过度使用
- [ ] 项目结构遵循推荐的目录布局
- [ ] 使用 Pinia 进行状态管理
- [ ] 应用类型安全的 API 调用
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 性能指标符合 Core Web Vitals 目标
- [ ] 实现了 XSS 和 CSRF 防护
- [ ] 使用 Vite 和 TypeScript 完整配置
- [ ] 依赖使用 yarn 进行管理
