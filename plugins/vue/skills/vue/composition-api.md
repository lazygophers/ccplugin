# Composition API 详细指南

## ref 与 reactive 的选择

### ref - 推荐用法

```typescript
// ✅ 推荐：ref 用于基本类型和需要整体替换的对象
import { ref } from 'vue'

// 基本类型
const count = ref(0)
const name = ref('Vue')

// 对象类型（推荐方式）
const user = ref({ id: 1, name: 'John', profile: { age: 30 } })
user.value = { id: 2, name: 'Jane', profile: { age: 25 } }
```

**特点：**
- 包裹在 .value 中
- 解构时自动解包（在模板中）
- 适合整体替换的数据

### reactive - 特殊场景

```typescript
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

## computed 高效用法

### 基础计算属性

```typescript
import { computed, ref } from 'vue'

const firstName = ref('John')
const lastName = ref('Doe')

// ✅ 计算属性：自动缓存，只在依赖变化时重新计算
const fullName = computed(() => {
  console.log('计算 fullName')
  return `${firstName.value} ${lastName.value}`
})
```

### 带 setter 的计算属性

```typescript
const email = ref('john@example.com')

// ✅ 带 setter 的计算属性（用于双向同步）
const normalizedEmail = computed({
  get: () => email.value.toLowerCase(),
  set: (val) => { email.value = val }
})
```

### 避免的模式

```typescript
// ❌ 避免：在计算属性中执行副作用
const badComputed = computed(() => {
  // 不要在这里调用 API 或修改其他数据
  fetch('/api/user') // 错误！
  return data.value
})
```

## watch 与 watchEffect

### watch - 显式依赖

```typescript
import { watch, ref } from 'vue'

const userId = ref(1)
const user = ref(null)

// ✅ watch：明确指定依赖，适合处理复杂逻辑
watch(userId, async (newId) => {
  const response = await fetch(`/api/users/${newId}`)
  user.value = await response.json()
}, { immediate: true })

// ✅ watch 数组追踪多个源
const firstName = ref('John')
const lastName = ref('Doe')

watch([firstName, lastName], ([first, last]) => {
  console.log(`Full name: ${first} ${last}`)
})

// ✅ 深层监听和立即执行
const formData = ref({ profile: { name: '' } })

watch(
  () => formData.value.profile,
  (newProfile) => { validateProfile(newProfile) },
  { deep: true, immediate: true }
)
```

### watchEffect - 自动依赖追踪

```typescript
// ✅ watchEffect：自动追踪依赖，适合简单副作用
watchEffect(async () => {
  const response = await fetch(`/api/users/${userId.value}`)
  user.value = await response.json()
})
```

### 避免的模式

```typescript
// ❌ 避免：无限监听循环
watch(count, () => { count.value++ }) // 死循环！

// ❌ 避免：频繁的深层监听（性能问题）
watch(
  () => user.value.profile.settings,
  () => { /* 更新 */ },
  { deep: true } // 性能问题！
)
```

## Composition API 最佳实践

### 1. 使用 ref 而非 reactive

**原因：**
- 更好的TypeScript支持
- 更清晰的意图
- 避免响应性陷阱

```typescript
// ✅ 推荐
const user = ref({ name: 'John' })

// ❌ 避免
const user = reactive({ name: 'John' })
```

### 2. computed 用于派生状态

```typescript
const users = ref([
  { id: 1, name: 'John', active: true },
  { id: 2, name: 'Jane', active: false }
])

// ✅ 使用 computed 获取派生数据
const activeUsers = computed(() => 
  users.value.filter(u => u.active)
)

// ❌ 避免：在模板中进行复杂计算
// <div>{{ users.filter(u => u.active).map(u => u.name) }}</div>
```

### 3. 合理使用 watch

```typescript
// ✅ 适合：处理副作用（API调用、日志等）
watch(searchQuery, async (query) => {
  const results = await api.search(query)
  searchResults.value = results
})

// ❌ 避免：过度使用 watch
watch(count, () => { /* ... */ })
watch(count, () => { /* ... */ })
watch(count, () => { /* ... */ })
// 应该合并逻辑
```

### 4. Composables 复用逻辑

```typescript
// ✅ 推荐：提取为 Composable
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

  return { user, loading, fetchUser }
}

// 在组件中使用
const { user, loading } = useUser(123)
```

## 响应式数据流模式

### 单向数据流

```typescript
// ✅ 推荐：数据从上往下流动
const data = ref(initialValue)
const derivedData = computed(() => transform(data.value))
watch(data, (newValue) => { /* 处理副作用 */ })
```

### 避免的双向流动

```typescript
// ❌ 避免：循环依赖
const a = ref(0)
const b = computed(() => a.value + 1)
watch(b, (newB) => { a.value = newB - 1 }) // 死循环！
```

## 性能优化技巧

### 使用 shallowRef 处理大对象

```typescript
import { shallowRef } from 'vue'

// 对于大数据结构，避免深度追踪
const largeData = shallowRef({ /* 大数据结构 */ })

// 更新时需要重新赋值
largeData.value = newLargeData
```

### 使用 shallowReactive

```typescript
import { shallowReactive } from 'vue'

// 仅追踪顶层属性
const config = shallowReactive({
  api: { url: '', timeout: 5000 }
})

// 顶层属性响应
config.api = { url: 'new-url', timeout: 3000 } // ✅

// 嵌套属性不响应
config.api.url = 'new-url' // ❌
```

## 常见模式总结

| 需求 | 推荐方案 | 示例 |
|------|--------|------|
| 管理基本状态 | ref | const count = ref(0) |
| 派生状态 | computed | const doubled = computed(() => count.value * 2) |
| 处理副作用 | watch | watch(id, fetchData) |
| 自动追踪副作用 | watchEffect | watchEffect(() => doSomething()) |
| 复用逻辑 | Composable | useUser(id) |
| 大对象优化 | shallowRef | shallowRef(largeObject) |
